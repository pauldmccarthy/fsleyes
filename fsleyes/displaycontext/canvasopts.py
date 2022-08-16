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
    """The currently displayed position. This is in the display coordinate
    system, but transposed in terms of the :attr:`zax`.

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

    cursorWidth = props.Real(minval=1, default=1, maxval=10)
    """Width in pixels (approx) of the location cursor. """


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

    This setting is coupled to the :attr:`.SceneOpts.performance` setting.

    See the :class:`.SliceCanvas` for more details.
    """


    highDpi = props.Boolean(default=False)
    """If FSLeyes is being displayed on a high-DPI screen, try to display
    the scene at full resolution.
    """


    def __init__(self):
        """Create a ``SliceCanvasOpts`` instance. """

        self.__name = f'{type(self).__name__}_{id(self)}'
        self.__xax  = 0
        self.__yax  = 0

        self.addListener('zax', self.__name, self.__zaxChanged, immediate=True)
        self.__zaxChanged()


    @property
    def name(self):
        """Returns a unique name for this ``SliceCanvasOpts`` instance. """
        return self.__name


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


    def __zaxChanged(self, *a):
        """Calle when the :attr:`zax` property changes. Derives the
        ``xax`` and ``yax`` values.
        """

        dims = list(range(3))
        dims.pop(self.zax)
        self.__xax = dims[0]
        self.__yax = dims[1]


class LightBoxCanvasOpts(SliceCanvasOpts):
    """The ``LightBoxCanvasOpts`` class defines the display settings
    available on :class:`.LightBoxCanvas` instances.
    """


    sliceSpacing = props.Real(clamped=True,
                              minval=0.001,
                              maxval=0.25,
                              default=0.01)
    """This property controls the spacing between slices. It is defined
    as a percentage (0-1) of the Z axis length.
    """


    zrange = props.Bounds(ndims=1, minval=0, maxval=1)
    """This property controls the range of the slices to be displayed.
    The low/high limits are specified as percentages (0-1) of the Z axis
    length.

    This property is automatically synchronised with the
    :attr:`.SliceCanvasOpts.zoom` property.
    """


    ncols = props.Int(default=0, minval=0, clamped=True)
    """Number of columns to display. The default value (0) will cause
    the number of columns to be automatically calculated.
    """


    nrows = props.Int(default=0, minval=0, clamped=True)
    """Number of rows to display. The default value (0) will cause
    the number of rows to be automatically calculated. If both ``nrows``
    and :attr:`ncols` are set, ``nrows`` may be adjusted to honour
    the current :attr:`ncols`, :attr:`zrange` and :attr:`sliceSpacing`.
    """


    showGridLines = props.Boolean(default=False)
    """If ``True``, grid lines are drawn between the displayed slices. """


    highlightSlice = props.Boolean(default=False)
    """If ``True``, a box will be drawn around the slice containing the current
    location.
    """


    renderMode = props.Choice(('onscreen', 'offscreen'))
    """How the :class:`.GLObject` instances are rendered to the canvas.

    This setting is coupled to the :attr:`.LightBoxOpts.performance` setting.

    See the :class:`.LightBoxCanvas` for more details.
    """


    def __init__(self):
        super().__init__()
        self.setatt('zax',  'default', 2)
        self.setatt('zoom', 'default', 0)
        self.setatt('zoom', 'minval',  0)
        self.setatt('zoom', 'maxval',  1)
        self.setatt('zoom', 'clamped', True)

        self.zax    = 2
        self.zoom   = 0
        self.zrange = 0, 1

        name = self.name
        self.ilisten('zoom',         name, self.__zoomChanged)
        self.ilisten('zrange',       name, self.__zrangeChanged)
        self.ilisten('sliceSpacing', name, self.__sliceSpacingChanged)


    def __zoomChanged(self):
        """Called when :attr:`SliceCanvasOpts.zoom` changes. Propagates the
        change to the :attr:`zrange`.
        """

        # Map zoom to z range [sliceSpacing, 1], where:
        #
        #  - sliceSpacing == zoomed in, one slice displayed
        #  - 1            == zoomed out, all slices displayed
        newzlen = max(1 - self.zoom, self.sliceSpacing)
        zlo     = self.zrange.xlo
        zlen    = self.zrange.xlen

        # Preserving the z range centre
        zcentre = zlo     + zlen    / 2
        newzlo  = zcentre - newzlen / 2
        newzhi  = zcentre + newzlen / 2

        # But restricting the range to [0, 1]
        if newzlo < 0:
            newzhi -= newzlo
            newzlo  = 0
        elif newzhi > 1:
            newzlo -= (newzhi - 1)
            newzhi  = 1

        with props.skip(self, 'zrange', self.name):
            self.zrange = newzlo, newzhi


    def __sliceSpacingChanged(self):
        """Called when :attr:`sliceSpacing` changes. Sets some constraints
        on :attr:`zrange`.
        """
        spacing = self.sliceSpacing
        self.setatt('zrange', 'minDistance', spacing)


    def __zrangeChanged(self):
        """Called when :attr:`zrange` changes. Propagates the change to the
        :attr:`SliceCanvasOpts.zoom`.
        """
        with props.skip(self, 'zoom', self.name):
            self.zoom = 1 - self.zrange.xlen


    @property
    def nslices(self):
        """Returns the total number of slices that should currently be displayed,
        i.e. that fit within the current :attr:`zrange`. This is automatically
        calculated from the current :attr:`zrange` and :attr:`sliceSpacing`
        settings.

        Note that this may be different to the :meth:`.LightBoxCanvas.nslices`,
        which returns the total number of slices that can be displayed on the
        canvas (i.e. nrows * ncols).
        """
        # round to avoid floating point imprecision
        nslices = self.zrange.xlen / self.sliceSpacing
        return int(np.ceil(np.round(nslices, 5)))


    @property
    def maxslices(self):
        """Returns the maximum number of slices that would be displayed when
        the z range is set to [0, 1]. This is calculated from the current
        :attr:`sliceSpacing`.
        """
        nslices = 1 / self.sliceSpacing
        return int(np.round(nslices))


    @property
    def slices(self):
        """Returns the locations of all slices as values between 0 and 1. Use
        the :meth:`startslice` to identify the index of the starting slice to
        be displayed. The locations correspond to slice centres.
        """
        sliceSpacing = self.sliceSpacing
        return np.arange(sliceSpacing / 2, 1, sliceSpacing)


    @property
    def startslice(self):
        """Returns the index of the first slice to be displayed.
        """
        zlo          = self.zrange.xlo
        sliceSpacing = self.sliceSpacing
        return int(np.floor(zlo / sliceSpacing))


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
