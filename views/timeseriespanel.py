#!/usr/bin/env python
#
# timeseriespanel.py - The TimeSeriesPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesPanel`, which is a *FSLeyes
view* for displaying time series data from :class:`.Image` overlays.
"""


import logging

import wx

import                                                props

import                                                plotpanel
import fsl.data.featimage                          as fslfeatimage
import fsl.data.melodicimage                       as fslmelimage
import fsl.data.image                              as fslimage
import fsl.fsleyes.actions                         as actions
import fsl.fsleyes.plotting                        as plotting
import fsl.fsleyes.controls.timeseriescontrolpanel as timeseriescontrolpanel
import fsl.fsleyes.controls.plotlistpanel          as plotlistpanel


log = logging.getLogger(__name__)


class TimeSeriesPanel(plotpanel.OverlayPlotPanel):
    """The ``TimeSeriesPanel`` is an :class:`.OverlayPlotPanel` which plots
    time series data from overlays. A ``TimeSeriesPanel`` looks something like
    the following:

    
    .. image:: images/timeseriespanel.png
       :scale: 50%
       :align: center

    
    A ``TimeSeriesPanel`` plots one or more :class:`.TimeSeries` instances,
    which encapsulate time series data from an overlay. All ``TimeSeries``
    classes are defined in the :mod:`.plotting.timeseries` module; these are
    all sub-classes of the :class:`.DataSeries` class - see the
    :class:`.PlotPanel` and :class:`.OverlayPlotPanel` documentation for more
    details:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.plotting.timeseries.TimeSeries
       ~fsl.fsleyes.plotting.timeseries.FEATTimeSeries
       ~fsl.fsleyes.plotting.timeseries.MelodicTimeSeries


    **Control panels**

    
    Some *FSLeyes control* panels are associated with the
    :class:`.TimeSeriesPanel`:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsl.fsleyes.controls.timeseriescontrolpanel.TimeSeriesControlPanel

    
    The ``TimeSeriesPanel`` defines some :mod:`.actions`, allowing the user
    to show/hide these control panels:

    .. autosummary::
       :nosignatures:

       toggleTimeSeriesList
       toggleTimeSeriesControl


    **FEATures**


    The ``TimeSeriesPanel`` has some extra functionality for
    :class:`.FEATImage` overlays. For these overlays, a
    :class:`.FEATTimeSeries` instance is plotted, instead of a regular
    :class:`.TimeSeries` instance. The ``FEATTimeSeries`` class, in turn, has
    the ability to generate more ``TimeSeries`` instances which represent
    various aspects of the FEAT model fit. See the :class:`.FEATTimeSeries`
    and the :class:`.TimeSeriesControlPanel` classes for more details.

    
    **Melodic features**

    
    The ``TimeSeriesPanel`` also has some functionality for
    :class:`.MelodicImage` overlays - a :class:`.MelodicTimeSeries` instance
    is used to plot the component time courses for the current component (as
    defined by the :attr:`.ImageOpts.volume` property).
    """

    
    usePixdim = props.Boolean(default=True)
    """If ``True``, the X axis data is scaled by the pixdim value of the
    selected overlay (which, for FMRI time series data is typically set
    to the TR time).
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


    plotMelodicICs = props.Boolean(default=True)
    """If ``True``, the component time courses are plotted for
    :class:`.MelodicImage` overlays (using a :class:`.MelodicTimeSeries`
    instance). Otherwise, ``MelodicImage`` overlays are treated as regular
    4D :class:`.Image` overlays (a :class:`.TimeSeries` instance is used).
    """


    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``TimeSeriesPanel``.

        :arg parent:      A :mod:`wx` parent object.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        """

        plotpanel.OverlayPlotPanel.__init__(
            self, parent, overlayList, displayCtx)

        self.addListener('plotMode',  self._name, self.draw)
        self.addListener('usePixdim', self._name, self.draw)
        self.addListener('plotMelodicICs',
                         self._name,
                         self.__plotMelodicICsChanged)


    def destroy(self):
        """Removes some listeners, and calls the :meth:`.PlotPanel.destroy`
        method.
        """
        
        self.removeListener('plotMode',       self._name)
        self.removeListener('usePixdim',      self._name)
        self.removeListener('plotMelodicICs', self._name)
        
        plotpanel.OverlayPlotPanel.destroy(self)


    @actions.toggleControlAction(plotlistpanel.PlotListPanel)
    def toggleTimeSeriesList(self):
        """Shows/hides a :class:`.PlotListPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(plotlistpanel.PlotListPanel, self, location=wx.TOP)

        
    @actions.toggleControlAction(timeseriescontrolpanel.TimeSeriesControlPanel)
    def toggleTimeSeriesControl(self):
        """Shows/hides a :class:`.TimeSeriesControlPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(timeseriescontrolpanel.TimeSeriesControlPanel,
                         self,
                         location=wx.TOP)

        
    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``TimeSeriesPanel``.
        """
        actions = [self.screenshot,
                   self.toggleTimeSeriesList,
                   self.toggleTimeSeriesControl]

        names = [a.__name__ for a in actions]

        return zip(names, actions)


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Passes some :class:`.TimeSeries`
        instances to the :meth:`.PlotPanel.drawDataSeries` method.
        """

        if self.showMode == 'all':
            overlays = self._overlayList[:]
            
        elif self.showMode == 'current':
            overlays = [self._displayCtx.getSelectedOverlay()]
            
        else:
            overlays = []

        tss = [self.getDataSeries(o) for o in overlays]
        tss = [ts for ts in tss if ts is not None]

        for i, ts in enumerate(list(tss)):
            if isinstance(ts, plotting.FEATTimeSeries):
                tss.pop(i)
                tss = tss[:i] + ts.getModelTimeSeries() + tss[i:]

        for ts in tss:
            ts.label = ts.makeLabel()

        self.drawDataSeries(extraSeries=tss,
                            preproc=self.__prepareTimeSeriesData)


    def createDataSeries(self, overlay):
        """Overrides :meth:`.OverlayPlotPanel.createDataSeries`. Creates and
        returns a :class:`.TimeSeries` instance (or an instance of one of the
        :class:`.TimeSeries` sub-classes) for the specified overlay.

        Returns a tuple containing the following:
        
          - A :class:`.TimeSeries` instance for the given overlay
        
          - A list of *targets* - objects which have properties that
            influence the state of the ``TimeSeries`` instance.
        
          - A list of *property names*, one for each target.

        If the given overlay is not compatible (i.e. it has no time series
        data to be plotted), a tuple of ``None`` values is returned.
        """

        if not (isinstance(overlay, fslimage.Image) and overlay.is4DImage()):
            return None, None, None

        if isinstance(overlay, fslfeatimage.FEATImage):
            ts = plotting.FEATTimeSeries(self, overlay, self._displayCtx)
            targets   = [self._displayCtx]
            propNames = ['location']
            
        elif isinstance(overlay, fslmelimage.MelodicImage) and \
             self.plotMelodicICs:
            ts = plotting.MelodicTimeSeries(self, overlay, self._displayCtx)
            targets   = [self._displayCtx.getOpts(overlay)]
            propNames = ['volume'] 
            
        else:
            ts = plotting.VoxelTimeSeries(self, overlay, self._displayCtx)
            targets   = [self._displayCtx]
            propNames = ['location'] 

        ts.colour    = self.getOverlayPlotColour(overlay)
        ts.alpha     = 1
        ts.lineWidth = 1
        ts.lineStyle = '-'
        ts.label     = ts.makeLabel()
                
        return ts, targets, propNames


    def __prepareTimeSeriesData(self, ts):
        """Given a :class:`.TimeSeries` instance, scales and normalises
        the x and y data according to the current values of the
        :attr:`usePixdim` and :attr:`plotMode` properties.

        This method is used as a preprocessing function for all
        :class:`.TimeSeries` instances that are plotted - see the
        :meth:`.PlotPanel.drawDataSeries` method.
        """

        xdata, ydata = ts.getData()

        if self.usePixdim:
            if isinstance(ts.overlay, fslmelimage.MelodicImage):
                xdata = xdata * ts.overlay.tr
            else:
                xdata = xdata * ts.overlay.pixdim[3]
        
        if self.plotMode == 'demean':
            ydata = ydata - ydata.mean()

        elif self.plotMode == 'normalise':
            ymin  = ydata.min()
            ymax  = ydata.max()
            ydata = 2 * (ydata - ymin) / (ymax - ymin) - 1
            
        elif self.plotMode == 'percentChange':
            mean  = ydata.mean()
            ydata = 100 * (ydata / mean) - 100
            
        return xdata, ydata 


    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`plotMelodicICs` property changes. Re-creates
        the internally cached :class:`.TimeSeries` instances for all
        :class:`.MelodicImage` overlays in the :class:`.OverlayList`.
        """

        for overlay in self._overlayList:
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.clearDataSeries(overlay)

        self.updateDataSeries()
        self.draw()
