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

import props

import pwidgets.elistbox    as elistbox

import fsl.fsleyes.panel    as fslpanel
import fsl.fsleyes.plotting as plotting
import fsl.fsleyes.tooltips as fsltooltips
import fsl.data.strings     as strings


class PlotListPanel(fslpanel.FSLEyesPanel):
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


    def __init__(self, parent, overlayList, displayCtx, plotPanel):
        """Create a ``PlotListPanel``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList`.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg plotPanel:   The :class:`.OverlayPlotPanel` associated with this
                          ``PlotListPanel``.
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__plotPanel = plotPanel
        self.__dsList    = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE |
                         elistbox.ELB_EDITABLE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__dsList, flag=wx.EXPAND, proportion=1)

        self.__dsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__dsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__dsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__dsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        
        self.__plotPanel.addListener('dataSeries',
                                     self._name,
                                     self.__dataSeriesChanged)

        self.__dataSeriesChanged()
        self.Layout()

        
    def destroy(self):
        """Must be called when this ``PlotListPanel`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.FSLEyesPanel.destroy` method.
        """

        self.__plotPanel.removeListener('dataSeries', self._name)
        fslpanel.FSLEyesPanel.destroy(self)


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`.PlotPanel.dataSeries` list of the
        :class:`.OverlayPlotPanel` changes. Updates the list of
        :class:`.TimeSeriesWidget` controls.
        """

        self.__dsList.Clear()

        for ds in self.__plotPanel.dataSeries:
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

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return
        
        ds = self.__plotPanel.getDataSeries(overlay)

        if ds is None:
            return

        opts = self._displayCtx.getOpts(overlay)

        if isinstance(ds, plotting.FEATTimeSeries):
            toAdd = list(ds.getModelTimeSeries())
        else:
            toAdd = [ds]

        copies = []

        for ds in toAdd:

            copy = plotting.DataSeries(overlay)

            copy.alpha     = ds.alpha
            copy.lineWidth = ds.lineWidth
            copy.lineStyle = ds.lineStyle
            copy.colour    = ds.colour
            copy.label     = ds.label

            copy.setData(*ds.getData())

            copies.append(copy)

            # This is a bit hacky.
            # When the user selects a data series in
            # the list, we want to change the selected
            # overlay/location/volume/etc to the
            # properties associated with the data series.
            # So here we're adding some attributes to
            # each data series instance so that the
            # __onListSelect method can update the
            # display properties.
            #
            if isinstance(ds, (plotting.MelodicTimeSeries,
                               plotting.MelodicPowerSpectrumSeries)):
                copy._volume = opts.volume
                
            elif isinstance(ds, (plotting.VoxelTimeSeries,
                                 plotting.VoxelPowerSpectrumSeries)):
                copy._location = opts.getVoxel()
                
        self.__plotPanel.dataSeries.extend(copies)

        
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
        opts    = self._displayCtx.getOpts(overlay)

        self._displayCtx.selectedOverlay = self._overlayList.index(overlay)

        # See hacky things in __onListAdd
        if hasattr(ds, '_volume'):
            opts.volume = ds._volume
            
        elif hasattr(ds, '_location'):
            voxLoc = np.array(ds._location)
            disLoc = opts.transformCoords([voxLoc], 'voxel', 'display')[0]
            self._displayCtx.location = disLoc

        
    def __onListRemove(self, ev):
        """Called when the user removes an item from the
        :class:`.EditableListBox`. Removes the corresponding
        :class:`.DataSeries` instance from the :attr:`.PlotPanel.dataSeries`
        list of the :class:`.OverlayPlotPanel`.
        """
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

        self.__colour    = props.makeWidget(self,
                                            dataSeries,
                                            'colour')
        self.__alpha     = props.makeWidget(self,
                                            dataSeries,
                                            'alpha',
                                            slider=True,
                                            spin=False,
                                            showLimits=False) 
        self.__lineWidth = props.makeWidget(self,
                                            dataSeries,
                                            'lineWidth')
        self.__lineStyle = props.makeWidget(
            self,
            dataSeries,
            'lineStyle',
            labels=strings.choices['DataSeries.lineStyle'])

        self.__colour.SetToolTipString(
            fsltooltips.properties[dataSeries, 'colour'])
        self.__alpha.SetToolTipString(
            fsltooltips.properties[dataSeries, 'alpha'])
        self.__lineWidth.SetToolTipString(
            fsltooltips.properties[dataSeries, 'lineWidth'])
        self.__lineStyle.SetToolTipString(
            fsltooltips.properties[dataSeries, 'lineStyle'])

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__colour)
        self.__sizer.Add(self.__alpha)
        self.__sizer.Add(self.__lineWidth)
        self.__sizer.Add(self.__lineStyle)

        self.Layout()
