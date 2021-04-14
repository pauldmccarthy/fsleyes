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

import fsl.data.featimage                 as fslfeatimage
import fsl.data.melodicimage              as fslmelimage
import fsl.data.image                     as fslimage
import fsl.data.mesh                      as fslmesh
import fsleyes_props                      as props

import fsleyes.overlay                    as fsloverlay
import fsleyes.strings                    as strings
import fsleyes.profiles.timeseriesprofile as timeseriesprofile
import fsleyes.plotting.timeseries        as timeseries
import fsleyes.views.plotpanel            as plotpanel


log = logging.getLogger(__name__)


class TimeSeriesPanel(plotpanel.OverlayPlotPanel):
    """The ``TimeSeriesPanel`` is an :class:`.OverlayPlotPanel` which plots
    time series data from overlays. A ``TimeSeriesPanel`` looks something like
    the following:


    .. image:: images/timeseriespanel.png
       :scale: 50%
       :align: center


    A ``TimeSeriesPanel`` plots one or more :class:`.DataSeries` instances,
    which encapsulate time series data from an overlay. All time series
    related ``DataSeries`` classes are defined in the
    :mod:`.plotting.timeseries` module; these are all sub-classes of the
    :class:`.DataSeries` class - see the :class:`.PlotPanel` and
    :class:`.OverlayPlotPanel` documentation for more details:

    .. autosummary::
       :nosignatures:

       .timeseries.VoxelTimeSeries
       .timeseries.ComplexTimeSeries
       .timeseries.FEATTimeSeries
       .timeseries.MelodicTimeSeries
       .timeseries.MeshTimeSeries


    **Control panels**


    Some *FSLeyes control* panels are associated with the
    :class:`.TimeSeriesPanel`, and can be added/removed via
    :meth:`.ViewPanel.togglePanel`.

    .. autosummary::
       :nosignatures:

       ~fsleyes.controls.plotlistpanel.PlotListPanel
       ~fsleyes.controls.timeseriescontrolpanel.TimeSeriesControlPanel


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
    4D :class:`.Image` overlays (a :class:`.VoxelTimeSeries` instance is used).
    """


    @staticmethod
    def defaultLayout():
        """Returns a list of control panel types to be added for the default
        time series panel layout.
        """
        return ['TimeSeriesToolBar',
                'OverlayListPanel',
                'PlotListPanel']


    @staticmethod
    def controlOrder():
        """Returns a list of control panel names, specifying the order in
        which they should appear in the  FSLeyes ortho panel settings menu.
        """
        return ['OverlayListPanel',
                'PlotListPanel',
                'TimeSeriesToolBar',
                'TimeSeriesControlPanel']


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

        self.initProfile(timeseriesprofile.TimeSeriesProfile)


    def destroy(self):
        """Removes some listeners, and calls the :meth:`.PlotPanel.destroy`
        method.
        """

        self.removeListener('plotMode',       self.name)
        self.removeListener('usePixdim',      self.name)
        self.removeListener('plotMelodicICs', self.name)

        plotpanel.OverlayPlotPanel.destroy(self)


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``TimeSeriesPanel``.
        """
        actionz = [self.screenshot,
                   self.importDataSeries,
                   self.exportDataSeries]

        names = [a.actionName if a is not None else None for a in actionz]
        return list(zip(names, actionz))


    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Passes some :class:`.DataSeries`
        instances to the :meth:`.PlotCanvas.drawDataSeries` method, then
        calls :meth:`.PlotCanvas.drawArtists`.
        """

        if not self or self.destroyed:
            return

        tss = self.getDataSeriesToPlot()
        for ts in tss:

            # Changing the label might trigger
            # another call to this method, as
            # the PlotPanel might have a listener
            # registered on it. Hence the suppress
            with props.suppress(ts, 'label'):
                ts.label = ts.makeLabel()

        xlabel, ylabel = self.__generateDefaultLabels(tss)

        self.canvas.drawDataSeries(extraSeries=tss,
                                   xlabel=xlabel,
                                   ylabel=ylabel)
        self.canvas.drawArtists()


    def createDataSeries(self, overlay):
        """Overrides :meth:`.OverlayPlotPanel.createDataSeries`. Creates and
        returns a :class:`.TimeSeries` instance (or an instance of one of the
        :class:`.TimeSeries` sub-classes) for the specified overlay.

        Returns a tuple containing the following:

          - A :class:`.DataSeries` instance for the given overlay

          - A list of *targets* - objects which have properties that
            influence the state of the ``TimeSeries`` instance.

          - A list of *property names*, one for each target.

        If the given overlay is not compatible (i.e. it has no time series
        data to be plotted), a tuple of ``None`` values is returned.
        """

        displayCtx  = self.displayCtx
        overlayList = self.overlayList
        tsargs      = (overlay, overlayList, displayCtx, self.canvas)

        # Is this a mesh?
        if isinstance(overlay, fslmesh.Mesh):
            ts        = timeseries.MeshTimeSeries(*tsargs)
            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'vertexData']

        # Is this a FEAT filtered_func_data image?
        elif isinstance(overlay, fslfeatimage.FEATImage):

            # If the filtered_func for this FEAT analysis
            # has been loaded, we show its time series.
            ts        = timeseries.FEATTimeSeries(*tsargs)
            targets   = [displayCtx]
            propNames = ['location']

        # If this is a melodic IC image, and we are
        # currently configured to plot component ICs,
        # we use a MelodicTimeSeries object.
        elif isinstance(overlay, fslmelimage.MelodicImage) and \
             self.plotMelodicICs:
            ts        = timeseries.MelodicTimeSeries(*tsargs)
            targets   = [displayCtx.getOpts(overlay)]
            propNames = ['volume']

        # Otherwise it's a normal image
        elif isinstance(overlay, fslimage.Image) and overlay.ndim > 3:

            # Is it a complex data image?
            if overlay.iscomplex:
                ts = timeseries.ComplexTimeSeries(*tsargs)

            # Or just a bog-standard 4D image?
            else:
                ts = timeseries.VoxelTimeSeries(*tsargs)

            # listen to volumeDim for
            # images with >4 dimensions
            opts      = displayCtx.getOpts(overlay)
            targets   = [displayCtx, opts]
            propNames = ['location', 'volumeDim']
        else:
            return None, None, None

        ts.colour    = self.getOverlayPlotColour(overlay)
        ts.lineStyle = self.getOverlayPlotStyle(overlay)
        ts.lineWidth = 2
        ts.alpha     = 1

        return ts, targets, propNames


    def prepareDataSeries(self, ts):
        """Overrides :class:`.PlotPanel.prepareDataSeries`. Given a
        :class:`.DataSeries` instance, scales and normalises the x and y data
        according to the current values of the :attr:`usePixdim` and
        :attr:`plotMode` properties.
        """

        xdata, ydata = ts.getData()

        if (xdata is None) or (ydata is None) or (len(xdata) == 0):
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
        """Called by :meth:`draw`. If the :attr:`.PlotCanvas.xlabel` or
        :attr:`.PlotCanvas.ylabel` properties are unset, an attempt is made
        to generate default labels.
        """

        xlabel = self.canvas.xlabel
        ylabel = self.canvas.ylabel

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
        overlays = [ts.overlay
                    for ts in it.chain(timeSeries, self.canvas.dataSeries)]
        overlays = set(overlays)

        if not all([isinstance(o, fslimage.Image) for o in overlays]):
            return xlabel, ylabel

        # And all of their time units
        units = [o.timeUnits for o in overlays]

        if len(set(units)) == 1:
            xlabel = strings.nifti.get(('t_unit', units[0]),
                                       'INVALID TIME UNITS')

        return xlabel, ylabel
