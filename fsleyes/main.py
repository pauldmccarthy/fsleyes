#!/usr/bin/env python
#
# fsleyes.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the entry point to *FSLeyes*, the FSL image viewer.

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


import            os
import os.path as op
import            sys
import            textwrap
import            argparse
import            logging

import wx

from fsl.utils.platform import platform as fslplatform

import                   fsleyes
import fsleyes.splash as fslsplash


log = logging.getLogger(__name__)


class FSLeyesApp(wx.App):
    """FSLeyes-specific sub-class of ``wx.App``. """

    def __init__(self, *args, **kwargs):
        """Create a ``FSLeyesApp``. """

        self.__overlayList = None
        self.__displayCtx  = None

        wx.App.__init__(self, *args, **kwargs)

        self.SetAppName('FSLeyes')


    def SetOverlayListAndDisplayContext(self, overlayList, displayCtx):
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


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

        if self.__overlayList is None:
            return

        import fsleyes.actions.loadoverlay as loadoverlay
        import fsleyes.autodisplay         as autodisplay

        def onLoad(overlays):

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
    command line arguments, and shows a :class:`.FSLeyesFrame`.
    """

    if args is None:
        args = sys.argv[1:]

    # Hack to allow render to
    # be called via fsleyes.main
    if len(args) >= 1 and args[0] == 'render':
        import fsleyes.render as render
        render.main(args[1:])
        sys.exit(0)

    # Implement various hacks and workarounds
    hacksAndWorkarounds()

    # Then, first thing's first. Create a wx.App,
    # and initialise the FSLeyes package.
    app = FSLeyesApp()
    fsleyes.initialise()

    # Show the splash screen as soon as
    # possible, unless it looks like the
    # user is asking for the software
    # version or command line help.
    splash = fslsplash.FSLeyesSplash(None)

    if (len(args) > 0) and (args[0] in ('-V',
                                        '-h',
                                        '-fh',
                                        '--version',
                                        '--help',
                                        '--fullhelp')):
        splash.Hide()

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

    # This is a container, shared amongst
    # the callbacks, which contains the
    # parsed argparse.Namespace object.
    namespace = [None]

    def init(splash):

        # Parse command line arguments. If the
        # user has asked for help (see above),
        # the parseargs module will raise
        # SystemExit. Hence we make sure the
        # splash screen is shown only after
        # arguments have been parsed.
        try:
            namespace[0] = parseArgs(args)

        # But the wx.App.MainLoop eats SystemExit
        # exceptions for unknown reasons, and
        # and causes the application to exit
        # immediately. This makes testing FSLeyes
        # (e.g. code coverage) impossible. So I'm
        # catching SystemExit here, and then
        # telling the wx.App to exit gracefully.
        except SystemExit:
            app.ExitMainLoop()
            return

        # See FSLeyesSplash.Show
        # for horribleness.
        splash.Show()

        # Configure logging (this has to be done
        # after cli arguments have been parsed,
        # but before initialise is called).
        fsleyes.configLogging(namespace[0])

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
        frame = makeFrame(namespace[0], displayCtx, overlayList, splash)

        app.SetTopWindow(frame)
        frame.Show()

        # Check that $FSLDIR is set, complain
        # to the user if it isn't
        if not namespace[0].skipfslcheck:
            wx.CallAfter(fslDirWarning, frame)

        # Check for updates. Ignore point
        # releases, otherwise users might
        # get swamped with update notifications.
        if not namespace[0].skipupdatecheck:
            import fsleyes.actions.updatecheck as updatecheck
            wx.CallAfter(updatecheck.UpdateCheckAction(),
                         showUpToDateMessage=False,
                         showErrorMessage=False,
                         ignorePoint=True)

    # Note: If no wx.Frame is created, the
    # wx.MainLoop call will exit immediately,
    # even if we have scheduled something via
    # wx.CallAfter. In this case, we have
    # already created the splash screen, so
    # all is well.
    wx.CallAfter(init, splash)
    app.MainLoop()
    shutdown()


def hacksAndWorkarounds():
    """Called by :func:`main`. Implements hacks and workarounds for
    various things.
    """

    # Under wxPython/Phoenix, the
    # wx.html package must be imported
    # before a wx.App has been created
    import wx.html

    # PyInstaller 3.2.1 forces matplotlib to use a
    # temporary directory for its settings and font
    # cache, and then deletes the directory on exit.
    # This is silly, because the font cache can take
    # a long time to create.  Clearing the environment
    # variable should cause matplotlib to use
    # $HOME/.matplotlib (or, failing that, a temporary
    # directory).
    #
    # https://matplotlib.org/faq/environment_variables_faq.html#\
    #   envvar-MPLCONFIGDIR
    #
    # https://github.com/pyinstaller/pyinstaller/blob/v3.2.1/\
    #   PyInstaller/loader/rthooks/pyi_rth_mplconfig.py
    #
    # n.b. This will cause issues if building FSLeyes
    #      with the pyinstaller '--onefile' option, as
    #      discussed in the above pyinstaller file.
    if fslplatform.frozen:
        os.environ.pop('MPLCONFIGDIR', None)

    # OSX sometimes sets the local environment
    # variables to non-standard values, which
    # breaks the python locale module.
    #
    # http://bugs.python.org/issue18378
    try:
        import locale
        locale.getdefaultlocale()
    except:
        os.environ['LC_ALL'] = 'C.UTF-8'


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
    import fsleyes.colourmaps as colourmaps

    props.initGUI()

    colourmaps.init()

    # The save/load directory defaults
    # to the current working directory.
    curDir = op.normpath(os.getcwd())

    # But if we are running as a frozen application, check to
    # see if FSLeyes has been started by the system (e.g.
    # double-clicking instead of being called from the CLI).
    #
    # If so, we set the save/load directory
    # to the user's home directory instead.
    if fslplatform.frozen:

        fsleyesDir = op.dirname(__file__)

        # If we're a frozen OSX application,
        # we need to adjust the FSLeyes dir
        # (which will be:
        #   [install_dir]/FSLeyes.app/Contents/MacOS/fsleyes/),
        #
        # Because the cwd will default to:
        #   [install_dir/

        if fslplatform.os == 'Darwin':

            fsleyesDir = op.normpath(op.join(fsleyesDir,
                                             '..', '..', '..', '..'))

        # Similar adjustment for linux
        elif fslplatform.os == 'Linux':
            fsleyesDir = op.normpath(op.join(fsleyesDir, '..'))

        if curDir == fsleyesDir:
            curDir = op.expanduser('~')

    fslsettings.write('loadSaveOverlayDir', curDir)

    # Initialise silly things
    if namespace.bumMode:
        import fsleyes.controls.orthotoolbar    as ot
        import fsleyes.controls.lightboxtoolbar as lbt
        ot .BUM_MODE = True
        lbt.BUM_MODE = True

    # This is called by fsleyes.gl.getGLContext
    # when the GL context is ready to be used.
    def realCallback():
        fslgl.bootstrap(namespace.glversion)
        callback()

    try:
        # Force the creation of a wx.glcanvas.GLContext object,
        # and initialise OpenGL version-specific module loads.
        # The splash screen is used as the parent of the dummy
        # canvas created by the gl.getWXGLContext function.
        fslgl.getGLContext(parent=splash, ready=realCallback)

    except:
        log.error('Unable to initialise OpenGL!', exc_info=True)
        splash.Destroy()
        sys.exit(1)


def shutdown():
    """Called when FSLeyes exits normally (i.e. the user closes the window).
    Does some final clean-up before exiting.
    """

    import fsl.utils.settings as fslsettings

    # Clear the cached directory for loading/saving
    # files - when FSLeyes starts up, we want it to
    # default to the current directory.
    fslsettings.delete('loadSaveOverlayDir')


def parseArgs(argv):
    """Parses the given ``fsleyes`` command line arguments. See the
    :mod:`.parseargs` module for details on the ``fsleyes`` command
    line interface.

    :arg argv: command line arguments for ``fsleyes``.
    """

    import fsleyes.parseargs    as parseargs
    import fsleyes.perspectives as perspectives
    import fsleyes.version      as version

    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=parseargs.FSLeyesHelpFormatter)

    parser.add_argument('-r', '--runscript',
                        metavar='SCRIPTFILE',
                        help='Run custom FSLeyes script')

    # We include the list of available
    # perspectives in the help description
    persps      = list(perspectives.BUILT_IN_PERSPECTIVES.keys()) + \
                  list(perspectives.getAllPerspectives())
    name        = 'fsleyes'
    prolog      = 'FSLeyes version {}\n'.format(version.__version__)
    description = textwrap.dedent("""\
        FSLeyes - the FSL image viewer.

        Use the '--scene' option to load a saved perspective ({persps}).

        If no '--scene' is specified, the previous layout is restored, unless
        a script is provided via the '--runscript' argument, in which case
        it is assumed that the script sets up the scene, so the previous
        layout is not restored.
        """.format(persps=', '.join(persps)))

    # Options for configuring the scene are
    # managed by the parseargs module
    return parseargs.parseArgs(parser,
                               argv,
                               name,
                               prolog=prolog,
                               desc=description,
                               argOpts=['r', 'runscript'])


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

    # While the DisplayContext may refer to
    # multiple overlay groups, we are currently
    # using just one, allowing the user to specify
    # a set of overlays for which their display
    # properties are 'locked'.
    lockGroup   = displaycontext.OverlayGroup(displayCtx, overlayList)
    displayCtx.overlayGroups.append(lockGroup)

    log.debug('Created overlay list and master DisplayContext ({})'.format(
        id(displayCtx)))

    # Load the images - the splash screen status will
    # be updated with the currently loading overlay name.
    #
    # The applyOverlayArgs function gets called before
    # the applySceneArgs function, so we'll manually
    # apply some important settings to the DC here so
    # they get used when any overlays are loaded.
    if namespace.bigmem is not None:
        displayCtx.loadInMemory = namespace.bigmem
    if namespace.autoDisplay is not None:
        displayCtx.autoDisplay = namespace.autoDisplay

    parseargs.applyOverlayArgs(namespace, overlayList, displayCtx)

    return overlayList, displayCtx


def makeFrame(namespace, displayCtx, overlayList, splash):
    """Creates the *FSLeyes* interface.

    This function does the following:

     1. Creates the :class:`.FSLeyesFrame` the top-level frame for ``fsleyes``.

     2. Configures the frame according to the command line arguments (e.g.
        ortho or lightbox view).

     3. Destroys the splash screen that was created by the :func:`context`
        function.

    :arg namespace:   Parsed command line arguments, as returned by
                      :func:`parseArgs`.

    :arg displayCtx:  The  :class:`.DisplayContext`, as created and returned
                      by :func:`makeDisplayContext`.

    :arg overlayList: The :class:`.OverlayList`, as created and returned by
                      :func:`makeDisplayContext`.

    :arg splash:      The :class:`.FSLeyesSplash` frame.

    :returns: the :class:`.FSLeyesFrame` that was created.
    """

    import fsl.utils.async              as async
    import fsleyes_widgets.utils.status as status
    import fsleyes.parseargs            as parseargs

    # The fsleyes.actions.frameactions module
    # monkey-patches some things into the
    # FSLeyesFrame class, so it must be
    # imported immediately after fsleyes.frame.
    import fsleyes.frame                as fsleyesframe
    import fsleyes.actions.frameactions as frameactions

    import fsleyes.displaycontext       as fsldisplay
    import fsleyes.perspectives         as perspectives
    import fsleyes.views.canvaspanel    as canvaspanel
    import fsleyes.views.orthopanel     as orthopanel

    # Set up the frame scene (a.k.a. layout, perspective)
    # The scene argument can be:
    #
    #   - The name of a saved (or built-in) perspective
    #
    #   - None, in which case the default or previous
    #     layout is restored, unless a custom script
    #     has been provided.
    script = namespace.runscript
    scene  = namespace.scene

    # If a scene/perspective or custom script
    # has not been specified, the default
    # behaviour is to restore the previous
    # frame layout.
    restore = (scene is None) and (script is None)

    status.update('Creating FSLeyes interface...')

    frame = fsleyesframe.FSLeyesFrame(
        None, overlayList, displayCtx, restore, True)

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
        splash.Close()
    frame.Bind(wx.EVT_WINDOW_DESTROY, onFrameDestroy)

    status.update('Setting up scene...')

    # Set the default SceneOpts.performance
    # level so that all created SceneOpts
    # instances will default to it
    if namespace.performance is not None:
        fsldisplay.SceneOpts.performance.setConstraint(
            None, 'default', namespace.performance)

    # If a perspective has been specified,
    # we load the perspective
    if namespace.scene is not None:
        perspectives.loadPerspective(frame, namespace.scene)

    # Apply any view-panel specific arguments
    viewPanels = frame.getViewPanels()
    for viewPanel in viewPanels:

        if not isinstance(viewPanel, canvaspanel.CanvasPanel):
            continue

        displayCtx = viewPanel.getDisplayContext()
        viewOpts   = viewPanel.getSceneOptions()

        parseargs.applySceneArgs(
            namespace, overlayList, displayCtx, viewOpts)

        def centre(vp=viewPanel):
            xc, yc, zc = parseargs.calcCanvasCentres(namespace,
                                                     overlayList,
                                                     displayCtx)

            vp.getXCanvas().centreDisplayAt(*xc)
            vp.getYCanvas().centreDisplayAt(*yc)
            vp.getZCanvas().centreDisplayAt(*zc)

        if isinstance(viewPanel, orthopanel.OrthoPanel):
            async.idle(centre)

    # If a script has been specified, we run
    # the script. This has to be done on the
    # idle loop, because overlays specified
    # on the command line are loaded on the
    # idle loop. Therefore, if we schedule the
    # script on idle (which is a queue), the
    # script can assume that all overlays have
    # already been loaded.
    if script is not None:
        async.idle(frame.runScript, script)

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
