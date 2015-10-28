#!/usr/bin/env python
#
# timeserieslistpanel.py - The TimeSeriesListPanel and TimeSeriesWidget
#                          classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesListPanel` class, which is a
*FSLeyes control* panel for use with the :class:`.TimeSeriesPanel` view.
"""


import          wx
import numpy as np

import                                    props
import pwidgets.elistbox               as elistbox
import fsl.fsleyes.panel               as fslpanel
import fsl.fsleyes.tooltips            as fsltooltips
import fsl.fsleyes.plotting.timeseries as timeseries
import fsl.data.strings                as strings


class TimeSeriesListPanel(fslpanel.FSLEyesPanel):
    """The ``TimeSeriesListPanel`` is a control panel for use with the
    :class:`.TimeSeriesPanel` view. It allows the user to add/remove
    :class:`.TimeSeries` plots to/from the ``TimeSeriesPanel``, and to
    configure the settings for each ``TimeSeries`` in the
    :attr:`.PlotPanel.dataSeries` list. A ``TimeSeriesListPanel`` looks
    something like the following:

    .. image:: images/timeserieslistpanel.png
       :scale: 50%
       :align: center


    For every :class:`.TimeSeries` instance in the
    :attr:`.PlotPanel.dataSeries` list of the :class:`.TimeSeriesPanel`, the
    ``TimeSeriesListPanel`` creates a :class:`.TimeSeriesWidget`, which allows
    the user to change the display settings of the :class:`.TimeSeries`
    instance. A :class:`pwidgets.EditableListBox` is used to display the
    labels for each :class:`.TimeSeries` instance, and the associated
    :class:`.TimeSeriesWidget` controls.

    A label is also shown above the list, containing the name of the currently
    selected overlay, and the voxel coordinates of the current
    :attr:`.DisplayContext.location`.
    """

    
    def __init__(self, parent, overlayList, displayCtx, timeSeriesPanel):
        """Create a ``TimeSeriesListPanel``.

        :arg parent:          The :mod:`wx` parent object.
        :arg overlayList:     The :class:`.OverlayList` instance.
        :arg displayCtx:      The :class:`.DisplayContext` instance.
        :arg timeSeriesPanel: The :class:`.TimeSeriesPanel` instance.
        """
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__tsPanel      = timeSeriesPanel
        self.__currentLabel = wx.StaticText(self)
        self.__tsList       = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE |
                         elistbox.ELB_EDITABLE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__currentLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__tsList,       flag=wx.EXPAND, proportion=1)

        self.__tsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__tsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__tsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__tsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        
        displayCtx    .addListener('selectedOverlay',
                                   self._name,
                                   self.__locationChanged)
        displayCtx    .addListener('location',
                                   self._name,
                                   self.__locationChanged) 
        overlayList   .addListener('overlays',
                                   self._name,
                                   self.__locationChanged)
        self.__tsPanel.addListener('dataSeries',
                                   self._name,
                                   self.__timeSeriesChanged)

        self.__timeSeriesChanged()
        self.__locationChanged()
        self.Layout()

        
    def destroy(self):
        """Must be called when this ``TimeSeriesListPanel`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.FSLEyesPanel.destroy` method.
        """
        
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('location',        self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.__tsPanel   .removeListener('dataSeries',      self._name)
        
        fslpanel.FSLEyesPanel.destroy(self)


    def __timeSeriesChanged(self, *a):
        """Called when the :attr:`.PlotPanel.dataSeries` list of the
        :class:`.TimeSeriesPanel` changes. Updates the list of
        :class:`.TimeSeriesWidget` controls.
        """

        self.__tsList.Clear()

        for ts in self.__tsPanel.dataSeries:
            widg = TimeSeriesWidget(self, ts)
            self.__tsList.Append(
                ts.label,
                clientData=ts,
                tooltip=fsltooltips.properties[ts, 'label'],
                extraWidget=widg)


    def __locationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.location` changes.

        Updates a label at the top of the ``TimeSeriesListPanel``, displaying
        the currently selected overlay, and the current voxel location.
        """

        overlay = self._displayCtx.getSelectedOverlay()

        ts = self.__tsPanel.getTimeSeries(overlay)

        if ts is None:
            self.__currentLabel.SetLabel('')
            return

        self.__currentLabel.SetLabel(ts.makeLabel())

    
    def __onListAdd(self, ev):
        """Called when the user pushes the *add* button on the
        :class:`pwidgets.EditableListBox`.  Adds the *current* time series
        plot to the :attr:`.PlotPanel.dataSeries` list of the
        :class:`.TimeSeriesPanel` (see the :class:`.TimeSeriesPanel` class
        documentation).
        """

        overlay = self._displayCtx.getSelectedOverlay()
        
        if overlay is None:
            return
        
        ts = self.__tsPanel.getTimeSeries(overlay)

        if ts is None:
            return

        if isinstance(ts, timeseries.FEATTimeSeries):
            toAdd = list(ts.getModelTimeSeries())
        else:
            toAdd = [ts]

        copies = []

        for ts in toAdd:

            copy = timeseries.TimeSeries(self.__tsPanel,
                                         overlay,
                                         self._displayCtx)

            copy.alpha     = ts.alpha
            copy.lineWidth = ts.lineWidth
            copy.lineStyle = ts.lineStyle
            copy.colour    = ts.colour
            copy.label     = ts.label

            copy.setData(*ts.getData())

            # This is hacky, and is here in order to
            # make the __onListSelect method work.
            if isinstance(ts, timeseries.MelodicTimeSeries):
                copy.tsLoc = 'volume'
                copy.coord = ts.getComponent()
            else:
                copy.tsLoc = 'location'
                copy.coord = ts.getVoxel()

            copies.append(copy)

        self.__tsPanel.dataSeries.extend(copies)

        
    def __onListEdit(self, ev):
        """Called when the user edits a label on the
        :class:`pwidgets.EditableListBox`. Updates the
        :attr:`.DataSeries.label` property of the corresponding
        :class:`.TimeSeries` instance.
        """
        ev.data.label = ev.label

        
    def __onListSelect(self, ev):
        """Called when the user selects an item in the
        :class:`pwidgets.EditableListBox`. Sets the
        :attr:`.DisplayContext.selectedOverlay` to the overlay associated with
        the corresponding :class:`.TimeSeries` instance.
        """

        ts      = ev.data
        overlay = ts.overlay 
        opts    = self._displayCtx.getOpts(overlay)

        # See hacky things in __onListAdd
        if ts.tsLoc == 'volume':
            opts.volume = ts.coord
            
        elif ts.tsLoc == 'location':
            voxLoc = np.array(ts.coord)
            disLoc = opts.transformCoords([voxLoc], 'voxel', 'display')[0]

            self._displayCtx.location = disLoc

        self._displayCtx.selectedOverlay = self._overlayList.index(overlay)

        
    def __onListRemove(self, ev):
        """Called when the user removes an item from the
        :class:`pwidgets.EditableListBox`. Removes the corresponding
        :class:`.TimeSeries` instance from the :attr:`.PlotPanel.dataSeries`
        list of the :class:`.TimeSeriesPanel`.
        """
        self.__tsPanel.dataSeries.remove(ev.data)

        
class TimeSeriesWidget(wx.Panel):
    """The ``TimeSeriesWidget`` class is a panel which contains controls
    that modify the properties of a :class:`.TimeSeries` instance. A
    ``TimeSeriesWidget`` is created by the :class:`TimeSeriesListPanel` for
    every ``TimeSeries`` in the :attr:`.TimeSeriesPanel.dataSeries` list.

    A ``TimeSeriesWidget`` may be created for instances of any sub-class
    of :class:`.DataSeries`, not just the :class:`.TimeSeries` class.
    """

    
    def __init__(self, parent, timeSeries):
        """Create a ``TimeSeriesWidget``.

        :arg parent:     The :mod:`wx` parent object.
        
        :arg timeSeries: The :class:`.DataSeries` instance.
        """

        wx.Panel.__init__(self, parent)

        self.__colour    = props.makeWidget(self,
                                            timeSeries,
                                            'colour')
        self.__alpha     = props.makeWidget(self,
                                            timeSeries,
                                            'alpha',
                                            slider=True,
                                            spin=False,
                                            showLimits=False) 
        self.__lineWidth = props.makeWidget(self,
                                            timeSeries,
                                            'lineWidth')
        self.__lineStyle = props.makeWidget(
            self,
            timeSeries,
            'lineStyle',
            labels=strings.choices['DataSeries.lineStyle'])

        self.__colour.SetToolTipString(
            fsltooltips.properties[timeSeries, 'colour'])
        self.__alpha.SetToolTipString(
            fsltooltips.properties[timeSeries, 'alpha'])
        self.__lineWidth.SetToolTipString(
            fsltooltips.properties[timeSeries, 'lineWidth'])
        self.__lineStyle.SetToolTipString(
            fsltooltips.properties[timeSeries, 'lineStyle'])

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__colour)
        self.__sizer.Add(self.__alpha)
        self.__sizer.Add(self.__lineWidth)
        self.__sizer.Add(self.__lineStyle)

        self.Layout()
