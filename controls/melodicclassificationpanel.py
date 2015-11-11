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


import logging

import wx

import pwidgets.notebook         as notebook

import fsl.data.strings          as strings
import fsl.data.melodicimage     as fslmelimage
import fsl.fsleyes.colourmaps    as fslcm
import fsl.fsleyes.panel         as fslpanel
import melodicclassificationgrid as melodicgrid


log = logging.getLogger(__name__)


class MelodicClassificationPanel(fslpanel.FSLEyesPanel):
    """The ``MelodicClassificationPanel``
    """

    #
    # File format:
    #   First line:    ica directory name
    #   Lines 2-(N+1): One line for each component
    #   Last line:     List of bad components
    #
    # A component line:
    #   Component index, Label1, Label2, True|False
    #
    #
    #
    # Save to a FSLeyes label file:
    #
    # Save to a FIX/MELview file:
    #   - Component has 'Signal' label
    #   - Component has 'Unknown' label
    #   - All other labels are output as 'Unclassified Noise'
    #     (these are added  to the list on the last line of the file)
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


        self.__lut           = fslcm.getLookupTable('melodic-classes')
        self.__notebook      = notebook.Notebook(self)
        self.__componentGrid = melodicgrid.ComponentGrid(
            self.__notebook,
            self._overlayList,
            self._displayCtx,
            self.__lut)

        # self.__labelGrid     = melodicgrid.LabelGrid(
        #     self.__notebook,
        #     self._overlayList,
        #     self._displayCtx,
        #     self.__lut)
        self.__labelGrid = wx.Panel(self.__notebook)

        self.__loadButton  = wx.Button(self)
        self.__saveButton  = wx.Button(self)
        self.__clearButton = wx.Button(self)

        self.__notebook.AddPage(self.__componentGrid,
                                strings.labels[self, 'componentTab'])
        self.__notebook.AddPage(self.__labelGrid,
                                strings.labels[self, 'labelTab'])

        self.__loadButton .SetLabel(strings.labels[self, 'loadButton'])
        self.__saveButton .SetLabel(strings.labels[self, 'saveButton'])
        self.__clearButton.SetLabel(strings.labels[self, 'clearButton'])

        # Things which you don't want shown when
        # a melodic image is not selected should
        # be added to __mainSizer. Things which
        # you always want displayed should be
        # added to __sizer (but need to be laid
        # out w.r.t. __disabledText/__mainSizer)
 
        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer     = wx.BoxSizer(wx.VERTICAL)

        self.__btnSizer .Add(self.__loadButton,   flag=wx.EXPAND, proportion=1)
        self.__btnSizer .Add(self.__saveButton,   flag=wx.EXPAND, proportion=1)
        self.__btnSizer .Add(self.__clearButton,  flag=wx.EXPAND, proportion=1)
        
        self.__mainSizer.Add(self.__notebook,     flag=wx.EXPAND, proportion=1)
        self.__mainSizer.Add(self.__btnSizer,     flag=wx.EXPAND)

        self.__sizer    .Add(self.__disabledText, flag=wx.EXPAND, proportion=1)
        self.__sizer    .Add(self.__mainSizer,    flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer)

        self.__loadButton .Bind(wx.EVT_BUTTON, self.__onLoadButton)
        self.__saveButton .Bind(wx.EVT_BUTTON, self.__onSaveButton)
        self.__clearButton.Bind(wx.EVT_BUTTON, self.__onClearButton)

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
        """
        """

        overlay = self._displayCtx.getSelectedOverlay()

        if (overlay is None) or \
           not isinstance(overlay, fslmelimage.MelodicImage):
            self.__enable(False, strings.messages[self, 'disabled'])
            return

        self.__enable(True)

        
    def __onLoadButton(self, ev):
        """
        """

        lut      = self.__lut
        overlay  = self._displayCtx.getSelectedOverlay()
        melclass = overlay.getICClassification()
        dlg      = wx.FileDialog(
            self,
            message=strings.titles[self, 'loadDialog'],
            defaultDir=overlay.getMelodicDir(),
            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filename = dlg.GetPath()

        # Disable notification during the load,
        # so the component/label grids don't
        # confuse themselves. We'll manually
        # refresh them below.
        melclass.disableNotification('labels')
        lut     .disableNotification('labels')

        try:
            melclass.clear()
            melclass.load(filename)
            
        except Exception as e:
            e     = str(e)
            msg   = strings.messages[self, 'loadError'].format(filename, e)
            title = strings.titles[  self, 'loadError']
            log.debug('Error loading classification file '
                      '({}), ({})'.format(filename, e), exc_info=True)
            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK)

        # Make sure a colour in the melodic
        # lookup table exists for all labels
        for comp, labels in enumerate(melclass.labels):
            for label in labels:
                
                lutLabel = lut.getByName(label)
                if lutLabel is not None:
                    print 'Label {} is already in lookup table'.format(label)
                    continue

                print     'New melodic classification label: {}'.format(label)
                log.debug('New melodic classification label: {}'.format(label))
                lut.new(label)

        melclass.enableNotification('labels') 
        lut     .enableNotification('labels')

        lut     .notify('labels')
        melclass.notify('labels')

    
    def __onSaveButton(self, ev):
        """
        """
        overlay  = self._displayCtx.getSelectedOverlay()
        melclass = overlay.getICClassification()
        dlg      = wx.FileDialog(
            self,
            message=strings.titles[self, 'saveDialog'],
            defaultDir=overlay.getMelodicDir(),
            style=wx.FD_SAVE)
        
        if dlg.ShowModal() != wx.ID_OK:
            return

        filename = dlg.GetPath()

        try:
            melclass.save(filename)
            
        except Exception as e:
            e     = str(e)
            msg   = strings.messages[self, 'saveError'].format(filename, e)
            title = strings.titles[  self, 'saveError']
            log.debug('Error saving classification file '
                      '({}), ({})'.format(filename, e), exc_info=True)
            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 

    
    def __onClearButton(self, ev):
        """
        """
        
        overlay  = self._displayCtx.getSelectedOverlay()
        melclass = overlay.getICClassification()

        melclass.clear()
