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
import fsl.fsleyes.colourmaps                      as fslcmaps
import fsl.fsleyes.plotting                        as plotting
import fsl.fsleyes.controls.timeseriescontrolpanel as timeseriescontrolpanel
import fsl.fsleyes.controls.timeserieslistpanel    as timeserieslistpanel


log = logging.getLogger(__name__)


class TimeSeriesPanel(plotpanel.PlotPanel):
    """The ``TimeSeriesPanel`` is a :class:`.PlotPanel` which plots time series
    data from :class:`.Image` overlays. A ``TimeSeriesPanel`` looks something
    like the following:

    .. image:: images/timeseriespanel.png
       :scale: 50%
       :align: center

    
    A ``TimeSeriesPanel`` plots one or more :class:`.TimeSeries` instances,
    which encapsulate time series data from an overlay. All ``TimeSeries``
    classes are defined in the :mod:`.plotting.timeseries` module; these are
    all sub-classes of the :class:`.DataSeries` class - see the
    :class:`.PlotPanel` documentation for more details:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.plotting.timeseries.TimeSeries
       ~fsl.fsleyes.plotting.timeseries.FEATTimeSeries
       ~fsl.fsleyes.plotting.timeseries.MelodicTimeSeries

    
    **The current time course**

    
    By default, the ``TimeSeriesPanel`` plots the time series of the current
    voxel from the currently selected overlay, which is determined from the
    :attr:`.DisplayContext.selectedOverlay`. This time series is referred to
    as the *current* time course. The :attr:`showMode` property allows the
    user to choose between showing only the current time course, showing the
    time course for all (compatible) overlays, or only showing the time
    courses that have been added to the :attr:`.PlotPanel.dataSeries` list.
    

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


    showMode = props.Choice(('current', 'all', 'none'))
    """Defines which time series to plot.


    =========== ======================================================
    ``current`` The time course for  the currently selected overlay is
                plotted.
    ``all``     The time courses for all compatible overlays in the
                :class:`.OverlayList` are plotted.
    ``none``    Only the ``TimeSeries`` that are in the
                :attr:`.PlotPanel.dataSeries` list will be plotted.
    =========== ======================================================
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

        self       .addListener('plotMode',        self._name, self.draw)
        self       .addListener('usePixdim',       self._name, self.draw)
        self       .addListener('showMode',        self._name, self.draw)
        displayCtx .addListener('selectedOverlay', self._name, self.draw)
        self       .addListener('plotMelodicICs',
                                self._name,
                                self.__plotMelodicICsChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__overlayListChanged) 

        # The currentTss attribute is a dictionary of
        #
        #   {overlay : TimeSeries}
        #
        # mappings, containing a TimeSeries instance for
        # each compatible overlay in the overlay list.
        # 
        # Different TimeSeries types need to be re-drawn
        # when different properties change. For example,
        # a TimeSeries instance needs to be redrawn when
        # the DisplayContext.location property changes,
        # whereas a MelodicTimeSeries instance needs to
        # be redrawn when the VolumeOpts.volume property
        # changes.
        #
        # Therefore, the refreshProps dictionary contains
        # a set of
        #
        #   {overlay : ([targets], [propNames])}
        #
        # mappings - for each overlay, a list of
        # target objects (e.g. DisplayContext, VolumeOpts,
        # etc), and a list of property names on each,
        # defining the properties that need to trigger a
        # redraw.
        self.__currentTss     = {}
        self.__refreshProps   = {} 
        self.__overlayColours = {}

        def addPanels():
            self.run('toggleTimeSeriesControl') 
            self.run('toggleTimeSeriesList') 

        wx.CallAfter(addPanels)

        self.__overlayListChanged()


    def destroy(self):
        """Removes some listeners, and calls the :meth:`.PlotPanel.destroy`
        method.
        """
        
        self.removeListener('plotMode',  self._name)
        self.removeListener('usePixdim', self._name)
        self.removeListener('showMode',  self._name)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        for (targets, propNames) in self.__refreshProps.values():
            for target, propName in zip(targets, propNames):
                target.removeListener(propName, self._name)

        for ts in self.__currentTss.values():
            ts.removeGlobalListener(self)

        self.__currentTss   = None
        self.__refreshProps = None

        plotpanel.PlotPanel.destroy(self) 


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

        tss = [self.__currentTss.get(o) for o in overlays]
        tss = [ts for ts in tss if ts is not None]

        for i, ts in enumerate(list(tss)):
            if isinstance(ts, plotting.FEATTimeSeries):
                tss.pop(i)
                tss = tss[:i] + ts.getModelTimeSeries() + tss[i:]

        for ts in tss:
            ts.label = ts.makeLabel()

        self.drawDataSeries(extraSeries=tss,
                            preproc=self.__prepareTimeSeriesData)


    def getTimeSeries(self, overlay):
        """Returns the :class:`.TimeSeries` instance for the specified
        overlay, or ``None`` if there is none.
        """
        return self.__currentTss.get(overlay)


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
                xdata *= ts.overlay.tr
            else:
                xdata *= ts.overlay.pixdim[3]
        
        if self.plotMode == 'demean':
            ydata = ydata - ydata.mean()

        elif self.plotMode == 'normalise':
            ymin  = ydata.min()
            ymax  = ydata.max()
            ydata = 2 * (ydata - ymin) / (ymax - ymin) - 1
            
        elif self.plotMode == 'percentChange':
            mean  = ydata.mean()
            ydata =  100 * (ydata / mean) - 100
            
        return xdata, ydata 


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Makes sure that
        there are no :class:`.TimeSeries` instances in the
        :attr:`.PlotPanel.dataSeries` list, or in the internal cache, which
        refer to overlays that no longer exist.

        Also calls :meth:`__updateCurrentTimeSeries`, whic ensures that a
        :class:`.TimeSeries` instance for every compatiblew overlay is
        cached internally.
        """

        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
                ds.destroy()
        
        for overlay in list(self.__currentTss.keys()):
            if overlay not in self._overlayList:
                self.__clearCacheForOverlay(overlay)

        self.__updateCurrentTimeSeries()
        self.draw()


    def __clearCacheForOverlay(self, overlay):
        """Destroys the internally cached :class:`.TimeSeries` for the given
        overlay.
        """
        
        ts                 = self.__currentTss  .pop(overlay, None)
        targets, propNames = self.__refreshProps.pop(overlay, ([], []))

        if ts is not None:
            ts.destroy()

        for t, p in zip(targets, propNames):
            t.removeListener(p, self._name)

        
    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`plotMelodicICs` property changes. Re-creates
        the internally cached :class:`.TimeSeries` instances for all
        :class:`.MelodicImage` overlays in the :class:`.OverlayList`.
        """

        for overlay in self._overlayList:
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.__clearCacheForOverlay(overlay)

        self.__updateCurrentTimeSeries()
        self.draw()

        
    def __updateCurrentTimeSeries(self, *a):
        """Makes sure that a :class:`.TimeSeries` instance exists for every
        compatible overlay in the :class:`.OverlayList`, and that
        relevant property listeners are registered so they are redrawn as
        needed.
        """

        for ovl in self._overlayList:
            if ovl not in self.__currentTss:
                
                ts, refreshTargets, refreshProps = self.__genOneTimeSeries(ovl)

                if ts is None:
                    continue

                self.__currentTss[  ovl] = ts
                self.__refreshProps[ovl] = (refreshTargets, refreshProps)
                
                ts.addGlobalListener(self._name, self.draw, overwrite=True)
        
        for targets, propNames in self.__refreshProps.values():
            for target, propName in zip(targets, propNames):
                target.addListener(propName,
                                   self._name,
                                   self.draw,
                                   overwrite=True)


    
    def __genOneTimeSeries(self, overlay):
        """Creates and returns a :class:`.TimeSeries` instance (or an
        instance of one of the :class:`.TimeSeries` sub-classes) for the
        specified overlay.

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

        ts.colour    = fslcmaps.randomDarkColour()
        ts.alpha     = 1
        ts.lineWidth = 1
        ts.lineStyle = '-'
        ts.label     = ts.makeLabel()
                
        return ts, targets, propNames
