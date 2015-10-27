#!/usr/bin/env python
#
# timeseriespanel.py - A panel which plots time series/volume data from a
# collection of overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesPanel`, which is a *FSLeyes
view* for displaying time series data from :class:`.Image` overlays.

The following :class:`.DataSeries` sub-classes, defined in the
:mod:`.plotting.timeseries` module, are used by the :class:`TimeSeriesPanel`
(see the :class:`.PlotPanel` documentation for more details):

.. autosummary::
   :nosignatures:

   TimeSeries
   FEATTimeSeries
   MelodicTimeSeries
"""


import copy
import logging

import wx

import numpy as np

import                                                props

import                                                plotpanel
import fsl.data.featimage                          as fslfeatimage
import fsl.data.melodicimage                       as fslmelimage
import fsl.data.image                              as fslimage
import fsl.fsleyes.displaycontext                  as fsldisplay
import fsl.fsleyes.colourmaps                      as fslcmaps
import fsl.fsleyes.plotting.timeseries             as timeseries
import fsl.fsleyes.controls.timeseriescontrolpanel as timeseriescontrolpanel
import fsl.fsleyes.controls.timeserieslistpanel    as timeserieslistpanel


log = logging.getLogger(__name__)



class TimeSeriesPanel(plotpanel.PlotPanel):
    """A :class:`.PlotPanel` which plots time series data from :class:`.Image`
    overlays. A ``TimeSeriesPanel`` looks something like the following:

    .. image:: images/timeseriespanel.png
       :scale: 50%
       :align: center


    A ``TimeSeriesPanel`` plots one or more :class:`TimeSeries` instances,
    which encapsulate time series data for a voxel from a :class:`.Image`
    overlay.

    
    **The current time course**

    
    By default, the ``TimeSeriesPanel`` plots the time series of the current
    voxel from the currently selected overlay, if it is an :class:`.Image`
    instance.  The selected overlay and voxel are determined from the
    :attr:`.DisplayContext.selectedOverlay` and
    :attr:`.DisplayContext.location` respectively. This time series is
    referred to as the *current* time course. This behaviour can be disabled
    with the :attr:`showCurrent` setting. If the :attr:`showAllCurrent`
    setting is ``True``, the current time course for all compatible overlays
    in the :class:`.OverlayList` is plotted.
    

    Other time courses can be *held* by adding them to the
    :attr:`.PlotPanel.dataSeries` list - the :class:`.TimeSeriesListPanel`
    provides the user with the ability to add/remove time courses from the
    ``dataSeries`` list.


    **Control panels**

    
    Some *FSLeyes control* panels are associated with the
    :class:`.TimeSeriesPanel`:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.controls.timeserieslistpanel.TimeSeriesListPanel
       ~fsl.fsleyes.controls.timeseriescontrolpanel.TimeSeriesControlPanel

    
    The ``TimeSeriesPanel`` defines some :mod:`.actions`, allowing the user
    to show/hide these control panels (see the :meth:`.ViewPanel.togglePanel`
    method):

    =========================== ===============================================
    ``toggleTimeSeriesList``    Shows/hides a :class:`.TimeSeriesListPanel`.
    ``toggleTimeSeriesControl`` Shows/hides a :class:`.TimeSeriesControlPanel`.
    =========================== ===============================================

    New ``TimeSeriesPanel`` instances will display a ``TimeSeriesListPanel``
    and a ``TimeSeriesControlPanel`` by default.


    **FEATures**


    The ``TimeSeriesPanel`` has some extra functionality for
    :class:`.FEATImage` overlays. For these overlays, a
    :class:`.FEATTimeSeries` instance is plotted, instead of a regular
    :class:`.TimeSeries` instance. The ``FEATTimeSeries`` class, in turn, has
    the ability to generate more ``TimeSeries`` instances which represent
    various aspects of the FEAT model fit. See the :class:`.FEATTimeSeries`
    and the :class:`.TimeSeriesControlPanel` classes for more details.
    """

    
    usePixdim = props.Boolean(default=False)
    """If ``True``, the X axis data is scaled by the pixdim value of the
    selected overlay (which, for FMRI time series data is typically set
    to the TR time).
    """

    
    showCurrent = props.Boolean(default=True)
    """If ``True``, the time course for the current voxel of the currently
    selected overlay is plotted.
    """

    
    showAllCurrent = props.Boolean(default=False)
    """If ``True``, the time courses from the current
    :attr:`.DisplayContext.location` for all compatible overlays in the
    :class:`.OverlayList` are plotted.
    """

    
    plotMode = props.Choice(('normal', 'demean', 'normalise', 'percentChange'))
    """Options to scale/offset the plotted time courses.

    ================= =======================================================
    ``normal``        The data is plotted with no modifications
    ``demean``        The data is demeaned (i.e. plotted with a mean of 0)
    ``normalise``     The data is normalised to lie in the range ``[-1, 1]``.
    ``percentChange`` The data is scaled to percent changed
    ================= =======================================================
    """

    currentColour = copy.copy(timeseries.TimeSeries.colour)
    """Colour to use for the current time course. """

    
    currentAlpha = copy.copy(timeseries.TimeSeries.alpha)
    """Transparency to use for the current time course. """

    
    currentLineWidth = copy.copy(timeseries.TimeSeries.lineWidth)
    """Line width to use for the current time course. """

    
    currentLineStyle = copy.copy(timeseries.TimeSeries.lineStyle)
    """Line style to use for the current time course. """


    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``TimeSeriesPanel``.

        :arg parent:      A :mod:`wx` parent object.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        """

        self.currentColour    = (0, 0, 0)
        self.currentAlpha     = 1
        self.currentLineWidth = 1
        self.currentLineStyle = '-'

        actionz = {
            'toggleTimeSeriesList'    : lambda *a: self.togglePanel(
                timeserieslistpanel.TimeSeriesListPanel,
                self,
                location=wx.TOP),
            'toggleTimeSeriesControl' : lambda *a: self.togglePanel(
                timeseriescontrolpanel.TimeSeriesControlPanel,
                self,
                location=wx.TOP) 
        }

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz=actionz)

        figure = self.getFigure()

        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        overlayList.addListener('overlays',
                                self._name,
                                self.__overlaysChanged)        
 
        displayCtx .addListener('selectedOverlay', self._name, self.draw) 
        displayCtx .addListener('location',        self._name, self.draw)

        self.addListener('plotMode',    self._name, self.draw)
        self.addListener('usePixdim',   self._name, self.draw)
        self.addListener('showCurrent', self._name, self.draw)

        csc = self.__currentSettingsChanged
        self.addListener('currentColour',    self._name, csc)
        self.addListener('currentAlpha',     self._name, csc)
        self.addListener('currentLineWidth', self._name, csc)
        self.addListener('currentLineStyle', self._name, csc)

        self.__currentOverlay = None
        self.__currentTs      = None
        self.__overlayColours = {}

        def addPanels():
            self.run('toggleTimeSeriesControl') 
            self.run('toggleTimeSeriesList') 

        wx.CallAfter(addPanels)

        self.draw()


    def destroy(self):
        """Removes some listeners, and calls the :meth:`.PlotPanel.destroy`
        method.
        """
        
        self.removeListener('plotMode',    self._name)
        self.removeListener('usePixdim',   self._name)
        self.removeListener('showCurrent', self._name)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)

        plotpanel.PlotPanel.destroy(self) 

        
    def getCurrent(self):
        """Returns the :class:`.TimeSeries` instance for the current time
        course. If :attr:`showCurrent` is ``False``, or the currently
        selected overlay is not a :class:`.Image` (see
        :attr:`.DisplayContext.selectedOverlay`) this method will return
        ``None``.
        """
        
        return self.__currentTs


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Generates the current time
        course(s) if necessary, and calls the :meth:`.PlotPanel.drawDataSeries`
        method.
        """

        self.__calcCurrent()
        current = self.__currentTs

        if self.showCurrent:

            extras      = []
            currOverlay = None

            if current is not None:
                if isinstance(current, timeseries.FEATTimeSeries):
                    extras = current.getModelTimeSeries()
                else:
                    extras = [current]

                currOverlay = current.overlay

            if self.showAllCurrent:
                
                overlays = [o for o in self._overlayList
                            if o is not currOverlay]

                tss = map(self.__genTimeSeries, overlays)

                extras.extend([ts for ts in tss if ts is not None])
                    
                for ts in tss:
                    ts.alpha     = 1
                    ts.lineWidth = 0.5

                    # Use a random colour for each overlay,
                    # but use the same random colour each time
                    colour = self.__overlayColours.get(
                        ts.overlay,
                        fslcmaps.randomBrightColour())
                        
                    ts.colour = colour
                    self.__overlayColours[ts.overlay] = colour
                        
                    if isinstance(ts, timeseries.FEATTimeSeries):
                        extras.extend(ts.getModelTimeSeries())
                
            self.drawDataSeries(extras)
        else:
            self.drawDataSeries()

        
    def __currentSettingsChanged(self, *a):
        """Called when the settings controlling the display of the current time
        course(s) changes.  If the current time course is a
        :class:`.FEATTimeSeries`, the display settings are propagated to all of
        its associated time courses (see the
        :meth:`.FEATTimeSeries.getModelTimeSeries` method).
        """
        if self.__currentTs is None:
            return

        tss = [self.__currentTs]
        
        if isinstance(self.__currentTs, timeseries.FEATTimeSeries):
            tss = self.__currentTs.getModelTimeSeries()

            for ts in tss:

                if ts is self.__currentTs:
                    continue

                # Don't change the colour for associated
                # time courses (e.g. model fits)
                if ts is self.__currentTs:
                    ts.colour = self.currentColour
                    
                ts.alpha     = self.currentAlpha
                ts.lineWidth = self.currentLineWidth
                ts.lineStyle = self.currentLineStyle



    def __overlaysChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Makes sure
        that there are no :class:`.TimeSeries` instances in the
        :attr:`.PlotPanel.dataSeries` list which refer to overlays that
        no longer exist.
        """

        self.disableListener('dataSeries', self._name)
        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
        self.enableListener('dataSeries', self._name)
        self.draw()


    def __bindCurrentProps(self, ts, bind=True):
        """Binds or unbinds the properties of the given :class:`.TimeSeries`
        instance with the current display settings (e.g.
        :attr:`currentColour`, :attr:`currentAlpha`, etc).
        """
        ts.bindProps('colour'   , self, 'currentColour',    unbind=not bind)
        ts.bindProps('alpha'    , self, 'currentAlpha',     unbind=not bind)
        ts.bindProps('lineWidth', self, 'currentLineWidth', unbind=not bind)
        ts.bindProps('lineStyle', self, 'currentLineStyle', unbind=not bind)

        if bind: self.__currentTs.addGlobalListener(   self._name, self.draw)
        else:    self.__currentTs.removeGlobalListener(self._name)


    def __getTimeSeriesLocation(self, overlay):
        """Calculates and returns the voxel coordinates corresponding to the
        current :attr:`.DisplayContext.location` for the specified ``overlay``.

        Returns ``None`` if the given overlay is not a 4D :class:`.Image`
        which is being displayed with a :class:`.VolumeOpts` instance, or if
        the current location is outside of the image bounds.
        """

        x, y, z = self._displayCtx.location.xyz
        opts    = self._displayCtx.getOpts(overlay)

        if not isinstance(overlay, fslimage.Image)        or \
           not isinstance(opts,    fsldisplay.VolumeOpts) or \
           not overlay.is4DImage():
            return None

        if isinstance(overlay, fslmelimage.MelodicImage):
            return opts.volume

        vox = opts.transformCoords([[x, y, z]], 'display', 'voxel')[0]
        vox = np.round(vox)

        if vox[0] < 0                 or \
           vox[1] < 0                 or \
           vox[2] < 0                 or \
           vox[0] >= overlay.shape[0] or \
           vox[1] >= overlay.shape[1] or \
           vox[2] >= overlay.shape[2]:
            return None

        return vox

    
    def __genTimeSeries(self, overlay):
        """Creates and returns a :class:`.TimeSeries` or
        :class:`.FEATTimeSeries` instance for the specified voxel of the
        specified overlay.
        """

        loc = self.__getTimeSeriesLocation(overlay)

        if loc is None:
            return None

        if isinstance(overlay, fslfeatimage.FEATImage):
            ts = timeseries.FEATTimeSeries(self, overlay, loc)
            
        elif isinstance(overlay, fslmelimage.MelodicImage):
            ts = timeseries.MelodicTimeSeries(self, overlay, loc)
            
        else:
            ts = timeseries.TimeSeries(self, overlay, loc)

        ts.colour    = self.currentColour
        ts.alpha     = self.currentAlpha
        ts.lineWidth = self.currentLineWidth
        ts.lineStyle = self.currentLineStyle
        ts.label     = None            
                
        return ts
            
        
    def __calcCurrent(self):
        """Called by the :meth:`draw` method. Makes sure that the current
        time course(s) is/are up to date.
        """

        prevTs      = self.__currentTs
        prevOverlay = self.__currentOverlay

        if prevTs is not None:
            self.__bindCurrentProps(prevTs, False)

        self.__currentTs      = None
        self.__currentOverlay = None

        if len(self._overlayList) == 0:
            return

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is prevOverlay:
            self.__currentOverlay = prevOverlay
            self.__currentTs      = prevTs
            prevTs.update(self.__getTimeSeriesLocation(overlay))

        else:
            ts                    = self.__genTimeSeries(overlay)
            self.__currentTs      = ts
            self.__currentOverlay = overlay

        self.__bindCurrentProps(self.__currentTs)
