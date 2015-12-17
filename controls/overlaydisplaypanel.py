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

    An ``OverlayDisplayPanel`` uses a :class:`.WidgetList` to organise the
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

        dispProps = _DISPLAY_PROPS.get(target, [])
        labels    = [strings.properties.get((target, p.key), p.key)
                     for p in dispProps]
        tooltips  = [fsltooltips.properties.get((target, p.key), None)
                     for p in dispProps]

        widgets = []

        for p in dispProps:

            widget = props.buildGUI(self.__widgets, target, p)

            # Build a panel for the VolumeOpts colour map controls.
            if isinstance(target, displayctx.VolumeOpts) and p.key == 'cmap':
                widget = self.__buildColourMapWidget(target, widget)
                
            widgets.append(widget)

        for label, tooltip, widget in zip(labels, tooltips, widgets):
            self.__widgets.AddWidget(
                widget,
                label,
                tooltip=tooltip, 
                groupName=groupName)

        self.Layout()


    def __buildColourMapWidget(self, target, cmapWidget):
        """Builds a panel which contains widgets for controlling the
        :attr:`.VolumeOpts.cmap`, :attr:`.VolumeOpts.negativeCmap`, and
        :attr:`.VolumeOpts.useNegativeCmap`.
        """

        widgets = self.__widgets

        # Button to load a new
        # colour map from file
        loadAction = loadcmap.LoadColourMapAction(self._displayCtx,
                                                  self._overlayList)

        loadButton = wx.Button(widgets)
        loadButton.SetLabel(strings.labels[self, 'loadCmap'])

        loadAction.bindToWidget(self, wx.EVT_BUTTON, loadButton)

        # Negative colour map widget
        negCmap    = props.Widget('negativeCmap',
                                  enabledWhen=lambda i, enc: enc,
                                  dependencies=['useNegativeCmap'])
        useNegCmap = props.Widget('useNegativeCmap')
        
        negCmap    = props.buildGUI(widgets, target, negCmap)
        useNegCmap = props.buildGUI(widgets, target, useNegCmap)

        useNegCmap.SetLabel(strings.properties[target, 'useNegativeCmap'])

        sizer = wx.FlexGridSizer(2, 2)
        sizer.AddGrowableCol(0)

        sizer.Add(cmapWidget, flag=wx.EXPAND)
        sizer.Add(loadButton, flag=wx.EXPAND)
        sizer.Add(negCmap,    flag=wx.EXPAND)
        sizer.Add(useNegCmap, flag=wx.EXPAND)
        
        return sizer


def _imageName(img):
    """Used to generate choice labels for the :attr`.VectorOpts.modulateImage`,
    :attr`.VectorOpts.clipImage` and :attr:`.ModelOpts.refImage` properties.
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
        props.Widget('linkLowRanges'),
        props.Widget('linkHighRanges'),
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
        props.Widget('interpolation',
                     labels=strings.choices['VolumeOpts.interpolation']),
        props.Widget('xColour'),
        props.Widget('yColour'),
        props.Widget('zColour'),
        props.Widget('suppressX'),
        props.Widget('suppressY'),
        props.Widget('suppressZ'),
        props.Widget('modulateImage', labels=_imageName),
        props.Widget('clipImage',     labels=_imageName),
        props.Widget('clippingRange',
                     showLimits=False,
                     slider=True,
                     labels=[strings.choices['VectorOpts.clippingRange.min'],
                             strings.choices['VectorOpts.clippingRange.max']],
                     dependencies=['clipImage'],
                     enabledWhen=lambda o, ci: ci is not None)],

    'LineVectorOpts' : [
        props.Widget('resolution', showLimits=False),
        props.Widget('xColour'),
        props.Widget('yColour'),
        props.Widget('zColour'),
        props.Widget('suppressX'),
        props.Widget('suppressY'),
        props.Widget('suppressZ'),
        props.Widget('directed'),
        props.Widget('lineWidth', showLimits=False),
        props.Widget('modulateImage', labels=_imageName),
        props.Widget('clipImage',     labels=_imageName),
        props.Widget('clippingRange',
                     showLimits=False,
                     slider=True,
                     labels=[strings.choices['VectorOpts.clippingRange.min'],
                             strings.choices['VectorOpts.clippingRange.max']],
                     dependencies=['clipImage'],
                     enabledWhen=lambda o, ci: ci is not None)],

    'ModelOpts' : [
        props.Widget('colour'),
        props.Widget('outline'),
        props.Widget('outlineWidth', showLimits=False),
        props.Widget('refImage', labels=_imageName),
        # props.Widget('showName'),
        props.Widget('coordSpace',
                     enabledWhen=lambda o, ri: ri != 'none',
                     dependencies=['refImage'])],

    'TensorOpts' : [
        props.Widget('lighting'),
        props.Widget(
            'tensorResolution',
            showLimits=False,
            spin=False,
            labels=[strings.choices['TensorOpts.tensorResolution.min'],
                    strings.choices['TensorOpts.tensorResolution.max']]),
        props.Widget('tensorScale', showLimits=False, spin=False),
        props.Widget('xColour'),
        props.Widget('yColour'),
        props.Widget('zColour'),
        props.Widget('suppressX'),
        props.Widget('suppressY'),
        props.Widget('suppressZ'),
        props.Widget('modulateImage', labels=_imageName),
        props.Widget('clipImage',     labels=_imageName),
        props.Widget('clippingRange',
                     showLimits=False,
                     slider=True,
                     labels=[strings.choices['VectorOpts.clippingRange.min'],
                             strings.choices['VectorOpts.clippingRange.max']],
                     dependencies=['clipImage'],
                     enabledWhen=lambda o, ci: ci is not None)],

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
