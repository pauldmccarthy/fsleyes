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

import fsleyes_props      as props
import fsl.utils.idle     as idle
import fsl.data.image     as fslimage

import fsleyes.overlay    as fsloverlay
from . import                plotprofile


log = logging.getLogger(__name__)


class HistogramProfile(plotprofile.PlotProfile):
    """The ``HistogramProfile`` class is an interaction profile for use with
    :class:`.HistogramPanel` views. In addition to the behaviour provided by
    :class:`.PlotProfile`, the ``HistogramProfile`` implements the
    ``overlayRange`` mode, which allows the user to select the
    :attr:`.HistogramSeries.showOverlayRange`, for the currently selected
    overlay, by clicking and dragging on the plot.  This behaviour is only
    enabled when the :attr:`.HistogramSeries.showOverlay` property ``True``.


    For each plotted :class:`.HistogramSeries`, the ``HistogramProfile`` class
    creates and manages a :class:`HistogramOverlay` (which shows a 3D overlay
    of the voxels included in the histogram), and a :class:`RangePolygon`
    (which shows the 3D overlay range on the plot). The user can click and drag
    on the plot to adjust the extent of the :class:`RangePolygon`, which is
    linked to the mask :class:`.Image` managed by the
    :class:`.HistogramOverlay`.
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
        self.__rangePolygons = {}
        self.__rangeOverlays = {}

        # This flag is raised when the user
        # is dragging the showOverlayRange
        # overlay on the plot. If the user
        # starts dragging the low or high
        # range values, this flag gets set
        # to 'lo' or 'hi' respectively.
        # Otherwise it is set to False.
        self.__draggingRange = False

        overlayList.addListener('overlays',
                                self.name,
                                self.__overlayListChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``HistogramProfile`` is no longer needed.
        Removes property listeners, and cleans some things up.
        """

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)

        for hs in list(self.__rangePolygons.keys()):
            self.__deregisterHistogramSeries(hs)

        self.__rangePolygons = None
        self.__rangeOverlays = None

        plotprofile.PlotProfile.destroy(self)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Cleans up some
        things related to overlays that are no longer in the list.
        """

        for hs in list(self.__rangePolygons.keys()):
            if hs.overlay not in self.overlayList:
                self.__deregisterHistogramSeries(hs)

        self.__selectedOverlayChanged()


    def __registerHistogramSeries(self, hs):
        """Called when a new :class:`.HistogramSeries` is plotted. Creates
        a :class:`.HistogramOverlay` and a :class:`.RangePolygon` for the
        series.
        """

        if hs is None:                 return
        if hs in self.__rangePolygons: return

        rangePolygon = RangePolygon(
            hs,
            self.viewPanel,
            np.zeros((2, 2)),
            closed=True,
            linewidth=2)

        rangeOverlay = HistogramOverlay(
            hs,
            hs.overlay,
            self.displayCtx,
            self.overlayList)

        self.__rangePolygons[hs] = rangePolygon
        self.__rangeOverlays[hs] = rangeOverlay


    def __deregisterHistogramSeries(self, hs):
        """Called when a :class:`.HistogramSeries` is no longer to be plotted.
        Destroys the :class:`.HistogramOverlay` and :class:`.RangePolygon`
        associated with the series.
        """

        rangePolygon = self.__rangePolygons.pop(hs, None)
        rangeOverlay = self.__rangeOverlays.pop(hs, None)

        if rangePolygon is not None: rangePolygon.destroy()
        if rangeOverlay is not None: rangeOverlay.destroy()


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        Makes sure that a :class:`HistogramOverlay` and :class:`RangePolygon`
        exist for the newly selected overlay.
        """

        overlay = self.displayCtx.getSelectedOverlay()
        oldHs   = self.__currentHs
        newHs   = self.viewPanel.getDataSeries(overlay)

        if oldHs == newHs:
            return

        if isinstance(overlay, fslimage.Image):
            self.__currentHs = newHs
            self.__registerHistogramSeries(newHs)
        else:
            self.__currentHs = None


    def __updateShowOverlayRange(self, datax, which=False):
        """Called by the ``overlayRange`` mouse event handlers.  Updates the
        :attr:`.HistogramSeries.showOverlayRange`.

        :arg datax: X data coordinate corresponding to the mouse position.

        :arg which: Used to keep track of which value in the
                    ``showOverlayRange`` property the user is currently
                    modifying. On mouse down events, this method figures out
                    which range should be modified, and returns either
                    ``'lo'`` or ``'hi'``. On subsequent calls to this method
                    (on mouse drag and mouse up events), that return value
                    should be passed back into this method so that the same
                    value continues to get modified.
        """

        hs           = self.__currentHs
        rangePolygon = self.__rangePolygons.get(hs, None)

        if hs           is None: return
        if rangePolygon is None: return

        rangelo, rangehi = hs.showOverlayRange

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
        # canvas draw is faster if we do it manually. Hence
        # the listener skip.
        with props.skip(hs, 'showOverlayRange', rangePolygon._rp_name):
            hs.showOverlayRange = newRange

        # Manually refresh the histogram range polygon.
        rangePolygon.updatePolygon()

        return which


    def _overlayRangeModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse down events in ``overlayRange`` mode. Calls the
        :meth:`__updateShowOverlayRange` method.
        """

        if self.__currentHs is None:                     return
        if not self.__currentHs.showOverlay:             return
        if self.__currentHs not in self.__rangePolygons: return
        if canvasPos is None:                            return

        self.__draggingRange = self.__updateShowOverlayRange(canvasPos[0])


    def _overlayRangeModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse down events in ``overlayRange`` mode. Calls the
        :meth:`__updateShowOverlayRange` method.
        """

        if not self.__draggingRange: return
        if canvasPos is None:        return

        self.__updateShowOverlayRange(canvasPos[0], self.__draggingRange)


    def _overlayRangeModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse up events in ``overlayRange`` mode. Clears
        some internal state.
        """

        if not self.__draggingRange:
            return

        self.__draggingRange = False


class RangePolygon(patches.Polygon):
    """The ``RangePolygon`` class is a ``matplotlib.patches.Polygon`` which
    is used to display a data range over a :class:`.HistogramSeries` plot.


    Whenever any property on the ``HistogramSeries`` changes (and on calls to
    :meth:`updatePolygon`), the vertices of a polygon spanning the
    :attr:`.HistogramSeries.showOverlayRange` property are generated.


    The ``RangePolygon`` automatically adds and removes itself to the
    :attr:`.PlotPanel.artists` list of the owning :class:`.HistogramPanel`
    according to the values of the :attr:`.HistogramSeries.showOverlay` and
    :attr:`.DataSeries.enabled` properties.
    """

    def __init__(self, hs, hsPanel, *args, **kwargs):
        """Create a ``RangePolygon``.

        :arg hs:      The :class:`.HistogramSeries`
        :arg hsPanel: The :class:`.HistogramPanel`

        All other arguments are passed through to the ``Polygon.__init__``
        method.
        """
        patches.Polygon.__init__(self, *args, **kwargs)

        # Dodgily trying to avoid collisions
        # with any patches.Polygon attributes
        self._rp_hs      = hs
        self._rp_hsPanel = hsPanel
        self._rp_name    = '{}_{}'.format(type(self).__name__, id(self))

        hs.addGlobalListener(           self._rp_name, self.asyncUpdatePolygon)
        hsPanel.addListener('smooth',   self._rp_name, self.asyncUpdatePolygon)
        hsPanel.addListener('histType', self._rp_name, self.asyncUpdatePolygon)
        hsPanel.addListener('plotType', self._rp_name, self.asyncUpdatePolygon)

        self.updatePolygon()


    def destroy(self):
        """Must be called when this ``RangePolygon`` is no longer needed.

        Removes property listeners and cleans up references.
        """

        hs      = self._rp_hs
        hsPanel = self._rp_hsPanel

        hs.removeGlobalListener(           self._rp_name)
        hsPanel.removeListener('smooth',   self._rp_name)
        hsPanel.removeListener('histType', self._rp_name)
        hsPanel.removeListener('plotType', self._rp_name)

        if self in hsPanel.artists:
            hsPanel.artists.remove(self)

        self._rp_hs      = None
        self._rp_hsPanel = None


    def asyncUpdatePolygon(self, *a, **kwa):
        """Asynchronously schedule :meth:`updatePolygon` via
        :func:`.idle.idle`.
        """

        # We need to make sure, if the histogram
        # data has changed, that the data plot is
        # updated before the polygon is updated.
        #
        # This is subtly complicated, and is tightly
        # coupled to the OverlayPlotPanel internals.
        #
        # 1. OverlayPlotPanel draws via asyncDraw(),
        #    which schedules draw() on the idle loop
        #    (the idle.idle call below makes sure
        #     we get scheduled after this).
        #
        # 2. draw() prepares data on a TaskThread
        #    (the OPP draw queue; waitUntilIdle
        #     is run on a separate thread which
        #     blocks until the draw queue is empty).
        #
        # 3. When data is prepared, __drawDataSeries()
        #    is scheduled on idle loop (the onFinish
        #    function below - updatePolygon - is
        #    schduled on idle after this).
        #
        # We need to wait until all of the above has
        # completed before updating the range polygon.

        q        = self._rp_hsPanel.getDrawQueue()
        taskName = '{}.draw'.format(id(self))

        idle.idle(idle.run,
                  q.waitUntilIdle,
                  onFinish=self.updatePolygon,
                  name=taskName,
                  dropIfQueued=True)


    def updatePolygon(self, *a, **kwa):
        """Called whenever any property changes on the
        :class:`.HistogramSeries`, and called manually by the
        :class:`HistogramProfile`.

        Adds/removes this ``RangePolygon`` to the :attr:`.PlotPanel.artists`
        list and regenerates the polygon vertices as needed.
        """

        hs      = self._rp_hs
        hsPanel = self._rp_hsPanel

        # If smoothing is enabled, or we are
        # plotting bin centres, we get
        # the histogram data from the plotted
        # Line2D instance. This is because the
        # HistogramPanel does the smoothing and
        # bin centre adjustmennt, not the
        # HistogramSeries instance.
        #
        # Try/except because the HistogramSeries
        # may not yet have been plotted.
        if hsPanel.smooth or hsPanel.plotType == 'centre':
            try:

                hsArtist = hsPanel.getArtist(hs)
                x        = hsArtist.get_xdata()
                y        = hsArtist.get_ydata()
                vertices = np.array([x, y]).T

            except Exception:
                vertices = np.zeros(0)

        # Otherwise we can get the data
        # directly from the HistogramSeries.
        # The HS class has a method which
        # generates histogram vertices for us.
        else:
            vertices = hs.getVertexData()

            # HistogramSeries, we need to apply
            # post-processing normally performed
            # by the HistogramPanel to the data.
            if hsPanel.histType == 'probability':
                vertices[:, 1] /= hs.getNumHistogramValues()

        # Nothing to plot, or we shouldn't
        # be plotting the range overlay
        if not ((vertices.size > 0) and hs.enabled and hs.showOverlay):

            if self in hsPanel.artists:
                hsPanel.artists.remove(self)

            return

        lo, hi   = hs.showOverlayRange
        mask     = (vertices[:, 0] >= lo) & (vertices[:, 0] <= hi)
        vertices = vertices[mask, :]

        # Happens if lo == hi. Create some dummy
        # vertices, so that something gets drawn.
        if vertices.size == 0:

            histx, histy = hs.getData()

            try:              xidx = np.where(histx[:] < hi)[0][-1]
            except Exception: xidx = len(histy) - 1

            if xidx >= len(histy):
                xidx = -1

            yval = float(histy[xidx])

            if hsPanel.histType == 'probability':
                yval /= hs.getNumHistogramValues()

            vertices = np.array([[lo, 0], [lo, yval], [hi, yval], [hi, 0]])

        # The showOverlayRange coordinates probably
        # don't align with the histogram bins. So
        # we add some start/end vertices to make the
        # histogram polygon all nice and squareish.
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

        self.set_xy(vertices)

        # Make sure the polygon
        # colour is up to date
        colour = list(hs.colour)[:3]

        self.set_edgecolor(colour + [1.0])
        self.set_facecolor(colour + [0.3])

        # Add to the artists list if needed,
        # so the polygon gets shown.
        if self not in hsPanel.artists: hsPanel.artists.append(self)
        else:                           hsPanel.drawArtists(immediate=True)


class HistogramOverlay(object):
    """The ``HistogramOverlay`` class manages the creation, destruction, and
    display of a :class:`.ProxyImage` overlay which displays the voxels that
    are included in a histogram plot. The user can toggle the display of this
    overlay via the :attr:`.HistogramSeries.showOverlay` property.
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

        display = displayCtx.getDisplay(overlay)

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__histSeries  = histSeries
        self.__overlay     = overlay
        self.__display     = display
        self.__opts        = None
        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__histMask    = None

        display    .addListener('overlayType',
                                self.__name,
                                self.__overlayTypeChanged)
        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        histSeries.addListener('showOverlay',
                                self.__name,
                                self.__showOverlayChanged)

        self.__overlayTypeChanged()


    def destroy(self):
        """Must be called when this ``HistogramOverlay`` is no longer needed.
        Removes property listeners and clears references.
        """

        self.__overlayList.removeListener('overlays',    self.__name)
        self.__histSeries .removeListener('showOverlay', self.__name)
        self.__display    .removeListener('overlayType', self.__name)

        if self.__opts is not None:
            self.__opts.removeListener('volume', self.__name)


        if self.__histMask is not None:
            self.__overlayList.remove(self.__histMask)

        self.__histSeries  = None
        self.__overlay     = None
        self.__display     = None
        self.__opts        = None
        self.__displayCtx  = None
        self.__overlayList = None
        self.__histMask    = None


    def __overlayTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` changes.
        De/re-registers a listener on the :attr:`.NiftiOpts.volume` property
        (as ``Opts`` instances are destroyed/re-created when the
        ``overlayType`` changes).
        """

        oldOpts     = self.__opts
        newOpts     = self.__displayCtx.getOpts(self.__overlay)
        self.__opts = newOpts

        if oldOpts is not None:
            oldOpts.removeListener('volume', self.__name)

        newOpts.addListener('volume', self.__name, self.__volumeChanged)


    def __volumeChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.volume` property changes. Makes
        sure  that the 3d mask overlay is up to date (if it is being shown).
        """
        self.__showOverlayChanged(force=True)


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


    def __showOverlayChanged(self, *args, **kwargs):
        """Called when the :attr:`.HistogramSeries.showOverlay` property
        changes.

        Adds/removes a 3D mask :class:`.Image` to the :class:`.OverlayList`,
        which highlights the voxels that have been included in the histogram.
        The :class:`.MaskOpts.threshold` property is bound to the
        :attr:`.HistogramSeries.showOverlayRange` property, so the masked
        voxels are updated whenever the histogram overlay range changes, and
        vice versa.

        :arg force: If ``True``, and ``HistogramSeries.showOverlay is True``,
                    the mask overlay is recreated even if one already exists.
        """

        hs     = self.__histSeries
        force  = kwargs.get('force', False)
        exists = self.__histMask is not None

        if      hs.showOverlay  and      exists and (not force): return
        if (not hs.showOverlay) and (not exists):                return

        # Remove any old mask overlay
        if exists:

            log.debug('Removing 3D histogram overlay mask for {}'.format(
                self.__overlay.name))

            if self.__histMask in self.__overlayList:
                self.__overlayList.remove(self.__histMask)

            self.__histMask = None

        # Create a new mask overlay
        if hs.showOverlay:

            log.debug('Creating 3D histogram overlay mask for {}'.format(
                self.__overlay.name))

            opts = self.__displayCtx.getOpts(hs.overlay)

            self.__histMask = fsloverlay.ProxyImage(
                self.__overlay,
                volume=opts.index(),
                name='{}/histogram/mask'.format(self.__overlay.name))

            self.__overlayList.append(self.__histMask, overlayType='mask')

            opts = self.__displayCtx.getOpts(self.__histMask)

            opts.bindProps('colour',    hs)
            opts.bindProps('threshold', hs, 'showOverlayRange')
