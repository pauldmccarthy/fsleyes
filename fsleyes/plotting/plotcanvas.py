#!/usr/bin/env python
#
# plotcanvas.py - The PlotCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PlotCanvas` class, which plots
:class:`.DataSeries` instances on a ``matplotlib`` canvas. The ``PlotCanvas``
is used by the :class:`.TimeSeriesPanel`, :class:`.HistogramPanel`, and
:class:`.PowerSpectrumPanel` views, and potentially by other FSLeyes control
panels.
"""


import logging
import collections

import numpy                             as np
import scipy.interpolate                 as interp
import matplotlib.pyplot                 as plt
import matplotlib.backends.backend_wxagg as wxagg

import fsl.utils.idle                    as idle
import fsleyes_props                     as props
import fsleyes_widgets                   as fwidgets

import fsleyes.strings                   as strings


log = logging.getLogger(__name__)


class PlotCanvas(props.HasProperties):
    """The ``PlotCanvas`` can be used to plot :class:`.DataSeries` instances
    onto a ``matplotlib`` ``FigureCanvasWxAgg`` canvas.

    The ``PlotCanvas`` is used by all *FSLeyes views* which display some sort
    of 2D data plot, such as the :class:`.TimeSeriesPanel`, and the
    :class:`.HistogramPanel`.

    The ``PlotCanvas`` uses :mod:`matplotlib` for its plotting. The
    ``matplotlib`` ``Figure``, ``Axis``, and ``Canvas`` instances can be
    accessed via the :meth:`figure`, :meth:`axis`, and :meth:`canvas` methods,
    if they are needed. Various display settings can be configured through
    ``PlotCanvas`` properties, including :attr:`legend`, :attr:`smooth`, etc.


    **Basic usage**

    After you have created a ``PlotCanvas``, you can add :class:`.DataSeries`
    instances to the :attr:`dataSeries` property, then call :meth:`draw` or
    :meth:`asyncDraw`.

    The :meth:`draw` method simply calls :meth:`drawDataSeries` and
    :meth:`drawArtists`, so you can alternately call those methods directly,
    or pass your own  ``drawFunc`` when creating a ``PlotCanvas``.

    The ``PlotCanvas`` itself is not a ``wx`` object, so cannot be displayed -
    the ``matplotilb Canvas`` object, accessible through the :meth:`canvas`
    method, is what you should add to a ``wx`` parent object.


    **Data series**

    A ``PlotCanvas`` instance plots data contained in one or more
    :class:`.DataSeries` instances; all ``DataSeries`` classes are defined in
    the :mod:`.plotting` sub-package.

    ``DataSeries`` objects can be plotted by passing them to the
    :meth:`drawDataSeries` method.

    Or, if you want one or more ``DataSeries`` to be *held*, i.e. plotted
    every time, you can add them to the :attr:`dataSeries` list. The
    ``DataSeries`` in the :attr:`dataSeries` list will be plotted on every
    call to :meth:`drawDataSeries` (in addition to any ``DataSeries`` passed
    directly to :meth:`drawDataSeries`) until they are removed from the
    :attr:`dataSeries` list.


    **The draw queue**


    The ``PlotCanvas`` uses a :class:`.async.TaskThread` to asynchronously
    extract and prepare data for plotting, This is because data preparation
    may take a long time for certain types of ``DataSeries``
    (e.g. :class:`TimeSeries` which are retrieving data from large
    :class:`.Image` overlays), and the main application thread should not be
    blocked while this is occurring. The ``TaskThread`` instance is accessible
    through the :meth:`getDrawQueue` method, in case anything needs to be
    scheduled on it.
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


    invertX = props.Boolean(default=False)
    """Invert the plot along the X axis. """


    invertY = props.Boolean(default=False)
    """Invert the plot along the Y axis. """


    xScale = props.Real(default=1)
    """Scale to apply to the X axis data. """


    yScale = props.Real(default=1)
    """Scale to apply to the Y axis data. """


    xOffset = props.Real(default=0)
    """Offset to apply to the X axis data. """


    yOffset = props.Real(default=0)
    """Offset to apply to the Y axis data. """


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


    showPreparingMessage = props.Boolean(default=True)
    """Show a message on the canvas whilst data is being prepared for plotting.
    """


    def __init__(self,
                 parent,
                 drawFunc=None,
                 prepareFunc=None):
        """Create a ``PlotCanvas``.

        :arg parent:      The :mod:`wx` parent object.
        :arg drawFunc:    Custon function to call instead of :meth:`draw`.
        :arg prepareFunc: Custom function to call instead of
                          :meth:`prepareDataSeries`.
        """

        figure = plt.Figure()
        axis   = figure.add_subplot(111)
        canvas = wxagg.FigureCanvasWxAgg(parent, -1, figure)

        figure.subplots_adjust(top=1.0, bottom=0.0, left=0.0, right=1.0)
        figure.patch.set_visible(False)

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__figure      = figure
        self.__axis        = axis
        self.__canvas      = canvas
        self.__prepareFunc = prepareFunc
        self.__drawFunc    = drawFunc
        self.__destroyed   = False

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
        self.__drawQueue = idle.TaskThread()
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
                         'invertX',
                         'invertY',
                         'xScale',
                         'yScale',
                         'xOffset',
                         'yOffset',
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


    def destroy(self):
        """Removes some property listeners, and clears references to all
        :class:`.DataSeries`, ``matplotlib`` and ``wx`` objects.
        """

        for propName in ['dataSeries',
                         'artists',
                         'limits',
                         'legend',
                         'xAutoScale',
                         'yAutoScale',
                         'xLogScale',
                         'yLogScale',
                         'invertX',
                         'invertY',
                         'xScale',
                         'yScale',
                         'xOffset',
                         'yOffset',
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

        self.__drawQueue.stop()
        self.__drawQueue       = None
        self.__drawnDataSeries = None
        self.dataSeries        = []
        self.artists           = []
        self.__figure          = None
        self.__axis            = None
        self.__destroyed       = True


    @property
    def destroyed(self):
        """Returns True if :meth:`destroy` has been called, ``False``
        otherwise.
        """
        return self.__destroyed


    @property
    def figure(self):
        """Returns the ``matplotlib`` ``Figure`` instance."""
        return self.__figure

    @property
    def axis(self):
        """Returns the ``matplotlib`` ``Axis`` instance."""
        return self.__axis


    @property
    def canvas(self):
        """Returns the ``matplotlib`` ``Canvas`` instance."""
        return self.__canvas


    def getDrawQueue(self):
        """Returns the :class`.idle.TaskThread` instance used for data
        preparation.
        """
        return self.__drawQueue


    def draw(self, *a):
        """Call :meth:`drawDataSeries` and then :meth:`drawArtists`.
        Or, if a ``drawFunc`` was provided, calls that instead.

        You will generally want to call :meth:`asyncDraw` instead of this
        method.
        """
        if self.destroyed:
            return

        if self.__drawFunc:
            self.__drawFunc(*a)
        else:
            self.drawDataSeries()
            self.drawArtists()


    def asyncDraw(self, *a):
        """Schedules :meth:`draw` to be run asynchronously. This method
        should be used in preference to calling :meth:`draw` directly
        in most cases, particularly where the call occurs within a
        property callback function.

        This method is automatically called called whenever a
        :class:`.DataSeries` is added to the :attr:`dataSeries` list, or when
        any plot display properties change.
        """

        # don't run the task if it's
        # already scheduled on the idle loop
        idleName = '{}.draw'.format(id(self))
        if not self.destroyed and not idle.idleLoop.inIdle(idleName):
            idle.idle(self.draw, name=idleName)


    def message(self, msg, clear=True, border=False):
        """Displays the given message in the centre of the figure.

        This is a convenience method provided for use by subclasses.
        """

        axis = self.axis

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

        self.canvas.draw()


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
        (but **not** applied to :class:`.DataSeries` that have been added to
        the :attr:`dataSeries` list).

        This implementation just returns :class:`.DataSeries.getData` - you
        can pass a ``prepareFunc`` to ``__init__`` to perform any custom
        preprocessing.
        """
        if self.__prepareFunc:
            return self.__prepareFunc(ds)
        else:
            return ds.getData()


    def drawArtists(self, refresh=True, immediate=False):
        """Draw all ``matplotlib.Artist`` instances in the :attr:`artists`
        list, then refresh the canvas.

        :arg refresh: If ``True`` (default), the canvas is refreshed.
        """

        axis   = self.axis
        canvas = self.canvas

        def realDraw():

            # Just in case this PlotPanel is destroyed
            # before this task gets executed
            if not fwidgets.isalive(self.__canvas):
                return

            for artist in self.artists:
                if artist not in axis.findobj(type(artist)):
                    axis.add_artist(artist)

        if immediate: realDraw()
        else:         self.__drawQueue.enqueue(idle.idle, realDraw)

        def refreshCanvas():
            if not self.destroyed:
                canvas.draw()

        if refresh:
            if immediate: refreshCanvas()
            else:         self.__drawQueue.enqueue(idle.idle, refreshCanvas)


    def drawDataSeries(self, extraSeries=None, refresh=False, **plotArgs):
        """Queues a request to plot all of the :class:`.DataSeries` instances
        in the :attr:`dataSeries` list.

        This method does not do the actual plotting - it is performed
        asynchronously, to avoid locking up the GUI:

         1. The data for each ``DataSeries`` instance is prepared on
            separate threads (using :func:`.idle.run`).

         2. A call to :func:`.idle.wait` is enqueued on a
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

        canvas      = self.canvas
        axis        = self.axis
        toPlot      = self.dataSeries[:]

        toPlot      = [ds for ds in toPlot      if ds.enabled]
        extraSeries = [ds for ds in extraSeries if ds.enabled]

        toPlot      = extraSeries + toPlot
        preprocs    = [True] * len(extraSeries) + [False] * len(toPlot)

        if len(toPlot) == 0:
            self.__drawnDataSeries.clear()
            axis.clear()
            canvas.draw()
            return

        # Before clearing/redrawing, save
        # a copy of the x/y axis limits -
        # the user may have changed them
        # via panning/zooming and, if
        # autoLimit is off, we will want
        # to preserve the limits that the
        # user set. These are passed to
        # the __drawDataSeries method.
        #
        # Make sure the limits are ordered
        # as (min, max), as they won't be
        # if invertX/invertY are active.
        axxlim = list(sorted(self.limits.x))
        axylim = list(sorted(self.limits.y))

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
        tasks = [idle.run(t) for t in tasks]

        # Show a message while we're
        # preparing the data.
        if self.showPreparingMessage:
            self.message(strings.messages[self, 'preparingData'],
                         clear=False,
                         border=True)

        # Wait until data preparation is
        # done, then call __drawDataSeries.
        self.__drawRequests += 1
        self.__drawQueue.enqueue(idle.wait,
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

        # Avoid spursious post-destruction
        # notifications (occur sporadically
        # during testing)
        if self.destroyed:
            return

        # Only draw the plot if there are no
        # pending draw requests. Otherwise
        # we would be drawing out-of-date data.
        self.__drawRequests -= 1
        if self.__drawRequests != 0:
            return

        axis          = self.axis
        canvas        = self.canvas
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

            xdata      = self.xOffset + self.xScale * xdata
            ydata      = self.yOffset + self.yScale * ydata
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
            axis.tick_params(axis='both', which='both', length=3)

            for ytl in axis.yaxis.get_ticklabels():
                ytl.set_horizontalalignment('left')

            for xtl in axis.xaxis.get_ticklabels():
                xtl.set_verticalalignment('bottom')
        else:

            # we clear the labels, but
            # leave the ticks, so the
            # axis grid gets drawn
            xlabels = ['' for i in range(len(axis.xaxis.get_ticklabels()))]
            ylabels = ['' for i in range(len(axis.yaxis.get_ticklabels()))]

            axis.set_xticklabels(xlabels)
            axis.set_yticklabels(ylabels)
            axis.tick_params(axis='both', which='both', length=0)

        # Limits
        if xmin != xmax:
            if self.invertX: axis.set_xlim((xmax, xmin))
            else:            axis.set_xlim((xmin, xmax))
            if self.invertY: axis.set_ylim((ymax, ymin))
            else:            axis.set_ylim((ymin, ymax))

        # legend
        labels = [ds.label for ds in dataSeries if ds.label is not None]
        if len(labels) > 0 and self.legend:
            handles, labels = axis.get_legend_handles_labels()
            legend          = axis.legend(
                handles,
                labels,
                loc='upper right',
                fontsize=10,
                handlelength=3,
                fancybox=True)
            legend.get_frame().set_alpha(0.6)

        if self.grid:
            axis.grid(linestyle='-',
                      color=self.gridColour,
                      linewidth=0.5,
                      zorder=0)
        else:
            axis.grid(False)

        axis.spines['right'] .set_visible(False)
        axis.spines['left']  .set_visible(False)
        axis.spines['top']   .set_visible(False)
        axis.spines['bottom'].set_visible(False)

        axis.set_axisbelow(True)
        axis.patch.set_facecolor(self.bgColour)
        self.figure.patch.set_alpha(0)

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

        xdata = np.asarray(xdata, dtype=float)
        ydata = np.asarray(ydata, dtype=float)

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

        axis = self.axis
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

        axis = self.axis
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
