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
import colorsys

import          wx
import numpy as np

import fsl.data.image                as fslimage
import fsl.utils.idle                as idle

import fsleyes_props                 as props
import fsleyes_widgets.bitmaptoggle  as bmptoggle
import fsleyes_widgets.elistbox      as elistbox

import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.icons                 as icons
import fsleyes.autodisplay           as autodisplay
import fsleyes.strings               as strings
import fsleyes.tooltips              as fsltooltips
import fsleyes.actions.loadoverlay   as loadoverlay
import fsleyes.actions.saveoverlay   as saveoverlay
import fsleyes.actions.removeoverlay as removeoverlay


log = logging.getLogger(__name__)


class OverlayListPanel(ctrlpanel.ControlPanel):
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


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.BOTTOM}


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 viewPanel,
                 showVis=True,
                 showGroup=True,
                 showSave=True,
                 propagateSelect=True,
                 elistboxStyle=None,
                 filterFunc=None):
        """Create an ``OverlayListPanel``.

        :arg parent:          The :mod:`wx` parent object.

        :arg overlayList:     An :class:`.OverlayList` instance.

        :arg displayCtx:      A :class:`.DisplayContext` instance.

        :arg viewPanel:       The :class:`.ViewPanel` instance.

        :arg showVis:         If ``True`` (the default), a button will be shown
                              alongside each overlay, allowing the user to
                              toggle the overlay visibility.

        :arg showGroup:       If ``True`` (the default), a button will be shown
                              alongside each overlay, allowing the user to
                              toggle overlay grouping.

        :arg showSave:        If ``True`` (the default), a button will be shown
                              alongside each overlay, allowing the user to save
                              the overlay (if it is not saved).

        :arg propagateSelect: If ``True`` (the default), when the user
                              interacts with the :class:`.ListItemWidget` for
                              an overlay which is *not* the currently selected
                              overlay, that overlay is updated to be the
                              selected overlay.

        :arg elistboxStyle:   Style flags passed through to the
                              :class:`.EditableListBox`.

        :arg filterFunc:      Function which must accept an overlay as its
                              sole argument, and return ``True`` or ``False``.
                              If this function returns ``False`` for an
                              overlay, the :class:`ListItemWidget` for that
                              overlay will be disabled.
        """

        def defaultFilter(o):
            return True

        if filterFunc is None:
            filterFunc = defaultFilter

        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, viewPanel)

        self.__showVis         = showVis
        self.__showGroup       = showGroup
        self.__showSave        = showSave
        self.__propagateSelect = propagateSelect
        self.__filterFunc      = filterFunc

        if elistboxStyle is None:
            elistboxStyle = (elistbox.ELB_REVERSE      |
                             elistbox.ELB_TOOLTIP_DOWN |
                             elistbox.ELB_SCROLL_BUTTONS)

        # list box containing the list of overlays - it
        # is populated in the _overlayListChanged method
        self.__listBox = elistbox.EditableListBox(self, style=elistboxStyle)

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

        self.overlayList.addListener(
            'overlays',
            self.name,
            self.__overlayListChanged)

        self.displayCtx.addListener(
            'overlayOrder',
            self.name,
            self.__overlayListChanged)

        self.displayCtx.addListener(
            'selectedOverlay',
            self.name,
            self.__selectedOverlayChanged)

        self.__overlayListChanged()

        self.__selectedOverlayChanged()

        self.Layout()

        self.__minSize = self.__sizer.GetMinSize()
        self.SetMinSize(self.__minSize)


    def GetMinSize(self):
        """Returns the minimum size for this ``OverlayListPanel``.

        Under Linux/GTK, the ``wx.agw.lib.aui`` layout manager seems to
        arbitrarily adjust the minimum sizes of some panels. Therefore, The
        minimum size of the ``OverlayListPanel`` is calculated in
        :meth:`__init__`, and is fixed.
        """
        return self.__minSize


    def destroy(self):
        """Must be called when this ``OverlayListPanel`` is no longer needed.
        Removes some property listeners, and calls
        :meth:`.ControlPanel.destroy`.
        """

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.displayCtx .removeListener('overlayOrder',    self.name)

        # A listener on name was added
        # in the _overlayListChanged method
        for overlay in self.overlayList:
            display = self.displayCtx.getDisplay(overlay)
            display.removeListener('name', self.name)

        self.__filterFunc = None
        self.__listBox.Clear()

        ctrlpanel.ControlPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` property
        changes. Updates the selected item in the list box.
        """

        if len(self.overlayList) > 0:
            self.__listBox.SetSelection(
                self.displayCtx.getOverlayOrder(
                    self.displayCtx.selectedOverlay))


    def __overlayNameChanged(self, value, valid, display, propName):
        """Called when the :attr:`.Display.name` of an overlay changes. Updates
        the corresponding label in the overlay list.
        """

        overlay = display.overlay
        idx     = self.displayCtx.getOverlayOrder(overlay)
        name    = display.name

        if name is None:
            name = ''

        self.__listBox.SetItemLabel(idx, name)


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.  All of the items
        in the overlay list are re-created.
        """

        self.__listBox.Clear()

        for i, overlay in enumerate(self.displayCtx.getOrderedOverlays()):

            display  = self.displayCtx.getDisplay(overlay)
            name     = display.name
            if name is None: name = ''

            self.__listBox.Append(name, overlay)

            widget = ListItemWidget(self,
                                    overlay,
                                    display,
                                    self.displayCtx,
                                    self.__listBox,
                                    showVis=self.__showVis,
                                    showGroup=self.__showGroup,
                                    showSave=self.__showSave,
                                    propagateSelect=self.__propagateSelect)

            if not self.__filterFunc(overlay):
                widget.Disable()

            self.__listBox.SetItemWidget(i, widget)

            tooltip = overlay.dataSource
            if tooltip is None:
                tooltip = strings.labels['OverlayListPanel.noDataSource']
            self.__listBox.SetItemTooltip(i, tooltip)

            display.addListener('name',
                                self.name,
                                self.__overlayNameChanged,
                                overwrite=True)

        if len(self.overlayList) > 0:
            self.__listBox.SetSelection(
                self.displayCtx.getOverlayOrder(
                    self.displayCtx.selectedOverlay))

        self.__listBox.Layout()


    def __lbMove(self, ev):
        """Called when an overlay is moved in the :class:`.EditableListBox`.
        Reorders the :attr:`.DisplayContext.overlayOrder` to reflect the
        change.
        """
        self.displayCtx.disableListener('overlayOrder', self.name)
        self.displayCtx.overlayOrder.move(ev.oldIdx, ev.newIdx)
        self.displayCtx.enableListener('overlayOrder', self.name)


    def __lbSelect(self, ev):
        """Called when an overlay is selected in the
        :class:`.EditableListBox`. Updates the
        :attr:`.DisplayContext.selectedOverlay` property.
        """


        self.displayCtx.disableListener('selectedOverlay', self.name)
        self.displayCtx.selectedOverlay = self.displayCtx.overlayOrder[ev.idx]
        self.displayCtx.enableListener('selectedOverlay', self.name)


    def __lbAdd(self, ev):
        """Called when the *add* button on the list box is pressed.
        Calls the :func:`.loadoverlay.interactiveLoadOverlays` method.
        """

        def onLoad(paths, overlays):
            if len(overlays) == 0:
                return

            self.overlayList.extend(overlays)
            self.displayCtx.selectedOverlay = len(self.overlayList) - 1

            if self.displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.overlayList,
                                            self.displayCtx)

        loadoverlay.interactiveLoadOverlays(
            onLoad=onLoad,
            inmem=self.displayCtx.loadInMemory)


    def __lbRemove(self, ev):
        """Called when an item is removed from the overlay listbox.
        Removes the corresponding overlay from the :class:`.OverlayList`.
        """

        overlay = self.displayCtx.overlayOrder[ev.idx]
        overlay = self.overlayList[overlay]

        with props.skip(self.overlayList, 'overlays',     self.name), \
             props.skip(self.displayCtx,  'overlayOrder', self.name):

            if not removeoverlay.removeOverlay(self.overlayList,
                                               self.displayCtx,
                                               overlay):
                ev.Veto()

            # The overlayListChanged method
            # must be called asynchronously,
            # otherwise it will corrupt the
            # EditableListBox state
            else:
                idle.idle(self.__overlayListChanged)


    def __lbDblClick(self, ev):
        """Called when an item label is double clicked on the overlay list
        box. Toggles the visibility of the overlay, via the
        :attr:`.Display.enabled` property..
        """
        idx             = self.displayCtx.overlayOrder[ev.idx]
        overlay         = self.overlayList[idx]
        display         = self.displayCtx.getDisplay(overlay)
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


    def __init__(self,
                 parent,
                 overlay,
                 display,
                 displayCtx,
                 listBox,
                 showVis=True,
                 showGroup=True,
                 showSave=True,
                 propagateSelect=True):
        """Create a ``ListItemWidget``.

        :arg parent:          The :mod:`wx` parent object.
        :arg overlay:         The overlay associated with this
                              ``ListItemWidget``.
        :arg display:         The :class:`.Display` associated with the
                              overlay.
        :arg displayCtx:      The :class:`.DisplayContext` instance.
        :arg listBox:         The :class:`.EditableListBox` that contains this
                              ``ListItemWidget``.
        :arg showVis:         If ``True`` (the default), a button will be shown
                              allowing the user to toggle the overlay
                              visibility.
        :arg showGroup:       If ``True`` (the default), a button will be shown
                              allowing the user to toggle overlay grouping.
        :arg showSave:        If ``True`` (the default), a button will be shown
                              allowing the user to save the overlay (if it is
                              not saved).
        :arg propagateSelect: If ``True`` (the default), when an overlay is
                              selected in the list, the
                              :attr:`.DisplayContext.selectedOverlay` is
                              updated accordingly.
        """
        wx.Panel.__init__(self, parent)

        self.enabledFG  = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
        self.disabledFG = wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT)

        # give unsaved overlays reddish colours
        isdark = False

        # GetAppearance added in wxwidgets 3.1.3 (~=wxpython 4.1.0)
        if hasattr(wx.SystemSettings, 'GetAppearance'):
            isdark = wx.SystemSettings.GetAppearance().IsDark()
        else:
            # Guess whether we have a light or dark theme
            colour = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW).Get()
            isdark = all(c < 128 for c in colour[:3])

        if isdark:
            self.unsavedDefaultBG  = '#443333'
            self.unsavedSelectedBG = '#551111'
        else:
            self.unsavedDefaultBG  = '#ffeeee'
            self.unsavedSelectedBG = '#ffcdcd'

        self.__overlay         = overlay
        self.__display         = display
        self.__displayCtx      = displayCtx
        self.__listBox         = listBox
        self.__propagateSelect = propagateSelect
        self.__name            = '{}_{}'.format(self.__class__.__name__,
                                                id(self))
        self.__sizer           = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.__sizer)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.__onDestroy)

        btnStyle = wx.BU_EXACTFIT | wx.BU_NOTEXT

        if showSave:
            self.__saveButton = wx.Button(self, style=btnStyle)
            self.__saveButton.SetBitmapLabel(icons.loadBitmap('floppydisk16'))
            self.__saveButton.SetToolTip(
                wx.ToolTip(fsltooltips.actions[self, 'save']))

            self.__sizer.Add(self.__saveButton, flag=wx.EXPAND, proportion=1)

            if isinstance(overlay, fslimage.Image):
                overlay.register(self.__name,
                                 self.__saveStateChanged,
                                 'saveState')
                self.__saveButton.Bind(wx.EVT_BUTTON, self.__onSaveButton)
            else:
                self.__saveButton.Enable(False)

            self.__saveStateChanged()

        if showGroup:
            self.__lockButton = bmptoggle.BitmapToggleButton(
                self, style=btnStyle)

            self.__lockButton.SetBitmap(
                icons.loadBitmap('chainlinkHighlight16'),
                icons.loadBitmap('chainlink16'))

            self.__lockButton.SetToolTip(
                wx.ToolTip(fsltooltips.actions[self, 'group']))

            self.__sizer.Add(self.__lockButton, flag=wx.EXPAND, proportion=1)

            # There is currently only one overlay
            # group in the application. In the
            # future there may be multiple groups.
            group = displayCtx.overlayGroups[0]

            group  .addListener('overlays',
                                self.__name,
                                self.__overlayGroupChanged)

            self.__lockButton.Bind(wx.EVT_TOGGLEBUTTON, self.__onLockButton)
            self.__overlayGroupChanged()

        # Set up the show/hide button if needed
        if showVis:
            self.__visibility = bmptoggle.BitmapToggleButton(
                self,
                trueBmp=icons.loadBitmap('eyeHighlight16'),
                falseBmp=icons.loadBitmap('eye16'),
                style=btnStyle)

            self.__visibility.SetToolTip(
                wx.ToolTip(fsltooltips.properties[display, 'enabled']))

            self.__sizer.Add(self.__visibility, flag=wx.EXPAND, proportion=1)

            display.addListener('enabled',
                                self.__name,
                                self.__displayVisChanged)

            self.__visibility.Bind(bmptoggle.EVT_BITMAP_TOGGLE,
                                   self.__onVisButton)

            self.__displayVisChanged()


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

        if self.__propagateSelect:
            self.__displayCtx.selectOverlay(self.__overlay)

        if not self.__overlay.saveState:
            saveoverlay.saveOverlay(self.__overlay, self.__display)


    def __onLockButton(self, ev):
        """Called when the *lock* button is pushed. Adds/removes the overlay
        to/from the :class:`.OverlayGroup`.
        """
        if self.__propagateSelect:
            self.__displayCtx.selectOverlay(self.__overlay)

        group = self.__displayCtx.overlayGroups[0]

        if self.__lockButton.GetValue(): group.addOverlay(   self.__overlay)
        else:                            group.removeOverlay(self.__overlay)


    def __onVisButton(self, ev):
        """Called when the *visibility* button is pushed. Toggles the overlay
        visibility.
        """

        if self.__propagateSelect:
            self.__displayCtx.selectOverlay(self.__overlay)

        idx     = self.__listBox.IndexOf(self.__overlay)
        enabled = self.__visibility.GetValue()

        with props.suppress(self.__display, 'enabled', self.__name):
            self.__display.enabled = enabled

        if enabled: fgColour = self.enabledFG
        else:       fgColour = self.disabledFG

        self.__listBox.SetItemForegroundColour(idx, fgColour)


    def __displayVisChanged(self, *a):
        """Called when the :attr:`.Display.enabled` property of the overlay
        changes. Updates the state of the *enabled* buton, and changes the
        item foreground colour.
        """

        idx = self.__listBox.IndexOf(self.__overlay)

        enabled = self.__display.enabled

        if enabled: fgColour = self.enabledFG
        else:       fgColour = self.disabledFG

        self.__visibility.SetValue(enabled)
        self.__listBox.SetItemForegroundColour(idx, fgColour)


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

        if self.__display.hasListener('enabled',  self.__name):
            self.__display.removeListener('enabled',  self.__name)

        if group.hasListener('overlays', self.__name):
            group.removeListener('overlays', self.__name)

        if isinstance(self.__overlay, fslimage.Image):

            # Notifier.deregister will ignore
            # non-existent listener de-registration
            self.__overlay.deregister(self.__name, 'saveState')


    def __saveStateChanged(self, *a):
        """If the overlay is an :class:`.Image` instance, this method is
        called when its :attr:`.Image.saved` property changes. Updates the
        state of the *save* button.
        """

        if not isinstance(self.__overlay, fslimage.Image):
            return

        idx = self.__listBox.IndexOf(self.__overlay)

        self.__saveButton.Enable(not self.__overlay.saveState)

        if self.__overlay.saveState:
            self.__listBox.SetItemBackgroundColour(idx)

        else:
            self.__listBox.SetItemBackgroundColour(
                idx,
                self.unsavedDefaultBG,
                self.unsavedSelectedBG),

        tooltip = self.__overlay.dataSource
        if tooltip is None:
            tooltip = strings.labels['OverlayListPanel.noDataSource']
        self.__listBox.SetItemTooltip(idx, tooltip)
