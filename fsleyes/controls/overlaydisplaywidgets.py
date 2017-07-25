#!/usr/bin/env python
#
# overlaydisplaywidgets.py - Contents of the OverlayDisplayPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module is used by the :class:`.OverlayDisplayPanel`. It contains
definitions of all the settings that are displayed on the
``OverlayDisplayPanel`` for each overlay type.
"""




import os.path as op
import            sys
import            functools

import fsleyes_props                  as props
import fsleyes_widgets.utils.typedict as td
import fsleyes.strings                as strings
import fsleyes.colourmaps             as fslcm


_PROPERTIES      = td.TypeDict()
_3D_PROPERTIES   = td.TypeDict()
_WIDGET_SPECS    = td.TypeDict()
_3D_WIDGET_SPECS = td.TypeDict()


def getPropertyList(target):

    plist = _getThing(target, '_initPropertyList_', _PROPERTIES)

    if plist is None:
        return []

    return functools.reduce(lambda a, b: a + b, plist)


def get3DPropertyList(target):

    plist = _getThing(target, '_init3DPropertyList_', _3D_PROPERTIES)

    if plist is None:
        return []

    return functools.reduce(lambda a, b: a + b, plist)


def getWidgetSpecs(target):

    sdicts = _getThing(target, '_initWidgetSpec_', _WIDGET_SPECS)

    if sdicts is None:
        return {}

    return functools.reduce(_merge_dicts, sdicts)


def get3DWidgetSpecs(target):

    sdicts = _getThing(target, '_init3DWidgetSpec_', _3D_WIDGET_SPECS)

    if sdicts is None:
        return {}

    return functools.reduce(_merge_dicts, sdicts)


def _merge_dicts(d1, d2):
    d3 = d1.copy()
    d3.update(d2)
    return d3


def _getThing(target, prefix, thingDict):

    thing = thingDict.get(target, None, allhits=True)

    if thing is not None:
        return thing

    keys, funcs = _getInitFuncs(prefix, target)

    for key, func in zip(keys, funcs):
        thingDict[key] = func()

    return thingDict.get(target, None, allhits=True)


def _getInitFuncs(prefix, target):

    if isinstance(target, type): ttype = target
    else:                        ttype = type(target)

    key   = ttype.__name__
    bases = ttype.__bases__

    thismod  = sys.modules[__name__]
    initFunc = '{}{}'.format(prefix, key)
    initFunc = getattr(thismod, initFunc, None)

    if initFunc is None:
        return [], []

    keys      = [key]
    initFuncs = [initFunc]

    for base in bases:
        bkeys, bfuncs = _getInitFuncs(prefix, base)

        keys     .extend(bkeys)
        initFuncs.extend(bfuncs)

    return keys, initFuncs


def _initPropertyList_Display():
    return ['name',
            'overlayType',
            'enabled',
            'alpha',
            'brightness',
            'contrast']


def _initPropertyList_VolumeOpts():
    return ['volume',
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
            'enableOverrideDataRange']


def _init3DPropertyList_VolumeOpts():
    return ['dithering',
            'numSteps',
            'numClipPlanes']


def _initPropertyList_MaskOpts():
    return ['volume',
            'colour',
            'invert',
            'threshold']


def _initPropertyList_VectorOpts():
    return ['colourImage',
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
            'suppressMode']


def _initPropertyList_RGBVectorOpts():
    return ['interpolation']


def _initPropertyList_LineVectorOpts():
    return ['directed',
            'unitLength',
            'orientFlip',
            'lineWidth',
            'lengthScale']


def _initPropertyList_TensorOpts():
    return ['lighting',
            'orientFlip',
            'tensorResolution',
            'tensorScale']


def _initPropertyList_MeshOpts():
    return ['refImage',
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
            'discardClipped',
            'linkLowRanges',
            'linkHighRanges',
            'displayRange',
            'clippingRange',
            'wireframe',
            'lighting']


def _initPropertyList_LabelOpts():
    return ['lut',
            'outline',
            'outlineWidth',
            'volume']


def _initPropertyList_SHOpts():
    return ['shResolution',
            'shOrder',
            'orientFlip',
            'lighting',
            'size',
            'radiusThreshold',
            'colourMode']


def _initWidgetSpec_Display():
    return {
        'name'        : props.Widget('name'),
        'overlayType' : props.Widget(
            'overlayType',
            labels=strings.choices['Display.overlayType']),
        'enabled'     : props.Widget('enabled'),
        'alpha'       : props.Widget('alpha',      showLimits=False),
        'brightness'  : props.Widget('brightness', showLimits=False),
        'contrast'    : props.Widget('contrast',   showLimits=False),
    }


def _initWidgetSpec_ColourMapOpts():
    return {
        'cmap'           : props.Widget(
            'cmap',
            labels=fslcm.getColourMapLabel),
        'useNegativeCmap' : props.Widget('useNegativeCmap'),
        'negativeCmap'    : props.Widget(
            'negativeCmap',
            labels=fslcm.getColourMapLabel,
            dependencies=['useNegativeCmap'],
            enabledWhen=lambda i, unc : unc),
        'cmapResolution'  : props.Widget(
            'cmapResolution',
            slider=True,
            spin=True,
            showLimits=False),
        'interpolateCmaps' : props.Widget('interpolateCmaps'),
        'invert'           : props.Widget('invert'),
        'invertClipping'   : props.Widget('invertClipping'),
        'linkLowRanges'    : props.Widget('linkLowRanges'),
        'linkHighRanges'   : props.Widget('linkHighRanges'),
        'displayRange'     : props.Widget(
            'displayRange',
            showLimits=False,
            slider=True,
            labels=[strings.choices['ColourMapOpts.displayRange.min'],
                    strings.choices['ColourMapOpts.displayRange.max']]),
        'clippingRange'  : props.Widget(
            'clippingRange',
            showLimits=False,
            slider=True,
            labels=[strings.choices['ColourMapOpts.displayRange.min'],
                    strings.choices['ColourMapOpts.displayRange.max']]),
    }


def _initWidgetSpec_VolumeOpts():

    def imageName(img):
        if img is None: return 'None'
        else:           return img.name

    return {
        'volume'         : props.Widget(
            'volume',
            showLimits=False,
            enabledWhen=lambda o: o.overlay.is4DImage()),
        'interpolation'  : props.Widget(
            'interpolation',
            labels=strings.choices['VolumeOpts.interpolation']),
        'clipImage'      : props.Widget(
            'clipImage',
            labels=imageName),
        'enableOverrideDataRange'  : props.Widget(
            'enableOverrideDataRange'),
        'overrideDataRange' : props.Widget(
            'overrideDataRange',
            showLimits=False,
            spin=True,
            slider=False,
            dependencies=['enableOverrideDataRange'],
            enabledWhen=lambda vo, en: en),
    }

def _init3DWidgetSpec_VolumeOpts():

    return {
        'dithering'     : props.Widget('dithering',     showLimits=False),
        'numSteps'      : props.Widget('numSteps',      showLimits=False),
        'numClipPlanes' : props.Widget('numClipPlanes', showLimits=False),
    }


def _initWidgetSpec_MaskOpts():
    return {
        'volume'     : props.Widget(
            'volume',
            showLimits=False,
            enabledWhen=lambda o: o.overlay.is4DImage()),
        'colour'     : props.Widget('colour'),
        'invert'     : props.Widget('invert'),
        'threshold'  : props.Widget('threshold', showLimits=False),
    }


def _initWidgetSpec_LabelOpts():
    return {
        'lut'          : props.Widget('lut', labels=lambda l: l.name),
        'outline'      : props.Widget('outline'),
        'outlineWidth' : props.Widget('outlineWidth', showLimits=False),
        'volume'       : props.Widget(
            'volume',
            showLimits=False,
            enabledWhen=lambda o: o.overlay.is4DImage()),
    }


def _initWidgetSpec_VectorOpts():
    def imageName(img):
        if img is None: return 'None'
        else:           return img.name

    return {
        'colourImage'   : props.Widget(
            'colourImage',
            labels=imageName),
        'modulateImage' : props.Widget(
            'modulateImage',
            labels=imageName,
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'clipImage'     : props.Widget('clipImage', labels=imageName),
        'cmap'          : props.Widget(
            'cmap',
            labels=fslcm.getColourMapLabel,
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is not None),
        'clippingRange' : props.Widget(
            'clippingRange',
            showLimits=False,
            slider=True,
            labels=[strings.choices['VectorOpts.clippingRange.min'],
                    strings.choices['VectorOpts.clippingRange.max']],
            dependencies=['clipImage'],
            enabledWhen=lambda o, ci: ci is not None),
        'modulateRange' : props.Widget(
            'modulateRange',
            showLimits=False,
            slider=True,
            labels=[strings.choices['VectorOpts.modulateRange.min'],
                    strings.choices['VectorOpts.modulateRange.max']],
            dependencies=['colourImage', 'modulateImage'],
            enabledWhen=lambda o, ci, mi: ci is None and mi is not None),
        'xColour'       : props.Widget(
            'xColour',
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'yColour'       : props.Widget(
            'yColour',
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'zColour'       : props.Widget(
            'zColour',
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'suppressX'     : props.Widget(
            'suppressX',
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'suppressY'     : props.Widget(
            'suppressY',
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'suppressZ'     : props.Widget(
            'suppressZ',
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'suppressMode'  : props.Widget(
            'suppressMode',
            dependencies=['colourImage'],
            labels=strings.choices['VectorOpts.suppressMode'],
            enabledWhen=lambda o, ci: ci is None),
    }


def _initWidgetSpec_RGBVectorOpts():
    return {
        'interpolation' : props.Widget(
            'interpolation',
            labels=strings.choices['VolumeOpts.interpolation'])
    }


def _initWidgetSpec_LineVectorOpts():
    return {
        'directed'    : props.Widget('directed'),
        'unitLength'  : props.Widget('unitLength'),
        'orientFlip'  : props.Widget('orientFlip'),
        'lineWidth'   : props.Widget('lineWidth',   showLimits=False),
        'lengthScale' : props.Widget('lengthScale', showLimits=False),
    }


def _initWidgetSpec_TensorOpts():
    return {
        'lighting'         : props.Widget('lighting'),
        'orientFlip'       : props.Widget('orientFlip'),
        'tensorResolution' : props.Widget(
            'tensorResolution',
            showLimits=False,
            spin=False,
            labels=[strings.choices['TensorOpts.tensorResolution.min'],
                    strings.choices['TensorOpts.tensorResolution.max']]),
        'tensorScale'      : props.Widget(
            'tensorScale',
            showLimits=False,
            spin=False),
    }

def _initWidgetSpec_SHOpts():
    return {
        'shResolution'    : props.Widget(
            'shResolution',
            spin=False,
            showLimits=False),
        'shOrder'    : props.Widget('shOrder'),
        'orientFlip' : props.Widget('orientFlip'),
        'lighting'   : props.Widget('lighting'),
        'size'       : props.Widget(
            'size',
            spin=False,
            showLimits=False),
        'radiusThreshold' : props.Widget(
            'radiusThreshold',
            spin=False,
            showLimits=False),
        'colourMode'      : props.Widget(
            'colourMode',
            labels=strings.choices['SHOpts.colourMode'],
            dependencies=['colourImage'],
            enabledWhen=lambda o, ci: ci is None),
        'cmap' : props.Widget(
            'cmap',
            labels=fslcm.getColourMapLabel,
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is not None or cm == 'radius'),
        'xColour'         : props.Widget(
            'xColour',
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
        'yColour'         : props.Widget(
            'yColour',
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
        'zColour'         : props.Widget(
            'zColour',
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
        'suppressX'         : props.Widget(
            'suppressX',
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
        'suppressY'         : props.Widget(
            'suppressY',
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
        'suppressZ'         : props.Widget(
            'suppressZ',
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
        'suppressMode'         : props.Widget(
            'suppressMode',
            dependencies=['colourImage', 'colourMode'],
            enabledWhen=lambda o, ci, cm: ci is None and cm == 'direction'),
    }



def _initWidgetSpec_MeshOpts():

    def imageName(img):
        if img is None: return 'None'
        else:           return img.name

    def vertexDataName(vdata):
        if vdata is None: return 'None'
        else:             return op.basename(vdata)

    def colourEnabledWhen(opts, vdata, outline, useLut):
        return outline and (vdata is not None) and (not useLut)

    colourKwargs = {
        'dependencies' : ['vertexData', 'outline', 'useLut'],
        'enabledWhen'  : colourEnabledWhen
    }

    return {
        'outline'      : props.Widget('outline'),
        'outlineWidth' : props.Widget(
            'outlineWidth',
            showLimits=False,
            dependencies=['outline'],
            enabledWhen=lambda o, outline: outline),
        'refImage'     : props.Widget('refImage', labels=imageName),
        'coordSpace'   : props.Widget(
            'coordSpace',
            enabledWhen=lambda o, ri: ri != 'none',
            labels=strings.choices['MeshOpts.coordSpace'],
            dependencies=['refImage']),
        'colour'       : props.Widget('colour'),
        'vertexData'   : props.Widget(
            'vertexData',
            labels=vertexDataName),
        'vertexDataIndex' : props.Widget(
            'vertexDataIndex',
            showLimits=False,
            dependencies=['vertexData'],
            enabledWhen=lambda o, vd: vd is not None),
        'useLut' : props.Widget(
            'useLut',
            dependencies=['outline'],
            enabledWhen=lambda opts, o: o),
        'lut'    : props.Widget(
            'lut',
            labels=lambda l: l.name,
            dependencies=['outline'],
            enabledWhen=lambda opts, o: o),

        # We override the ColourMapOpts definitions
        # for custom enabledWhen behaviour.
        'cmap'           : props.Widget(
            'cmap',
            labels=fslcm.getColourMapLabel,
            **colourKwargs),

        'useNegativeCmap' : props.Widget(
            'useNegativeCmap',
            **colourKwargs),
        'negativeCmap'    : props.Widget(
            'negativeCmap',
            labels=fslcm.getColourMapLabel,
            **colourKwargs),
        'cmapResolution'  : props.Widget(
            'cmapResolution',
            slider=True,
            spin=True,
            showLimits=False,
            **colourKwargs),
        'interpolateCmaps' : props.Widget(
            'interpolateCmaps',
            **colourKwargs),
        'invert'           : props.Widget(
            'invert',
            **colourKwargs),
        'invertClipping'   : props.Widget(
            'invertClipping',
            **colourKwargs),
        'linkLowRanges'    : props.Widget(
            'linkLowRanges',
            **colourKwargs),
        'linkHighRanges' : props.Widget(
            'linkHighRanges',
            **colourKwargs),
        'displayRange'   : props.Widget(
            'displayRange',
            showLimits=False,
            slider=True,
            labels=[strings.choices['ColourMapOpts.displayRange.min'],
                    strings.choices['ColourMapOpts.displayRange.max']],
            **colourKwargs),
        'clippingRange'  : props.Widget(
            'clippingRange',
            showLimits=False,
            slider=True,
            labels=[strings.choices['ColourMapOpts.displayRange.min'],
                    strings.choices['ColourMapOpts.displayRange.max']],
            dependencies=['vertexData', 'outline'],
            enabledWhen=lambda opts, vd, o: (vd is not None) and o),
        'discardClipped' : props.Widget(
            'discardClipped',
            **colourKwargs),
        'wireframe'     :  props.Widget('wireframe'),
        'lighting'      :  props.Widget('lighting'),
    }
