#!/usr/bin/env python
#
# lookuptablepanel.py - The LookupTablePanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LookupTablePanel`, a *FSLeyes control*
panel which allows the user to manage lookup tables. See the
:mod:`.colourmaps` module for more details on lookup tables.

A few other class are defined in this module, all for use by the
``LookupTablePanel``:

.. autosummary::
   :nosignatures:

   LabelWidget
   NewLutDialog
   LutLabelDialog
"""


import os
import logging

import wx

import numpy as np

import pwidgets.elistbox          as elistbox

import fsl.fsleyes.panel          as fslpanel
import fsl.fsleyes.displaycontext as displayctx
import fsl.fsleyes.colourmaps     as fslcmaps
import fsl.data.strings           as strings
import fsl.data.melodicimage      as fslmelimage


log = logging.getLogger(__name__)


class LookupTablePanel(fslpanel.FSLEyesPanel):
    """A ``LookupTablePanel`` is a :class:`.FLSEyesPanel` which allows users
    to manage ``LookupTable`` instances. A ``LookupTablePanel`` looks
    something like this:

    .. image:: images/lookuptablepanel.png
       :scale: 50%
       :align: center

    
    A ``LookupTablePanel`` allows the user to do the following:
    
      - Add/remove labels to/from a :class:`LookupTable`.
    
      - Change the colour, name, and visibility of a label in a
        ``LookupTable``.
    
      - Create a new ``LookupTable``, or copy an existing one.

      - Save/load a ``LookupTable`` to/from a file.

    
    The ``LookupTablePanel`` keeps track of the currently selected overlay
    (see the :attr:`.DisplayContext.selectedOverlay` property). If the overlay
    is associated with a :class:`.LabelOpts` instance, its
    :attr:`.Labelopts.lut` property will be updated when the
    :class:`LookupTable` is changed through the ``LookupTablePanel``, and vice
    versa.
    """ 
    

    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``LookupTablePanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """ 

        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__controlCol = wx.Panel(self)
        self.__labelList  = elistbox.EditableListBox(
            self, style=(elistbox.ELB_NO_MOVE   |
                         elistbox.ELB_NO_ADD    |
                         elistbox.ELB_NO_REMOVE |
                         elistbox.ELB_EDITABLE))

        self.__lutChoice       = wx.Choice(self.__controlCol)
        self.__addLabelButton  = wx.Button(self.__controlCol)
        self.__rmLabelButton   = wx.Button(self.__controlCol)
        self.__newLutButton    = wx.Button(self.__controlCol)
        self.__copyLutButton   = wx.Button(self.__controlCol)
        self.__saveLutButton   = wx.Button(self.__controlCol)
        self.__loadLutButton   = wx.Button(self.__controlCol)

        self.__controlColSizer = wx.BoxSizer(wx.VERTICAL)
        self.__sizer           = wx.BoxSizer(wx.HORIZONTAL)

        self.__controlCol.SetSizer(self.__controlColSizer)
        self             .SetSizer(self.__sizer)

        self.__controlColSizer.Add(self.__lutChoice,      flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__addLabelButton, flag=wx.EXPAND) 
        self.__controlColSizer.Add(self.__rmLabelButton,  flag=wx.EXPAND) 
        self.__controlColSizer.Add(self.__newLutButton,   flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__copyLutButton,  flag=wx.EXPAND) 
        self.__controlColSizer.Add(self.__loadLutButton,  flag=wx.EXPAND)
        self.__controlColSizer.Add(self.__saveLutButton,  flag=wx.EXPAND)

        self.__sizer.Add(self.__controlCol, flag=wx.EXPAND)
        self.__sizer.Add(self.__labelList,  flag=wx.EXPAND, proportion=1)

        # Label the buttons
        self.__addLabelButton.SetLabel(strings.labels[  self, 'addLabel'])
        self.__rmLabelButton .SetLabel(strings.labels[  self, 'removeLabel'])
        self.__newLutButton  .SetLabel(strings.labels[  self, 'newLut'])
        self.__copyLutButton .SetLabel(strings.labels[  self, 'copyLut'])
        self.__loadLutButton .SetLabel(strings.labels[  self, 'loadLut'])
        self.__saveLutButton .SetLabel(strings.labels[  self, 'saveLut'])

        self.__labelList.Bind(elistbox.EVT_ELB_EDIT_EVENT, self.__onLabelEdit)

        self.__lutChoice     .Bind(wx.EVT_CHOICE, self.__onLutChoice)
        self.__addLabelButton.Bind(wx.EVT_BUTTON, self.__onLabelAdd)
        self.__rmLabelButton .Bind(wx.EVT_BUTTON, self.__onLabelRemove) 
        self.__newLutButton  .Bind(wx.EVT_BUTTON, self.__onNewLut)
        self.__copyLutButton .Bind(wx.EVT_BUTTON, self.__onCopyLut)
        self.__loadLutButton .Bind(wx.EVT_BUTTON, self.__onLoadLut)
        self.__saveLutButton .Bind(wx.EVT_BUTTON, self.__onSaveLut)

        self.__selectedOverlay = None
        self.__selectedOpts    = None
        self.__selectedLut     = None

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__updateLutChoices()
        self.__selectedOverlayChanged()

        # If the selected lut was not set
        # via the selectedOverlayChanged
        # call, we'll manually set it here
        if self.__selectedLut is None:
            self.__setLut(fslcmaps.getLookupTables()[0])
            
        self.Layout()
        self.SetMinSize(self.__sizer.GetMinSize())

        
    def destroy(self):
        """Must be called when this ``LookupTablePanel`` is no longer needed.
        Removes some property listeners, and calls the
        :meth:`FSLEyesPanel.destroy` method.
        """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        overlay = self.__selectedOverlay
        opts    = self.__selectedOpts
        lut     = self.__selectedLut

        if overlay is not None and overlay in self._overlayList:

            display = self._displayCtx.getDisplay(overlay)
            display.removeListener('overlayType', self._name)

        if opts is not None:
            opts.removeListener('lut', self._name)

        if lut is not None:
            lut.removeListener('labels', self._name)
            lut.removeListener('saved',  self._name)

        self.__selectedOverlay = None
        self.__selectedOpts    = None
        self.__selectedLut     = None

        fslpanel.FSLEyesPanel.destroy(self)

        
    def __updateLutChoices(self):
        """Refreshes the contents of the lookup table drop down box,
        using the :class:`.LookupTable` instances returned by the
        :func:`.colourmaps.getLookupTables` function.
        """

        log.debug('Updating lookup table choices')        

        oldNames     = self.__lutChoice.GetItems()
        oldSelection = self.__lutChoice.GetSelection()

        luts     = fslcmaps.getLookupTables()
        newNames = [l.name for l in luts]

        try:    newSelection = oldNames.index(oldNames[oldSelection])
        except: newSelection = 0

        self.__lutChoice.SetItems(newNames)
        self.__lutChoice.SetSelection(newSelection)

        for i, lut in enumerate(luts):
            self.__lutChoice.SetClientData(i, lut)

        
    def __createLabelList(self):
        """Refreshes the contents of the class:`.LookupTable` label list, from
        the :attr:`.LookupTable.labels` property of the currently selected
        ``LookupTable``.
        """

        log.debug('Creating lookup table label list')

        self.__labelList.Clear()

        lut = self.__selectedLut

        for i, label in enumerate(lut.labels):

            self.__labelList.Append(label.displayName())

            widget = LabelWidget(self, lut, label.value())
            self.__labelList.SetItemWidget(i, widget)


    def __setLut(self, lut):
        """Updates this ``LookupTablePanel`` to display the labels for the
        given ``lut`` (assumed to be a :class:`.LookupTable` instance).
 
        If the currently selected overlay is associated with a
        :class:`.LabelOpts` instance, its :attr:`.LabelOpts.lut` property is
        set to the new ``LookupTable``.
        """

        log.debug('Selecting lut: {}'.format(lut))

        if self.__selectedLut is not None:
            self.__selectedLut.removeListener('labels', self._name)
            self.__selectedLut.removeListener('saved',  self._name)
        
        self.__selectedLut = lut

        if lut is not None:
            lut.addListener('labels', self._name, self.__lutLabelsChanged)
            lut.addListener('saved',  self._name, self.__lutSaveStateChanged)

        if lut is not None and self.__selectedOpts is not None:
            self.__selectedOpts.disableListener('lut', self._name)
            self.__selectedOpts.lut = lut
            self.__selectedOpts.enableListener('lut', self._name)

        allLuts = fslcmaps.getLookupTables()
        
        self.__lutChoice.SetSelection(allLuts.index(lut))
        
        self.__lutSaveStateChanged()
        self.__createLabelList()

        
    def __lutSaveStateChanged(self, *a):
        """Called when the :attr:`.LookupTable.saved` property of the
        current :class:`LookupTable` instance changes. Sets the state
        of the *save* button accordingly.
        """
        print 'Updating save state ({})'.format(self.__selectedLut.saved)
        self.__saveLutButton.Enable(not self.__selectedLut.saved)


    def __lutLabelsChanged(self, *a):
        """Called when the :attr:`.LookupTable.labels` property of the current
        :class:`LookupTable` instance changes. Updates the list of displayed
        labels (see the :meth:`__createLabelList` method).
        """
        self.__createLabelList()


    def __onLutChoice(self, ev):
        """Called when the user changes the selected :class:`.LookupTable`
        via the lookup table drop down box. See the :meth:`__setLut` method..
        """

        selection = self.__lutChoice.GetSelection()
        lut       = self.__lutChoice.GetClientData(selection)

        log.debug('Lut choice: {}'.format(lut))

        self.__setLut(lut)


    def __onNewLut(self, ev):
        """Called when the user presses the *New LUT* button. Displays a
        :class:`NewLutDialog`, prompting the user to enter a name, and then
        creates and registers a new :class:`.LookupTable` instance. Updates
        this ``LookupTablePanel`` via the :meth:`__updateLutChoices` and
        :meth:`__setLut` methods.
        """

        dlg = NewLutDialog(self.GetTopLevelParent())
        if dlg.ShowModal() != wx.ID_OK:
            return

        name = dlg.GetName()

        log.debug('Creating and registering new '
                  'LookupTable: {}'.format(name))

        lut = fslcmaps.LookupTable(name)
        fslcmaps.registerLookupTable(lut, self._overlayList, self._displayCtx)

        self.__updateLutChoices()
        self.__setLut(lut)


    def __onCopyLut(self, ev):
        """Called when the user presses the *Copy LUT* button.  Displays a
        :class:`NewLutDialog`, prompting the user to enter a name, and then
        creates and registers a new :class:`.LookupTable` instance which is
        initialised with the same label as the previously selected
        ``LookupTable``. Updates this ``LookupTablePanel`` via the
        :meth:`__updateLutChoices` and :meth:`__setLut` methods.
        """

        oldName = self.__selectedLut.name
        dlg     = NewLutDialog(self.GetTopLevelParent(), oldName)
        
        if dlg.ShowModal() != wx.ID_OK:
            return

        newName = dlg.GetName()

        log.debug('Creating and registering new '
                  'LookupTable {} (copied from {})'.format(newName, oldName))

        lut = fslcmaps.LookupTable(newName)

        for label in self.__selectedLut.labels:
            lut.set(label.value(),
                    name=label.displayName(),
                    colour=label.colour(),
                    enabled=label.enabled())
        
        fslcmaps.registerLookupTable(lut, self._overlayList, self._displayCtx)

        self.__updateLutChoices()
        self.__setLut(lut)

        
    def __onLoadLut(self, ev):
        """Called when the user presses the *Load LUT* button.  Displays a
        :class:`NewLutDialog`, prompting the user to enter a name, and then a
        ``wx.FileDialog`, prompting the user to select a file containing
        lookup table information.  Then creates and registers a new
        :class:`.LookupTable` instance, initialising it with the selected
        file. Updates this ``LookupTablePanel`` via the
        :meth:`__updateLutChoices` and :meth:`__setLut` methods.

        See the :mod:`.colourmaps` module for more details on the file format.
        """ 

        nameDlg = NewLutDialog(self.GetTopLevelParent())
        
        if nameDlg.ShowModal() != wx.ID_OK:
            return
        
        fileDlg = wx.FileDialog(wx.GetApp().GetTopWindow(),
                                message=strings.titles[self, 'loadLut'],
                                defaultDir=os.getcwd(),
                                style=wx.FD_OPEN)

        if fileDlg.ShowModal() != wx.ID_OK:
            return

        name = nameDlg.GetName()
        path = fileDlg.GetPath()

        lut = fslcmaps.registerLookupTable(path,
                                           self._overlayList,
                                           self._displayCtx,
                                           name)

        self.__updateLutChoices()
        self.__setLut(lut)
        
    
    def __onSaveLut(self, ev):
        """Called when the user presses the *Save LUT* button. Makes sure
        that the current :class:`LookupTable` is saved (see the
        :func:`.colourmaps.installLookupTable` function).
        """
        fslcmaps.installLookupTable(self.__selectedLut.key)

    
    def __onLabelAdd(self, ev):
        """Called when the user pushes the *add* button on the lookup table
        label list. Displays a :class:`LutLabelDialog`, prompting the user
        to select a name, value and colour, and then adds a new label to the
        current :class:`.LookupTable` instance.
        """

        lut    = self.__selectedLut
        value  = lut.max() + 1
        name   = strings.labels['LutLabelDialog.newLabel']
        colour = fslcmaps.randomBrightColour()
        colour = [int(round(c * 255.0)) for c in colour]

        dlg = LutLabelDialog(self.GetTopLevelParent(), value, name, colour)
        if dlg.ShowModal() != wx.ID_OK:
            return

        lut    = self.__selectedLut
        value  = dlg.GetValue()
        name   = dlg.GetName()
        colour = dlg.GetColour()[:3]
        colour = [c / 255.0 for c in colour]

        if lut.get(value) is not None:
            wx.MessageBox(
                strings.messages[self, 'labelExists'].format(lut.name, value),
                strings.titles[  self, 'labelExists'], (wx.ICON_INFORMATION |
                                                        wx.OK))
            return

        log.debug('New lut label for {}: {}, {}, {}'.format(
            lut.name,
            value,
            name,
            colour))

        lut.set(value, name=name, colour=colour)

    
    def __onLabelRemove(self, ev):
        """Called when the user pushes the *remove* button on the lookup
        table label list. Removes the selected label from the current
        :class:`.LookupTable`.
        """

        idx   = self.__labelList.GetSelection()
        lut   = self.__selectedLut
        value = lut.labels[idx].value()

        lut.disableListener('labels', self._name)
        lut.delete(value)
        self.__labelList.Delete(idx)
        lut.enableListener('labels', self._name)


    def __onLabelEdit(self, ev):
        """Called when the user edits the name of a label in the lookup
        table label list. Updates the corresponding lookup table label via
        the :meth:`.LookupTable.set` method.
        """

        lut = self.__selectedLut
        value = lut.labels[ev.idx].value()

        lut.disableListener('labels', self._name)
        lut.set(value, name=ev.label)
        lut.enableListener('labels', self._name)
        
    
    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes.  Refreshes the
        ``LookupTablePanel`` accordingly.
        """

        newOverlay = self._displayCtx.getSelectedOverlay()

        if self.__selectedOverlay is not None and \
           self.__selectedOverlay in self._overlayList:
            
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('overlayType', self._name)

        self.__selectedOverlay = newOverlay

        if newOverlay is not None:
            
            display = self._displayCtx.getDisplay(newOverlay)
            display.addListener('overlayType',
                                self._name,
                                self.__overlayTypeChanged)

        self.__overlayTypeChanged()
        

    def __overlayTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` property of the
        currently selected overlay changes. If the :class:`.DisplayOpts`
        instance associated with the new overlay type is a
        :class:`.LabelOpts`, a listener is addd to its ``lut`` property.
        """

        if self.__selectedOpts is not None:
            self.__selectedOpts.removeListener('lut', self._name)
            self.__selectedOpts = None

        overlay = self.__selectedOverlay
        opts    = None

        if overlay is None:
            return

        opts = self._displayCtx.getOpts(overlay)

        if not isinstance(opts, displayctx.LabelOpts):

            # If the image is a Melodic image, show
            # the melodic classification lut
            if isinstance(overlay, fslmelimage.MelodicImage):
                self.__setLut(fslcmaps.getLookupTable('melodic-classes'))
                
            return

        opts.addListener('lut', self._name, self.__lutChanged)
        
        self.__selectedOpts = opts
        self.__lutChanged()
        self.Layout()


    def __lutChanged(self, *a):
        """Called when the :attr:`.LabelOpts.lut` property associated
        with the currently selected overlay changes. Changes the
        :class:~.LookupTable` displayed  on this ``LookupTablePanel`` (see
        the  :meth:`__setLut` method).
        """
        self.__setLut(self.__selectedOpts.lut)
            

class LabelWidget(wx.Panel):
    """A ``LabelWidget`` is shown for each label of the :class:`.LookupTable`
    which is currently displayed on a :class:`LookupTablePanel`. A
    ``LabelWidget`` allows the user to change the colour and visibility of the
    label value.
    """

    
    def __init__(self, lutPanel, lut, value):
        """Create a ``LabelWidget``.

        :arg lutPanel: The :class:`LookupTablePanel` that is displaying this
                       ``LabelWidget``.
        
        :arg lut:      The :class:`.LookupTable` currently being displayed.
        
        :arg value:    The label value that this ``LabelWidget`` is associated
                       with.
        """
        wx.Panel.__init__(self, lutPanel)

        self.__lutPanel = lutPanel
        self.__lut      = lut
        self.__value    = value

        # TODO Change the enable box to a toggle
        #      button with an eye icon
        
        self.__valueLabel   = wx.StaticText(self,
                                            style=wx.ALIGN_CENTRE_VERTICAL |
                                            wx.ALIGN_RIGHT)
        self.__enableBox    = wx.CheckBox(self)
        self.__colourButton = wx.ColourPickerCtrl(self)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__valueLabel,
                         flag=wx.ALIGN_CENTRE,
                         proportion=1)
        self.__sizer.Add(self.__enableBox,
                         flag=wx.ALIGN_CENTRE,
                         proportion=1)
        self.__sizer.Add(self.__colourButton,
                         flag=wx.ALIGN_CENTRE,
                         proportion=1)

        label  = lut.get(value)
        colour = [np.floor(c * 255.0) for c in label.colour()]

        self.__valueLabel  .SetLabel(str(value))
        self.__colourButton.SetColour(colour)
        self.__enableBox   .SetValue(label.enabled())

        self.__enableBox   .Bind(wx.EVT_CHECKBOX,             self.__onEnable)
        self.__colourButton.Bind(wx.EVT_COLOURPICKER_CHANGED, self.__onColour)

        
    def __onEnable(self, ev):
        """Called when the user toggles the checkbox controlling label
        visibility. Updates the label visibility via the
        :meth:`.LookupTable.set` method.
        """

        # Disable the LutPanel listener, otherwise
        # it will recreate the label list (see
        # LookupTablePanel._createLabelList)
        self.__lut.disableListener('labels', self.__lutPanel._name)
        self.__lut.set(self.__value, enabled=self.__enableBox.GetValue())
        self.__lut.enableListener('labels', self.__lutPanel._name)

        
    def __onColour(self, ev):
        """Called when the user changes the colour via the colour button.
        Updates the label colour via the :meth:`.LookupTable.set` method.
        """ 

        newColour = self.__colourButton.GetColour()
        newColour = [c / 255.0 for c in newColour]

        # See comment in __onEnable 
        self.__lut.disableListener('labels', self.__lutPanel._name)
        self.__lut.set(self.__value, colour=newColour)
        self.__lut.enableListener('labels', self.__lutPanel._name)

        
class NewLutDialog(wx.Dialog):
    """A dialog which is displayed when the user chooses to create a new
    :class:`.LookupTable`.

    Prompts the user to enter a name for the new ``LookupTable``. The entered
    name will be accessible via the :meth:`GetName` method after the user
    dismisses the dialog.
    """
    
    def __init__(self, parent, name=None):
        """Create a ``NewLutDialog``.

        :arg parent: The :mod:`wx` parent object.

        :arg name:   Initial name to display.
        """

        if name is None:
            name = strings.labels[self, 'newLut']

        wx.Dialog.__init__(self, parent, title=strings.titles[self])

        self.__message = wx.StaticText(self)
        self.__name    = wx.TextCtrl(  self)
        self.__ok      = wx.Button(    self, id=wx.ID_OK)
        self.__cancel  = wx.Button(    self, id=wx.ID_CANCEL)

        self.__message.SetLabel(strings.messages[self, 'newLut'])
        self.__ok     .SetLabel(strings.labels[  self, 'ok'])
        self.__cancel .SetLabel(strings.labels[  self, 'cancel'])
        self.__name   .SetValue(name)

        self.__sizer    = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__message,  flag=wx.EXPAND | wx.ALL, border=10)
        self.__sizer.Add(self.__name,     flag=wx.EXPAND | wx.ALL, border=10)
        self.__sizer.Add(self.__btnSizer, flag=wx.EXPAND)
        
        self.__btnSizer.Add(self.__ok,       flag=wx.EXPAND, proportion=1)
        self.__btnSizer.Add(self.__cancel,   flag=wx.EXPAND, proportion=1)

        self.__ok    .Bind(wx.EVT_BUTTON, self.__onOk)
        self.__cancel.Bind(wx.EVT_BUTTON, self.__onCancel)

        self.__ok.SetDefault()
        
        self.Fit()
        self.Layout()

        self.CentreOnParent()

        self.__enteredName = None


    def GetName(self):
        """Returns the name that the user entered. Returns ``None`` if the
        user dismissed this ``NewLutDialog``, or this method has been called
        before the dialog is dismissed.
        """
        return self.__enteredName

    
    def __onOk(self, ev):
        """Called when the user confirms the dialog. Saves the name that the 
        user entered, and closes the dialog.
        """
        self.__enteredName = self._name.GetValue()
        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the user cancels the dialog. Closes the dialog.
        """ 
        self.EndModal(wx.ID_CANCEL)
 

class LutLabelDialog(wx.Dialog):
    """A dialog which is displayed when the user adds a new label to the
    :class:`.LookupTable` currently displayed in the
    :class:`LookupTablePanel`.

    Prompts the user to enter a label value, name, and colour. After the
    dialog is dismissed, the entered information is available via the
    following methods:

    .. autosummary::
       :nosignatures:
    
       GetValue    
       GetName
       GetColour
    """

    
    def __init__(self, parent, value, name, colour):
        """Create a ``LutLabelDialog``.

        :arg parent: The :mod:`wx` paren object.
        """

        wx.Dialog.__init__(self, parent, title=strings.titles[self])

        self.__value  = wx.SpinCtrl(        self)
        self.__name   = wx.TextCtrl(        self)
        self.__colour = wx.ColourPickerCtrl(self)

        self.__valueLabel  = wx.StaticText(self)
        self.__nameLabel   = wx.StaticText(self)
        self.__colourLabel = wx.StaticText(self)

        self.__ok     = wx.Button(self, id=wx.ID_OK)
        self.__cancel = wx.Button(self, id=wx.ID_CANCEL)

        self.__valueLabel .SetLabel(strings.labels[self, 'value'])
        self.__nameLabel  .SetLabel(strings.labels[self, 'name'])
        self.__colourLabel.SetLabel(strings.labels[self, 'colour'])
        self.__ok         .SetLabel(strings.labels[self, 'ok'])
        self.__cancel     .SetLabel(strings.labels[self, 'cancel'])

        self.__value      .SetValue( value)
        self.__name       .SetValue( name)
        self.__colour     .SetColour(colour)

        self.__sizer = wx.GridSizer(4, 2)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__valueLabel,  flag=wx.EXPAND)
        self.__sizer.Add(self.__value,       flag=wx.EXPAND)
        self.__sizer.Add(self.__nameLabel,   flag=wx.EXPAND)
        self.__sizer.Add(self.__name,        flag=wx.EXPAND)
        self.__sizer.Add(self.__colourLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__colour,      flag=wx.EXPAND)
        self.__sizer.Add(self.__ok,          flag=wx.EXPAND)
        self.__sizer.Add(self.__cancel,      flag=wx.EXPAND)

        self.__ok    .Bind(wx.EVT_BUTTON, self.__onOk)
        self.__cancel.Bind(wx.EVT_BUTTON, self.__onCancel)

        self.__ok.SetDefault()

        self.Layout()
        self.Fit()
        
        self.CentreOnParent()

        self.__enteredValue  = None
        self.__enteredName   = None
        self.__enteredColour = None

        
    def GetValue(self):
        """Returns the value that was entered by the user. Or, returns
        ``None`` if  the user cancelled the dialog, or the dialog has not
        yet been closed.
        """
        return self.__enteredValue

    
    def GetName(self):
        """Returns the name that was entered by the user. Or, returns
        ``None`` if  the user cancelled the dialog, or the dialog has not
        yet been closed.
        """ 
        return self.__enteredName

    
    def GetColour(self):
        """Returns the colour that was entered by the user. Or, returns
        ``None`` if  the user cancelled the dialog, or the dialog has not
        yet been closed.
        """ 
        return self.__enteredColour  

    
    def __onOk(self, ev):
        """Called when the user confirms the dialog. Saves the name, colour,
        and value that were entered, and closes the dialog.
        """
        self.__enteredValue  = self.__value .GetValue()
        self.__enteredName   = self.__name  .GetValue()
        self.__enteredColour = self.__colour.GetColour()

        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the user cancells the dialog. Closes the dialog."""
        
        self.EndModal(wx.ID_CANCEL)
