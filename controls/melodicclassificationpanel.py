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


import pwidgets.notebook         as notebook

import fsl.data.strings          as strings
import fsl.data.melodicimage     as fslmelimage
import fsl.fsleyes.colourmaps    as fslcm
import fsl.fsleyes.panel         as fslpanel
import melodicclassificationgrid as melodicgrid


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


        lut = fslcm.getLookupTable('melodic-classes')

        self.__notebook      = notebook.Notebook(self)
        self.__componentGrid = melodicgrid.ComponentGrid(
            self.__notebook,
            self._overlayList,
            self._displayCtx,
            lut)

        self.__labelGrid     = melodicgrid.LabelGrid(
            self.__notebook,
            self._overlayList,
            self._displayCtx,
            lut) 

        self.__notebook.AddPage(self.__componentGrid,
                                strings.labels[self, 'componentTab'])
        self.__notebook.AddPage(self.__labelGrid,
                                strings.labels[self, 'labelTab'])

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

        self.__selectedOverlayChanged()

        self.SetMinSize((400, 100))


    def destroy(self):
        """
        """
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.__componentGrid.destroy()
        self.__labelGrid    .destroy()
        
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

        self.__enable(True)
