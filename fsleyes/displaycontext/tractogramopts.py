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
import fsl.transform.affine                 as affine
import fsleyes.gl                           as fslgl
import fsleyes.strings                      as strings
import fsleyes_props                        as props
import fsleyes.displaycontext.display       as fsldisplay
import fsleyes.displaycontext.colourmapopts as cmapopts
import fsleyes.displaycontext.vectoropts    as vectoropts


class TractogramOpts(fsldisplay.DisplayOpts,
                     cmapopts.ColourMapOpts,
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


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``TractogramOpts`` instance. """

        # Default to drawing a random sub-sample
        # of streamlines for large tractograms
        if overlay.nstreamlines > 150000:
            self.subsample = 15000000 / overlay.nstreamlines

        fsldisplay.DisplayOpts  .__init__(self, overlay, *args, **kwargs)
        cmapopts  .ColourMapOpts.__init__(self)
        vectoropts.VectorOpts   .__init__(self)

        olist         = self.overlayList
        lo, hi        = self.overlay.bounds
        xlo, ylo, zlo = lo
        xhi, yhi, zhi = hi
        self.bounds   = [xlo, xhi, ylo, yhi, zlo, zhi]

        self .addListener('colourMode', self.name, self.__colourModeChanged)
        self .addListener('clipMode',   self.name, self.__clipModeChanged)
        olist.addListener('overlays',   self.name, self.updateColourClipModes)

        self.updateColourClipModes()
        self.updateDataRange()


    def destroy(self):
        """Removes property listeners. """
        self.overlayList.removeListener('overlays', self.name)
        fsldisplay.DisplayOpts.destroy(self)


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


    def updateColourClipModes(self, *_):
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


    @property
    def displayTransform(self):
        """Return an affine transformation which will transform streamline
        vertex coordinates into the current display coordinate system.
        """
        ref = self.displayCtx.displaySpace

        if not isinstance(ref, fslimage.Image):
            return np.eye(4)

        opts = self.displayCtx.getOpts(ref)

        return opts.getTransform('world', 'display')


    def sliceWidth(self, zax):
        """Returns a width along the specified **display** coordinate system
        axis, to be used for drawing a 2D slice through the tractogram on the
        axis plane.
        """

        # The z axis is specified in terms of
        # the display coordinate system -
        # identify the corresponding axis in the
        # tractogram/world coordinate system.
        codes = [[0, 0], [1, 1], [2, 2]]
        xform = affine.invert(self.displayTransform)
        zax   = nib.orientations.aff2axcodes(xform, codes)[zax]

        los, his = self.overlay.bounds
        zlen     = his[zax] - los[zax]
        return zlen / 200


    def __colourModeChanged(self, *_):
        """Called when :attr:`colourMode` changes.  Calls
        :meth:`.ColourMapOpts.updateDataRange`, to ensure that the display
        and clipping ranges are up to date.
        """
        self.updateDataRange(resetCR=(self.clipMode is None))


    def __clipModeChanged(self, *_):
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
