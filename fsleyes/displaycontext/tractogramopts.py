#!/usr/bin/env python
#
# tractogramopts.py - The TractogramOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TractogramOpts` class, which defines
display properties for :class:`.Tractogram` overlays.
"""


import numpy as np

import fsl.data.image                       as fslimage
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
        - by per-vertex or per-streamline data
        - by data from an image

    Per-vertex data sets and NIFTI images are dynamically added as options
    to this property.
    """

    # clipMode = props.Choice((None,))


    lineWidth = props.Int(minval=1, maxval=10, default=2)
    """Width to draw the streamlines. """


    resolution = props.Int(minval=1, maxval=10, default=3, clamped=True)
    """Only relevant when using OpenGL >= 3.3. Streamlines are drawn as tubes -
    this setting defines the resolution at which the tubes are drawn. IF
    resolution <= 2, the streamlines are drawn as lines.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``TractogramOpts``. """
        fsldisplay.DisplayOpts  .__init__(self, *args, **kwargs)
        cmapopts  .ColourMapOpts.__init__(self)
        vectoropts.VectorOpts   .__init__(self)

        olist         = self.overlayList
        lo, hi        = self.overlay.bounds
        xlo, ylo, zlo = lo
        xhi, yhi, zhi = hi
        self.bounds   = [xlo, xhi, ylo, yhi, zlo, zhi]

        self .addListener('colourMode', self.name, self.__colourModeChanged)
        olist.addListener('overlays',   self.name, self.updateColourMode)

        self.updateColourMode()
        self.__colourModeChanged()


    def destroy(self):
        """Removes property listeners. """
        self.overlayList.removeListener('overlays', self.name)
        fsldisplay.DisplayOpts.destroy(self)


    def updateColourMode(self, *_):
        """Called when the :class:`.OverlayList` changes, and may be called
        externally (see e.g. :func:`.loadvertexdata.loadVertexData`) .
        Refreshes the options available on the  the :attr:`colourMode`
        property - ``'orientation'``, all vertex data sets on the
        :class:`.Tractogram` overlay, and all :class:`.Image` overlays
        in the :class:`.OverlayList`.
        """

        overlay   = self.overlay
        cmodeProp = self.getProp('colourMode')
        cmode     = self.colourMode

        vdata     = overlay.vertexDataSets()
        overlays  = self.displayCtx.getOrderedOverlays()
        overlays  = [o for o in overlays if isinstance(o, fslimage.Image)]

        options   = ['orientation'] + overlays + vdata

        cmodeProp.setChoices(options, instance=self)

        # Preserve previous value, or
        # default to orientation
        if cmode in options: self.colourMode = cmode
        else:                self.colourMode = 'orientation'


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


    def __colourModeChanged(self, *_):
        """Called when :attr:`colourMode`, :attr:`vertexData`, or
        :attr:`colourImage` changes.  Calls
        :meth:`.ColourMapOpts.updateDataRange`, to ensure that the display
        range is up to date.
        """
        self.updateDataRange()


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
        return None

        # TODO
        if self.colourMode != 'orientation':
            return None
        data = self.__getData('vertexData')
        if data is None: return None
        else:            return np.nanmin(data), np.nanmax(data)
