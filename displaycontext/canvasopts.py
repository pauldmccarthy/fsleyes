#!/usr/bin/env python
#
# canvasopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props


class SliceCanvasOpts(props.HasProperties):

    
    pos = props.Point(ndims=3)
    """The currently displayed position. The ``pos.x`` and ``pos.y`` positions
    denote the position of a 'cursor', which is highlighted with green
    crosshairs. The ``pos.z`` position specifies the currently displayed
    slice. While the values of this point are in the display coordinate
    system, the dimension ordering may not be the same as the display
    coordinate dimension ordering. For this position, the x and y dimensions
    correspond to horizontal and vertical on the screen, and the z dimension
    to 'depth'.
    """

    
    zoom = props.Percentage(minval=100.0,
                            maxval=1000.0,
                            default=100.0,
                            clamped=True)
    """The :attr:`.DisplayContext.bounds` are divided by this zoom
    factor to produce the canvas display bounds.
    """

    
    displayBounds = props.Bounds(ndims=2)
    """The display bound x/y values specify the horizontal/vertical display
    range of the canvas, in display coordinates. This may be a larger area
    than the size of the displayed overlays, as it is adjusted to preserve
    the aspect ratio.
    """

    
    showCursor = props.Boolean(default=True)
    """If ``False``, the green crosshairs which show
    the current cursor location will not be drawn.
    """
 

    zax = props.Choice((0, 1, 2))
    """The display coordinate system axis to be used as the screen 'depth'
    axis.
    """

    
    invertX = props.Boolean(default=False)
    """If True, the display is inverted along the X (horizontal screen) axis.
    """

    
    invertY = props.Boolean(default=False)
    """If True, the display is inverted along the Y (vertical screen) axis.
    """


    cursorColour = props.Colour(default=(0, 1, 0))
    """Canvas cursor colour."""


    bgColour = props.Colour(default=(0, 0, 0))
    """Canvas background colour."""

    
    renderMode = props.Choice(('onscreen', 'offscreen', 'prerender'))
    """How the GLObjects are rendered to the canvas - onscreen is the
    default, but the other options will give better performance on
    slower platforms.
    """
    
    
    softwareMode = props.Boolean(default=False)
    """If ``True``, the :attr:`.Display.softwareMode` property for every
    displayed image is set to ``True``.
    """

    
    resolutionLimit = props.Real(default=0, minval=0, maxval=5, clamped=True)
    """The minimum resolution at which overlays should be drawn."""


class LightBoxCanvasOpts(SliceCanvasOpts):

    
    sliceSpacing = props.Real(clamped=True,
                              minval=0.1,
                              maxval=30.0,
                              default=1.0)
    """This property controls the spacing
    between slices (in display coordinates).
    """

    
    ncols = props.Int(clamped=True, minval=1, maxval=100, default=5)
    """This property controls the number of 
    slices to be displayed on a single row.
    """

    
    nrows = props.Int(clamped=True, minval=1, maxval=100, default=4)
    """This property controls the number of 
    rows to be displayed on the canvas.
    """ 

    
    topRow = props.Int(clamped=True, minval=0, maxval=20, default=0)
    """This property controls the (0-indexed) row
    to be displayed at the top of the canvas, thus
    providing the ability to scroll through the
    slices.
    """

    
    zrange = props.Bounds(ndims=1)
    """This property controls the range, in display
    coordinates, of the slices to be displayed.
    """


    showGridLines = props.Boolean(default=False)
    """If True, grid lines are drawn between the displayed slices. """


    highlightSlice = props.Boolean(default=False)
    """If True, a box will be drawn around the slice containing the current
    location.
    """    
