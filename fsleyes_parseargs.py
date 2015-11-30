#!/usr/bin/env python
#
# fsleyes_parseargs.py - Parsing FSLEyes command line arguments.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module encapsulates the logic for parsing command line arguments which
specify a scene to be displayed in *FSLeyes*.  This logic is shared between
the :mod:`~fsl.tools.fsleyes` and :mod:`~fsl.tools.render` tools.  This module
make use of the command line generation features of the :mod:`props` package.


There are a lot of command line arguments made available to the user,
broadly split into the following groups:

 - *Main* arguments control the overall scene display, such as the
   display type (e.g. orthographic or lightbox), the displayed location,
   and whether to show a colour bar.


 - *Display* arguments control the display for a single overlay file (e.g.
   a NIFTI1 image), such as interpolation, colour map, etc.


This module provides the following functions: 

.. autosummary::
   :nosignatures:

   parseArgs
   applySceneArgs
   generateSceneArgs
   generateOverlayArgs
   applyOverlayArgs


-------------------------------
Adding new command line options
-------------------------------


Most classes in *FSLeyes* derive from the :class:`.HasProperties` class of the
:mod:`props` package. Therefore, with only a couple of excpetions, the
processing of nearly all *FSLeyes* command line arguments is completely
automatic.

Therefore, adding a new command line option is fairly easy.  For example,
let's say you have added a new property on the :class:`.ModelOpts` class,
called ``rotation``::

    class ModelOpts(fsldisplay.DisplayOpts):
        # .
        # .
        # .
        rotation = props.Int(minval=0, maxval=360, clamped=True)
        # .
        # .
        # .

To make this new propery settable via the command line, you need to:

  1. Add an entry to the :data:`OPTIONS` dictionary::

         OPTIONS = td.TypeDict({
             # .
             # .
             # .
             'ModelOpts'      : ['colour',
                                 'outline',
                                 'outlineWidth',
                                 'refImage',
                                 'rotation'],
             # .
             # .
             # .
         })

  2. Specify the command line flags to use, in the :data:`ARGUMENTS`
     dictionary::

         ARGUMENTS = td.TypeDict({
             # .
             # .
             # .
             'ModelOpts.rotation' : ('mr', 'modelRotation'),
             # .
             # .
             # .
         })

  3. Add a description in the :data:`HELP` dictionary::

         HELP = td.TypeDict({
             # .
             # .
             # .
             'ModelOpts.rotation' : 'Rotate the model by this much',
             # .
             # .
             # .
         })
"""

import sys
import os.path as op
import functools
import argparse
import logging

import props

import fsl.utils.typedict as td

import overlay as fsloverlay

# The colour maps module needs to be imported
# before the displaycontext.opts modules are
# imported, as some of their class definitions
# rely on the colourmaps being initialised
import colourmaps as colourmaps
colourmaps.init()

import displaycontext as fsldisplay

import displaydefaults


log = logging.getLogger(__name__)


def concat(lists):
    """Concatenates a list of lists.

    This function is used a few times, and writing concat(lists) is
    nicer-looking than writing lambda blah blah each time.
    """
    return functools.reduce(lambda a, b: a + b, lists)


# Names of all of the property which are 
# customisable via command line arguments.
OPTIONS = td.TypeDict({

    'Main'          : ['help',
                       'glversion',
                       'scene',
                       'voxelLoc',
                       'worldLoc',
                       'selectedOverlay',
                       'defaultDisplay'],

    # From here on, all of the keys are
    # the names of HasProperties classes,
    # and all of the values are the 
    # names of properties on them.
    
    'SceneOpts'     : ['showCursor',
                       'bgColour',
                       'cursorColour',
                       'showColourBar',
                       'colourBarLocation',
                       'colourBarLabelSide',
                       'performance'],
    'OrthoOpts'     : ['xzoom',
                       'yzoom',
                       'zzoom',
                       'showLabels',
                       'layout',
                       'showXCanvas',
                       'showYCanvas',
                       'showZCanvas'],
    'LightBoxOpts'  : ['sliceSpacing',
                       'ncols',
                       'nrows',
                       'zrange',
                       'showGridLines',
                       'highlightSlice',
                       'zax'],

    # The order in which properties are listed
    # here is the order in which they are applied.
    'Display'        : ['name',
                        'overlayType',
                        'alpha',
                        'brightness',
                        'contrast'],
    'ImageOpts'      : ['transform',
                        'resolution',
                        'volume'],
    'VolumeOpts'     : ['cmap',
                        'displayRange',
                        'clippingRange',
                        'invert',
                        'invertClipping',
                        'interpolation'],
    'MaskOpts'       : ['colour',
                        'invert',
                        'threshold'],
    'VectorOpts'     : ['xColour',
                        'yColour',
                        'zColour',
                        'suppressX',
                        'suppressY',
                        'suppressZ',
                        'modulate',
                        'modThreshold'],
    'LineVectorOpts' : ['lineWidth',
                        'directed'],
    'RGBVectorOpts'  : ['interpolation'],
    'ModelOpts'      : ['colour',
                        'outline',
                        'outlineWidth',
                        'refImage'],
    'LabelOpts'      : ['lut',
                        'outline',
                        'outlineWidth'],
})
"""This dictionary defines all of the options which are exposed on the command
line.

With the exception of ``Main``, every key is the name of a
:class:`.HasProperties` class, and the list of values are the names of
properties on that class.
"""


# Headings for each of the option groups
GROUPNAMES = td.TypeDict({
    'Main'           : 'Main options',
    'SceneOpts'      : 'Scene options',
    'OrthoOpts'      : 'Ortho display options',
    'LightBoxOpts'   : 'LightBox display options',
    
    'Display'        : 'Overlay display options',
    'ImageOpts'      : 'Options for NIFTI images',
    'VolumeOpts'     : 'Volume options',
    'MaskOpts'       : 'Mask options',
    'VectorOpts'     : 'Vector options',
    'LineVectorOpts' : 'Line vector options',
    'RGBVectorOpts'  : 'RGB vector options',
    'ModelOpts'      : 'Model options',
    'LabelOpts'      : 'Label options',
})
"""Command line arguments are grouped according to the class to which
they are applied (see the :data:`ARGUMENTS` dictionary). This dictionary
defines descriptions for ecah command line group.
"""

# Descriptions for each group
GROUPDESCS = td.TypeDict({

    'SceneOpts'    : 'These settings are only applied if the \'--scene\' '
                     'option is set to \'lightbox\' or \'ortho\'.',

    'OrthoOpts'    : 'These settings are only applied if the \'--scene\' '
                     'option is set to \'ortho\'.', 

    'LightBoxOpts' : 'These settings are only applied if the \'--scene\' '
                     'option is set to \'lightbox\'.',
 
    'Display'      : 'Each display option will be applied to the '
                     'overlay which is listed before that option.'
})
"""This dictionary contains descriptions for each argument group. """

# Short/long arguments for all of those options
# 
# There cannot be any collisions between the main
# options, the scene options, and the colour bar
# options.
#
# There can't be any collisions between the 
# Display options and the *Opts options.
ARGUMENTS = td.TypeDict({

    'Main.help'            : ('h',  'help'),
    'Main.glversion'       : ('gl', 'glversion'),
    'Main.scene'           : ('s',  'scene'),
    'Main.voxelLoc'        : ('v',  'voxelloc'),
    'Main.worldLoc'        : ('w',  'worldloc'),
    'Main.selectedOverlay' : ('o',  'selectedOverlay'),
    'Main.defaultDisplay'  : ('d',  'defaultDisplay'),
    
    'SceneOpts.showColourBar'      : ('cb',  'showColourBar'),
    'SceneOpts.bgColour'           : ('bg',  'bgColour'),
    'SceneOpts.cursorColour'       : ('cc',  'cursorColour'),
    'SceneOpts.colourBarLocation'  : ('cbl', 'colourBarLocation'),
    'SceneOpts.colourBarLabelSide' : ('cbs', 'colourBarLabelSide'),
    'SceneOpts.showCursor'         : ('hc',  'hideCursor'),
    'SceneOpts.performance'        : ('p',   'performance'),
    
    'OrthoOpts.xzoom'       : ('xz', 'xzoom'),
    'OrthoOpts.yzoom'       : ('yz', 'yzoom'),
    'OrthoOpts.zzoom'       : ('zz', 'zzoom'),
    'OrthoOpts.layout'      : ('lo', 'layout'),
    'OrthoOpts.showXCanvas' : ('xh', 'hidex'),
    'OrthoOpts.showYCanvas' : ('yh', 'hidey'),
    'OrthoOpts.showZCanvas' : ('zh', 'hidez'),
    'OrthoOpts.showLabels'  : ('lh', 'hideLabels'),

    'OrthoOpts.xcentre'     : ('xc', 'xcentre'),
    'OrthoOpts.ycentre'     : ('yc', 'ycentre'),
    'OrthoOpts.zcentre'     : ('zc', 'zcentre'),

    'LightBoxOpts.sliceSpacing'   : ('ss', 'sliceSpacing'),
    'LightBoxOpts.ncols'          : ('nc', 'ncols'),
    'LightBoxOpts.nrows'          : ('nr', 'nrows'),
    'LightBoxOpts.zrange'         : ('zr', 'zrange'),
    'LightBoxOpts.showGridLines'  : ('sg', 'showGridLines'),
    'LightBoxOpts.highlightSlice' : ('hs', 'highlightSlice'),
    'LightBoxOpts.zax'            : ('zx', 'zaxis'),

    'Display.name'          : ('n',  'name'),
    'Display.overlayType'   : ('ot', 'overlayType'),
    'Display.alpha'         : ('a',  'alpha'),
    'Display.brightness'    : ('b',  'brightness'),
    'Display.contrast'      : ('c',  'contrast'),

    'ImageOpts.resolution'    : ('r',  'resolution'),
    'ImageOpts.transform'     : ('tf', 'transform'),
    'ImageOpts.volume'        : ('vl', 'volume'),

    'VolumeOpts.displayRange'   : ('dr', 'displayRange'),
    'VolumeOpts.interpolation'  : ('in', 'interp'),
    'VolumeOpts.invertClipping' : ('ic', 'invertClipping'),
    'VolumeOpts.clippingRange'  : ('cr', 'clippingRange'),
    'VolumeOpts.cmap'           : ('cm', 'cmap'),
    'VolumeOpts.invert'         : ('ci', 'cmapInvert'),

    'MaskOpts.colour'    : ('co', 'maskColour'),
    'MaskOpts.invert'    : ('mi', 'maskInvert'),
    'MaskOpts.threshold' : ('t',  'threshold'),

    'VectorOpts.xColour'     : ('xc', 'xColour'),
    'VectorOpts.yColour'     : ('yc', 'yColour'),
    'VectorOpts.zColour'     : ('zc', 'zColour'),
    'VectorOpts.suppressX'   : ('xs', 'suppressX'),
    'VectorOpts.suppressY'   : ('ys', 'suppressY'),
    'VectorOpts.suppressZ'   : ('zs', 'suppressZ'),
    'VectorOpts.modulate'    : ('m',  'modulate'),
    'VectorOpts.modThreshold': ('mt', 'modThreshold'),

    'LineVectorOpts.lineWidth'    : ('lvw', 'lineWidth'),
    'LineVectorOpts.directed'     : ('lvi', 'directed'),
    'RGBVectorOpts.interpolation' : ('rvi', 'rvInterpolation'),

    'ModelOpts.colour'       : ('mc',  'modelColour'),
    'ModelOpts.outline'      : ('mo',  'modelOutline'),
    'ModelOpts.outlineWidth' : ('mw',  'modelOutlineWidth'),
    'ModelOpts.refImage'     : ('mr',  'modelRefImage'),

    'LabelOpts.lut'          : ('ll',  'lut'),
    'LabelOpts.outline'      : ('lo',  'labelOutline'),
    'LabelOpts.outlineWidth' : ('lw',  'labelOutlineWidth'),
})
"""This dictionary defines the short and long command line flags to be used
for every option.

.. note:: 1. There cannot be any collisions between the main options, the 
             :class:`.SceneOpts` options, the :class:`.OrthOpts` options,
             and the :class:`.LightBoxOpts` options.

          2. There cannot be any collisions between the :class:`.Display`
             options and any of the :class:`.DisplayOpts` options.

          3. There *can* be collisions between these two groups though.
"""

# Help text for all of the options
HELP = td.TypeDict({

    'Main.help'          : 'Display this help and exit',
    'Main.glversion'     : 'Desired (major, minor) OpenGL version',
    'Main.scene'         : 'Scene to show. If not provided, the '
                           'previous scene layout is restored.',

    # TODO how about other overlay types?
    'Main.voxelLoc'        : 'Location to show (voxel coordinates of '
                             'first overlay)',
    'Main.worldLoc'        : 'Location to show (world coordinates, '
                             'takes precedence over --voxelloc)',
    'Main.selectedOverlay' : 'Selected overlay (default: last)',
    'Main.defaultDisplay'  : 'Apply default display settings to overlays '
                             '(unless any display setting specified)',

    'SceneOpts.showCursor'         : 'Do not display the green cursor '
                                     'highlighting the current location',
    'SceneOpts.bgColour'           : 'Canvas background colour',
    'SceneOpts.cursorColour'       : 'Cursor location colour',
    'SceneOpts.showColourBar'      : 'Show colour bar',
    'SceneOpts.colourBarLocation'  : 'Colour bar location',
    'SceneOpts.colourBarLabelSide' : 'Colour bar label orientation',
    'SceneOpts.performance'        : 'Rendering performance '
                                     '(1=fastest, 5=best looking)',
    
    'OrthoOpts.xzoom'       : 'X canvas zoom',
    'OrthoOpts.yzoom'       : 'Y canvas zoom',
    'OrthoOpts.zzoom'       : 'Z canvas zoom',
    'OrthoOpts.layout'      : 'Canvas layout',
    'OrthoOpts.showXCanvas' : 'Hide the X canvas',
    'OrthoOpts.showYCanvas' : 'Hide the Y canvas',
    'OrthoOpts.showZCanvas' : 'Hide the Z canvas',
    'OrthoOpts.showLabels'  : 'Hide orientation labels',

    'OrthoOpts.xcentre'     : 'X canvas display centre (world coordinates)',
    'OrthoOpts.ycentre'     : 'Y canvas display centre (world coordinates)',
    'OrthoOpts.zcentre'     : 'Z canvas display centre (world coordinates)',

    'LightBoxOpts.sliceSpacing'   : 'Slice spacing',
    'LightBoxOpts.ncols'          : 'Number of columns',
    'LightBoxOpts.nrows'          : 'Number of rows',
    'LightBoxOpts.zrange'         : 'Slice range',
    'LightBoxOpts.showGridLines'  : 'Show grid lines',
    'LightBoxOpts.highlightSlice' : 'Highlight current slice',
    'LightBoxOpts.zax'            : 'Z axis',

    'Display.name'          : 'Overlay name',
    'Display.overlayType'   : 'Overlay type',
    'Display.alpha'         : 'Opacity',
    'Display.brightness'    : 'Brightness',
    'Display.contrast'      : 'Contrast',

    'ImageOpts.resolution' : 'Resolution',
    'ImageOpts.transform'  : 'Transformation',
    'ImageOpts.volume'     : 'Volume',

    'VolumeOpts.displayRange'   : 'Display range',
    'VolumeOpts.clippingRange'  : 'Clipping range',
    'VolumeOpts.invertClipping' : 'Invert clipping',
    'VolumeOpts.cmap'           : 'Colour map',
    'VolumeOpts.interpolation'  : 'Interpolation',
    'VolumeOpts.invert'         : 'Invert colour map',

    'MaskOpts.colour'    : 'Colour',
    'MaskOpts.invert'    : 'Invert',
    'MaskOpts.threshold' : 'Threshold',

    'VectorOpts.xColour'      : 'X colour',
    'VectorOpts.yColour'      : 'Y colour',
    'VectorOpts.zColour'      : 'Z colour',
    'VectorOpts.suppressX'    : 'Suppress X magnitude',
    'VectorOpts.suppressY'    : 'Suppress Y magnitude',
    'VectorOpts.suppressZ'    : 'Suppress Z magnitude',
    'VectorOpts.modulate'     : 'Modulate vector colours',
    'VectorOpts.modThreshold' : 'Hide voxels where modulation '
                                'value is below this threshold '
                                '(expressed as a percentage)',

    'LineVectorOpts.lineWidth'    : 'Line width',
    'LineVectorOpts.directed'     : 'Interpret vectors as directed',
    'RGBVectorOpts.interpolation' : 'Interpolation',

    'ModelOpts.colour'       : 'Model colour',
    'ModelOpts.outline'      : 'Show model outline',
    'ModelOpts.outlineWidth' : 'Model outline width',
    'ModelOpts.refImage'     : 'Reference image for model',
    
    'LabelOpts.lut'          : 'Label image LUT',
    'LabelOpts.outline'      : 'Show label outlines',
    'LabelOpts.outlineWidth' : 'Label outline width', 
})
"""This dictionary defines the help text for all command line options."""


# Extra settings for some properties, passed through 
# to the props.cli.addParserArguments function.
EXTRA = td.TypeDict({
    'Display.overlayType' : {'choices' : fsldisplay.ALL_OVERLAY_TYPES,
                             'default' : fsldisplay.ALL_OVERLAY_TYPES[0]},

    'LabelOpts.lut'       : {
        # The LabelOpts.lut choice property has
        # LookupTable instances as values, which
        # obviously cannot be passed in on the
        # command line. But the lut property will
        # also accept the lut key as an alternate
        # value, so we accept these on the command
        # line instead. See the colourmaps and
        # labelopts modules for more detail.
        'choices'       : [],
        'useAlts'       : True
    }
})
"""This dictionary defines any extra settings to be passed through
to the :func:`.props.addParserArguments` function.
"""

# Transform functions for properties where the
# value passed in on the command line needs to
# be manipulated before the property value is
# set
#
# TODO If/when you have a need for more
# complicated property transformations (i.e.
# non-reversible ones), you'll need to have
# an inverse transforms dictionary
def _imageTrans(i):
    if i == 'none': return None
    else:           return i.dataSource


def _lutTrans(l):
    if isinstance(l, colourmaps.LookupTable): return l.key
    else:                                     return l

    
TRANSFORMS = td.TypeDict({
    'SceneOpts.showCursor'  : lambda b: not b,
    'OrthoOpts.showXCanvas' : lambda b: not b,
    'OrthoOpts.showYCanvas' : lambda b: not b,
    'OrthoOpts.showZCanvas' : lambda b: not b,
    'OrthoOpts.showLabels'  : lambda b: not b,

    # These properties are handled specially
    # when reading in command line arguments -
    # the transform function specified here
    # is only used when generating arguments
    'VectorOpts.modulate'   : _imageTrans,
    'ModelOpts.refImage'    : _imageTrans,

    'LabelOpts.lut'         : _lutTrans,
})
"""This dictionary defines any transformations for command line options
where the value passed on the command line cannot be directly converted
into the corresponding property value.
"""


def _setupParsers(mainParser):
    """Sets up an argument parser which handles options related
    to the scene. This function configures the following argument
    groups:
    
      - *Main*:         Top level optoins
      - *SceneOpts*:    Common scene options
      - *OrthoOpts*:    Options related to setting up a orthographic display
      - *LightBoxOpts*: Options related to setting up a lightbox display
    """

    # FSLEyes application options

    # Options defining the overall scene,
    # and separate parser groups for scene
    # settings, ortho, and lightbox.
 
    mainGroup  = mainParser.add_argument_group(GROUPNAMES[    'Main'],
                                               GROUPDESCS.get('Main'))
    sceneGroup = mainParser.add_argument_group(GROUPNAMES[    'SceneOpts'],
                                               GROUPDESCS.get('SceneOpts'))
    orthoGroup = mainParser.add_argument_group(GROUPNAMES[    'OrthoOpts'],
                                               GROUPDESCS.get('OrthoOpts'))
    lbGroup    = mainParser.add_argument_group(GROUPNAMES[    'LightBoxOpts'],
                                               GROUPDESCS.get('LightBoxOpts'))

    _configMainParser(     mainGroup)
    _configSceneParser(    sceneGroup)
    _configOrthoParser(    orthoGroup)
    _configLightBoxParser( lbGroup)


def _configParser(target, parser, propNames=None):
    """Configures the given parser so it will parse arguments for the
    given target.
    """

    if propNames is None:
        propNames = OPTIONS[target]
    shortArgs = {}
    longArgs  = {}
    helpTexts = {}
    extra     = {}

    for propName in propNames:

        shortArg, longArg = ARGUMENTS[ target, propName]
        helpText          = HELP[      target, propName]
        propExtra         = EXTRA.get((target, propName), None)

        shortArgs[propName] = shortArg
        longArgs[ propName] = longArg
        helpTexts[propName] = helpText

        if propExtra is not None:
            extra[propName] = propExtra

    props.addParserArguments(target,
                             parser,
                             cliProps=propNames,
                             shortArgs=shortArgs,
                             longArgs=longArgs,
                             propHelp=helpTexts,
                             extra=extra)


def _configMainParser(mainParser):
    """Adds options to the given parser which allow the user to specify
    *main* FSLeyes options.
    """
    mainArgs = {name: ARGUMENTS['Main', name] for name in OPTIONS['Main']}
    mainHelp = {name: HELP[     'Main', name] for name in OPTIONS['Main']}

    for name, (shortArg, longArg) in mainArgs.items():
        mainArgs[name] = ('-{}'.format(shortArg), '--{}'.format(longArg))

    mainParser.add_argument(*mainArgs['help'],
                            action='store_true',
                            help=mainHelp['help'])
    mainParser.add_argument(*mainArgs['glversion'],
                            metavar=('MAJOR', 'MINOR'),
                            type=int,
                            nargs=2,
                            help=mainHelp['glversion'])
    mainParser.add_argument(*mainArgs['scene'],
                            choices=('ortho', 'lightbox'),
                            help=mainHelp['scene'])
    mainParser.add_argument(*mainArgs['voxelLoc'],
                            metavar=('X', 'Y', 'Z'),
                            type=int,
                            nargs=3,
                            help=mainHelp['voxelLoc'])
    mainParser.add_argument(*mainArgs['worldLoc'],
                            metavar=('X', 'Y', 'Z'),
                            type=float,
                            nargs=3,
                            help=mainHelp['worldLoc'])
    mainParser.add_argument(*mainArgs['selectedOverlay'],
                            type=int,
                            help=mainHelp['selectedOverlay'])
    mainParser.add_argument(*mainArgs['defaultDisplay'],
                            action='store_true',
                            help=mainHelp['defaultDisplay']) 
    

def _configSceneParser(sceneParser):
    """Adds options to the given argument parser which allow
    the user to specify :class:`.SceneOpts` properties.
    """
    _configParser(fsldisplay.SceneOpts, sceneParser)
   

def _configOrthoParser(orthoParser):
    """Adds options to the given parser allowing the user to
    configure :class:`.OrthoOpts` properties.
    """

    OrthoOpts = fsldisplay.OrthoOpts
    _configParser(OrthoOpts, orthoParser)
                             
    # Extra configuration options that are
    # not OrthoPanel properties, so can't
    # be automatically set up
    for opt, metavar in zip(['xcentre',  'ycentre',  'zcentre'],
                            [('Y', 'Z'), ('X', 'Z'), ('X', 'Y')]):
        
        shortArg, longArg = ARGUMENTS[OrthoOpts, opt]
        helpText          = HELP[     OrthoOpts, opt]

        shortArg =  '-{}'.format(shortArg)
        longArg  = '--{}'.format(longArg)

        orthoParser.add_argument(shortArg,
                                 longArg,
                                 metavar=metavar,
                                 type=float,
                                 nargs=2,
                                 help=helpText)


def _configLightBoxParser(lbParser):
    """Adds options to the given parser allowing the user to
    configure :class:`.LightBoxOpts` properties.
    """    
    _configParser(fsldisplay.LightBoxOpts, lbParser)


def _configOverlayParser(ovlParser):
    """Adds options to the given parser allowing the user to
    configure the display of a single overlay.
    """

    Display        = fsldisplay.Display
    ImageOpts      = fsldisplay.ImageOpts
    VolumeOpts     = fsldisplay.VolumeOpts
    VectorOpts     = fsldisplay.VectorOpts
    RGBVectorOpts  = fsldisplay.RGBVectorOpts
    LineVectorOpts = fsldisplay.LineVectorOpts
    MaskOpts       = fsldisplay.MaskOpts
    ModelOpts      = fsldisplay.ModelOpts
    LabelOpts      = fsldisplay.LabelOpts
    
    dispParser  = ovlParser.add_argument_group(GROUPNAMES[    Display],
                                               GROUPDESCS.get(Display))
    imgParser   = ovlParser.add_argument_group(GROUPNAMES[ImageOpts])
    volParser   = ovlParser.add_argument_group(GROUPNAMES[VolumeOpts])
    vecParser   = ovlParser.add_argument_group(GROUPNAMES[VectorOpts])
    lvParser    = ovlParser.add_argument_group(GROUPNAMES[LineVectorOpts])
    rvParser    = ovlParser.add_argument_group(GROUPNAMES[RGBVectorOpts])
    maskParser  = ovlParser.add_argument_group(GROUPNAMES[MaskOpts])
    modelParser = ovlParser.add_argument_group(GROUPNAMES[ModelOpts])
    labelParser = ovlParser.add_argument_group(GROUPNAMES[LabelOpts])

    targets = [(Display,        dispParser),
               (ImageOpts,      imgParser),
               (VolumeOpts,     volParser),
               (VectorOpts,     vecParser),
               (LineVectorOpts, lvParser),
               (RGBVectorOpts,  rvParser),
               (MaskOpts,       maskParser),
               (ModelOpts,      modelParser),
               (LabelOpts,      labelParser)]

    for target, parser in targets:

        propNames      = list(OPTIONS[target])
        specialOptions = []
        
        # The VectorOpts.modulate
        # option needs special treatment
        if target == VectorOpts and 'modulate' in propNames:
            specialOptions.append('modulate')
            propNames.remove('modulate')

        # The same goes for the
        # ModelOpts.refImage option
        if target == ModelOpts and 'refImage' in propNames:
            specialOptions.append('refImage')
            propNames.remove('refImage') 

        _configParser(target, parser, propNames)

        # We need to process the special options
        # manually, rather than using the props.cli
        # module - see the handleOverlayArgs function.
        for opt in specialOptions:
            shortArg, longArg = ARGUMENTS[target, opt]
            helpText          = HELP[     target, opt]

            shortArg =  '-{}'.format(shortArg)
            longArg  = '--{}'.format(longArg)
            parser.add_argument(
                shortArg,
                longArg,
                metavar='FILE',
                help=helpText)

            
def parseArgs(mainParser, argv, name, desc, toolOptsDesc='[options]'):
    """Parses the given command line arguments, returning an
    :class:`argparse.Namespace` object containing all the arguments.

    The display options for individual overlays are parsed separately. The
    :class:`~argparse.Namespace` objects for each overlay are returned in a
    list, stored as an attribute, called ``overlays``, of the returned
    top-level ``Namespace`` instance. Each of the overlay ``Namespace``
    instances also has an attribute, called ``overlay``, which contains the
    full path of the overlay file that was speciied.

      - mainParser:   A :class:`argparse.ArgumentParser` which should be
                      used as the top level parser.
    
      - argv:         The arguments as passed in on the command line.
    
      - name:         The name of the tool - this function might be called by
                      either the :mod:`~fsl.tools.fsleyes` tool or the
                      :mod:`~fsl.tools.render` tool.
    
      - desc:         A description of the tool.
    
      - toolOptsDesc: A string describing the tool-specific options (those
                      options which are handled by the tool, not by this
                      module).
    """

    log.debug('Parsing arguments for {}: {}'.format(name, argv))

    # I hate argparse. By default, it does not support
    # the command line interface that I want to provide,
    # as demonstrated in this usage string. 
    usageStr   = '{} {} [overlayfile [displayOpts]] '\
                 '[overlayfile [displayOpts]] ...'.format(
                     name,
                     toolOptsDesc)

    # So I'm using two argument parsers - the
    # mainParser parses application options
    mainParser.usage       = usageStr
    mainParser.prog        = name
    mainParser.description = desc

    _setupParsers(mainParser)

    # And the ovlParser parses overlay display options
    # for a single overlay - below we're going to
    # manually step through the list of arguments,
    # and pass each block of arguments to the ovlParser
    # one at a time
    ovlParser = argparse.ArgumentParser(add_help=False)

    # Because I'm splitting the argument parsing across two
    # parsers, I'm using a custom print_help function 
    def printHelp(shortHelp=False):

        # Print help for the main parser first,
        # and then separately for the overlay parser
        if shortHelp: mainParser.print_usage()
        else:         mainParser.print_help()

        # Did I mention that I hate argparse?  Why
        # can't we customise the help text? 
        dispGroup = GROUPNAMES[fsldisplay.Display]
        if shortHelp:
            ovlHelp    = ovlParser.format_usage()
            ovlHelp    = ovlHelp.split('\n')

            # Argparse usage text starts with 'usage [toolname]:',
            # and then proceeds to give short help for all the
            # possible arguments. Here, we're removing this
            # 'usage [toolname]:' section, and replacing it with
            # spaces. We're also adding the overlay display argument
            # group title to the beginning of the usage text
            start      = ' '.join(ovlHelp[0].split()[:2])
            ovlHelp[0] = ovlHelp[0].replace(start, ' ' * len(start))
            
            ovlHelp.insert(0, dispGroup)

            ovlHelp = '\n'.join(ovlHelp)
        else:

            # Here we're skipping over the first section of
            # the overlay parser help text,  everything before
            # where the help text contains the overlay display
            # options (which were identifying by searching
            # through the text for the argument group title)
            ovlHelp = ovlParser.format_help()
            ovlHelp = ovlHelp[ovlHelp.index(dispGroup):]
            
        print 
        print ovlHelp

    # And I want to handle overlay argument errors,
    # rather than having the overlay parser force
    # the program to exit
    def ovlArgError(message):
        raise RuntimeError(message)

    # The argparse internals are completely inconfigurable,
    # and completely undocumented. Here, I'm monkey-patching
    # the overlay parser error handler 
    ovlParser.error = ovlArgError

    _configOverlayParser(ovlParser)

    # Figure out where the overlay files
    # are in the argument list, accounting
    # for any options which accept file
    # names as arguments.
    # 
    # Make a list of all the options which
    # accept filenames, and which we need
    # to account for when we're searching
    # for overlay files, flattening the
    # short/long arguments into a 1D list.
    fileOpts = []

    # The VectorOpts.modulate option allows
    # the user to specify another image file
    # by which the vector image colours are
    # to be modulated. The same goes for the
    # ModelOpts.refImage option
    fileOpts.extend(ARGUMENTS[fsldisplay.VectorOpts, 'modulate'])
    fileOpts.extend(ARGUMENTS[fsldisplay.ModelOpts,  'refImage']) 

    # There is a possibility that the user
    # may specify an overlay name which is the
    # same as the overlay file - so we make
    # sure that such situations don't result
    # in an overlay file match.
    fileOpts.extend(ARGUMENTS[fsldisplay.Display, 'name'])

    # Compile a list of arguments which
    # look like overlay file names
    ovlIdxs = []
    
    for i in range(len(argv)):

        # See if the current argument looks like a data source
        dtype, fname = fsloverlay.guessDataSourceType(argv[i])

        # If the file name refers to a file that
        # does not exist, assume it is an argument
        if not op.exists(fname):
            continue

        # Check that this overlay file was 
        # not a parameter to a file option
        if i > 0 and argv[i - 1].strip('-') in fileOpts:
            continue

        # Unrecognised overlay type -
        # I don't know what to do
        if dtype is None:
            raise RuntimeError('Unrecognised overlay type: {}'.format(fname))

        # Otherwise, it's an overlay
        # file that needs to be loaded
        ovlIdxs.append(i)
        
    ovlIdxs.append(len(argv))

    # Separate the program arguments 
    # from the overlay display arguments
    progArgv = argv[:ovlIdxs[0]]
    ovlArgv  = argv[ ovlIdxs[0]:]

    # Parse the application options with the mainParser
    namespace = mainParser.parse_args(progArgv)

    if namespace.help:
        printHelp()
        sys.exit(0)
 
    # Then parse each block of
    # display options one by one.
    namespace.overlays = []
    for i in range(len(ovlIdxs) - 1):

        ovlArgv = argv[ovlIdxs[i]:ovlIdxs[i + 1]]
        ovlFile = ovlArgv[0]
        ovlArgv = ovlArgv[1:]

        try:
            ovlNamespace         = ovlParser.parse_args(ovlArgv)
            ovlNamespace.overlay = ovlFile
            
        except Exception as e:
            printHelp(shortHelp=True)
            print e.message
            sys.exit(1)

        # We just add a list of argparse.Namespace
        # objects, one for each overlay, to the
        # parent Namespace object.
        namespace.overlays.append(ovlNamespace)

    return namespace


def _applyArgs(args, target, propNames=None):
    """Applies the given command line arguments to the given target object."""

    if propNames is None:
        propNames = concat(OPTIONS.get(target, allhits=True))
        
    longArgs  = {name : ARGUMENTS[target, name][1] for name in propNames}
    xforms    = {}
    
    for name in propNames:
        xform = TRANSFORMS.get((target, name), None)
        if xform is not None:
            xforms[name] = xform

    log.debug('Applying arguments to {}: {}'.format(
        type(target).__name__,
        propNames))

    props.applyArguments(target,
                         args,
                         propNames=propNames,
                         xformFuncs=xforms,
                         longArgs=longArgs)


def _generateArgs(source, propNames=None):
    """Does the opposite of :func:`_applyArgs` - generates command line
    arguments which can be used to configure another ``source`` instance
    in the same way as the provided one.
    """

    if propNames is None:
        propNames = concat(OPTIONS.get(source, allhits=True))
        
    longArgs  = {name : ARGUMENTS[source, name][1] for name in propNames}
    xforms    = {}
    
    for name in propNames:
        xform = TRANSFORMS.get((source, name), None)
        if xform is not None:
            xforms[name] = xform

    return props.generateArguments(source,
                                   xformFuncs=xforms,
                                   cliProps=propNames,
                                   longArgs=longArgs)


def applySceneArgs(args, overlayList, displayCtx, sceneOpts):
    """Configures the scene displayed by the given :class:`.DisplayContext`
    instance according to the arguments that were passed in on the command
    line.

    :arg args:        :class:`argparse.Namespace` object containing the parsed
                      command line arguments.

    :arg overlayList: A :class:`.OverlayList` instance.

    :arg displayCtx:  A :class:`.DisplayContext` instance.

    :arg sceneOpts:   A :class:`.SceneOpts` instance.
    """
    
    # First apply all command line options
    # related to the display context 
    if args.selectedOverlay is not None:
        if args.selectedOverlay < len(overlayList):
            displayCtx.selectedOverlay = args.selectedOverlay
    else:
        if len(overlayList) > 0:
            displayCtx.selectedOverlay = len(overlayList) - 1

    # voxel/world location
    if len(overlayList) > 0:
        if args.worldloc:
            wloc = args.worldloc
        elif args.voxelloc:
            opts = displayCtx.getOpts(overlayList[0])
            vloc = args.voxelloc
            wloc = opts.transformCoords([vloc], 'voxel', 'display')[0]
          
        else:
            wloc = [displayCtx.bounds.xlo + 0.5 * displayCtx.bounds.xlen,
                    displayCtx.bounds.ylo + 0.5 * displayCtx.bounds.ylen,
                    displayCtx.bounds.zlo + 0.5 * displayCtx.bounds.zlen]

        displayCtx.location.xyz = wloc

    _applyArgs(args, sceneOpts)


def generateSceneArgs(overlayList, displayCtx, sceneOpts, exclude=None):
    """Generates command line arguments which describe the current state of
    the provided ``displayCtx`` and ``sceneOpts`` instances.

    :arg overlayList: A :class:`.OverlayList` instance.

    :arg displayCtx:  A :class:`.DisplayContext` instance.

    :arg sceneOpts:   A :class:`.SceneOpts` instance.
    
    :arg exclude:     A list of property names to exclude.
    """

    if exclude is None:
        exclude = []

    args = []

    args += ['--{}'.format(ARGUMENTS['Main.scene'][1])]
    if   isinstance(sceneOpts, fsldisplay.OrthoOpts):    args += ['ortho']
    elif isinstance(sceneOpts, fsldisplay.LightBoxOpts): args += ['lightbox']
    else: raise ValueError('Unrecognised SceneOpts '
                           'type: {}'.format(type(sceneOpts).__name__))

    # main options
    if len(overlayList) > 0:
        args += ['--{}'.format(ARGUMENTS['Main.worldLoc'][1])]
        args += ['{}'.format(c) for c in displayCtx.location.xyz]

    if displayCtx.selectedOverlay is not None:
        args += ['--{}'.format(ARGUMENTS['Main.selectedOverlay'][1])]
        args += ['{}'.format(displayCtx.selectedOverlay)]

    props = OPTIONS.get(sceneOpts, allhits=True)

    props = [p for p in props if p not in exclude]
    args += _generateArgs(sceneOpts, concat(props))

    return args


def generateOverlayArgs(overlay, displayCtx):
    """Generates command line arguments which describe the display
    of the current overlay.

    :arg overlay:    An overlay object.

    :arg displayCtx: A :class:`.DisplayContext` instance.
    """
    display = displayCtx.getDisplay(overlay)
    opts    = display   .getDisplayOpts()
    args    = _generateArgs(display) + _generateArgs(opts)

    return args


def applyOverlayArgs(args, overlayList, displayCtx, **kwargs):
    """Loads and configures any overlays which were specified on the
    command line.

    :arg args:        A :class:`~argparse.Namespace` instance, as returned
                      by the :func:`parseArgs` function.
    
    :arg overlayList: An :class:`.OverlayList` instance, to which the
                      overlays should be added.
    
    :arg displayCtx:  A :class:`.DisplayContext` instance, which manages the
                      scene and overlay display.
    
    :arg kwargs:      Passed through to the :func:`.Overlay.loadOverlays`
                      function.
    """

    import fsl.data.image as fslimage
    import fsl.data.model as fslmodel

    paths = [o.overlay for o in args.overlays]

    if len(paths) > 0:
        overlays = fsloverlay.loadOverlays(paths, **kwargs)
        overlayList.extend(overlays)

    # per-overlay display arguments
    for i, overlay in enumerate(overlayList):

        display = displayCtx.getDisplay(overlay)
        
        _applyArgs(args.overlays[i], display)

        # Retrieve the DisplayOpts instance
        # after applying arguments to the
        # Display instance - if the overlay
        # type is set on the command line, the
        # DisplayOpts instance will be replaced
        opts = display.getDisplayOpts()

        # VectorOpts.modulate is a Choice property,
        # where the valid choices are defined by
        # the current contents of the overlay list.
        # So when the user specifies a modulation
        # image, we need to do an explicit check
        # to see if the specified image is vaid
        # 
        # Here, I'm loading the image, and checking
        # to see if it can be used to modulate the
        # vector image (just with a dimension check).
        # If it can, I add it to the image list - the
        # applyArguments function will apply the
        # value. If the modulate file is not valid,
        # an error is raised.
        if isinstance(opts, fsldisplay.VectorOpts) and \
           args.overlays[i].modulate is not None:

            modImage = _findOrLoad(overlayList,
                                   args.overlays[i].modulate,
                                   fslimage.Image,
                                   overlay)

            if modImage.shape != overlay.shape[ :3]:
                raise RuntimeError(
                    'Image {} cannot be used to modulate {} - '
                    'dimensions don\'t match'.format(modImage, overlay))

            opts.modulate             = modImage
            args.overlays[i].modulate = None

            log.debug('Set {} to be modulated by {}'.format(
                overlay, modImage))

        # A similar process is followed for 
        # the ModelOpts.refImage property
        if isinstance(overlay, fslmodel.Model)        and \
           isinstance(opts,    fsldisplay.ModelOpts)  and \
           args.overlays[i].modelRefImage is not None:

            refImage = _findOrLoad(overlayList,
                                   args.overlays[i].modelRefImage,
                                   fslimage.Image,
                                   overlay)

            opts.refImage                  = refImage
            args.overlays[i].modelRefImage = None
            
            log.debug('Set {} reference image to {}'.format(
                overlay, refImage)) 

        # After handling the special cases
        # above, we can apply the CLI
        # options to the Opts instance
        _applyArgs(args.overlays[i], opts)

        
def _findOrLoad(overlayList, overlayFile, overlayType, relatedTo=None):
    """Searches for the given ``overlayFile`` in the ``overlayList``. If not
    present, it is created using the given ``overlayType`` constructor, and
    inserted into the ``overlayList``. The new overlay is inserted into the
    ``overlayList`` before the ``relatedTo`` overlay if provided, otherwise
    appended to the end of the list.
    """

    overlay = overlayList.find(overlayFile)

    if overlay is None:
        overlay = overlayType(overlayFile)

        if relatedTo is not None:
            overlayList.insert(overlayList.index(relatedTo), overlay)
        else:
            overlayList.append(overlay)

    return overlay
