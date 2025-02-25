#!/usr/bin/env python
#
# tractogramopts.py - The TractogramOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TractogramOpts` class, which defines
display properties for :class:`.Tractogram` overlays.
"""


import numpy   as np
import nibabel as nib

import fsl.data.image                       as fslimage
import fsleyes.strings                      as strings
import fsleyes_props                        as props
import fsleyes.displaycontext.display       as fsldisplay
import fsleyes.displaycontext.colourmapopts as cmapopts
import fsleyes.displaycontext.vectoropts    as vectoropts
import fsleyes.displaycontext.refimageopts  as refimgopts


class TractogramOpts(fsldisplay.DisplayOpts,
                     cmapopts.ColourMapOpts,
                     refimgopts.RefImageOpts,
                     vectoropts.VectorOpts):
    """Display options for :class:`.Tractogram` overlays. """


    colourMode = props.Choice(('orientation',))
    """Whether to colour streamlines by:
        - their orientation (e.g. RGB colouring)
        - per-vertex or per-streamline data
        - data from an image

    Per-vertex data sets and NIFTI images are dynamically added as options
    to this property.
    """


    clipMode = props.Choice((None,))
    """Whether to clip streamlines by:
        - per-vertex or per-streamline data
        - data from an image

    Per-vertex data sets and NIFTI images are dynamically added as options
    to this property.
    """


    lineWidth = props.Real(minval=1, maxval=10, default=2)
    """Width to draw the streamlines. When drawing in 3D, this controls the
    line width / tube diameter. When drawing in 2D, this controls the point
    diameter.
    """


    sliceWidth = props.Percentage(default=1)
    """Width of the slice to draw, when drawing 2D slices/cross-sections,
    either when:
    - :attr:`pseudo3D` is ``False``, or
    - :attr:`pseudo3D` is ``True``, and the ``clipdir`` setting for the
       axis being drawn is is ``'slice'``.

    When a :attr:`refImage` is set, the width is specified in terms of the
    reference image voxel size along each axis. Otherwise it is specified as
    a percentage of the tractogram bounding box along each axis. In either
    case, use the :meth:`calculateSliceWidth` method to calculate a width in
    the display coordinate system.
    """


    resolution = props.Int(minval=1, maxval=10, default=1, clamped=True)
    """When drawing in 3D as tubes, or in 2D as circles, this setting defines
    the resolution at which the tubes/circles are drawn. In 3D, if
    resolution <= 2, the streamlines are drawn as lines. In 2D, the
    resolution is clamped to a minimum of 3, with the effect that streamline
    vertices are drawn as triangles.
    """


    subsample = props.Percentage(default=100)
    """Draw a random sub-sample of all streamlines. This is useful when drawing
    very large tractograms.
    """


    pseudo3D = props.Boolean(default=False)
    """When drawing to a 2D canvas (e.g. an :class:`.OrthoPanel`), this
    property controls whether the tractogram is drawn as a 2D cross-section of
    individual vertices, or as pseudo-3D streamlines overlaid on top of the
    2D canvas.
    """


    xclipdir = props.Choice(('low', 'high', 'slice', 'none'))
    """Clipping direction along the X axis when :attr:`pseudo3D` is active.
    This property controls whether areas of the tractogram are clipped along
    the the depth axis:

    - ``'slice'``: Areas below and above the current depth are clipped
    - ``'low'``:   Areas below the current depth are clipped
    - ``'high'``:  Areas above the current depth are clipped
    - ``'none'``:  No clipping - the entire tractogram is drawn
    """


    yclipdir = props.Choice(('low', 'high', 'slice', 'none'))
    """Clipping direction along the X axis when :attr:`pseudo3D` is active. """


    zclipdir = props.Choice(('low', 'high', 'slice', 'none'))
    """Clipping direction along the Z axis when :attr:`pseudo3D` is active. """


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``TractogramOpts`` instance. """

        # Default to drawing a random sub-sample
        # of streamlines for large tractograms
        if overlay.nstreamlines > 150000:
            self.subsample = 15000000 / overlay.nstreamlines

        # nibabel.streamlines.Tractogram vertices
        # should be defined in mm coordinates
        self.getProp('coordSpace').setDefault('affine', self)
        self.coordSpace = 'affine'

        nounbind = kwargs.get('nounbind', [])
        nounbind.extend(['refImage', 'coordSpace'])
        kwargs['nounbind'] = nounbind

        fsldisplay.DisplayOpts  .__init__(self, overlay, *args, **kwargs)
        cmapopts  .ColourMapOpts.__init__(self)
        refimgopts.RefImageOpts .__init__(self)
        vectoropts.VectorOpts   .__init__(self)

        self.__child = self.getParent() is not None

        if self.__child:

            olist = self.overlayList

            self .listen('colourMode', self.name, self.__colourModeChanged)
            self .listen('clipMode',   self.name, self.__clipModeChanged)
            olist.listen('overlays',   self.name, self.updateColourClipModes)

            self.updateColourClipModes()
            self.updateDataRange()


    def getBounds(self):
        """Overrides :meth:`.RefImageOpts.getBounds`. Returns the
        tractogram vertex bounds in its native coordinate system.
        """
        return self.overlay.bounds


    def destroy(self):
        """Removes property listeners. """
        if self.__child:
            self.overlayList.removeListener('overlays', self.name)
            self.remove('clipMode',   self.name)
            self.remove('colourMode', self.name)
        cmapopts.ColourMapOpts .destroy(self)
        refimgopts.RefImageOpts.destroy(self)
        fsldisplay.DisplayOpts .destroy(self)


    @property
    def effectiveColourMode(self):
        """Returns one of ``'orientation'``, ``'vertexData'``, or
        ``'imageData'``, depending on the current :attr:`colourMode`.
        """
        ovl   = self.overlay
        cmode = self.colourMode
        if   isinstance(cmode, fslimage.Image): return 'imageData'
        elif cmode in ovl.vertexDataSets():     return 'vertexData'
        else:                                   return 'orientation'


    @property
    def effectiveClipMode(self):
        """Returns one of ``'none'``, ``'vertexData'``, or
        ``'imageData'``, depending on the current :attr:`clipMode`.
        """
        ovl   = self.overlay
        cmode = self.clipMode
        if   isinstance(cmode, fslimage.Image): return 'imageData'
        elif cmode in ovl.vertexDataSets():     return 'vertexData'
        else:                                   return 'none'


    def getLabels(self):
        """Overrides :meth:`.DisplayOpts.getLabele`. Returns orientation
        labels and codes for the coordinate system in which the streamline
        vertices are defined.
        """
        xorient, yorient, zorient  = self.overlay.orientation
        xlo = strings.anatomy['Nifti', 'lowshort',  xorient]
        ylo = strings.anatomy['Nifti', 'lowshort',  yorient]
        zlo = strings.anatomy['Nifti', 'lowshort',  zorient]
        xhi = strings.anatomy['Nifti', 'highshort', xorient]
        yhi = strings.anatomy['Nifti', 'highshort', yorient]
        zhi = strings.anatomy['Nifti', 'highshort', zorient]

        return ((xlo, ylo, zlo, xhi, yhi, zhi),
                (xorient, yorient, zorient))


    def getDataRange(self):
        """Overrides :meth:`.ColourMapOpts.getDataRange`. Returns the
        current data range to use for colouring - this depends on the
        current :attr:`colourMode`, and selected :attr:`vertexData` or
        :attr:`colourImage`.
        """
        data = self.__getData(self.colourMode)
        if data is None: return 0, 1
        else:            return np.nanmin(data), np.nanmax(data)


    def getClippingRange(self):
        """Overrides :meth:`.ColourMapOpts.getClippingRange`. Returns the
        current data range to use for clipping/thresholding - this depends on
        the selected :attr:`colourMode` and :attr:`vertexData` - if
        ``colourMode == 'orientation'``, the data may be clipped according
        to per-vertex data. Otherwise the clipping range will be equal to the
        display range.
        """

        colourMode = self.colourMode
        clipMode   = self.clipMode

        # if clipMode == colourMode, the same
        # data set that is used for colouring
        # will also be used for clipping
        if clipMode in (None, colourMode):
            return None

        data = self.__getData(clipMode)

        if data is None: return None
        else:            return np.nanmin(data), np.nanmax(data)


    def updateColourClipModes(self):
        """Called when the :class:`.OverlayList` changes, and may be called
        externally (see e.g. :func:`.loadvertexdata.loadVertexData`) .
        Refreshes the options available on the :attr:`colourMode` and
        :attr:`clipMode` properties - ``'orientation'``, all vertex data
        sets on the :class:`.Tractogram` overlay, and all :class:`.Image`
        overlays in the :class:`.OverlayList`.
        """

        overlay    = self.overlay
        colourProp = self.getProp('colourMode')
        colour     = self.colourMode
        clipProp   = self.getProp('clipMode')
        clip       = self.clipMode

        vdata     = overlay.vertexDataSets()
        overlays  = self.displayCtx.getOrderedOverlays()
        overlays  = [o for o in overlays if isinstance(o, fslimage.Image)]

        colourOptions = ['orientation'] + overlays + vdata
        clipOptions   = [None]          + overlays + vdata

        colourProp.setChoices(colourOptions, instance=self)
        clipProp  .setChoices(clipOptions,   instance=self)

        # Preserve previous value,
        # or revert to default
        if colour in colourOptions: self.colourMode = colour
        else:                       self.colourMode = 'orientation'
        if clip   in clipOptions:   self.clipMode   = clip
        else:                       self.clipMode   = None


    def calculateSliceWidth(self, zax):
        """Returns a width along the specified **display** coordinate system
        axis, to be used for drawing a 2D slice through the tractogram on the
        axis plane. The width is derived from the current :attr:`sliceWidth`
        value.
        """

        ref   = self.refImage
        width = self.sliceWidth

        # Clip according the width of the
        # tractogram bounding box along the
        # Z axis.
        if ref is None:
            # The z axis is specified in terms of
            # the display coordinate system -
            # identify the corresponding axis in the
            # tractogram/world coordinate system.
            codes = [[0, 0], [1, 1], [2, 2]]
            xform = self.getTransform(from_='display')
            zax   = nib.orientations.aff2axcodes(xform, codes)[zax]

            # Calculate <sliceWidth> percent
            # of the Z axis bounds
            los, his = self.overlay.bounds
            zlen     = his[zax] - los[zax]

            return (width * zlen) / 200

        # Clip to N voxels in terms of the reference image
        else:
            # Identify the voxel axis corresponding
            # to the requested display axis, and
            # return a width in terms of its pixdim
            axes  = ref.axisMapping(self.getTransform('display', 'voxel'))
            zax   = abs(axes[zax] - 1)
            zlen  = ref.pixdim[zax]
            return width * zlen


    def __colourModeChanged(self):
        """Called when :attr:`colourMode` changes.  Calls
        :meth:`.ColourMapOpts.updateDataRange`, to ensure that the display
        and clipping ranges are up to date.
        """
        self.updateDataRange(resetCR=(self.clipMode is None))


    def __clipModeChanged(self):
        """Called when :attr:`clipMode` changes.  Calls
        :meth:`.ColourMapOpts.updateDataRange`, to ensure that the display
        and clipping ranges are up to date.
        """
        self.updateDataRange(resetDR=False)


    def __getData(self, mode):
        """Used by :meth:`getDataRange` and :meth:`getClippingRange`. Returns
        a numpy array containing data to be used for colouring/clipping.

        :arg mode: Current value of :attr:`colourMode` or :attr:`clipMode`.
        """
        overlay = self.overlay

        if isinstance(mode, fslimage.Image):
            return mode.data
        elif mode in overlay.vertexDataSets():
            return overlay.getVertexData(mode)
        # mode == 'orientation', or an invalid value
        else:
            return None
