#!/usr/bin/env python
#
# notebook.py - The NotebookAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`NotebookAction` class, ...


refs

https://github.com/ipython/ipython/issues/8097
https://github.com/ebanner/extipy
"""


import os
import atexit
import logging
import tempfile
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

except ImportError:
    pass


log = logging.getLogger(__name__)


# Debug during development
log.setLevel(logging.DEBUG)



class NotebookAction(base.Action):


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

        self.kernel = None


    def __openNotebook(self):

        env = runscript.fsleyesScriptEnvironment(
            self.__frame,
            self.__overlayList,
            self.__displayCtx)[1]

        if self.kernel is None:
            self.kernel = BackgroundIPythonKernel(env)
            self.kernel.start()


class BackgroundIPythonKernel(threading.Thread):

    def __init__(self, env):

        threading.Thread.__init__(self)

        self.daemon = True

        ip             = '127.0.0.1'
        transport      = 'tcp'
        addr           = '{}://{}'.format(transport, ip)
        self.connfile  = None
        self.ioloop    = None
        self.kernel    = None
        self.heartbeat = heartbeat.Heartbeat(zmq.Context(), (transport, ip, 0))

        self.heartbeat.start()

        # empty key to disable message signing
        session = jcsession.Session(key=b'')
        context = zmq.Context.instance()

        # create sockets for kernel communication
        shell_socket   = context.socket(zmq.ROUTER)
        iopub_socket   = context.socket(zmq.PUB)
        control_socket = context.socket(zmq.ROUTER)

        shell_port   = shell_socket.bind_to_random_port(addr)
        iopub_port   = iopub_socket.bind_to_random_port(addr)
        control_port = control_socket.bind_to_random_port(addr)
        hb_port      = self.heartbeat.port

        shell_stream   = zmqstream.ZMQStream(shell_socket)
        control_stream = zmqstream.ZMQStream(control_socket)

        # Create the kernel
        self.kernel = ipkernel.IPythonKernel(
            session=session,
            shell_streams=[shell_stream, control_stream],
            iopub_socket=iopub_socket,
            user_ns=env,
            log=logging.getLogger('ipykernel.kernelbase'))

        # write connection file to a temp dir
        hd, fname = tempfile.mkstemp(
            prefix='kernel-fsleyes-{}.json'.format(os.getpid()),
            suffix='.json')
        os.close(hd)

        self.connfile = fname

        log.debug('IPython kernel connection file: %s', fname)

        jc.write_connection_file(
            fname,
            shell_port=shell_port,
            iopub_port=iopub_port,
            control_port=control_port,
            hb_port=hb_port,
            ip=ip)
        atexit.register(self.__deleteConnectionFile)


    def __deleteConnectionFile(self):
        """
        """
        try:
            if self.connfile is not None:
                os.remove(self.connfile)
                self.connfile = None
        except Exception:
            pass


    def kernelDispatch(self):
        """
        """
        idle.idle(self.kernel.do_one_iteration)
        self.ioloop.call_later(self.kernel._poll_interval, self.kernelDispatch)


    def run(self):
        """
        """
        self.ioloop = ioloop.IOLoop()

        self.ioloop.make_current()
        self.kernel.start()
        self.ioloop.call_later(self.kernel._poll_interval, self.kernelDispatch)
        self.ioloop.start()
