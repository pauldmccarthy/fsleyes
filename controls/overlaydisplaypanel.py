#!/usr/bin/env python
#
# overlaydisplaypanel.py - The OverlayDisplayPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides the :class:`OverlayDisplayPanel` class, a *FSLeyes
control* panel which allows the user to change overlay display settings.
"""


import logging

import wx
import props

import pwidgets.widgetlist               as widgetlist

import fsl.utils.typedict                as td
import fsl.data.strings                  as strings
import fsl.fsleyes.tooltips              as fsltooltips
import fsl.fsleyes.panel                 as fslpanel
import fsl.fsleyes.actions.loadcolourmap as loadcmap
import fsl.fsleyes.displaycontext        as displayctx


log = logging.getLogger(__name__)

    
class OverlayDisplayPanel(fslpanel.FSLEyesPanel):
    """The ``OverlayDisplayPanel`` is a :Class:`.FSLEyesPanel` which allows
    the user to change the display settings of the currently selected
    overlay (which is defined by the :attr:`.DisplayContext.selectedOverlay`
    property). The display settings for an overlay are contained in the
    :class:`.Display` and :class:`.DisplayOpts` instances associated with
    that overlay. An ``OverlayDisplayPanel`` looks something like the
    following:

    .. image:: images/overlaydisplaypanel.png
       :scale: 50%
       :align: center

    An ``OverlayDisplayPanel`` uses a :class:`.WidgetGrid` to organise the
    settings into two main sections:

      - Settings which are common across all overlays - these are defined
        in the :class:`.Display` class.
    
      - Settings which are specific to the current
        :attr:`.Display.overlayType` - these are defined in the
        :class:`.DisplayOpts` sub-classes.

    
    The settings that are displayed on an ``OverlayDisplayPanel`` are
    defined in the :attr:`_DISPLAY_PROPS` dictionary.
    """

    
    def __init__(self, parent, overlayList, displayCtx):
        """Create an ``OverlayDisplayPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__overlayName = wx.StaticText(self, style=wx.ALIGN_CENTRE)
        self.__widgets     = widgetlist.WidgetList(self)
        self.__sizer       = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__overlayName, flag=wx.EXPAND)
        self.__sizer.Add(self.__widgets,     flag=wx.EXPAND, proportion=1)

        displayCtx .addListener('selectedOverlay',
                                 self._name,
                                 self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                 self._name,
                                 self.__selectedOverlayChanged)

        self.__currentOverlay = None
        self.__selectedOverlayChanged()

        self.Layout()
        self.SetMinSize((100, 50))

        
    def destroy(self):
        """Must be called when this ``OverlayDisplayPanel`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.FSLEyesPanel.destroy` method.
        """

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:
            
            display = self._displayCtx.getDisplay(self.__currentOverlay)
            
            display.removeListener('overlayType', self._name)
            display.removeListener('name',        self._name)

        self.__currentOverlay = None
        fslpanel.FSLEyesPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes. Refreshes this
        ``OverlayDisplayPanel`` so that the display settings for the newly
        selected overlay are shown.
        """

        overlay     = self._displayCtx.getSelectedOverlay()
        lastOverlay = self.__currentOverlay

        if overlay is None:
            self.__currentOverlay = None
            self.__overlayName.SetLabel('')
            self.__widgets.Clear()
            self.Layout()
            return

        if overlay is lastOverlay:
            return

        self.__currentOverlay = overlay

        if lastOverlay is not None and \
           lastOverlay in self._overlayList:
            
            lastDisplay = self._displayCtx.getDisplay(lastOverlay)
            
            lastDisplay.removeListener('overlayType', self._name)
            lastDisplay.removeListener('name',        self._name)

        if lastOverlay is not None:
            displayExpanded = self.__widgets.IsExpanded('display')
            optsExpanded    = self.__widgets.IsExpanded('opts')
        else:
            displayExpanded = True
            optsExpanded    = True

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()
            
        display.addListener('overlayType', self._name, self.__ovlTypeChanged)
        display.addListener('name',        self._name, self.__ovlNameChanged) 
        
        self.__widgets.Clear()
        self.__widgets.AddGroup('display', strings.labels[self, display])
        self.__widgets.AddGroup('opts',    strings.labels[self, opts]) 

        self.__overlayName.SetLabel(display.name)
        self.__updateWidgets(display, 'display')
        self.__updateWidgets(opts,    'opts')

        self.__widgets.Expand('display', displayExpanded)
        self.__widgets.Expand('opts',    optsExpanded)
        
        self.Layout()

        
    def __ovlNameChanged(self, *a):
        """Called when the :attr:`.Display.name` of the current overlay
        changes. Updates the text label at the top of this
        ``OverlayDisplayPanel``.
        """
        
        display = self._displayCtx.getDisplay(self.__currentOverlay)
        self.__overlayName.SetLabel(display.name)
        self.Layout()
        

    def __ovlTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` of the current overlay
        changes. Refreshes the :class:`.DisplayOpts` settings which are shown,
        as a new :class:`.DisplayOpts` instance will have been created for the
        overlay.
        """

        opts = self._displayCtx.getOpts(self.__currentOverlay)
        self.__updateWidgets(opts, 'opts')
        self.Layout()
        

    def __updateWidgets(self, target, groupName):
        """Called by the :meth:`__selectedOverlayChanged` and
        :meth:`__ovlTypeChanged` methods. Re-creates the controls on this
        ``OverlayDisplayPanel`` for the specified group.

        :arg target:    A :class:`.Display` or :class:`.DisplayOpts` instance,
                        which contains the properties that controls are to be
                        created for.

        :arg groupName: Either ``'display'`` or ``'opts'``, corresponding
                        to :class:`.Display` or :class:`.DisplayOpts`
                        properties.
        """

        self.__widgets.ClearGroup(groupName)

        dispProps = _DISPLAY_PROPS[target]
        labels    = [strings.properties[target, p.key] for p in dispProps]
        tooltips  = [fsltooltips.properties.get((target, p.key), None)
                     for p in dispProps]

        widgets = []

        for p in dispProps:

            widget = props.buildGUI(self.__widgets,
                                    target,
                                    p,
                                    showUnlink=False)            

            # Add a 'load colour map' button next 
            # to the VolumeOpts.cmap control
            if isinstance(target, displayctx.VolumeOpts) and \
               p.key == 'cmap':
                widget = self.__buildColourMapWidget(widget)
                
            widgets.append(widget)

        for label, tooltip, widget in zip(labels, tooltips, widgets):
            self.__widgets.AddWidget(
                widget,
                label,
                tooltip=tooltip, 
                groupName=groupName)

        self.Layout()


    def __buildColourMapWidget(self, cmapWidget):
        """Creates a control which allows the user to load a custom colour
        map. This control is added to the settings for :class:`.Image`
        overlays with a :attr:`.Display.overlayType`  of ``'volume'``.
        """

        action = loadcmap.LoadColourMapAction(self._displayCtx,
                                              self._overlayList)

        button = wx.Button(self.__widgets)
        button.SetLabel(strings.labels[self, 'loadCmap'])

        action.bindToWidget(self, wx.EVT_BUTTON, button)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(cmapWidget, flag=wx.EXPAND, proportion=1)
        sizer.Add(button,     flag=wx.EXPAND)
        
        return sizer


def _imageName(img):
    """Used to generate choice labels for the :attr`.VectorOpts.modulate` and
    :attr:`.ModelOpts.refImage` properties.
    """
    if img is None: return 'None'
    else:           return img.name


_DISPLAY_PROPS = td.TypeDict({
    'Display' : [
        props.Widget('name'),
        props.Widget('overlayType',
                     labels=strings.choices['Display.overlayType']),
        props.Widget('enabled'),
        props.Widget('alpha',      showLimits=False),
        props.Widget('brightness', showLimits=False),
        props.Widget('contrast',   showLimits=False)],

    'VolumeOpts' : [
        props.Widget('resolution',    showLimits=False),
        props.Widget('volume',
                     showLimits=False,
                     enabledWhen=lambda o: o.overlay.is4DImage()),
        props.Widget('interpolation',
                     labels=strings.choices['VolumeOpts.interpolation']),
        props.Widget('cmap'),
        props.Widget('invert'),
        props.Widget('invertClipping'),
        props.Widget('displayRange',
                     showLimits=False,
                     slider=True,
                     labels=[strings.choices['VolumeOpts.displayRange.min'],
                             strings.choices['VolumeOpts.displayRange.max']]),
        props.Widget('clippingRange',
                     showLimits=False,
                     slider=True,
                     labels=[strings.choices['VolumeOpts.displayRange.min'],
                             strings.choices['VolumeOpts.displayRange.max']])],

    'MaskOpts' : [
        props.Widget('resolution', showLimits=False),
        props.Widget('volume',
                     showLimits=False,
                     enabledWhen=lambda o: o.overlay.is4DImage()),
        props.Widget('colour'),
        props.Widget('invert'),
        props.Widget('threshold',  showLimits=False)],

    'RGBVectorOpts' : [
        props.Widget('resolution', showLimits=False),
        props.Widget('interpolation'),
        props.Widget('xColour'),
        props.Widget('yColour'),
        props.Widget('zColour'),
        props.Widget('suppressX'),
        props.Widget('suppressY'),
        props.Widget('suppressZ'),
        props.Widget('modulate', labels=_imageName),
        props.Widget('modThreshold', showLimits=False, spin=False)],

    'LineVectorOpts' : [
        props.Widget('resolution',    showLimits=False),
        props.Widget('xColour'),
        props.Widget('yColour'),
        props.Widget('zColour'),
        props.Widget('suppressX'),
        props.Widget('suppressY'),
        props.Widget('suppressZ'),
        props.Widget('directed'),
        props.Widget('lineWidth', showLimits=False),
        props.Widget('modulate', labels=_imageName),
        props.Widget('modThreshold', showLimits=False, spin=False)],

    'ModelOpts' : [
        props.Widget('colour'),
        props.Widget('outline'),
        props.Widget('outlineWidth', showLimits=False),
        props.Widget('refImage', labels=_imageName),
        # props.Widget('showName'),
        props.Widget('coordSpace',
                     enabledWhen=lambda o, ri: ri != 'none',
                     dependencies=['refImage'])],

    'LabelOpts' : [
        props.Widget('lut', labels=lambda l: l.name),
        props.Widget('outline'),
        props.Widget('outlineWidth', showLimits=False),
        # props.Widget('showNames'),
        props.Widget('resolution',   showLimits=False),
        props.Widget('volume',
                     showLimits=False,
                     enabledWhen=lambda o: o.overlay.is4DImage())]
})
"""This dictionary contains specifications for all controls that are shown on
an ``OverlayDisplayPanel``.
"""
