#!/usr/bin/env python
#
# notebook.py - The NotebookAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`NotebookAction` class, an action which
starts an IPython kernel and a Jupyter notebook server, allowing the user
to interact with FSLeyes via a jupyter notebook.
"""


import               os
import os.path    as op
import subprocess as sp
import               sys
import               time
import               atexit
import               shutil
import               logging
import               binascii
import               tempfile
import               warnings
import               threading
import               contextlib
import               webbrowser

import               wx
import jinja2     as j2

import fsleyes_widgets.utils.progress     as progress
import fsleyes_widgets.utils.status       as status
import fsl.utils.settings                 as settings
from   fsl.utils.platform import platform as fslplatform
import fsl.utils.tempdir                  as tempdir
import fsl.utils.idle                     as idle

import                                       fsleyes
import fsleyes.strings                    as strings
import fsleyes.actions.screenshot         as screenshot

from . import                                base
from . import                                runscript

try:
    import                            zmq

    import zmq.eventloop.zmqstream as zmqstream

    import ipykernel.ipkernel      as ipkernel
    import ipykernel.iostream      as iostream
    import ipykernel.zmqshell      as zmqshell
    import ipykernel.heartbeat     as heartbeat

    import notebook.notebookapp    as notebookapp

    import IPython.display         as display

    import jupyter_client          as jc
    import jupyter_client.session  as jcsession

    ENABLED = True

except ImportError:

    class mock(object):
        pass

    # so the sub-class defs in
    # this module do not error
    zmqshell                     = mock()
    zmqshell.ZMQInteractiveShell = mock
    ipkernel                     = mock()
    ipkernel.IPythonKernel       = mock

    ENABLED = False


log = logging.getLogger(__name__)


class NotebookAction(base.Action):
    """The ``NotebookAction`` is an :class:`.Action` which (if necessary)
    starts an embedded IPython kernel and a jupyter notebook server, and
    opens the server home page in a web browser allowing the user to interact
    with FSLeyes via notebooks.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``NotebookAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The master :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__openNotebooks)

        # permanently disable if any
        # dependencies are not present
        self.enabled        = ENABLED
        self.__overlayList  = overlayList
        self.__displayCtx   = displayCtx
        self.__frame        = frame
        self.__kernel       = None
        self.__server       = None


    def __openNotebooks(self):
        """Called when this ``NotebookAction`` is invoked. Starts the
        server and kernel if necessary, then opens a new notebook in a
        web browser.
        """

        # have the kernel or server threads crashed?
        if self.__kernel is not None and not self.__kernel.is_alive():
            self.__kernel = None
        if self.__server is not None and not self.__server.is_alive():
            self.__server = None

        # show a progress dialog if we need
        # to initialise the kernel or server
        if self.__kernel is None or self.__server is None:
            title   = strings.titles[self, 'init']
            progdlg = progress.Bounce(title)
        else:
            progdlg = None

        try:
            # start the kernel/server, and show
            # an error if something goes wrong
            errt = strings.titles[  self, 'init.error']
            errm = strings.messages[self, 'init.error']
            with status.reportIfError(errt, errm):
                if self.__kernel is None:
                    self.__kernel = self.__startKernel(progdlg)
                if self.__server is None:
                    self.__server = self.__startServer(progdlg)

        finally:
            if progdlg is not None:
                progdlg.Destroy()
                progdlg = None

        # if all is well, open the
        # notebook server homepage
        webbrowser.open(self.__server.url)


    def __bounce(self, secs, progdlg):
        """Used by :meth:`__startKernel` and :meth:`__startServer`. Blocks for
        ``secs``, bouncing the :class:`.Progress` dialog ten times per second,
        and yielding to the ``wx`` main loop.
        """
        for i in range(int(secs * 10)):
            progdlg.DoBounce()
            wx.GetApp().Yield()
            time.sleep(0.1)


    def __startKernel(self, progdlg):
        """Attempts to create and start a :class:`BackgroundIPythonKernel`.

        :returns: the kernel if it was started.

        :raises: A :exc:`RuntimeError` if the kernel did not start.
        """
        progdlg.UpdateMessage(strings.messages[self, 'init.kernel'])
        kernel = BackgroundIPythonKernel(
            self.__overlayList,
            self.__displayCtx,
            self.__frame)
        kernel.start()
        self.__bounce(1, progdlg)

        if not kernel.is_alive():
            raise RuntimeError('Could not start IPython kernel: '
                               '{}'.format(kernel.error))

        return kernel


    def __startServer(self, progdlg):
        """Attempts to create and start a :class:`NotebookServer`.

        :returns: the server if it was started.

        :raises: A :exc:`RuntimeError` if the serer did not start.
        """

        progdlg.UpdateMessage(strings.messages[self, 'init.server'])
        server = NotebookServer(self.__kernel.connfile)
        server.start()

        elapsed = 0

        while elapsed < 5 and not server.ready:
            self.__bounce(0.5, progdlg)
            elapsed += 0.5

        if elapsed >= 5 or not server.is_alive():
            raise RuntimeError('Could not start notebook server: '
                               '{}'.format(server.stderr))

        return server


class BackgroundIPythonKernel(object):
    """The BackgroundIPythonKernel creates an IPython jupyter kernel and makes
    it accessible over tcp (on the local machine only).

    Before FSLeyes 0.28.0, this class derived from ``threading.Thread``, and
    ran its own ``IOLoop`` which was used to run the IPython kernel.  But now
    the IPython kernel is run on the main thread, by repeatedly scheduling
    calls to ``IPythonKernel.do_one_iteration`` on :func:`.idle.idle`.

    This update was necessary due to changes in ``ipykernel`` from version 4
    to version 5, namely that ipykernel 5 uses ``asyncio`` co-routines, making
    it difficult to transfer execution between threads.

    Because the ``BackgroundIPythonKernel`` used to be a thread, it is still
    necessary to call its :meth:`start` method to start the kernel loop.

    The Jupyter/IPython documentation is quite fragmented at this point in
    time; `this github issue <https://github.com/ipython/ipython/issues/8097>`_
    was useful in figuring out the implementation details.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Set up the kernel and ``zmq`` ports. A jupyter connection file
        containing the information needed to connect to the kernel is saved
        to a temporary file - its path is accessed as an attribute
        called :meth:`connfile`.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The master :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        ip                 = '127.0.0.1'
        transport          = 'tcp'
        addr               = '{}://{}'.format(transport, ip)
        self.__connfile    = None
        self.__kernel      = None
        self.__error       = None
        self.__lastIter    = 0
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame
        self.__env         = runscript.fsleyesScriptEnvironment(
            frame,
            overlayList,
            displayCtx)[1]

        self.__env['screenshot'] = self.__screenshot

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=DeprecationWarning)

            # Use an empty key to disable message signing
            session = jcsession.Session(key=b'')
            context = zmq.Context.instance()

            # create sockets for kernel communication
            shellsock   = context.socket(zmq.ROUTER)
            stdinsock   = context.socket(zmq.ROUTER)
            controlsock = context.socket(zmq.ROUTER)
            iopubsock   = context.socket(zmq.PUB)

            shellstrm   = zmqstream.ZMQStream(shellsock)
            controlstrm = zmqstream.ZMQStream(controlsock)

            # I/O and heartbeat communication
            # are managed by separate threads.
            self.__iopub     = iostream.IOPubThread(iopubsock)
            self.__heartbeat = heartbeat.Heartbeat(zmq.Context(),
                                                   (transport, ip, 0))
            iopubsock = self.__iopub.background_socket

            self.__heartbeat.start()
            self.__iopub.start()

            # Streams which redirect stdout/
            # stderr to the iopub socket
            stdout = iostream.OutStream(session, self.__iopub, u'stdout')
            stderr = iostream.OutStream(session, self.__iopub, u'stderr')

            # TCP ports for all sockets
            shellport   = shellsock  .bind_to_random_port(addr)
            stdinport   = stdinsock  .bind_to_random_port(addr)
            controlport = controlsock.bind_to_random_port(addr)
            iopubport   = iopubsock  .bind_to_random_port(addr)
            hbport      = self.__heartbeat.port

            # Create the kernel
            self.__kernel = FSLeyesIPythonKernel.instance(
                stdout,
                stderr,
                shell_class=FSLeyesIPythonShell,
                session=session,
                shell_streams=[shellstrm, controlstrm],
                iopub_socket=iopubsock,
                stdin_socket=stdinsock,
                user_ns=self.__env,
                log=logging.getLogger('ipykernel.kernelbase'))

        # write connection file to a temp dir
        hd, fname = tempfile.mkstemp(
            prefix='fsleyes-kernel-{}.json'.format(os.getpid()),
            suffix='.json')
        os.close(hd)

        self.__connfile = fname

        log.debug('IPython kernel connection file: %s', fname)

        jc.write_connection_file(
            fname,
            shell_port=shellport,
            stdin_port=stdinport,
            iopub_port=iopubport,
            control_port=controlport,
            hb_port=hbport,
            ip=ip)

        atexit.register(os.remove, self.__connfile)


    def is_alive(self):
        """Returns ``True`` if the kernel loop appears to be running, ``False``
        otherwise
        """
        # We check that the last kernel
        # iteration was not too long ago,
        # that an error hasn't occurred,
        # and that the worker threads are
        # alive.
        now   = time.time()
        delta = 1.0

        return (now - self.__lastIter) < delta and \
               self.__error is None            and \
               self.__iopub.thread.is_alive()  and \
               self.__heartbeat.is_alive()


    @property
    def kernel(self):
        """The ``IPythonKernel`` object. """
        return self.__kernel


    @property
    def env(self):
        """The namespace passed to the kernel."""
        return self.__env


    @property
    def connfile(self):
        """The jupyter connection file containing information to connect
        to the IPython kernel.
        """
        return self.__connfile


    @property
    def error(self):
        """If an error occurs on the kernel loop causing it to crash, a
        reference to the ``Exception`` is stored here.
        """
        return self.__error


    def __screenshot(self, view):
        """Insert a screenshot of the given view into the notebook. """
        with tempdir.tempdir():
            screenshot.screenshot(view, 'screenshot.png')
            return display.Image('screenshot.png')


    def __kernelDispatch(self):
        """Event loop used for the IPython kernel. Calls
        IPythonKernel.do_one_iteration, and then schedules a future call to
        ``__kernelDispatch`` via :func:`.idle.idle` loop.
        """
        try:
            self.__kernel.do_one_iteration()
            idle.idle(self.__kernelDispatch,
                      after=self.__kernel._poll_interval)

            # save the time on each iteration,
            # so the is_alive method has an
            # idea of whether the kernel is
            # still running
            self.__lastIter = time.time()

        except Exception as e:
            self.__error = e
            raise


    def start(self):
        """Start the IPython kernel loop. This method returns immediately - the
        kernel loop is executed on :func:`.idle.idle`.
        """
        self.__kernel.start()
        idle.idle(self.__kernelDispatch, after=self.__kernel._poll_interval)


class FSLeyesIPythonKernel(ipkernel.IPythonKernel):
    """Custom IPython kernel used by FSLeyes. All this class does is ensure
    that the ``sys.stdout`` and ``sys.stderr`` streams are set appropriately
    when the kernel is executing code.
    """

    def __init__(self, stdout, stderr, *args, **kwargs):
        self.__stdout = stdout
        self.__stderr = stderr
        super(FSLeyesIPythonKernel, self).__init__(*args, **kwargs)

    @contextlib.contextmanager
    def __patch_streams(self):

        stdout     = sys.stdout
        stderr     = sys.stderr
        sys.stdout = self.__stdout
        sys.stderr = self.__stderr

        try:
            yield
        finally:

            sys.stdout = stdout
            sys.stderr = stderr
            self.__stdout.flush()
            self.__stderr.flush()

    def execute_request(self, *args, **kwargs):
        with self.__patch_streams():
            return super(FSLeyesIPythonKernel, self).execute_request(
                *args, **kwargs)

    def dispatch_control(self, *args, **kwargs):
        with self.__patch_streams():
            return super(FSLeyesIPythonKernel, self).dispatch_control(
                *args, **kwargs)

    def dispatch_shell(self, *args, **kwargs):
        with self.__patch_streams():
            return super(FSLeyesIPythonKernel, self).dispatch_shell(
                *args, **kwargs)


class FSLeyesIPythonShell(zmqshell.ZMQInteractiveShell):
    """Custom IPython shell class used by FSLeyes. """

    def enable_gui(self, gui):
        """Overrides  ``ipykernel.zmqshell.ZMQInteractiveShell.enable_gui``.

        The default implementation will attempt to change the IPython GUI
        integration event loop, which will conflict with our own event loop
        in the :class:`BackgroundIPythonKernel`. So this implementation
        does nothing.
        """
        pass


class NotebookServer(threading.Thread):
    """Thread which starts a jupyter notebook server, and waits until
    it dies or is killed.

    The server is configured such that all notebooks will connect to
    the same kernel, specified by the ``kernelFile`` parameter to
    :meth:`__init__`.
    """


    def __init__(self, connfile):
        """Create a ``NotebookServer`` thread.

        :arg connfile: Connection file of the IPython kernel to connect to.
        """

        threading.Thread.__init__(self)
        self.daemon        = True
        self.__connfile    = connfile
        self.__stdout      = None
        self.__stderr      = None
        self.__port        = None
        self.__token       = binascii.hexlify(os.urandom(24)).decode('ascii')


    @property
    def port(self):
        """Returns the TCP port that the notebook server is listening on.
        Will return ``None`` before the server has started.
        """
        if self.__port is not None:
            return self.__port

        self.__port = self.__readPort()
        return self.__port


    def __readPort(self):
        for server in notebookapp.list_running_servers():
            if server['token'] == self.__token:
                return server['port']
        return None


    @property
    def ready(self):
        """Returns ``True`` if the server is running and ready, ``False``
        otherwise.
        """
        return self.__readPort() is not None


    @property
    def token(self):
        """Returns an authentication token to use for connectng to the
        notebook server.
        """
        return self.__token


    @property
    def url(self):
        """Returns the URL to use to connect to this server. """
        return 'http://localhost:{}?token={}'.format(self.port, self.token)


    @property
    def stdout(self):
        """After the server has died, returns its standard output. While the
        server is still running, returns ``None``.
        """
        return self.__stdout


    @property
    def stderr(self):
        """After the server has died, returns its standard error. While the
        server is still running, returns ``None``.
        """
        return self.__stderr


    def run(self):
        """Sets up a server configuration file, and then calls
        ``jupyer-notebook`` via ``subprocess.Popen``. Waits until
        the notebook process dies.
        """

        # copy our custom jupyter config template
        # directory to a temporary location that
        # will be deleted on exit.
        cfgdir = op.join(tempfile.mkdtemp(prefix='fsleyes-jupyter'), 'config')
        shutil.copytree(op.join(fsleyes.assetDir, 'assets', 'jupyter'), cfgdir)

        log.debug('Copied notebook configuration to %s', cfgdir)

        self.__initConfigDir(cfgdir)

        # Set up the environment in which the
        # server will run - make sure FSLeyes
        # is on the PYTHONPATH, and
        # JUPYTER_CONFIG_DIR is set, so our
        # custom bits and pieces will be found.
        env        = dict(os.environ)
        pythonpath = os.pathsep.join((cfgdir, env.get('PYTHONPATH', '')))

        env['JUPYTER_CONFIG_DIR'] = cfgdir
        env['PYTHONPATH']         = pythonpath

        # command to start the notebook
        # server in a sub-process

        # With frozen FSLeyes versions, there
        # probbaly isn't a 'jupyter-notebook'
        # executable. So we use a hook in
        # fsleyes.main to run the server.
        if fslplatform.frozen:
            exe = op.join(op.dirname(sys.executable), 'fsleyes')
            log.debug('Running notebook server via %s notebook', sys.argv[0])

            # py2app manipulates the PYTHONPATH, so we
            # pass it through as a command-line argument.
            self.__nbproc = sp.Popen([exe, 'notebook', 'server', cfgdir],
                                     stdout=sp.PIPE,
                                     stderr=sp.PIPE,
                                     cwd=cfgdir,
                                     env=env)

        # Otherwise we can call
        # it in the usual manner.
        else:
            log.debug('Running notebook server via jupyter-notebook')
            self.__nbproc = sp.Popen(['jupyter-notebook'],
                                     stdout=sp.PIPE,
                                     stderr=sp.PIPE,
                                     cwd=cfgdir,
                                     env=env)

        def killServer():
            # We need two CTRL+Cs to kill
            # the notebook server
            self.__nbproc.terminate()
            self.__nbproc.terminate()

            # Give it a little time, then
            # force kill if needed
            try:
                self.__nbproc.wait(0.25)
            except sp.TimeoutExpired:
                self.__nbproc.kill()

            shutil.rmtree(op.abspath(op.join(cfgdir, '..')))

        # kill the server when we get killed
        atexit.register(killServer)

        # wait forever
        o, e          = self.__nbproc.communicate()
        self.__stdout = o.decode()
        self.__stderr = e.decode()


    def __initConfigDir(self, cfgdir):
        """Creates a copy of the FSLeyes ``/assets/jupyter/`` configuration
        directory in ``$TMPDIR``, and customises its settings accordingly.
        """

        nbextdir    = op.join(cfgdir, 'nbextensions')
        defaultPort = settings.read('fsleyes.notebook.port', 8888)

        # Environment for generating a jupyter
        # notebook server configuration file
        cfgenv = {
            'fsleyes_nbserver_port'       : defaultPort,
            'fsleyes_nbserver_token'      : self.__token,
            'fsleyes_nbserver_dir'        : op.expanduser('~'),
            'fsleyes_nbserver_static_dir' : cfgdir,
            'fsleyes_nbextension_dir'     : nbextdir,
            'fsleyes_kernel_connfile'     : self.__connfile,
        }

        with open(op.join(nbextdir, 'fsleyes_notebook_intro.md'), 'rt') as f:
            intro = f.read()

        # Environment for generating the
        # notebook template extension
        extenv = {
            'intro' : intro.replace('\n', '\\n'),
        }

        cfgfile = op.join(cfgdir, 'jupyter_notebook_config.py')
        extfile = op.join(cfgdir, 'nbextensions', 'notebook_template.js')

        files = [cfgfile, extfile]
        envs  = [cfgenv,  extenv]

        for fn, e in zip(files, envs):
            with open(fn, 'rt') as f: template = j2.Template(f.read())
            with open(fn, 'wt') as f: f.write(template.render(**e))


def nbmain(argv):
    """Notebook entry point used when FSLeyes is running as a frozen
    application.

    Used to start notebook server and kernel processes.
    """

    if not fslplatform.frozen:
        raise RuntimeError('nbmain can only be used in '
                           'frozen versions of FSLeyes')

    if argv[0] != 'notebook':
        raise RuntimeError('argv does not look like nbmain arguments '
                           '(first arg is not \'notebook\')')

    argv = argv[1:]

    # run the notebook server
    if argv[0] == 'server':
        from notebook.notebookapp import main

        # second argument is a path
        # to add to the PYTHONPATH.
        # See NotebookServer.run.
        sys.path.insert(0, argv[1])
        return main(argv=[])

    # run a kernel (in place of ipykernel_launcher}
    elif argv[0] == 'kernel':
        from ipykernel.kernelapp import IPKernelApp

        app = IPKernelApp.instance()
        app.initialize(argv[1:])
        return app.start()
