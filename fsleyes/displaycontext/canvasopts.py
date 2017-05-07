#!/usr/bin/env python
#
# canvasopts.py - The SliceCanvasOpts and LightBoxCanvasOpts classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SliceCanvasOpts` and
:class:`LightBoxCanvasOpts` classes, which respectively define
slice/lightbox canvas display options.
"""

import fsleyes_props as props


class SliceCanvasOpts(props.HasProperties):
    """The ``SliceCanvasOpts`` class hosts all of the display settings
    for a :class:`.SliceCanvas`.

    Every ``SliceCanvas`` creats a single ``SliceCanvasOpts`` instance,
    and uses it to manage its display settings.
    """


    pos = props.Point(ndims=3)
    """The currently displayed position.

    The ``pos.x`` and ``pos.y`` positions denote the position of a *cursor*,
    which is highlighted with crosshairs (see the :attr:`showCursor`
    property). The ``pos.z`` position specifies the currently displayed slice.

    While the values of this point are in the display coordinate system, the
    dimension ordering may not be the same as the display coordinate dimension
    ordering. For this position, the x and y dimensions correspond to the
    horizontal and vertical screen axes, and the z dimension to *depth*.
    """


    zoom = props.Percentage(minval=100.0,
                            maxval=5000.0,
                            default=100.0,
                            clamped=False)
    """The :attr:`.DisplayContext.bounds` are divided by this zoom
    factor to produce the canvas display bounds.
    """


    displayBounds = props.Bounds(ndims=2, clamped=False)
    """The display bound x/y values specify the horizontal/vertical display
    range of the canvas, in display coordinates. This may be a larger area
    than the size of the displayed overlays, as it is adjusted to preserve
    the aspect ratio.
    """


    showCursor = props.Boolean(default=True)
    """If ``False``, the crosshairs which show the current cursor location
    will not be drawn.
    """


    cursorGap = props.Boolean(default=False)
    """If ``True``, and the currently selected overlay is a :class:`.Nifti`
    instance, a gap will be shown at the cursor centre (i.e. the current
    voxel).
    """


    zax = props.Choice((0, 1, 2),
                       alternates=[['x', 'X'], ['y', 'Y'], ['z', 'Z']],
                       allowStr=True)
    """The display coordinate system axis to be used as the screen *depth*
    axis.
    """


    invertX = props.Boolean(default=False)
    """If ``True``, the display is inverted along the X (horizontal screen)
    axis.
    """


    invertY = props.Boolean(default=False)
    """If ``True``, the display is inverted along the Y (vertical screen)
    axis.
    """


    cursorColour = props.Colour(default=(0, 1, 0))
    """Canvas cursor colour."""


    bgColour = props.Colour(default=(0, 0, 0))
    """Canvas background colour."""


    renderMode = props.Choice(('onscreen', 'offscreen', 'prerender'))
    """How the :class:`.GLObject` instances are rendered to the canvas.

    See the :class:`.SliceCanvas` for more details.
    """


    def __init__(self):
        pass


class LightBoxCanvasOpts(SliceCanvasOpts):
    """The ``LightBoxCanvasOpts`` class is used by :class:`.LightBoxCanvas`
    instances to manage light box display settings.
    """


    sliceSpacing = props.Real(clamped=True,
                              minval=0.1,
                              maxval=30.0,
                              default=1.0)
    """This property controls the spacing between slices in the display
    coordinate system.
    """


    ncols = props.Int(clamped=True, minval=1, maxval=100, default=5)
    """This property controls the number of slices to be displayed on a
    single row.
    """


    nrows = props.Int(clamped=True, minval=1, maxval=100, default=4)
    """This property controls the number of rows to be displayed on the
    canvas.
    """


    topRow = props.Int(clamped=True, minval=0, maxval=20, default=0)
    """This property controls the (0-indexed) row to be displayed at the top
    of the canvas, thus providing the ability to scroll through the slices.
    """


    zrange = props.Bounds(ndims=1)
    """This property controls the range, in display coordinates, of the slices
    to be displayed.
    """


    showGridLines = props.Boolean(default=False)
    """If ``True``, grid lines are drawn between the displayed slices. """


    highlightSlice = props.Boolean(default=False)
    """If ``True``, a box will be drawn around the slice containing the current
    location.
    """
