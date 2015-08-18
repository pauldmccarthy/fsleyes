#!/usr/bin/env python
#
# plotpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import matplotlib        as mpl
import numpy             as np
import scipy.interpolate as interp


mpl.use('WxAgg')


import matplotlib.pyplot as plt

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wx    import NavigationToolbar2Wx
from mpl_toolkits.mplot3d              import Axes3D

import                     props
import                     viewpanel
import fsl.data.strings as strings


log = logging.getLogger(__name__)


class DataSeries(props.HasProperties):

    colour    = props.Colour()
    alpha     = props.Real(minval=0.0, maxval=1.0, default=1.0, clamped=True)
    label     = props.String()
    lineWidth = props.Choice((0.5, 1, 2, 3, 4, 5))
    lineStyle = props.Choice(
        *zip(*[('-',  'Solid line'),
               ('--', 'Dashed line'),
               ('-.', 'Dash-dot line'),
               (':',  'Dotted line')]))

    
    def __init__(self, overlay):
        self.overlay = overlay


    def __copy__(self):
        return type(self)(self.overlay)


    def getData(self):
        raise NotImplementedError('The getData method must be '
                                  'implemented by subclasses')


class PlotPanel(viewpanel.ViewPanel):
    """A ``PlotPanel`` instance adds a listener to every one of its properties,
    using :attr:`FSLEyesPanel._name` as the listener name.

    Therefore, If ``PlotPanel`` subclasses add a listener to any of their
    properties, they should use ``overwrite=True``, and should ensure that the
    custom listener calls the :meth:`draw` method.
    """


    dataSeries = props.List()
    legend     = props.Boolean(default=True)
    autoScale  = props.Boolean(default=True)
    xLogScale  = props.Boolean(default=False)
    yLogScale  = props.Boolean(default=False) 
    ticks      = props.Boolean(default=True)
    grid       = props.Boolean(default=True)
    smooth     = props.Boolean(default=False)
    xlabel     = props.String()
    ylabel     = props.String()
    limits     = props.Bounds(ndims=2)


    def importDataSeries(self, *a):
        # TODO import data series from text file
        pass


    def exportDataSeries(self, *a):
        # TODO export all displayed data series to text file
        pass
    
    
    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 actionz=None,
                 proj=None,
                 interactive=True):
        
        if actionz is None:
            actionz = {}

        actionz = dict([('screenshot', self.screenshot)] + actionz.items())
        
        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = plt.Figure()
        axis   = figure.add_subplot(111, projection=proj)
        canvas = Canvas(self, -1, figure) 

        self.setCentrePanel(canvas)

        self.__figure = figure
        self.__axis   = axis
        self.__canvas = canvas

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
                         'smooth',
                         'xlabel',
                         'ylabel']:
            self.addListener(propName, self._name, self.draw)
            
        # custom listeners for a couple of properties
        self.__name = '{}_{}'.format(self._name, id(self))        
        self.addListener('dataSeries',
                         self.__name,
                         self.__dataSeriesChanged)
        self.addListener('limits',
                         self.__name,
                         self.__limitsChanged)

        self.Bind(wx.EVT_SIZE, lambda *a: self.draw())


    def draw(self, *a):
        raise NotImplementedError('The draw method must be '
                                  'implemented by PlotPanel subclasses')


    def __dataSeriesChanged(self, *a):
        for ds in self.dataSeries:
            ds.addGlobalListener(self._name, self.draw, overwrite=True)
        self.draw()

        
    def destroy(self):
        self.removeListener('dataSeries', self.__name)
        self.removeListener('limits',     self.__name)
        for propName in ['legend',
                         'autoScale',
                         'xLogScale',
                         'yLogScale',
                         'ticks',
                         'grid',
                         'smooth',
                         'xlabel',
                         'ylabel']:
            self.removeListener(propName, self._name)
        viewpanel.ViewPanel.destroy(self)


    def getFigure(self):
        return self.__figure
    

    def getAxis(self):
        return self.__axis


    def getCanvas(self):
        return self.__canvas

    
    def __onMouseDown(self, ev):
        self.__mouseDown  = True

        
    def __onMouseUp(self, ev):
        self.__mouseUp  = False

        
    def __onMouseMove(self, ev):

        if not self.__mouseDown:
            return

        xlims = list(self.__axis.get_xlim())
        ylims = list(self.__axis.get_ylim())

        self.disableListener('limits', self.__name)
        self.limits.x = xlims
        self.limits.y = ylims
        self.enableListener( 'limits', self.__name)


    def __limitsChanged(self, *a):

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


    def drawDataSeries(self, extraSeries=None, **plotArgs):

        if extraSeries is None:
            extraSeries = []

        axis          = self.getAxis()
        canvas        = self.getCanvas()
        width, height = canvas.get_width_height()

        # Before clearing/redrawing, save
        # a copy of the x/y axis limits -
        # the user may have changed them
        # via panning/zooming, and we may
        # want to preserve the limits that
        # the user set
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
            xlim, ylim = self.__drawOneDataSeries(ds, **plotArgs)
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

        axis.grid(self.grid)

        canvas.draw()
        self.Refresh()


    def __drawOneDataSeries(self, ds, **plotArgs):

        if ds.alpha == 0:
            return (0, 0), (0, 0)

        log.debug('Drawing plot for {}'.format(ds.overlay))

        xdata, ydata = ds.getData()

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

    
    def screenshot(self, *a):

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


    def message(self, msg):

        axis = self.getAxis()
        axis.clear()
        axis.set_xlim((0.0, 1.0))
        axis.set_ylim((0.0, 1.0))

        if isinstance(axis, Axes3D):
            axis.text(0.5, 0.5, 0.5, msg, ha='center', va='center')
        else:
            axis.text(0.5, 0.5, msg, ha='center', va='center')
        
        self.getCanvas().draw()
        self.Refresh() 
