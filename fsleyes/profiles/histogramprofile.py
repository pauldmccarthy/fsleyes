#!/usr/bin/env python
#
# histogramprofile.py - The HistogramProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.HistogramProfile` class, an interaction
profile for the :class:`.HistogramPanel`.
"""


import logging

import numpy              as np
import matplotlib.patches as patches

import                       props

import fsleyes.overlay    as fsloverlay
from . import                plotprofile


log = logging.getLogger(__name__)


class HistogramProfile(plotprofile.PlotProfile):
    """
    """

    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create a ``HistogramProfile``.

        :arg viewPanel:    A :class:`.HistogramPanel` instance.

        :arg overlayList:  The :class:`.OverlayList` instance.

        :arg displayCtx:   The :class:`.DisplayContext` instance.
        """ 
        plotprofile.PlotProfile.__init__(self,
                                         viewPanel,
                                         overlayList,
                                         displayCtx,
                                         ['overlayRange'])

        self.__currentHs     = None
        self.__rangePolygon  = None
        self.__rangeOverlay  = None

        # This flag is raised when the user
        # is dragging the showOverlayRange
        # overlay on the plot. If the user
        # starts dragging the low or high
        # range values, this flag gets set
        # to 'lo' or 'hi' respectively.
        # Otherwise it is set to False.
        self.__draggingRange = False

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):

        self.__deregisterHistogramSeries()
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        plotprofile.PlotProfile.destroy(self)


    def __registerHistogramSeries(self, hs):

        hsPanel = self._viewPanel

        self.__rangePolygon = RangePolygon(
            hs,
            hsPanel,
            np.zeros((2, 2)),
            closed=True,
            edgecolor='black',
            facecolor=hs.colour,
            linewidth=3,
            alpha=0.3)

        self.__rangeOverlay = HistogramOverlay(
            hs,
            hs.overlay,
            self._displayCtx,
            self._overlayList)

    
    def __deregisterHistogramSeries(self):

        if self.__currentHs is None:
            return
        
        if self.__rangePolygon is not None:
            self.__rangePolygon.destroy()

        if self.__rangeOverlay is not None:
            self.__rangeOverlay.destroy()

        self.__rangePolygon = None
        self.__rangeOverlay = None


    def __selectedOverlayChanged(self, *a):

        overlay = self._displayCtx.getSelectedOverlay()
        oldHs   = self.__currentHs
        newHs   = self._viewPanel.getDataSeries(overlay)
        
        if oldHs == newHs:
            return

        self.__deregisterHistogramSeries()

        self.__currentHs = newHs

        if newHs is None:
            return
        
        self.__registerHistogramSeries(newHs)


    def __updateShowOverlayRange(self, datax, which=False):
        """
        """

        rangelo, rangehi = self.__currentHs.showOverlayRange

        
        if   which == 'lo': newRange = [datax,   rangehi]
        elif which == 'hi': newRange = [rangelo, datax]

        else:
            # Less than low range 
            if datax < rangelo:
                which    = 'lo'
                newRange =  (datax, rangehi)
            # Less than high range 
            elif datax > rangehi:
                which    = 'hi'
                newRange =  (rangelo, datax)

            # In between low/high ranges -
            # is the mouse location closer
            # to the low or high range?
            else:
                
                lodist = abs(datax - rangelo)
                hidist = abs(datax - rangehi)

                if lodist < hidist:
                    which    = 'lo'
                    newRange = [datax, rangehi]
                else:
                    which    = 'hi'
                    newRange = [rangelo, datax]

        if newRange[1] < newRange[0]:
            if   which == 'lo': newRange[0] = newRange[1]
            elif which == 'hi': newRange[1] = newRange[0]

        # The range polygon will automatically update itself
        # when any HistogramSeries properties change. But the
        # canvas draw is faster if we do it ourselves. Hence
        # the listener skip.
        with props.skip(self.__currentHs,
                        'showOverlayRange',
                        self.__rangePolygon._rp_name):
            self.__currentHs.showOverlayRange = newRange
            
        self.__rangePolygon.updatePolygon()
        self._viewPanel.drawArtists(immediate=True)
        return which 

    
    def _overlayRangeModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """
        """

        if self.__currentHs    is None: return False
        if self.__rangePolygon is None: return False
        if canvasPos           is None: return False 

        self.__draggingRange = self.__updateShowOverlayRange(canvasPos[0])

        return True


    def _overlayRangeModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):

        if not self.__draggingRange: return False
        if canvasPos is None:        return False

        self.__updateShowOverlayRange(canvasPos[0], self.__draggingRange) 

        return True


        
    def _overlayRangeModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):

        if not self.__draggingRange:
            return False

        self.__draggingRange = False
        return True



class RangePolygon(patches.Polygon):
    """
    """

    def __init__(self, hs, hsPanel, *args, **kwargs):
        """
        """
        patches.Polygon.__init__(self, *args, **kwargs)


        # Dodgily trying to avoid collisions
        # with any patches.Polygon attributes
        self._rp_hs      = hs
        self._rp_hsPanel = hsPanel
        self._rp_name    = '{}_{}'.format(type(self).__name__, id(self))

        hs.addGlobalListener(self._rp_name, self.updatePolygon)

        self.updatePolygon()


    def destroy(self):
        """
        """

        hs      = self._rp_hs
        hsPanel = self._rp_hsPanel

        hs.removeGlobalListener(self._rp_name)

        if self in hsPanel.artists:
            hsPanel.artists.remove(self)

        self._rp_hs      = None
        self._rp_hsPanel = None

        
    def updatePolygon(self, *a):
        """
        """

        hs       = self._rp_hs
        hsPanel  = self._rp_hsPanel

        # The HistogramSeries may
        # not yet have been plotted
        try:    hsArtist = hsPanel.getArtist(hs)
        except: return

        if not hs.showOverlay and self in hsPanel.artists:
            hsPanel.artists.remove(self)
            return

        if hsPanel.smooth:
            x        = hsArtist.get_xdata()
            y        = hsArtist.get_ydata()
            vertices = np.array([x, y]).T
        else:
            vertices = hs.getVertexData()

        if hsPanel.histType == 'probability':
            vertices[:, 1] /= hs.getNumHistogramValues()

        lo, hi   = hs.showOverlayRange
        mask     = (vertices[:, 0] >= lo) & (vertices[:, 0] <= hi)
        vertices = vertices[mask, :]

        # Happens if lo == hi. Create some dummy
        # vertices, so that something gets drawn.
        if vertices.size == 0:

            histx, histy = hs.getData()

            try:    xidx = np.where(histx[:] < hi)[0][-1]
            except: xidx = len(histy) - 1
                
            if xidx >= len(histy):
                xidx = -1

            yval = float(histy[xidx])

            if hsPanel.histType == 'probability':
                yval /= hs.getNumHistogramValues()

            vertices = np.array([[lo, 0], [lo, yval], [hi, yval], [hi, 0]])
        else:

            padVerts          = np.zeros((vertices.shape[0] + 4, 2))
            padVerts[2:-2, :] = vertices

            padVerts[ 0, 0] = lo
            padVerts[ 0, 1] = 0
            padVerts[ 1, 0] = lo
            padVerts[ 1, 1] = vertices[0, 1]

            padVerts[-2, 0] = hi
            padVerts[-2, 1] = vertices[-1, 1]
            padVerts[-1, 0] = hi
            padVerts[-1, 1] = 0

            vertices = padVerts

        self.set_xy(   vertices)
        self.set_color(hs.colour)

        if hs.showOverlay and self not in hsPanel.artists:
            hsPanel.artists.append(self)


class HistogramOverlay(object):
    """The ``HistogramOverlay`` class manages the creation, destruction, and
    display of a :class:`.ProxyImage` overlay which displays the voxels that
    are included in a histogram plot. The user can toggle the display of this
    overlay via the :attr:`.HistogramSeries.showOverlay` property.

    One ``HistogramOverlay`` is created by every :class:`.HistogramSeries``.
    """
    
    def __init__(self, histSeries, overlay, displayCtx, overlayList):
        """Create a ``HistogramOverlay``.

        :arg histSeries:  The :class:`.HistogramSeries` instance which owns
                          this ``HistobgramOverlay``.

        :arg overlay:     The :class:`.Image` overlay associated with this
                          ``HistogramOverlay``.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg overlayList: The :class:`.OverlayList` instance. 
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__histSeries  = histSeries
        self.__overlay     = overlay
        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__histMask    = None

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        histSeries.addListener('showOverlay',
                                self.__name,
                                self.__showOverlayChanged)


    def destroy(self):
        """Must be called when this ``HistogramOverlay`` is no longer needed.
        """

        self.__overlayList.removeListener('overlays',    self.__name)
        self.__histSeries .removeListener('showOverlay', self.__name)
        
        if self.__histMask is not None:
            self.__overlayList.remove(self.__histMask)

        self.__histSeries  = None
        self.__overlay     = None 
        self.__displayCtx  = None
        self.__overlayList = None
        self.__histMask    = None 


    def __showOverlayChanged(self, *a):
        """Called when the :attr:`.HistogramSeries.showOverlay` property
        changes.

        Adds/removes a 3D mask :class:`.Image` to the :class:`.OverlayList`,
        which highlights the voxels that have been included in the histogram.
        The :class:`.MaskOpts.threshold` property is bound to the
        :attr:`.HistogramSeries.showOverlayRange` property, so the masked
        voxels are updated whenever the histogram overlay range changes, and
        vice versa.
        """

        hs = self.__histSeries

        if      hs.showOverlay  and (self.__histMask is not None): return
        if (not hs.showOverlay) and (self.__histMask is     None): return 

        if not hs.showOverlay:

            log.debug('Removing 3D histogram overlay mask for {}'.format(
                self.__overlay.name))

            if self.__histMask in self.__overlayList:
                self.__overlayList.remove(self.__histMask)
                
            self.__histMask = None

        else:

            log.debug('Creating 3D histogram overlay mask for {}'.format(
                self.__overlay.name))
            
            self.__histMask = fsloverlay.ProxyImage(
                self.__overlay,
                name='{}/histogram/mask'.format(self.__overlay.name))

            self.__overlayList.append(self.__histMask, overlayType='mask')

            opts = self.__displayCtx.getOpts(self.__histMask)

            opts.bindProps('volume',    hs)
            opts.bindProps('colour',    hs)
            opts.bindProps('threshold', hs, 'showOverlayRange')


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.

        If a 3D mask overlay was being shown, and it has been removed from the
        ``OverlayList``, the :attr:`.HistogramSeries.showOverlay` property is
        updated accordingly.
        """
        
        if self.__histMask is None:
            return

        # If a 3D overlay was being shown, and it
        # has been removed from the overlay list
        # by the user, turn the showOverlay property
        # off
        if self.__histMask not in self.__overlayList:

            with props.skip(self.__histSeries, 'showOverlay', self.__name):
                self.__histSeries.showOverlay = False
                self.__showOverlayChanged()
