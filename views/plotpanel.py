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

import wx

import matplotlib        as mpl
import numpy             as np
import scipy.interpolate as interp


mpl.use('WxAgg')


import matplotlib.pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wx    import NavigationToolbar2Wx

import                     props
import                     viewpanel
import fsl.data.strings as strings


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

      4. If necessary, override the :meth:`destroy` method, but make
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


    **Plot panel actions**

    A number of actions are also provided by the ``PlotPanel`` class:

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

    
    legend = props.Boolean(default=True)
    """If ``True``, a legend is added to the plot, with an entry for every
    ``DataSeries`` instance in the :attr:`dataSeries` list.
    """

    
    autoScale = props.Boolean(default=True)
    """If ``True``, the plot :attr:`limits` are automatically updated to
    fit all plotted data.
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
    """The x/y axis limits. If :attr:`autoScale` is ``True``, these limit
    values are automatically updated on every call to :meth:`drawDataSeries`.
    """

    
    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 actionz=None,
                 interactive=True):
        """Create a ``PlotPanel``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: An :class:`.OverlayList` instance.
        
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        
        :arg actionz:     A dictionary of ``{ name : function }``
                          mappings, containing actions implemented by
                          the sub-class.

        :arg interactive: If ``True`` (the default), the canvas is configured
                          so the user can pan/zoom the plot with the mouse.
        """
        
        if actionz is None:
            actionz = {}

        actionz = dict([('screenshot', self.screenshot)] + actionz.items())
        
        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = plt.Figure()
        axis   = figure.add_subplot(111)
        canvas = Canvas(self, -1, figure)

        figure.subplots_adjust(top=1.0, bottom=0.0, left=0.0, right=1.0)
        figure.patch.set_visible(False)
        
        self.setCentrePanel(canvas)

        self.__figure = figure
        self.__axis   = axis
        self.__canvas = canvas
        self.__name   = 'OverlayPlotPanel_{}'.format(self._name)

        if interactive:
            
            # Pan/zoom functionality is implemented
            # by the NavigationToolbar2Wx, but the
            # toolbar is not actually shown.
            self.__mouseDown = False
            self.__toolbar = NavigationToolbar2Wx(canvas)
            self.__toolbar.Show(False)
            self.__toolbar.pan()
            
            canvas.mpl_connect('button_press_event',   self.__onMouseDown)
            canvas.mpl_connect('motion_notify_event',  self.__onMouseMove)
            canvas.mpl_connect('button_release_event', self.__onMouseUp)
            canvas.mpl_connect('axes_leave_event',     self.__onMouseUp)

        # Redraw whenever any property changes, 
        for propName in ['legend',
                         'autoScale',
                         'xLogScale',
                         'yLogScale',
                         'ticks',
                         'grid',
                         'gridColour',
                         'bgColour',
                         'smooth',
                         'xlabel',
                         'ylabel']:
            self.addListener(propName, self.__name, self.draw)
            
        # custom listeners for a couple of properties
        self.addListener('dataSeries',
                         self.__name,
                         self.__dataSeriesChanged)
        self.addListener('limits',
                         self.__name,
                         self.__limitsChanged)

        self.Bind(wx.EVT_SIZE, self.draw)


    def getFigure(self):
        """Returns the ``matplotlib`` ``Figure`` instance."""
        return self.__figure
    

    def getAxis(self):
        """Returns the ``matplotlib`` ``Axis`` instance."""
        return self.__axis


    def getCanvas(self):
        """Returns the ``matplotlib`` ``Canvas`` instance."""
        return self.__canvas


    def draw(self, *a):
        """This method must be overridden by ``PlotPanel`` sub-classes.

        It is called whenever a :class:`.DataSeries` is added to the
        :attr:`dataSeries` list, or when any plot display properties change.

        Sub-class implementations should call the :meth:`drawDataSeries`
        method.
        """
        raise NotImplementedError('The draw method must be '
                                  'implemented by PlotPanel subclasses')

        
    def destroy(self):
        """Removes some property listeners, and then calls
        :meth:`.ViewPanel.destroy`.
        """
        self.removeListener('dataSeries', self.__name)
        self.removeListener('limits',     self.__name)
        
        for propName in ['legend',
                         'autoScale',
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
            ds.removeGlobalListener(self.__name, self.draw)

        self.dataSeries = []
            
        viewpanel.ViewPanel.destroy(self)

    
    def screenshot(self, *a):
        """Prompts the user  to select a file name, then saves a screenshot
        of the current plot.
        """

        formats  = self.__canvas.get_supported_filetypes().items()

        wildcard = ['{}|*.{}'.format(desc, fmt) for fmt, desc in formats]
        wildcard = '|'.join(wildcard)

        dlg = wx.FileDialog(self,
                            message=strings.messages[self, 'screenshot'],
                            wildcard=wildcard,
                            style=wx.FD_SAVE)

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


    def importDataSeries(self, *a):
        """Not implemented yet. Imports data series from a text file."""
        pass


    def exportDataSeries(self, *a):
        """Not implemented yet. Exports displayed data series to a text file.
        """
        pass
            

    def message(self, msg):
        """Displays the given message in the centre of the figure.

        This is a convenience method provided for use by subclasses.
        """

        axis = self.getAxis()
        axis.clear()
        axis.set_xlim((0.0, 1.0))
        axis.set_ylim((0.0, 1.0))

        axis.text(0.5, 0.5, msg, ha='center', va='center')
        
        self.getCanvas().draw()
        self.Refresh()


    def drawDataSeries(self, extraSeries=None, preproc=None, **plotArgs):
        """Plots all of the :class:`.DataSeries` instances in the
        :attr:`dataSeries` list

        :arg extraSeries: A sequence of additional ``DataSeries`` to be
                          plotted.

        :arg preproc:     An optional preprocessing function - passed to the
                          :meth:`__drawOneDataSeries` method.

        :arg plotArgs:    Passed through to the :meth:`__drawOneDataSeries`
                          method.
        """

        if extraSeries is None:
            extraSeries = []

        axis          = self.getAxis()
        canvas        = self.getCanvas()
        width, height = canvas.get_width_height()

        # Before clearing/redrawing, save
        # a copy of the x/y axis limits -
        # the user may have changed them
        # via panning/zooming and, if
        # autoLimit is off, we will want
        # to preserve the limits that the
        # user set.
        axxlim = axis.get_xlim()
        axylim = axis.get_ylim()

        axis.clear()

        toPlot = self.dataSeries[:]
        toPlot = extraSeries + toPlot

        if len(toPlot) == 0:
            canvas.draw()
            self.Refresh()
            return

        xlims = []
        ylims = []

        for ds in toPlot:
            xlim, ylim = self.__drawOneDataSeries(ds, preproc, **plotArgs)
            xlims.append(xlim)
            ylims.append(ylim)

        (xmin, xmax), (ymin, ymax) = self.__calcLimits(
            xlims, ylims, axxlim, axylim, width, height)

        if xmax - xmin < 0.0000000001 or \
           ymax - ymin < 0.0000000001:
            axis.clear()
            canvas.draw()
            self.Refresh()
            return

        # x/y axis labels
        xlabel = self.xlabel 
        ylabel = self.ylabel

        if xlabel is None: xlabel = ''
        if ylabel is None: ylabel = ''

        xlabel = xlabel.strip()
        ylabel = ylabel.strip()

        if xlabel != '':
            axis.set_xlabel(self.xlabel, va='bottom')
            axis.xaxis.set_label_coords(0.5, 10.0 / height)
            
        if ylabel != '':
            axis.set_ylabel(self.ylabel, va='top')
            axis.yaxis.set_label_coords(10.0 / width, 0.5)

        # Ticks
        if self.ticks:
            axis.tick_params(direction='in', pad=-5)

            for ytl in axis.yaxis.get_ticklabels():
                ytl.set_horizontalalignment('left')
                
            for xtl in axis.xaxis.get_ticklabels():
                xtl.set_verticalalignment('bottom')
        else:
            axis.set_xticks([])
            axis.set_yticks([])

        # Limits
        axis.set_xlim((xmin, xmax))
        axis.set_ylim((ymin, ymax))

        # legend
        labels = [ds.label for ds in toPlot if ds.label is not None]
        if len(labels) > 0 and self.legend:
            handles, labels = axis.get_legend_handles_labels()
            legend          = axis.legend(
                handles,
                labels,
                loc='upper right',
                fontsize=12,
                fancybox=True)
            legend.get_frame().set_alpha(0.6)

        if self.grid:
            axis.grid(linestyle='-',
                      color=self.gridColour,
                      linewidth=2,
                      zorder=0)
        else:
            axis.grid(False)

        axis.set_axisbelow(True)
        axis.patch.set_facecolor(self.bgColour)
        self.getFigure().patch.set_alpha(0)
            
        canvas.draw()
        self.Refresh()

        
    def __drawOneDataSeries(self, ds, preproc=None, **plotArgs):
        """Plots a single :class:`.DataSeries` instance. This method is called
        by the :meth:`drawDataSeries` method.

        :arg ds:       The ``DataSeries`` instance.

        :arg preproc:  An optional preprocessing function which must accept
                       the ``DataSeries`` instance as its sole argument, and
                       must return the ``(xdata, ydata)`` with any required
                       processing applied.  The default preprocessing function
                       returns the result of a call to
                       :meth:`.DataSeries.getData`.

        :arg plotArgs: May be used to customise the plot - these
                       arguments are all passed through to the
                       ``Axis.plot`` function.
        """
        
        if preproc is None:
            preproc = lambda s: s.getData()

        if ds.alpha == 0:
            return (0, 0), (0, 0)

        log.debug('Drawing {} for {}'.format(type(ds).__name__,
                                             ds.overlay))

        xdata, ydata = preproc(ds)

        if len(xdata) != len(ydata) or len(xdata) == 0:
            return (0, 0), (0, 0)

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

        axis.plot(xdata, ydata, **kwargs)

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

    
    def __onMouseDown(self, ev):
        """Sets a flag so the :meth:`__onMouseMove` method knows that the
        mouse is down.
        """
        self.__mouseDown = True

        
    def __onMouseUp(self, ev):
        """Sets a flag so the :meth:`__onMouseMove` method knows that the
        mouse is up.
        """ 
        self.__mouseDown = False

        
    def __onMouseMove(self, ev):
        """If this ``PlotPanel`` is interactive (determined by the
        ``interactive`` parameter to :meth:`__init__`), mouse drags will
        change the axis limits.

        This behaviour is provided by ``matplotlib`` - this method simply
        makes sure that the :attr:`limits` property is up to date.
        """

        if not self.__mouseDown:
            return

        xlims = list(self.__axis.get_xlim())
        ylims = list(self.__axis.get_ylim())

        self.disableListener('limits', self.__name)
        self.limits.x = xlims
        self.limits.y = ylims
        self.enableListener( 'limits', self.__name)


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`dataSeries` list changes. Adds listeners
        to any new :class:`.DataSeries` instances, and then calls :meth:`draw`.
        """
        
        for ds in self.dataSeries:
            ds.addGlobalListener(self.__name, self.draw, overwrite=True)
        self.draw()


    def __limitsChanged(self, *a):
        """Called when the :attr:`limits` change. Updates the axis limits
        accordingly.
        """

        axis = self.getAxis()
        axis.set_xlim(self.limits.x)
        axis.set_ylim(self.limits.y)
        self.draw()

        
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

        If :attr:`autoScale` is enabled, the limits are calculated from the
        data range, using the canvas width and height to maintain consistent
        padding around the plotted data, irrespective of the canvas size.

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

        if self.autoScale:

            xmin = min([lim[0] for lim in dataxlims])
            xmax = max([lim[1] for lim in dataxlims])
            ymin = min([lim[0] for lim in dataylims])
            ymax = max([lim[1] for lim in dataylims])

            bPad = (ymax - ymin) * (50.0 / axHeight)
            tPad = (ymax - ymin) * (50.0 / axHeight)
            lPad = (xmax - xmin) * (50.0 / axWidth)
            rPad = (xmax - xmin) * (50.0 / axWidth)

            xmin = xmin - lPad
            xmax = xmax + rPad
            ymin = ymin - bPad
            ymax = ymax + tPad 
            
        else:
            xmin = axisxlims[0]
            xmax = axisxlims[1]
            ymin = axisylims[0]
            ymax = axisylims[1]

        self.disableListener('limits', self.__name)
        self.limits[:] = [xmin, xmax, ymin, ymax]
        self.enableListener('limits', self.__name)            
 
        return (xmin, xmax), (ymin, ymax)


class OverlayPlotPanel(PlotPanel):
    """The ``OverlayPlotPanel`` is a :class:`.PlotPanel` which contains
    some extra logic for creating and storing :class:`.DataSeries`
    instances for each overlay in the :class:`.OverlayList`.


    **Subclass requirements**

    Sub-classes must:

     1. Implement the :meth:`createDataSeries` method, so it creates a
        :class:`.DataSeries` instance for a specified overlay.

     2. Implement the :meth:`PlotPanel.draw` method so it honours the
        current value of the :attr:`showMode` property.

    
    **The internal data series store**


    The ``OverlayPlotPanel`` maintains a store of :class:`.DataSeries`
    instances, one for each compatible overlay. The ``OverlayPlotPanel``
    manages the property listeners that must be registered with each of these
    ``DataSeries`` to refresh the plot.  These instances are created by the
    :meth:`createDataSeries` method, which is implemented by sub-classes. The
    following methods are available to sub-classes, for managing the internal
    store of :class:`.DataSeries` instances:

    .. autosummary::
       :nosignatures:

       getDataSeries
       clearDataSeries
       updateDataSeries

    
    **The current data series**

    
    By default, the ``OverlayPlotPanel`` plots the data series associated with
    the currently selected overlay, which is determined from the
    :attr:`.DisplayContext.selectedOverlay`. This data series is referred to
    as the *current* data series. The :attr:`showMode` property allows the
    user to choose between showing only the current data series, showing the
    data series for all (compatible) overlays, or only showing the data series
    that have been added to the :attr:`.PlotPanel.dataSeries` list.  Other
    data series can be *held* by adding them to the
    :attr:`.PlotPanel.dataSeries` list.


    **Control panels**


    The :class:`.PlotControlPanel` and :class:`.PlotListPanel` are *FSLeyes
    control* panels which work with the :class:`.OverlayPlotPanel`.

    
    The ``OverlayPlotPanel`` is the base class for:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.views.timeseriespanel.TimeSeriesPanel
       ~fsl.fsleyes.views.histogrampanel.HistogramPanel
       ~fsl.fsleyes.views.powerspectrumpanel.PowerSpectrumPanel
    """

    
    showMode = props.Choice(('current', 'all', 'none'))
    """Defines which data series to plot.

    =========== =====================================================
    ``current`` The data series for the currently selected overlay is
                plotted.
    ``all``     The data series for all compatible overlays in the
                :class:`.OverlayList` are plotted.
    ``none``    Only the ``DataSeries`` that are in the
                :attr:`.PlotPanel.dataSeries` list will be plotted.
    =========== =====================================================
    """ 


    def __init__(self, *args, **kwargs):
        """Create an ``OverlayPlotPanel``. All argumenst are passed through to 
        :meth:`PlotPanel.__init__`.
        """

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
        #
        # See the createDataSeries method for more
        # information.
        self.__dataSeries   = {}
        self.__refreshProps = {}

        self             .addListener('showMode',
                                      self.__name,
                                      self.draw)
        self._displayCtx .addListener('selectedOverlay',
                                      self.__name,
                                      self.draw)
        self._overlayList.addListener('overlays',
                                      self.__name,
                                      self.__overlayListChanged)
        
        self.updateDataSeries()


    def destroy(self):
        """Must be called when this ``OverlayPlotPanel`` is no longer needed.
        Removes some property listeners, and calls :meth:`PlotPanel.destroy`.
        """
        self             .removeListener('showMode',        self.__name)
        self._overlayList.removeListener('overlays',        self.__name)
        self._displayCtx .removeListener('selectedOverlay', self.__name)
        PlotPanel.destroy(self)
        

    def getDataSeries(self, overlay):
        """Returns the :class:`.DataSeries` instance associated with the
        specified overlay, or ``None`` if there is no ``DataSeries`` instance.
        """
        return self.__dataSeries.get(overlay)
 

    def createDataSeries(self, overlay):
        """This method must be implemented by sub-classes. It must create and
        return a :class:`.DataSeries` instance for the specified overlay.

        Different ``DataSeries`` types need to be re-drawn when different
        properties change. For example, a :class:`.TimeSeries`` instance needs
        to be redrawn when the :attr:`.DisplayContext.location` property
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
         * A list of *property names*.
        
        The target and property name lists must have the same length.
        """
        raise NotImplementedError('createDataSeries must be '
                                  'implemented by sub-classes')

    
    def clearDataSeries(self, overlay):
        """Destroys the internally cached :class:`.DataSeries` for the given
        overlay.
        """
        
        ts                 = self.__dataSeries  .pop(overlay, None)
        targets, propNames = self.__refreshProps.pop(overlay, ([], []))

        if ts is not None:
            ts.destroy()

        for t, p in zip(targets, propNames):
            t.removeListener(p, self.__name)

        
    def updateDataSeries(self):
        """Makes sure that a :class:`.DataSeries` instance has been created
        for every compatible overlay, and that property listeners are
        correctly registered, so the plot can be refreshed when needed.
        """
        
        for ovl in self._overlayList:
            if ovl not in self.__dataSeries:
                
                ds, refreshTargets, refreshProps = self.createDataSeries(ovl)

                if ds is None:
                    continue

                self.__dataSeries[  ovl] = ds
                self.__refreshProps[ovl] = (refreshTargets, refreshProps)
                
                ds.addGlobalListener(self.__name, self.draw, overwrite=True)
        
        for targets, propNames in self.__refreshProps.values():
            for target, propName in zip(targets, propNames):
                target.addListener(propName,
                                   self.__name,
                                   self.draw,
                                   overwrite=True) 


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Makes sure that
        there are no :class:`.DataSeries` instances in the
        :attr:`.PlotPanel.dataSeries` list, or in the internal cache, which
        refer to overlays that no longer exist.

        Also calls :meth:`updateDataSeries`, whic ensures that a
        :class:`.DataSeries` instance for every compatible overlay is cached
        internally.
        """

        for ds in list(self.dataSeries):
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
                ds.destroy()
        
        for overlay in list(self.__dataSeries.keys()):
            if overlay not in self._overlayList:
                self.clearDataSeries(overlay)

        self.updateDataSeries()
        self.draw()
