#!/usr/bin/env python
#
# plotpanel.py - The PlotPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PlotPanel` and :class:`.OverlayPlotPanel`
classes.  The ``PlotPanel`` class is the base class for all *FSLeyes views*
which display some sort of data plot. The ``OverlayPlotPanel`` is a
``PlotPanel`` which contains some extra logic for displaying plots related to
the currently selected overlay.
"""


import logging
import collections

import wx

import numpy             as np
import scipy.interpolate as interp

import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas

import fsl.utils.async                    as async
from   fsl.utils.platform import platform as fslplatform
import fsleyes_props                      as props
import fsleyes_widgets.elistbox           as elistbox

import fsleyes.strings                    as strings
import fsleyes.actions                    as actions
import fsleyes.overlay                    as fsloverlay
import fsleyes.colourmaps                 as fslcm
import fsleyes.plotting                   as plotting
import fsleyes.controls.overlaylistpanel  as overlaylistpanel
import fsleyes.controls.plotlistpanel     as plotlistpanel
from . import                                viewpanel


log = logging.getLogger(__name__)


class PlotPanel(viewpanel.ViewPanel):
    """The ``PlotPanel`` class is the base class for all *FSLeyes views*
    which display some sort of 2D data plot, such as the
    :class:`.TimeSeriesPanel`, and the :class:`.HistogramPanel`.
    See also the :class:`OverlayPlotPanel`, which contains extra logic for
    displaying plots related to the currently selected overlay.


    ``PlotPanel`` uses :mod:`matplotlib` for its plotting. The ``matplotlib``
    ``Figure``, ``Axis``, and ``Canvas`` instances can be accessed via the
    :meth:`getFigure`, :meth:`getAxis`, and :meth:`getCanvas` methods, if they
    are needed. Various display settings can be configured through
    ``PlotPanel`` properties, including :attr:`legend`, :attr:`smooth`, etc.


    **Sub-class requirements**

    Sub-class implementations of ``PlotPanel`` must do the following:

      1. Call the ``PlotPanel`` constructor.

      2. Define a :class:`.DataSeries` sub-class.

      3. Override the :meth:`draw` method, so it calls the
         :meth:`drawDataSeries` method.

      4. If necessary, override the :meth:`prepareDataSeries` method to
         perform any preprocessing on ``extraSeries`` passed to the
         :meth:`drawDataSeries` method (but not applied to
         :class:`.DataSeries` that have been added to the :attr:`dataSeries`
         list).

      5. If necessary, override the :meth:`destroy` method, but make
         sure that the base-class implementation is called.


    **Data series**

    A ``PlotPanel`` instance plots data contained in one or more
    :class:`.DataSeries` instances; all ``DataSeries`` classes are defined in
    the :mod:`.plotting` sub-package.  Therefore, ``PlotPanel`` sub-classes
    also need to define a sub-class of the :class:`.DataSeries` base class.

    ``DataSeries`` objects can be plotted by passing them to the
    :meth:`drawDataSeries` method.

    Or, if you want one or more ``DataSeries`` to be *held*, i.e. plotted
    every time, you can add them to the :attr:`dataSeries` list. The
    ``DataSeries`` in the :attr:`dataSeries` list will be plotted on every
    call to :meth:`drawDataSeries` (in addition to any ``DataSeries`` passed
    directly to :meth:`drawDataSeries`) until they are removed from the
    :attr:`dataSeries` list.


    **The draw queue**


    The ``PlotPanel`` uses a :class:`.async.TaskThread` to asynchronously
    extract and prepare data for plotting, This is because data preparation
    may take a long time for large :class:`.Image` overlays, and the main
    application thread should not be blocked while this is occurring. The
    ``TaskThread`` instance is accessible through the :meth:`getDrawQueue`
    method, in case anything needs to be scheduled on it.


    **Plot panel actions**

    A number of :mod:`actions` are also provided by the ``PlotPanel`` class:

    .. autosummary::
       :nosignatures:

       screenshot
       importDataSeries
       exportDataSeries
    """


    dataSeries = props.List()
    """This list contains :class:`.DataSeries` instances which are plotted
    on every call to :meth:`drawDataSeries`. ``DataSeries`` instances can
    be added/removed directly to/from this list.
    """


    artists = props.List()
    """This list contains any ``matplotlib.Artist`` instances which are
    plotted every call to :meth:`drawArtists`.
    """


    legend = props.Boolean(default=True)
    """If ``True``, a legend is added to the plot, with an entry for every
    ``DataSeries`` instance in the :attr:`dataSeries` list.
    """


    xAutoScale = props.Boolean(default=True)
    """If ``True``, the plot :attr:`limits` for the X axis are automatically
    updated to fit all plotted data.
    """


    yAutoScale = props.Boolean(default=True)
    """If ``True``, the plot :attr:`limits` for the Y axis are automatically
    updated to fit all plotted data.
    """


    xLogScale = props.Boolean(default=False)
    """Toggle a :math:`log_{10}` x axis scale. """


    yLogScale = props.Boolean(default=False)
    """Toggle a :math:`log_{10}` y axis scale. """


    ticks = props.Boolean(default=True)
    """Toggle axis ticks and tick labels on/off."""


    grid = props.Boolean(default=True)
    """Toggle an axis grid on/off."""


    gridColour = props.Colour(default=(1, 1, 1))
    """Grid colour (if :attr:`grid` is ``True``)."""


    bgColour = props.Colour(default=(0.8, 0.8, 0.8))
    """Plot background colour."""


    smooth = props.Boolean(default=False)
    """If ``True`` all plotted data is up-sampled, and smoothed using
    spline interpolation.
    """


    xlabel = props.String()
    """A label to show on the x axis. """


    ylabel = props.String()
    """A label to show on the y axis. """


    limits = props.Bounds(ndims=2)
    """The x/y axis limits. If :attr:`xAutoScale` and :attr:`yAutoScale` are
    ``True``, these limit values are automatically updated on every call to
    :meth:`drawDataSeries`.
    """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``PlotPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: An :class:`.OverlayList` instance.

        :arg displayCtx:  A :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        figure = plt.Figure()
        axis   = figure.add_subplot(111)
        canvas = Canvas(self, -1, figure)

        figure.subplots_adjust(top=1.0, bottom=0.0, left=0.0, right=1.0)
        figure.patch.set_visible(False)

        self.setCentrePanel(canvas)

        self.__figure    = figure
        self.__axis      = axis
        self.__canvas    = canvas
        self.__name      = 'PlotPanel_{}'.format(self._name)

        # Accessing data from large compressed
        # files may take time, so we maintain
        # a queue of plotting requests. The
        # functions executed on this task
        # thread are used to prepare data for
        # plotting - the plotting occurs on
        # the main WX event loop.
        #
        # The drawDataSeries method sets up the
        # asynchronous data preparation, and the
        # __drawDataSeries method does the actual
        # plotting.
        self.__drawQueue = async.TaskThread()
        self.__drawQueue.daemon = True
        self.__drawQueue.start()

        # Whenever a new request comes in to
        # draw the plot, we can't cancel any
        # pending requests, as they are running
        # on separate threads and out of our
        # control (and could be blocking on I/O).
        #
        # Instead, we keep track of the total
        # number of pending requests. The
        # __drawDataSeries method (which does the
        # actual plotting) will only draw the
        # plot if there are no pending requests
        # (because otherwise it would be drawing
        # out-of-date data).
        self.__drawRequests = 0

        # The getDrawnDataSeries method returns
        # data as it is shown on the plot - some
        # pre/post-processing may be applied to
        # the data as retrieved by DataSeries
        # instances, so this dictionary is used
        # to keep copies of the mpl Artist object
        # which contains the data with all
        # processing applied, that is currrently
        # on the plot (and accessible via
        # getDrawnDataSeries).
        self.__drawnDataSeries = collections.OrderedDict()

        # Redraw whenever any property changes,
        for propName in ['legend',
                         'xAutoScale',
                         'yAutoScale',
                         'xLogScale',
                         'yLogScale',
                         'ticks',
                         'grid',
                         'gridColour',
                         'bgColour',
                         'smooth',
                         'xlabel',
                         'ylabel']:
            self.addListener(propName, self.__name, self.asyncDraw)

        # custom listeners for a couple of properties
        self.addListener('dataSeries',
                         self.__name,
                         self.__dataSeriesChanged)
        self.addListener('artists',
                         self.__name,
                         self.__artistsChanged)
        self.addListener('limits',
                         self.__name,
                         self.__limitsChanged)


    def getFigure(self):
        """Returns the ``matplotlib`` ``Figure`` instance."""
        return self.__figure


    def getAxis(self):
        """Returns the ``matplotlib`` ``Axis`` instance."""
        return self.__axis


    def getCanvas(self):
        """Returns the ``matplotlib`` ``Canvas`` instance."""
        return self.__canvas


    def getDrawQueue(self):
        """Returns the :class`.async.DrawQueue` instance used for data
        preparation.
        """
        return self.__drawQueue


    def draw(self, *a):
        """This method must be overridden by ``PlotPanel`` sub-classes.

        It is called whenever a :class:`.DataSeries` is added to the
        :attr:`dataSeries` list, or when any plot display properties change.

        Sub-class implementations should call the :meth:`drawDataSeries`
        and meth:`drawArtists` methods.
        """
        raise NotImplementedError('The draw method must be '
                                  'implemented by PlotPanel subclasses')


    def asyncDraw(self, *a):
        """Schedules :meth:`draw` to be run asynchronously. This method
        should be used in preference to calling :meth:`draw` directly
        in most cases, particularly where the call occurs within a
        property callback function.
        """

        idleName = '{}.draw'.format(id(self))

        if not self.destroyed() and not async.inIdle(idleName):
            async.idle(self.draw, name=idleName)


    def destroy(self):
        """Removes some property listeners, and then calls
        :meth:`.ViewPanel.destroy`.
        """

        self.__drawQueue.stop()
        self.__drawQueue = None

        self.removeListener('dataSeries', self.__name)
        self.removeListener('artists',    self.__name)
        self.removeListener('limits',     self.__name)

        for propName in ['legend',
                         'xAutoScale',
                         'yAutoScale',
                         'xLogScale',
                         'yLogScale',
                         'ticks',
                         'grid',
                         'gridColour',
                         'bgColour',
                         'smooth',
                         'xlabel',
                         'ylabel']:
            self.removeListener(propName, self.__name)

        for ds in self.dataSeries:

            for propName in ds.redrawProperties():
                ds.removeListener(propName, self.__name)
            ds.destroy()

        self.dataSeries = []
        self.artists    = []

        viewpanel.ViewPanel.destroy(self)


    @actions.action
    def screenshot(self, *a):
        """Prompts the user to select a file name, then saves a screenshot
        of the current plot.
        """

        formats  = list(self.__canvas.get_supported_filetypes().items())

        wildcard = ['{}|*.{}'.format(desc, fmt) for fmt, desc in formats]
        wildcard = '|'.join(wildcard)

        dlg = wx.FileDialog(self,
                            message=strings.messages[self, 'screenshot'],
                            wildcard=wildcard,
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() != wx.ID_OK:
            return

        path = dlg.GetPath()

        try:
            self.__figure.savefig(path)

        except Exception as e:
            wx.MessageBox(
                strings.messages[self, 'screenshot', 'error'].format(str(e)),
                strings.titles[  self, 'screenshot', 'error'],
                wx.ICON_ERROR)


    @actions.action
    def importDataSeries(self, *a):
        """Imports data series from a text file.

        See the :class:`.ImportDataSeriesAction`.
        """

        from fsleyes.actions.importdataseries import ImportDataSeriesAction

        ImportDataSeriesAction(self.getOverlayList(),
                               self.getDisplayContext(),
                               self)()


    @actions.action
    def exportDataSeries(self, *args, **kwargs):
        """Exports displayed data series to a text file.

        See the :class:`.ExportDataSeriesAction`.
        """

        from fsleyes.actions.exportdataseries import ExportDataSeriesAction

        ExportDataSeriesAction(self.getOverlayList(),
                               self.getDisplayContext(),
                               self)()


    def message(self, msg, clear=True, border=False):
        """Displays the given message in the centre of the figure.

        This is a convenience method provided for use by subclasses.
        """

        axis = self.getAxis()

        if clear:
            self.__drawnDataSeries.clear()
            axis.clear()
            axis.set_xlim((0.0, 1.0))
            axis.set_ylim((0.0, 1.0))

        if border:
            bbox = {'facecolor' : '#ffffff',
                    'edgecolor' : '#cdcdff',
                    'boxstyle'  : 'round,pad=1'}
        else:
            bbox = None

        axis.text(0.5, 0.5,
                  msg,
                  ha='center', va='center',
                  transform=axis.transAxes,
                  bbox=bbox)

        self.getCanvas().draw()
        self.Refresh()


    def getArtist(self, ds):
        """Returns the ``matplotlib.Artist`` (typically a ``Line2D`` instance)
        associated with the given :class:`.DataSeries` instance. A
        ``KeyError`` is raised if there is no such artist.
        """

        return self.__drawnDataSeries[ds]


    def getDrawnDataSeries(self):
        """Returns a list of tuples, each tuple containing the
        ``(DataSeries, x, y)`` data for one ``DataSeries`` instance
        as it is shown on the plot.
        """

        return [(ds, np.array(l.get_xdata()), np.array(l.get_ydata()))
                for ds, l in self.__drawnDataSeries.items()]


    def prepareDataSeries(self, ds):
        """Prepares the data from the given :class:`.DataSeries` so it is
        ready to be plotted. Called by the :meth:`__drawOneDataSeries` method
        for any ``extraSeries`` passed to the :meth:`drawDataSeries` method
        (but not applied to :class:`.DataSeries` that have been added to the
        :attr:`dataSeries` list).

        This implementation just returns :class:`.DataSeries.getData` -
        override it to perform any custom preprocessing.
        """
        return ds.getData()


    def drawArtists(self, refresh=True, immediate=False):
        """Draw all ``matplotlib.Artist`` instances in the :attr:`artists`
        list, then refresh the canvas.

        :arg refresh: If ``True`` (default), the canvas is refreshed.
        """

        axis   = self.getAxis()
        canvas = self.getCanvas()

        def realDraw():

            # Just in case this PlotPanel is destroyed
            # before this task gets executed
            if not fslplatform.isWidgetAlive(self):
                return

            for artist in self.artists:
                if artist not in axis.findobj(type(artist)):
                    axis.add_artist(artist)

        if immediate: realDraw()
        else:
            self.__drawQueue.enqueue(async.idle, realDraw)

        if refresh:
            if immediate: canvas.draw()
            else:         self.__drawQueue.enqueue(async.idle, canvas.draw)


    def drawDataSeries(self, extraSeries=None, refresh=False, **plotArgs):
        """Queues a request to plot all of the :class:`.DataSeries` instances
        in the :attr:`dataSeries` list.

        This method does not do the actual plotting - it is performed
        asynchronously, to avoid locking up the GUI:

         1. The data for each ``DataSeries`` instance is prepared on
            separate threads (using :func:`.async.run`).

         2. A call to :func:`.async.wait` is enqueued on a
            :class:`.TaskThread`.

         3. This ``wait`` function waits until all of the data preparation
            threads have completed, and then passes all of the data to
            the :meth:`__drawDataSeries` method.

        :arg extraSeries: A sequence of additional ``DataSeries`` to be
                          plotted. These series are passed through the
                          :meth:`prepareDataSeries` method before being
                          plotted.

        :arg refresh:     If ``True``, the canvas is refreshed. Otherwise,
                          you must call ``getCanvas().draw()`` manually.
                          Defaults to ``False`` - the :meth:`drawArtists`
                          method will refresh the canvas, so if you call
                          :meth:`drawArtists` immediately after calling
                          this method (which you should), then you don't
                          need to manually refresh the canvas.

        :arg plotArgs:    Passed through to the :meth:`__drawDataSeries`
                          method.


        .. note:: This method must only be called from the main application
                  thread (the ``wx`` event loop).
        """

        if extraSeries is None:
            extraSeries = []

        canvas      = self.getCanvas()
        axis        = self.getAxis()
        toPlot      = self.dataSeries[:]

        toPlot      = [ds for ds in toPlot      if ds.enabled]
        extraSeries = [ds for ds in extraSeries if ds.enabled]

        toPlot      = extraSeries + toPlot
        preprocs    = [True] * len(extraSeries) + [False] * len(toPlot)

        if len(toPlot) == 0:
            self.__drawnDataSeries.clear()
            axis.clear()
            canvas.draw()
            self.Refresh()
            return

        # Before clearing/redrawing, save
        # a copy of the x/y axis limits -
        # the user may have changed them
        # via panning/zooming and, if
        # autoLimit is off, we will want
        # to preserve the limits that the
        # user set. These are passed to
        # the __drawDataSeries method.
        axxlim = axis.get_xlim()
        axylim = axis.get_ylim()

        # Here we are preparing the data for
        # each data series on separate threads,
        # as data preparation can be time
        # consuming for large images. We
        # display a message on the canvas
        # during preparation.
        tasks    = []
        allXdata = [None] * len(toPlot)
        allYdata = [None] * len(toPlot)

        # Create a separate function
        # for each data series
        for idx, (ds, preproc) in enumerate(zip(toPlot, preprocs)):

            def getData(d=ds, p=preproc, i=idx):

                if not d.enabled:
                    return

                if p: xdata, ydata = self.prepareDataSeries(d)
                else: xdata, ydata = d.getData()

                allXdata[i] = xdata
                allYdata[i] = ydata

            tasks.append(getData)

        # Run the data preparation tasks,
        # a separate thread for each.
        tasks = [async.run(t) for t in tasks]

        # Show a message while we're
        # preparing the data.
        self.message(strings.messages[self, 'preparingData'],
                     clear=False,
                     border=True)

        # Wait until data preparation is
        # done, then call __drawDataSeries.
        self.__drawRequests += 1
        self.__drawQueue.enqueue(async.wait,
                                 tasks,
                                 self.__drawDataSeries,
                                 toPlot,
                                 allXdata,
                                 allYdata,
                                 axxlim,
                                 axylim,
                                 refresh,
                                 taskName='{}.wait'.format(id(self)),
                                 wait_direct=True,
                                 **plotArgs)


    def __drawDataSeries(
            self,
            dataSeries,
            allXdata,
            allYdata,
            oldxlim,
            oldylim,
            refresh,
            xlabel=None,
            ylabel=None,
            **plotArgs):
        """Called by :meth:`__drawDataSeries`. Plots all of the data
        associated with the given ``dataSeries``.

        :arg dataSeries: The list of :class:`.DataSeries` instances to plot.

        :arg allXdata:   A list of arrays containing X axis data, one for each
                         ``DataSeries``.

        :arg allYdata:   A list of arrays containing Y axis data, one for each
                         ``DataSeries``.

        :arg oldxlim:    X plot limits from the previous draw. If
                         ``xAutoScale`` is disabled, this limit is preserved.

        :arg oldylim:    Y plot limits from the previous draw. If
                         ``yAutoScale`` is disabled, this limit is preserved.

        :arg refresh:    Refresh the canvas - see :meth:`drawDataSeries`.

        :arg xlabel:     If provided, overrides the value of the :attr:`xlabel`
                         property.

        :arg ylabel:     If provided, overrides the value of the :attr:`ylabel`
                         property.

        :arg plotArgs:   Remaining arguments passed to the
                         :meth:`__drawOneDataSeries` method.
        """

        # Only draw the plot if there are no
        # pending draw requests. Otherwise
        # we would be drawing out-of-date data.
        self.__drawRequests -= 1
        if self.__drawRequests != 0:
            return

        axis          = self.getAxis()
        canvas        = self.getCanvas()
        width, height = canvas.get_width_height()

        self.__drawnDataSeries.clear()
        axis.clear()

        xlims = []
        ylims = []

        for ds, xdata, ydata in zip(dataSeries, allXdata, allYdata):

            if any((ds is None, xdata is None, ydata is None)):
                continue

            if not ds.enabled:
                continue

            xlim, ylim = self.__drawOneDataSeries(ds,
                                                  xdata,
                                                  ydata,
                                                  **plotArgs)

            if np.any(np.isclose([xlim[0], ylim[0]], [xlim[1], ylim[1]])):
                continue

            xlims.append(xlim)
            ylims.append(ylim)

        if len(xlims) == 0:
            xmin, xmax = 0.0, 0.0
            ymin, ymax = 0.0, 0.0
        else:
            (xmin, xmax), (ymin, ymax) = self.__calcLimits(
                xlims, ylims, oldxlim, oldylim, width, height)

        # x/y axis labels
        if xlabel is None: xlabel = self.xlabel
        if ylabel is None: ylabel = self.ylabel
        if xlabel is None: xlabel = ''
        if ylabel is None: ylabel = ''

        xlabel = xlabel.strip()
        ylabel = ylabel.strip()

        if xlabel != '':
            axis.set_xlabel(xlabel, va='bottom')
            axis.xaxis.set_label_coords(0.5, 10.0 / height)

        if ylabel != '':
            axis.set_ylabel(ylabel, va='top')
            axis.yaxis.set_label_coords(10.0 / width, 0.5)

        # Ticks
        if self.ticks:
            axis.tick_params(direction='in', pad=-5)

            for ytl in axis.yaxis.get_ticklabels():
                ytl.set_horizontalalignment('left')

            for xtl in axis.xaxis.get_ticklabels():
                xtl.set_verticalalignment('bottom')
        else:
            xlabels = ['' for i in range(len(axis.xaxis.get_ticklabels()))]
            ylabels = ['' for i in range(len(axis.yaxis.get_ticklabels()))]

            axis.set_xticklabels(xlabels)
            axis.set_yticklabels(ylabels)

        # Limits
        if xmin != xmax:
            axis.set_xlim((xmin, xmax))
            axis.set_ylim((ymin, ymax))

        # legend
        labels = [ds.label for ds in dataSeries if ds.label is not None]
        if len(labels) > 0 and self.legend:
            handles, labels = axis.get_legend_handles_labels()
            legend          = axis.legend(
                handles,
                labels,
                loc='upper right',
                fontsize=10,
                fancybox=True)
            legend.get_frame().set_alpha(0.6)

        if self.grid:
            axis.grid(linestyle='-',
                      color=self.gridColour,
                      linewidth=0.5,
                      zorder=0)
        else:
            axis.grid(False)

        axis.set_axisbelow(True)
        axis.patch.set_facecolor(self.bgColour)
        self.getFigure().patch.set_alpha(0)

        if refresh:
            canvas.draw()


    def __drawOneDataSeries(self, ds, xdata, ydata, **plotArgs):
        """Plots a single :class:`.DataSeries` instance. This method is called
        by the :meth:`drawDataSeries` method.

        :arg ds:       The ``DataSeries`` instance.
        :arg xdata:    X axis data.
        :arg ydata:    Y axis data.
        :arg plotArgs: May be used to customise the plot - these
                       arguments are all passed through to the
                       ``Axis.plot`` function.
        """

        if ds.alpha == 0:
            return (0, 0), (0, 0)

        if len(xdata) != len(ydata) or len(xdata) == 0:
            log.debug('{}: data series length mismatch, or '
                      'no data points (x: {}, y: {})'.format(
                          ds.overlay.name, len(xdata), len(ydata)))
            return (0, 0), (0, 0)

        log.debug('Drawing {} for {}'.format(type(ds).__name__, ds.overlay))

        # Note to self: If the smoothed data is
        # filled with NaNs, it is possibly due
        # to duplicate values in the x data, which
        # are not handled very well by splrep.
        if self.smooth:

            tck   = interp.splrep(xdata, ydata)
            xdata = np.linspace(xdata[0],
                                xdata[-1],
                                len(xdata) * 5,
                                dtype=np.float32)
            ydata = interp.splev(xdata, tck)

        nans        = ~(np.isfinite(xdata) & np.isfinite(ydata))
        xdata[nans] = np.nan
        ydata[nans] = np.nan

        if self.xLogScale: xdata[xdata <= 0] = np.nan
        if self.yLogScale: ydata[ydata <= 0] = np.nan

        if np.all(np.isnan(xdata) | np.isnan(ydata)):
            return (0, 0), (0, 0)

        kwargs = plotArgs

        kwargs['lw']    = kwargs.get('lw',    ds.lineWidth)
        kwargs['alpha'] = kwargs.get('alpha', ds.alpha)
        kwargs['color'] = kwargs.get('color', ds.colour)
        kwargs['label'] = kwargs.get('label', ds.label)
        kwargs['ls']    = kwargs.get('ls',    ds.lineStyle)

        axis = self.getAxis()
        line = axis.plot(xdata, ydata, **kwargs)[0]

        self.__drawnDataSeries[ds] = line

        if self.xLogScale:
            axis.set_xscale('log')
            posx    = xdata[xdata > 0]
            xlimits = np.nanmin(posx), np.nanmax(posx)

        else:
            xlimits = np.nanmin(xdata), np.nanmax(xdata)

        if self.yLogScale:
            axis.set_yscale('log')
            posy    = ydata[ydata > 0]
            ylimits = np.nanmin(posy), np.nanmax(posy)
        else:
            ylimits = np.nanmin(ydata), np.nanmax(ydata)

        return xlimits, ylimits


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`dataSeries` list changes. Adds listeners
        to any new :class:`.DataSeries` instances, and then calls
        :meth:`asyncDraw`.
        """

        for ds in self.dataSeries:
            for propName in ds.redrawProperties():
                ds.addListener(propName,
                               self.__name,
                               self.asyncDraw,
                               overwrite=True)
        self.asyncDraw()


    def __artistsChanged(self, *a):
        """Called when the :attr:`artists` list changes. Calls
        :meth:`asyncDraw`.
        """
        self.asyncDraw()


    def __limitsChanged(self, *a):
        """Called when the :attr:`limits` change. Updates the axis limits
        accordingly.
        """

        axis = self.getAxis()
        axis.set_xlim(self.limits.x)
        axis.set_ylim(self.limits.y)
        self.asyncDraw()


    def __calcLimits(self,
                     dataxlims,
                     dataylims,
                     axisxlims,
                     axisylims,
                     axWidth,
                     axHeight):
        """Calculates and returns suitable axis limits for the current plot.
        Also updates the :attr:`limits` property. This method is called by
        the :meth:`drawDataSeries` method.

        If :attr:`xAutoScale` or :attr:`yAutoScale` are enabled, the limits are
        calculated from the data range, using the canvas width and height to
        maintain consistent padding around the plotted data, irrespective of
        the canvas size.

        . Otherwise, the existing axis limits are retained.

        :arg dataxlims: A tuple containing the (min, max) x data range.

        :arg dataylims: A tuple containing the (min, max) y data range.

        :arg axisxlims: A tuple containing the current (min, max) x axis
                        limits.

        :arg axisylims: A tuple containing the current (min, max) y axis
                        limits.

        :arg axWidth:   Canvas width in pixels

        :arg axHeight:  Canvas height in pixels
        """

        if self.xAutoScale:

            xmin = min([lim[0] for lim in dataxlims])
            xmax = max([lim[1] for lim in dataxlims])

            lPad = (xmax - xmin) * (50.0 / axWidth)
            rPad = (xmax - xmin) * (50.0 / axWidth)

            xmin = xmin - lPad
            xmax = xmax + rPad
        else:
            xmin = axisxlims[0]
            xmax = axisxlims[1]

        if self.yAutoScale:

            ymin = min([lim[0] for lim in dataylims])
            ymax = max([lim[1] for lim in dataylims])

            bPad = (ymax - ymin) * (50.0 / axHeight)
            tPad = (ymax - ymin) * (50.0 / axHeight)

            ymin = ymin - bPad
            ymax = ymax + tPad

        else:

            ymin = axisylims[0]
            ymax = axisylims[1]

        self.disableListener('limits', self.__name)
        self.limits[:] = [xmin, xmax, ymin, ymax]
        self.enableListener('limits', self.__name)

        return (xmin, xmax), (ymin, ymax)


class OverlayPlotPanel(PlotPanel):
    """The ``OverlayPlotPanel`` is a :class:`.PlotPanel` which contains
    some extra logic for creating, storing, and drawing :class:`.DataSeries`
    instances for each overlay in the :class:`.OverlayList`.


    **Subclass requirements**

    Sub-classes must:

     1. Implement the :meth:`createDataSeries` method, so it creates a
        :class:`.DataSeries` instance for a specified overlay.

     2. Implement the :meth:`PlotPanel.draw` method so it calls the
        :meth:`.PlotPanel.drawDataSeries`, passing :class:`.DataSeries`
        instances for all overlays where :attr:`.Display.enabled` is
        ``True``.

     3. Optionally implement the :meth:`prepareDataSeries` method to
        perform any custom preprocessing.


    **The internal data series store**


    The ``OverlayPlotPanel`` maintains a store of :class:`.DataSeries`
    instances, one for each compatible overlay in the
    :class:`.OverlayList`. The ``OverlayPlotPanel`` manages the property
    listeners that must be registered with each of these ``DataSeries`` to
    refresh the plot.  These instances are created by the
    :meth:`createDataSeries` method, which is implemented by sub-classes. The
    following methods are available to sub-classes, for managing the internal
    store of :class:`.DataSeries` instances:

    .. autosummary::
       :nosignatures:

       getDataSeries
       getDataSeriesToPlot
       clearDataSeries
       updateDataSeries
       addDataSeries
       removeDataSeries


    **Proxy images**


    The ``OverlayPlotPanel`` will replace all :class:`.ProxyImage` instances
    with their base images. This functionality was originally added to support
    the :attr:`.HistogramSeries.showOverlay` functionality - it adds a mask
    image to the :class:`.OverlayList` to display the histogram range.
    Sub-classes may wish to adhere to the same logic (replacing ``ProxyImage``
    instances with their bases)


    **Control panels**


    The :class:`.PlotControlPanel`, :class:`.PlotListPanel`, and
    :class:`.OverlayListPanel` are *FSLeyes control* panels which work with
    the :class:`.OverlayPlotPanel`. The ``PlotControlPanel`` is not intended
    to be used directly - plot-specific sub-classes are used instead. The
    following actions can be used to toggle control panels on an
    ``OverlayPlotPanel``:

    .. autosummary::
       :nosignatures:

       toggleOverlayList
       togglePlotList


    **Sub-classes**


    The ``OverlayPlotPanel`` is the base class for:

    .. autosummary::
       :nosignatures:

       ~fsleyes.views.timeseriespanel.TimeSeriesPanel
       ~fsleyes.views.histogrampanel.HistogramPanel
       ~fsleyes.views.powerspectrumpanel.PowerSpectrumPanel
    """


    plotColours = {}
    """This dictionary is used to store a collection of ``{overlay : colour}``
    mappings. It is shared across all ``OverlayPlotPanel`` instances, so that
    the same (initial) colour is used for the same overlay, across multiple
    plots.

    Sub-classes should use the :meth:`getOverlayPlotColour` method to retrieve
    the initial colour to use for a given overlay.
    """


    def __init__(self, *args, **kwargs):
        """Create an ``OverlayPlotPanel``.

        :arg initialState: Must be passed as a keyword argument. Allows you to
                           specify the initial enabled/disabled state for each
                           overlay. See :meth:`updateDataSeries`. If not
                           provided, only the data series for the currently
                           selected overlay is shown (if possible).

        All other argumenst are passed through to :meth:`PlotPanel.__init__`.
        """

        initialState = kwargs.pop('initialState', None)

        PlotPanel.__init__(self, *args, **kwargs)

        self.__name = 'OverlayPlotPanel_{}'.format(self._name)

        # The dataSeries attribute is a dictionary of
        #
        #   {overlay : DataSeries}
        #
        # mappings, containing a DataSeries instance for
        # each compatible overlay in the overlay list.
        #
        # Different DataSeries types need to be re-drawn
        # when different properties change. For example,
        # a VoxelTimeSeries instance needs to be redrawn
        # when the DisplayContext.location property
        # changes, whereas a MelodicTimeSeries instance
        # needs to be redrawn when the VolumeOpts.volume
        # property changes.
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
        #
        # See the createDataSeries method for more
        # information.
        self.__dataSeries   = {}
        self.__refreshProps = {}

        self             .addListener('dataSeries',
                                      self.__name,
                                      self.__dataSeriesChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self.__name,
                                      self.__selectedOverlayChanged)
        self._overlayList.addListener('overlays',
                                      self.__name,
                                      self.__overlayListChanged)

        self.__overlayListChanged(initialState=initialState)
        self.__dataSeriesChanged()


    def destroy(self):
        """Must be called when this ``OverlayPlotPanel`` is no longer needed.
        Removes some property listeners, and calls :meth:`PlotPanel.destroy`.
        """
        self._overlayList.removeListener('overlays',        self.__name)
        self._displayCtx .removeListener('selectedOverlay', self.__name)
        self             .removeListener('dataSeries',      self.__name)

        for overlay in list(self.__dataSeries.keys()):
            self.clearDataSeries(overlay)

        self.__dataSeries   = None
        self.__refreshProps = None

        PlotPanel.destroy(self)


    def getDataSeriesToPlot(self):
        """Convenience method which returns a list of overlays which have
        :class:`.DataSeries` that should be plotted.
        """

        overlays = self._overlayList[:]

        # Display.enabled
        overlays = [o for o in overlays
                    if self._displayCtx.getDisplay(o).enabled]

        # Replace proxy images
        overlays = [o.getBase() if isinstance(o, fsloverlay.ProxyImage)
                    else o for o in overlays]

        # Have data series
        dss = [self.getDataSeries(o) for o in overlays]
        dss = [ds for ds in dss if ds is not None]

        # Remove duplicates
        unique = []
        for ds in dss:
            if ds not in unique:
                unique.append(ds)

        return unique


    def getDataSeries(self, overlay):
        """Returns the :class:`.DataSeries` instance associated with the
        specified overlay, or ``None`` if there is no ``DataSeries`` instance.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        return self.__dataSeries.get(overlay)


    def getOverlayPlotColour(self, overlay):
        """Returns an initial colour to use for plots associated with the
        given overlay. If a colour is present in the  :attr:`plotColours`
        dictionary, it is returned. Otherwise a random colour is generated,
        added to ``plotColours``, and returned.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        colour = self.plotColours.get(overlay)

        if colour is None:
            colour = fslcm.randomDarkColour()
            self.plotColours[overlay] = colour

        return colour


    @actions.action
    def addDataSeries(self):
        """Every :class:`.DataSeries` which is currently plotted, and has not
        been added to the :attr:`PlotPanel.dataSeries` list, is added to said
        list.
        """

        # Get all the DataSeries objects which
        # have been drawn, and are not in the
        # dataSeries list.
        toAdd = self.getDrawnDataSeries()
        toAdd = [d[0] for d in toAdd if d[0] not in self.dataSeries]

        if len(toAdd) == 0:
            return

        # Replace each DataSeries instance with a copy.
        # This is necessary because some DataSeries
        # sub-classes have complicated behaviour (e.g.
        # changing their data when some properties
        # change). But we just want to 'freeze' the
        # data as it is currently shown. So we create
        # a dumb copy.
        for i, ds  in enumerate(toAdd):

            copy           = plotting.DataSeries(ds.overlay)
            toAdd[i]       = copy

            copy.alpha     = ds.alpha
            copy.lineWidth = ds.lineWidth
            copy.lineStyle = ds.lineStyle
            copy.label     = ds.label
            copy.colour    = ds.colour

            # We have to re-generate the data,
            # because the x/y data returned by
            # the getDrawnDataSeries method
            # above may have had post-processing
            # applied to it (e.g. smoothing)
            xdata, ydata = self.prepareDataSeries(ds)

            copy.setData(xdata, ydata)

            # This is disgraceful. It wasn't too bad
            # when this function was defined in the
            # PlotListPanel class, but is a horrendous
            # hack now that it is defined here in the
            # PlotPanel class.
            #
            # At some stage I will remove this offensive
            # code, and figure out a more robust system
            # for appending this metadata to DataSeries
            # instances.
            #
            # When the user selects a data series in
            # the list, we want to change the selected
            # overlay/location/volume/etc to the
            # properties associated with the data series.
            # So here we're adding some attributes to
            # each data series instance so that the
            # PlotListPanel.__onListSelect method can
            # update the display properties.
            opts = self._displayCtx.getOpts(ds.overlay)
            if isinstance(ds, (plotting.MelodicTimeSeries,
                               plotting.MelodicPowerSpectrumSeries)):
                copy._volume = opts.volume

            elif isinstance(ds, (plotting.VoxelTimeSeries,
                                 plotting.VoxelPowerSpectrumSeries)):
                copy._location = opts.getVoxel()

        self.dataSeries.extend(toAdd)


    @actions.action
    def removeDataSeries(self, *a):
        """Removes the most recently added :class:`.DataSeries` from this
        ``OverlayPlotPanel``.
        """
        if len(self.dataSeries) > 0:
            self.dataSeries.pop()


    def createDataSeries(self, overlay):
        """This method must be implemented by sub-classes. It must create and
        return a :class:`.DataSeries` instance for the specified overlay.


        .. note:: Sub-class implementations should set the
                  :attr:`.DataSeries.colour` property to that returned by
                  the :meth:`getOverlayPlotColour` method.


        Different ``DataSeries`` types need to be re-drawn when different
        properties change. For example, a :class:`.VoxelTimeSeries`` instance
        needs to be redrawn when the :attr:`.DisplayContext.location` property
        changes, whereas a :class:`.MelodicTimeSeries` instance needs to be
        redrawn when the :attr:`.VolumeOpts.volume` property changes.

        Therefore, in addition to creating and returning a ``DataSeries``
        instance for the given overlay, sub-class implementations must also
        specify the properties which affect the state of the ``DataSeries``
        instance. These must be specified as two lists:

         - the *targets* list, a list of objects which own the dependant
           properties (e.g. the :class:`.DisplayContext` or
           :class:`.VolumeOpts` instance).

         - The *properties* list, a list of names, each specifying the
           property on the corresponding target.

        This method must therefore return a tuple containing:

          - A :class:`.DataSeries` instance, or ``None`` if the overlay
            is incompatible.
          - A list of *target* instances.
          - A list of *property names*.

        The target and property name lists must have the same length.
        """
        raise NotImplementedError('createDataSeries must be '
                                  'implemented by sub-classes')


    def clearDataSeries(self, overlay):
        """Destroys the internally cached :class:`.DataSeries` for the given
        overlay.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        ds                 = self.__dataSeries  .pop(overlay, None)
        targets, propNames = self.__refreshProps.pop(overlay, ([], []))

        if ds is not None:

            log.debug('Destroying {} for {}'.format(
                type(ds).__name__, overlay))

            for propName in ds.redrawProperties():
                ds.removeListener(propName, self.__name)
            ds.destroy()

        for t, p in zip(targets, propNames):
            try:    t.removeListener(p, self.__name)
            except: pass


    def updateDataSeries(self, initialState=None):
        """Makes sure that a :class:`.DataSeries` instance has been created
        for every compatible overlay, and that property listeners are
        correctly registered, so the plot can be refreshed when needed.

        :arg initialState: If provided, must be a ``dict`` of ``{ overlay :
                           bool }`` mappings, specifying the initial value
                           of the :attr:`.DataSeries.enabled` property for
                           newly created instances. If not provided, only
                           the data series for the currently selected
                           overlay (if it has been newly added) is initially
                           enabled.
        """

        # Default to showing the
        # currently selected overlay
        if initialState is None:
            if len(self._overlayList) > 0:
                initialState = {self._displayCtx.getSelectedOverlay() : True}
            else:
                initialState = {}

        # Make sure that a DataSeries
        # exists for every compatible overlay
        newOverlays = []
        for ovl in self._overlayList:

            if ovl in self.__dataSeries:
                continue

            if isinstance(ovl, fsloverlay.ProxyImage):
                continue

            ds, refreshTargets, refreshProps = self.createDataSeries(ovl)
            display                          = self._displayCtx.getDisplay(ovl)

            if ds is None:

                # "Disable" overlays which don't have any data
                # to plot. We do this mostly so the overlay
                # appears greyed out in the OverlayListPanel.
                self._displayCtx.getDisplay(ovl).enabled = False
                continue

            # Display.enabled == DataSeries.enabled
            ds.bindProps('enabled', display)

            ds.enabled = initialState.get(ovl, False)

            log.debug('Created {} for overlay {} (enabled: {})'.format(
                type(ds).__name__, ovl, ds.enabled))

            newOverlays.append(ovl)

            self.__dataSeries[  ovl] = ds
            self.__refreshProps[ovl] = (refreshTargets, refreshProps)

        # Make sure that property listeners are
        # registered all of these overlays
        for overlay in newOverlays:

            targets, propNames = self.__refreshProps.get(overlay, (None, None))

            if targets is None:
                continue

            ds = self.__dataSeries[overlay]

            for propName in ds.redrawProperties():
                ds.addListener(propName,
                               self.__name,
                               self.asyncDraw,
                               overwrite=True)

            for target, propName in zip(targets, propNames):

                log.debug('Adding listener on {}.{} for {} data '
                          'series'.format(type(target).__name__,
                                          propName,
                                          overlay))

                target.addListener(propName,
                                   self.__name,
                                   self.asyncDraw,
                                   overwrite=True)


    @actions.toggleControlAction(overlaylistpanel.OverlayListPanel)
    def toggleOverlayList(self):
        """Shows/hides an :class:`.OverlayListPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """

        # Tell the overlay list panel to disable
        # all overlays that aren't being plotted.
        #
        # This OverlayPlotPanel will always be
        # notified about a new overlay before
        # this OverlayListPanel, so a DataSeries
        # instance will always have been created
        # by the time the list panel calls this
        # filter function.
        def listFilter(overlay):
            return self.getDataSeries(overlay) is not None

        self.togglePanel(overlaylistpanel.OverlayListPanel,
                         showVis=True,
                         showSave=False,
                         showGroup=False,
                         propagateSelect=False,
                         elistboxStyle=(elistbox.ELB_REVERSE      |
                                        elistbox.ELB_TOOLTIP_DOWN |
                                        elistbox.ELB_NO_ADD       |
                                        elistbox.ELB_NO_REMOVE    |
                                        elistbox.ELB_NO_MOVE),
                         location=wx.LEFT,
                         filterFunc=listFilter)


    @actions.toggleControlAction(plotlistpanel.PlotListPanel)
    def togglePlotList(self, floatPane=False):
        """Shows/hides a :class:`.PlotListPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(plotlistpanel.PlotListPanel,
                         self,
                         location=wx.LEFT,
                         floatPane=floatPane)


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`dataSeries` list changes. Enables/disables
        the :meth:`removeDataSeries` action accordingly.
        """
        self.removeDataSeries.enabled = len(self.dataSeries) > 0


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.

        If a :class:`.DataSeries` instance for the newly selected overlay
        exists, and is not currently enabled, it is enabled.
        """

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        ds = self.getDataSeries(overlay)

        if ds is not None and not ds.enabled:
            ds.enabled = True
        else:
            self.asyncDraw()


    def __overlayListChanged(self, *a, **kwa):
        """Called when the :class:`.OverlayList` changes. Makes sure that
        there are no :class:`.DataSeries` instances in the
        :attr:`.PlotPanel.dataSeries` list, or in the internal cache, which
        refer to overlays that no longer exist.

        :arg initialState: Must be passed as a keyword argument. If provided,
                           passed through to the :meth:`updateDataSeries`
                           method.
        """

        initialState = kwa.get('initialState', None)

        for ds in list(self.dataSeries):
            if ds.overlay is not None and ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
                ds.destroy()

        for overlay in list(self.__dataSeries.keys()):
            if overlay not in self._overlayList:
                self.clearDataSeries(overlay)

        for overlay in self._overlayList:
            display = self._displayCtx.getDisplay(overlay)

            # PlotPanels use the Display.enabled property
            # to toggle on/off overlay plots. We don't want
            # this to interfere with CanvasPanels, which
            # use Display.enabled to toggle on/off overlays.
            display.unsyncFromParent('enabled')

        self.updateDataSeries(initialState=initialState)
        self.asyncDraw()
