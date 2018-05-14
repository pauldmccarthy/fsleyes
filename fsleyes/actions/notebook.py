#!/usr/bin/env python
#
# notebook.py - The NotebookAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`NotebookAction` class, an action which
starts a Jupyter notebook server and opens a notebook which allows the user
to interact with FSLeyes.

refs

https://github.com/ebanner/extipy
"""


import os
import atexit
import logging
import tempfile
import warnings
import threading

import fsl.utils.idle as idle

from . import base
from . import runscript

try:
    import                            zmq
    import zmq.eventloop.zmqstream as zmqstream
    import tornado.ioloop          as ioloop

    import ipykernel.ipkernel      as ipkernel
    import ipykernel.heartbeat     as heartbeat

    import jupyter_client          as jc
    import jupyter_client.session  as jcsession

    ENABLED = True

except ImportError:
    ENABLED = False


log = logging.getLogger(__name__)


# Debug during development
log.setLevel(logging.DEBUG)



class NotebookAction(base.Action):
    """The ``NotebookAction`` is an :class:`.Action` which (if necessary)
    starts a jupyter notebook server and an embedded IPython kernel, and then
    opens a notebook in a web browser allowing the user to interact with
    FSLeyes.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``NotebookAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__openNotebook)
        self.__frame       = frame
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx

        self.__kernel  = None
        self.enabled = ENABLED


    def __openNotebook(self):
        """Called when this ``NotebookAction`` is invoked. Starts the
        server and kernel if necessary, then opens a new notebook in a
        web browser.
        """

        env = runscript.fsleyesScriptEnvironment(
            self.__frame,
            self.__overlayList,
            self.__displayCtx)[1]

        if self.__kernel is None:
            self.__kernel = BackgroundIPythonKernel(env)
            self.__kernel.start()


class BackgroundIPythonKernel(threading.Thread):
    """The BackgroundIPythonKernel creates an IPython jupyter kernel and makes
    it accessible over tcp, on the local machine only. The ``zmq`` event loop
    is run on a separate thread, but the kernel handles events on the main
    thread, via :func:`.idle.idle`.


    The Jupyter/IPython documentation is quite fragmented at this point in
    time; `this github issue <https://github.com/ipython/ipython/issues/8097>`_
    was useful in figuring out the details.
    """


    def __init__(self, env):
        """Set up the kernel and ``zmq`` ports. A jupyter connection file
        containing the information needed to connect to the kernel is saved
        to a temporary file - its path is accessed as an attribute
        called :meth:`connfile`.

        :arg env: Dictionary to be used as the kernel namespace.
        """

        threading.Thread.__init__(self)

        self.daemon = True

        ip              = '127.0.0.1'
        transport       = 'tcp'
        addr            = '{}://{}'.format(transport, ip)
        self.__connfile = None
        self.__ioloop   = None
        self.__kernel   = None

        with warnings.catch_warnings():
            warnings.simplefilter('ignore')

            self.__heartbeat = heartbeat.Heartbeat(
                zmq.Context(), (transport, ip, 0))
            self.__heartbeat.start()

            # Use an empty key to disable message signing
            session = jcsession.Session(key=b'')
            context = zmq.Context.instance()

            # create sockets for kernel communication
            shellsock   = context.socket(zmq.ROUTER)
            iopubsock   = context.socket(zmq.PUB)
            controlsock = context.socket(zmq.ROUTER)

            shellport   = shellsock  .bind_to_random_port(addr)
            iopubport   = iopubsock  .bind_to_random_port(addr)
            controlport = controlsock.bind_to_random_port(addr)
            hbport      = self.__heartbeat.port

            shellstrm   = zmqstream.ZMQStream(shellsock)
            controlstrm = zmqstream.ZMQStream(controlsock)

            # Create the kernel
            self.__kernel = ipkernel.IPythonKernel(
                session=session,
                shell_streams=[shellstrm, controlstrm],
                iopub_socket=iopubsock,
                user_ns=env,
                log=logging.getLogger('ipykernel.kernelbase'))

        # write connection file to a temp dir
        hd, fname = tempfile.mkstemp(
            prefix='kernel-fsleyes-{}.json'.format(os.getpid()),
            suffix='.json')
        os.close(hd)

        self.__connfile = fname

        log.debug('IPython kernel connection file: %s', fname)

        jc.write_connection_file(
            fname,
            shell_port=shellport,
            iopub_port=iopubport,
            control_port=controlport,
            hb_port=hbport,
            ip=ip)

        atexit.register(os.remove, self.__connfile)


    @property
    def connfile(self):
        """The jupyter connection file containing information to connect
        to the IPython kernel.
        """
        return self.__connfile


    def __kernelDispatch(self):
        """Event loop used for the IPython kernel. Submits the kernel function
        to the :func:`.idle.idle` loop, and schedules another call to this
        method on the ``zmq`` event loop.

        This means that, while the ``zmq`` loop runs in its own thread, the
        IPython kernel is executed on the main thread.
        """
        idle.idle(self.__kernel.do_one_iteration)
        self.__ioloop.call_later(self.__kernel._poll_interval,
                                 self.__kernelDispatch)


    def run(self):
        """Start the IPython kernel and Run the ``zmq`` event loop. """

        self.__ioloop = ioloop.IOLoop()
        self.__ioloop.make_current()
        self.__kernel.start()
        self.__ioloop.call_later(self.__kernel._poll_interval,
                                 self.__kernelDispatch)
        self.__ioloop.start()

