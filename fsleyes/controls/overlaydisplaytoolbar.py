#!/usr/bin/env python
#
# overlaydisplaytoolbar.py - The OverlayDisplayToolBar.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides the :class:`OverlyDisplyaToolBar`, a
:class:`.ControlToolBar` containing controls for changing the display settings
of the currently selected overlay.
"""


import            logging
import os.path as op

import wx

import fsleyes_props                  as props
import fsleyes_widgets                as fwidgets
import fsleyes_widgets.utils.typedict as td
import fsleyes.controls.controlpanel  as ctrlpanel
import fsleyes.views.canvaspanel      as canvaspanel
import fsleyes.icons                  as icons
import fsleyes.tooltips               as fsltooltips
import fsleyes.actions                as actions
import fsleyes.colourmaps             as fslcm
import fsleyes.strings                as strings


log = logging.getLogger(__name__)


class OverlayDisplayToolBar(ctrlpanel.ControlToolBar):
    """The ``OverlyDisplyaToolBar`` is a :class:`.ControlToolBar` containing
    controls which allow the user to change the display settings of the
    currently selected overlay (as defined by the
    :attr:`.DisplayContext.selectedOverlay` property). The display settings
    for an overlay are contained in the :class:`.Display` and
    :class:`.DisplayOpts` instances that are associated with that overlay.


    An ``OverlyDisplyaToolBar`` looks something like the following:

    .. image:: images/overlaydisplaytoolbar.png
       :scale: 50%
       :align: center


    The specific controls which are displayed are defined in the
    :attr:`self.__widgetSpecs` dictionary, and are created by the following
    methods:

    .. autosummary::
       :nosignatures:

       _OverlayDisplayToolBar__makeDisplayTools
       _OverlayDisplayToolBar__makeVolumeOptsTools
       _OverlayDisplayToolBar__makeMaskOptsTools
       _OverlayDisplayToolBar__makeLabelOptsTools
       _OverlayDisplayToolBar__makeVectorOptsTools
       _OverlayDisplayToolBar__makeRGBVectorOptsTools
       _OverlayDisplayToolBar__makeLineVectorOptsTools
       _OverlayDisplayToolBar__makeMeshOptsTools
       _OverlayDisplayToolBar__makeGiftiOptsTools
       _OverlayDisplayToolBar__makeFreesurferOptsTools
       _OverlayDisplayToolBar__makeTensorOptsTools
       _OverlayDisplayToolBar__makeSHOptsTools
       _OverlayDisplayToolBar__makeMIPOptsTools
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``OverlayDisplayToolBar`` is only intended to be added to
        :class:`.OrthoPanel`, :class:`.LightBoxPanel`, or
        :class:`.Scene3DPanel` views.
        """
        return [canvaspanel.CanvasPanel]


    def __init__(self, parent, overlayList, displayCtx, viewPanel):
        """Create an ``OverlyDisplyaToolBar``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg viewPanel:   The :class:`.ViewPanel` which this
                          ``OverlayDisplayToolBar`` is owned by.
        """

        ctrlpanel.ControlToolBar.__init__(self,
                                          parent,
                                          overlayList,
                                          displayCtx,
                                          viewPanel,
                                          height=24,
                                          kbFocus=True)

        self.__viewPanel      = viewPanel
        self.__currentOverlay = None

        self.displayCtx.addListener(
            'selectedOverlay',
            self.name,
            self.__selectedOverlayChanged)
        self.overlayList.addListener(
            'overlays',
            self.name,
            self.__selectedOverlayChanged)

        self.__generateWidgetSpecs()
        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``OverlyDisplyaToolBar`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.ControlToolBar.destroy` method.
        """

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self.overlayList:

            display = self.displayCtx.getDisplay(self.__currentOverlay)
            display.removeListener('overlayType', self.name)
            display.removeListener('enabled',     self.name)

        self.__currentOverlay = None
        self.__viewPanel      = None

        ctrlpanel.ControlToolBar.destroy(self)


    def __showTools(self, overlay):
        """Creates and shows a set of controls allowing the user to change
        the display settings of the specified ``overlay``.
        """

        oldTools = self.GetTools()

        # See long comment at bottom
        def destroyOldTools():
            if self.destroyed:
                return
            for t in oldTools:
                if fwidgets.isalive(t):
                    t.Destroy()

        for t in oldTools:
            t.Show(False)

        self.ClearTools(destroy=False, postevent=False)

        log.debug('Showing tools for {}'.format(overlay))

        display   = self.displayCtx.getDisplay(overlay)
        opts      = display.opts
        tools     = []
        nav       = []

        # Display tools
        dispTools, dispNav = self.__makeDisplayTools(display)

        tools.extend(dispTools)
        nav  .extend(dispNav)

        # DisplayOpts tools
        makeFunc = getattr(self, '_{}__make{}Tools'.format(
            type(self).__name__, type(opts).__name__), None)

        if makeFunc is not None:
            optsTools, optsNav = makeFunc(opts)

            tools.extend(optsTools)
            nav  .extend(optsNav)

        self.SetTools(   tools)
        self.setNavOrder(nav)

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
        display = self.displayCtx.getDisplay(self.__currentOverlay)
        self.Enable(display.enabled)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` changes. Ensures that controls for the currently
        selected overlay are being shown.
        """

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self.overlayList:
            display = self.displayCtx.getDisplay(self.__currentOverlay)
            display.removeListener('overlayType', self.name)
            display.removeListener('enabled',     self.name)

        overlay = self.displayCtx.getSelectedOverlay()

        self.__currentOverlay = overlay

        if overlay is None:
            self.ClearTools(destroy=True)
            return

        display = self.displayCtx.getDisplay(overlay)

        display.addListener('enabled',
                            self.name,
                            self.__overlayEnableChanged)
        display.addListener('overlayType',
                            self.name,
                            self.__selectedOverlayChanged)

        self.__showTools(overlay)
        self.Enable(display.enabled)


    def __makeDisplayTools(self, display):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.Display` instance.
        """

        viewPanel = self.__viewPanel

        # Display settings
        nameSpec  = self.__widgetSpecs[display, 'name']
        typeSpec  = self.__widgetSpecs[display, 'overlayType']
        alphaSpec = self.__widgetSpecs[display, 'alpha']
        briSpec   = self.__widgetSpecs[display, 'brightness']
        conSpec   = self.__widgetSpecs[display, 'contrast']


        # Buttons which toggle overlay
        # info and display panel
        # This is really hacky. The FSLeyesFrame
        # setattrs a ToggleControlPanelAction for every
        # built-in control to the view panel object,
        # so here we access attributes called
        # "OverlayDisplayPanel" and "OverlayInfoPanel".
        # This will hopefully change in the future.
        panelSpec = actions.ToggleActionButton(
            'OverlayDisplayPanel',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('gearHighlight24'),
                  icons.findImageFile('gear24')],
            tooltip=fsltooltips.actions[viewPanel, 'OverlayDisplayPanel'])
        infoSpec = actions.ToggleActionButton(
            'OverlayInfoPanel',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('informationHighlight24'),
                  icons.findImageFile('information24')],
            tooltip=fsltooltips.actions[viewPanel, 'OverlayInfoPanel'])

        # Name/overlay type and brightness/contrast
        # are respectively placed together
        nameTypePanel = wx.Panel(self)
        briconPanel   = wx.Panel(self)
        nameTypeSizer = wx.BoxSizer(wx.VERTICAL)
        briconSizer   = wx.FlexGridSizer(2, 2, 0, 0)

        briconSizer.AddGrowableCol(1)

        nameTypePanel.SetSizer(nameTypeSizer)
        briconPanel  .SetSizer(briconSizer)

        panelWidget = props.buildGUI(self,          viewPanel, panelSpec)
        infoWidget  = props.buildGUI(self,          viewPanel, infoSpec)
        nameWidget  = props.buildGUI(nameTypePanel, display,   nameSpec)
        typeWidget  = props.buildGUI(nameTypePanel, display,   typeSpec)
        briWidget   = props.buildGUI(briconPanel,   display,   briSpec)
        conWidget   = props.buildGUI(briconPanel,   display,   conSpec)
        alphaWidget = props.buildGUI(self,          display,   alphaSpec)

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

        tools = [panelWidget,
                 infoWidget,
                 nameTypePanel,
                 alphaPanel,
                 briconPanel]
        nav   = [panelWidget,
                 infoWidget,
                 nameWidget,
                 typeWidget,
                 alphaWidget,
                 briWidget,
                 conWidget]

        return tools, nav


    def __makeVolumeOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.VolumeOpts` instance.
        """
        rangeSpec      = self.__widgetSpecs[opts, 'displayRange']
        resetSpec      = self.__widgetSpecs[opts, 'resetDisplayRange']
        cmapSpec       = self.__widgetSpecs[opts, 'cmap']
        negCmapSpec    = self.__widgetSpecs[opts, 'negativeCmap']
        useNegCmapSpec = self.__widgetSpecs[opts, 'useNegativeCmap']

        cmapPanel = wx.Panel(self)

        rangeWidget      = props.buildGUI(self,      opts, rangeSpec)
        resetWidget      = props.buildGUI(self,      opts, resetSpec)
        useNegCmapWidget = props.buildGUI(self,      opts, useNegCmapSpec)
        cmapWidget       = props.buildGUI(cmapPanel, opts, cmapSpec)
        negCmapWidget    = props.buildGUI(cmapPanel, opts, negCmapSpec)

        cmapSizer = wx.BoxSizer(wx.VERTICAL)
        cmapPanel.SetSizer(cmapSizer)
        cmapSizer.Add(cmapWidget)
        cmapSizer.Add(negCmapWidget)

        tools = [resetWidget, rangeWidget, useNegCmapWidget, cmapPanel]
        nav   = [resetWidget, rangeWidget, useNegCmapWidget, cmapWidget,
                 negCmapWidget]

        return tools, nav


    def __makeComplexOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.ComplexOpts` instance.
        """
        rangeSpec = self.__widgetSpecs[opts, 'displayRange']
        resetSpec = self.__widgetSpecs[opts, 'resetDisplayRange']
        cmapSpec  = self.__widgetSpecs[opts, 'cmap']
        compSpec  = self.__widgetSpecs[opts, 'component']
        ccpanel   = wx.Panel(self)

        rangeWidget = props.buildGUI(self,    opts, rangeSpec)
        resetWidget = props.buildGUI(self,    opts, resetSpec)
        cmapWidget  = props.buildGUI(ccpanel, opts, cmapSpec)
        compWidget  = props.buildGUI(ccpanel, opts, compSpec)

        ccsizer = wx.BoxSizer(wx.VERTICAL)
        ccpanel.SetSizer(ccsizer)
        ccsizer.Add(cmapWidget, flag=wx.EXPAND)
        ccsizer.Add(compWidget, flag=wx.EXPAND)

        tools = [resetWidget, rangeWidget, ccpanel]
        nav   = [resetWidget, rangeWidget, cmapWidget, compWidget]

        return tools, nav


    def __makeMaskOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.MaskOpts` instance.
        """
        thresSpec  = self.__widgetSpecs[opts, 'threshold']
        colourSpec = self.__widgetSpecs[opts, 'colour']

        thresWidget  = props.buildGUI(self, opts, thresSpec)
        colourWidget = props.buildGUI(self, opts, colourSpec)

        tools = [thresWidget, colourWidget]

        return tools, tools


    def __makeLabelOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.LabelOpts` instance.
        """

        lutSpec     = self.__widgetSpecs[opts, 'lut']
        outlineSpec = self.__widgetSpecs[opts, 'outline']
        widthSpec   = self.__widgetSpecs[opts, 'outlineWidth']

        # lut/outline width widgets
        # are on a single panel
        lutWidthPanel = wx.Panel(self)
        lutWidthSizer = wx.FlexGridSizer(2, 2, 0, 0)
        lutWidthPanel.SetSizer(lutWidthSizer)

        lutWidget     = props.buildGUI(lutWidthPanel, opts, lutSpec)
        widthWidget   = props.buildGUI(lutWidthPanel, opts, widthSpec)
        outlineWidget = props.buildGUI(self,          opts, outlineSpec)

        lutLabel   = wx.StaticText(lutWidthPanel)
        widthLabel = wx.StaticText(lutWidthPanel)

        lutLabel  .SetLabel(strings.properties[opts, 'lut'])
        widthLabel.SetLabel(strings.properties[opts, 'outlineWidth'])

        lutWidthSizer.Add(lutLabel)
        lutWidthSizer.Add(lutWidget,   flag=wx.EXPAND)
        lutWidthSizer.Add(widthLabel)
        lutWidthSizer.Add(widthWidget, flag=wx.EXPAND)

        tools = [lutWidthPanel, outlineWidget]
        nav   = [lutWidget, widthWidget, outlineWidget]

        return tools, nav


    def __makeVectorOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.VectorOpts` instance.
        """

        modSpec   = self.__widgetSpecs[opts, 'modulateImage']
        clipSpec  = self.__widgetSpecs[opts, 'clipImage']
        rangeSpec = self.__widgetSpecs[opts, 'clippingRange']

        panel = wx.Panel(self)
        sizer = wx.GridBagSizer()
        panel.SetSizer(sizer)

        modWidget   = props.buildGUI(panel, opts, modSpec)
        clipWidget  = props.buildGUI(panel, opts, clipSpec)
        rangeWidget = props.buildGUI(panel, opts, rangeSpec)
        modLabel    = wx.StaticText(panel)
        clipLabel   = wx.StaticText(panel)

        modLabel .SetLabel(strings.properties[opts, 'modulateImage'])
        clipLabel.SetLabel(strings.properties[opts, 'clipImage'])

        sizer.Add(modLabel,    pos=(0, 0), span=(1, 1), flag=wx.EXPAND)
        sizer.Add(modWidget,   pos=(0, 1), span=(1, 1), flag=wx.EXPAND)
        sizer.Add(clipLabel,   pos=(1, 0), span=(1, 1), flag=wx.EXPAND)
        sizer.Add(clipWidget,  pos=(1, 1), span=(1, 1), flag=wx.EXPAND)
        sizer.Add(rangeWidget, pos=(0, 2), span=(2, 1), flag=wx.EXPAND)

        tools = [panel]
        nav   = [modWidget, clipWidget, rangeWidget]

        return tools, nav


    def __makeRGBVectorOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.RGBVectorOpts` instance.
        """
        return self.__makeVectorOptsTools(opts)


    def __makeLineVectorOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.LineVectorOpts` instance.
        """
        widthSpec = self.__widgetSpecs[opts, 'lineWidth']

        widget    = props.buildGUI(self, opts, widthSpec)
        lblWidget = self.MakeLabelledTool(
            widget, strings.properties[opts, 'lineWidth'])

        tools, nav = self.__makeVectorOptsTools(opts)

        return tools + [lblWidget], nav + [widget]


    def __makeMeshOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.MeshOpts` instance.
        """
        colourSpec  = self.__widgetSpecs[opts, 'colour']
        outlineSpec = self.__widgetSpecs[opts, 'outline']
        widthSpec   = self.__widgetSpecs[opts, 'outlineWidth']

        colourWidget  = props.buildGUI(self, opts, colourSpec)
        outlineWidget = props.buildGUI(self, opts, outlineSpec)
        widthWidget   = props.buildGUI(self, opts, widthSpec)

        lblWidthWidget  = self.MakeLabelledTool(
            widthWidget, strings.properties[opts, 'outlineWidth'])

        tools = [colourWidget, outlineWidget, lblWidthWidget]
        nav   = [colourWidget, outlineWidget, widthWidget]

        return tools, nav


    def __makeGiftiOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.GiftiOpts` instance.
        """
        tools, nav = self.__makeMeshOptsTools(opts)

        vertWidget  = self.__widgetSpecs[opts, 'vertexSet']
        vdataWidget = self.__widgetSpecs[opts, 'vertexData']

        panel       = wx.Panel(self)
        sizer       = wx.BoxSizer(wx.VERTICAL)
        vertWidget  = props.buildGUI(panel, opts, vertWidget)
        vdataWidget = props.buildGUI(panel, opts, vdataWidget)

        sizer.Add(vertWidget,  flag=wx.EXPAND)
        sizer.Add(vdataWidget, flag=wx.EXPAND)
        panel.SetSizer(sizer)

        tools += [panel]
        nav   += [vertWidget, vdataWidget]

        return tools, nav


    def __makeFreesurferOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.FreesurferOpts` instance.
        """
        return self.__makeGiftiOptsTools(opts)


    def __makeTensorOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.TensorOpts` instance.
        """
        lightingSpec   = self.__widgetSpecs[opts, 'lighting']
        lightingWidget = props.buildGUI(self, opts, lightingSpec)

        tools, nav = self.__makeVectorOptsTools(opts)

        return tools + [lightingWidget], nav + [lightingWidget]


    def __makeSHOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.SHOpts` instance.
        """
        sizeSpec = self.__widgetSpecs[opts, 'size']
        radSpec  = self.__widgetSpecs[opts, 'radiusThreshold']

        panel = wx.Panel(self)
        sizer = wx.FlexGridSizer(2, 2, 0, 0)

        sizeWidget  = props.buildGUI(panel, opts, sizeSpec)
        radWidget   = props.buildGUI(panel, opts, radSpec)

        sizeLabel = wx.StaticText(panel)
        radLabel  = wx.StaticText(panel)

        sizeLabel.SetLabel(strings.properties[opts, 'size'])
        radLabel .SetLabel(strings.properties[opts, 'radiusThreshold'])

        sizer.Add(sizeLabel)
        sizer.Add(sizeWidget)
        sizer.Add(radLabel)
        sizer.Add(radWidget)
        panel.SetSizer(sizer)

        tools, nav = self.__makeVectorOptsTools(opts)

        tools.extend([panel])
        nav.extend(  [sizeWidget, radWidget])

        return tools, nav


    def __makeMIPOptsTools(self, opts):
        """Creates and returns a collection of controls for editing properties
        of the given :class:`.MIPOpts` instance.
        """
        rangeSpec = self.__widgetSpecs[opts, 'displayRange']
        resetSpec = self.__widgetSpecs[opts, 'resetDisplayRange']
        cmapSpec  = self.__widgetSpecs[opts, 'cmap']

        cmapPanel = wx.Panel(self)

        rangeWidget = props.buildGUI(self,      opts, rangeSpec)
        resetWidget = props.buildGUI(self,      opts, resetSpec)
        cmapWidget  = props.buildGUI(cmapPanel, opts, cmapSpec)

        cmapSizer = wx.BoxSizer(wx.VERTICAL)
        cmapPanel.SetSizer(cmapSizer)
        cmapSizer.Add(cmapWidget)

        tools = [resetWidget, rangeWidget, cmapPanel]
        nav   = [resetWidget, rangeWidget, cmapWidget]

        return tools, nav


    def __generateWidgetSpecs(self):
        """Called by :meth:`__init__`. Creates specifications for the toolbar
        widgets for all overlay types.
        """

        def _imageLabel(img):
            """Used to generate labels for the :attr:`.VectorOpts.modulateImage`,
            :attr:`.VectorOpts.clipImage`, and other :class:`.Image`-based
            choice properties.
            """
            if img is None: return 'None'
            else:           return self.displayCtx.getDisplay(img).name

        def _pathLabel(p):
            if p is None: return 'None'
            else:         return op.basename(p)

        self.__widgetSpecs = td.TypeDict({

            'Display.name'         : props.Widget(
                'name',
                tooltip=_TOOLTIPS['Display.name']),
            'Display.overlayType'  : props.Widget(
                'overlayType',
                tooltip=_TOOLTIPS['Display.overlayType'],
                labels=strings.choices['Display.overlayType']),
            'Display.alpha'        : props.Widget(
                'alpha',
                spin=False,
                showLimits=False,
                tooltip=_TOOLTIPS['Display.alpha']),
            'Display.brightness'   : props.Widget(
                'brightness',
                spin=False,
                showLimits=False,
                tooltip=_TOOLTIPS['Display.brightness']),
            'Display.contrast'     : props.Widget(
                'contrast',
                spin=False,
                showLimits=False,
                tooltip=_TOOLTIPS['Display.contrast']),

            'VolumeOpts.resetDisplayRange' : actions.ActionButton(
                'resetDisplayRange',
                icon=icons.findImageFile('verticalReset32')
            ),

            'VolumeOpts.displayRange' : props.Widget(
                'displayRange',
                slider=False,
                showLimits=False,
                spinWidth=10,
                tooltip=_TOOLTIPS['ColourMapOpts.displayRange'],
                labels=[strings.choices['ColourMapOpts.displayRange.min'],
                        strings.choices['ColourMapOpts.displayRange.max']]),
            'VolumeOpts.cmap' : props.Widget(
                'cmap',
                labels=fslcm.getColourMapLabel,
                tooltip=_TOOLTIPS['VolumeOpts.cmap']),
            'VolumeOpts.useNegativeCmap' : props.Widget(
                'useNegativeCmap',
                icon=[icons.findImageFile('twocmaps24'),
                      icons.findImageFile('onecmap24')],
                toggle=True,
                tooltip=_TOOLTIPS['VolumeOpts.useNegativeCmap']),

            'VolumeOpts.negativeCmap' : props.Widget(
                'negativeCmap',
                labels=fslcm.getColourMapLabel,
                tooltip=_TOOLTIPS['VolumeOpts.negativeCmap'],
                dependencies=['useNegativeCmap'],
                enabledWhen=lambda i, unc : unc),

            'ComplexOpts.component' : props.Widget(
                'component',
                labels=strings.choices['ComplexOpts.component'],
                tooltip=_TOOLTIPS['ComplexOpts.component']),

            'MaskOpts.threshold' : props.Widget(
                'threshold',
                showLimits=False,
                spin=True,
                tooltip=_TOOLTIPS['MaskOpts.threshold'],
                labels=[strings.choices['MaskOpts.threshold.min'],
                        strings.choices['MaskOpts.threshold.max']]),
            'MaskOpts.colour'    : props.Widget(
                'colour',
                size=(24, 24),
                tooltip=_TOOLTIPS['MaskOpts.colour']),

            'LabelOpts.lut'     : props.Widget(
                'lut',
                tooltip=_TOOLTIPS['LabelOpts.lut'],
                labels=lambda l: l.name),
            'LabelOpts.outline' : props.Widget(
                'outline',
                tooltip=_TOOLTIPS['LabelOpts.outline'],
                icon=[icons.findImageFile('outline24'),
                      icons.findImageFile('filled24')],
                toggle=True),
            'LabelOpts.outlineWidth' : props.Widget(
                'outlineWidth',
                tooltip=_TOOLTIPS['LabelOpts.outlineWidth'],
                showLimits=False,
                spin=False),

            'MeshOpts.colour'       : props.Widget(
                'colour',
                size=(24, 24),
                tooltip=_TOOLTIPS['MeshOpts.colour']),
            'MeshOpts.outline'      : props.Widget(
                'outline',
                tooltip=_TOOLTIPS['MeshOpts.outline'],
                icon=[icons.findImageFile('outline24'),
                      icons.findImageFile('filled24')],
                toggle=True),
            'MeshOpts.outlineWidth' : props.Widget(
                'outlineWidth',
                showLimits=False,
                spin=False,
                tooltip=_TOOLTIPS['MeshOpts.outlineWidth'],
                enabledWhen=lambda i: i.outline),
            'MeshOpts.vertexSet' : props.Widget(
                'vertexSet',
                labels=_pathLabel,
                tooltip=_TOOLTIPS['MeshOpts.vertexSet']
            ),
            'MeshOpts.vertexData' : props.Widget(
                'vertexData',
                labels=_pathLabel,
                tooltip=_TOOLTIPS['MeshOpts.vertexData']
            ),

            'VectorOpts.modulateImage' : props.Widget(
                'modulateImage',
                labels=_imageLabel,
                tooltip=_TOOLTIPS['VectorOpts.modulateImage']),
            'VectorOpts.clipImage' : props.Widget(
                'clipImage',
                labels=_imageLabel,
                tooltip=_TOOLTIPS['VectorOpts.clipImage']),
            'VectorOpts.clippingRange' : props.Widget(
                'clippingRange',
                showLimits=False,
                slider=True,
                spin=False,
                tooltip=_TOOLTIPS['VectorOpts.clippingRange'],
                labels=[strings.choices['VectorOpts.clippingRange.min'],
                        strings.choices['VectorOpts.clippingRange.max']],
                dependencies=['clipImage'],
                enabledWhen=lambda o, ci: ci is not None),

            'LineVectorOpts.lineWidth' : props.Widget(
                'lineWidth',
                showLimits=False,
                spin=False,
                tooltip=_TOOLTIPS['LineVectorOpts.lineWidth']),

            'TensorOpts.lighting'      : props.Widget(
                'lighting',
                icon=[icons.findImageFile('lightbulbHighlight24'),
                      icons.findImageFile('lightbulb24')],
                tooltip=_TOOLTIPS['TensorOpts.lighting']),

            'SHOpts.lighting'        : props.Widget(
                'lighting',
                icon=[icons.findImageFile('lightbulbHighlight24'),
                      icons.findImageFile('lightbulb24')],
                tooltip=_TOOLTIPS['SHOpts.lighting']),
            'SHOpts.size'            : props.Widget(
                'size',
                showLimits=False,
                slider=True,
                spin=False,
                tooltip=_TOOLTIPS['SHOpts.size']),
            'SHOpts.radiusThreshold' : props.Widget(
                'radiusThreshold',
                slider=True,
                spin=False,
                showLimits=False,
                tooltip=_TOOLTIPS['SHOpts.radiusThreshold']),

            'MIPOpts.resetDisplayRange' : actions.ActionButton(
                'resetDisplayRange',
                icon=icons.findImageFile('verticalReset32')
            ),

            'MIPOpts.displayRange' : props.Widget(
                'displayRange',
                slider=False,
                showLimits=False,
                spinWidth=10,
                tooltip=_TOOLTIPS['ColourMapOpts.displayRange'],
                labels=[strings.choices['ColourMapOpts.displayRange.min'],
                        strings.choices['ColourMapOpts.displayRange.max']]),
            'MIPOpts.cmap' : props.Widget(
                'cmap',
                labels=fslcm.getColourMapLabel,
                tooltip=_TOOLTIPS['VolumeOpts.cmap']),
        })


_TOOLTIPS = td.TypeDict({

    'Display.name'        : fsltooltips.properties['Display.name'],
    'Display.overlayType' : fsltooltips.properties['Display.overlayType'],
    'Display.alpha'       : fsltooltips.properties['Display.alpha'],
    'Display.brightness'  : fsltooltips.properties['Display.brightness'],
    'Display.contrast'    : fsltooltips.properties['Display.contrast'],

    'ColourMapOpts.displayRange' :
    fsltooltips.properties['ColourMapOpts.displayRange'],
    'VolumeOpts.cmap'              :
    fsltooltips.properties['ColourMapOpts.cmap'],
    'VolumeOpts.negativeCmap'      :
    fsltooltips.properties['ColourMapOpts.negativeCmap'],
    'VolumeOpts.useNegativeCmap'   :
    fsltooltips.properties['ColourMapOpts.useNegativeCmap'],

    'ComplexOpts.component' : fsltooltips.properties['ComplexOpts.component'],

    'MaskOpts.threshold' : fsltooltips.properties['MaskOpts.threshold'],
    'MaskOpts.colour'    : fsltooltips.properties['MaskOpts.colour'],

    'LabelOpts.lut'          : fsltooltips.properties['LabelOpts.lut'],

    'LabelOpts.outline'      : fsltooltips.properties['LabelOpts.outline'],
    'LabelOpts.outlineWidth' : fsltooltips.properties['LabelOpts.'
                                                      'outlineWidth'],

    'VectorOpts.modulateImage' : fsltooltips.properties['VectorOpts.'
                                                        'modulateImage'],
    'VectorOpts.clipImage'     : fsltooltips.properties['VectorOpts.'
                                                        'clipImage'],
    'VectorOpts.clippingRange' : fsltooltips.properties['VectorOpts.'
                                                        'clippingRange'],

    'LineVectorOpts.lineWidth' : fsltooltips.properties['LineVectorOpts.'
                                                        'lineWidth'],

    'MeshOpts.colour'       : fsltooltips.properties['MeshOpts.colour'],
    'MeshOpts.outline'      : fsltooltips.properties['MeshOpts.outline'],
    'MeshOpts.outlineWidth' : fsltooltips.properties['MeshOpts.'
                                                     'outlineWidth'],
    'MeshOpts.vertexSet'    : fsltooltips.properties['MeshOpts.vertexSet'],
    'MeshOpts.vertexData'   : fsltooltips.properties['MeshOpts.vertexData'],

    'TensorOpts.lighting' : fsltooltips.properties['TensorOpts.'
                                                   'lighting'],

    'SHOpts.lighting'        : fsltooltips.properties['SHOpts.lighting'],
    'SHOpts.size'            : fsltooltips.properties['SHOpts.size'],
    'SHOpts.radiusThreshold' : fsltooltips.properties['SHOpts.'
                                                      'radiusThreshold'],
})
"""This dictionary contains tooltips for :class:`.Display` and
:class:`.DisplayOpts` properties. It is used by the
:meth:`OverlayDisplayToolBar.__generateWidgetSpecs` method.
"""
