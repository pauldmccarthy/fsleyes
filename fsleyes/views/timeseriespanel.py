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
import itertools as it

import numpy as np

import wx

import fsl.data.featimage                      as fslfeatimage
import fsl.data.melodicimage                   as fslmelimage
import fsl.data.image                          as fslimage
import fsl.data.mesh                           as fslmesh
import fsleyes_props                           as props

import fsleyes.overlay                         as fsloverlay
import fsleyes.actions                         as actions
import fsleyes.actions.addmaskdataseries       as addmaskdataseries
import fsleyes.strings                         as strings
import fsleyes.plotting                        as plotting
import fsleyes.controls.timeseriescontrolpanel as timeseriescontrolpanel
import fsleyes.controls.timeseriestoolbar      as timeseriestoolbar
from . import                                     plotpanel


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

       .timeseries.TimeSeries
       .timeseries.VoxelTimeSeries
       .timeseries.FEATTimeSeries
       .timeseries.MelodicTimeSeries
       .timeseries.MeshTimeSeries


    **Control panels**


    Some *FSLeyes control* panels are associated with the
    :class:`.TimeSeriesPanel`:

    .. autosummary::
       :nosignatures:

       ~fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsleyes.controls.timeseriescontrolpanel.TimeSeriesControlPanel


    The ``TimeSeriesPanel`` defines some :mod:`.actions`, allowing the user
    to show/hide these control panels:

    .. autosummary::
       :nosignatures:

       toggleTimeSeriesToolBar
       toggleTimeSeriesControl


    Some tools are also available, to do various things:

    .. autosummary::
       :nosignatures:

       addMaskDataSeries


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
    defined by the :attr:`.NiftiOpts.volume` property).
    """


    usePixdim = props.Boolean(default=False)
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


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``TimeSeriesPanel``.

        :arg parent:      A :mod:`wx` parent object.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        # If the currently selected image is from
        # a FEAT analysis, and the corresponding
        # filtered_func_data is loaded, enable the
        # initial state of the time course for
        # that filtered_func_data
        featImage = fsloverlay.findFEATImage(
            overlayList,
            displayCtx.getSelectedOverlay())

        if featImage is None: initialState = None
        else:                 initialState = {featImage : True}

        plotpanel.OverlayPlotPanel.__init__(
            self,
            parent,
            overlayList,
            displayCtx,
            frame,
            initialState=initialState)

        self.addListener('plotMode',  self.name, self.draw)
        self.addListener('usePixdim', self.name, self.draw)
        self.addListener('plotMelodicICs',
                         self.name,
                         self.__plotMelodicICsChanged)

        self.__addMaskAction = addmaskdataseries.AddMaskDataSeriesAction(
            overlayList,
            displayCtx,
            self)

        self.addMaskDataSeries.bindProps('enabled', self.__addMaskAction)

        self.initProfile()


    def destroy(self):
        """Removes some listeners, and calls the :meth:`.PlotPanel.destroy`
        method.
        """

        self.removeListener('plotMode',       self.name)
        self.removeListener('usePixdim',      self.name)
        self.removeListener('plotMelodicICs', self.name)

        self.__addMaskAction.destroy()
        self.__addMaskAction = None

        plotpanel.OverlayPlotPanel.destroy(self)


    @actions.toggleControlAction(timeseriescontrolpanel.TimeSeriesControlPanel)
    def toggleTimeSeriesControl(self, floatPane=False):
        """Shows/hides a :class:`.TimeSeriesControlPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(timeseriescontrolpanel.TimeSeriesControlPanel,
                         self,
                         location=wx.RIGHT,
                         floatPane=floatPane)


    @actions.toggleControlAction(timeseriestoolbar.TimeSeriesToolBar)
    def toggleTimeSeriesToolBar(self):
        """Shows/hides a :class:`.TimeSeriesToolBar`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(timeseriestoolbar.TimeSeriesToolBar, tsPanel=self)


    @actions.action
    def addMaskDataSeries(self):
        """Executes the :class:`AddMaskDataSeriesAction`. """
        self.__addMaskAction()


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``TimeSeriesPanel``.
        """
        actionz = [self.screenshot,
                   self.importDataSeries,
                   self.exportDataSeries,
                   None,
                   self.toggleOverlayList,
                   self.togglePlotList,
                   self.toggleTimeSeriesToolBar,
                   self.toggleTimeSeriesControl]

        names = [a.__name__ if a is not None else None for a in actionz]

        return list(zip(names, actionz))


    def getTools(self):
        """Returns a list of tools to be added to the ``FSLeyesFrame`` for
        ``TimeSeriesPanel`` views.
        """
        return [self.addMaskDataSeries]


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Passes some :class:`.TimeSeries`
        instances to the :meth:`.PlotPanel.drawDataSeries` method.
        """

        if not self or self.destroyed():
            return

        tss = self.getDataSeriesToPlot()

        # Include all of the extra model series
        # for all FEATTimeSeries instances
        newTss = []
        for ts in tss:
            if isinstance(ts, plotting.FEATTimeSeries):

                mtss    = ts.getModelTimeSeries()
                newTss += mtss

                # If the FEATTimeSeries is disabled,
                # disable the associated model time
                # series.
                for mts in mtss:
                    mts.enabled = ts.enabled
            else:
                newTss.append(ts)
        tss = newTss

        for ts in tss:

            # Changing the label might trigger
            # another call to this method, as
            # the PlotPanel might have a listener
            # registered on it. Hence the suppress
            with props.suppress(ts, 'label'):
                ts.label = ts.makeLabel()

        xlabel, ylabel = self.__generateDefaultLabels(tss)

        self.drawDataSeries(extraSeries=tss, xlabel=xlabel, ylabel=ylabel)
        self.drawArtists()


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

        displayCtx  = self.displayCtx
        overlayList = self.overlayList
        tsargs      = (overlay, overlayList, displayCtx, self)

        # Is this a FEAT filtered_func_data image?
        if isinstance(overlay, fslfeatimage.FEATImage):

            # If the filtered_func for this FEAT analysis
            # has been loaded, we show its time series.
            ts        = plotting.FEATTimeSeries(*tsargs)
            targets   = [displayCtx]
            propNames = ['location']

        # If this is a melodic IC image, and we are
        # currently configured to plot component ICs,
        # we use a MelodicTimeSeries object.
        elif isinstance(overlay, fslmelimage.MelodicImage) and \
             self.plotMelodicICs:
            ts        = plotting.MelodicTimeSeries(*tsargs)
            targets   = [displayCtx.getOpts(overlay)]
            propNames = ['volume']

        # Otherwise we just plot
        # bog-standard 4D voxel data
        # (listening to volumeDim for
        # images with >4 dimensions)
        elif isinstance(overlay, fslimage.Image) and overlay.ndim > 3:
            ts        = plotting.VoxelTimeSeries(*tsargs)
            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'volumeDim']

        elif isinstance(overlay, fslmesh.Mesh):
            ts        = plotting.MeshTimeSeries(*tsargs)
            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'vertexData']

        else:
            return None, None, None

        ts.colour    = self.getOverlayPlotColour(overlay)
        ts.alpha     = 1
        ts.lineWidth = 1
        ts.lineStyle = '-'
        ts.label     = ts.makeLabel()

        return ts, targets, propNames


    def prepareDataSeries(self, ts):
        """Overrides :class:`.PlotPanel.prepareDataSeries`. Given a
        :class:`.TimeSeries` instance, scales and normalises the x and y data
        according to the current values of the :attr:`usePixdim` and
        :attr:`plotMode` properties.
        """

        xdata, ydata = ts.getData()

        if len(xdata) == 0:
            return xdata, ydata

        if self.usePixdim and isinstance(ts.overlay, fslimage.Image):
            if isinstance(ts.overlay, fslmelimage.MelodicImage):
                xdata = xdata * ts.overlay.tr
            else:
                xdata = xdata * ts.overlay.pixdim[3]

            toffset = ts.overlay.nibImage.header.get('toffset', 0)
            xdata  += toffset

        if self.plotMode == 'demean':
            ydata = ydata - ydata.mean()

        elif self.plotMode == 'normalise':
            ymin  = ydata.min()
            ymax  = ydata.max()
            if not np.isclose(ymin, ymax):
                ydata = 2 * (ydata - ymin) / (ymax - ymin) - 1
            else:
                ydata = np.zeros(len(ydata))

        elif self.plotMode == 'percentChange':
            mean  = ydata.mean()
            ydata = 100 * (ydata / mean) - 100

        return xdata, ydata


    def __plotMelodicICsChanged(self, *a):
        """Called when the :attr:`plotMelodicICs` property changes. Re-creates
        the internally cached :class:`.TimeSeries` instances for all
        :class:`.MelodicImage` overlays in the :class:`.OverlayList`.
        """

        for overlay in self.overlayList:
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.clearDataSeries(overlay)

        self.updateDataSeries()
        self.draw()


    def __generateDefaultLabels(self, timeSeries):
        """Called by :meth:`draw`. If the :attr:`.PlotPanel.xlabel` or
        :attr:`.PlotPanel.ylabel` properties are unset, an attempt is made
        to generate default labels.
        """

        xlabel = self.xlabel
        ylabel = self.ylabel

        if xlabel is not None:
            return xlabel, ylabel

        if not self.usePixdim:
            xlabel = strings.nifti['t_unit', -1]
            return xlabel, ylabel

        # If all of the overlays related to the data series being
        # plotted:
        #
        #   - are Images
        #   - have the same time unit (as specified in the nifti header)
        #
        # Then a default label is specified
        #
        # n.b. this is not foolproof, as many
        # non-time 4D images will still set
        # the time units to seconds.
        #
        #
        # TODO Non-Image overlays with associated
        #      time series (e.g. MeshOpts)

        # Get all the unique overlays
        overlays = [ts.overlay for ts in it.chain(timeSeries, self.dataSeries)]
        overlays = set(overlays)

        if not all([isinstance(o, fslimage.Image) for o in overlays]):
            return xlabel, ylabel

        # And all of their time units
        units = [o.timeUnits for o in overlays]

        if len(set(units)) == 1:
            xlabel = strings.nifti.get(('t_unit', units[0]),
                                       'INVALID TIME UNITS')

        return xlabel, ylabel
