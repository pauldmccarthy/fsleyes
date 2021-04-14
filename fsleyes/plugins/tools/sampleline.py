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


import numpy         as np
import scipy.ndimage as ndimage
import                  wx

import fsl.data.image                             as fslimage
import fsleyes_props                              as props
import fsleyes.strings                            as strings
import fsleyes.actions                            as actions
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
        super().__init__(overlayList, displayCtx, SampleLinePanel, ortho)

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


class SampleLinePanel(ctrlpanel.ControlPanel):
    """The ``SampleLinePanel`` is a FSLeyes control which can be used in
    conjunction with an :class:`.OrthoPanel` view. It allows the user to draw
    a line on an ``OrthoPanel`` canvas, and plot the voxel intensities, along
    that line, from the currently selected :class:`.Image` overlay.

    The :class:`.SampleLineProfile` class implements user interaction, and the
    :class:`.PlotCanvas` class is used for plotting.
    """


    interp = props.Int(minval=0, maxval=5, default=1, clamped=True)
    """How to interpolate the sampled data when it is plotted. The value is
    used directly as the ``order`` parameter to the
    ``scipy.ndimage.map_coordinates`` function.
    """


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

        self.__ortho   = ortho
        self.__profile = profile
        self.__ds      = None

        # Labels which show the start and end
        # coordinates of the sample line in voxel
        # ("v") and world ("w") coordinates, and
        # the line length in [units] (probably mm)
        self.__vfromlbl = wx.StaticText(self)
        self.__vtolbl   = wx.StaticText(self)
        self.__wfromlbl = wx.StaticText(self)
        self.__wtolbl   = wx.StaticText(self)
        self.__vfromval = wx.StaticText(self)
        self.__vtoval   = wx.StaticText(self)
        self.__wfromval = wx.StaticText(self)
        self.__wtoval   = wx.StaticText(self)
        self.__lenlbl   = wx.StaticText(self)
        self.__lenval   = wx.StaticText(self)

        self.__vfromlbl.SetLabel(strings.labels[self, 'voxelfrom'])
        self.__vtolbl  .SetLabel(strings.labels[self, 'voxelto'])
        self.__wfromlbl.SetLabel(strings.labels[self, 'worldfrom'])
        self.__wtolbl  .SetLabel(strings.labels[self, 'worldto'])
        self.__lenlbl  .SetLabel(strings.labels[self, 'length'])

        self.__infoSizer = wx.FlexGridSizer(3, 4, 5, 5)
        self.__infoSizer.AddGrowableCol(1)
        self.__infoSizer.AddGrowableCol(3)
        self.__infoSizer.Add(self.__vfromlbl)
        self.__infoSizer.Add(self.__vfromval)
        self.__infoSizer.Add(self.__vtolbl)
        self.__infoSizer.Add(self.__vtoval)
        self.__infoSizer.Add(self.__wfromlbl)
        self.__infoSizer.Add(self.__wfromval)
        self.__infoSizer.Add(self.__wtolbl)
        self.__infoSizer.Add(self.__wtoval)
        self.__infoSizer.Add(self.__lenlbl)
        self.__infoSizer.Add(self.__lenval)
        self.__infoSizer.Add((1, 1))
        self.__infoSizer.Add((1, 1))

        # Controls which allow the user to select
        # interpolation, to save the data to a file,
        # and to save a screenshot of the plot
        # todo

        # plot which displays the sampled data
        self.__canvas = plotcanvas.PlotCanvas(self, drawFunc=self.__draw)

        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__mainSizer.Add(self.__infoSizer,     flag=wx.EXPAND)
        self.__mainSizer.Add(self.__canvas.canvas, flag=wx.EXPAND,
                             proportion=1)

        profile.registerHandler(
            'LeftMouseDown', self.name, self.__onMouseDown)
        profile.registerHandler(
            'LeftMouseDrag', self.name, self.__onMouseDrag)
        profile.registerHandler(
            'LeftMouseUp', self.name, self.__onMouseUp)

        self.SetSizer(self.__mainSizer)
        self.Layout()


    def __updateInfo(self, canvas):
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
            length = np.sqrt(np.sum((ws - we) ** 2))

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


    def __onMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse down events on an :class:`.OrthoPanel` canvas.
        Calls :meth:`__updateInfo`.
        """
        self.__updateInfo(canvas)


    def __onMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse drag events on an :class:`.OrthoPanel` canvas.
        Calls :meth:`__updateInfo`.
        """
        self.__updateInfo(canvas)


    def __onMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse up events on an :class:`.OrthoPanel` canvas.
        Samples and plots data from the currently selected overlay along
        the drawn sample line.
        """

        start = self.__profile.sampleStart
        end   = self.__profile.sampleEnd
        image = self.displayCtx.getSelectedOverlay()

        if start is None or end is None:
            return

        if image is None or not isinstance(image, fslimage.Image):
            return

        opts   = self.displayCtx.getOpts(image)
        data   = image[opts.index()]
        vstart = opts.transformCoords(start, 'display', 'voxel')
        vend   = opts.transformCoords(end,   'display', 'voxel')

        order        = self.interp
        resolution   = 100
        points       = np.zeros((3, resolution))
        points[0, :] = np.linspace(vstart[0], vend[0], resolution)
        points[1, :] = np.linspace(vstart[1], vend[1], resolution)
        points[2, :] = np.linspace(vstart[2], vend[2], resolution)

        x      = np.linspace(0, 1, resolution)
        y      = ndimage.map_coordinates(data, points, order=order)
        series = plotting.DataSeries(image,
                                     self.overlayList,
                                     self.displayCtx,
                                     self.__canvas)
        series.colour    = '#000050'
        series.lineWidth = 2
        series.setData(x, y)
        self.__ds = series
        self.__canvas.asyncDraw()


    def __draw(self):
        """Passed as the ``drawFunc`` to the :class:`.PlotCanvas`. Calls
        :meth:`.PlotCanvas.drawDataSeries`.
        """

        if self.__ds is None: series = None
        else:                 series = [self.__ds]

        self.__canvas.drawDataSeries(extraSeries=series, refresh=True)
