#!/usr/bin/env python
#
# lookuptablepanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import copy
import logging

import wx

import numpy as np

import props

import pwidgets.elistbox          as elistbox

import fsl.fsleyes.panel          as fslpanel
import fsl.fsleyes.displaycontext as displayctx
import fsl.fsleyes.colourmaps     as fslcmaps
import fsl.data.strings           as strings


log = logging.getLogger(__name__)




class LabelWidget(wx.Panel):
    
    def __init__(self, lutPanel, overlayOpts, lut, value):
        wx.Panel.__init__(self, lutPanel)

        self.lutPanel = lutPanel
        self.opts     = overlayOpts
        self.lut      = lut
        self.value    = value

        # TODO Change the enable box to a toggle
        #      button with an eye icon
        
        self.valueLabel   = wx.StaticText(self,
                                          style=wx.ALIGN_CENTRE_VERTICAL |
                                                wx.ALIGN_RIGHT)
        self.enableBox    = wx.CheckBox(self)
        self.colourButton = wx.ColourPickerCtrl(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.sizer.Add(self.valueLabel,   flag=wx.ALIGN_CENTRE, proportion=1)
        self.sizer.Add(self.enableBox,    flag=wx.ALIGN_CENTRE, proportion=1)
        self.sizer.Add(self.colourButton, flag=wx.ALIGN_CENTRE, proportion=1)

        label  = lut.get(value)
        colour = [np.floor(c * 255.0) for c in label.colour()]

        self.valueLabel  .SetLabel(str(value))
        self.colourButton.SetColour(colour)
        self.enableBox   .SetValue(label.enabled())

        self.enableBox   .Bind(wx.EVT_CHECKBOX,             self.__onEnable)
        self.colourButton.Bind(wx.EVT_COLOURPICKER_CHANGED, self.__onColour)

        
    def __onEnable(self, ev):

        # Disable the LutPanel listener, otherwise
        # it will recreate the label list (see
        # LookupTablePanel._initLabelList)
        self.lut.disableListener('labels', self.lutPanel._name)
        self.lut.set(self.value, enabled=self.enableBox.GetValue())
        self.lut.enableListener('labels', self.lutPanel._name)

        
    def __onColour(self, ev):

        newColour = self.colourButton.GetColour()
        newColour = [c / 255.0 for c in newColour]

        self.lut.disableListener('labels', self.lutPanel._name)
        self.lut.set(self.value, colour=newColour)
        self.lut.enableListener('labels', self.lutPanel._name)


class LookupTablePanel(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx):

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__controlRow    = wx.Panel(self)
        self.__disabledLabel = wx.StaticText(self,
                                             style=wx.ALIGN_CENTER_VERTICAL |
                                                   wx.ALIGN_CENTER_HORIZONTAL)
        self.__labelList     = elistbox.EditableListBox(
            self,
            style=elistbox.ELB_NO_MOVE | elistbox.ELB_EDITABLE)

        self.__overlayNameLabel = wx.StaticText(self,
                                                style=wx.ST_ELLIPSIZE_MIDDLE)

        self.__lutWidget        = None
        self.__newLutButton     = wx.Button(self.__controlRow)
        self.__copyLutButton    = wx.Button(self.__controlRow)
        self.__saveLutButton    = wx.Button(self.__controlRow)
        self.__loadLutButton    = wx.Button(self.__controlRow)

        self.__controlRowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer           = wx.BoxSizer(wx.VERTICAL)

        self.__controlRow.SetSizer(self.__controlRowSizer)
        self             .SetSizer(self.__sizer)

        self.__controlRowSizer.Add(self.__newLutButton,
                                   flag=wx.EXPAND, proportion=1)
        self.__controlRowSizer.Add(self.__copyLutButton,
                                   flag=wx.EXPAND, proportion=1) 
        self.__controlRowSizer.Add(self.__loadLutButton,
                                   flag=wx.EXPAND, proportion=1)
        self.__controlRowSizer.Add(self.__saveLutButton,
                                   flag=wx.EXPAND, proportion=1)

        self.__sizer.Add(self.__overlayNameLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__controlRow,       flag=wx.EXPAND)
        self.__sizer.Add(self.__disabledLabel,    flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__labelList,        flag=wx.EXPAND, proportion=1)

        # Label the labels and buttons
        self.__disabledLabel.SetLabel(strings.messages[self, 'notLutOverlay'])
        self.__newLutButton .SetLabel(strings.labels[  self, 'newLut'])
        self.__copyLutButton.SetLabel(strings.labels[  self, 'copyLut'])
        self.__loadLutButton.SetLabel(strings.labels[  self, 'loadLut'])
        self.__saveLutButton.SetLabel(strings.labels[  self, 'saveLut'])

        # Listen for listbox events
        self.__labelList.Bind(elistbox.EVT_ELB_ADD_EVENT,
                              self.__onLabelAdd)
        self.__labelList.Bind(elistbox.EVT_ELB_REMOVE_EVENT,
                              self.__onLabelRemove)
        self.__labelList.Bind(elistbox.EVT_ELB_EDIT_EVENT,
                              self.__onLabelEdit)

        self.__newLutButton .Bind(wx.EVT_BUTTON, self.__onNewLut)
        self.__copyLutButton.Bind(wx.EVT_BUTTON, self.__onCopyLut)
        self.__loadLutButton.Bind(wx.EVT_BUTTON, self.__onLoadLut)
        self.__saveLutButton.Bind(wx.EVT_BUTTON, self.__onSaveLut)

        self.__selectedOverlay = None
        self.__selectedOpts    = None
        self.__selectedLut     = None

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__disabledLabel.Show(False)
        self.__controlRowSizer.SetMinSize(self.__calcControlRowMinSize())
        self.Layout()
        self.SetMinSize(self.__sizer.GetMinSize())

        self.__selectedOverlayChanged()


    def __calcControlRowMinSize(self):
        """This method calculates and returns a minimum width and height
        for the control row.

        When the LookupTable is first created, there is no LUT widget - it is
        created when an appropriate overlay is selected (see
        :meth:`__overlayTypeChanged`). Here, we create a dummy LUT widget, and
        use its best size, along with the control row button sizes, to
        calculate the minimum size needed to lay out the control row.
        """

        class DummyLut(props.HasProperties):
            lut = copy.copy(displayctx.LabelOpts.lut)

        dl             = DummyLut()
        dummyLutWidget = props.makeWidget(
            self,
            dl,
            'lut',
            labels=lambda l: l.name)
        width, height  = dummyLutWidget.GetBestSize().Get()
        
        for btn in [self.__newLutButton,
                    self.__copyLutButton,
                    self.__saveLutButton,
                    self.__loadLutButton]:
            
            w, h   =  btn.GetBestSize().Get()
            width += w

            if h > height:
                height = h
        
        dummyLutWidget.Destroy()

        return width, height

        
    def destroy(self):

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        overlay = self.__selectedOverlay
        opts    = self.__selectedOpts
        lut     = self.__selectedLut

        if overlay is not None:

            display = self._displayCtx.getDisplay(overlay)

            display.removeListener('name',        self._name)
            display.removeListener('overlayType', self._name)

        if opts is not None:
            opts.removeListener('lut', self._name)

        if lut is not None:
            lut.removeListener('labels', self._name)
            lut.removeListener('saved',  self._name)

        fslpanel.FSLEyesPanel.destroy(self)
    

    def __selectedOverlayChanged(self, *a):

        newOverlay = self._displayCtx.getSelectedOverlay()

        if self.__selectedOverlay == newOverlay:
            return

        if self.__selectedOverlay is not None and \
           self.__selectedOverlay in self._overlayList:
            
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            
            display.removeListener('name',        self._name)
            display.removeListener('overlayType', self._name)

        self.__selectedOverlay = newOverlay

        if newOverlay is not None:
            display = self._displayCtx.getDisplay(newOverlay)
            display.addListener('name',
                                self._name,
                                self.__overlayNameChanged)
            display.addListener('overlayType',
                                self._name,
                                self.__overlayTypeChanged)

        self.__overlayNameChanged()
        self.__overlayTypeChanged()


    def __overlayNameChanged(self, *a):

        overlay = self.__selectedOverlay

        if overlay is None:
            self.__overlayNameLabel.SetLabel('')
            return

        display = self._displayCtx.getDisplay(overlay)

        self.__overlayNameLabel.SetLabel(display.name)
        

    def __overlayTypeChanged(self, *a):

        if self.__lutWidget is not None:
            self.__controlRowSizer.Detach(self.__lutWidget)
            self.__lutWidget.Destroy()
            self.__lutWidget = None

        if self.__selectedOpts is not None:
            self.__selectedOpts.removeListener('lut', self._name)
            self.__selectedOpts = None

        overlay = self.__selectedOverlay
        enabled = False

        if overlay is not None:
            opts = self._displayCtx.getOpts(overlay)

            if isinstance(opts, displayctx.LabelOpts):
                enabled = True

        self.__overlayNameLabel.Show(    enabled)
        self.__controlRow      .Show(    enabled)
        self.__labelList       .Show(    enabled)
        self.__disabledLabel   .Show(not enabled)

        if not enabled:
            self.Layout()
            return

        opts = self._displayCtx.getOpts(overlay)

        opts.addListener('lut', self._name, self.__lutChanged)
        
        self.__selectedOpts = opts
        self.__lutWidget    = props.makeWidget(
            self.__controlRow, opts, 'lut', labels=lambda l: l.name)

        self.__controlRowSizer.Insert(
            0, self.__lutWidget, flag=wx.EXPAND, proportion=1)

        self.__lutChanged()

        self.Layout()


    def __lutChanged(self, *a):

        if self.__selectedLut is not None:
            self.__selectedLut.removeListener('labels', self._name)
            self.__selectedLut.removeListener('saved',  self._name)
            self.__selecedLut = None

        opts = self.__selectedOpts

        if opts is not None:
            self.__selectedLut = opts.lut

            self.__selectedLut.addListener(
                'labels', self._name, self.__initLabelList)
            self.__selectedLut.addListener(
                'saved', self._name, self.__lutSaveStateChanged)

        self.__initLabelList()
        self.__lutSaveStateChanged()

        
    def __lutSaveStateChanged(self, *a):
        self.__saveLutButton.Enable(not self.__selectedLut.saved)

        
    def __initLabelList(self, *a):

        self.__labelList.Clear()

        if self.__selectedOpts is None:
            return

        opts = self.__selectedOpts
        lut  = opts.lut

        for i, label in enumerate(lut.labels):

            self.__labelList.Append(label.name())

            widget = LabelWidget(self, opts, lut, label.value())
            self.__labelList.SetItemWidget(i, widget)


    def __onNewLut(self, ev):

        dlg = NewLutDialog(self.GetTopLevelParent())
        if dlg.ShowModal() != wx.ID_OK:
            return

        log.debug('Creating and registering new '
                  'LookupTable: {}'.format(dlg.name))

        lut = fslcmaps.LookupTable(dlg.name)
        fslcmaps.registerLookupTable(lut, self._overlayList, self._displayCtx)

        if self.__selectedOpts is not None:
            self.__selectedOpts.lut = lut


    def __onCopyLut(self, ev):

        name = self.__selectedLut.name

        dlg = NewLutDialog(self.GetTopLevelParent(), name)
        
        if dlg.ShowModal() != wx.ID_OK:
            return

        log.debug('Creating and registering new '
                  'LookupTable {} (copied from {})'.format(dlg.name, name))

        lut = fslcmaps.LookupTable(dlg.name)

        for label in self.__selectedLut.labels:
            lut.set(label.value(),
                    name=label.name(),
                    colour=label.colour(),
                    enabled=label.enabled())
        
        fslcmaps.registerLookupTable(lut, self._overlayList, self._displayCtx)

        if self.__selectedOpts is not None:
            self.__selectedOpts.lut = lut 

    
    def __onLoadLut(self, ev):

        nameDlg = NewLutDialog(self.GetTopLevelParent())
        
        if nameDlg.ShowModal() != wx.ID_OK:
            return
        
        fileDlg = wx.FileDialog(wx.GetApp().GetTopWindow(),
                                message=strings.titles[self, 'loadLut'],
                                defaultDir=os.getcwd(),
                                style=wx.FD_OPEN)

        if fileDlg.ShowModal() != wx.ID_OK:
            return

        name = nameDlg.name
        path = fileDlg.GetPath()

        lut = fslcmaps.registerLookupTable(path,
                                           self._overlayList,
                                           self._displayCtx,
                                           name)

        if self.__selectedOpts is not None:
            self.__selectedOpts.lut = lut
        
    
    def __onSaveLut(self, ev):
        fslcmaps.installLookupTable(self.__selectedLut.name)

    
    def __onLabelAdd(self, ev):

        dlg = LutLabelDialog(self.GetTopLevelParent())
        if dlg.ShowModal() != wx.ID_OK:
            return

        opts   = self.__selectedOpts
        value  = dlg.value
        name   = dlg.name
        colour = dlg.colour[:3]
        colour = [c / 255.0 for c in colour]

        if opts.lut.get(value) is not None:
            wx.MessageBox(
                strings.messages[self, 'labelExists'].format(
                    opts.lut.name, value),
                strings.titles[  self, 'labelExists'],
                wx.ICON_INFORMATION | wx.OK)
            return

        log.debug('New lut label for {}: {}, {}, {}'.format(
            opts.lut.name,
            value,
            name,
            colour))

        opts.lut.set(value, name=name, colour=colour)

    
    def __onLabelRemove(self, ev):

        opts  = self.__selectedOpts
        value = opts.lut.labels[ev.idx].value()

        self.__selectedLut.disableListener('labels', self._name)
        opts.lut.delete(value)
        self.__selectedLut.enableListener('labels', self._name)


    def __onLabelEdit(self, ev):

        opts  = self.__selectedOpts
        value = opts.lut.labels[ev.idx].value()

        self.__selectedLut.disableListener('labels', self._name)
        opts.lut.set(value, name=ev.label)
        self.__selectedLut.enableListener('labels', self._name)


class NewLutDialog(wx.Dialog):
    """A dialog which is displayed when the user chooses to create a new LUT.

    Prompts the user to enter a name.
    """
    
    def __init__(self, parent, name=None):

        if name is None:
            name = strings.labels[self, 'newLut']

        wx.Dialog.__init__(self, parent, title=strings.titles[self])

        self._message = wx.StaticText(self)
        self._name    = wx.TextCtrl(  self)
        self._ok      = wx.Button(    self, id=wx.ID_OK)
        self._cancel  = wx.Button(    self, id=wx.ID_CANCEL)

        self._message.SetLabel(strings.messages[self, 'newLut'])
        self._ok     .SetLabel(strings.labels[  self, 'ok'])
        self._cancel .SetLabel(strings.labels[  self, 'cancel'])
        self._name   .SetValue(name)

        self._sizer    = wx.BoxSizer(wx.VERTICAL)
        self._btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.SetSizer(self._sizer)

        self._sizer   .Add(self._message,  flag=wx.EXPAND | wx.ALL, border=10)
        self._sizer   .Add(self._name,     flag=wx.EXPAND | wx.ALL, border=10)
        self._sizer   .Add(self._btnSizer, flag=wx.EXPAND)
        self._btnSizer.Add(self._ok,       flag=wx.EXPAND, proportion=1)
        self._btnSizer.Add(self._cancel,   flag=wx.EXPAND, proportion=1)

        self._ok    .Bind(wx.EVT_BUTTON, self.onOk)
        self._cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self._ok.SetDefault()
        
        self.Fit()
        self.Layout()

        self.CentreOnParent()

        self.name = None


    def onOk(self, ev):
        self.name = self._name.GetValue()
        self.EndModal(wx.ID_OK)


    def onCancel(self, ev):
        self.EndModal(wx.ID_CANCEL)
 

class LutLabelDialog(wx.Dialog):
    """A dialog which is displayed when the user adds a new label to the
    current :class:`.LookupTable`.

    Prompts the user to enter a label value, name, and colour.
    """

    def __init__(self, parent):

        wx.Dialog.__init__(self, parent, title=strings.titles[self])

        self._value  = wx.SpinCtrl(        self)
        self._name   = wx.TextCtrl(        self)
        self._colour = wx.ColourPickerCtrl(self)

        self._valueLabel  = wx.StaticText(self)
        self._nameLabel   = wx.StaticText(self)
        self._colourLabel = wx.StaticText(self)

        self._ok     = wx.Button(self, id=wx.ID_OK)
        self._cancel = wx.Button(self, id=wx.ID_CANCEL)

        self._valueLabel .SetLabel(strings.labels[self, 'value'])
        self._nameLabel  .SetLabel(strings.labels[self, 'name'])
        self._colourLabel.SetLabel(strings.labels[self, 'colour'])
        self._ok         .SetLabel(strings.labels[self, 'ok'])
        self._cancel     .SetLabel(strings.labels[self, 'cancel'])
        self._name       .SetValue(strings.labels[self, 'newLabel'])
        self._value      .SetValue(0)

        self._sizer = wx.GridSizer(4, 2)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._valueLabel,  flag=wx.EXPAND)
        self._sizer.Add(self._value,       flag=wx.EXPAND)
        self._sizer.Add(self._nameLabel,   flag=wx.EXPAND)
        self._sizer.Add(self._name,        flag=wx.EXPAND)
        self._sizer.Add(self._colourLabel, flag=wx.EXPAND)
        self._sizer.Add(self._colour,      flag=wx.EXPAND)
        self._sizer.Add(self._ok,          flag=wx.EXPAND)
        self._sizer.Add(self._cancel,      flag=wx.EXPAND)

        self._ok    .Bind(wx.EVT_BUTTON, self.onOk)
        self._cancel.Bind(wx.EVT_BUTTON, self.onCancel)

        self._ok.SetDefault()

        self.Layout()
        self.Fit()
        
        self.CentreOnParent()

        self.value  = None
        self.name   = None
        self.colour = None


    def onOk(self, ev):
        self.value  = self._value .GetValue()
        self.name   = self._name  .GetValue()
        self.colour = self._colour.GetColour()

        self.EndModal(wx.ID_OK)


    def onCancel(self, ev):
        self.EndModal(wx.ID_CANCEL)
