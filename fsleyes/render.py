#!/usr/bin/env python
#
# render.py - Generate screenshots of overlays using OpenGL.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``render`` module is a program which provides off-screen rendering
capability for scenes which can otherwise be displayed via *FSLeyes*.
"""


import os.path as op
import            sys
import            logging
import            textwrap

import numpy as np

import fsl.utils.idle                        as idle
import fsleyes_widgets.utils.layout          as fsllayout

import                                          fsleyes
import fsleyes.version                       as version
import fsleyes.overlay                       as fsloverlay
import fsleyes.colourmaps                    as fslcm
import fsleyes.parseargs                     as parseargs
import fsleyes.displaycontext                as displaycontext
import fsleyes.displaycontext.orthoopts      as orthoopts
import fsleyes.displaycontext.lightboxopts   as lightboxopts
import fsleyes.displaycontext.scene3dopts    as scene3dopts
import fsleyes.controls.colourbar            as cbar
import fsleyes.plugins.tools.saveannotations as saveannotations
import fsleyes.gl                            as fslgl
import fsleyes.gl.textures.imagetexture      as imagetexture
import fsleyes.gl.ortholabels                as ortholabels
import fsleyes.gl.offscreenslicecanvas       as slicecanvas
import fsleyes.gl.offscreenlightboxcanvas    as lightboxcanvas
import fsleyes.gl.offscreenscene3dcanvas     as scene3dcanvas


log = logging.getLogger(__name__)


def main(args=None, hook=None):
    """Entry point for ``render``.

    Creates and renders an OpenGL scene, and saves it to a file, according
    to the specified command line arguments (which default to
    ``sys.argv[1:]``).
    """

    if args is None:
        args = sys.argv[1:]

    # Initialise FSLeyes and implement
    # hacks. This must come first as it
    # does a number of important things.
    fsleyes.initialise()

    # Initialise colour maps module
    fslcm.init()

    # Create a GL context
    fslgl.getGLContext(offscreen=True, createApp=True)

    # Now that GL inititalisation is over,
    # make sure that the idle loop executes
    # all tasks synchronously, instead of
    # trying to schedule them on the wx
    # event loop. And make sure image textures
    # don't use separate threads for data
    # processing.
    with idle.idleLoop.synchronous(), \
         imagetexture.ImageTexture.enableThreading(False):

        # Parse arguments, and
        # configure logging/debugging
        namespace = parseArgs(args)
        fsleyes.configLogging(namespace.verbose, namespace.noisy)

        # Initialise the fsleyes.gl modules
        fslgl.bootstrap(namespace.glversion)

        # Create a description of the scene
        overlayList, displayCtx, sceneOpts = makeDisplayContext(namespace)

        import matplotlib.image as mplimg

        # Render that scene, and save it to file
        bitmap, bg = render(
            namespace, overlayList, displayCtx, sceneOpts, hook)

        if namespace.crop is not None:
            bitmap = autocrop(bitmap, bg, namespace.crop)

        # Alpha-blending does work, but the final
        # pixel values seem to take on the alpha
        # value of the most recently drawn item,
        # which is undesirable. So we save out
        # as rgb
        bitmap = bitmap[:, :, :3]

        mplimg.imsave(namespace.outfile, bitmap)

        # Clear the GL context
        fslgl.shutdown()


def parseArgs(argv):
    """Creates an argument parser which accepts options for off-screen
    rendering. Uses the :mod:`fsleyes.parseargs` module to peform the
    actual parsing.

    :returns: An ``argparse.Namespace`` object containing the parsed
              arguments.
    """

    mainParser = parseargs.ArgumentParser(
        add_help=False,
        formatter_class=parseargs.FSLeyesHelpFormatter)

    mainParser.add_argument('-of',
                            '--outfile',
                            help='Output image file name')
    mainParser.add_argument('-c',
                            '--crop',
                            type=int,
                            metavar='BORDER',
                            help='Auto-crop image, leaving a '
                                 'border on each side')
    mainParser.add_argument('-sz',
                            '--size',
                            type=int, nargs=2,
                            metavar=('W', 'H'),
                            help='Size in pixels (width, height)',
                            default=(800, 600))

    name        = 'render'
    prolog      = 'FSLeyes render version {}\n'.format(version.__version__)
    optStr      = '-of outfile'
    description = textwrap.dedent("""\
        FSLeyes screenshot generator.

        Use the '--scene' option to choose between orthographic
        ('ortho'), lightbox ('lightbox'), or 3D ('3d') views.
        """)

    namespace = parseargs.parseArgs(
        mainParser,
        argv,
        name,
        prolog=prolog,
        desc=description,
        usageProlog=optStr,
        argOpts=['-of', '--outfile',
                 '-sz', '--size',
                 '-c',  '--crop'],
        shortHelpExtra=['--outfile', '--size', '--crop'])

    if namespace.outfile is None:
        log.error('outfile is required')
        mainParser.print_usage()
        sys.exit(1)

    namespace.outfile = op.abspath(namespace.outfile)

    if namespace.scene not in ('ortho', 'lightbox', '3d'):
        log.info('Unknown scene specified  ("{}") - defaulting '
                 'to ortho'.format(namespace.scene))
        namespace.scene = 'ortho'

    return namespace


def makeDisplayContext(namespace):
    """Creates :class:`.OverlayList`, :class:`.DisplayContext``, and
    :class:`.SceneOpts` instances which represent the scene to be rendered,
    as described by the arguments in the given ``namespace`` object.
    """

    # Create an overlay list and display context.
    # The DisplayContext, Display and DisplayOpts
    # classes are designed to be created in a
    # parent-child hierarchy. So we need to create
    # a 'dummy' master display context to make
    # things work properly.
    overlayList      = fsloverlay.OverlayList()
    masterDisplayCtx = displaycontext.DisplayContext(overlayList)
    childDisplayCtx  = displaycontext.DisplayContext(overlayList,
                                                     parent=masterDisplayCtx)

    # We have to artificially create a ref to the
    # master display context, otherwise it may get
    # gc'd arbitrarily. The parent reference in the
    # child creation above is ultimately stored as
    # a weakref, so we need to create a real one.
    childDisplayCtx.masterDisplayCtx = masterDisplayCtx

    # The handleOverlayArgs function uses the
    # fsleyes.overlay.loadOverlays function,
    # which will call these functions as it
    # goes through the list of overlay to be
    # loaded.
    def load(ovl):
        log.info('Loading overlay {} ...'.format(ovl))

    def error(ovl, error):
        log.error('Error loading overlay {}: {}'.format(ovl, error))
        raise error

    # Load the overlays specified on the command
    # line, and configure their display properties
    parseargs.applyMainArgs(   namespace,
                               overlayList,
                               masterDisplayCtx)
    parseargs.applyOverlayArgs(namespace,
                               overlayList,
                               masterDisplayCtx,
                               loadFunc=load,
                               errorFunc=error)

    # Create a SceneOpts instance describing
    # the scene to be rendered. The parseargs
    # module assumes that GL canvases have
    # already been created, so we use mock
    # objects to trick it. The options applied
    # to these mock objects are applied to the
    # real canvases later on, in the render
    # function below.
    if namespace.scene == 'ortho':
        sceneOpts = orthoopts.OrthoOpts(MockCanvasPanel(3))
    elif namespace.scene == 'lightbox':
        sceneOpts = lightboxopts.LightBoxOpts(MockCanvasPanel(1))
    elif namespace.scene == '3d':
        sceneOpts = scene3dopts.Scene3DOpts(MockCanvasPanel(1))

    # 3D views default to
    # world display space
    if namespace.scene == '3d':
        childDisplayCtx.displaySpace = 'world'

    parseargs.applySceneArgs(namespace,
                             overlayList,
                             childDisplayCtx,
                             sceneOpts)

    # Centre the location. The DisplayContext
    # will typically centre its location on
    # initialisation, but this may not work
    # if any overlay arguments change the bounds
    # of an overlay (e.g. mesh reference image)
    if namespace.worldLoc is None and namespace.voxelLoc is None:
        b = childDisplayCtx.bounds
        childDisplayCtx.location = [
            b.xlo + 0.5 * b.xlen,
            b.ylo + 0.5 * b.ylen,
            b.zlo + 0.5 * b.zlen]

    # This has to be applied after applySceneArgs,
    # in case the user used the '-std'/'-std1mm'
    # options.
    if namespace.selectedOverlay is not None:
        masterDisplayCtx.selectedOverlay = namespace.selectedOverlay

    if len(overlayList) == 0:
        raise RuntimeError('At least one overlay must be specified')

    return overlayList, childDisplayCtx, sceneOpts


def render(namespace, overlayList, displayCtx, sceneOpts, hook=None):
    """Renders the scene, and returns a tuple containing the bitmap and the
    background colour.

    :arg namespace:   ``argparse.Namespace`` object containing command line
                      arguments.
    :arg overlayList: The :class:`.OverlayList` instance.
    :arg displayCtx:  The :class:`.DisplayContext` instance.
    :arg sceneOpts:   The :class:`.SceneOpts` instance.
    :arg hook:        Function which is called after the canvases have been
                      created, but before the scene is rendered. Can be used
                      to perform any configuration/drawing in addition to that
                      specified via ``namespace``.

    .. note:: The ``hook`` argument was added for testing purposes, but may
              be useful in other situations.
    """

    # Calculate canvas and colour bar sizes
    # so that the entire scene will fit in
    # the width/height specified by the user
    width, height = namespace.size
    (width, height), (cbarWidth, cbarHeight) = \
        adjustSizeForColourBar(width,
                               height,
                               sceneOpts.showColourBar,
                               sceneOpts.colourBarLocation,
                               sceneOpts.labelSize)

    # Lightbox view -> only one canvas
    if namespace.scene == 'lightbox':
        c = createLightBoxCanvas(namespace,
                                 width,
                                 height,
                                 overlayList,
                                 displayCtx,
                                 sceneOpts)
        canvases = [c]

    # Ortho view -> up to three canvases
    elif namespace.scene == 'ortho':
        canvases = createOrthoCanvases(namespace,
                                       width,
                                       height,
                                       overlayList,
                                       displayCtx,
                                       sceneOpts)
        labelMgr = ortholabels.OrthoLabels(overlayList,
                                           displayCtx,
                                           sceneOpts,
                                           *canvases)
        labelMgr.refreshLabels()

    # 3D -> one 3D canvas
    elif namespace.scene == '3d':
        c = create3DCanvas(namespace,
                           width,
                           height,
                           overlayList,
                           displayCtx,
                           sceneOpts)

        canvases = [c]

    # Do we need to do a neuro/radio l/r flip?
    if namespace.scene in ('ortho', 'lightbox'):
        inRadio = displayCtx.displaySpaceIsRadiological()
        lrFlip  = displayCtx.radioOrientation != inRadio

        if lrFlip:
            for c in canvases:
                if c.opts.zax in (1, 2):
                    c.opts.invertX = True

    # fix orthographic projection if
    # showing an ortho grid layout.
    # Note that, if the user chose 'grid',
    # but also chose to hide one or more
    # canvases, the createOrthoCanvases
    # function will have adjusted the
    # value of sceneOpts.layout. So
    # if layout == grid, we definitely
    # have three canvases.
    #
    # The createOrthoCanvases also
    # re-orders the canvases, which
    # we're assuming knowledge of,
    # by indexing canvases[1].
    if namespace.scene == 'ortho' and sceneOpts.layout == 'grid':
        canvases[1].opts.invertX = True

    # Load annotations, only on ortho
    if namespace.scene == 'ortho' and namespace.annotations is not None:
        saveannotations.loadAnnotations(MockOrthoPanel(canvases),
                                        namespace.annotations)

    # Configure each of the canvases (with those
    # properties that are common to both ortho and
    # lightbox canvases) and render them one by one
    canvasBmps = []

    # Call hook if provided (used for testing)
    if hook is not None:
        hook(overlayList, displayCtx, sceneOpts, canvases)

    for c in canvases:

        c.opts.pos = displayCtx.location

        # HACK If a SliceCanvas/LightBoxCanvas
        # is rendering the sceen to an off-screen
        # texture due to the low performance
        # setting, its internal viewport will not
        # be set until after all GLObjects have
        # been rendered. But some GLObjects (e.g.
        # GLLabel) need to know the current
        # viewport.
        #
        # This is very much an edge case, as who
        # would be using a low performance setting
        # for off-screen rendering?

        if namespace.scene in ('ortho', 'lightbox') and \
           namespace.performance is not None        and \
           int(namespace.performance) < 3:
            c._setViewport()

        c.draw()

        canvasBmps.append(c.getBitmap())

    # destroy the canvases
    for c in canvases:
        c.destroy()
    canvases = None

    # layout the bitmaps
    if namespace.scene in ('lightbox', '3d'):
        layout = fsllayout.Bitmap(canvasBmps[0])
    elif len(canvasBmps) > 0:
        layout = fsllayout.buildOrthoLayout(canvasBmps,
                                            None,
                                            sceneOpts.layout,
                                            False,
                                            0)
    else:
        layout = fsllayout.Space(width, height)

    # Render a colour bar if required
    if sceneOpts.showColourBar:
        cbarBmp = buildColourBarBitmap(overlayList,
                                       displayCtx,
                                       cbarWidth,
                                       cbarHeight,
                                       sceneOpts)
        if cbarBmp is not None:
            layout  = buildColourBarLayout(layout,
                                           cbarBmp,
                                           sceneOpts.colourBarLocation,
                                           sceneOpts.colourBarLabelSide)

    # Turn the layout tree into a bitmap image
    bgColour = [c * 255 for c in sceneOpts.bgColour]
    return fsllayout.layoutToBitmap(layout, bgColour), bgColour


def createLightBoxCanvas(namespace,
                         width,
                         height,
                         overlayList,
                         displayCtx,
                         sceneOpts):
    """Creates, configures, and returns an :class:`.OffScreenLightBoxCanvas`.

    :arg namespace:   ``argparse.Namespace`` object.
    :arg width:       Available width in pixels.
    :arg height:      Available height in pixels.
    :arg overlayList: The :class:`.OverlayList` instance.
    :arg displayCtx:  The :class:`.DisplayContext` instance.
    :arg sceneOpts:   The :class:`.SceneOpts` instance.
    """

    canvas = lightboxcanvas.OffScreenLightBoxCanvas(
        overlayList,
        displayCtx,
        zax=sceneOpts.zax,
        width=width,
        height=height)

    if sceneOpts.zrange == (0, 0):
        sceneOpts.zrange = displayCtx.bounds.getRange(sceneOpts.zax)

    opts                = canvas.opts
    opts.showCursor     = sceneOpts.showCursor
    opts.bgColour       = sceneOpts.bgColour
    opts.cursorColour   = sceneOpts.cursorColour
    opts.renderMode     = sceneOpts.renderMode
    opts.zax            = sceneOpts.zax
    opts.sliceSpacing   = sceneOpts.sliceSpacing
    opts.nrows          = sceneOpts.nrows
    opts.ncols          = sceneOpts.ncols
    opts.zrange         = sceneOpts.zrange
    opts.showGridLines  = sceneOpts.showGridLines
    opts.highlightSlice = sceneOpts.highlightSlice

    return canvas


def createOrthoCanvases(namespace,
                        width,
                        height,
                        overlayList,
                        displayCtx,
                        sceneOpts):
    """Creates, configures, and returns up to three
    :class:`.OffScreenSliceCanvas` instances, for rendering the scene.

    :arg namespace:   ``argparse.Namespace`` object.
    :arg width:       Available width in pixels.
    :arg height:      Available height in pixels.
    :arg overlayList: The :class:`.OverlayList` instance.
    :arg displayCtx:  The :class:`.DisplayContext` instance.
    :arg sceneOpts:   The :class:`.SceneOpts` instance.
    """

    canvases = []

    # Build a list containing the horizontal
    # and vertical axes for each canvas
    canvasAxes = []
    zooms      = []
    centres    = []
    inverts    = []
    if sceneOpts.showXCanvas:
        canvasAxes.append((1, 2))
        zooms     .append(sceneOpts.xzoom)
        centres   .append(sceneOpts.panel.getGLCanvases()[0].centre)
        inverts   .append((sceneOpts.invertXHorizontal,
                           sceneOpts.invertXVertical))
    if sceneOpts.showYCanvas:
        canvasAxes.append((0, 2))
        zooms     .append(sceneOpts.yzoom)
        centres   .append(sceneOpts.panel.getGLCanvases()[1].centre)
        inverts   .append((sceneOpts.invertYHorizontal,
                           sceneOpts.invertYVertical))
    if sceneOpts.showZCanvas:
        canvasAxes.append((0, 1))
        zooms     .append(sceneOpts.zzoom)
        centres   .append(sceneOpts.panel.getGLCanvases()[2].centre)
        inverts   .append((sceneOpts.invertZHorizontal,
                           sceneOpts.invertZVertical))

    # Grid layout only makes sense if
    # we're displaying 3 canvases
    if sceneOpts.layout == 'grid' and len(canvasAxes) <= 2:
        sceneOpts.layout = 'horizontal'

    if sceneOpts.layout == 'grid':
        canvasAxes = [canvasAxes[1], canvasAxes[0], canvasAxes[2]]
        centres    = [centres[   1], centres[   0], centres[   2]]
        zooms      = [zooms[     1], zooms[     0], zooms[     2]]
        inverts    = [inverts[   1], inverts[   0], inverts[   2]]

    # Calculate the size in pixels for each canvas
    sizes = calculateOrthoCanvasSizes(overlayList,
                                      displayCtx,
                                      width,
                                      height,
                                      canvasAxes,
                                      sceneOpts.layout)

    # Configure the properties on each canvas
    for ((width, height),
         (xax, yax),
         zoom,
         centre,
         (invertx, inverty)) in zip(sizes,
                                    canvasAxes,
                                    zooms,
                                    centres,
                                    inverts):

        zax = 3 - xax - yax

        c = slicecanvas.OffScreenSliceCanvas(
            overlayList,
            displayCtx,
            zax=zax,
            width=int(width),
            height=int(height))

        opts              = c.opts
        opts.showCursor   = sceneOpts.showCursor
        opts.cursorColour = sceneOpts.cursorColour
        opts.cursorGap    = sceneOpts.cursorGap
        opts.bgColour     = sceneOpts.bgColour
        opts.renderMode   = sceneOpts.renderMode
        opts.invertX      = invertx
        opts.invertY      = inverty

        if zoom is not None:
            opts.zoom = zoom

        # Default to centering
        # on the cursor
        if centre is None:
            centre = [displayCtx.location[xax], displayCtx.location[yax]]

        c.centreDisplayAt(*centre)

        canvases.append(c)

    return canvases


def create3DCanvas(namespace,
                   width,
                   height,
                   overlayList,
                   displayCtx,
                   sceneOpts):
    """Creates, configures, and returns an :class:`.OffScreenScene3DCanvas`.

    :arg namespace:   ``argparse.Namespace`` object.
    :arg width:       Available width in pixels.
    :arg height:      Available height in pixels.
    :arg overlayList: The :class:`.OverlayList` instance.
    :arg displayCtx:  The :class:`.DisplayContext` instance.
    :arg sceneOpts:   The :class:`.SceneOpts` instance.
    """

    canvas = scene3dcanvas.OffScreenScene3DCanvas(
        overlayList,
        displayCtx,
        width=width,
        height=height)

    opts                 = canvas.opts
    opts.showCursor      = sceneOpts.showCursor
    opts.cursorColour    = sceneOpts.cursorColour
    opts.bgColour        = sceneOpts.bgColour
    opts.showLegend      = sceneOpts.showLegend
    opts.legendColour    = sceneOpts.fgColour
    opts.occlusion       = sceneOpts.occlusion
    opts.light           = sceneOpts.light
    opts.zoom            = sceneOpts.zoom
    opts.offset          = sceneOpts.offset
    opts.rotation        = sceneOpts.rotation

    if parseargs.wasSpecified(namespace, sceneOpts, 'lightPos') or \
       parseargs.wasSpecified(namespace, sceneOpts, 'lightDistance'):
        opts.lightPos        = sceneOpts.lightPos
        opts.lightDistance   = sceneOpts.lightDistance
        canvas.resetLightPos = False
    else:
        canvas.defaultLightPos()

    return canvas


def buildColourBarBitmap(overlayList,
                         displayCtx,
                         width,
                         height,
                         sceneOpts):
    """If the currently selected overlay has a display range,
    creates and returns a bitmap containing a colour bar. Returns
    ``None`` otherwise.

    :arg overlayList:   The :class:`.OverlayList`.

    :arg displayCtx:    The :class:`.DisplayContext`.

    :arg width:         Colour bar width in pixels.

    :arg height:        Colour bar height in pixels.

    :arg sceneOpts:     :class:`.SceneOpts` instance containing display
                        settings.
    """

    overlay = displayCtx.getSelectedOverlay()
    display = displayCtx.getDisplay(overlay)
    opts    = display.opts

    cbarLocation = sceneOpts.colourBarLocation
    cbarSize     = sceneOpts.colourBarSize

    if   cbarLocation in ('top', 'bottom'): width  = width  * cbarSize / 100.0
    elif cbarLocation in ('left', 'right'): height = height * cbarSize / 100.0

    if not isinstance(opts, displaycontext.ColourMapOpts):
        return None

    if   cbarLocation in ('top', 'bottom'): orient = 'horizontal'
    elif cbarLocation in ('left', 'right'): orient = 'vertical'

    cb = cbar.ColourBar(overlayList, displayCtx)
    cb.orientation = orient
    cb.labelSide   = sceneOpts.colourBarLabelSide
    cb.bgColour    = sceneOpts.bgColour
    cb.textColour  = sceneOpts.fgColour
    cb.fontSize    = sceneOpts.labelSize

    cbarBmp = cb.colourBar(width, height)

    # The colourBarBitmap function returns a w*h*4
    # array, but the fsleyes_widgets.utils.layout.Bitmap
    # (see the next function) assumes a h*w*4 array
    cbarBmp = cbarBmp.transpose((1, 0, 2))

    return cbarBmp


def buildColourBarLayout(canvasLayout,
                         cbarBmp,
                         cbarLocation,
                         cbarLabelSide):
    """Given a layout object containing the rendered canvas bitmaps,
    creates a new layout which incorporates the given colour bar bitmap.

    :arg canvasLayout:  An object describing the canvas layout (see
                        :mod:`fsleyes_widgets.utils.layout`)

    :arg cbarBmp:       A bitmap containing a rendered colour bar.

    :arg cbarLocation:  Colour bar location (see :func:`buildColourBarBitmap`).

    :arg cbarLabelSide: Colour bar label side (see
                        :func:`buildColourBarBitmap`).
    """

    cbarBmp = fsllayout.Bitmap(cbarBmp)

    if   cbarLocation in ('top',    'left'):  items = [cbarBmp, canvasLayout]
    elif cbarLocation in ('bottom', 'right'): items = [canvasLayout, cbarBmp]

    if   cbarLocation in ('top', 'bottom'): return fsllayout.VBox(items)
    elif cbarLocation in ('left', 'right'): return fsllayout.HBox(items)


def adjustSizeForColourBar(width,
                           height,
                           showColourBar,
                           colourBarLocation,
                           fontSize):
    """Calculates the widths and heights of the image display space, and the
    colour bar if it is enabled.

    :arg width:             Desired width in pixels

    :arg height:            Desired height in pixels

    :arg showColourBar:     ``True`` if a colour bar is to be shown, ``False``
                            otherwise.

    :arg colourBarLocation: Colour bar location (see
                            :func:`buildColourBarBitmap`).

    :arg fontSize           Font size (points) used in colour bar labels.

    :returns:               Two tuples - the first tuple contains the
                            ``(width, height)`` of the available canvas space,
                            and the second contains the ``(width, height)`` of
                            the colour bar.
    """

    if showColourBar:

        cbarWidth = int(round(cbar.colourBarMinorAxisSize(fontSize)))
        if colourBarLocation in ('top', 'bottom'):
            height     = height - cbarWidth
            cbarHeight = cbarWidth
            cbarWidth  = width
        else:
            width      = width  - cbarWidth
            cbarHeight = height
    else:
        cbarWidth  = 0
        cbarHeight = 0

    return (width, height), (cbarWidth, cbarHeight)


def calculateOrthoCanvasSizes(overlayList,
                              displayCtx,
                              width,
                              height,
                              canvasAxes,
                              layout):
    """Calculates the sizes, in pixels, for each canvas to be displayed in an
    orthographic layout.

    :arg overlayList: The :class:`.OverlayList`.

    :arg displayCtx:  The :class:`.DisplayContext`.

    :arg width:       Available width in pixels.

    :arg height:      Available height in pixels.

    :arg canvasAxes:  A sequence of ``(xax, yax)`` indices, one for each
                      bitmap in ``canvasBmps``.

    :arg layout:      Either ``'horizontal'``, ``'vertical'``, or ``'grid'``,
                      describing the canvas layout.

    :returns:         A list of ``(width, height)`` tuples, one for each
                      canvas, each specifying the canvas width and height in
                      pixels.
    """

    bounds   = displayCtx.bounds
    axisLens = [bounds.xlen, bounds.ylen, bounds.zlen]

    # Grid layout only makes sense if we're
    # displaying all three canvases
    if layout == 'grid' and len(canvasAxes) <= 2:
        raise ValueError('Grid layout only supports 3 canvases')

    # Distribute the height across canvas heights
    return fsllayout.calcSizes(layout,
                               canvasAxes,
                               axisLens,
                               width,
                               height)


def autocrop(data, bgColour, border=0):
    """Crops the given bitmap image on all sides where the ``bgColour`` is
    the only colour present.

    If the image is completely empty. it is not cropped.

    :arg data:     ``numpy`` array of shape ``(w, h, 4)`` containing the image.
    :arg bgColour: Sequence of length 4 containing the background colour to
                   crop.
    :arg border:   Number of pixels to leave around each side.
    """

    w, h = data.shape[:2]

    low, hiw = 0, w
    loh, hih = 0, h

    while np.all(data[low,     :] == bgColour): low += 1
    while np.all(data[hiw - 1, :] == bgColour): hiw -= 1
    while np.all(data[:, loh]     == bgColour): loh += 1
    while np.all(data[:, hih - 1] == bgColour): hih -= 1

    if low < hiw and loh < hih:
        data = data[low:hiw, loh:hih, :]

        if border > 0:
            w, h, c = data.shape
            new = np.zeros((w + 2 * border, h + 2 * border, c),
                           dtype=data.dtype)
            new[:, :] = bgColour
            new[border:-border, border:-border, :] = data
            data = new

    return data


class MockSliceCanvas:
    """Used in place of a :class:`.SliceCanvas`. The :mod:`.parseargs` module
    needs access to ``SliceCanvas`` instances to apply some command line
    options. However, ``render`` calls :func:`.parseargs.applySceneArgs`
    before any ``SliceCanvas`` instances have been created.

    Instances of this class are just used to capture those options, so they
    can later be applied to the real ``SliceCanvas`` instances.

    The following arguments may be applied to this class.
      - ``--xcentre``
      - ``--ycentre``
      - ``--zcentre``
    """
    def __init__(self):
        self.centre = None
    def centreDisplayAt(self, x, y):
        self.centre = x, y


class MockCanvasPanel:
    """Used in place of a :class:`.CanvasPanel`. This is used as a container
    for :class:`MockSliceCanvas` instances.
    """
    def __init__(self, ncanvases):
        self.canvases = [MockSliceCanvas() for i in range(ncanvases)]
    def getGLCanvases(self):
        return self.canvases


class MockOrthoPanel:
    """Used in place of an :class:`.OrthoPanel`. This is used as a container
    for three :class:`SliceCanvas` instances.
    """
    def __init__(self, canvases):
        self.canvases = canvases
    def getGLCanvases(self):
        return self.canvases
    def getXCanvas(self):
        return self.canvases[0]
    def getYCanvas(self):
        return self.canvases[1]
    def getZCanvas(self):
        return self.canvases[2]


if __name__ == '__main__':
    main()
