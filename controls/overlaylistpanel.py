#!/usr/bin/env python
#
# overlaylistpanel.py - The OverlayListPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the ``OverlayListPanel``, a *FSLeyes control* which
displays a list of all overlays currently in the :class:`.OverlayList`.
"""


import logging

import wx

import props

import pwidgets.elistbox as elistbox

import fsl.fsleyes.panel as fslpanel
import fsl.fsleyes.icons as icons
import fsl.data.image    as fslimage


log = logging.getLogger(__name__)


class OverlayListPanel(fslpanel.FSLEyesPanel):
    """The ``OverlayListPanel`` displays all overlays in the
    :class:`.OverlayList`, and allows the user to add, remove, and re-order
    overlays. An ``OverlayListPanel`` looks something like this:

    .. image:: images/overlaylistpanel.png
       :scale: 50%
       :align: center

    
    A :class:`ListItemWidget` is displayed alongside every overlay in the
    list - this allows the user to enable/disable, group, and save each
    overlay.

    The ``OverlayListPanel`` is closely coupled to a few
    :class:`.DisplayContext` properties: the
    :attr:`.DisplayContext.selectedOverlay` property is linked to the currently
    selected item in the overlay list, and the order in which the overlays are
    shown is defined by the :attr:`.DisplayContext.overlayOrder` property. This
    property is updated when the user changes the order of items in the list.
    """

    
    def __init__(self, parent, overlayList, displayCtx):
        """Create an ``OverlayListPanel``.

        :param parent:      The :mod:`wx` parent object.
        :param overlayList: An :class:`.OverlayList` instance.
        :param displayCtx:  A :class:`.DisplayContext` instance.
        """
        
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        # list box containing the list of overlays - it 
        # is populated in the _overlayListChanged method
        self.__listBox = elistbox.EditableListBox(
            self,
            style=(elistbox.ELB_REVERSE | 
                   elistbox.ELB_TOOLTIP))

        # listeners for when the user does
        # something with the list box
        self.__listBox.Bind(elistbox.EVT_ELB_SELECT_EVENT,   self.__lbSelect)
        self.__listBox.Bind(elistbox.EVT_ELB_MOVE_EVENT,     self.__lbMove)
        self.__listBox.Bind(elistbox.EVT_ELB_REMOVE_EVENT,   self.__lbRemove)
        self.__listBox.Bind(elistbox.EVT_ELB_ADD_EVENT,      self.__lbAdd)
        self.__listBox.Bind(elistbox.EVT_ELB_DBLCLICK_EVENT, self.__lbDblClick)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__listBox, flag=wx.EXPAND, proportion=1)

        self._overlayList.addListener(
            'overlays',
            self._name,
            self.__overlayListChanged)
        
        self._displayCtx.addListener(
            'overlayOrder',
            self._name,
            self.__overlayListChanged) 

        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self.__selectedOverlayChanged)

        self.__overlayListChanged()
        self.__selectedOverlayChanged()

        self.Layout()

        self.SetMinSize(self.__sizer.GetMinSize())


    def destroy(self):
        """Must be called when this ``OverlayListPanel`` is no longer needed.
        Removes some property listeners, and calls
        :meth:`.FSLEyesPanel.destroy`.
        """
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('overlayOrder',    self._name)

        # A listener on name was added 
        # in the _overlayListChanged method
        for overlay in self._overlayList:
            display = self._displayCtx.getDisplay(overlay)
            display.removeListener('name', self._name)
            
        fslpanel.FSLEyesPanel.destroy(self)

        
    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` property
        changes. Updates the selected item in the list box.
        """

        if len(self._overlayList) > 0:
            self.__listBox.SetSelection(
                self._displayCtx.getOverlayOrder(
                    self._displayCtx.selectedOverlay))


    def __overlayNameChanged(self, value, valid, display, propName):
        """Called when the :attr:`.Display.name` of an overlay changes. Updates
        the corresponding label in the overlay list.
        """

        overlay = display.getOverlay()
        idx     = self._displayCtx.getOverlayOrder(overlay)
        name    = display.name
        
        if name is None:
            name = ''
            
        self.__listBox.SetItemLabel(idx, name) 

        
    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.  All of the items
        in the overlay list are re-created.
        """
        
        self.__listBox.Clear()

        for i, overlay in enumerate(self._displayCtx.getOrderedOverlays()):

            display  = self._displayCtx.getDisplay(overlay)
            name     = display.name
            if name is None: name = ''

            tooltip = overlay.dataSource
            
            self.__listBox.Append(name, overlay, tooltip)

            widget = ListItemWidget(self,
                                    overlay,
                                    display,
                                    self._displayCtx,
                                    self.__listBox)

            self.__listBox.SetItemWidget(i, widget)

            display.addListener('name',
                                self._name,
                                self.__overlayNameChanged,
                                overwrite=True)

        if len(self._overlayList) > 0:
            self.__listBox.SetSelection(
                self._displayCtx.getOverlayOrder(
                    self._displayCtx.selectedOverlay))
        
        
    def __lbMove(self, ev):
        """Called when an overlay is moved in the :class:`.EditableListBox`.
        Reorders the :attr:`.DisplayContext.overlayOrder` to reflect the
        change.
        """
        self._displayCtx.disableListener('overlayOrder', self._name)
        self._displayCtx.overlayOrder.move(ev.oldIdx, ev.newIdx)
        self._displayCtx.enableListener('overlayOrder', self._name)

        
    def __lbSelect(self, ev):
        """Called when an overlay is selected in the
        :class:`.EditableListBox`. Updates the
        :attr:`.DisplayContext.selectedOverlay` property.
        """
        self._displayCtx.disableListener('selectedOverlay', self._name)
        self._displayCtx.selectedOverlay = \
            self._displayCtx.overlayOrder[ev.idx]
        self._displayCtx.enableListener('selectedOverlay', self._name)

        
    def __lbAdd(self, ev):
        """Called when the *add* button on the list box is pressed.
        Calls the :meth:`.OverlayList.addOverlays` method.
        """
        if self._overlayList.addOverlays():
            self._displayCtx.selectedOverlay = len(self._overlayList) - 1


    def __lbRemove(self, ev):
        """Called when an item is removed from the overlay listbox.
        Removes the corresponding overlay from the :class:`.OverlayList`.
        """
        self._overlayList.pop(self._displayCtx.overlayOrder[ev.idx])


    def __lbDblClick(self, ev):
        """Called when an item label is double clicked on the overlay list
        box. Toggles the visibility of the overlay, via the
        :attr:`.Display.enabled` property..
        """
        idx             = self._displayCtx.overlayOrder[ev.idx]
        overlay         = self._overlayList[idx]
        display         = self._displayCtx.getDisplay(overlay)
        display.enabled = not display.enabled


class ListItemWidget(wx.Panel):
    """A ``LisItemWidget`` is created by the :class:`OverlayListPanel` for
    every overlay in the :class:`.OverlayList`. A ``LisItemWidget`` contains
    controls which allow the user to:

     - Toggle the visibility of the overlay (via the :attr:`.Display.enabled`
       property)

     - Add the overlay to a group (see the
       :attr:`.DisplayContext.overlayGroups` property, and the :mod:`.group`
       module).

     - Save the overlay (if it has been modified).

    .. note:: While the :class:`.DisplayContext` allows multiple
              :class:`.OverlayGroup` instances to be defined (and added to its
              :attr:`.DisplayContext.overlayGroups` property), *FSLeyes*
              currently only defines a single group . This ``OverlayGroup``
              is created in the :func:`.fsleyes.context` function, and overlays
              can be added/removed to/from it via the *lock* button on a
              ``ListItemWidget``. This functionality might change in a future
              version of *FSLeyes*.


    .. note:: Currently, only :class:`.Image` overlays can be saved. The *save*
              button is disabled for all other overlay types.
    """

    
    enabledFG  = '#000000'
    """This colour is used as the foreground (text) colour for overlays
    where their :attr:`.Display.enabled` property is ``True``.
    """

    
    disabledFG = '#CCCCCC'
    """This colour is used as the foreground (text) colour for overlays
    where their :attr:`.Display.enabled` property is ``False``.
    """ 

    
    unsavedDefaultBG = '#ffaaaa'
    """This colour is used as the default background colour for
    :class:`.Image` overlays with an :attr:`.Image.saved` property
    of ``False``.
    """

    
    unsavedSelectedBG = '#aa4444'
    """This colour is used as the background colour for :class:`.Image`
    overlays with an :attr:`.Image.saved` property of ``False``, when
    they are selected in the :class:`OverlayListPanel`.
    """ 

    
    def __init__(self, parent, overlay, display, displayCtx, listBox):
        """Create a ``ListItemWidget``.

        :arg parent:     The :mod:`wx` parent object.
        :arg overlay:    The overlay associated with this ``ListItemWidget``.
        :arg display:    The :class:`.Display` associated with the overlay.
        :arg displayCtx: The :class:`.DisplayContext` instance.
        :arg listBox:    The :class:`.EditableListBox` that contains this
                         ``ListItemWidget``.
        """
        wx.Panel.__init__(self, parent)

        self.__overlay    = overlay
        self.__display    = display
        self.__displayCtx = displayCtx
        self.__listBox    = listBox
        self.__name       = '{}_{}'.format(self.__class__.__name__, id(self))

        # BU_NOTEXT causes a segmentation fault under OSX
        if wx.Platform == '__WXMAC__': btnStyle = wx.BU_EXACTFIT
        else:                          btnStyle = wx.BU_EXACTFIT | wx.BU_NOTEXT

        self.__saveButton = wx.Button(      self, style=btnStyle)
        self.__lockButton = wx.ToggleButton(self, style=btnStyle)

        self.__saveButton.SetBitmap(icons.loadBitmap('floppydisk16'))
        self.__lockButton.SetBitmap(icons.loadBitmap('chainlink16'))
        
        self.__visibility = props.makeWidget(
            self,
            display,
            'enabled',
            icon=icons.findImageFile('eye16'))

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__saveButton, flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__lockButton, flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__visibility, flag=wx.EXPAND, proportion=1)

        # There is currently only one overlay
        # group in the application. In the
        # future there may be multiple groups.
        group = displayCtx.overlayGroups[0]

        display.addListener('enabled',
                            self.__name,
                            self.__vizChanged)
        group  .addListener('overlays',
                            self.__name,
                            self.__overlayGroupChanged)
        
        if isinstance(overlay, fslimage.Image):
            overlay.addListener('saved', self.__name, self.__saveStateChanged)
        else:
            self.__saveButton.Enable(False)

        self.__saveButton.Bind(wx.EVT_BUTTON,         self.__onSaveButton)
        self.__lockButton.Bind(wx.EVT_TOGGLEBUTTON,   self.__onLockButton)
        self             .Bind(wx.EVT_WINDOW_DESTROY, self.__onDestroy)

        self.__overlayGroupChanged()
        self.__vizChanged()
        self.__saveStateChanged()


    def __overlayGroupChanged(self, *a):
        """Called when the :class:`.OverlayGroup` changes. Updates the *lock*
        button based on whether the overlay associated with this
        ``ListItemWidget`` is in the group or not.
        """
        group = self.__displayCtx.overlayGroups[0]
        self.__lockButton.SetValue(self.__overlay in group.overlays)

        
    def __onSaveButton(self, ev):
        """Called when the *save* button is pushed. Calls the
        :meth:`.Image.save` method.
        """
        self.__displayCtx.selectOverlay(self.__overlay)
        self.__overlay.save()


    def __onLockButton(self, ev):
        """Called when the *lock* button is pushed. Adds/removes the overlay
        to/from the :class:`.OverlayGroup`.
        """
        self.__displayCtx.selectOverlay(self.__overlay)
        group = self.__displayCtx.overlayGroups[0]
        
        if self.__lockButton.GetValue(): group.addOverlay(   self.__overlay)
        else:                            group.removeOverlay(self.__overlay)

        
    def __onDestroy(self, ev):
        """Called when this ``ListItemWidget`` is destroyed (i.e. when the
        associated overlay is removed from the :class:`OverlayListPanel`).
        Removes some proprety listeners from the :class:`.Display` and
        :class:`.OverlayGroup` instances, and from the overlay if it is an
        :class:`.Image` instance.
        """
        ev.Skip()
        if ev.GetEventObject() is not self:
            return

        group = self.__displayCtx.overlayGroups[0]

        self.__display.removeListener('enabled',  self.__name)
        group         .removeListener('overlays', self.__name)

        if isinstance(self.__overlay, fslimage.Image):
            self.__overlay.removeListener('saved', self.__name)

        
    def __saveStateChanged(self, *a):
        """If the overlay is an :class:`.Image` instance, this method is
        called when its :attr:`.Image.saved` property changes. Updates the
        state of the *save* button.
        """

        if not isinstance(self.__overlay, fslimage.Image):
            return
        
        idx = self.__listBox.IndexOf(self.__overlay)
        
        self.__saveButton.Enable(not self.__overlay.saved)

        if self.__overlay.saved:
            self.__listBox.SetItemBackgroundColour(idx)
            
        else:
            self.__listBox.SetItemBackgroundColour(
                idx,
                ListItemWidget.unsavedDefaultBG,
                ListItemWidget.unsavedSelectedBG),

            
    def __vizChanged(self, *a):
        """Called when the :attr:`.Display.enabled` property of the overlay
        changes. Updates the state of the *enabled* buton, and changes the
        item foreground colour.
        """
        self.__displayCtx.selectOverlay(self.__overlay)

        idx = self.__listBox.IndexOf(self.__overlay)

        if self.__display.enabled: fgColour = ListItemWidget.enabledFG
        else:                      fgColour = ListItemWidget.disabledFG

        self.__listBox.SetItemForegroundColour(idx, fgColour)
