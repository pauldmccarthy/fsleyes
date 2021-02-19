#!/usr/bin/env python
#
# canvasopts.py - The SliceCanvasOpts and LightBoxCanvasOpts classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the following classes:

  - :class:`SliceCanvasOpts` (for the :class:`.SliceCanvas`)
  - :class:`LightBoxCanvasOpts` (for the :class:`.LightBoxCanvas`)
  - :class:`Scene3DCanvasOpts` (for the :class:`.Scene3DCanvas`)

These classes contain the definitions of properties which are available on the
corresponding canvas class.

These classes are defined independently of the :class:`.SliceCanvas` (and
other) classes so they can be inspected without having to import the
:mod:`.slicecanvas` (and other) modules, e.g. during command line argument
parsing.
"""


import copy

import numpy as np

import fsleyes_props as props


class SliceCanvasOpts(props.HasProperties):
    """The ``SliceCanvasOpts`` class defines all of the display settings
    for a :class:`.SliceCanvas`.
    """


    pos = props.Point(ndims=3)
    """The currently displayed position.

    The ``pos.x`` and ``pos.y`` positions denote the position of a *cursor*,
    which is highlighted with crosshairs (see the :attr:`showCursor`
    property). The ``pos.z`` position specifies the currently displayed slice.
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
    axis. The :meth:`xax` and :meth:`yax` attributes are derived from this
    property:

     - If ``zax == 0``, ``xax, yax == 1, 2``
     - If ``zax == 1``, ``xax, yax == 0, 2``
     - If ``zax == 2``, ``xax, yax == 0, 1``
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


    highDpi = props.Boolean(default=False)
    """If FSLeyes is being displayed on a high-DPI screen, try to display
    the scene at full resolution.
    """


    def __init__(self):
        """Create a ``SliceCanvasOpts`` instance. """

        self.__name = '{}_{}'.format(type(self).__name__, id(self))
        self.__xax  = 0
        self.__yax  = 0

        self.addListener('zax', self.__name, self.__zaxChanged, immediate=True)
        self.__zaxChanged()


    def __zaxChanged(self, *a):
        """Calle when the :attr:`zax` property changes. Derives the
        ``xax`` and ``yax`` values.
        """

        dims = list(range(3))
        dims.pop(self.zax)
        self.__xax = dims[0]
        self.__yax = dims[1]


    @property
    def xax(self):
        """The display coordinate system axis which maps to the X (horizontal)
        canvas axis.
        """
        return self.__xax


    @property
    def yax(self):
        """The display coordinate system axis which maps to the Y (vertical)
        canvas axis.
        """
        return self.__yax


class LightBoxCanvasOpts(SliceCanvasOpts):
    """The ``LightBoxCanvasOpts`` class defines the display settings
    available on :class:`.LightBoxCanvas` instances.
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


class Scene3DCanvasOpts(props.HasProperties):
    """The ``Scene3DCanvasOpts`` class defines the display settings
    available on :class:`.Scene3DCanvas` instances.
    """

    pos = copy.copy(SliceCanvasOpts.pos)
    """Current cursor position in the display coordinate system. The dimensions
    are in the same ordering as the display coordinate system, in contrast
    to the :attr:`SliceCanvasOpts.pos` property.
    """


    showCursor   = copy.copy(SliceCanvasOpts.showCursor)
    cursorColour = copy.copy(SliceCanvasOpts.cursorColour)
    bgColour     = copy.copy(SliceCanvasOpts.bgColour)
    zoom         = copy.copy(SliceCanvasOpts.zoom)
    highDpi      = copy.copy(SliceCanvasOpts.highDpi)


    showLegend = props.Boolean(default=True)
    """If ``True``, an orientation guide will be shown on the canvas. """


    legendColour = props.Colour(default=(0, 1, 0))
    """Colour to use for the legend text."""


    labelSize = props.Int(minval=4, maxval=96, default=12, clamped=True)
    """Font size used for the legend labels. """


    occlusion = props.Boolean(default=True)
    """If ``True``, objects closer to the camera will occlude objects
    further away. Toggles ``gl.DEPTH_TEST``.
    """


    light = props.Boolean(default=True)
    """If ``True``, a lighting effect is applied to compatible overlays
    in the scene.
    """


    showLight = props.Boolean(default=False)
    """If ``True``, a point is drawn at the current light position. """


    lightPos = props.Point(ndims=3)
    """Defines the light position in the display coordinate system. This
    property contains a set of three rotation values, in degrees.

    The lighting model uses a point source which is located a fixed distance
    away from the display coordinate system centre - the distance is set
    by the :attr:`lightDistance` property.

    The lightPos property defines how the light is rotated with respect to
    the centre of the display coordinate system.

    The :meth:`.Scene3DCanvas.lightPos` method can be used to calculate the
    actual position of the light in the display coordinate system.
    """


    lightDistance = props.Real(minval=0.5, maxval=10, default=2)
    """Distance of the light source from the centre of the display coordinate
    system. This is used as a multiplicative factor - a value of 2 set the
    light source a distance of twice the length of the display bounding box
    from the bounding box centre.
    """


    offset = props.Point(ndims=2)
    """An offset, in X/Y pixels normalised to the range ``[-1, 1]``, from the
    centre of the ``Scene3DCanvas``.
    """


    rotation = props.Array(
        dtype=np.float64,
        shape=(3, 3),
        resizable=False,
        default=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    """A rotation matrix which defines the current ``Scene3DCanvas`` view
    orientation. This rotation is defined in terms of the display coordinate
    system (defined by the :class:`.DisplayContext.bounds`), and applied to
    the scene that is being displayed.

    We use a rotation matrix here because it makes iterative updates of
    the camera position easier - see the :class:`.Scene3DViewProfile` class.
    """
