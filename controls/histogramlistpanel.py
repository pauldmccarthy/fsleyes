#!/usr/bin/env python
#
# histogramlistpanel.py - The HistogramListPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramListPanel` class, which
is a *FSLeyes control* panel for use with :class:`.HistogramPanel` views.
"""


import wx

import pwidgets.elistbox      as elistbox
import fsl.fsleyes.panel      as fslpanel
import fsl.fsleyes.colourmaps as fslcm

import                           timeserieslistpanel 
    

class HistogramListPanel(fslpanel.FSLEyesPanel):
    """The ``HistogramListPanel`` is a control panel for use with the
    :class:`.HistogramPanel` view. It allows the user to add/remove
    :class:`.HistogramSeries` plots to/from the :class:`.HistogramPanel`,
    and to configure the display settings for each. A ``HistogramListPanel``
    looks something like this:

    .. image:: images/histogramlistpanel.png
       :scale: 50%
       :align: center

    
    The ``HistogramListPanel`` performs the same task for the
    :class:`.HistogramPanel` that the :class:`.TimeSeriesListPanel` does for
    the :class:`.TimeSeriesPanel`. For each :class:`.HistogramSeries` that is
    in the :attr:`.PlotPanel.dataSeries` list of the :class:`.HistogramPanel`,
    a :class:`.TimeSeriesWidget` control is added to a
    :class:`pwidgets.EditableListBox`.
    """

    
    def __init__(self, parent, overlayList, displayCtx, histPanel):
        """Create a ``HistogramListPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg histPanel:   The :class:`.HistogramPanel` instance. 
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__hsPanel      = histPanel
        self.__hsList       = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE |
                         elistbox.ELB_EDITABLE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__hsList, flag=wx.EXPAND, proportion=1)

        self.__hsList.Bind(elistbox.EVT_ELB_ADD_EVENT,    self.__onListAdd)
        self.__hsList.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self.__onListRemove)
        self.__hsList.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self.__onListEdit)
        self.__hsList.Bind(elistbox.EVT_ELB_SELECT_EVENT, self.__onListSelect)
        
        self.__hsPanel.addListener('dataSeries',
                                   self._name,
                                   self.__histSeriesChanged)

        self.__histSeriesChanged()
        self.Layout()

        
    def destroy(self):
        """Must be called when this ``HistogramListPanel`` is no longer needed.
        Removes some property listeners, and calls the
        :meth:`.FSLEyesPanel.destroy` method.
        """
        self.__hsPanel.removeListener('dataSeries', self._name)
        fslpanel.FSLEyesPanel.destroy(self)


    def getListBox(self):
        """Returns the :class:`pwidgets.EditableListBox` instance contained
        within this ``HistogramListPanel``.
        """
        return self.__hsList


    def __histSeriesChanged(self, *a):
        """Called when the :attr:`.PlotPanel.dataSeries` list of the
        :class:`.HistogramPanel` changes. Refreshes the contents of the
        :class:`pwidgets.EditableListBox`.
        """

        self.__hsList.Clear()

        for hs in self.__hsPanel.dataSeries:
            widg = timeserieslistpanel.TimeSeriesWidget(self, hs)
            
            self.__hsList.Append(hs.label,
                                 clientData=hs,
                                 extraWidget=widg)

        if len(self.__hsPanel.dataSeries) > 0:
            self.__hsList.SetSelection(0)
        
    
    def __onListAdd(self, ev):
        """Called when the user pushes the *add* button on the
        :class:`pwidgets.EditableListBox`. Adds the *current* histogram plot
        to the list (see the :class:`.HistogramPanel` class documentation).
        """
        hs = self.__hsPanel.getCurrent()

        if hs is None:
            return
        
        hs.alpha     = 1
        hs.lineWidth = 2
        hs.lineStyle = '-'
        hs.colour    = fslcm.randomColour()
        hs.label     = hs.overlay.name

        self.__hsPanel.dataSeries.append(hs)
        self.__hsPanel.selectedSeries = self.__hsList.GetSelection()

        
    def __onListEdit(self, ev):
        """Called when the user edits a label on the
        :class:`pwidgets.EditableListBox`. Updates the
        :attr:`.DataSeries.label` property of the corresponding
        :class:`.HistogramSeries` instance.
        """ 
        ev.data.label = ev.label

        
    def __onListSelect(self, ev):
        """Called when the user selects an item in the
        :class:`pwidgets.EditableListBox`. Sets the
        :attr:`.DisplayContext.selectedOverlay` to the overlay associated with
        the corresponding :class:`.HistogramSeries` instance.
        """ 
        overlay = ev.data.overlay
        self._displayCtx.selectedOverlay = self._overlayList.index(overlay)
        self.__hsPanel.selectedSeries = ev.idx

        
    def __onListRemove(self, ev):
        """Called when the user removes an item from the
        :class:`pwidgets.EditableListBox`. Removes the corresponding
        :class:`.HistogramSeries` instance from the
        :attr:`.PlotPanel.dataSeries` list of the :class:`.HistogramPanel`.
        """ 
        self.__hsPanel.dataSeries.remove(ev.data)
        self.__hsPanel.selectedSeries = self.__hsList.GetSelection()
        ev.data.destroy()
