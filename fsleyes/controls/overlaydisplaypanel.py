#!/usr/bin/env python
#
# overlaydisplaypanel.py - The OverlayDisplayPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides the :class:`OverlayDisplayPanel` class, a *FSLeyes
control* panel which allows the user to change overlay display settings.
"""


import logging
import functools

import wx
import props

import fsl.utils.typedict            as td
import fsleyes.strings               as strings
import fsleyes.tooltips              as fsltooltips
import fsleyes.panel                 as fslpanel
import fsleyes.colourmaps            as fslcm
import fsleyes.actions.loadcolourmap as loadcmap
import fsleyes.displaycontext        as displayctx


log = logging.getLogger(__name__)

    
class OverlayDisplayPanel(fslpanel.FSLEyesSettingsPanel):
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
    defined in the :attr:`_DISPLAY_PROPS` and :attr:`_DISPLAY_WIDGETS`
    dictionaries.
    """

    
    def __init__(self, parent, overlayList, displayCtx):
        """Create an ``OverlayDisplayPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        fslpanel.FSLEyesSettingsPanel.__init__(self,
                                               parent,
                                               overlayList,
                                               displayCtx)

        displayCtx .addListener('selectedOverlay',
                                 self._name,
                                 self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                 self._name,
                                 self.__selectedOverlayChanged)

        self.__currentOverlay = None
        self.__selectedOverlayChanged()

        
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

        self.__updateWidgets(display, 'display')
        self.__updateWidgets(opts,    'opts')

        widgetList.Expand('display', displayExpanded)
        widgetList.Expand('opts',    optsExpanded)
        
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
        widgets  = []

        for p in dispProps:

            widget = props.buildGUI(widgetList, target, p)

            # Build a panel for the VolumeOpts colour map controls.
            if isinstance(target, displayctx.VolumeOpts) and p.key == 'cmap':
                widget = self.__buildColourMapWidget(target, widget)
                
            widgets.append(widget)

        for label, tooltip, widget in zip(labels, tooltips, widgets):
            widgetList.AddWidget(
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

        widgets = self.getWidgetList()

        # Button to load a new
        # colour map from file
        loadAction = loadcmap.LoadColourMapAction(self._overlayList,
                                                  self._displayCtx)

        loadButton = wx.Button(widgets)
        loadButton.SetLabel(strings.labels[self, 'loadCmap'])

        loadAction.bindToWidget(self, wx.EVT_BUTTON, loadButton)

        # Negative colour map widget
        negCmap    = props.Widget('negativeCmap',
                                  labels=fslcm.getColourMapLabel,
                                  dependencies=['useNegativeCmap'],
                                  enabledWhen=lambda i, unc : unc)
        useNegCmap = props.Widget('useNegativeCmap')
        
        negCmap    = props.buildGUI(widgets, target, negCmap)
        useNegCmap = props.buildGUI(widgets, target, useNegCmap)

        useNegCmap.SetLabel(strings.properties[target, 'useNegativeCmap'])

        sizer = wx.FlexGridSizer(2, 2, 0, 0)
        sizer.AddGrowableCol(0)

        sizer.Add(cmapWidget, flag=wx.EXPAND)
        sizer.Add(loadButton, flag=wx.EXPAND)
        sizer.Add(negCmap,    flag=wx.EXPAND)
        sizer.Add(useNegCmap, flag=wx.EXPAND)
        
        return sizer


def _imageName(img):
    """Used to generate choice labels for the :attr`.VectorOpts.modulateImage`,
    :attr`.VectorOpts.clipImage`, :attr`.VectorOpts.colourImage` and
    :attr:`.ModelOpts.refImage` properties.
    """
    if img is None: return 'None'
    else:           return img.name


_DISPLAY_PROPS = td.TypeDict({
    'Display'        : ['name',
                        'overlayType',
                        'enabled',
                        'alpha',
                        'brightness',
                        'contrast'],
    'VolumeOpts'     : ['resolution',
                        'volume',
                        'interpolation',
                        'cmap',
                        'invert',
                        'invertClipping',
                        'linkLowRanges',
                        'linkHighRanges',
                        'displayRange',
                        'clippingRange',
                        'clipImage'],
    'MaskOpts'       : ['resolution',
                        'volume',
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
    'RGBVectorOpts'  : ['resolution',
                        'interpolation'],
    'LineVectorOpts' : ['directed',
                        'unitLength',
                        'neuroOrientFlip',
                        'resolution',
                        'lineWidth',
                        'lengthScale'],
    'ModelOpts'      : ['colour',
                        'outline',
                        'outlineWidth',
                        'refImage',
                        'coordSpace'],
    'TensorOpts'     : ['lighting',
                        'neuroOrientFlip',
                        'tensorResolution',
                        'tensorScale'],
    'LabelOpts'      : ['lut',
                        'outline',
                        'outlineWidth',
                        'resolution',
                        'volume'],
    'SHOpts'         : ['resolution',
                        'shResolution',
                        'shOrder',
                        'neuroOrientFlip',
                        'lighting',
                        'size',
                        'radiusThreshold',
                        'colourMode']
})
"""This dictionary contains lists of all the properties which are to be
displayed on an ``OverlayDisplayPanel``.
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

    # VolumeOpts
    'VolumeOpts.resolution'     : props.Widget('resolution', showLimits=False),
    'VolumeOpts.volume'         : props.Widget(
        'volume',
        showLimits=False,
        enabledWhen=lambda o: o.overlay.is4DImage()),
    'VolumeOpts.interpolation'  : props.Widget(
        'interpolation',
        labels=strings.choices['VolumeOpts.interpolation']),
    'VolumeOpts.cmap'           : props.Widget(
        'cmap',
        labels=fslcm.getColourMapLabel),
    'VolumeOpts.invert'         : props.Widget('invert'),
    'VolumeOpts.invertClipping' : props.Widget('invertClipping'),
    'VolumeOpts.linkLowRanges'  : props.Widget(
        'linkLowRanges',
        dependencies=['clipImage'],
        enabledWhen=lambda vo, ci: ci is None),
    'VolumeOpts.linkHighRanges' : props.Widget(
        'linkHighRanges',
        dependencies=['clipImage'],
        enabledWhen=lambda vo, ci: ci is None),
    'VolumeOpts.displayRange'   : props.Widget(
        'displayRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']]),
    'VolumeOpts.clippingRange'  : props.Widget(
        'clippingRange',
        showLimits=False,
        slider=True,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']]),
    'VolumeOpts.clipImage'      : props.Widget(
        'clipImage',
        labels=_imageName),

    # MaskOpts
    'MaskOpts.resolution' : props.Widget('resolution', showLimits=False),
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
    'RGBVectorOpts.resolution'    : props.Widget(
        'resolution',
        showLimits=False),
    'RGBVectorOpts.interpolation' : props.Widget(
        'interpolation',
        labels=strings.choices['VolumeOpts.interpolation']),

    # LineVectorOpts
    'LineVectorOpts.directed'        : props.Widget('directed'),
    'LineVectorOpts.unitLength'      : props.Widget('unitLength'),
    'LineVectorOpts.neuroOrientFlip' : props.Widget('neuroOrientFlip'),
    'LineVectorOpts.resolution'      : props.Widget('resolution',
                                                    showLimits=False),
    'LineVectorOpts.lineWidth'       : props.Widget('lineWidth',
                                                    showLimits=False),
    'LineVectorOpts.lengthScale'     : props.Widget('lengthScale',
                                                    showLimits=False),

    # ModelOpts
    'ModelOpts.colour'       : props.Widget('colour'),
    'ModelOpts.outline'      : props.Widget('outline'),
    'ModelOpts.outlineWidth' : props.Widget('outlineWidth', showLimits=False),
    'ModelOpts.refImage'     : props.Widget('refImage', labels=_imageName),
    'ModelOpts.coordSpace'   : props.Widget(
        'coordSpace',
        enabledWhen=lambda o, ri: ri != 'none',
        labels=strings.choices['ModelOpts.coordSpace'],
        dependencies=['refImage']),

        
    # TensorOpts
    'TensorOpts.lighting'         : props.Widget('lighting'),
    'TensorOpts.neuroOrientFlip'  : props.Widget('neuroOrientFlip'),
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
    'LabelOpts.resolution'   : props.Widget('resolution',   showLimits=False),
    'LabelOpts.volume'       : props.Widget(
        'volume',
        showLimits=False,
        enabledWhen=lambda o: o.overlay.is4DImage()),

    # SHOpts
    'SHOpts.resolution'      : props.Widget('resolution',   showLimits=False),
    'SHOpts.shResolution'    : props.Widget(
        'shResolution',
        spin=False,
        showLimits=False),
    'SHOpts.shOrder'         : props.Widget('shOrder'), 
    'SHOpts.neuroOrientFlip' : props.Widget('neuroOrientFlip'), 
    'SHOpts.lighting'        : props.Widget('lighting'), 
    'SHOpts.size'            : props.Widget(
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
