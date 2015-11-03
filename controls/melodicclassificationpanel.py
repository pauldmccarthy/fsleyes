#!/usr/bin/env python
#
# melodicclassificationpanel.py - The MelodicClassificationPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MelodicClassificationPanel` class, a
*FSLeyes control* panel which allows the user to classify the components
of a :class:`.MelodicImage`.
"""

import wx


import pwidgets.widgetgrid as widgetgrid
import pwidgets.texttag    as texttag
import pwidgets.notebook   as notebook

import fsl.data.strings      as strings
import fsl.data.melodicimage as fslmelimage
import fsl.fsleyes.panel     as fslpanel


class MelodicClassificationPanel(fslpanel.FSLEyesPanel):
    """The ``MelodicClassificationPanel``
    """

    # 
    # Choose label colours
    # Load/save from/to file
    #
    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``MelodicClassificationPanel``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList`.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """ 
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__disabledText = wx.StaticText(
            self,
            style=(wx.ALIGN_CENTRE_HORIZONTAL |
                   wx.ALIGN_CENTRE_VERTICAL))

        self.__notebook      = notebook.Notebook(self)
        self.__componentGrid = ComponentGrid(    self.__notebook)
        self.__labelGrid     = LabelGrid(        self.__notebook)

        self.__notebook.AddPage(self.__componentGrid, 'Components')
        self.__notebook.AddPage(self.__labelGrid,     'Labels')

        self.__mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__mainSizer.Add(self.__notebook, flag=wx.EXPAND, proportion=1)

        # TODO Things which you don't want shown when
        #      a melodic image is not selected should
        #      be added to __mainSizer. Things which
        #      you always want displayed should be
        #      added to __sizer (but need to be laid
        #      out w.r.t. __disabledText/__mainSizer)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__disabledText, flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__mainSizer,    flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer)

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__overlay = None
        self.__selectedOverlayChanged()


    def destroy(self):
        """
        """
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        fslpanel.FSLEyesPanel.destroy(self)


    def __enable(self, enable=True, message=''):
        """
        """

        self.__disabledText.SetLabel(message)
        
        self.__sizer.Show(self.__disabledText, not enable)
        self.__sizer.Show(self.__mainSizer,    enable)

        self.Layout()


    def __selectedOverlayChanged(self, *a):

        overlay = self._displayCtx.getSelectedOverlay()

        if (overlay is None) or \
           not isinstance(overlay, fslmelimage.MelodicImage):
            self.__enable(False, strings.messages[self, 'disabled'])
            return

        self.__overlay = overlay

        self.__componentGrid.setOverlay(overlay)
        self.__labelGrid    .setOverlay(overlay)

        self.__enable(True)


class ComponentGrid(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.__grid  = widgetgrid.WidgetGrid(self)
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__grid.ShowRowLabels(False)
        self.__grid.ShowColLabels(True)
        
        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer)

        
    def setOverlay(self, overlay):

        numComps = overlay.numComponents()

        self.__grid.ClearGrid()
        self.__grid.SetGridSize(numComps, 2, growCols=[1])

        self.__grid.SetColLabel(0, 'Component #')
        self.__grid.SetColLabel(1, 'Labels')

        for i in range(numComps):

            tags = texttag.TextTagPanel(self.__grid,
                                        style=(texttag.TTP_ALLOW_NEW_TAGS |
                                               texttag.TTP_ADD_NEW_TAGS   |
                                               texttag.TTP_NO_DUPLICATES))
            
            self.__grid.SetText(  i, 0, str(i))
            self.__grid.SetWidget(i, 1, tags)

        self.Layout()
        
        

class LabelGrid(wx.Panel):

    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent)

        self.__grid  = widgetgrid.WidgetGrid(self)
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer) 

        
    def setOverlay(self, overlay):
        pass
