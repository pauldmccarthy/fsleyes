#!/usr/bin/env python
#
# overlaydisplaytoolbar.py - The OverlayDisplayToolBar.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides the :class:`OverlyDisplyaToolBar`, a
:class:`.FSLEyesToolBar` containing controls for changing the display settings
of the currently selected overlay.
"""


import logging

import wx

import props

import fsl.fsleyes.toolbar  as fsltoolbar
import fsl.fsleyes.icons    as icons
import fsl.fsleyes.tooltips as fsltooltips
import fsl.fsleyes.actions  as actions
import fsl.utils.typedict   as td
import fsl.data.strings     as strings
import overlaydisplaypanel  as overlaydisplay


log = logging.getLogger(__name__)


class OverlayDisplayToolBar(fsltoolbar.FSLEyesToolBar):
    """The ``OverlyDisplyaToolBar`` is a :class:`.FSLEyesToolBar` containing
    controls which allow the user to change the display settings of the
    currently selected overlay (as defined by the
    :attr:`.DisplayContext.selectedOverlay` property). The display settings
    for an overlay are contained in the :class:`.Display` and
    :class:`.DisplayOpts` instances that are associated with that overlay.
    

    An ``OverlyDisplyaToolBar`` looks something like the following:

    .. image:: images/overlaydisplaytoolbar.png
       :scale: 50%
       :align: center

    
    The ``OverlayDisplayToolBar`` also defines an action called ``more``
    (which is linked to the :meth:`showMoreSettings` method), which opens an
    :class:`.OverlayDisplayPanel`.


    The specific controls which are displayed are defined in the
    :attr:`_TOOLBAR_PROPS` dictionary, and are created by the following
    methods:

    .. autosummary::
       :nosignatures:

       __makeDisplayTools
       __makeVolumeOptsTools
       __makeMaskOptsTools
       __makeLabelOptsTools
       __makeVectorOptsTools
       __makeRGBVectorOptsTools
       __makeLineVectorOptsTools
       __makeModelOptsTools
    """
    
    def __init__(self, parent, overlayList, displayCtx, viewPanel):
        """Create an ``OverlyDisplyaToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList` instance.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg viewPanel:   The :class:`.ViewPanel` which this
                          ``OverlayDisplayToolBar`` is owned by.
        """

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLEyesToolBar.__init__(
            self, parent, overlayList, displayCtx, 24, actionz)

        self.__viewPanel      = viewPanel
        self.__currentOverlay = None

        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self.__selectedOverlayChanged)
        self._overlayList.addListener(
            'overlays',
            self._name,
            self.__selectedOverlayChanged) 

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``OverlyDisplyaToolBar`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.FSLEyesToolBar.destroy` method.
        """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:

            display = self._displayCtx.getDisplay(self.__currentOverlay)
            display.removeListener('overlayType', self._name)
            display.removeListener('enabled',     self._name)

        self.__currentOverlay = None
        self.__viewPanel      = None
            
        fsltoolbar.FSLEyesToolBar.destroy(self)


    def showMoreSettings(self, *a):
        """Shows/hides a :class:`.OverlayDisplayPanel` dialog. """
        self.__viewPanel.togglePanel(overlaydisplay.OverlayDisplayPanel,
                                     floatPane=True)


    def __showTools(self, overlay):
        """Creates and shows a set of controls allowing the user to change
        the display settings of the specified ``overlay``.
        """

        oldTools = self.GetTools()

        # See long comment at bottom
        def destroyOldTools():
            for t in oldTools:
                t.Destroy()

        for t in oldTools:
            t.Show(False)

        self.ClearTools(destroy=False, postevent=False)

        log.debug('Showing tools for {}'.format(overlay))

        display   = self._displayCtx.getDisplay(overlay)
        opts      = display.getDisplayOpts()

        # Display tools
        tools     = self.__makeDisplayTools(display)

        # DisplayOpts tools
        makeFunc = getattr(self, '_{}__make{}Tools'.format(
            type(self).__name__, type(opts).__name__), None)

        if makeFunc is not None:
            tools.extend(makeFunc(opts))

        # Button which opens the OverlayDisplayPanel
        more = props.buildGUI(
            self,
            self,
            view=actions.ActionButton(
                'more',
                icon=icons.findImageFile('gear24'),
                tooltip=fsltooltips.actions[self, 'more']))

        tools.insert(0, more)

        self.SetTools(tools)
        
        # This method may have been called via an
        # event handler an existing tool in the
        # toolbar - in this situation, destroying
        # that tool will result in nasty crashes,
        # as the wx widget that generated the event
        # will be destroyed while said event is
        # being processed. So we destroy the old
        # tools asynchronously, well after the event
        # which triggered this method call will have
        # returned.
        wx.CallLater(1000, destroyOldTools)

        
    def __overlayEnableChanged(self, *a):
        """Called when the :attr:`.Display.enabled` property for the currently
        selected overlay changes. Enables/disables this
        ``OverlayDisplayToolBar`` accordingly.
        """
        display = self._displayCtx.getDisplay(self.__currentOverlay)
        self.Enable(display.enabled)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` changes. Ensures that controls for the currently
        selected overlay are being shown.
        """

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:
            display = self._displayCtx.getDisplay(self.__currentOverlay)
            display.removeListener('overlayType', self._name)
            display.removeListener('enabled',     self._name)

        overlay = self._displayCtx.getSelectedOverlay()

        self.__currentOverlay = overlay

        if overlay is None:
            self.ClearTools(destroy=True)
            return

        display = self._displayCtx.getDisplay(overlay)

        display.addListener('enabled',
                            self._name,
                            self.__overlayEnableChanged)
        display.addListener('overlayType',
                            self._name,
                            self.__selectedOverlayChanged)

        self.__showTools(overlay)
        self.Enable(display.enabled)


    def __makeDisplayTools(self, display):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.Display` instance.
        """
        
        dispSpecs = _TOOLBAR_PROPS[display]

        # Display settings
        nameSpec  = dispSpecs['name']
        typeSpec  = dispSpecs['overlayType']
        alphaSpec = dispSpecs['alpha']
        briSpec   = dispSpecs['brightness']
        conSpec   = dispSpecs['contrast']

        # Name/overlay type and brightness/contrast
        # are respectively placed together
        nameTypePanel = wx.Panel(self)
        briconPanel   = wx.Panel(self)
        nameTypeSizer = wx.BoxSizer(wx.VERTICAL)
        briconSizer   = wx.FlexGridSizer(2, 2)
        
        briconSizer.AddGrowableCol(1)

        nameTypePanel.SetSizer(nameTypeSizer)
        briconPanel  .SetSizer(briconSizer)

        nameWidget  = props.buildGUI(nameTypePanel, display, nameSpec)
        typeWidget  = props.buildGUI(nameTypePanel, display, typeSpec)
        briWidget   = props.buildGUI(briconPanel,   display, briSpec)
        conWidget   = props.buildGUI(briconPanel,   display, conSpec)
        alphaWidget = props.buildGUI(self,          display, alphaSpec)

        briLabel    = wx.StaticText(briconPanel)
        conLabel    = wx.StaticText(briconPanel)

        briLabel.SetLabel(strings.properties[display, 'brightness'])
        conLabel.SetLabel(strings.properties[display, 'contrast'])

        # name/type panel
        nameTypeSizer.Add(nameWidget, flag=wx.EXPAND)
        nameTypeSizer.Add(typeWidget, flag=wx.EXPAND)

        # opacity is given a label
        alphaPanel = self.MakeLabelledTool(
            alphaWidget, strings.properties[display, 'alpha'])

        # bricon panel
        briconSizer.Add(briLabel)
        briconSizer.Add(briWidget)
        briconSizer.Add(conLabel)
        briconSizer.Add(conWidget)

        return [nameTypePanel, alphaPanel, briconPanel]


    def __makeVolumeOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.VolumeOpts` instance.
        """
        rangeSpec = _TOOLBAR_PROPS[opts]['displayRange']
        resetSpec = _TOOLBAR_PROPS[opts]['resetDisplayRange']
        cmapSpec  = _TOOLBAR_PROPS[opts]['cmap']

        rangeWidget = props.buildGUI(self, opts, rangeSpec)
        resetWidget = props.buildGUI(self, opts, resetSpec)
        cmapWidget  = props.buildGUI(self, opts, cmapSpec)

        cmapWidget = self.MakeLabelledTool(
            cmapWidget,
            strings.properties[opts, 'cmap'])

        return [rangeWidget, resetWidget, cmapWidget]


    def __makeMaskOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.MaskOpts` instance.
        """ 
        thresSpec  = _TOOLBAR_PROPS[opts]['threshold']
        colourSpec = _TOOLBAR_PROPS[opts]['colour']

        thresWidget  = props.buildGUI(self, opts, thresSpec)
        colourWidget = props.buildGUI(self, opts, colourSpec)

        return [thresWidget, colourWidget]


    def __makeLabelOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.LabelOpts` instance.
        """        

        lutSpec     = _TOOLBAR_PROPS[opts]['lut']
        outlineSpec = _TOOLBAR_PROPS[opts]['outline']
        widthSpec   = _TOOLBAR_PROPS[opts]['outlineWidth']

        # lut/outline width widgets
        # are on a single panel
        lutWidthPanel = wx.Panel(self)
        lutWidthSizer = wx.FlexGridSizer(2, 2)
        lutWidthPanel.SetSizer(lutWidthSizer)
        
        lutWidget     = props.buildGUI(lutWidthPanel, opts, lutSpec)
        widthWidget   = props.buildGUI(lutWidthPanel, opts, widthSpec)
        outlineWidget = props.buildGUI(self,          opts, outlineSpec)

        # lutWidget = self.MakeLabelledTool(
        #     lutWidget, strings.properties[opts, 'lut'])

        lutLabel   = wx.StaticText(lutWidthPanel)
        widthLabel = wx.StaticText(lutWidthPanel)

        lutLabel  .SetLabel(strings.properties[opts, 'lut'])
        widthLabel.SetLabel(strings.properties[opts, 'outlineWidth'])

        lutWidthSizer.Add(lutLabel)
        lutWidthSizer.Add(lutWidget,   flag=wx.EXPAND)
        lutWidthSizer.Add(widthLabel)
        lutWidthSizer.Add(widthWidget, flag=wx.EXPAND)

        return [lutWidthPanel, outlineWidget]


    def __makeVectorOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.VectorOpts` instance.
        """        
        
        modSpec   = _TOOLBAR_PROPS[opts]['modulate']
        thresSpec = _TOOLBAR_PROPS[opts]['modThreshold']

        panel = wx.Panel(self)
        sizer = wx.FlexGridSizer(2, 2)
        panel.SetSizer(sizer)

        modWidget   = props.buildGUI(panel, opts, modSpec)
        thresWidget = props.buildGUI(panel, opts, thresSpec)
        modLabel    = wx.StaticText(panel)
        thresLabel  = wx.StaticText(panel)

        modLabel  .SetLabel(strings.properties[opts, 'modulate'])
        thresLabel.SetLabel(strings.properties[opts, 'modThreshold'])

        sizer.Add(modLabel)
        sizer.Add(modWidget,   flag=wx.EXPAND)
        sizer.Add(thresLabel)
        sizer.Add(thresWidget, flag=wx.EXPAND)

        return [panel]

    def __makeRGBVectorOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.RGBVectorOpts` instance.
        """        
        return self.__makeVectorOptsTools(opts)

    
    def __makeLineVectorOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.LineVectorOpts` instance.
        """        
        widthSpec = _TOOLBAR_PROPS[opts]['lineWidth']

        widget = props.buildGUI(self, opts, widthSpec)
        widget = self.MakeLabelledTool(widget,
                                       strings.properties[opts, 'lineWidth'])

        return self.__makeVectorOptsTools(opts) + [widget]


    def __makeModelOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.ModelOpts` instance.
        """        
        colourSpec  = _TOOLBAR_PROPS[opts]['colour']
        outlineSpec = _TOOLBAR_PROPS[opts]['outline']
        widthSpec   = _TOOLBAR_PROPS[opts]['outlineWidth']

        colourWidget  = props.buildGUI(self, opts, colourSpec)
        outlineWidget = props.buildGUI(self, opts, outlineSpec)
        widthWidget   = props.buildGUI(self, opts, widthSpec)

        widthWidget  = self.MakeLabelledTool(
            widthWidget, strings.properties[opts, 'outlineWidth'])
        return [colourWidget, outlineWidget, widthWidget]


def _modImageLabel(img):
    """Used to generate labels for the :attr:`.VectorOpts.modulate`
    property choices.
    """
    if img is None: return strings.choices['VectorOpts.modulate.none']
    else:           return img.name

    
_TOOLTIPS = td.TypeDict({

    'Display.name'        : fsltooltips.properties['Display.name'],
    'Display.overlayType' : fsltooltips.properties['Display.overlayType'],
    'Display.alpha'       : fsltooltips.properties['Display.alpha'],
    'Display.brightness'  : fsltooltips.properties['Display.brightness'],
    'Display.contrast'    : fsltooltips.properties['Display.contrast'],

    'VolumeOpts.displayRange'      : fsltooltips.properties['VolumeOpts.'
                                                            'displayRange'],
    'VolumeOpts.resetDisplayRange' : fsltooltips.actions[   'VolumeOpts.reset'
                                                            'DisplayRange'],
    'VolumeOpts.cmap'              : fsltooltips.properties['VolumeOpts.cmap'],

    'MaskOpts.threshold' : fsltooltips.properties['MaskOpts.threshold'],
    'MaskOpts.colour'    : fsltooltips.properties['MaskOpts.colour'],

    'LabelOpts.lut'          : fsltooltips.properties['LabelOpts.lut'],
    'LabelOpts.outline'      : fsltooltips.properties['LabelOpts.outline'],
    'LabelOpts.outlineWidth' : fsltooltips.properties['LabelOpts.'
                                                      'outlineWidth'],

    'RGBVectorOpts.modulate'     : fsltooltips.properties['VectorOpts.'
                                                          'modulate'],
    'RGBVectorOpts.modThreshold' : fsltooltips.properties['VectorOpts.'
                                                          'modThreshold'],

    'LineVectorOpts.modulate'     : fsltooltips.properties['VectorOpts.'
                                                           'modulate'],
    'LineVectorOpts.modThreshold' : fsltooltips.properties['VectorOpts.'
                                                           'modThreshold'],
    'LineVectorOpts.lineWidth'    : fsltooltips.properties['LineVectorOpts.'
                                                           'lineWidth'],

    'ModelOpts.colour'       : fsltooltips.properties['ModelOpts.colour'],
    'ModelOpts.outline'      : fsltooltips.properties['ModelOpts.outline'],
    'ModelOpts.outlineWidth' : fsltooltips.properties['ModelOpts.'
                                                      'outlineWidth'],
})
"""This dictionary contains tooltips for :class:`.Display` and
:class:`.DisplayOpts` properties. It is referenced in the
:attr:`_TOOLBAR_PROPS` dictionary definition.
"""


_TOOLBAR_PROPS = td.TypeDict({

    'Display' : {
        'name'         : props.Widget(
            'name',
            tooltip=_TOOLTIPS['Display.name']),
        'overlayType'  : props.Widget(
            'overlayType',
            tooltip=_TOOLTIPS['Display.overlayType'],
            labels=strings.choices['Display.overlayType']),
        'alpha'        : props.Widget(
            'alpha',
            spin=False,
            showLimits=False,
            tooltip=_TOOLTIPS['Display.alpha']),
        'brightness'   : props.Widget(
            'brightness',
            spin=False,
            showLimits=False,
            tooltip=_TOOLTIPS['Display.brightness']),
        'contrast'     : props.Widget(
            'contrast',
            spin=False,
            showLimits=False,
            tooltip=_TOOLTIPS['Display.contrast'])},

    'VolumeOpts' : {
        'displayRange' : props.Widget(
            'displayRange',
            slider=False,
            showLimits=False,
            tooltip=_TOOLTIPS['VolumeOpts.displayRange'],
            labels=[strings.choices['VolumeOpts.displayRange.min'],
                    strings.choices['VolumeOpts.displayRange.max']]),
        'resetDisplayRange' : actions.ActionButton(
            'resetDisplayRange',
            icon=icons.findImageFile('verticalReset24'),
            tooltip=_TOOLTIPS['VolumeOpts.resetDisplayRange']), 
        'cmap' : props.Widget(
            'cmap',
            tooltip=_TOOLTIPS['VolumeOpts.cmap'])},

    'MaskOpts' : {
        'threshold' : props.Widget(
            'threshold',
            showLimits=False,
            spin=False,
            tooltip=_TOOLTIPS['MaskOpts.threshold']),
        'colour'    : props.Widget(
            'colour',
            size=(24, 24),
            tooltip=_TOOLTIPS['MaskOpts.colour'])},

    'LabelOpts' : {
        'lut'     : props.Widget(
            'lut',
            tooltip=_TOOLTIPS['LabelOpts.lut'],
            labels=lambda l: l.name),
        'outline' : props.Widget(
            'outline',
            tooltip=_TOOLTIPS['LabelOpts.outline'],
            icon=[icons.findImageFile('outline24'),
                  icons.findImageFile('filled24')],
            toggle=True,
            enabledWhen=lambda i, sw: not sw,
            dependencies=[(lambda o: o.display, 'softwareMode')]),
        
        'outlineWidth' : props.Widget(
            'outlineWidth',
            tooltip=_TOOLTIPS['LabelOpts.outlineWidth'],
            enabledWhen=lambda i, sw: not sw,
            dependencies=[(lambda o: o.display, 'softwareMode')],
            showLimits=False,
            spin=False)},

    'RGBVectorOpts' : {
        'modulate'     : props.Widget(
            'modulate',
            labels=_modImageLabel,
            tooltip=_TOOLTIPS['RGBVectorOpts.modulate']),
        'modThreshold' : props.Widget(
            'modThreshold',
            showLimits=False,
            spin=False,
            tooltip=_TOOLTIPS['RGBVectorOpts.modThreshold'])},

    'LineVectorOpts' : {
        'modulate'     : props.Widget(
            'modulate',
            labels=_modImageLabel,
            tooltip=_TOOLTIPS['LineVectorOpts.modulate']),
        'modThreshold' : props.Widget(
            'modThreshold',
            showLimits=False,
            spin=False,
            tooltip=_TOOLTIPS['LineVectorOpts.modThreshold']), 
        'lineWidth' : props.Widget(
            'lineWidth',
            showLimits=False,
            spin=False,
            tooltip=_TOOLTIPS['LineVectorOpts.lineWidth']),
    },

    'ModelOpts' : {
        'colour'       : props.Widget(
            'colour',
            size=(24, 24),
            tooltip=_TOOLTIPS['ModelOpts.colour']),
        'outline'      : props.Widget(
            'outline',
            tooltip=_TOOLTIPS['ModelOpts.outline'],
            icon=[icons.findImageFile('outline24'),
                  icons.findImageFile('filled24')],
            toggle=True),
        'outlineWidth' : props.Widget(
            'outlineWidth',
            showLimits=False,
            spin=False,
            tooltip=_TOOLTIPS['ModelOpts.outlineWidth'],
            enabledWhen=lambda i: i.outline)}
})
"""This dictionary defines specifications for all controls shown on an
:class:`OverlayDisplayToolBar`. 
"""
