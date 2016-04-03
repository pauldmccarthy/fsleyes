#!/usr/bin/env python
#
# render.py - Generate screenshots of overlays using OpenGL.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module implements an application which provides off-screen rendering
capability for scenes which can otherwise be displayed via fsleyes.

See:
  - :mod:`fsl.tools.fsleyes`
  - :mod:`fsl.fsleyes.fsleyes_parseargs`
"""


import            os
import os.path as op
import            sys
import            logging
import            textwrap
import            argparse

import props

import fsl
import fsl.utils.layout                        as fsllayout
import fsl.utils.colourbarbitmap               as cbarbitmap
import fsl.utils.textbitmap                    as textbitmap
import fsl.data.constants                      as constants
import fsl.fsleyes.strings                     as strings
import fsl.fsleyes.overlay                     as fsloverlay
import fsl.fsleyes.colourmaps                  as fslcm
import fsl.fsleyes.fsleyes_parseargs           as fsleyes_parseargs
import fsl.fsleyes.displaycontext              as displaycontext
import fsl.fsleyes.displaycontext.orthoopts    as orthoopts
import fsl.fsleyes.displaycontext.lightboxopts as lightboxopts


log = logging.getLogger(__name__)


if   sys.platform.startswith('linux'): _LD_LIBRARY_PATH = 'LD_LIBRARY_PATH'
elif sys.platform         == 'darwin': _LD_LIBRARY_PATH = 'DYLD_LIBRARY_PATH'


CBAR_SIZE   = 75
LABEL_SIZE  = 20


def buildLabelBitmaps(overlayList,
                      displayCtx,
                      canvasAxes, 
                      canvasBmps,
                      bgColour,
                      alpha):
    """Creates bitmaps containing anatomical orientation labels.

    Returns a list of dictionaries, one dictionary for each canvas. Each
    dictionary contains ``{label -> bitmap}`` mappings, where ``label`` is
    either ``top``, ``bottom``, ``left`` or ``right``.
    """
    
    # Default label colour is determined from the background
    # colour. If the orientation labels cannot be determined
    # though, the foreground colour will be changed to red.
    fgColour = fslcm.complementaryColour(bgColour)

    overlay = displayCtx.getReferenceImage(displayCtx.getSelectedOverlay())

    # There's no reference image for the selected overlay,
    # so we cannot calculate orientation labels
    if overlay is None:
        xorient = constants.ORIENT_UNKNOWN
        yorient = constants.ORIENT_UNKNOWN
        zorient = constants.ORIENT_UNKNOWN
    else:

        display = displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()
        xform   = opts.getTransform('world', 'display')
        xorient = overlay.getOrientation(0, xform)
        yorient = overlay.getOrientation(1, xform)
        zorient = overlay.getOrientation(2, xform)

    if constants.ORIENT_UNKNOWN in [xorient, yorient, zorient]:
        fgColour = 'red'

    xlo = strings.anatomy['Nifti1', 'lowshort',  xorient]
    ylo = strings.anatomy['Nifti1', 'lowshort',  yorient]
    zlo = strings.anatomy['Nifti1', 'lowshort',  zorient]
    xhi = strings.anatomy['Nifti1', 'highshort', xorient]
    yhi = strings.anatomy['Nifti1', 'highshort', yorient]
    zhi = strings.anatomy['Nifti1', 'highshort', zorient]

    loLabels = [xlo, ylo, zlo]
    hiLabels = [xhi, yhi, zhi]

    labelBmps = []

    for (xax, yax), canvasBmp in zip(canvasAxes, canvasBmps):

        width        = canvasBmp.shape[1]
        height       = canvasBmp.shape[0]

        allLabels    = {}
        labelKeys    = ['left', 'right', 'top', 'bottom']
        labelTexts   = [loLabels[xax], hiLabels[xax],
                        loLabels[yax], hiLabels[yax]]
        labelWidths  = [LABEL_SIZE, LABEL_SIZE, width,      width]
        labelHeights = [height,     height,     LABEL_SIZE, LABEL_SIZE]


        for key, text, width, height in zip(labelKeys,
                                            labelTexts,
                                            labelWidths,
                                            labelHeights):

            allLabels[key] = textbitmap.textBitmap(
                text=text,
                width=width,
                height=height,
                fontSize=12,
                fgColour=fgColour,
                bgColour=bgColour,
                alpha=alpha)

        labelBmps.append(allLabels)
            
    return labelBmps


def buildColourBarBitmap(overlayList,
                         displayCtx,
                         width,
                         height,
                         cbarLocation,
                         cbarLabelSide,
                         bgColour):
    """If the currently selected overlay has a display range,
    creates and returns a bitmap containing a colour bar. Returns
    ``None`` otherwise.
    """

    overlay = displayCtx.getSelectedOverlay()
    display = displayCtx.getDisplay(overlay)
    opts    = display.getDisplayOpts()

    # TODO Support other overlay types which
    # have a display range (when they exist).
    if not isinstance(opts, displaycontext.VolumeOpts):
        return None
    
    if   cbarLocation in ('top', 'bottom'): orient = 'horizontal'
    elif cbarLocation in ('left', 'right'): orient = 'vertical'
    
    if   cbarLabelSide == 'top-left':
        if orient == 'horizontal': labelSide = 'top'
        else:                      labelSide = 'left'
    elif cbarLabelSide == 'bottom-right':
        if orient == 'horizontal': labelSide = 'bottom'
        else:                      labelSide = 'right'

    cbarBmp = cbarbitmap.colourBarBitmap(
        opts.cmap,
        opts.displayRange.xlo,
        opts.displayRange.xhi,
        width,
        height,
        display.name,
        orient,
        labelSide,
        bgColour=bgColour,
        textColour=fslcm.complementaryColour(bgColour))

    # The colourBarBitmap function returns a w*h*4
    # array, but the fsl.utils.layout.Bitmap (see
    # the next function) assumes a h*w*4 array
    cbarBmp = cbarBmp.transpose((1, 0, 2))
    
    return cbarBmp

 
def buildColourBarLayout(canvasLayout,
                         cbarBmp,
                         cbarLocation,
                         cbarLabelSide):
    """Given a layout object containing the rendered canvas bitmaps,
    creates a new layout which incorporates the given colour bar bitmap.
    """

    cbarBmp = fsllayout.Bitmap(cbarBmp)

    if   cbarLocation in ('top',    'left'):  items = [cbarBmp, canvasLayout]
    elif cbarLocation in ('bottom', 'right'): items = [canvasLayout, cbarBmp]

    if   cbarLocation in ('top', 'bottom'): return fsllayout.VBox(items)
    elif cbarLocation in ('left', 'right'): return fsllayout.HBox(items)


def adjustSizeForColourBar(width, height, showColourBar, colourBarLocation):
    """Calculates the widths and heights of the image display space, and the
    colour bar if it is enabled.

    Returns two tuples - the first tuple contains the (width, height) of the
    available canvas space, and the second contains the (width, height) of
    the colour bar.
    """

    if showColourBar:

        cbarWidth = CBAR_SIZE
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


def calculateOrthoCanvasSizes(
        overlayList,
        displayCtx,
        width,
        height,
        canvasAxes,
        showLabels,
        layout):

    bounds   = displayCtx.bounds
    axisLens = [bounds.xlen, bounds.ylen, bounds.zlen]

    # Grid layout only makes sense if we're
    # displaying all three canvases
    if layout == 'grid' and len(canvasAxes) <= 2:
        raise ValueError('Grid layout only supports 3 canvases')

    # If we're displaying orientation labels,
    # reduce the available width and height
    # by a fixed amount
    if showLabels:
        if layout == 'horizontal':
            width  -= 2 * LABEL_SIZE * len(canvasAxes)
            height -= 2 * LABEL_SIZE
        elif layout == 'vertical':
            width  -= 2 * LABEL_SIZE
            height -= 2 * LABEL_SIZE * len(canvasAxes)
        elif layout == 'grid':
            width  -= 4 * LABEL_SIZE
            height -= 4 * LABEL_SIZE

    # Distribute the height across canvas heights
    return fsllayout.calcSizes(layout,
                               canvasAxes,
                               axisLens,
                               width,
                               height)


def run(args, context):
    """Creates and renders an OpenGL scene, and saves it to a file, according
    to the specified command line arguments.
    """

    # If this process is not configured for off-screen
    # rendering using osmesa, start a new process
    env = os.environ.copy()

    if env.get('FSL_OSMESA_PATH', None) is None:
        
        log.error('The FSL_OSMESA_PATH environment variable is not set - '
                  'I need to know where the OSMESA libraries are. Set this '
                  'variable and rerun render.')
        sys.exit(1)
    
    if env.get('PYOPENGL_PLATFORM', None) != 'osmesa':

        # Tell PyOpenGL that it should use
        # osmesa for off-screen rendering
        env['PYOPENGL_PLATFORM'] = 'osmesa'
        env[_LD_LIBRARY_PATH]    = env['FSL_OSMESA_PATH']

        log.warning('Restarting render.py with '
                    'off-screen rendering configured...')

        # Restart render with the same arguments,
        # but with an updated environment
        argv = list(sys.argv)
        argv = argv[argv.index('render') + 1:]

        fsl.runTool('render', argv, env=env)
        sys.exit(0)

    # Make sure that FSL_OSMESA_PATH is definitely on the
    # library path before OpenGL is imported (which occurs
    # in fskl.fsleyes.gl) - pyinstaller clears the
    # DYLD_LIBRARY_PATH env var before running a compiled
    # script, so our above restart is useless.
    os.environ[_LD_LIBRARY_PATH] = os.environ.get(_LD_LIBRARY_PATH, '') + \
                                   op.pathsep + env['FSL_OSMESA_PATH']

    import fsl.fsleyes.gl                      as fslgl
    import fsl.fsleyes.gl.osmesaslicecanvas    as slicecanvas
    import fsl.fsleyes.gl.osmesalightboxcanvas as lightboxcanvas

    # Make sure than an OpenGL context 
    # exists, and initalise OpenGL modules
    fslgl.getOSMesaContext()
    fslgl.bootstrap((1, 4))

    overlayList, displayCtx = context

    if   args.scene == 'ortho':    sceneOpts = orthoopts   .OrthoOpts()
    elif args.scene == 'lightbox': sceneOpts = lightboxopts.LightBoxOpts()

    fsleyes_parseargs.applySceneArgs(args, overlayList, displayCtx, sceneOpts)

    # Calculate canvas and colour bar sizes
    # so that the entire scene will fit in
    # the width/height specified by the user
    width, height = args.size
    (width, height), (cbarWidth, cbarHeight) = \
        adjustSizeForColourBar(width,
                               height,
                               sceneOpts.showColourBar,
                               sceneOpts.colourBarLocation)
    
    canvases = []

    # Lightbox view -> only one canvas
    if args.scene == 'lightbox':
        c = lightboxcanvas.OSMesaLightBoxCanvas(
            overlayList,
            displayCtx,
            zax=sceneOpts.zax,
            width=width,
            height=height)

        props.applyArguments(c, args)
        canvases.append(c)

    # Ortho view -> up to three canvases
    elif args.scene == 'ortho':

        xc, yc, zc = fsleyes_parseargs.calcCanvasCentres(args,
                                                         overlayList,
                                                         displayCtx) 
 
        # Build a list containing the horizontal 
        # and vertical axes for each canvas
        canvasAxes = []
        zooms      = []
        centres    = []
        if sceneOpts.showXCanvas:
            canvasAxes.append((1, 2))
            zooms     .append(sceneOpts.xzoom)
            centres   .append(xc)
        if sceneOpts.showYCanvas:
            canvasAxes.append((0, 2))
            zooms     .append(sceneOpts.yzoom)
            centres   .append(yc)
        if sceneOpts.showZCanvas:
            canvasAxes.append((0, 1))
            zooms     .append(sceneOpts.zzoom)
            centres   .append(zc)

        # Grid only makes sense if
        # we're displaying 3 canvases
        if sceneOpts.layout == 'grid' and len(canvasAxes) <= 2:
            sceneOpts.layout = 'horizontal'

        if sceneOpts.layout == 'grid':
            canvasAxes = [canvasAxes[1], canvasAxes[0], canvasAxes[2]]
            centres    = [centres[   1], centres[   0], centres[   2]]
            zooms      = [zooms[     1], zooms[     0], zooms[     2]]
        
        sizes = calculateOrthoCanvasSizes(overlayList,
                                          displayCtx,
                                          width,
                                          height,
                                          canvasAxes,
                                          sceneOpts.showLabels,
                                          sceneOpts.layout)

        for ((width, height), (xax, yax), zoom, centre) in zip(sizes,
                                                               canvasAxes,
                                                               zooms,
                                                               centres):

            zax = 3 - xax - yax

            if centre is None:
                centre = (displayCtx.location[xax], displayCtx.location[yax])

            c = slicecanvas.OSMesaSliceCanvas(
                overlayList,
                displayCtx,
                zax=zax,
                width=int(width),
                height=int(height))

            c.showCursor      = sceneOpts.showCursor
            c.cursorColour    = sceneOpts.cursorColour
            c.bgColour        = sceneOpts.bgColour
            c.renderMode      = sceneOpts.renderMode
            c.resolutionLimit = sceneOpts.resolutionLimit
            
            if zoom is not None: c.zoom = zoom
            c.centreDisplayAt(*centre)
            canvases.append(c)

    # Configure each of the canvases (with those
    # properties that are common to both ortho and
    # lightbox canvases) and render them one by one
    for i, c in enumerate(canvases):

        if   c.zax == 0: c.pos.xyz = displayCtx.location.yzx
        elif c.zax == 1: c.pos.xyz = displayCtx.location.xzy
        elif c.zax == 2: c.pos.xyz = displayCtx.location.xyz

        c.draw()

        canvases[i] = c.getBitmap()

    # Show/hide orientation labels -
    # not supported on lightbox view
    if args.scene == 'lightbox' or not sceneOpts.showLabels:
        labelBmps = None
    else:
        labelBmps = buildLabelBitmaps(overlayList,
                                      displayCtx,
                                      canvasAxes,
                                      canvases,
                                      sceneOpts.bgColour[:3],
                                      sceneOpts.bgColour[ 3])

    # layout
    if args.scene == 'lightbox':
        layout = fsllayout.Bitmap(canvases[0])
    else:
        layout = fsllayout.buildOrthoLayout(canvases,
                                            labelBmps,
                                            sceneOpts.layout,
                                            sceneOpts.showLabels,
                                            LABEL_SIZE)

    # Render a colour bar if required
    if sceneOpts.showColourBar:
        cbarBmp = buildColourBarBitmap(overlayList,
                                       displayCtx,
                                       cbarWidth,
                                       cbarHeight,
                                       sceneOpts.colourBarLocation,
                                       sceneOpts.colourBarLabelSide,
                                       sceneOpts.bgColour)
        if cbarBmp is not None:
            layout  = buildColourBarLayout(layout,
                                           cbarBmp,
                                           sceneOpts.colourBarLocation,
                                           sceneOpts.colourBarLabelSide)

 
    if args.outfile is not None:
        
        import matplotlib.image as mplimg
        bitmap = fsllayout.layoutToBitmap(
            layout, [c * 255 for c in sceneOpts.bgColour])
        mplimg.imsave(args.outfile, bitmap)

    
def parseArgs(argv):
    """Creates an argument parser which accepts options for off-screen
    rendering.
    
    Uses the :mod:`.fsleyes_parseargs` module to peform the actual parsing.
    """

    mainParser = argparse.ArgumentParser(add_help=False)

    mainParser.add_argument('-of', '--outfile',  metavar='OUTPUTFILE',
                            help='Output image file name')
    mainParser.add_argument('-sz', '--size', type=int, nargs=2,
                            metavar=('W', 'H'),
                            help='Size in pixels (width, height)',
                            default=(800, 600))

    name        = 'render'
    optStr      = '-of outfile [options]'
    description = textwrap.dedent("""\
        FSLeyes screenshot generator.

        Use the '--scene' option to choose between orthographic
        ('ortho') or lightbox ('lightbox') view.

        Tensor overlays are not supported by render.
        """)
    
    namespace = fsleyes_parseargs.parseArgs(mainParser,
                                            argv,
                                            name,
                                            description,
                                            optStr,
                                            fileOpts=['of', 'outfile'])

    if namespace.outfile is None:
        log.error('outfile is required')
        mainParser.print_usage()
        sys.exit(1)

    if namespace.scene not in ('ortho', 'lightbox'):
        log.info('Unknown scene specified  ("{}") - defaulting '
                 'to ortho'.format(namespace.scene))
        namespace.scene = 'ortho'
 
    return namespace


def context(args, *a, **kwa):

    # Create an image list and display context.
    # The DisplayContext, Display and DisplayOpts
    # classes are designed to be created in a
    # parent-child hierarchy. So we need to create
    # a 'dummy' master display context to make
    # things work properly.
    overlayList      = fsloverlay.OverlayList()
    masterDisplayCtx = displaycontext.DisplayContext(overlayList)
    childDisplayCtx  = displaycontext.DisplayContext(overlayList,
                                                     parent=masterDisplayCtx)

    # The handleOverlayArgs function uses the
    # fsl.fsleyes.overlay.loadOverlays function,
    # which will call these functions as it
    # goes through the list of overlay to be
    # loaded.
    def load(ovl):
        log.info('Loading overlay {} ...'.format(ovl))
    def error(ovl, error):
        log.info('Error loading overlay {}: '.format(ovl, error))

    # Load the overlays specified on the command
    # line, and configure their display properties
    fsleyes_parseargs.applyOverlayArgs(
        args, overlayList, masterDisplayCtx, loadFunc=load, errorFunc=error)

    if len(overlayList) == 0:
        raise RuntimeError('At least one overlay must be specified')

    return overlayList, childDisplayCtx
 

FSL_TOOLNAME  = 'Render'
FSL_EXECUTE   = run
FSL_CONTEXT   = context
FSL_PARSEARGS = parseArgs
