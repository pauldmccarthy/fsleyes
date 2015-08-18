#!/usr/bin/env python
#
# overlaydisplaytoolbar.py - A toolbar which shows display control options for
#                            the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""A :class:`wx.Panel` which shows display control options for the currently
selected overlay.
"""

import logging

import wx

import props

import fsl.fsleyes.toolbar as fsltoolbar
import fsl.fsleyes.icons   as icons
import fsl.fsleyes.actions as actions
import fsl.utils.typedict  as td
import fsl.data.strings    as strings
import overlaydisplaypanel as overlaydisplay


log = logging.getLogger(__name__)



_TOOLBAR_PROPS = td.TypeDict({

    'Display' : {
        'name'         : props.Widget('name'),
        'overlayType'  : props.Widget('overlayType'),
        'alpha'        : props.Widget('alpha',
                                      spin=False,
                                      showLimits=False),
        'brightness'   : props.Widget('brightness',
                                      spin=False,
                                      showLimits=False),
        'contrast'     : props.Widget('contrast',
                                      spin=False,
                                      showLimits=False)},

    'VolumeOpts' : {
        'displayRange' : props.Widget('displayRange',
                                      slider=False,
                                      showLimits=False),
        'resetDisplayRange' : actions.ActionButton(
            'resetDisplayRange',
            icon=icons.findImageFile('verticalReset24')), 
        'cmap' : props.Widget('cmap')},

    
    'MaskOpts' : {
        'threshold' : props.Widget('threshold', showLimits=False, spin=False),
        'colour'    : props.Widget('colour', size=(24, 24))},

    'LabelOpts' : {
        'lut'     : props.Widget('lut'),
        'outline' : props.Widget(
            'outline',
            icon=[icons.findImageFile('outline24'),
                  icons.findImageFile('filled24')],
            toggle=True,
            enabledWhen=lambda i, sw: not sw,
            dependencies=[(lambda o: o.display, 'softwareMode')]),
        
        'outlineWidth' : props.Widget(
            'outlineWidth',
            enabledWhen=lambda i, sw: not sw,
            dependencies=[(lambda o: o.display, 'softwareMode')],
            showLimits=False,
            spin=False)},

    'RGBVectorOpts' : {
        'modulate'     : props.Widget('modulate'),
        'modThreshold' : props.Widget('modThreshold',
                                      showLimits=False,
                                      spin=False)},

    'LineVectorOpts' : {
        'modulate'     : props.Widget('modulate'),
        'modThreshold' : props.Widget('modThreshold',
                                      showLimits=False,
                                      spin=False), 
        'lineWidth' : props.Widget('lineWidth', showLimits=False, spin=False),
    },

    'ModelOpts' : {
        'colour'       : props.Widget('colour', size=(24, 24)),
        'outline'      : props.Widget(
            'outline',
            icon=[icons.findImageFile('outline24'),
                  icons.findImageFile('filled24')],
            toggle=True),
        'outlineWidth' : props.Widget(
            'outlineWidth',
            showLimits=False,
            spin=False,
            enabledWhen=lambda i: i.outline)}
})


class OverlayDisplayToolBar(fsltoolbar.FSLEyesToolBar):
    
    def __init__(self, parent, overlayList, displayCtx, viewPanel):

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
        """Deregisters property listeners. """

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
        self.__viewPanel.togglePanel(overlaydisplay.OverlayDisplayPanel,
                                     floatPane=True)

        
    def __overlayEnableChanged(self, *a):
        display = self._displayCtx.getDisplay(self.__currentOverlay)
        self.Enable(display.enabled)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay`
        index changes. Ensures that the correct display panel is visible.
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
        """
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
        """
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
        """
        """
        thresSpec  = _TOOLBAR_PROPS[opts]['threshold']
        colourSpec = _TOOLBAR_PROPS[opts]['colour']

        thresWidget  = props.buildGUI(self, opts, thresSpec)
        colourWidget = props.buildGUI(self, opts, colourSpec)

        return [thresWidget, colourWidget]


    def __makeLabelOptsTools(self, opts):
        """
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
        return self.__makeVectorOptsTools(opts)

    
    def __makeLineVectorOptsTools(self, opts):
        widthSpec = _TOOLBAR_PROPS[opts]['lineWidth']

        widget = props.buildGUI(self, opts, widthSpec)
        widget = self.MakeLabelledTool(widget,
                                       strings.properties[opts, 'lineWidth'])

        return self.__makeVectorOptsTools(opts) + [widget]


    def __makeModelOptsTools(self, opts):
        colourSpec  = _TOOLBAR_PROPS[opts]['colour']
        outlineSpec = _TOOLBAR_PROPS[opts]['outline']
        widthSpec   = _TOOLBAR_PROPS[opts]['outlineWidth']

        colourWidget  = props.buildGUI(self, opts, colourSpec)
        outlineWidget = props.buildGUI(self, opts, outlineSpec)
        widthWidget   = props.buildGUI(self, opts, widthSpec)

        widthWidget  = self.MakeLabelledTool(
            widthWidget, strings.properties[opts, 'outlineWidth'])
        return [colourWidget, outlineWidget, widthWidget]


    def __showTools(self, overlay):

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
                'more', icon=icons.findImageFile('gear24')))

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
