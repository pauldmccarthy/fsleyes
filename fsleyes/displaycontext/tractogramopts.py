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


    colourMode = props.Choice(('orientation',
                               'vertexData',
                               'streamlineData',
                               'imageData'))
    """Whether to colour streamlines by:
        - their orientation (e.g. RGB colouring)
        - by per-vertex data (see :attr:`vertexData`)
        - by per-streamline data (see :attr:`streamlineData`)
        - by data from an image (see :attr:`colourImage`)
    """


    clipBy = props.Choice((None,
                           'vertexData',
                           'streamlineData',
                           'imageData'))
    """Use a data set to clip/threshold the streamlines.
    When the colourMode is changed, this seting will automatically be
    changed to the same value (``None`` for ``'orientation'``). But
    it can then be set independently so, for example, you can colour
    streamlines according to orientation, but clip them according to
    per-vertex data.
    """


    vertexData = props.Choice((None,))
    """Per-vertex data set with which to colour the streamlines, when
    ``colourMode == 'vertexData'``.
    """


    streamlineData = props.Choice((None,))
    """Per-streamline data set with which to colour the streamlines, when
    ``colourMode == 'streamlineData'``.
    """


    colourImage = props.Choice((None,))
    """:class:`.Image` used to colour streamlines, when the :attr:`colourMode`
    is set to ``'imageData'``.
    """


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

        self .addListener('colourMode',     self.name, self.__dataChanged)
        self .addListener('clipBy',         self.name, self.__dataChanged)
        self .addListener('vertexData',     self.name, self.__dataChanged)
        self .addListener('streamlineData', self.name, self.__dataChanged)
        self .addListener('colourImage',    self.name, self.__dataChanged)
        olist.addListener('overlays',       self.name, self.__overlaysChanged)

        self.addVertexDataOptions(    self.overlay.vertexDataSets())
        self.addStreamlineDataOptions(self.overlay.streamlineDataSets())
        self.__overlaysChanged()
        self.__dataChanged()


    def destroy(self):
        """Removes property listeners. """
        self.overlayList.removeListener('overlays', self.name)
        fsldisplay.DisplayOpts.destroy(self)


    def __dataChanged(self, *_):
        """Called when :attr:`colourMode`, :attr:`vertexData`,
        :attr:`streamlineData`, or :attr:`colourImage` changes.
        Calls :meth:`.ColourMapOpts.updateDataRange`, to ensure that
        the display range is up to date.
        """
        self.updateDataRange()


    def __overlaysChanged(self, *_):
        """Called when the :class:`.OverlayList` changes. Updates the
        :attr:`colourImage` property.
        """
        cimageProp = self.getProp('colourImage')
        cimage     = self.colourImage
        overlays   = self.displayCtx.getOrderedOverlays()
        overlays   = [o for o in overlays if isinstance(o, fslimage.Image)]
        options    = [None] + overlays

        cimageProp.setChoices(options, instance=self)

        if cimage in options: self.colourImage = cimage
        else:                 self.colourImage = None


    def __getData(self, mode):
        """Used by :meth:`getDataRange` and :meth:`getClippingRange`. Returns
        a numpy array containing data to be used for colouring/clipping.

        :arg mode: Current value of :attr:`colourMode` or :attr:`clipBy`.
        """
        overlay = self.overlay
        vdata   = self.vertexData
        sdata   = self.streamlineData
        cimage  = self.colourImage

        if mode == 'vertexData' and vdata is not None:
            return overlay.getVertexData(vdata)
        elif mode == 'streamlineData'and sdata is not None:
            return overlay.getStreamlineData(sdata)
        elif mode == 'imageData' and cimage is not None:
            return cimage.data
        else:
            return None


    def getDataRange(self):
        """Overrides :meth:`.ColourMapOpts.getDataRange`. Returns the
        current data range to use for colouring - this depends on the
        current :attr:`colourMode`, and selected :attr:`vertexData`,
        :attr:`streamlineData`, or :attr:`colourImage`.
        """
        data = self.__getData(self.colourMode)
        if data is None: return 0, 1
        else:            return np.nanmin(data), np.nanmax(data)


    def getClippingRange(self):
        """Overrides :meth:`.ColourMapOpts.getClippingRange`. Returns the
        current data range to use for clipping/thresholding - this depends on
        the current :attr:`clipBy` value, and selected :attr:`vertexData`,
        :attr:`streamlineData`, or :attr:`colourImage`.
        """
        data = self.__getData(self.clipBy)
        if data is None: return None
        else:            return np.nanmin(data), np.nanmax(data)


    @property
    def effectiveColourMode(self):
        """Returns a string indicating how the tractogram should be coloured:
          - ``'orient'`` - colour by streamline orientation
          - ``'vdata'``  - colour by per vertex/streamline data
          - ``'idata'``  - colour by separate image
        """
        cmode  = self.colourMode
        sdata  = self.streamlineData
        vdata  = self.vertexData
        cimage = self.colourImage

        if   cmode == 'vertexData'     and vdata  is not None: return 'vdata'
        elif cmode == 'streamlineData' and sdata  is not None: return 'vdata'
        elif cmode == 'imageData'      and cimage is not None: return 'idata'
        else:                                                  return 'orient'


    @property
    def effectiveClipBy(self):
        """Returns a string indicating how the tractogram should be clipped:
          - ``None``     - No clipping
          - ``'vdata'``  - clip by per vertex/streamline data
          - ``'idata'``  - clip by separate image
        """
        cmode  = self.clipBy
        sdata  = self.streamlineData
        vdata  = self.vertexData
        cimage = self.colourImage

        if   cmode == 'vertexData'     and vdata  is not None: return 'vdata'
        elif cmode == 'streamlineData' and sdata  is not None: return 'vdata'
        elif cmode == 'imageData'      and cimage is not None: return 'idata'
        else:                                                  return None


    def addVertexDataOptions(self, paths):
        """Adds the given sequence of paths as options to the
        :attr:`vertexData` property. It is assumed that the paths refer
        to valid vertex data files for the overlay associated with this
        ``TractogramOpts`` instance.
        """
        self.__addDataSetOptions(self.getProp('vertexData'), paths)


    def addStreamlineDataOptions(self, paths):
        """Adds the given sequence of paths as options to the
        :attr:`streamlineData` property. It is assumed that the paths refer
        to valid streamline data files for the overlay associated with this
        ``TractogramOpts`` instance.
        """
        self.__addDataSetOptions(self.getProp('streamlineData'), paths)


    def __addDataSetOptions(self, prop, paths):
        """Used by :meth:`addVertexDataOptions` and
        :meth:`addStreamlineDataOptions`.
        """
        if len(paths) == 0:
            return
        newPaths = paths
        paths    = prop.getChoices(instance=self)
        paths    = paths + [p for p in newPaths if p not in paths]
        prop.setChoices(paths, instance=self)
