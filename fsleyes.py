#!/usr/bin/env python
#
# fsleyes.py - Image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""*FSLeyes* - a 3D image viewer.

.. image:: images/fsleyes.png
   :scale: 50%
   :align: center

This module provides the front-end to *FSLeyes*, the FSL image viewer.  Nearly
all of the ``fsleyes`` functionality is located in the :mod:`fsl.fsleyes`
package. This module just parses command line arguments (via the
:mod:`.fsleyes_parseargs` module) and does some GUI bootstrapping necessities.


See the :mod:`~fsl.fsleyes` package documentation for more details on
``fsleyes``.
"""


from __future__ import print_function

import sys
import logging
import textwrap
import argparse

import fsl.fsleyes.perspectives           as perspectives
import fsl.fsleyes.strings                as strings
import fsl.utils.status                   as status
import fsl.utils.async                    as async
from   fsl.utils.platform import platform as fslplatform


log = logging.getLogger(__name__)


def init():
    """Creates and returns a :class:`.FSLEyesSplash` frame. """

    import fsl.fsleyes.splash as fslsplash

    frame = fslsplash.FSLEyesSplash(None)

    frame.CentreOnScreen()
    frame.Show()
    frame.Refresh()
    frame.Update()

    return frame


def parseArgs(argv):
    """Parses the given ``fsleyes`` command line arguments. See the
    :mod:`.fsleyes_parseargs` module for details on the ``fsleyes`` command
    line interface.
    
    :arg argv: command line arguments for ``fsleyes``.
    """

    import fsl.fsleyes.fsleyes_parseargs as fsleyes_parseargs

    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-r', '--runscript',
                        metavar='SCRIPTFILE',
                        help='Run custom FSLeyes script')

    # TODO Dynamically generate perspective list
    # in description. To do this, you will need
    # to make fsl.utils.settings work without a
    # wx.App (so we can retrieve the perspective
    # list before the GUI is created).
    name        = 'fsleyes'
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
    return fsleyes_parseargs.parseArgs(parser,
                                       argv,
                                       name,
                                       description,
                                       fileOpts=['r', 'runscript'])


def context(args, splash):
    """Creates the ``fsleyes`` context.

    This function does a few things:

     1. Displays the ``fsleyes`` splash screen (see
        :class:`.FSLEyesSplash`). The splash screen is destroyed later on by
        the :func:`interface` function.

     2. Initialises OpenGL (see the :mod:`fsl.fsleyes.gl` package).

     3. Creates the :class:`.OverlayList` and the top level
        :class:`.DisplayContext`.

     4. Loads all of the overlays which were passed in on the command line.

    :arg args:   Parsed command line arguments (see :func:`parseArgs`).

    :arg splash: The :class:`.FSLEyesSplash` frame, created in :func:`init`.

    :returns: a tuple containing:
                - the :class:`.OverlayList`
                - the master :class:`.DisplayContext`
                - the :class:`.FSLEyesSplash` frame
    """

    import fsl.fsleyes.overlay           as fsloverlay
    import fsl.fsleyes.fsleyes_parseargs as fsleyes_parseargs
    import fsl.fsleyes.displaycontext    as displaycontext
    import fsl.fsleyes.gl                as fslgl
    import props
    
    props.initGUI()

    # The splash screen is used as the parent of the dummy
    # canvas created by the gl.getWXGLContext function; the
    # splash screen frame is returned by this function, and
    # passed through to the interface function below, which
    # takes care of destroying it.    
    
    # force the creation of a wx.glcanvas.GLContext object,
    # and initialise OpenGL version-specific module loads.
    try:
        fslgl.getWXGLContext(splash)
        fslgl.bootstrap(args.glversion)
        
    except:
        log.error('Unable to initialise OpenGL!', exc_info=True)
        splash.Destroy()
        sys.exit(1)

    # Redirect status updates
    # to the splash frame
    status.setTarget(splash.SetStatus)

    # Create the overlay list (only one of these
    # ever exists) and the master DisplayContext.
    # A new DisplayContext instance will be
    # created for every new view that is opened
    # in the FSLEyesFrame (which is created in
    # the interface function, above), but all
    # child DisplayContext instances will be
    # linked to this master one.
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
    fsleyes_parseargs.applyOverlayArgs(args, overlayList, displayCtx)  

    return overlayList, displayCtx, splash


def interface(parent, args, ctx):
    """Creates the ``fsleyes`` interface.

    This function does the following:

     1. Creates the :class:`.FSLEyesFrame` the top-level frame for ``fsleyes``.

     2. Configures the frame according to the command line arguments (e.g. 
        ortho or lightbox view).

     3. Destroys the splash screen that was created by the :func:`context`
        function.

    :arg parent: :mod:`wx` parent object.

    :arg args:   Parsed command line arguments, as returned by
                 :func:`parseArgs`.

    :arg ctx:    The :class:`.OverlayList`, :class:`.DisplayContext`, and
                 :class:`.FSLEyesSplash`, as created and returned by
                 :func:`context`.

    :returns: the :class:`.FSLEyesFrame` that was created.
    """

    import                                  wx
    import fsl.fsleyes.fsleyes_parseargs as fsleyes_parseargs
    import fsl.fsleyes.frame             as fsleyesframe
    import fsl.fsleyes.displaycontext    as fsldisplay
    import fsl.fsleyes.views             as views

    overlayList, displayCtx, splashFrame = ctx

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
    script = args.runscript 
    scene  = args.scene

    # If a scene/perspective or custom script
    # has not been specified, the default
    # behaviour is to restore the previous
    # frame layout. 
    restore = (scene is None) and (script is None)

    status.update('Creating FSLeyes interface...')
    
    frame = fsleyesframe.FSLEyesFrame(
        parent, overlayList, displayCtx, restore, True)

    # Make sure the new frame is shown
    # before destroying the splash screen
    frame.Show(True)
    frame.Refresh()
    frame.Update()

    # Closing the splash screen immediately
    # can cause a crash under linux/GTK, so
    # we'll hide it now, and destroy it later.
    splashFrame.Hide()
    splashFrame.Refresh()
    splashFrame.Update()

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
            splashFrame.Close()
        frame.Bind(wx.EVT_WINDOW_DESTROY, onFrameDestroy)
    else:
        wx.CallLater(250, splashFrame.Close)

    status.update('Setting up scene...')

    # Set the default SceneOpts.performance
    # level so that all created SceneOpts
    # instances will default to it
    if args.performance is not None:
        fsldisplay.SceneOpts.performance.setConstraint(
            None, 'default', args.performance)

    # If a perspective has been specified,
    # we load the perspective
    if args.scene is not None:
        perspectives.loadPerspective(frame, args.scene)

    # Apply any view-panel specific arguments
    viewPanels = frame.getViewPanels()
    for viewPanel in viewPanels:

        if not isinstance(viewPanel, views.CanvasPanel):
            continue

        displayCtx = viewPanel.getDisplayContext()
        viewOpts   = viewPanel.getSceneOptions()

        fsleyes_parseargs.applySceneArgs(
            args, overlayList, displayCtx, viewOpts)

        def centre(vp=viewPanel):
            xc, yc, zc = fsleyes_parseargs.calcCanvasCentres(args,
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


def diagnosticReport(frame, ctx):
    """Set as a ``FSL_ACTION`` (see the :mod:`.tools` documentation).
    Creates and calls a :class:`.DiagnosticReportAction`.
    """
    overlayList, displayCtx, _ = ctx
    import fsl.fsleyes.actions as actions
    actions.DiagnosticReportAction(overlayList, displayCtx, frame)()


def about(frame, ctx):
    """Set as a ``FSL_ACTION`` (see the :mod:`.tools` documentation).
    Creates and calls an :class:`.AboutAction`.
    """
    overlayList, displayCtx, _ = ctx
    import fsl.fsleyes.actions as actions
    actions.AboutAction(overlayList, displayCtx, frame)() 

    
#############################################
# See the fsl.tools package documentation for
# details on these module-level attributes
#############################################


FSL_TOOLNAME  = 'FSLeyes'
FSL_HELPPAGE  = 'http://users.fmrib.ox.ac.uk/~paulmc/fsleyes/'
FSL_INTERFACE = interface
FSL_CONTEXT   = context
FSL_INIT      = init
FSL_PARSEARGS = parseArgs
FSL_ACTIONS   = [(strings.actions['AboutAction'],            about),
                 (strings.actions['DiagnosticReportAction'], diagnosticReport)]
