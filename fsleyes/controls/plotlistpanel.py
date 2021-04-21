#!/usr/bin/env python
#
# plotlistpanel.py - The PlotListPanel class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PlotListPanel` a *FSLeyes control* panel
which allows the user to add/remove :class:`.DataSeries` from an
:class:`.OverlayPlotPanel`.
"""


import numpy as np

import wx

import fsleyes_props                 as props
import fsleyes_widgets.elistbox      as elistbox

import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.views.plotpanel       as plotpanel
import fsleyes.tooltips              as fsltooltips
import fsleyes.strings               as strings


class PlotListPanel(ctrlpanel.ControlPanel):
    """The ``PlotListPanel`` is a *FSLeyes control* panel for use with
    :class:`.OverlayPlotPanel` views. It allows the user to add and remove
    :class:`.DataSeries` instances from the :attr:`.PlotPanel.dataSeries`
    list.


    For every :class:`.DataSeries` instance in the
    :attr:`.PlotPanel.dataSeries` list of the :class:`.OverlayPlotPanel`, the
    ``PlotListPanel`` creates a :class:`.DataSeriesWidget`, which allows the
    user to change the display settings of the :class:`.DataSeries`
    instance. A :class:`.EditableListBox` is used to display the labels for
    each :class:`.DataSeries` instance, and the associated
    :class:`.DataSeriesWidget` controls.
    """


    @staticmethod
    def supportedViews():
        """The ``PlotListPanel`` is restricted for use with
        :class:`.OverlayPlotPanel` views. This method may be overridden by
        sub-classes.
        """
        return [plotpanel.OverlayPlotPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.LEFT}


    def __init__(self, parent, overlayList, displayCtx, plotPanel):
        """Create a ``PlotListPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList`.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg plotPanel:   The :class:`.OverlayPlotPanel` associated with this
                          ``PlotListPanel``.
        """

        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, plotPanel)

        self.__plotPanel = plotPanel
        self.__dsList    = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE  |
                         elistbox.ELB_EDITABLE |
                         elistbox.ELB_WIDGET_RIGHT))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__dsList, flag=wx.EXPAND, proportion=1)

        self.__dsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__dsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__dsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__dsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)

        self.__plotPanel.canvas.addListener('dataSeries',
                                            self.name,
                                            self.__dataSeriesChanged)

        self.__dataSeriesChanged()
        self.Layout()
        self.SetMinSize(self.__sizer.GetMinSize())


    def destroy(self):
        """Must be called when this ``PlotListPanel`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.ControlPanel.destroy` method.
        """

        # the plot panel may have already
        # cleared its canvas ref before we
        # get destroyed
        if self.__plotPanel.canvas is not None:
            self.__plotPanel.canvas.removeListener('dataSeries', self.name)
        self.__plotPanel = None
        self.__dsList.Clear()
        ctrlpanel.ControlPanel.destroy(self)


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`.PlotPanel.dataSeries` list of the
        :class:`.OverlayPlotPanel` changes. Updates the list of
        :class:`.TimeSeriesWidget` controls.
        """

        self.__dsList.Clear()

        for ds in self.__plotPanel.canvas.dataSeries:
            widg = DataSeriesWidget(self, ds)
            self.__dsList.Append(
                ds.label,
                clientData=ds,
                tooltip=fsltooltips.properties[ds, 'label'],
                extraWidget=widg)


    def __onListAdd(self, ev):
        """Called when the user pushes the *add* button on the
        :class:`.EditableListBox`.  Adds the :class:`.DataSeries` associated
        with the currently selected overlay to the
        :attr:`.PlotPanel.dataSeries` list of the :class:`.OverlayPlotPanel`.
        """

        self.__plotPanel.addDataSeries()


    def __onListEdit(self, ev):
        """Called when the user edits a label on the
        :class:`.EditableListBox`. Updates the :attr:`.DataSeries.label`
        property of the corresponding :class:`DataSeries` instance.
        """
        ev.data.label = ev.label


    def __onListSelect(self, ev):
        """Called when the user selects an item in the
        :class:`.EditableListBox`. Sets the
        :attr:`.DisplayContext.selectedOverlay` to the overlay associated
        with the corresponding :class:`.DataSeries` instance.
        """

        ds      = ev.data
        overlay = ds.overlay

        if overlay is None:
            return

        opts = self.displayCtx.getOpts(overlay)

        self.displayCtx.selectedOverlay = self.overlayList.index(overlay)

        # See hacky things in __onListAdd
        if hasattr(ds, '_volume'):
            opts.volume = ds._volume

        elif hasattr(ds, '_location'):
            voxLoc = np.array(ds._location)
            disLoc = opts.transformCoords([voxLoc], 'voxel', 'display')[0]
            self.displayCtx.location = disLoc


    def __onListRemove(self, ev):
        """Called when the user removes an item from the
        :class:`.EditableListBox`. Removes the corresponding
        :class:`.DataSeries` instance from the :attr:`.PlotPanel.dataSeries`
        list of the :class:`.OverlayPlotPanel`.
        """
        with props.skip(self.__plotPanel.canvas, 'dataSeries', self.name):
            self.__plotPanel.dataSeries.remove(ev.data)


class DataSeriesWidget(wx.Panel):
    """The ``DataSeriesWidget`` class is a panel which contains controls
    that modify the properties of a :class:`.DataSeries` instance. A
    ``DataSeriesWidget`` is created by the :class:`PlotListPanel` for
    every ``DataSeries`` in the :attr:`.PlotPanel.dataSeries` list.
    """


    def __init__(self, parent, dataSeries):
        """Create a ``DataSeriesWidget``.

        :arg parent:     The :mod:`wx` parent object.

        :arg dataSeries: The :class:`.DataSeries` instance.
        """

        wx.Panel.__init__(self, parent)

        self.__enabled   = props.makeWidget(self, dataSeries, 'enabled')
        self.__colour    = props.makeWidget(self, dataSeries, 'colour')
        self.__lineWidth = props.makeWidget(self, dataSeries, 'lineWidth')
        self.__lineStyle = props.makeWidget(
            self,
            dataSeries,
            'lineStyle',
            labels=strings.choices['DataSeries.lineStyle'])

        self.__enabled.SetToolTip(
            wx.ToolTip(fsltooltips.properties[dataSeries, 'enabled']))
        self.__colour.SetToolTip(
            wx.ToolTip(fsltooltips.properties[dataSeries, 'colour']))
        self.__lineWidth.SetToolTip(
            wx.ToolTip(fsltooltips.properties[dataSeries, 'lineWidth']))
        self.__lineStyle.SetToolTip(
            wx.ToolTip(fsltooltips.properties[dataSeries, 'lineStyle']))

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__enabled)
        self.__sizer.Add(self.__colour)
        self.__sizer.Add(self.__lineWidth)
        self.__sizer.Add(self.__lineStyle)

        self.Layout()
