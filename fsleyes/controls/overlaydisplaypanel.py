#!/usr/bin/env python
#
# overlaydisplaypanel.py - The OverlayDisplayPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides the :class:`OverlayDisplayPanel` class, a *FSLeyes
control* panel which allows the user to change overlay display settings.
"""


import            logging
import            functools
import os.path as op

import wx

import fsleyes_props                  as props
import fsleyes_widgets.utils.typedict as td

import fsleyes.strings                as strings
import fsleyes.tooltips               as fsltooltips
import fsleyes.panel                  as fslpanel
import fsleyes.colourmaps             as fslcm
import fsleyes.actions.loadcolourmap  as loadcmap
import fsleyes.actions.loadvertexdata as loadvdata
import fsleyes.displaycontext         as displayctx


log = logging.getLogger(__name__)


class OverlayDisplayPanel(fslpanel.FSLeyesSettingsPanel):
    """The ``OverlayDisplayPanel`` is a :Class:`.FSLeyesPanel` which allows
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
    defined in the :attr:`_DISPLAY_PROPS` and :attr:`_DISPLAY_WIDGETS`
    dictionaries.
    """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create an ``OverlayDisplayPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        fslpanel.FSLeyesSettingsPanel.__init__(self,
                                               parent,
                                               overlayList,
                                               displayCtx,
                                               frame,
                                               kbFocus=True)

        displayCtx .addListener('selectedOverlay',
                                 self._name,
                                 self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                 self._name,
                                 self.__selectedOverlayChanged)

        self.__dispWidgets = None
        self.__optsWidgets = None

        self.__currentOverlay = None
        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``OverlayDisplayPanel`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.FSLeyesPanel.destroy` method.
        """

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:

            display = self._displayCtx.getDisplay(self.__currentOverlay)

            display.removeListener('overlayType', self._name)

        self.__currentOverlay = None
        self.__dispWidgets    = None
        self.__optsWidgets    = None

        fslpanel.FSLeyesPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes. Refreshes this
        ``OverlayDisplayPanel`` so that the display settings for the newly
        selected overlay are shown.
        """

        overlay     = self._displayCtx.getSelectedOverlay()
        lastOverlay = self.__currentOverlay
        widgetList  = self.getWidgetList()

        if overlay is None:
            self.__currentOverlay = None
            widgetList.Clear()
            self.Layout()
            return

        if overlay is lastOverlay:
            return

        self.__currentOverlay = overlay

        if lastOverlay is not None and \
           lastOverlay in self._overlayList:

            lastDisplay = self._displayCtx.getDisplay(lastOverlay)
            lastDisplay.removeListener('overlayType', self._name)

        if lastOverlay is not None:
            displayExpanded = widgetList.IsExpanded('display')
            optsExpanded    = widgetList.IsExpanded('opts')
        else:
            displayExpanded = True
            optsExpanded    = True

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        display.addListener('overlayType', self._name, self.__ovlTypeChanged)

        widgetList.Clear()
        widgetList.AddGroup('display', strings.labels[self, display])
        widgetList.AddGroup('opts',    strings.labels[self, opts])

        self.__dispWidgets = self.__updateWidgets(display, 'display')
        self.__optsWidgets = self.__updateWidgets(opts,    'opts')

        widgetList.Expand('display', displayExpanded)
        widgetList.Expand('opts',    optsExpanded)

        self.setNavOrder(self.__dispWidgets + self.__optsWidgets)
        self.Layout()


    def __ovlTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` of the current overlay
        changes. Refreshes the :class:`.DisplayOpts` settings which are shown,
        as a new :class:`.DisplayOpts` instance will have been created for the
        overlay.
        """

        opts = self._displayCtx.getOpts(self.__currentOverlay)
        self.__optsWidgets = self.__updateWidgets(opts, 'opts')

        self.setNavOrder(self.__dispWidgets + self.__optsWidgets)
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


        :returns:       A list containing all of the new widgets that
                        were created.
        """

        widgetList = self.getWidgetList()

        widgetList.ClearGroup( groupName)
        widgetList.RenameGroup(groupName, strings.labels[self, target])

        dispProps = _DISPLAY_PROPS.get(target, [], allhits=True)
        dispProps = functools.reduce(lambda a, b: a + b, dispProps)
        dispProps = [_DISPLAY_WIDGETS[target, dp] for dp in dispProps]

        labels   = [strings.properties.get((target, p.key), p.key)
                    for p in dispProps]
        tooltips = [fsltooltips.properties.get((target, p.key), None)
                    for p in dispProps]

        widgets         = []
        returnedWidgets = []

        for p in dispProps:

            widget   = props.buildGUI(widgetList, target, p)
            toReturn = [widget]

            # Build a panel for the ColourMapOpts
            # colour map controls.
            if isinstance(target, displayctx.ColourMapOpts):
                if p.key == 'cmap':
                    cmapWidget    = widget
                    widget, extra = self.__buildColourMapWidget(
                        target, cmapWidget)
                    toReturn = [cmapWidget] + list(extra)

            # Special case for VolumeOpts props
            if isinstance(target, displayctx.VolumeOpts):
                if p.key == 'enableOverrideDataRange':
                    enableWidget  = widget
                    widget, extra = self.__buildOverrideDataRangeWidget(
                        target, enableWidget)
                    toReturn = [enableWidget] + list(extra)

            # More special cases for MeshOpts
            elif isinstance(target, displayctx.MeshOpts):
                if p.key == 'vertexData':
                    vdataWidget   = widget
                    widget, extra = self.__buildVertexDataWidget(
                        target, vdataWidget)
                    toReturn = [vdataWidget] + list(extra)

                if p.key == 'lut':
                    lutWidget   = widget
                    widget, extra = self.__buildMeshOptsLutWidget(
                        target, lutWidget)
                    toReturn = [lutWidget] + list(extra)

            returnedWidgets.extend(toReturn)
            widgets        .append(widget)

        for label, tooltip, widget in zip(labels, tooltips, widgets):
            widgetList.AddWidget(
                widget,
                label,
                tooltip=tooltip,
                groupName=groupName)

        self.Layout()

        return returnedWidgets


    def __buildColourMapWidget(self, target, cmapWidget):
        """Builds a panel which contains widgets for controlling the
        :attr:`.VolumeOpts.cmap`, :attr:`.VolumeOpts.negativeCmap`, and
        :attr:`.VolumeOpts.useNegativeCmap`.

        :returns: A ``wx.Sizer`` containing all of the widgets, and a list
                  containing the extra widgets that were added.
        """

        widgets = self.getWidgetList()

        # Button to load a new
        # colour map from file
        loadAction = loadcmap.LoadColourMapAction(self._overlayList,
                                                  self._displayCtx)

        loadButton = wx.Button(widgets)
        loadButton.SetLabel(strings.labels[self, 'loadCmap'])

        loadAction.bindToWidget(self, wx.EVT_BUTTON, loadButton)

        # Negative colour map widget
        negCmap    = _DISPLAY_WIDGETS[target, 'negativeCmap']
        useNegCmap = _DISPLAY_WIDGETS[target, 'useNegativeCmap']

        negCmap    = props.buildGUI(widgets, target, negCmap)
        useNegCmap = props.buildGUI(widgets, target, useNegCmap)

        useNegCmap.SetLabel(strings.properties[target, 'useNegativeCmap'])

        sizer = wx.FlexGridSizer(2, 2, 0, 0)
        sizer.AddGrowableCol(0)

        sizer.Add(cmapWidget, flag=wx.EXPAND)
        sizer.Add(loadButton, flag=wx.EXPAND)
        sizer.Add(negCmap,    flag=wx.EXPAND)
        sizer.Add(useNegCmap, flag=wx.EXPAND)

        return sizer, [negCmap, useNegCmap]


    def __buildVertexDataWidget(self, target, vdataWidget):
        """Builds a panel which contains a widget for controlling the
        :attr:`.MeshOpts.vertexData` property, and also has a button
        which opens a file dialog, allowing the user to select other
        data.
        """
        widgets = self.getWidgetList()

        loadAction = loadvdata.LoadVertexDataAction(self._overlayList,
                                                    self._displayCtx)
        loadButton = wx.Button(widgets)
        loadButton.SetLabel(strings.labels[self, 'loadVertexData'])

        loadAction.bindToWidget(self, wx.EVT_BUTTON, loadButton)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(vdataWidget, flag=wx.EXPAND, proportion=1)
        sizer.Add(loadButton,  flag=wx.EXPAND)

        return sizer, []


    def __buildMeshOptsLutWidget(self, target, lutWidget):
        """Builds a panel which contains the provided :attr:`.MeshOpts.lut`
        widget, and also a widget for :attr:`.MeshOpts.useLut`.
        """
        widgets = self.getWidgetList()

        # enable lut widget
        enableWidget = _DISPLAY_WIDGETS[target, 'useLut']
        enableWidget = props.buildGUI(widgets, target, enableWidget)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(enableWidget,  flag=wx.EXPAND)
        sizer.Add(lutWidget, flag=wx.EXPAND, proportion=1)

        return sizer, [enableWidget]


    def __buildOverrideDataRangeWidget(self, target, enableWidget):
        """Builds a panel which contains widgets for enabling and adjusting
        the :attr:`.VolumeOpts.overrideDataRange`.

        :returns: a ``wx.Sizer`` containing all of the widgets.
        """

        widgets = self.getWidgetList()

        # Override data range widget
        overrideRange = _DISPLAY_WIDGETS[target, 'overrideDataRange']
        overrideRange = props.buildGUI(widgets, target, overrideRange)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(enableWidget,  flag=wx.EXPAND)
        sizer.Add(overrideRange, flag=wx.EXPAND, proportion=1)

        return sizer, [overrideRange]


def _imageName(img):
    """Used to generate choice labels for the :attr`.VectorOpts.modulateImage`,
    :attr`.VectorOpts.clipImage`, :attr`.VectorOpts.colourImage` and
    :attr:`.MeshOpts.refImage` properties.
    """
    if img is None: return 'None'
    else:           return img.name


def _meshVertexDataName(vdata):
    """Used to generate choice labels for the :attr`.MeshOpts.vertexData`
    property.
    """
    if vdata is None: return 'None'
    else:             return op.basename(vdata)


_DISPLAY_PROPS = td.TypeDict({
    'Display'        : ['name',
                        'overlayType',
                        'enabled',
                        'alpha',
                        'brightness',
                        'contrast'],
    'VolumeOpts'     : ['volume',
                        'interpolation',
                        'cmap',
                        'cmapResolution',
                        'interpolateCmaps',
                        'invert',
                        'invertClipping',
                        'linkLowRanges',
                        'linkHighRanges',
                        'displayRange',
                        'clippingRange',
                        'clipImage',
                        'enableOverrideDataRange'],
    'MaskOpts'       : ['volume',
                        'colour',
                        'invert',
                        'threshold'],
    'VectorOpts'     : ['colourImage',
                        'modulateImage',
                        'clipImage',
                        'cmap',
                        'clippingRange',
                        'modulateRange',
                        'xColour',
                        'yColour',
                        'zColour',
                        'suppressX',
                        'suppressY',
                        'suppressZ',
                        'suppressMode'],
    'RGBVectorOpts'  : ['interpolation'],
    'LineVectorOpts' : ['directed',
                        'unitLength',
                        'orientFlip',
                        'lineWidth',
                        'lengthScale'],
    'MeshOpts'       : ['refImage',
                        'coordSpace',
                        'outline',
                        'outlineWidth',
                        'colour',
                        'vertexData',
                        'vertexDataIndex',
                        'lut',
                        'cmap',
                        'cmapResolution',
                        'interpolateCmaps',
                        'invert',
                        'invertClipping',
                        'linkLowRanges',
                        'linkHighRanges',
                        'displayRange',
                        'clippingRange'],
    'TensorOpts'     : ['lighting',
                        'orientFlip',
                        'tensorResolution',
                        'tensorScale'],
    'LabelOpts'      : ['lut',
                        'outline',
                        'outlineWidth',
                        'volume'],
    'SHOpts'         : ['shResolution',
                        'shOrder',
                        'orientFlip',
                        'lighting',
                        'size',
                        'radiusThreshold',
                        'colourMode']
})
"""This dictionary contains lists of all the properties which are to be
displayed on an ``OverlayDisplayPanel``.
"""


def meshOptsColourEnabledWhen(opts, vdata, outline, useLut):
    """Use to enable/disable :class:`.MeshOpts` colour properties.
    """
    return outline and (vdata is not None) and (not useLut)


meshOptsColourKwargs = {
    'dependencies' : ['vertexData', 'outline', 'useLut'],
    'enabledWhen'  : meshOptsColourEnabledWhen
}
"""Passed to the widget definitions for various :class:`.MeshOpts`
properties.
"""


_DISPLAY_WIDGETS = td.TypeDict({

    # Display
    'Display.name'        : props.Widget('name'),
    'Display.overlayType' : props.Widget(
        'overlayType',
        labels=strings.choices['Display.overlayType']),
    'Display.enabled'     : props.Widget('enabled'),
    'Display.alpha'       : props.Widget('alpha',      showLimits=False),
    'Display.brightness'  : props.Widget('brightness', showLimits=False),
    'Display.contrast'    : props.Widget('contrast',   showLimits=False),

    'ColourMapOpts.cmap'           : props.Widget(
        'cmap',
        labels=fslcm.getColourMapLabel),

    'ColourMapOpts.useNegativeCmap' : props.Widget('useNegativeCmap'),
    'ColourMapOpts.negativeCmap'    : props.Widget(
        'negativeCmap',
        labels=fslcm.getColourMapLabel,
        dependencies=['useNegativeCmap'],
        enabledWhen=lambda i, unc : unc),
    'ColourMapOpts.cmapResolution'  : props.Widget(
        'cmapResolution',
        slider=True,
        spin=True,
        showLimits=False),
    'ColourMapOpts.interpolateCmaps' : props.Widget('interpolateCmaps'),
    'ColourMapOpts.invert'           : props.Widget('invert'),
    'ColourMapOpts.invertClipping'   : props.Widget('invertClipping'),
    'ColourMapOpts.linkLowRanges'    : props.Widget('linkLowRanges'),
    'ColourMapOpts.linkHighRanges' : props.Widget(  'linkHighRanges'),
    'ColourMapOpts.displayRange'   : props.Widget(
        'displayRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['ColourMapOpts.displayRange.min'],
                strings.choices['ColourMapOpts.displayRange.max']]),
    'ColourMapOpts.clippingRange'  : props.Widget(
        'clippingRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['ColourMapOpts.displayRange.min'],
                strings.choices['ColourMapOpts.displayRange.max']]),

    # VolumeOpts
    'VolumeOpts.volume'         : props.Widget(
        'volume',
        showLimits=False,
        enabledWhen=lambda o: o.overlay.is4DImage()),
    'VolumeOpts.interpolation'  : props.Widget(
        'interpolation',
        labels=strings.choices['VolumeOpts.interpolation']),
    'VolumeOpts.clipImage'      : props.Widget(
        'clipImage',
        labels=_imageName),
    'VolumeOpts.enableOverrideDataRange'  : props.Widget(
        'enableOverrideDataRange'),
    'VolumeOpts.overrideDataRange' : props.Widget(
        'overrideDataRange',
        showLimits=False,
        spin=True,
        slider=False,
        dependencies=['enableOverrideDataRange'],
        enabledWhen=lambda vo, en: en),

    # MaskOpts
    'MaskOpts.volume'     : props.Widget(
        'volume',
        showLimits=False,
        enabledWhen=lambda o: o.overlay.is4DImage()),
    'MaskOpts.colour'     : props.Widget('colour'),
    'MaskOpts.invert'     : props.Widget('invert'),
    'MaskOpts.threshold'  : props.Widget('threshold', showLimits=False),

    # VectorOpts (shared by all
    # the VectorOpts sub-classes)
    'VectorOpts.colourImage'   : props.Widget(
        'colourImage',
        labels=_imageName),
    'VectorOpts.modulateImage' : props.Widget(
        'modulateImage',
        labels=_imageName,
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'VectorOpts.clipImage'     : props.Widget('clipImage', labels=_imageName),
    'VectorOpts.cmap'          : props.Widget(
        'cmap',
        labels=fslcm.getColourMapLabel,
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is not None),
    'VectorOpts.clippingRange' : props.Widget(
        'clippingRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['VectorOpts.clippingRange.min'],
                strings.choices['VectorOpts.clippingRange.max']],
        dependencies=['clipImage'],
        enabledWhen=lambda o, ci: ci is not None),
    'VectorOpts.modulateRange' : props.Widget(
        'modulateRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['VectorOpts.modulateRange.min'],
                strings.choices['VectorOpts.modulateRange.max']],
        dependencies=['colourImage', 'modulateImage'],
        enabledWhen=lambda o, ci, mi: ci is None and mi is not None),
    'VectorOpts.xColour'       : props.Widget(
        'xColour',
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'VectorOpts.yColour'       : props.Widget(
        'yColour',
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'VectorOpts.zColour'       : props.Widget(
        'zColour',
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'VectorOpts.suppressX'     : props.Widget(
        'suppressX',
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'VectorOpts.suppressY'     : props.Widget(
        'suppressY',
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'VectorOpts.suppressZ'     : props.Widget(
        'suppressZ',
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'VectorOpts.suppressMode'  : props.Widget(
        'suppressMode',
        dependencies=['colourImage'],
        labels=strings.choices['VectorOpts.suppressMode'],
        enabledWhen=lambda o, ci: ci is None),

    # RGBVectorOpts
    'RGBVectorOpts.interpolation' : props.Widget(
        'interpolation',
        labels=strings.choices['VolumeOpts.interpolation']),

    # LineVectorOpts
    'LineVectorOpts.directed'    : props.Widget('directed'),
    'LineVectorOpts.unitLength'  : props.Widget('unitLength'),
    'LineVectorOpts.orientFlip'  : props.Widget('orientFlip'),
    'LineVectorOpts.lineWidth'   : props.Widget('lineWidth',
                                                showLimits=False),
    'LineVectorOpts.lengthScale' : props.Widget('lengthScale',
                                                showLimits=False),

    # MeshOpts
    'MeshOpts.outline'      : props.Widget('outline'),
    'MeshOpts.outlineWidth' : props.Widget(
        'outlineWidth',
        showLimits=False,
        dependencies=['outline'],
        enabledWhen=lambda o, outline: outline),
    'MeshOpts.refImage'     : props.Widget('refImage', labels=_imageName),
    'MeshOpts.coordSpace'   : props.Widget(
        'coordSpace',
        enabledWhen=lambda o, ri: ri != 'none',
        labels=strings.choices['MeshOpts.coordSpace'],
        dependencies=['refImage']),
    'MeshOpts.colour'       : props.Widget('colour'),
    'MeshOpts.vertexData'   : props.Widget(
        'vertexData',
        labels=_meshVertexDataName),
    'MeshOpts.vertexDataIndex' : props.Widget(
        'vertexDataIndex',
        showLimits=False,
        dependencies=['vertexData'],
        enabledWhen=lambda o, vd: vd is not None),
    'MeshOpts.useLut' : props.Widget(
        'useLut',
        dependencies=['outline'],
        enabledWhen=lambda opts, o: o),
    'MeshOpts.lut'    : props.Widget(
        'lut',
        labels=lambda l: l.name,
        dependencies=['outline'],
        enabledWhen=lambda opts, o: o),

    # We override the ColourMapOpts definitions
    # above, for custom enabledWhen behaviour.
    'MeshOpts.cmap'           : props.Widget(
        'cmap',
        labels=fslcm.getColourMapLabel,
        **meshOptsColourKwargs),

    'MeshOpts.useNegativeCmap' : props.Widget(
        'useNegativeCmap',
        **meshOptsColourKwargs),
    'MeshOpts.negativeCmap'    : props.Widget(
        'negativeCmap',
        labels=fslcm.getColourMapLabel,
        **meshOptsColourKwargs),
    'MeshOpts.cmapResolution'  : props.Widget(
        'cmapResolution',
        slider=True,
        spin=True,
        showLimits=False,
        **meshOptsColourKwargs),
    'MeshOpts.interpolateCmaps' : props.Widget(
        'interpolateCmaps',
        **meshOptsColourKwargs),
    'MeshOpts.invert'           : props.Widget(
        'invert',
        **meshOptsColourKwargs),
    'MeshOpts.invertClipping'   : props.Widget(
        'invertClipping',
        **meshOptsColourKwargs),
    'MeshOpts.linkLowRanges'    : props.Widget(
        'linkLowRanges',
        **meshOptsColourKwargs),
    'MeshOpts.linkHighRanges' : props.Widget(
        'linkHighRanges',
        **meshOptsColourKwargs),
    'MeshOpts.displayRange'   : props.Widget(
        'displayRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['ColourMapOpts.displayRange.min'],
                strings.choices['ColourMapOpts.displayRange.max']],
        **meshOptsColourKwargs),
    'MeshOpts.clippingRange'  : props.Widget(
        'clippingRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['ColourMapOpts.displayRange.min'],
                strings.choices['ColourMapOpts.displayRange.max']],
        dependencies=['vertexData', 'outline'],
        enabledWhen=lambda opts, vd, o: (vd is not None) and o),

    # TensorOpts
    'TensorOpts.lighting'         : props.Widget('lighting'),
    'TensorOpts.orientFlip'       : props.Widget('orientFlip'),
    'TensorOpts.tensorResolution' : props.Widget(
        'tensorResolution',
        showLimits=False,
        spin=False,
        labels=[strings.choices['TensorOpts.tensorResolution.min'],
                strings.choices['TensorOpts.tensorResolution.max']]),
    'TensorOpts.tensorScale'      : props.Widget(
        'tensorScale',
        showLimits=False,
        spin=False),

    # LabelOpts
    'LabelOpts.lut'          : props.Widget('lut', labels=lambda l: l.name),
    'LabelOpts.outline'      : props.Widget('outline'),
    'LabelOpts.outlineWidth' : props.Widget('outlineWidth', showLimits=False),
    'LabelOpts.volume'       : props.Widget(
        'volume',
        showLimits=False,
        enabledWhen=lambda o: o.overlay.is4DImage()),

    # SHOpts
    'SHOpts.shResolution'    : props.Widget(
        'shResolution',
        spin=False,
        showLimits=False),
    'SHOpts.shOrder'    : props.Widget('shOrder'),
    'SHOpts.orientFlip' : props.Widget('orientFlip'),
    'SHOpts.lighting'   : props.Widget('lighting'),
    'SHOpts.size'       : props.Widget(
        'size',
        spin=False,
        showLimits=False),
    'SHOpts.radiusThreshold' : props.Widget(
        'radiusThreshold',
        spin=False,
        showLimits=False),
    'SHOpts.colourMode'      : props.Widget(
        'colourMode',
        labels=strings.choices['SHOpts.colourMode'],
        dependencies=['colourImage'],
        enabledWhen=lambda o, ci: ci is None),
    'SHOpts.cmap' : props.Widget(
        'cmap',
        labels=fslcm.getColourMapLabel,
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is not None or cm == 'radius'),
    'SHOpts.xColour'         : props.Widget(
        'xColour',
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
    'SHOpts.yColour'         : props.Widget(
        'yColour',
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
    'SHOpts.zColour'         : props.Widget(
        'zColour',
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
    'SHOpts.suppressX'         : props.Widget(
        'suppressX',
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
    'SHOpts.suppressY'         : props.Widget(
        'suppressY',
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
    'SHOpts.suppressZ'         : props.Widget(
        'suppressZ',
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
    'SHOpts.suppressMode'         : props.Widget(
        'suppressMode',
        dependencies=['colourImage', 'colourMode'],
        enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
})
"""This dictionary contains specifications for all controls that are shown on
an ``OverlayDisplayPanel``.
"""
