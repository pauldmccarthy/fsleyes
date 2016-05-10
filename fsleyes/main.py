#!/usr/bin/env python
#
# fsleyes.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the entry point to *FSLeyes*, the FSL image viewer.  

See the :mod:`fsleyes` package documentation for more details on ``fsleyes``.
"""


from __future__ import print_function

import wx

import os.path as op
import sys
import time
import logging
import warnings
import textwrap
import argparse
import threading

from fsl.utils.platform import platform as fslplatform
import fsleyes


# The logger is assigned in 
# the configLogging function
log = None


def main(args=None):
    """*FSLeyes* entry point. Shows a :class:`.FSLeyesSplash` screen, parses
    command line arguments, and shows a :class:`.FSLeyesFrame`.
    """
    
    if args is None:
        args = sys.argv[1:]

    # First thing's first. Create a wx.App, 
    # and figure out where all our stuff is.
    app = wx.App()
    app.SetAppName('FSLeyes')
 
    # If we are running from a bundled application,
    # the FSLeyes resources might not be alongside
    # the python source code.
    if fslplatform.frozen:
        sp       = wx.StandardPaths.Get()
        assetDir = op.join(sp.GetResourcesDir())
        
    # Otherwise we assume that the resources
    # are living alongside the FSLeyes source.
    else:
        assetDir = op.join(op.dirname(__file__), '..')

    fsleyes.assetDir = op.abspath(assetDir)

    # Show the splash screen as soon as
    # possible, unless it looks like the
    # user is asking for the software
    # version or command line help.
    splash = makeSplash()
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
    # loop - this is important for FSLEyes,
    # which displays status updates to the
    # user while it is loading overlays and
    # setting up the interface.
    # 
    # To make this work, this buildGUI
    # function is called on a separate thread
    # (so it is executed after wx.MainLoop
    # has been called), but it schedules its
    # work to be done on the wx.MainLoop. 
    def buildGUI(splash):

        def realBuild(splash):

            # Parse command line arguments
            namespace = parseArgs(args)

            # Make sure the splash screen is
            # visible - it probably is if we
            # got this far, but just to be sure.
            splash.Show()
            
            # Initialise sub-modules/packages
            initialise(splash, namespace)

            # Configure logging (this has to be done
            # after cli arguments have been parsed)
            configLogging(namespace)

            # Now the main stuff - create the overlay
            # list and the master display context,
            # and then create the FSLEyesFrame.
            overlayList, displayCtx = makeDisplayContext(namespace, splash)
            frame = makeFrame(namespace, displayCtx, overlayList, splash)

            app.SetTopWindow(frame)
            frame.Show()

            # Check that $FSLDIR is set, complain 
            # to the user if it isn't
            if not namespace.skipfslcheck:
                wx.CallAfter(fslDirWarning, frame)

        # Sleep a bit so the main thread (on which
        # wx.MainLoop is running) can start. 
        time.sleep(0.05)
        wx.CallAfter(realBuild, splash)

    threading.Thread(target=buildGUI, args=[splash]).start()
    app.MainLoop()


def initialise(splash, namespace):
    """Called by :func:`main`. Bootstraps/Initialises various parts of
    *FSLeyes*.
    """

    import                       props
    import fsleyes.gl         as fslgl
    import fsleyes.colourmaps as colourmaps

    props.initGUI()

    colourmaps.init()

    # Force the creation of a wx.glcanvas.GLContext object,
    # and initialise OpenGL version-specific module loads.
    # The splash screen is used as the parent of the dummy
    # canvas created by the gl.getWXGLContext function.
    try:
        fslgl.getWXGLContext(splash)
        fslgl.bootstrap(namespace.glversion)
        
    except:
        log.error('Unable to initialise OpenGL!', exc_info=True)
        splash.Destroy()
        sys.exit(1)
    

def parseArgs(argv):
    """Parses the given ``fsleyes`` command line arguments. See the
    :mod:`.fsleyes_parseargs` module for details on the ``fsleyes`` command
    line interface.
    
    :arg argv: command line arguments for ``fsleyes``.
    """

    import fsleyes.parseargs as parseargs
    import fsleyes.version   as version

    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=parseargs.FSLEyesHelpFormatter)

    parser.add_argument('-r', '--runscript',
                        metavar='SCRIPTFILE',
                        help='Run custom FSLeyes script')

    # TODO Dynamically generate perspective list
    # in description. To do this, you will need
    # to make fsl.utils.settings work without a
    # wx.App (so we can retrieve the perspective
    # list before the GUI is created).
    name        = 'fsleyes'
    prolog      = 'FSLeyes version {}\n'.format(version.__version__)
    description = textwrap.dedent("""\
        FSLeyes - the FSL image viewer.
        
        Use the '--scene' option to load a saved perspective (e.g. 'default',
        'melodic', 'feat', 'ortho', or 'lightbox').
        
        If no '--scene' is specified, the previous layout is restored, unless
        a script is provided via the '--runscript' argument, in which case
        it is assumed that the script sets up the scene, so the previous
        layout is not restored.
        """)

    # Options for configuring the scene are
    # managed by the fsleyes_parseargs module
    return parseargs.parseArgs(parser,
                               argv,
                               name,
                               prolog=prolog,
                               desc=description,
                               fileOpts=['r', 'runscript'])


def makeSplash():
    """Creates and returns a :class:`.FSLEyesSplash` frame. """
    
    import fsleyes.splash as fslsplash

    frame = fslsplash.FSLEyesSplash(None)

    frame.CentreOnScreen()
    frame.Show()
    frame.Refresh()
    frame.Update()

    return frame


def configLogging(namespace):
    """Configures *FSLeyes* ``logging``.

    .. note:: All logging calls are usually stripped from frozen
              versions of *FSLeyes*, so this function does nothing
              when we are running a frozen version.
    """

    global log
    
    # make numpy/matplotlib quiet
    warnings.filterwarnings('ignore', module='matplotlib')
    warnings.filterwarnings('ignore', module='mpl_toolkits')
    warnings.filterwarnings('ignore', module='numpy')

    # Set up my own custom logging level
    # for tracing memory related events.
    logging.MEMORY = 15
    def _logmemory(self, message, *args, **kwargs):
        """Log function for my custom ``logging.MEMORY`` logging level. """
        if self.isEnabledFor(logging.MEMORY):
            self._log(logging.MEMORY, message, args, **kwargs)

    logging.Logger.memory = _logmemory
    logging.addLevelName(logging.MEMORY, 'MEMORY') 

    # Set up the root logger
    logFormatter = logging.Formatter('%(levelname)8.8s '
                                     '%(filename)20.20s '
                                     '%(lineno)4d: '
                                     '%(funcName)-15.15s - '
                                     '%(message)s')
    logHandler  = logging.StreamHandler()
    logHandler.setFormatter(logFormatter)
    
    log = logging.getLogger()
    log.addHandler(logHandler)

    # Everything below this point sets up verbosity
    # as requested by the user. But verbosity-related
    # command line arguments are not exposed to the
    # user in frozen versions of FSLeyes, so if we're
    # running as a frozen app, there's nothing else
    # to do.
    if fslplatform.frozen:
        return

    # Now we can set up logging
    # as requested by the user.
    if namespace.noisy is None:
        namespace.noisy = []

    if namespace.verbose is None:
        if namespace.memory:
            class MemFilter(object):
                def filter(self, record):
                    if   record.name in namespace.noisy:   return 1
                    elif record.levelno == logging.MEMORY: return 1
                    else:                                  return 0

            log.setLevel(logging.MEMORY)
            log.handlers[0].addFilter(MemFilter())
            log.memory('Added filter for MEMORY messages')
            logging.getLogger('props')   .setLevel(logging.WARNING)
            logging.getLogger('pwidgets').setLevel(logging.WARNING)            
        
    if namespace.verbose == 1:
        log.setLevel(logging.DEBUG)

        # make some noisy things quiet
        logging.getLogger('fsleyes.gl')   .setLevel(logging.MEMORY)
        logging.getLogger('fsleyes.views').setLevel(logging.MEMORY)
        logging.getLogger('props')        .setLevel(logging.WARNING)
        logging.getLogger('pwidgets')     .setLevel(logging.WARNING)
    elif namespace.verbose == 2:
        log.setLevel(logging.DEBUG)
        logging.getLogger('props')   .setLevel(logging.WARNING)
        logging.getLogger('pwidgets').setLevel(logging.WARNING)
    elif namespace.verbose == 3:
        log.setLevel(logging.DEBUG)
        logging.getLogger('props')   .setLevel(logging.DEBUG)
        logging.getLogger('pwidgets').setLevel(logging.DEBUG)

    for mod in namespace.noisy:
        logging.getLogger(mod).setLevel(logging.DEBUG)

    # The trace module monkey-patches some
    # things if its logging level has been
    # set to DEBUG, so we import it now so
    # it can set itself up.
    traceLogger = logging.getLogger('props.trace')
    if traceLogger.getEffectiveLevel() <= logging.DEBUG:
        import props.trace


def makeDisplayContext(namespace, splash):
    """Creates the top-level *FSLeyes* :class:`.DisplayContext` and
    :class:`.OverlayList` .

    This function does a few things:

     1. Initialises OpenGL (see the :mod:`fsleyes.gl` package).

     2. Creates the :class:`.OverlayList` and the top level
        :class:`.DisplayContext`.

     3. Loads all of the overlays which were passed in on the command line.

    :arg namesace: Parsed command line arguments (see :func:`parseArgs`).

    :arg splash:   The :class:`.FSLEyesSplash` frame, created in :func:`init`.

    :returns: a tuple containing:
                - the :class:`.OverlayList`
                - the master :class:`.DisplayContext`
    """

    import fsl.utils.status       as status
    import fsleyes.overlay        as fsloverlay
    import fsleyes.parseargs      as parseargs
    import fsleyes.displaycontext as displaycontext

    # Redirect status updates
    # to the splash frame
    status.setTarget(splash.SetStatus)

    # Create the overlay list (only one of these
    # ever exists) and the master DisplayContext.
    # A new DisplayContext instance will be
    # created for every new view that is opened
    # in the FSLEyesFrame, but all child
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
    # be updated with the currently loading overlay name
    parseargs.applyOverlayArgs(namespace, overlayList, displayCtx) 

    return overlayList, displayCtx


def makeFrame(namespace, displayCtx, overlayList, splash):
    """Creates the *FSLeyes* interface.

    This function does the following:

     1. Creates the :class:`.FSLEyesFrame` the top-level frame for ``fsleyes``.

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

    :returns: the :class:`.FSLEyesFrame` that was created.
    """

    import fsl.utils.status       as status
    import fsl.utils.async        as async
    import fsleyes.parseargs      as parseargs
    import fsleyes.frame          as fsleyesframe
    import fsleyes.displaycontext as fsldisplay
    import fsleyes.perspectives   as perspectives
    import fsleyes.views          as views
    
    # Set up the frame scene (a.k.a. layout, perspective)
    # The scene argument can be:
    #
    #   - 'lightbox' or 'ortho', specifying a single view
    #      panel to display.
    # 
    #   - The name of a saved (or built-in) perspective
    # 
    #   - None, in which case the previous layout is restored,
    #     unless a custom script has been provided.
    script = namespace.runscript 
    scene  = namespace.scene

    # If a scene/perspective or custom script
    # has not been specified, the default
    # behaviour is to restore the previous
    # frame layout. 
    restore = (scene is None) and (script is None)

    status.update('Creating FSLeyes interface...')
    
    frame = fsleyesframe.FSLEyesFrame(
        None, overlayList, displayCtx, restore, True)

    # Make sure the new frame is shown
    # before destroying the splash screen
    frame.Show(True)
    frame.Refresh()
    frame.Update()

    # Closing the splash screen immediately
    # can cause a crash under linux/GTK, so
    # we'll hide it now, and destroy it later.
    splash.Hide()
    splash.Refresh()
    splash.Update()

    # In certain instances under Linux/GTK,
    # closing the splash screen will crash
    # the application. No idea why. So if
    # running GTK, we leave the splash
    # screen hidden, but not closed, and
    # close it when the main frame is
    # closed.
    if fslplatform.wxPlatform == fslplatform.WX_GTK:
        def onFrameDestroy(ev):
            ev.Skip()
            splash.Close()
        frame.Bind(wx.EVT_WINDOW_DESTROY, onFrameDestroy)
    else:
        wx.CallLater(250, splash.Close)

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

        if not isinstance(viewPanel, views.CanvasPanel):
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

        if isinstance(viewPanel, views.OrthoPanel):
            async.idle(centre)

    # If a script has been specified, we run
    # the script. This has to be done on the
    # idle loop, because overlays specified
    # on the command line are loaded on the
    # idle loop, and the script may assume
    # that they have already been loaded.
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

    # Check fslpy settings before
    # prompting the user
    fsldir = fslsettings.read('fsldir')

    if fsldir is not None:
        fslplatform.fsldir = fsldir
        return

    from fsl.utils.dialog import FSLDirDialog

    dlg = FSLDirDialog(parent, 'FSLeyes')
        
    if dlg.ShowModal() == wx.ID_OK:
            
        fsldir = dlg.GetFSLDir()
            
        log.debug('Setting $FSLDIR to {} (specified '
                  'by user)'.format(fsldir))

        fslplatform.fsldir        = fsldir
        fslsettings.write('fsldir', fsldir)


if __name__ == '__main__':
    main()
