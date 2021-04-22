#!/usr/bin/env python
#
# fsleyes.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the entry point to *FSLeyes*, the FSL image viewer.

Call the :func:`main` function to start the main FSLeyes application.

The :func:`embed` function can be called to open a :class:`.FSLeyesFrame`
within an existing application.

See the :mod:`fsleyes` package documentation for more details on ``fsleyes``.


.. note:: Even though ``fsleyes`` (this module) and :mod:`fsleyes.render` (the
          off-screen renderer) are intended to be separate applications, the
          current version of PyInstaller (3.x) does not support bundling of
          multiple executables
          (https://github.com/pyinstaller/pyinstaller/issues/1527).

          So at this point in time, :mod:`.fsleyes.render` can be invoked via
          ``fsleyes.main`` by passing ``'render'`` as the first argument,
          e.g.::

              python -m fsleyes.main render ...
"""


import functools as ft
import os.path   as op
import              os
import              sys
import              signal
import              logging
import              textwrap

import wx
import wx.adv

from   fsl.utils.platform import platform as fslplatform
import fsl.utils.idle                     as idle
import fsleyes_widgets                    as fwidgets
import fsleyes_widgets.utils.status       as status

import                       fsleyes
import fsleyes.strings    as strings
import fsleyes.splash     as fslsplash
import fsleyes.cliserver  as cliserver
import fsleyes.colourmaps as colourmaps


# wx.ModalDialogHook does not exist in wxPython < 4

if fwidgets.wxFlavour() in (fwidgets.WX_PYTHON, fwidgets.WX_UNKNOWN):
    class ModalDialogHook(object):
        def Register(self):
            pass

    wx.ModalDialogHook = ModalDialogHook


log = logging.getLogger(__name__)


class FSLeyesApp(wx.App):
    """FSLeyes-specific sub-class of ``wx.App``. """


    class ModalHook(wx.ModalDialogHook):
        """Keeps track of any modal dialogs/windows that are opened.

        Modal dialogs can interfere with shutdown, as they run their own event
        loop. Therefore we keep a reference is kept to all opened modal
        dialogs, so we can manually shut them down if needed (see the
        :func:`main` function).
        """

        def __init__(self, *args, **kwargs):
            wx.ModalDialogHook.__init__(self, *args, **kwargs)
            self.modals = set()

        def Enter(self, dlg):
            self.modals.add(dlg)
            return wx.ID_NONE

        def Exit(self, dlg):
            self.modals.discard(dlg)


    def __init__(self):
        """Create a ``FSLeyesApp``. """

        self.__overlayList = None
        self.__displayCtx  = None

        # On macOS, when the user drags a file onto the FSLeyes window,
        # or onto the FSLeyes.app icon, the file path will be passed to
        # MacOpenFiles method. But that method may be called very early
        # on in the startup process, before the DisplayContext and
        # OverlayList have been created. So when this happens, we cache
        # the files here, and then open them when the
        # SetOverlayListAndDisplayContext method gets called.
        self.__filesToOpen = []

        self.__modalHook = FSLeyesApp.ModalHook()
        self.__modalHook.Register()

        wx.App.__init__(self, clearSigInt=False)

        self.SetAppName('FSLeyes')

        try:
            self.__icon = wx.adv.TaskBarIcon(iconType=wx.adv.TBI_DOCK)
            self.__icon.SetIcon(wx.Icon(
                op.join(fsleyes.assetDir, 'icons', 'app_icon.png')))
        except Exception:
            self.__icon = None


    @property
    def modals(self):
        """Returns a list of all currently open modal windows. """
        return list(self.__modalHook.modals)


    def SetOverlayListAndDisplayContext(self, overlayList, displayCtx):
        """References to the :class:`.OverlayList` and master
        :class:`.DisplayContext` must be passed to the ``FSLeyesApp`` via this
        method.
        """
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx

        # MacOpenFiles was called before the
        # overlaylist/dc were created, and
        # queued some files that need to be
        # opened
        if len(self.__filesToOpen) > 0:
            wx.CallAfter(self.MacOpenFiles, self.__filesToOpen)
            self.__filesToOpen = None


    def MacReopenApp(self):
        """On OSX, make sure that the FSLeyes frame is restored if it is
        minimised, and (e.g.) the dock icon is clicked.
        """

        frame = self.GetTopWindow()
        frame.Iconize(False)
        frame.Raise()


    def MacOpenFile(self, filename):
        """On OSX, support opening files via context menu, and files dropped
        on the application icon.
        """
        self.MacOpenFiles([filename])


    def MacOpenURL(self, url):
        """On OSX, support opening files via a ``fsleyes://`` url. """

        if self.__overlayList is None:
            return

        import fsleyes_widgets.utils.status     as status
        import fsleyes.strings                  as strings
        import fsleyes.parseargs                as parseargs
        import fsleyes.actions.applycommandline as applycommandline

        errTitle = strings.titles[  self, 'openURLError']
        errMsg   = strings.messages[self, 'openURLError']

        with status.reportIfError(errTitle, errMsg):
            applycommandline.applyCommandLineArgs(
                self.__overlayList,
                self.__displayCtx,
                parseargs.fsleyesUrlToArgs(url))


    def MacOpenFiles(self, filenames):
        """On OSX, support opening files via context menu, and files dropped
        on the application icon.
        """

        # OverlayList has not yet been created -
        # queue the files to open them later
        # in SetOverlayListAndDisplayContext
        if self.__overlayList is None:
            self.__filesToOpen.extend(filenames)
            return

        import fsleyes.actions.loadoverlay as loadoverlay
        import fsleyes.autodisplay         as autodisplay

        def onLoad(paths, overlays):

            if len(overlays) == 0:
                return

            self.__overlayList.extend(overlays)

            if self.__displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.__overlayList,
                                            self.__displayCtx)

        loadoverlay.loadOverlays(
            filenames,
            onLoad=onLoad,
            inmem=self.__displayCtx.loadInMemory)


def main(args=None):
    """*FSLeyes* entry point. Shows a :class:`.FSLeyesSplash` screen, parses
    command line arguments, and shows a :class:`.FSLeyesFrame`. Returns
    an exit code.
    """

    if args is None:
        args = sys.argv[1:]

    # Hack to allow render to
    # be called via fsleyes.main
    if len(args) >= 1 and args[0] == 'render':
        import fsleyes.render as render
        render.main(args[1:])
        sys.exit(0)

    # the fsleyes.initialise function figures
    # out the path to asset files (e.g. cmaps)
    fsleyes.initialise()

    # Hook which allows us to run a jupyter
    # notebook server from an existing FSLeyes
    # instance
    if len(args) >= 1 and args[0] == 'notebook':
        from fsleyes.actions.notebook import nbmain
        fsleyes.configLogging()
        sys.exit(nbmain(args))

    # initialise colour maps - this must be
    # done before parsing arguments, as if
    # the user asks for help, available
    # colourmaps/luts will be listed.
    colourmaps.init()

    # Function to bootstrap the GUI - keep
    # reading below.
    def initgui():

        # First thing's first. Create a wx.App,
        # and initialise the FSLeyes package.
        app = FSLeyesApp()

        # Create a splash screen frame
        splash = fslsplash.FSLeyesSplash(None)
        return app, splash

    # If it looks like the user is asking for
    # help, or using cliserver to pass arguments
    # to an existing FSLeyes instance, then we
    # parse command line arguments before
    # creating a wx.App and showing the splash
    # screen. This means that FSLeyes help/
    # version information can be retrieved
    # without a display, and hopefully fairly
    # quickly.
    #
    # Otherwise we create the app and splash
    # screen first, so the splash screen gets
    # shown as soon as possible. Arguments
    # will get parsed in the init function below.
    #
    # The argparse.Namespace object is kept in a
    # list so it can be shared between the sub-
    # functions below
    #
    # If argument parsing bombs out, we put the
    # exit code here and return it at the bottom.
    namespace = [None]
    exitCode  = [0]

    # user asking for help - parse args first
    if (len(args) > 0) and (args[0] in ('-V',
                                        '-h',
                                        '-fh',
                                        '-cs',
                                        '--version',
                                        '--help',
                                        '--fullhelp',
                                        '--cliserver')):
        namespace   = [parseArgs(args)]
        app, splash = initgui()

    # otherwise parse arguments on wx.MainLoop
    # below
    else:
        app, splash = initgui()

    # We are going do all processing on the
    # wx.MainLoop, so the GUI can be shown
    # as soon as possible, and because it is
    # difficult to force immediate GUI
    # refreshes when not running on the main
    # loop - this is important for FSLeyes,
    # which displays status updates to the
    # user while it is loading overlays and
    # setting up the interface.
    #
    # All of the work is defined in a series
    # of functions, which are chained together
    # via ugly callbacks, but which are
    # ultimately scheduled and executed on the
    # wx main loop.
    def init(splash):

        # See FSLeyesSplash.Show
        # for horribleness.
        splash.Show()

        # Parse command line arguments if necessary.
        # If arguments are invalid, the parseargs
        # module will raise SystemExit.
        try:
            if namespace[0] is None:

                errmsg   = strings.messages['main.parseArgs.error']
                errtitle = strings.titles[  'main.parseArgs.error']
                with status.reportIfError(errtitle, errmsg, raiseError=True):
                    namespace[0] = parseArgs(args)

        # But the wx.App.MainLoop eats SystemExit
        # exceptions for unknown reasons, and
        # causes the application to exit
        # immediately. This makes testing FSLeyes
        # (e.g. code coverage) impossible. So I'm
        # catching SystemExit here, and then
        # telling the wx.App to exit gracefully.
        except (SystemExit, Exception) as e:
            app.ExitMainLoop()
            exitCode[0] = getattr(e, 'code', 1)
            return

        # Configure logging (this has to be done
        # after cli arguments have been parsed,
        # but before initialise is called).
        fsleyes.configLogging(namespace[0].verbose, namespace[0].noisy)

        # Initialise sub-modules/packages. The
        # buildGui function is passed through
        # as a callback, which gets called when
        # initialisation is complete.
        initialise(splash, namespace[0], buildGui)

    def buildGui():

        # Now the main stuff - create the overlay
        # list and the master display context,
        # and then create the FSLeyesFrame.
        overlayList, displayCtx = makeDisplayContext(namespace[0], splash)
        app.SetOverlayListAndDisplayContext(overlayList, displayCtx)
        frame = makeFrame(namespace[0],
                          displayCtx,
                          overlayList,
                          splash,
                          [shutdown])

        app.SetTopWindow(frame)
        frame.Show()

        # Check that $FSLDIR is set, complain
        # to the user if it isn't
        if not namespace[0].skipfslcheck:
            wx.CallAfter(fslDirWarning, frame)

        # Check for updates. Ignore point
        # releases, otherwise users might
        # get swamped with update notifications.
        if namespace[0].updatecheck:
            import fsleyes.actions.updatecheck as updatecheck
            wx.CallAfter(updatecheck.UpdateCheckAction(),
                         showUpToDateMessage=False,
                         showErrorMessage=False,
                         ignorePoint=False)

        # start notebook server
        if namespace[0].notebookFile is not None:
            namespace[0].notebook     = True
            namespace[0].notebookFile = op.abspath(namespace[0].notebookFile)
        if namespace[0].notebook:
            from fsleyes.actions.notebook import NotebookAction
            frame.menuActions[NotebookAction](namespace[0].notebookFile)

        # start CLI server
        if namespace[0].cliserver:
            cliserver.runserver(overlayList, displayCtx)

    # Shut down cleanly on sigint/sigterm.
    # We do this so that any functions
    # registered with atexit will actually
    # get called.
    nsignals = [0]

    def sigHandler(signo, frame):
        log.debug('Signal received - FSLeyes is shutting down...')

        # first signal - try to exit cleanly
        if nsignals[0] == 0:
            nsignals[0] += 1
            exitCode[0]  = signo

            # kill any modal windows
            # that are open
            for mdlg in app.modals:
                mdlg.EndModal(wx.ID_CANCEL)

            wx.CallAfter(app.ExitMainLoop)

        # subsequent signals - exit immediately
        else:
            sys.exit(signo)

    signal.signal(signal.SIGINT,  sigHandler)
    signal.signal(signal.SIGTERM, sigHandler)

    # Note: If no wx.Frame is created, the
    # wx.MainLoop call will exit immediately,
    # even if we have scheduled something via
    # wx.CallAfter. In this case, we have
    # already created the splash screen, so
    # all is well.
    wx.CallAfter(init, splash)

    # under mac, use appnope to make sure
    # we don't get put to sleep. This is
    # primarily for the jupyter notebook
    # integration - if the user is working
    # with a notebook in the web browser,
    # macos might put FSLeyes to sleep,
    # causing the kernel to become
    # unresponsive.
    try:
        import appnope
        appnope.nope()
    except ImportError:
        pass
    app.MainLoop()
    return exitCode[0]


def embed(mkFrame=True, **kwargs):
    """Initialise FSLeyes and create a :class:`.FSLeyesFrame`, when
    running within another application.

    .. note:: In most cases, this function must be called from the
              ``wx.MainLoop``.

    :arg mkFrame: Defaults to ``True``. If ``False``, FSLeyes is
                  initialised, but a :class:`.FSLeyesFrame` is not created.
                  If you set this to ``False``, you must ensure that a
                  ``wx.App`` object exists before calling this function.

    :returns:     A tuple containing:

                   - The :class:`.OverlayList`
                   - The master :class:`.DisplayContext`
                   - The :class:`.FSLeyesFrame` (or ``None``, if
                     ``makeFrame is False``).

    All other arguments are passed to :meth:`.FSLeyesFrame.__init__`.
    """

    import fsleyes_props          as props
    import fsleyes.gl             as fslgl
    import fsleyes.frame          as fslframe
    import fsleyes.overlay        as fsloverlay
    import fsleyes.displaycontext as fsldc

    # initialise must be called before
    # a FSLeyesApp gets created, as it
    # tries to access app_icon.png
    fsleyes.initialise()

    app    = wx.GetApp()
    ownapp = app is None

    if ownapp and (mkFrame is False):
        raise RuntimeError('If mkFrame is False, you '
                           'must create a wx.App before '
                           'calling fsleyes.main.embed')
    if ownapp:
        app = FSLeyesApp()

    colourmaps.init()
    props.initGUI()

    called = [False]
    ret    = [None]

    def until():
        return called[0]

    def ready():
        fslgl.bootstrap()

        overlayList = fsloverlay.OverlayList()
        displayCtx  = fsldc.DisplayContext(overlayList)

        if mkFrame:
            frame = fslframe.FSLeyesFrame(
                None, overlayList, displayCtx, **kwargs)
        else:
            frame = None

        if ownapp:
            app.SetOverlayListAndDisplayContext(overlayList, displayCtx)
            # Keep a ref to prevent the app from being GC'd
            frame._embed_app = app

        called[0] = True
        ret[0]    = (overlayList, displayCtx, frame)

    fslgl.getGLContext(ready=ready, raiseErrors=True)
    idle.block(10, until=until)

    if ret[0] is None:
        raise RuntimeError('Failed to start FSLeyes')
    return ret[0]


def initialise(splash, namespace, callback):
    """Called by :func:`main`. Bootstraps/Initialises various parts of
    *FSLeyes*.

    The ``callback`` function is asynchronously called when the initialisation
    is complete.

    :arg splash:    The :class:`.FSLeyesSplash` screen.

    :arg namespace: The ``argparse.Namespace`` object containing parsed
                    command line arguments.

    :arg callback:  Function which is called when initialisation is done.
    """

    import fsl.utils.settings as fslsettings
    import fsleyes_props      as props
    import fsleyes.gl         as fslgl

    props.initGUI()

    # The save/load directory defaults
    # to the current working directory.
    curDir = op.normpath(os.getcwd())

    fslsettings.write('loadSaveOverlayDir', curDir)

    # Initialise silly things
    if namespace.bumMode:
        import fsleyes.icons as icons
        icons.BUM_MODE = True

    # Set notebook server port
    fslsettings.write('fsleyes.notebook.port', namespace.notebookPort)

    # This is called by fsleyes.gl.getGLContext
    # when the GL context is ready to be used.
    def realCallback():
        fslgl.bootstrap(namespace.glversion)
        callback()

    try:
        # Force the creation of a wx.glcanvas.GLContext object,
        # and initialise OpenGL version-specific module loads.
        fslgl.getGLContext(ready=realCallback)

    except Exception:
        log.error('Unable to initialise OpenGL!', exc_info=True)
        splash.Destroy()
        sys.exit(1)


def shutdown(ev=None):
    """Called when FSLeyes exits normally (i.e. the user closes the window).
    Does some final clean-up before exiting.

    This function is used as a wxpython event handler, so it accepts an ``ev``
    arguments, but ignores its value.
    """

    if ev is not None:
        ev.Skip()

    import fsl.utils.settings as fslsettings
    import fsleyes.gl         as fslgl

    # Clear the cached directory for loading/saving
    # files - when FSLeyes starts up, we want it to
    # default to the current directory.
    fslsettings.delete('loadSaveOverlayDir')

    # Shut down the GL rendering context
    fslgl.shutdown()


def parseArgs(argv):
    """Parses the given ``fsleyes`` command line arguments. See the
    :mod:`.parseargs` module for details on the ``fsleyes`` command
    line interface.

    :arg argv: command line arguments for ``fsleyes``.
    """

    import fsleyes.parseargs as parseargs
    import fsleyes.layouts   as layouts
    import fsleyes.version   as version

    parser = parseargs.ArgumentParser(
        add_help=False,
        formatter_class=parseargs.FSLeyesHelpFormatter)

    serveraction = ft.partial(cliserver.CLIServerAction, allArgs=argv)

    parser.add_argument('-r', '--runscript',
                        metavar='SCRIPTFILE',
                        help='Run custom FSLeyes script')
    parser.add_argument('-cs', '--cliserver',
                        action=serveraction,
                        help='Pass all command-line arguments '
                             'to a single FSLeyes instance')

    # We include the list of available
    # layouts in the help description
    allLayouts  = list(layouts.BUILT_IN_LAYOUTS.keys()) + \
                  list(layouts.getAllLayouts())
    name        = 'fsleyes'
    prolog      = 'FSLeyes version {}\n'.format(version.__version__)
    description = textwrap.dedent("""\
        FSLeyes - the FSL image viewer.

        Use the '--scene' option to load a saved layout ({layouts}).

        If no '--scene' is specified, a default layout is shown or the
        previous layout is restored. If a script is provided via
        the '--runscript' argument, it is assumed that the script sets
        up the scene.
        """.format(layouts=', '.join(allLayouts)))

    # Options for configuring the scene are
    # managed by the parseargs module
    return parseargs.parseArgs(parser,
                               argv,
                               name,
                               prolog=prolog,
                               desc=description,
                               argOpts=['-r', '--runscript'])


def makeDisplayContext(namespace, splash):
    """Creates the top-level *FSLeyes* :class:`.DisplayContext` and
    :class:`.OverlayList` .

    This function does the following:

     1. Creates the :class:`.OverlayList` and the top level
        :class:`.DisplayContext`.

     2. Loads and configures all of the overlays which were passed in on the
        command line.

    :arg namesace: Parsed command line arguments (see :func:`parseArgs`).

    :arg splash:   The :class:`.FSLeyesSplash` frame, created in :func:`init`.

    :returns: a tuple containing:
                - the :class:`.OverlayList`
                - the master :class:`.DisplayContext`
    """

    import fsleyes_widgets.utils.status as status
    import fsleyes.overlay              as fsloverlay
    import fsleyes.parseargs            as parseargs
    import fsleyes.displaycontext       as displaycontext

    # Splash status update must be
    # performed on the main thread.
    def splashStatus(msg):
        wx.CallAfter(splash.SetStatus, msg)

    # Redirect status updates
    # to the splash frame
    status.setTarget(splashStatus)

    # Create the overlay list (only one of these
    # ever exists) and the master DisplayContext.
    # A new DisplayContext instance will be
    # created for every new view that is opened
    # in the FSLeyesFrame, but all child
    # DisplayContext instances will be linked to
    # this master one.
    overlayList = fsloverlay.OverlayList()
    displayCtx  = displaycontext.DisplayContext(overlayList)

    log.debug('Created overlay list and master DisplayContext ({})'.format(
        id(displayCtx)))

    # Load the images - the splash screen status will
    # be updated with the currently loading overlay name.
    parseargs.applyMainArgs(   namespace, overlayList, displayCtx)
    parseargs.applyOverlayArgs(namespace, overlayList, displayCtx)

    return overlayList, displayCtx


def makeFrame(namespace, displayCtx, overlayList, splash, closeHandlers):
    """Creates the *FSLeyes* interface.

    This function does the following:

     1. Creates the :class:`.FSLeyesFrame` the top-level frame for ``fsleyes``.

     2. Configures the frame according to the command line arguments (e.g.
        ortho or lightbox view).

     3. Destroys the splash screen that was created by the :func:`context`
        function.

    :arg namespace:     Parsed command line arguments, as returned by
                        :func:`parseArgs`.

    :arg displayCtx:    The  :class:`.DisplayContext`, as created and returned
                        by :func:`makeDisplayContext`.

    :arg overlayList:   The :class:`.OverlayList`, as created and returned by
                        :func:`makeDisplayContext`.

    :arg splash:        The :class:`.FSLeyesSplash` frame.

    :arg closeHandlers: List of event handlers to be called when the
                        ``FSLeyesFrame`` closes.

    :returns: the :class:`.FSLeyesFrame` that was created.
    """

    import fsl.utils.idle                        as idle
    import fsleyes_widgets.utils.status          as status
    import fsleyes.parseargs                     as parseargs
    import fsleyes.frame                         as fsleyesframe
    import fsleyes.displaycontext                as fsldisplay
    import fsleyes.layouts                       as layouts
    import fsleyes.views.canvaspanel             as canvaspanel
    import fsleyes.views.orthopanel              as orthopanel
    import fsleyes.plugins.tools.saveannotations as saveannotations

    # Set up the frame scene (a.k.a. layout)
    # The scene argument can be:
    #
    #   - The name of a saved (or built-in) layout
    #
    #   - None, in which case the default or previous
    #     layout is restored, unless a custom script
    #     has been provided.
    script = namespace.runscript
    scene  = namespace.scene

    # If a scene/layout or custom script
    # has not been specified, the default
    # behaviour is to restore the previous
    # frame layout.
    restore = (scene is None) and (script is None)

    status.update('Creating FSLeyes interface...')

    frame = fsleyesframe.FSLeyesFrame(
        None,
        overlayList,
        displayCtx,
        restore,
        True,
        fontSize=namespace.fontSize,
        closeHandlers=closeHandlers)

    # Allow files to be dropped
    # onto FSLeyes to open them
    dt = fsleyesframe.OverlayDropTarget(overlayList, displayCtx)
    frame.SetDropTarget(dt)

    # Make sure the new frame is shown
    # before destroying the splash screen
    frame.Show(True)
    frame.Refresh()
    frame.Update()

    # In certain instances under Linux/GTK,
    # closing the splash screen will crash
    # the application. No idea why. So we
    # leave the splash screen hidden, but
    # not closed, and close it when the main
    # frame is closed. This also works under
    # OSX.
    splash.Hide()
    splash.Refresh()
    splash.Update()

    def onFrameDestroy(ev):
        ev.Skip()

        # splash screen may already
        # have been destroyed
        try:              splash.Close()
        except Exception: pass

    frame.Bind(wx.EVT_WINDOW_DESTROY, onFrameDestroy)

    status.update('Setting up scene...')

    # Set the default SceneOpts.performance
    # level so that all created SceneOpts
    # instances will default to it
    if namespace.performance is not None:
        fsldisplay.SceneOpts.performance.setAttribute(
            None, 'default', namespace.performance)

    # If a layout has been specified,
    # we load the layout
    if namespace.scene is not None:
        layouts.loadLayout(frame, namespace.scene)

    # Apply any view-panel specific arguments
    viewPanels = frame.viewPanels
    for viewPanel in viewPanels:

        if not isinstance(viewPanel, canvaspanel.CanvasPanel):
            continue

        displayCtx = viewPanel.displayCtx
        viewOpts   = viewPanel.sceneOpts

        parseargs.applySceneArgs(
            namespace, overlayList, displayCtx, viewOpts)

    # If an annotations file has eben specified,
    # and an ortho view was opened, load the
    # annotations file, and apply it to the
    # first ortho view
    orthos = [vp for vp in viewPanels if isinstance(vp, orthopanel.OrthoPanel)]
    if namespace.annotations is not None and len(orthos) > 0:
        try:
            saveannotations.loadAnnotations(orthos[0], namespace.annotations)
        except Exception as e:
            log.warning('Error loading annotations from %s: %s',
                        namespace.annotations, e, exc_info=True)

    # If a script has been specified, we run
    # the script. This has to be done on the
    # idle loop, because overlays specified
    # on the command line are loaded on the
    # idle loop. Therefore, if we schedule the
    # script on idle (which is a queue), the
    # script can assume that all overlays have
    # already been loaded.
    from fsleyes.actions.runscript import RunScriptAction
    if script is not None:
        idle.idle(frame.menuActions[RunScriptAction], script)

    return frame


def fslDirWarning(parent):
    """Checks to see if the ``$FSLDIR`` environment variable is set, or
    if a FSL installation directory has been saved previously. If not,
    displays a warning via a :class:`.FSLDirDialog`.

    :arg parent: A ``wx`` parent object.
    """

    if fslplatform.fsldir is not None:
        return

    import fsl.utils.settings as fslsettings

    # Check settings before
    # prompting the user
    fsldir = fslsettings.read('fsldir')

    if fsldir is not None:
        fslplatform.fsldir = fsldir
        return

    from fsleyes_widgets.dialog import FSLDirDialog

    dlg = FSLDirDialog(parent, 'FSLeyes', fslplatform.os == 'Darwin')

    if dlg.ShowModal() == wx.ID_OK:

        fsldir = dlg.GetFSLDir()

        log.debug('Setting $FSLDIR to {} (specified '
                  'by user)'.format(fsldir))

        fslplatform.fsldir        = fsldir
        fslsettings.write('fsldir', fsldir)


if __name__ == '__main__':
    main()
