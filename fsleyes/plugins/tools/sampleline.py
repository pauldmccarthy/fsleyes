#!/usr/bin/env python
#
# sampleline.py - The SampleLineAction
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SampleLineAction` class, which allows
the user to open a :class:`SampleLinePanel`. The ``SampleLinePanel`` is
a FSLeyes control which allows the user to draw a line on the canvases of
an :class:`.OrthoPanel`, and plot the data along that line from the currently
selected :class:`.Image` overlay.
"""

import                  os
import                  copy

import numpy         as np
import scipy.ndimage as ndimage
import                  wx

import fsl.data.image                             as fslimage
import fsl.utils.settings                         as fslsettings
import fsl.transform.affine                       as affine
import fsleyes_widgets.widgetlist                 as widgetlist
import fsleyes_widgets.utils.status               as status
import fsleyes_props                              as props
import fsleyes.strings                            as strings
import fsleyes.tooltips                           as tooltips
import fsleyes.icons                              as fslicons
import fsleyes.actions                            as actions
import fsleyes.actions.screenshot                 as screenshot
import fsleyes.views.orthopanel                   as orthopanel
import fsleyes.controls.controlpanel              as ctrlpanel
import fsleyes.plotting                           as plotting
import fsleyes.plotting.plotcanvas                as plotcanvas
import fsleyes.plugins.profiles.samplelineprofile as samplelineprofile


class SampleLineAction(actions.ToggleControlPanelAction):
    """The ``SampleLineAction`` simply shows/hides a :class:`SampleLinePanel`.
    """


    @staticmethod
    def supportedViews():
        """The ``SampleLineAction`` is restricted for use with
        :class:`.OrthoPanel` views.
        """
        return [orthopanel.OrthoPanel]


    def __init__(self, overlayList, displayCtx, ortho):
        """Create a  ``SampleLineAction``. """
        super().__init__(overlayList, displayCtx, ortho, SampleLinePanel)

        self.__ortho = ortho
        self.__name  = '{}_{}'.format(type(self).__name__, id(self))

        displayCtx.addListener('selectedOverlay', self.__name,
                               self.__selectedOverlayChanged)


    def destroy(self):
        """Called when the :class:`.OrthoPanel` that owns this action is
        closed. Clears references, removes listeners, and calls the base
        class ``destroy`` method.
        """
        if self.destroyed:
            return

        self.__ortho = None
        self.displayCtx.removeListener('selectedOverlay', self.__name)
        super().destroy()


    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay changes. Enables/disables this
        action (and hence the bound Tools menu item) depending on whether the
        overlay is an image.
        """
        ovl = self.displayCtx.getSelectedOverlay()
        self.enabled = isinstance(ovl, fslimage.Image)


    def __run(self):
        """Open/close a :class:`SampleLinePanel`. """
        self.viewPanel.togglePanel(SampleLinePanel)


class SampleLineDataSeries(plotting.DataSeries):
    """The ``SampleLineDataSeries`` represents data that is sampled along
    a straight line through a 3D volume from an :class:`.Image` overlay.

    ``SampleLineDataSeries`` objects are created by the
    :class:`SampleLinePanel`.
    """


    interp = props.Choice((0, 1, 2, 3), default=0)
    """How to interpolate the sampled data when it is plotted. The value is
    used directly as the ``order`` parameter to the
    ``scipy.ndimage.map_coordinates`` function.
    """


    resolution = props.Int(minval=2, maxval=200, default=100, clamped=False)
    """The number of points (uniformly spaced) to sample along the line. """


    normalise = props.Choice(('none', 'y', 'x', 'xy'))
    """Whether to normalise all plotted data along the x, or y, or both, axes.
    """


    def __init__(self,
                 overlay,
                 overlayList,
                 displayCtx,
                 plotCanvas,
                 index,
                 start,
                 end):
        """Create a ``SampleLineDataSeries``.

        :arg overlay:     The :class:`.Image` overlay to sample from
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  A :class:`.DisplayContext` instance
        :arg plotCanvas:  The :class:`.PlotCanvas` that is plotting this
                          ``DataSeries``.
        :arg index:       Volume index, for images with more than 3
                          dimensions (see :meth:`.NiftiOpts.index`)
        :arg start:       Start of sampling line, in voxel coordinates
        :arg end:         End of sampling line, in voxel coordinates
        """

        plotting.DataSeries.__init__(
            self, overlay, overlayList, displayCtx, plotCanvas)

        self.__index  = index
        self.__start  = start
        self.__end    = end
        self.__coords = None

        self.addListener('resolution', self.name, self.__refreshData)
        self.addListener('interp',     self.name, self.__refreshData)
        self.addListener('normalise',  self.name, self.__refreshData)

        self.label = ('{}: [{:.2f} {:.2f} {:.2f}] -> '
                      '[{:.2f} {:.2f} {:.2f}]'.format(
                          overlay.name, *start, *end))


    @property
    def coords(self):
        """Return a ``(3, n)`` array containing the voxel coordinates of
        each sampled point for the most recently generated data, or ``None``
        if no data has been sampled yet.
        """
        return self.__coords


    def __refreshData(self, *a):
        """Called when :attr:`resolution`, :attr:`interp` or :attr:`normalise`
        change. Re-samples the data from the image.
        """

        resolution   = self.resolution
        order        = self.interp
        normalisex   = 'x' in self.normalise
        normalisey   = 'y' in self.normalise
        opts         = self.displayCtx.getOpts(self.overlay)
        data         = self.overlay[self.__index]
        start        = self.__start
        end          = self.__end

        coords       = np.zeros((3, resolution))
        coords[0, :] = np.linspace(start[0], end[0], resolution)
        coords[1, :] = np.linspace(start[1], end[1], resolution)
        coords[2, :] = np.linspace(start[2], end[2], resolution)

        y = ndimage.map_coordinates(data, coords, order=order,
                                    output=np.float64)

        if normalisey:
            y = (y - y.min()) / (y.max() - y.min())

        if normalisex:
            xmax = 1
        else:
            wstart = opts.transformCoords(start, 'voxel', 'world')
            wend   = opts.transformCoords(end,   'voxel', 'world')
            xmax   = affine.veclength(wstart - wend)[0]

        x = np.linspace(0, xmax, resolution)

        self.__coords = coords
        self.setData(x, y)


class SampleLinePanel(ctrlpanel.ControlPanel):
    """The ``SampleLinePanel`` is a FSLeyes control which can be used in
    conjunction with an :class:`.OrthoPanel` view. It allows the user to draw
    a line on an ``OrthoPanel`` canvas, and plot the voxel intensities, along
    that line, from the currently selected :class:`.Image` overlay.

    The :class:`.SampleLineProfile` class implements user interaction, and the
    :class:`.PlotCanvas` class is used for plotting.
    """


    # Used to synchronise between GUI widgets
    # and SampleLineDataSeries property values
    # The GUI widgets are bound to the most
    # recently added SampleLineDataSeries
    # instance
    interp     = copy.copy(SampleLineDataSeries.interp)
    resolution = copy.copy(SampleLineDataSeries.resolution)
    normalise  = copy.copy(SampleLineDataSeries.normalise)
    colour     = copy.copy(plotting.DataSeries.colour)
    lineWidth  = copy.copy(plotting.DataSeries.lineWidth)
    lineStyle  = copy.copy(plotting.DataSeries.lineStyle)


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``SampleLinePanel`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        return [orthopanel.OrthoPanel]


    @staticmethod
    def ignoreControl():
        """Tells FSLeyes not to add the ``SampleLinePanel`` as an option to
        the Settings menu. Instead, the :class:`SampleLineAction` is added as
        an option to the Tools menu.
        """
        return True


    @staticmethod
    def profileCls():
        """Returns the :class:`.SampleLineProfile` class, which needs to be
        activated in conjunction with the ``SampleLinePanel``.
        """
        return samplelineprofile.SampleLineProfile


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'floatPane' : True,
                'floatOnly' : True}


    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create a ``SampleLinePanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, ortho)

        profile = ortho.currentProfile

        # plot which displays the sampled data
        canvas = plotcanvas.PlotCanvas(self, drawFunc=self.__draw)
        canvas.canvas.SetMinSize((-1, 150))

        self.__ortho   = ortho
        self.__profile = profile
        self.__canvas  = canvas
        self.__current = None

        # initial settings
        self.colour    = '#000050'
        self.lineWidth = 2
        canvas.legend  = False

        # Controls which allow the user to select
        # interpolation/resolution, line colour, etc
        widgets = widgetlist.WidgetList(self)
        legend = props.makeWidget(
            widgets, canvas, 'legend',
            labels=strings.properties['PlotCanvas.legend'])

        interp = props.makeWidget(
            widgets, self, 'interp', labels=strings.choices[self, 'interp'])
        resolution = props.makeWidget(
            widgets, self, 'resolution', slider=True, spin=True,
            showLimits=False)
        normalise = props.makeWidget(
            widgets, self, 'normalise',
            labels=strings.choices[self, 'normalise'])

        colour    = props.makeWidget(widgets, self, 'colour')
        lineWidth = props.makeWidget(widgets, self, 'lineWidth')
        lineStyle = props.makeWidget(
            widgets, self, 'lineStyle',
            labels=strings.choices['DataSeries.lineStyle'])

        widgets.AddWidget(legend,     strings.labels[self, 'legend'])
        widgets.AddWidget(interp,     strings.labels[self, 'interp'])
        widgets.AddWidget(resolution, strings.labels[self, 'resolution'])
        widgets.AddWidget(normalise,  strings.labels[self, 'normalise'])
        widgets.AddWidget(colour,     strings.labels[self, 'colour'])
        widgets.AddWidget(lineWidth,  strings.labels[self, 'lineWidth'])
        widgets.AddWidget(lineStyle,  strings.labels[self, 'lineStyle'])

        # Controls allowing the user to add/remove
        # sample lines from the plot to save the
        # data to a file, and to save a screenshot
        # of the plot
        ctrlSizer  = wx.BoxSizer(wx.HORIZONTAL)
        screenshot = actions.ActionButton(
            'screenshot',
            icon=fslicons.findImageFile('camera24'),
            tooltip=tooltips.actions['PlotPanel.screenshot'])
        export = actions.ActionButton(
            'export',
            icon=fslicons.findImageFile('exportDataSeries24'),
            tooltip=tooltips.actions['PlotPanel.exportDataSeries'])
        add = actions.ActionButton(
            'addDataSeries',
            icon=fslicons.findImageFile('add24'),
            tooltip=tooltips.actions[self, 'addDataSeries'])
        remove = actions.ActionButton(
            'removeDataSeries',
            icon=fslicons.findImageFile('remove24'),
            tooltip=tooltips.actions[self, 'removeDataSeries'])

        screenshot = props.buildGUI(self, self, screenshot)
        export     = props.buildGUI(self, self, export)
        add        = props.buildGUI(self, self, add)
        remove     = props.buildGUI(self, self, remove)

        ctrlSizer.Add(screenshot, flag=wx.EXPAND)
        ctrlSizer.Add(export,     flag=wx.EXPAND)
        ctrlSizer.Add(add,        flag=wx.EXPAND)
        ctrlSizer.Add(remove,     flag=wx.EXPAND)

        # Labels which show the start and end
        # coordinates of the sample line in voxel
        # ("v") and world ("w") coordinates, and
        # the line length in [units] (probably mm)
        vfromlbl = wx.StaticText(self)
        vtolbl   = wx.StaticText(self)
        wfromlbl = wx.StaticText(self)
        wtolbl   = wx.StaticText(self)
        vfromval = wx.StaticText(self)
        vtoval   = wx.StaticText(self)
        wfromval = wx.StaticText(self)
        wtoval   = wx.StaticText(self)
        lenlbl   = wx.StaticText(self)
        lenval   = wx.StaticText(self)

        self.__vfromval = vfromval
        self.__vtoval   = vtoval
        self.__wfromval = wfromval
        self.__wtoval   = wtoval
        self.__lenval   = lenval

        vfromlbl.SetLabel(strings.labels[self, 'voxelfrom'])
        vtolbl  .SetLabel(strings.labels[self, 'voxelto'])
        wfromlbl.SetLabel(strings.labels[self, 'worldfrom'])
        wtolbl  .SetLabel(strings.labels[self, 'worldto'])
        lenlbl  .SetLabel(strings.labels[self, 'length'])

        infoSizer = wx.FlexGridSizer(3, 4, 5, 5)
        infoSizer.AddGrowableCol(1)
        infoSizer.AddGrowableCol(3)
        infoSizer.Add(vfromlbl)
        infoSizer.Add(vfromval)
        infoSizer.Add(vtolbl)
        infoSizer.Add(vtoval)
        infoSizer.Add(wfromlbl)
        infoSizer.Add(wfromval)
        infoSizer.Add(wtolbl)
        infoSizer.Add(wtoval)
        infoSizer.Add(lenlbl)
        infoSizer.Add(lenval)
        infoSizer.Add((1, 1))
        infoSizer.Add((1, 1))

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(ctrlSizer,     flag=wx.EXPAND)
        mainSizer.Add(widgets,       flag=wx.EXPAND)
        mainSizer.Add(infoSizer,     flag=wx.EXPAND)
        mainSizer.Add(canvas.canvas, flag=wx.EXPAND, proportion=1)

        self.SetSizer(mainSizer)
        self.Layout()

        profile.registerHandler('LeftMouseDown', self.name, self.__onMouseDown)
        profile.registerHandler('LeftMouseDrag', self.name, self.__onMouseDrag)
        profile.registerHandler('LeftMouseUp',   self.name, self.__onMouseUp)

        self.addListener('interp',     self.name, canvas.asyncDraw)
        self.addListener('resolution', self.name, canvas.asyncDraw)
        self.addListener('normalise',  self.name, canvas.asyncDraw)
        self.addListener('colour',     self.name, canvas.asyncDraw)
        self.addListener('lineWidth',  self.name, canvas.asyncDraw)
        self.addListener('lineStyle',  self.name, canvas.asyncDraw)


    def destroy(self):
        """Called when this ``SampleLinePanel`` is no longer needed. Clears
        references, and calls :meth:`.ControlPanel.destroy`.
        """
        super().destroy()
        self.__canvas.destroy()
        self.__ortho   = None
        self.__profile = None
        self.__canvas  = None
        self.__current = None


    @property
    def canvas(self):
        """Return a reference to the :class:`.PlotCanvas` that is used to
        plot sampled data from lines that the user has drawn.
        """
        return self.__canvas


    @actions.action
    def addDataSeries(self):
        """Holds/persists the most recently sampled line to the plot. """
        if self.__current is not None:
            self.__canvas.dataSeries.append(self.__current)
            self.__bindToDataSeries(self.__current, False)
            self.__current = None


    @actions.action
    def removeDataSeries(self):
        """Removes the most recently held/persisted line from the plot. """
        canvas = self.__canvas
        if len(canvas.dataSeries) > 0:
            canvas.dataSeries.pop()


    @actions.action
    def export(self):
        """Prompts the user to save the sampled data to a file. """

        # only one series can be saved - the
        # user is asked to select which one
        if self.__current is None: series = []
        else:                      series = [self.__current]

        series.extend(reversed(self.__canvas.dataSeries))

        if len(series) == 0:
            return

        # ask what series, and whether they
        # want coordinates of sample points
        parent = self.GetParent()
        dlg    = ExportSampledDataDialog(parent, series)
        if dlg.ShowModal() != wx.ID_OK:
            return

        series     = dlg.GetSeries()
        saveCoords = dlg.GetCoordinates()

        # ask where to save the file
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        msg     = strings.titles[self, 'savefile']
        dlg     = wx.FileDialog(parent,
                                message=msg,
                                defaultDir=fromDir,
                                defaultFile='sample.txt',
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filename = dlg.GetPath()

        # prepare the data
        if saveCoords == 'none':
            data = series.getData()[1]
        else:
            image      = series.overlay
            opts       = self.displayCtx.getOpts(image)
            samples    = series.getData()[1]
            coords     = series.coords.T
            data       = np.zeros((len(samples), 4))
            data[:, 0] = samples

            if saveCoords == 'voxel':
                data[:, 1:] = coords
            else:
                data[:, 1:] = opts.transformCoords(coords, 'voxel', 'world')

        # save the file
        errTitle = strings.titles[  self, 'exportError']
        errMsg   = strings.messages[self, 'exportError']
        with status.reportIfError(errTitle, errMsg):
            np.savetxt(filename, data, fmt='%0.8f')


    @actions.action
    def screenshot(self):
        """Creates and runs a :class:`.ScreenshotAction`, which propmts the
        user to save the plot to a file.
        """
        screenshot.ScreenshotAction(self.overlayList,
                                    self.displayCtx,
                                    self.__canvas)()


    def __bindToDataSeries(self, ds, bind=True):
        """Binds/unbinds the GUI widgets (:attr:`colour`, :attr:`resolution`),
        etc to/from the given :class:`SampleLineDataSeries` instance.
        """
        ds.bindProps('colour',     self, unbind=not bind)
        ds.bindProps('lineWidth',  self, unbind=not bind)
        ds.bindProps('lineStyle',  self, unbind=not bind)
        ds.bindProps('resolution', self, unbind=not bind)
        ds.bindProps('interp',     self, unbind=not bind)
        ds.bindProps('normalise',  self, unbind=not bind)


    def __updateInfo(self):
        """Called while the mouse is being dragged. Updates the information
        about the sampling line (e.g. start/end voxel coordinates) that is
        displayed at the top of the ``SampleLinePanel``.
        """
        start = self.__profile.sampleStart
        end   = self.__profile.sampleEnd
        if start is None or end is None:
            self.__vfromval.SetLabel('')
            self.__vtoval  .SetLabel('')
            self.__wfromval.SetLabel('')
            self.__wtoval  .SetLabel('')
            self.__lenval  .SetLabel('')
            return

        overlay = self.displayCtx.getSelectedOverlay()
        opts    = self.displayCtx.getOpts(overlay)
        image   = opts.referenceImage

        # display world and voxel coordinates
        if image is not None:
            opts   = self.displayCtx.getOpts(image)
            units  = image.xyzUnits
            units  = strings.nifti.get(('xyz_unit', units), '(unknown units)')
            ws     = opts.transformCoords(start, 'display', 'world')
            we     = opts.transformCoords(end,   'display', 'world')
            vs     = opts.transformCoords(start, 'display', 'voxel')
            ve     = opts.transformCoords(end,   'display', 'voxel')
            length = affine.veclength(ws - we)[0]

            vs     = '[{:.2f}, {:.2f}, {:.2f}]'.format(*vs)
            ve     = '[{:.2f}, {:.2f}, {:.2f}]'.format(*ve)
            ws     = '[{:.2f}, {:.2f}, {:.2f}]'.format(*ws)
            we     = '[{:.2f}, {:.2f}, {:.2f}]'.format(*we)
            length = f'{length:.2f} {units}'

            self.__vfromval.SetLabel(vs)
            self.__vtoval  .SetLabel(ve)
            self.__wfromval.SetLabel(ws)
            self.__wtoval  .SetLabel(we)
            self.__lenval  .SetLabel(length)


    def __onMouseDown(self, *a):
        """Called on mouse down events on an :class:`.OrthoPanel` canvas.
        Calls :meth:`__updateInfo`.
        """
        self.__updateInfo()


    def __onMouseDrag(self, *a):
        """Called on mouse drag events on an :class:`.OrthoPanel` canvas.
        Calls :meth:`__updateInfo`.
        """
        self.__updateInfo()


    def __onMouseUp(self, *a):
        """Called on mouse up events on an :class:`.OrthoPanel` canvas.
        Samples and plots data from the currently selected overlay along
        the drawn sample line.
        """

        start  = self.__profile.sampleStart
        end    = self.__profile.sampleEnd
        image  = self.displayCtx.getSelectedOverlay()

        if start is None or end is None:
            return

        if image is None or not isinstance(image, fslimage.Image):
            return

        if self.__current is not None:
            self.__bindToDataSeries(self.__current, False)

        # Round to avoid floating point imprecision
        opts   = self.displayCtx.getOpts(image)
        vstart = opts.transformCoords(start, 'display', 'voxel').round(6)
        vend   = opts.transformCoords(end,   'display', 'voxel').round(6)

        series = SampleLineDataSeries(image,
                                      self.overlayList,
                                      self.displayCtx,
                                      self.__canvas,
                                      opts.index(),
                                      vstart,
                                      vend)

        self.__bindToDataSeries(series)
        self.__current = series
        self.__canvas.asyncDraw()


    def __draw(self):
        """Passed as the ``drawFunc`` to the :class:`.PlotCanvas`. Calls
        :meth:`.PlotCanvas.drawDataSeries`.
        """
        if self.__current is None: extras = None
        else:                      extras = [self.__current]
        self.__canvas.drawDataSeries(extraSeries=extras, refresh=True)


class ExportSampledDataDialog(wx.Dialog):
    """The ``ExportSampledDataDialog`` is used by the
    :meth:`SampleLinePanel.export` method to ask the user which sample data
    they want to save, and whether they want to save the sample point
    coordinates to file as well as the samples themselves.
    """


    def __init__(self, parent, series):
        """Create an ``ExportSampledDataDialog``.

        :arg parent: ``wx`` parent object
        :arg series: Sequence of ``SampleLineDataSeries`` instances. Must
                     contain at least one series. If there is more than one
                     series, the user is asked to choose one.
        """
        title        = strings.titles[self]
        coords       = strings.choices[self, 'saveCoordinates']
        seriesLabels = [s.label for s in series]
        coordsLabels = list(coords.values())
        coords       = list(coords.keys())

        wx.Dialog.__init__(self,
                           parent,
                           title=title,
                           style=wx.DEFAULT_DIALOG_STYLE)

        self.__series       = series
        self.__coords       = coords
        self.__coordsChoice = wx.Choice(self, choices=coordsLabels)
        self.__coordsChoice.SetSelection(0)

        coordsLabel = wx.StaticText(self)
        ok          = wx.Button(self, id=wx.ID_OK)
        cancel      = wx.Button(self, id=wx.ID_CANCEL)

        coordsLabel.SetLabel(strings.labels[self, 'coords'])
        ok         .SetLabel(strings.labels[self, 'ok'])
        cancel     .SetLabel(strings.labels[self, 'cancel'])

        if len(series) > 1:
            self.__seriesChoice = wx.Choice(self, choices=seriesLabels)
            self.__seriesChoice.SetSelection(0)
            seriesLabel = wx.StaticText(self)
            seriesLabel.SetLabel(strings.labels[self, 'series'])

        ok.SetDefault()
        ok    .Bind(wx.EVT_BUTTON, self.__onOk)
        cancel.Bind(wx.EVT_BUTTON, self.__onCancel)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer   = wx.BoxSizer(wx.VERTICAL)

        buttonSizer.Add((10, 10), proportion=1)
        buttonSizer.Add(ok)
        buttonSizer.Add((10, 10))
        buttonSizer.Add(cancel)
        buttonSizer.Add((10, 10), proportion=1)

        mainSizer.Add((10, 10), proportion=1)

        if len(series) > 1:
            mainSizer.Add(seriesLabel,
                          flag=wx.ALIGN_CENTRE | wx.ALL, border=10)
            mainSizer.Add((10, 10))
            mainSizer.Add(self.__seriesChoice,
                          flag=wx.ALIGN_CENTRE | wx.ALL, border=10)
            mainSizer.Add((10, 10))

        mainSizer.Add(coordsLabel, flag=wx.ALIGN_CENTRE | wx.ALL, border=10)
        mainSizer.Add((10, 10))
        mainSizer.Add(self.__coordsChoice,
                      flag=wx.ALIGN_CENTRE | wx.ALL, border=10)
        mainSizer.Add((10, 10), proportion=1)
        mainSizer.Add(buttonSizer, flag=wx.ALIGN_CENTRE | wx.ALL, border=10)
        mainSizer.Add((10, 10))

        self.SetSizer(mainSizer)
        self.Layout()
        self.Fit()
        self.CentreOnParent()


    def __onOk(self, ev):
        """Called when the ok button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the cancel button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_CANCEL)


    def GetCoordinates(self):
        """Return one of ``'none'``, ``'voxel'``, or ``'world'``, denoting
        the user's preference for saving coordinates to the file.
        """
        idx = self.__coordsChoice.GetSelection()
        return self.__coords[idx]


    def GetSeries(self):
        """Return the :class:`.SampleLineDataSeries` that was selected."""
        if len(self.__series) == 1:
            return self.__series[0]
        idx = self.__seriesChoice.GetSelection()
        return self.__series[idx]
