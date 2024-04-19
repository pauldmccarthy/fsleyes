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
    available on :class:`.LightBoxCanvas` instances. This class also
    provides a set of utility methods for managing and calculating slice
    positions.

    The Z axis of the display coordinate system (controlled by the
    :attr:`zax` property) is divided up into slices, which are defined
    in a "slice coordinate system" having range 0 to 1, according to the
    :attr:`zrange` and :attr:`sliceSpacing` properties.

    Two sampling regimes are supported, controlled by the :attr:`sampleSlices`
    property.  In the first regime (``sampleSlices = 'centre'``), the entire
    0-1 range is divided into N slices, and each slice is sampled at its
    centre. The slices within which the low and high ``zrange`` bound are
    located determine the first and last slices to be displayed::

                           zlo                     zhi
                            |                       |
                      0                                       1
        slice centre  |   *       *       *       *       *   |
        slice index   |   0   |   1   |   2   |   3   |   4   |
                      |-------|
                       spacing

    where ``*`` denotes the slice sampling points - these correspond to the Z
    positions returned by the :meth:`slices` property.

    In the second regime (``sampleSlices = 'start'``), the 0-1 range is
    divided into N slices such that the low ``zrange`` bound falls at the
    beginning of a slice. Each slice is sampled at its beginning::

                          zlo                        zhi
                           |                          |
                      0                                       1
        slice start   |    |*      |*      |*      |*      |* |
        slice index   |  0 |   1   |   2   |   3   |   4   |  |
                           |-------|
                            spacing

    The first ``'centre'`` regime is the default, and is useful when viewing
    overlays with different dimensions, where the specific slices being
    displayed are not important. The second ``'start'`` regime is useful when a
    specific starting slice is desired. See the :class:`.LightBoxSamplePanel`
    for an example using the :attr:`sampleSlices` property.
    """


    sliceSpacing = props.Real(clamped=True,
                              minval=0.001,
                              maxval=0.25,
                              default=0.01)
    """This property controls the spacing between slices. It is defined
    as a percentage (0-1) of the Z axis length.
    """


    zrange = props.Bounds(ndims=1, minval=0, maxval=1, default=(0.4, 0.6))
    """This property controls the range of the slices to be displayed.
    The low/high limits are specified as percentages (0-1) of the Z axis
    length.

    This property is automatically synchronised with the
    :attr:`.SliceCanvasOpts.zoom` property.

    The :meth:`normzrange` and :meth:`normzlen` properties should usually be
    used in preference to the raw ``zrange`` values - this is because the Z
    range of slices that end up being displayed may not precisely match the
    ``zrange`` values, as each slice is internally modelled so as to have a Z
    width of ``sliceSpacing``.
    """


    zax = props.Choice((2, 0, 1),
                       alternates=[['z', 'Z'], ['x', 'X'], ['y', 'Y']],
                       allowStr=True)
    """Equivalent to :attr:`.SliceCanvasOpts.zax`, but with a different
    default.
    """


    zoom = props.Percentage(minval=0,
                            maxval=1,
                            default=0,
                            clamped=True)
    """The :attr:`.DisplayContext.bounds` are divided by this zoom
    factor to produce the canvas display bounds.
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


    labelSpace = props.Choice(('none', 'voxel', 'world'))
    """If not ``'none'`` the current location along the depth axis is shown on
    each slice, in either the ``'voxel'`` or ``'world'`` coordinate system,
    with respect to the currently selected overlay.
    """


    labelSize = props.Int(minval=4, maxval=96, default=10, clamped=True)
    """Font size used for slice location labels. """


    fgColour = props.Colour(default=(1, 1, 1))
    """Colour to use for slice location labels."""


    renderMode = props.Choice(('onscreen', 'offscreen'))
    """How the :class:`.GLObject` instances are rendered to the canvas.

    This setting is coupled to the :attr:`.LightBoxOpts.performance` setting.

    See the :class:`.LightBoxCanvas` for more details.
    """


    reverseSlices = props.Boolean(default=False)
    """Controls whether slices are drawn from low Z value to high Z value
    (``False``, the default) or from high Z value to low Z value (``True``).
    """


    sliceOverlap = props.Percentage(minval=0, maxval=75, default=0,
                                    clamped=True)
    """How much the slice rows/columns overlap with each other. Can range
    from 0 (default, no overlap) to 50 (50% overlap along both horizontal
    and vertical axes).
    """


    reverseOverlap = props.Boolean(default=False)
    """When ``sliceOverlap > 0``, adjacent slices will be drawn on top of each
    other. This property controls the order in which slices are drawn. The
    default value (``'+'``) will cause slices with a low Z value to be drawn
    first, with the effect that slices with higher Z values will be drawn on
    top. When this property is set to ``'-'``, the drawing order is reversed,
    so slices with a lower Z value will be drawn on top.
    """


    sampleSlices = props.Choice(('centre', 'start'))
    """Controls whether the slice positions returned by :meth:`slices`
    correspond to slice centres or to slice starts. This is used by the
    :class:`.LightBoxSampleDialog`, which allows the user to select slices
    in terms of voxel coordinates.
    """


    def __init__(self):
        super().__init__()
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
    def normzrange(self):
        """Returns :attr:`zrange`, adjusted to respect the
        :attr:`sliceSpacing`.
        """
        start    = self.startslice
        end      = start + self.nslices
        ssp      = self.sliceSpacing
        return start * ssp, end * ssp


    @property
    def normzlen(self):
        """Returns the length of :attr:`zrange`, adjusted to respect the
        :attr:`sliceSpacing`.
        """
        zlo, zhi = self.normzrange
        return zhi - zlo


    @property
    def nslices(self):
        """Returns the total number of slices that should currently be
        displayed, i.e. that fit within the current :attr:`zrange`. This is
        automatically calculated from the current :attr:`zrange` and
        :attr:`sliceSpacing` settings.

        Note that this may be different to the :meth:`.LightBoxCanvas.nslices`,
        which returns the total number of slices that can be displayed on the
        canvas (i.e. nrows * ncols).
        """
        # round to avoid floating point imprecision
        nslices = np.round(self.zrange.xlen / self.sliceSpacing, 5)
        return int(np.ceil(nslices))


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
        ssp = self.sliceSpacing

        # ssp / 2 -> sampling from slice centres
        if self.sampleSlices == 'centre':
            start = ssp / 2

        # Sample from slice beginning. Start slices
        # at a location such that zlo is located
        # at the beginning of a slice.

        # Add a small fixed offset to ensure that
        # we're within the region corresponding to
        # each slice, as otherwise e.g. the first
        # two slices [0.0, <sliceSpacing>] may
        # resolve to the same slice.
        else:
            zlo    = self.zrange.xlo
            start  = zlo - ssp * np.floor(zlo / ssp)
            start += 0.0001

        return np.arange(start, 1, ssp)


    @property
    def startslice(self):
        """Returns the index of the first slice to be displayed. """
        sliceSpacing = self.sliceSpacing
        zlo          = self.zrange.xlo
        startslice   = np.round(zlo / sliceSpacing, 5)
        return int(np.floor(startslice))


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
