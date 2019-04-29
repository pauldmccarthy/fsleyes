#!/usr/bin/env python
#
# parseargs.py - Parsing FSLeyes command line arguments.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module encapsulates the logic for parsing command line arguments which
specify a scene to be displayed in *FSLeyes*.  This logic is shared between
the :mod:`fsleyes` and :mod:`.render` tools.  This module make use of the
command line generation features of the :mod:`props` package.  Broadly
speaking, this module can be used to do three things:

 - _Parse_ command line arguments, generating an ``argparse.Namespace``
   object which contains the parsed options.

 - _Apply_ the options contained in an ``argparse.Namespace`` option to
   the objects which describe a scene - a :class:`.SceneOpts` instance,
   a :class:`.DisplayContext` instance, and the :class:`.Display` and
   :class:`.DisplayOpts` instances for each overlay.

 - _Generate_ command line arguments that can be used to describe an
   existing scene.


There are a lot of command line arguments made available to the user,
broadly split into the following groups:

 - *Main* arguments control the overall scene display, such as the
   display type (e.g. orthographic or lightbox), the displayed location,
   and whether to show a colour bar. These arguemnts generally correspond
   to properties of the :class:`.SceneOpts`, :class:`.OrthoOpts`,
   :class:`.LightBoxOpts` and :class:`.DisplayContext` classes.


 - *Display* arguments control the display for a single overlay file (e.g.
   a NIFTI image), such as interpolation, colour map, etc. These arguments
   correspond to properties of the :class:`.Display` class, and sub-classes
   of :class:`.DisplayOpts`.


This module provides the following functions:

.. autosummary::
   :nosignatures:

   parseArgs
   applyMainArgs
   applySceneArgs
   applyOverlayArgs
   generateSceneArgs
   generateOverlayArgs


-----
Usage
-----


Call the :func:`parseArgs` function to parse all command line arguments.  Then
create a :class:`.DisplayContext` and :class:`.OverlayList`, and pass them,
along with the ``argparse.Namespace`` object, to the :func:`applyMainArgs`,
:func:`applySceneArgs` and :func:`applyOverlayArgs`
functions. :func:`applyMainArgs` should be called first, but the order of the
latter two does not matter.


--------------------------
``argparse`` modifications
--------------------------


The ``argparse`` module is quite frustrating to work with for the command
line interface that I want to provide. Therefore, this module modifies
the behaviour of ``argparse.ArgumentParser`` instances (by monkey-patching
instances - not the class itself) such that:

 - Prefix matching (a.k.a. abbreviation) is disabled

 - An error is raised when invalid arguments are passed, rather than
   the program exiting.


------------------------------
Command line parsing procedure
------------------------------


*FSLeyes* command line arguments are processed using the following procedure
 (implemented in the :func:`parseArgs` function):


 1. All overlay paths are identified.

 2. *Main* arguments are separated out from the *display* arguments for every
    overlay.

 3. Main arguments are parsed.

 4. The display arguments for each overlay are parsed, using a parser that
    is only configured to identify the overlay type.

 5. The display arguments for each overlay are parsed again, using a parser
    that is configured to handle arguments specific to the overlay type.


-------------------------------
Adding new command line options
-------------------------------


Many classes in *FSLeyes* derive from the :class:`.HasProperties` class of the
:mod:`props` package. Therefore, with only a couple of exceptions, the
processing of nearly all *FSLeyes* command line arguments is completely
automatic.

Therefore, adding a new command line option is fairly easy.  For example,
let's say you have added a new property on the :class:`.MeshOpts` class,
called ``rotation``::

    class MeshOpts(fsldisplay.DisplayOpts):
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
             'MeshOpts'      : ['colour',
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
             'MeshOpts.rotation' : ('mr', 'meshRotation', True),
             # .
             # .
             # .
         })

  3. Add a description in the :data:`HELP` dictionary::

         HELP = td.TypeDict({
             # .
             # .
             # .
             'MeshOpts.rotation' : 'Rotate the mesh by this much',
             # .
             # .
             # .
         })


  4. If the property specifies a file/path name (e.g.
     :attr:`.VolumeOpts.clipImage`), add an entry in the :attr:`FILE_OPTIONS`
     dictionary. In the present example, this is not necessary, but if it were,
     the ``FILE_OPTIONS`` entry might look like this::

         FILE_OPTIONS = td.TypeDict({
             # .
             # .
             # .
             'MeshOpts' : ['refImage', 'rotation'],
             # .
             # .
             # .
         })


-------------------------------------
Adding special (non-property) options
-------------------------------------


If you need to add an option which does not directly map to a
:class:`SceneOpts` or :class:`DisplayOpts` property, or if you need to perform
some custom/extra processing for a property, you need to do some extra
work. For example, let's say we wish to add a custom option ``clipAndDisplay``
to modify both the ``clippingRange`` and ``displayRange`` properties of the
:class:`.VolumeOpts` class.

1. Following steps 1-3 above, we add ``'clipAndDisplay'`` to the
   ``OPTIONS['VolumeOpts']`` list, and add a ``'VolumeOpts.clipAndDisplay'``
   entries to the ``ARGUMENTS`` and ``HELP`` dictionaries.

2. Add a function which configures the argument parser for your option. The
   function must have the following signature::

       def _configSpecial_[target]_[option](
           target,    # The class with which the option is associated
           parser,    # The ArgumentParser to be configured
           shortArg,  # String to use as the short form argument
           longArg,   # String to use as the longform argument
           helpText   # Help text
       )

   where ``target`` is the name of the ``DisplayOpts`` class you are adding
   an option for (e.g. ``'VolumeOpts'``), and ``option`` is the option name.
   In our example, we would add a function::

       def _configSpecial_VolumeOpts_clipAndDisplay(...):

   This function simply needs to add the option to the ``ArgumentParser``
   instance.

3. Add a function which applies parsed command line arguments for your option.
   The function must have the following signature::

       def _applySpecial_[target]_[option](
           args,        # argparse.Namespace object containing parsed arguments
           overlayList, # The OverlayList instance
           displayCtx,  # The DisplayContext instance
           target       # The target instance (e.g. a VolumeOpts instance)
       )

   Apply functions should typically return ``None`` or ``False``, which
   indicates that the argument has been fully processed. However, if you
   have a property for which you need to perform some pre-processing, but
   you also want to be handled by :func:`fsleyes_props.applyArguments`,
   you can have your apply function return ``True``, which indicates that
   the arguemnt should be passed through to ``applyArguments``, in addition
   to being handled by your apply function.

4. Add a function which, given a ``target`` instance, will generate command
   line arguments that can reproduce the ``target`` state. This function must
   have the following signature::

       def _generateSpecial_[target]_[option](
           overlayList, # The OverlayList instance
           displayCtx,  # The DisplayContext instance
           source,      # The source instance
           longArg      # String to use as the long form argument
       )

   In a similar vein to the apply function, described above, a generate
   function may return a value of ``False``, indicating that the argument
   should be passed through to the :func:`fsleyes_props.generateArguments`
   function.
"""


from __future__ import print_function

import os.path          as op
import itertools        as it
import                     sys
import                     types
import                     logging
import                     warnings
import                     textwrap
import                     argparse
import                     collections
import six.moves.urllib as urllib
import numpy            as np

import fsl.data.image                     as fslimage
import fsl.data.utils                     as dutils
import fsl.utils.idle                     as idle
import fsl.utils.transform                as transform
from   fsl.utils.platform import platform as fslplatform

import fsleyes_props                      as props
import fsleyes_widgets.utils.typedict     as td
import fsleyes_widgets.utils.status       as status

from . import displaycontext as fsldisplay
from . import                   colourmaps
from . import                   autodisplay
import                          fsleyes


log = logging.getLogger(__name__)


def _get_option_tuples(self, option_string):
    """By default, the ``argparse`` module uses a *prefix matching* strategy,
    which allows the user to (unambiguously) specify only part of an argument.

    While this may be a good idea for simple programs with a small number of
    arguments, it is very disruptive to the way that I have designed this
    module.

    To disable this prefix matching functionality, this function is
    monkey-patched into all ArgumentParser instances created in this module.


    .. note:: This is unnecessary in python 3.5 and above, due to the addition
              of the ``allow_abbrev`` option.


    See http://stackoverflow.com/questions/33900846/\
    disable-unique-prefix-matches-for-argparse-and-optparse
    """
    result = []

    # option strings starting with two prefix characters are only
    # split at the '='
    chars = self.prefix_chars
    if option_string[0] in chars and option_string[1] in chars:
        if '=' in option_string:
            option_prefix, explicit_arg = option_string.split('=', 1)
        else:
            option_prefix = option_string
            explicit_arg = None
        for option_string in self._option_string_actions:
            if option_string == option_prefix:
                action = self._option_string_actions[option_string]
                tup = action, option_string, explicit_arg
                result.append(tup)

    # single character options can be concatenated with their arguments
    # but multiple character options always have to have their argument
    # separate
    elif option_string[0] in chars and option_string[1] not in chars:
        option_prefix = option_string
        explicit_arg = None
        short_option_prefix = option_string[:2]
        short_explicit_arg = option_string[2:]

        for option_string in self._option_string_actions:
            if option_string == short_option_prefix:
                action = self._option_string_actions[option_string]
                tup = action, option_string, short_explicit_arg
                result.append(tup)
            elif option_string == option_prefix:
                action = self._option_string_actions[option_string]
                tup = action, option_string, explicit_arg
                result.append(tup)

    # shouldn't ever get here
    else:
        self.error(('unexpected option string: %s') % option_string)

    # return the collected option tuples
    return result


class ArgumentError(Exception):
    """Custom ``Exception`` class raised by ``ArgumentParser`` instances
    created and used in this module.
    """
    pass


def ArgumentParser(*args, **kwargs):
    """Wrapper around the ``argparse.ArgumentParser` constructor which
    creates, monkey-patches, and returns an ``ArgumentParser`` instance.
    """

    ap = argparse.ArgumentParser(*args, **kwargs)

    def ovlArgError(message):
        raise ArgumentError(message)

    # 1. I don't want prefix matching.
    #
    # 2. I want to handle argument errors,
    #    rather than having the parser
    #    force the program to exit
    ap._get_option_tuples = types.MethodType(_get_option_tuples, ap)
    ap.error              = ovlArgError

    return ap


class FSLeyesHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """A custom ``argparse.HelpFormatter`` class which customises a few
    annoying things about default ``argparse`` behaviour.
    """
    def _format_usage(self, usage, actions, groups, prefix):

        # Inhibit the 'usage: ' prefix
        return argparse.RawDescriptionHelpFormatter._format_usage(
            self, usage, actions, groups, '')


# Names of all of the property which are
# customisable via command line arguments.
OPTIONS = td.TypeDict({

    'Main'          : ['help',
                       'fullhelp',
                       'verbose',
                       'version',
                       'skipfslcheck',
                       'updatecheck',
                       'noisy',
                       'glversion',
                       'scene',
                       'voxelLoc',
                       'worldLoc',
                       'selectedOverlay',
                       'autoDisplay',
                       'displaySpace',
                       'neuroOrientation',
                       'standard',
                       'standard_brain',
                       'standard1mm',
                       'standard1mm_brain',
                       'initialDisplayRange',
                       'bigmem',
                       'bumMode',
                       'fontSize',
                       'notebook',
                       'notebookPort'],

    # From here on, all of the keys are
    # the names of HasProperties classes,
    # and all of the values are the
    # names of properties on them.

    'SceneOpts'     : ['showCursor',
                       'bgColour',
                       'fgColour',
                       'cursorColour',
                       'showColourBar',
                       'colourBarLocation',
                       'colourBarLabelSide',
                       'colourBarSize',
                       'labelSize',
                       'performance',
                       'movieSyncRefresh',
                       'highDpi'],
    'OrthoOpts'     : ['xzoom',
                       'yzoom',
                       'zzoom',
                       'cursorGap',
                       'showLabels',
                       'layout',
                       'showXCanvas',
                       'showYCanvas',
                       'showZCanvas',
                       'xcentre',
                       'ycentre',
                       'zcentre'],
    'LightBoxOpts'  : ['zax',
                       'sliceSpacing',
                       'zrange',
                       'ncols',
                       'nrows',
                       'showGridLines',
                       'highlightSlice'],
    'Scene3DOpts'   : ['zoom',
                       'showLegend',
                       'occlusion',
                       'light',
                       'lightPos',
                       'offset',
                       'cameraRotation'],

    # The order in which properties are listed
    # here is the order in which they are applied.
    # This is very important - for example,
    # changing the VolumeOpts.useNegativeCmap
    # property will result in its display range
    # being reset. So we need to apply
    # useNegativeCmap first, and then displayRange
    # second.
    'Display'        : ['name',
                        'enabled',
                        'overlayType',
                        'alpha',
                        'brightness',
                        'contrast'],
    'NiftiOpts'      : ['volume'],

    # n.b. I could list the ColourMapOpts
    # properties separately here, and
    # eliminate duplication  across e.g.
    # the VolumeOpts and MeshOpts lists.
    # But I'm a bit wary of the interaction
    # between the CMOpts and the clipImage/
    # overrideDataRange properties, so am
    # listing them separately until I can
    # be bothered to test.
    'VolumeOpts'     : ['linkLowRanges',
                        'linkHighRanges',
                        'overrideDataRange',
                        'clipImage',
                        'useNegativeCmap',
                        'displayRange',
                        'clippingRange',
                        'gamma',
                        'invertClipping',
                        'cmap',
                        'negativeCmap',
                        'cmapResolution',
                        'interpolation',
                        'interpolateCmaps',
                        'invert'],
    'Volume3DOpts'   : ['numSteps',
                        'blendFactor',
                        'smoothing',
                        'resolution',
                        'dithering',
                        'numInnerSteps',
                        'clipMode',
                        'clipPlane'],
    'MaskOpts'       : ['colour',
                        'invert',
                        'threshold',
                        'outline',
                        'outlineWidth',
                        'interpolation'],
    'VectorOpts'     : ['xColour',
                        'yColour',
                        'zColour',
                        'suppressX',
                        'suppressY',
                        'suppressZ',
                        'suppressMode',
                        'cmap',
                        'colourImage',
                        'modulateImage',
                        'modulateRange',
                        'clipImage',
                        'clippingRange'],
    'LineVectorOpts' : ['orientFlip',
                        'lineWidth',
                        'directed',
                        'unitLength',
                        'lengthScale'],
    'RGBVectorOpts'  : ['interpolation'],
    'MeshOpts'       : ['vertexData',
                        'vertexDataIndex',
                        'vertexSet',
                        'colour',
                        'outline',
                        'outlineWidth',
                        'refImage',
                        'coordSpace',
                        'useLut',
                        'lut',
                        'linkLowRanges',
                        'linkHighRanges',
                        'useNegativeCmap',
                        'displayRange',
                        'clippingRange',
                        'gamma',
                        'discardClipped',
                        'invertClipping',
                        'cmap',
                        'negativeCmap',
                        'cmapResolution',
                        'interpolateCmaps',
                        'invert',
                        'wireframe'],
    'GiftiOpts'      : [],
    'FreesurferOpts' : [],
    'TensorOpts'     : ['lighting',
                        'orientFlip',
                        'tensorResolution',
                        'tensorScale'],
    'LabelOpts'      : ['lut',
                        'outline',
                        'outlineWidth'],
    'SHOpts'         : ['orientFlip',
                        'shResolution',
                        'shOrder',
                        'size',
                        'normalise',
                        'lighting',
                        'radiusThreshold',
                        'colourMode'],
    'MIPOpts'        : ['linkLowRanges',
                        'linkHighRanges',
                        'displayRange',
                        'clippingRange',
                        'gamma',
                        'invertClipping',
                        'cmap',
                        'cmapResolution',
                        'interpolation',
                        'interpolateCmaps',
                        'invert',
                        'window',
                        'minimum',
                        'absolute'],
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
    'Scene3DOpts'    : '3D display options',
    'Display'        : 'Display options',
    'VolumeOpts'     : 'Volume options',
    'MaskOpts'       : 'Mask options',
    'LineVectorOpts' : 'Line vector options',
    'RGBVectorOpts'  : 'RGB vector options',
    'MeshOpts'       : 'Mesh options',
    'GiftiOpts'      : 'GIFTI surface options',
    'FreesurferOpts' : 'Freesurfer surface options',
    'LabelOpts'      : 'Label options',
    'TensorOpts'     : 'Tensor options',
    'SHOpts'         : 'SH options',
    'MIPOpts'        : 'MIP options',
})
"""Command line arguments are grouped according to the class to which
they are applied (see the :data:`ARGUMENTS` dictionary). This dictionary
defines descriptions for each command line group.
"""


# Descriptions for each group
GROUPDESCS = td.TypeDict({

    'SceneOpts'    : 'These settings are applied to every '
                     'orthographic, lightbox, and 3D view.',

    'OrthoOpts'    : 'These settings are applied to every '
                     'ortho view.',

    'LightBoxOpts' : 'These settings are applied to every '
                     'lightbox view.',

    'Scene3DOpts'  : 'These settings are applied to every '
                     '3D view.',

    'Display'      : 'Each display option will be applied to the '
                     'overlay which is listed before that option. '
                     'Passing any display option for an overlay will '
                     'override the \'--autoDisplay\' setting for that '
                     'overlay.',

    'VolumeOpts'     : 'These options are applied to \'volume\' overlays.',
    'MaskOpts'       : 'These options are applied to \'mask\' overlays.',
    'LabelOpts'      : 'These options are applied to \'label\' overlays.',
    'LineVectorOpts' : 'These options are applied to \'linevector\' overlays.',
    'RGBVectorOpts'  : 'These options are applied to \'rgbvector\' overlays.',
    'MeshOpts'       : 'These options are applied to \'mesh\' overlays.',
    'TensorOpts'     : 'These options are applied to \'tensor\' overlays.',
    'SHOpts'         : 'These options are applied to \'sh\' overlays.',
    'MIPOpts'        : 'These options are applied to \'mip\' overlays.',
})
"""This dictionary contains descriptions for each argument group. """


GROUPEPILOGS = td.TypeDict({

    'Display'    : 'Available overlay types: {}',
    'LabelOpts'  : 'Available lookup tables: {}. You can also specify a '
                   'lookup table file.',
    'VolumeOpts' : 'Available colour maps: {}. You can also specify any '
                   'matplotlib colour map, or a colour map file. ',
    'SHOpts'     : 'Available colour maps: {}. You can also specify any '
                   'matplotlib colour map, or a colour map file. ',
})
"""This dictionary contains epilogs for some types - information to be shown
after the help for that type. Use the :func:`groupEpilog` function to access
this dictionary.
"""


def groupEpilog(target):
    """Return a formatted value from the :attr:`GROUPEPILOGS` dictionary. The
    ``target`` must be a type.
    """

    epilog = GROUPEPILOGS.get(target)
    if epilog is not None:

        if issubclass(target, fsldisplay.Display):
            epilog = epilog.format(', '.join(
                sorted(fsldisplay.ALL_OVERLAY_TYPES)))

        elif issubclass(target, fsldisplay.LabelOpts):
            epilog = epilog.format(', '.join(
                sorted(colourmaps.scanLookupTables())))

        elif issubclass(target, fsldisplay.VolumeOpts):
            epilog = epilog.format(', '.join(
                sorted(colourmaps.scanColourMaps())))

        elif issubclass(target, fsldisplay.SHOpts):
            epilog = epilog.format(', '.join(
                sorted(colourmaps.scanColourMaps())))

    return epilog


# Short/long arguments for all of those options
ARGUMENTS = td.TypeDict({

    'Main.help'                : ('h',       'help',                False),
    'Main.fullhelp'            : ('fh',      'fullhelp',            False),
    'Main.verbose'             : ('v',       'verbose',             False),
    'Main.version'             : ('V',       'version',             False),
    'Main.skipfslcheck'        : ('S',       'skipfslcheck',        False),
    'Main.updatecheck'         : ('U',       'updatecheck',         False),
    'Main.noisy'               : ('n',       'noisy',               False),
    'Main.glversion'           : ('gl',      'glversion',           True),
    'Main.scene'               : ('s',       'scene',               True),
    'Main.voxelLoc'            : ('vl',      'voxelLoc',            True),
    'Main.worldLoc'            : ('wl',      'worldLoc',            True),
    'Main.selectedOverlay'     : ('o',       'selectedOverlay',     True),
    'Main.autoDisplay'         : ('ad',      'autoDisplay',         False),
    'Main.displaySpace'        : ('ds',      'displaySpace',        True),
    'Main.neuroOrientation'    : ('no',      'neuroOrientation',    False),
    'Main.standard'            : ('std',     'standard',            False),
    'Main.standard_brain'      : ('stdb',    'standard_brain',      False),
    'Main.standard1mm'         : ('std1mm',  'standard1mm',         False),
    'Main.standard1mm_brain'   : ('std1mmb', 'standard1mm_brain',   False),
    'Main.initialDisplayRange' : ('idr',     'initialDisplayRange', True),
    'Main.bigmem'              : ('b',       'bigmem',              False),
    'Main.bumMode'             : ('bums',    'bumMode',             False),
    'Main.fontSize'            : ('fs',      'fontSize',            True),
    'Main.notebook'            : ('nb',      'notebook',            False),
    'Main.notebookPort'        : ('nbp',     'notebookPort',        True),

    'SceneOpts.showColourBar'      : ('cb',  'showColourBar',      False),
    'SceneOpts.bgColour'           : ('bg',  'bgColour',           True),
    'SceneOpts.fgColour'           : ('fg',  'fgColour',           True),
    'SceneOpts.cursorColour'       : ('cc',  'cursorColour',       True),
    'SceneOpts.colourBarLocation'  : ('cbl', 'colourBarLocation',  True),
    'SceneOpts.colourBarLabelSide' : ('cbs', 'colourBarLabelSide', True),
    'SceneOpts.colourBarSize'      : ('cbi', 'colourBarSize',      True),
    'SceneOpts.showCursor'         : ('hc',  'hideCursor',         False),
    'SceneOpts.performance'        : ('p',   'performance',        True),
    'SceneOpts.highDpi'            : ('hd',  'highDpi',            False),
    'SceneOpts.movieSyncRefresh'   : ('ms',  'movieSync',          False),
    'SceneOpts.labelSize'          : ('ls',  'labelSize',          True),

    'OrthoOpts.xzoom'       : ('xz', 'xzoom',      True),
    'OrthoOpts.yzoom'       : ('yz', 'yzoom',      True),
    'OrthoOpts.zzoom'       : ('zz', 'zzoom',      True),
    'OrthoOpts.cursorGap'   : ('cg', 'cursorGap',  False),
    'OrthoOpts.layout'      : ('lo', 'layout',     True),
    'OrthoOpts.showXCanvas' : ('xh', 'hidex',      False),
    'OrthoOpts.showYCanvas' : ('yh', 'hidey',      False),
    'OrthoOpts.showZCanvas' : ('zh', 'hidez',      False),
    'OrthoOpts.showLabels'  : ('hl', 'hideLabels', False),


    'OrthoOpts.xcentre'     : ('xc', 'xcentre', True),
    'OrthoOpts.ycentre'     : ('yc', 'ycentre', True),
    'OrthoOpts.zcentre'     : ('zc', 'zcentre', True),

    'LightBoxOpts.sliceSpacing'   : ('ss', 'sliceSpacing',   True),
    'LightBoxOpts.ncols'          : ('nc', 'ncols',          True),
    'LightBoxOpts.nrows'          : ('nr', 'nrows',          True),
    'LightBoxOpts.zrange'         : ('zr', 'zrange',         True),
    'LightBoxOpts.showGridLines'  : ('sg', 'showGridLines',  False),
    'LightBoxOpts.highlightSlice' : ('hs', 'highlightSlice', False),
    'LightBoxOpts.zax'            : ('zx', 'zaxis',          True),

    'Scene3DOpts.zoom'           : ('z',   'zoom',           True),
    'Scene3DOpts.showLegend'     : ('he',  'hideLegend',     False),
    'Scene3DOpts.occlusion'      : ('noc', 'noOcclusion',    False),
    'Scene3DOpts.light'          : ('dl',  'disableLight',   False),
    'Scene3DOpts.lightPos'       : ('lp',  'lightPos',       True),
    'Scene3DOpts.offset'         : ('off', 'offset',         True),
    'Scene3DOpts.cameraRotation' : ('rot', 'cameraRotation', True),

    'Display.name'          : ('n',  'name',        True),
    'Display.enabled'       : ('d',  'disabled',    False),
    'Display.overlayType'   : ('ot', 'overlayType', True),
    'Display.alpha'         : ('a',  'alpha',       True),
    'Display.brightness'    : ('b',  'brightness',  True),
    'Display.contrast'      : ('c',  'contrast',    True),

    'NiftiOpts.volume'       : ('v',  'volume',     True),

    'ColourMapOpts.displayRange'     : ('dr',  'displayRange',     True),
    'ColourMapOpts.clippingRange'    : ('cr',  'clippingRange',    True),
    'ColourMapOpts.invertClipping'   : ('ic',  'invertClipping',   False),
    'ColourMapOpts.cmap'             : ('cm',  'cmap',             True),
    'ColourMapOpts.negativeCmap'     : ('nc',  'negativeCmap',     True),
    'ColourMapOpts.useNegativeCmap'  : ('un',  'useNegativeCmap',  False),
    'ColourMapOpts.cmapResolution'   : ('cmr', 'cmapResolution',   True),
    'ColourMapOpts.interpolateCmaps' : ('inc', 'interpolateCmaps', False),
    'ColourMapOpts.invert'           : ('i',   'invert',           False),
    'ColourMapOpts.gamma'            : ('g',   'gamma',            True),
    'ColourMapOpts.linkLowRanges'    : ('ll',  'unlinkLowRanges',  True),
    'ColourMapOpts.linkHighRanges'   : ('lh',  'linkHighRanges',   True),

    'VolumeOpts.overrideDataRange' : ('or',  'overrideDataRange', True),
    'VolumeOpts.clipImage'         : ('cl',  'clipImage',         True),
    'VolumeOpts.interpolation'     : ('in',  'interpolation',     True),

    'Volume3DOpts.numSteps'      : ('ns',  'numSteps',      True),
    'Volume3DOpts.blendFactor'   : ('bf',  'blendFactor',   True),
    'Volume3DOpts.smoothing'     : ('s',   'smoothing',     True),
    'Volume3DOpts.resolution'    : ('r',   'resolution',    True),
    'Volume3DOpts.dithering'     : ('dt',  'dithering',     True),
    'Volume3DOpts.numInnerSteps' : ('nis', 'numInnerSteps', True),
    'Volume3DOpts.clipPlane'     : ('cp',  'clipPlane',     True),
    'Volume3DOpts.clipMode'      : ('m',   'clipMode',      True),

    'MaskOpts.colour'        : ('mc', 'maskColour',    False),
    'MaskOpts.invert'        : ('i',  'maskInvert',    False),
    'MaskOpts.threshold'     : ('t',  'threshold',     True),
    'MaskOpts.outline'       : ('o',  'outline',       False),
    'MaskOpts.outlineWidth'  : ('w',  'outlineWidth',  True),
    'MaskOpts.interpolation' : ('in', 'interpolation', True),

    'VectorOpts.xColour'         : ('xc', 'xColour',       True),
    'VectorOpts.yColour'         : ('yc', 'yColour',       True),
    'VectorOpts.zColour'         : ('zc', 'zColour',       True),
    'VectorOpts.suppressX'       : ('xs', 'suppressX',     False),
    'VectorOpts.suppressY'       : ('ys', 'suppressY',     False),
    'VectorOpts.suppressZ'       : ('zs', 'suppressZ',     False),
    'VectorOpts.suppressMode'    : ('sm', 'suppressMode',  True),
    'VectorOpts.cmap'            : ('cm', 'cmap',          True),
    'VectorOpts.colourImage'     : ('co', 'colourImage',   True),
    'VectorOpts.modulateImage'   : ('mo', 'modulateImage', True),
    'VectorOpts.modulateRange'   : ('mr', 'modulateRange', True),
    'VectorOpts.clipImage'       : ('cl', 'clipImage',     True),
    'VectorOpts.clippingRange'   : ('cr', 'clippingRange', True),
    'VectorOpts.orientFlip'      : ('of', 'orientFlip',    False),

    'LineVectorOpts.lineWidth'    : ('lw', 'lineWidth',   True),
    'LineVectorOpts.directed'     : ('ld', 'directed',    False),
    'LineVectorOpts.unitLength'   : ('nu', 'notunit',     False),
    'LineVectorOpts.lengthScale'  : ('ls', 'lengthScale', True),

    'RGBVectorOpts.interpolation' : ('in', 'interpolation', True),

    'TensorOpts.lighting'         : ('dl', 'disableLighting',  False),
    'TensorOpts.tensorResolution' : ('tr', 'tensorResolution', True),
    'TensorOpts.tensorScale'      : ('s',  'scale',            True),

    'MeshOpts.colour'          : ('mc',  'colour',          True),
    'MeshOpts.outline'         : ('o',   'outline',         False),
    'MeshOpts.outlineWidth'    : ('w',   'outlineWidth',    True),
    'MeshOpts.refImage'        : ('r',   'refImage',        True),
    'MeshOpts.coordSpace'      : ('s',   'coordSpace',      True),
    'MeshOpts.vertexData'      : ('vd',  'vertexData',      True),
    'MeshOpts.vertexDataIndex' : ('vdi', 'vertexDataIndex', True),
    'MeshOpts.vertexSet'       : ('vs',  'vertexSet',       True),
    'MeshOpts.useLut'          : ('ul',  'useLut',          False),
    'MeshOpts.lut'             : ('l',   'lut',             True),
    'MeshOpts.discardClipped'  : ('dc',  'discardClipped',  False),
    'MeshOpts.wireframe'       : ('wf',  'wireframe',       False),

    'LabelOpts.lut'          : ('l',  'lut',          True),
    'LabelOpts.outline'      : ('o',  'outline',      False),
    'LabelOpts.outlineWidth' : ('w',  'outlineWidth', True),

    'SHOpts.shResolution'    : ('sr', 'shResolution',    True),
    'SHOpts.shOrder'         : ('so', 'shOrder',         True),
    'SHOpts.size'            : ('s',  'size',            True),
    'SHOpts.lighting'        : ('l',  'lighting',        False),
    'SHOpts.normalise'       : ('no', 'normalise',       False),
    'SHOpts.orientFlip'      : ('of', 'orientFlip',      False),
    'SHOpts.radiusThreshold' : ('t',  'radiusThreshold', True),
    'SHOpts.colourMode'      : ('m',  'colourMode',      True),
    'SHOpts.colourMap'       : ('cm', 'colourMap',       True),
    'SHOpts.xColour'         : ('xc', 'xColour',         True),
    'SHOpts.yColour'         : ('yc', 'yColour',         True),
    'SHOpts.zColour'         : ('zc', 'zColour',         True),

    'MIPOpts.window'         : ('w',  'window',        False),
    'MIPOpts.minimum'        : ('m',  'minimum',       False),
    'MIPOpts.absolute'       : ('ab', 'absolute',      False),
    'MIPOpts.interpolation'  : ('in', 'interpolation', False),
})
"""This dictionary defines the short and long command line flags to be used
for every option. Each value has the form::

    (shortForm, longForm, expectsArguments)

where ``expectsArguments`` is ``True`` if the flag is to be followed by one
or more arguments, ``False`` otherwise.


.. note:: 1. There cannot be any collisions between the main options, the
             :class:`.SceneOpts` options, the :class:`.OrthOpts` options,
             the :class:`.LightBoxOpts` options, and the :class:`.Scene3DOpts`
             options.

          2. There cannot be any collisions between the :class:`.Display`
             options and any one set of :class:`.DisplayOpts` options.

          3. There *can* be collisions between these two groups, and
             between the options for different :class:`.DisplayOpts` types.
"""


# Help text for all of the options
HELP = td.TypeDict({

    'Main.help'            : 'Display basic FSLeyes options and exit',
    'Main.fullhelp'        : 'Display all FSLeyes options and exit',
    'Main.verbose'         : 'Verbose output (can be used up to 3 times)',
    'Main.version'         : 'Print the current version and exit',
    'Main.skipfslcheck'    : 'Skip $FSLDIR check/warning',
    'Main.updatecheck'     : 'Check for FSLeyes updates on startup',
    'Main.noisy'           : 'Make the specified module noisy',
    'Main.glversion'       : 'Desired (major, minor) OpenGL version',
    'Main.scene'           : 'Scene to show',

    'Main.voxelLoc'         : 'Location to show (voxel coordinates of '
                              'first overlay)',
    'Main.worldLoc'         : 'Location to show (world coordinates, takes '
                              'precedence over --voxelLoc)',
    'Main.selectedOverlay'  : 'Selected overlay (index, starting from 0)',
    'Main.autoDisplay'      : 'Automatically configure overlay display '
                              'settings (unless any display settings are '
                              'specified)',
    'Main.displaySpace'     : 'Space in which all overlays are displayed - '
                              'can be "world", or a NIFTI image.',
    'Main.neuroOrientation' : 'Display images in neurological orientation '
                              '(default: radiological)',

    'Main.standard' :
    'Add the MNI152 2mm standard image as an underlay (only if $FSLDIR is '
    'set).',
    'Main.standard_brain' :
    'Add the MNI152 brain-extracted 2mm standard image as an underlay (only '
    'if $FSLDIR is set).',
    'Main.standard1mm' :
    'Add the MNI152 1mm standard image as an underlay (only if $FSLDIR is '
    'set).',
    'Main.standard1mm_brain' :
    'Add the MNI152 brain-extracted 1mm standard image as an underlay (only '
    'if $FSLDIR is set).',

    'Main.initialDisplayRange' :
    'Initial display range to use for volume overlays, expressed as '
    '(low, high) percentiles of the image data range (calculated on '
    'all non-zero voxels).',

    'Main.bigmem'           : 'Load all images into memory, '
                              'regardless of size.',
    'Main.bumMode'          : 'Make the coronal icon look like a bum',
    'Main.fontSize'         : 'Application font size',
    'Main.notebook'         : 'Start the Jupyter notebook server',
    'Main.notebookPort'     : 'Jupyter notebook server port',

    'SceneOpts.showCursor'         : 'Do not display the green cursor '
                                     'highlighting the current location',
    'SceneOpts.bgColour'           : 'Canvas background colour (0-1)',
    'SceneOpts.fgColour'           : 'Canvas foreground colour (0-1)',
    'SceneOpts.cursorColour'       : 'Cursor location colour (0-1)',
    'SceneOpts.showColourBar'      : 'Show colour bar',
    'SceneOpts.colourBarLocation'  : 'Colour bar location',
    'SceneOpts.colourBarLabelSide' : 'Colour bar label orientation',
    'SceneOpts.colourBarSize'      : 'Colour bar size (%%)',
    'SceneOpts.performance'        : 'Rendering performance '
                                     '(1=fastest, 3=best looking)',
    'SceneOpts.highDpi'            : 'If using a high-DPI (e.g. retina) '
                                     'display, render at the full display '
                                     'resolution',
    'SceneOpts.movieSyncRefresh'   : 'Toggle the canvas refresh strategy in '
                                     'movie mode.',
    'SceneOpts.labelSize'          : 'Orientation/colour bar label font size '
                                     '(4-96, default: 12)',

    'OrthoOpts.xzoom'       : 'X canvas zoom (100-5000, default: 100)',
    'OrthoOpts.yzoom'       : 'Y canvas zoom (100-5000, default: 100)',
    'OrthoOpts.zzoom'       : 'Z canvas zoom (100-5000, default: 100)',
    'OrthoOpts.cursorGap'   : 'Show a gap at the cursor centre',
    'OrthoOpts.layout'      : 'Canvas layout',
    'OrthoOpts.showXCanvas' : 'Hide the X canvas',
    'OrthoOpts.showYCanvas' : 'Hide the Y canvas',
    'OrthoOpts.showZCanvas' : 'Hide the Z canvas',
    'OrthoOpts.showLabels'  : 'Hide orientation labels',


    'OrthoOpts.xcentre'     : 'X canvas centre ([-1, 1])',
    'OrthoOpts.ycentre'     : 'Y canvas centre ([-1, 1])',
    'OrthoOpts.zcentre'     : 'Z canvas centre ([-1, 1])',

    'LightBoxOpts.sliceSpacing'   : 'Slice spacing',
    'LightBoxOpts.ncols'          : 'Number of columns',
    'LightBoxOpts.nrows'          : 'Number of rows',
    'LightBoxOpts.zrange'         : 'Slice range',
    'LightBoxOpts.showGridLines'  : 'Show grid lines',
    'LightBoxOpts.highlightSlice' : 'Highlight current slice',
    'LightBoxOpts.zax'            : 'Z axis',

    'Scene3DOpts.zoom'       : 'Zoom (1-5000, default: 100)',
    'Scene3DOpts.showLegend' : 'Hide the orientation legend',
    'Scene3DOpts.occlusion'  : 'Disable volume occlusion',
    'Scene3DOpts.light'      : 'Disable light source',
    'Scene3DOpts.lightPos'   : 'Light position (XYZ world coordinates)',
    'Scene3DOpts.offset'     : 'Offset from centre ([-1, 1])',
    'Scene3DOpts.cameraRotation' :
    'Rotation (degrees), specified as yaw (rotation about the vertical '
    'axis), pitch (rotation about the horizontal axis) and roll (rotation '
    'about the depth axis).',

    'Display.name'          : 'Overlay name',
    'Display.enabled'       : 'Disable (hide) overlay',
    'Display.overlayType'   : 'Overlay type',
    'Display.alpha'         : 'Opacity (0-100, default: 100)',
    'Display.brightness'    : 'Brightness (0-100, default: 50)',
    'Display.contrast'      : 'Contrast (0-100, default: 50)',

    'NiftiOpts.volume'     : 'Volume (index, starting from 0)',

    'ColourMapOpts.displayRange'      : 'Display range. Setting this will '
                                        'override brightnes/contrast '
                                        'settings. For volume overlays only: '
                                        'append a "%%" to the high value to '
                                        'set range by percentile.',
    'ColourMapOpts.clippingRange'     : 'Clipping range. Setting this will '
                                        'override the low display range '
                                        '(unless low ranges are unlinked).'
                                        'For volume overlays only: append '
                                        'a "%%" to the high value to clip by '
                                        'percentile.',
    'ColourMapOpts.invertClipping'    : 'Invert clipping',
    'ColourMapOpts.cmap'              : 'Colour map',
    'ColourMapOpts.negativeCmap'      : 'Colour map for negative values '
                                        '(only used if the negative '
                                        'colour map is enabled)',
    'ColourMapOpts.cmapResolution'    : 'Colour map resolution',
    'ColourMapOpts.useNegativeCmap'   : 'Use negative colour map',
    'ColourMapOpts.interpolateCmaps'  : 'Interpolate between colours '
                                        'in colour maps',
    'ColourMapOpts.invert'            : 'Invert colour map',
    'ColourMapOpts.gamma'             : 'Gamma correction [-1-+1, default: 0]',
    'ColourMapOpts.linkLowRanges'     : 'Unlink low display/clipping ranges',
    'ColourMapOpts.linkHighRanges'    : 'Link high display/clipping ranges',

    'VolumeOpts.overrideDataRange' : 'Override data range. Setting this '
                                     'effectively causes FSLeyes to ignore '
                                     'the actual image data range, and use '
                                     'this range instead. This is useful for '
                                     'images with a large data range that is '
                                     'driven by outliers.' ,
    'VolumeOpts.clipImage'         : 'Image containing clipping values '
                                     '(defaults to the image itself)' ,
    'VolumeOpts.interpolation'     : 'Interpolation',

    'Volume3DOpts.numSteps' :
    '3D only. Maximum number of samples per pixel',
    'Volume3DOpts.blendFactor' :
    '3D only Sample blending factor [0.001-1, default: 0.2]',
    'Volume3DOpts.smoothing' :
    '3D only. Smoothing radius [0-10, default: 1]',
    'Volume3DOpts.resolution' :
    '3D only. Resolution [1-100, default: 100]',
    'Volume3DOpts.dithering' :
    '3D only. Deprecated, has no effect.',
    'Volume3DOpts.numInnerSteps' :
    '3D/GL14 only. Number of samples to run on GPU',
    'Volume3DOpts.clipPlane' :
    '3D only. Add a clipping plane. Requires three values: position [0-100], '
    'azimuth [-180, 180], inclination [-180, 180]. Can be used up to 10 '
    'times.',
    'Volume3DOpts.clipMode' :
    '3D only. How to apply the clipping plane(s).',

    'MaskOpts.colour'       : 'Colour (0-1)',
    'MaskOpts.invert'        : 'Invert',
    'MaskOpts.threshold'     : 'Threshold',
    'MaskOpts.outline'       : 'Show mask outline',
    'MaskOpts.outlineWidth'  : 'Mask outline width (1-10, default: 2)',
    'MaskOpts.interpolation' : 'Interpolation',

    'VectorOpts.xColour'         : 'X colour (0-1)',
    'VectorOpts.yColour'         : 'Y colour (0-1)',
    'VectorOpts.zColour'         : 'Z colour (0-1)',
    'VectorOpts.suppressX'       : 'Suppress X magnitude',
    'VectorOpts.suppressY'       : 'Suppress Y magnitude',
    'VectorOpts.suppressZ'       : 'Suppress Z magnitude',
    'VectorOpts.suppressMode'    : 'Replace suppressed colours with '
                                   '\'white\' (default), \'black\', or '
                                   '\'transparent\'.',
    'VectorOpts.cmap'            : 'Colour map (only used if a '
                                   'colour image is provided)',
    'VectorOpts.colourImage'     : 'Image to colour vectors with',
    'VectorOpts.modulateImage'   : 'Image to modulate vector brightness with',
    'VectorOpts.modulateRange'   : 'Modulation range (only used if a '
                                   'modulation image is provided)',
    'VectorOpts.clipImage'       : 'Image to clip vectors with',
    'VectorOpts.clippingRange'   : 'Clipping range (only used if a '
                                   'clipping image is provided)',
    'VectorOpts.orientFlip'      : 'Flip L/R orientation within each voxel. '
                                   'Default: true for images with '
                                   'neurological storage order, false for '
                                   'images with radiological storage order. '
                                   'Passing this flag will invert the '
                                   'default behaviour.',

    'LineVectorOpts.lineWidth'    : 'Line width (1-10, default: 1)',
    'LineVectorOpts.directed'     : 'Interpret vectors as directed',
    'LineVectorOpts.unitLength'   : 'Do not scale lines to unit length',
    'LineVectorOpts.lengthScale'  : 'Scale line length by this '
                                    'percentage (10-500, default: 100)',
    'RGBVectorOpts.interpolation' : 'Interpolation',

    'MeshOpts.colour'       : 'Mesh colour (0-1)',
    'MeshOpts.outline'      : 'Show mesh outline',
    'MeshOpts.outlineWidth' : 'Mesh outline width (0-20, default: 2)',
    'MeshOpts.refImage'     : 'Reference image for mesh',
    'MeshOpts.coordSpace'   : 'Mesh vertex coordinate space '
                              '(relative to reference image)',
    'MeshOpts.vertexData' :
    'A file (e.g. Freesurfer .curv file, GIFTI functional, shape, label, '
    'or time series file, or a plain text file) containing one or more values '
    'for each vertex in the mesh.',
    'MeshOpts.vertexDataIndex' :
    'If the vertex data (-vd/--vertexData) file contains more than '
    'one value per vertex, specify the the index of the data to '
    'display.',
    'MeshOpts.vertexSet' :
    'A file containing an additional (compatible) mesh definition.',
    'MeshOpts.useLut' :
    'Use a lookup table instead of colour map(S) when colouring the mesh '
    'with vertex data.',
    'MeshOpts.lut' : 'Lookup table to use  (see -ul/--useLut).',
    'MeshOpts.discardClipped' :
    'Discard clipped regions, rather than colouring them with the flat colour',
    'MeshOpts.wireframe' :
    '3D only. Draw as wireframe',

    'TensorOpts.lighting'         : 'Disable lighting effect',
    'TensorOpts.tensorResolution' : 'Tensor resolution/quality '
                                    '(4-20, default: 10)',
    'TensorOpts.tensorScale'      : 'Tensor size (percentage of '
                                    'voxel size; 50-600, default: 100)',

    'LabelOpts.lut'          : 'Label image LUT',
    'LabelOpts.outline'      : 'Show label outlines',
    'LabelOpts.outlineWidth' : 'Label outline width (proportion of '
                               'one voxel; 0-1, default: 0.25)',

    'SHOpts.shResolution'    : 'FOD resolution/quality '
                               '(3-10, default: 5)',
    'SHOpts.shOrder'         : 'Maximum SH function order (0-maximum '
                               'determined from image [up to 16], '
                               'default: maximum)',
    'SHOpts.size'            : 'FOD size (10-500, default: 100)',
    'SHOpts.normalise'       : 'Normalise FOD sizes',
    'SHOpts.lighting'        : 'Enable dodgy lighting effect',
    'SHOpts.radiusThreshold' : 'Hide FODs with radius less than this '
                               '(min: 0, max: 1, default: 0.05)',
    'SHOpts.colourMode'      : 'Colour by \'direction\' or \'radius\' '
                               '(default: direction)',
    'SHOpts.colourMap'       : 'Colour map, if colouring by \'radius\'',
    'SHOpts.xColour'         : 'X colour, if colouring by \'direction\'',
    'SHOpts.yColour'         : 'Y colour, if colouring by \'direction\'',
    'SHOpts.zColour'         : 'Z colour, if colouring by \'direction\'',

    'MIPOpts.window'         :
    'Length of the window along which the MIP is calculated. Specified as '
    'a proportion of the image length. The window is centred at the '
    'current display location.' ,
    'MIPOpts.minimum'        :
    'Use the minimum intensity, rather than the maximum intensity, in the '
    'projection.',
    'MIPOpts.absolute'       :
    'Use the absolute intensity, rather than the maximum intensity, in the '
    'projection. This overrides the minimum intensity setting.',
})
"""This dictionary defines the help text for all command line options."""


# Help text for some properties, when user requests short (abbreviated) help.
SHORT_HELP = td.TypeDict({
    'ColourMapOpts.displayRange'  : 'Display range',
    'ColourMapOpts.clippingRange' : 'Clipping range. Setting this will '
                                    'override the display range.',
})
"""This dictionary defines the help text for some properties, used when the
user requests a short (abbreviated) version of the command line help.
"""


def getExtra(target, propName, default=None):
    """This function returns defines any extra settings to be passed
    through to the :func:`.props.addParserArguments` function for the
    given type and property.
    """

    # Overlay type options
    overlayTypeSettings = {
        'choices' : fsldisplay.ALL_OVERLAY_TYPES,
        'default' : fsldisplay.ALL_OVERLAY_TYPES[0],
        'metavar' : 'TYPE',
    }


    # Settings for the LabelOpts/MeshOpts.lut property -
    # we don't want to pre-load all LUTs as it takes too
    # long. And luts can be specified by name, or by file,
    # soe we accept any string here, and then parse them
    # witn an applySpecial function.
    lutSettings = {
        'choices'       : None,
        'useAlts'       : False,
        'metavar'       : 'LUT',
        'default'       : 'random',
    }

    # Similar procedure for the colour map properties
    cmapSettings = {
        'choices'  : None,
        'metavar'  : 'CMAP',
        'parseStr' : True
    }

    # shOrder can be up to a maximum of 16,
    # but will be limited by the image itself
    shOrderSettings = {
        'choices' : list(range(17)),
        'metavar' : 'ORDER',
    }

    # Expect RGB, not RGBA, for colour options
    colourSettings = {
        'alpha' : False,
    }

    # MeshOpts.vertexData is a Choice
    # property, but needs to accept
    # any value on the command line,
    # as the vertex data files need to
    # be pre-loaded (by an applySpecial
    # function).
    vertexDataSettings = {
        'metavar' : 'FILE',
        'choices' : None,
        'useAlts' : False,
        'action'  : 'append',
    }

    # Same for MeshOpts.vertexSet
    vertexSetSettings = dict(vertexDataSettings)

    # VolumeOpts.clippingRange and displayRange are
    # manually applied with special apply functions,
    # but if an invalid value is passed in, we want the
    # error to occur during argument parsing. So we define
    # a custom 'type' which validates the value, raises
    # an error if it is bad, but in the end returns the
    # argument unmodified.
    def rangeType(val):

        orig = val

        if val.endswith('%'):
            val = val[:-1]

        float(val)

        return orig

    rangeSettings = {
        'atype' : rangeType
    }

    allSettings = {
        (fsldisplay.Display,        'overlayType')   : overlayTypeSettings,
        (fsldisplay.LabelOpts,      'lut')           : lutSettings,
        (fsldisplay.MeshOpts,       'lut')           : lutSettings,
        (fsldisplay.GiftiOpts,      'lut')           : lutSettings,
        (fsldisplay.FreesurferOpts, 'lut')           : lutSettings,
        (fsldisplay.ColourMapOpts,  'cmap')          : cmapSettings,
        (fsldisplay.ColourMapOpts,  'negativeCmap')  : cmapSettings,
        (fsldisplay.MeshOpts,       'cmap')          : cmapSettings,
        (fsldisplay.GiftiOpts,      'negativeCmap')  : cmapSettings,
        (fsldisplay.GiftiOpts,      'cmap')          : cmapSettings,
        (fsldisplay.FreesurferOpts, 'negativeCmap')  : cmapSettings,
        (fsldisplay.FreesurferOpts, 'cmap')          : cmapSettings,
        (fsldisplay.MeshOpts,       'negativeCmap')  : cmapSettings,
        (fsldisplay.VolumeOpts,     'cmap')          : cmapSettings,
        (fsldisplay.VolumeOpts,     'clippingRange') : rangeSettings,
        (fsldisplay.VolumeOpts,     'displayRange')  : rangeSettings,
        (fsldisplay.VolumeOpts,     'negativeCmap')  : cmapSettings,
        (fsldisplay.LineVectorOpts, 'cmap')          : cmapSettings,
        (fsldisplay.RGBVectorOpts,  'cmap')          : cmapSettings,
        (fsldisplay.TensorOpts,     'cmap')          : cmapSettings,
        (fsldisplay.SHOpts,         'cmap')          : cmapSettings,
        (fsldisplay.SHOpts,         'shOrder')       : shOrderSettings,
        (fsldisplay.SceneOpts,      'bgColour')      : colourSettings,
        (fsldisplay.SceneOpts,      'fgColour')      : colourSettings,
        (fsldisplay.SceneOpts,      'cursorColour')  : colourSettings,
        (fsldisplay.MaskOpts,       'colour')        : colourSettings,
        (fsldisplay.LineVectorOpts, 'xColour')       : colourSettings,
        (fsldisplay.LineVectorOpts, 'yColour')       : colourSettings,
        (fsldisplay.LineVectorOpts, 'zColour')       : colourSettings,
        (fsldisplay.RGBVectorOpts,  'xColour')       : colourSettings,
        (fsldisplay.RGBVectorOpts,  'yColour')       : colourSettings,
        (fsldisplay.RGBVectorOpts,  'zColour')       : colourSettings,
        (fsldisplay.TensorOpts,     'xColour')       : colourSettings,
        (fsldisplay.TensorOpts,     'yColour')       : colourSettings,
        (fsldisplay.TensorOpts,     'zColour')       : colourSettings,
        (fsldisplay.SHOpts,         'xColour')       : colourSettings,
        (fsldisplay.SHOpts,         'yColour')       : colourSettings,
        (fsldisplay.SHOpts,         'zColour')       : colourSettings,
        (fsldisplay.MeshOpts,       'colour')        : colourSettings,
        (fsldisplay.GiftiOpts,      'colour')        : colourSettings,
        (fsldisplay.FreesurferOpts, 'colour')        : colourSettings,
        (fsldisplay.MeshOpts,       'vertexData')    : vertexDataSettings,
        (fsldisplay.GiftiOpts,      'vertexData')    : vertexDataSettings,
        (fsldisplay.FreesurferOpts, 'vertexData')    : vertexDataSettings,
        (fsldisplay.MeshOpts,       'vertexSet')     : vertexSetSettings,
        (fsldisplay.GiftiOpts,      'vertexSet')     : vertexSetSettings,
        (fsldisplay.FreesurferOpts, 'vertexSet')     : vertexSetSettings,
        (fsldisplay.MIPOpts,        'cmap')          : cmapSettings,
        (fsldisplay.MIPOpts,        'negativeCmap')  : cmapSettings,
    }

    # Add (str, propname) versions
    # of all keys so both class and
    # string lookups work
    strSettings = {(type(k[0]).__name__, k[1]) : v
                   for k, v in allSettings.items()}

    allSettings.update(strSettings)

    return allSettings.get((target, propName), None)


# Options which expect a file that
# needs to be loaded as an overlay
# need special treatment.
FILE_OPTIONS = td.TypeDict({
    'Main'       : ['displaySpace'],
    'VolumeOpts' : ['clipImage'],
    'VectorOpts' : ['clipImage',
                    'colourImage',
                    'modulateImage'],
    'MeshOpts'   : ['refImage'],
})
"""This dictionary contains all arguments which accept file or path
names. These arguments need special treatment - for these arguments, the user
may specify a file which refers to an overlay that may or may not have already
been loaded, so we need to figure out what to do.
"""


# Transform functions for properties where the
# value passed in on the command line needs to
# be manipulated before the property value is
# set. These are passed to the props.applyArguments
# and props.generateArguments functions.
#
# Transformations for overlay properties
# (Display/DisplayOpts) are passed the property
# value, and the overlay to which the property
# applies.
#
# Currently, the overlay-specific transform
# functions can tell the transform direction
# (either generating arguments or applying
# arguments) by checking whether the gen
# argument is True - if this is True, we are
# generating arguments.
#
# Transform functions for arguments which are
# associated with an overlay (applied to
# a Display or DisplayOpts instances) are also
# passed the overlay and the target (the
# Display or DisplayOpts instance) as keyword
# arguments.
#
# So a transform function needs a signature
# like so:
#
# def xform(value, gen=None, overlay=None, target=None):
#     ...

# When generating CLI arguments, turn Image
# instances into their file names. And a few
# other special cases.
def _imageTrans(i, **kwargs):

    stri = str(i).lower()

    if   i    is  None:    return None
    elif stri == 'none':   return None

    # Special cases for Main.displaySpace
    elif stri == 'world':  return 'world'
    else:                  return i.dataSource


# The command line interface
# for some boolean properties
# need the property value to be
# inverted.
def _boolTrans(b, **kwargs):
    return not b


# The props.addParserArguments function allows
# us to specify 'extra' parameters (above) to
# specify that we expect RGB, not RGBA colours.
# But the props.generateArguments does not
# accept 'extra' parameters. It accepts
# transform functions though, so we hackily
# truncate any RGBA colours via these transform
# functions.
def _colourTrans(c, **kwargs):
    return c[:3]


TRANSFORMS = td.TypeDict({
    'SceneOpts.showCursor'        : _boolTrans,
    'OrthoOpts.showXCanvas'       : _boolTrans,
    'OrthoOpts.showYCanvas'       : _boolTrans,
    'OrthoOpts.showZCanvas'       : _boolTrans,
    'OrthoOpts.showLabels'        : _boolTrans,
    'Scene3DOpts.showLegend'      : _boolTrans,
    'Scene3DOpts.occlusion'       : _boolTrans,
    'Scene3DOpts.light'           : _boolTrans,
    'Display.enabled'             : _boolTrans,
    'ColourMapOpts.linkLowRanges' : _boolTrans,
    'LineVectorOpts.unitLength'   : _boolTrans,
    'TensorOpts.lighting'         : _boolTrans,

    'SceneOpts.bgColour'         : _colourTrans,
    'SceneOpts.fgColour'         : _colourTrans,
    'SceneOpts.cursorColour'     : _colourTrans,
    'MeshOpts.colour'            : _colourTrans,
    'MaskOpts.colour'            : _colourTrans,
    'VectorOpts.xColour'         : _colourTrans,
    'VectorOpts.yColour'         : _colourTrans,
    'VectorOpts.zColour'         : _colourTrans,
})
"""This dictionary defines any transformations for command line options
where the value passed on the command line cannot be directly converted
into the corresponding property value. See the
:func:`props.applyArguments` and :func:`props.generateArguments`
functions.
"""

# All of the file options need special treatment
for target, fileOpts in FILE_OPTIONS.items():
    for fileOpt in fileOpts:
        key             = '{}.{}'.format(target, fileOpt)
        TRANSFORMS[key] = _imageTrans


EXAMPLES = """\
Examples:

{0} --help
{0} --fullhelp
{0}{1} T1.nii.gz --cmap red
{0}{1} MNI152_T1_2mm.nii.gz -dr 1000 10000
{0}{1} MNI152_T1_2mm.nii.gz -dr 1000 10000 zstats.nii.gz -cm hot -dr -5 5
"""


def _setupMainParser(mainParser):
    """Sets up an argument parser which handles options related
    to the scene. This function configures the following argument
    groups:

      - *Main*:         Top level optoins
      - *SceneOpts*:    Common scene options
      - *OrthoOpts*:    Options related to setting up a orthographic display
      - *LightBoxOpts*: Options related to setting up a lightbox display
      - *Scene3DOpts*:  Options related to setting up a 3D display
    """

    # FSLeyes application options

    # Options defining the overall scene,
    # and separate parser groups for scene
    # settings, ortho, lightbox, and 3D.

    mainParser._optionals.title       = GROUPNAMES[    'Main']
    mainParser._optionals.description = GROUPDESCS.get('Main')

    sceneGroup = mainParser.add_argument_group(GROUPNAMES[    'SceneOpts'],
                                               GROUPDESCS.get('SceneOpts'))
    orthoGroup = mainParser.add_argument_group(GROUPNAMES[    'OrthoOpts'],
                                               GROUPDESCS.get('OrthoOpts'))
    lbGroup    = mainParser.add_argument_group(GROUPNAMES[    'LightBoxOpts'],
                                               GROUPDESCS.get('LightBoxOpts'))
    s3dGroup   = mainParser.add_argument_group(GROUPNAMES[    'Scene3DOpts'],
                                               GROUPDESCS.get('Scene3DOpts'))

    _configMainParser(mainParser)
    _configParser(fsldisplay.SceneOpts,    sceneGroup)
    _configParser(fsldisplay.OrthoOpts,    orthoGroup)
    _configParser(fsldisplay.LightBoxOpts, lbGroup)
    _configParser(fsldisplay.Scene3DOpts,  s3dGroup)


def _configParser(target, parser, propNames=None, shortHelp=False):
    """Configures the given parser so it will parse arguments for the
    given target.
    """

    if propNames is None:
        propNames = list(OPTIONS[target])

    shortArgs = {}
    longArgs  = {}
    helpTexts = {}
    extra     = {}
    special   = []

    for propName in list(propNames):

        shortArg, longArg = ARGUMENTS[ target, propName][:2]
        propExtra         = getExtra(target, propName)
        helpText          = HELP.get((target, propName), 'no help')

        if shortHelp:
            helpText = SHORT_HELP.get((target, propName), helpText)

        shortArgs[propName] = shortArg
        longArgs[ propName] = longArg
        helpTexts[propName] = helpText

        if propExtra is not None:
            extra[propName] = propExtra

        if _isSpecialConfigOption(target, propName) or \
           not hasattr(target, propName):
            propNames.remove(propName)
            special  .append(propName)

    props.addParserArguments(target,
                             parser,
                             cliProps=propNames,
                             shortArgs=shortArgs,
                             longArgs=longArgs,
                             propHelp=helpTexts,
                             extra=extra)

    for s in special:
        _configSpecialOption(
            target, parser, s, shortArgs[s], longArgs[s], helpTexts[s])


def _configMainParser(mainParser):
    """Adds options to the given parser which allow the user to specify
    *main* FSLeyes options.
    """
    mainArgs = {name: ARGUMENTS['Main', name][:2] for name in OPTIONS['Main']}
    mainHelp = {name: HELP[     'Main', name]     for name in OPTIONS['Main']}

    for name, (shortArg, longArg) in list(mainArgs.items()):
        mainArgs[name] = ('-{}'.format(shortArg), '--{}'.format(longArg))

    mainParser.add_argument(*mainArgs['help'],
                            action='store_true',
                            help=mainHelp['help'])
    mainParser.add_argument(*mainArgs['fullhelp'],
                            action='store_true',
                            help=mainHelp['fullhelp'])
    mainParser.add_argument(*mainArgs['version'],
                            action='store_true',
                            help=mainHelp['version'])
    mainParser.add_argument(*mainArgs['skipfslcheck'],
                            action='store_true',
                            help=mainHelp['skipfslcheck'])
    mainParser.add_argument(*mainArgs['updatecheck'],
                            action='store_true',
                            help=mainHelp['updatecheck'])

    # Debug messages are stripped from frozen
    # versions of FSLeyes, so there's no point
    # in keeping these arguments.
    if not fsleyes.disableLogging:
        mainParser.add_argument(*mainArgs['verbose'],
                                action='count',
                                help=mainHelp['verbose'])
        mainParser.add_argument(*mainArgs['noisy'],
                                metavar='MODULE',
                                action='append',
                                help=mainHelp['noisy'])

    mainParser.add_argument(*mainArgs['glversion'],
                            metavar=('MAJOR', 'MINOR'),
                            type=int,
                            nargs=2,
                            help=mainHelp['glversion'])
    mainParser.add_argument(*mainArgs['scene'],
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
                            metavar='INDEX',
                            type=int,
                            help=mainHelp['selectedOverlay'])
    mainParser.add_argument(*mainArgs['autoDisplay'],
                            action='store_true',
                            help=mainHelp['autoDisplay'])
    mainParser.add_argument(*mainArgs['displaySpace'],
                            type=str,
                            help=mainHelp['displaySpace'])
    mainParser.add_argument(*mainArgs['neuroOrientation'],
                            action='store_true',
                            help=mainHelp['neuroOrientation'])

    mainParser.add_argument(*mainArgs['standard'],
                            action='store_true',
                            help=mainHelp['standard'])
    mainParser.add_argument(*mainArgs['standard_brain'],
                            action='store_true',
                            help=mainHelp['standard_brain'])
    mainParser.add_argument(*mainArgs['standard1mm'],
                            action='store_true',
                            help=mainHelp['standard1mm'])
    mainParser.add_argument(*mainArgs['standard1mm_brain'],
                            action='store_true',
                            help=mainHelp['standard1mm_brain'])

    mainParser.add_argument(*mainArgs['initialDisplayRange'],
                            metavar=('LO', 'HI'),
                            type=int,
                            nargs=2,
                            help=mainHelp['initialDisplayRange'])

    mainParser.add_argument(*mainArgs['bigmem'],
                            action='store_true',
                            help=mainHelp['bigmem'])
    mainParser.add_argument(*mainArgs['bumMode'],
                            action='store_true',
                            help=mainHelp['bumMode'])
    mainParser.add_argument(*mainArgs['fontSize'],
                            type=int,
                            help=mainHelp['fontSize'])
    mainParser.add_argument(*mainArgs['notebook'],
                            action='store_true',
                            help=mainHelp['notebook'])
    mainParser.add_argument(*mainArgs['notebookPort'],
                            type=int,
                            help=mainHelp['notebookPort'],
                            default=8888)


def _setupOverlayParsers(forHelp=False, shortHelp=False):
    """Creates a set of parsers which handle command line options for
    :class:`.Display` instances, and for all :class:`.DisplayOpts` instances.

    :arg forHelp:   If ``False`` (the default), each of the parsers created to
                    handle options for the :class:`.DisplayOpts` sub-classes
                    will be configured so that the can also handle options for
                    :class:`.Display` properties. Otherwise, the
                    ``DisplayOpts`` parsers will be configured to only handle
                    ``DisplayOpts`` properties. This option is available to
                    make it easier to separate the help sections when printing
                    help.

    :arg shortHelp: If ``False`` (the default), help text will be taken from
                    the :data:`HELP` dictionary. Otherwise, help text will
                    be taken from the :data:`SHORT_HELP` dictionary.

    :returns: A tuple containing:

                - An ``ArgumentParser`` which parses arguments specifying
                  the :class:`.Display` properties. This parser is not
                  actually used to parse arguments - it is only used to
                  generate help text.

                - An ``ArgumentParser`` which just parses arguments specifying
                  the :attr:`.Display.overlayType` property.

                - An ``ArgumentParser`` which parses arguments specifying
                  :class:`.Display` and :class:`.DisplayOpts` properties.
    """

    Display        = fsldisplay.Display
    VolumeOpts     = fsldisplay.VolumeOpts
    RGBVectorOpts  = fsldisplay.RGBVectorOpts
    LineVectorOpts = fsldisplay.LineVectorOpts
    TensorOpts     = fsldisplay.TensorOpts
    MaskOpts       = fsldisplay.MaskOpts
    MeshOpts       = fsldisplay.MeshOpts
    GiftiOpts      = fsldisplay.GiftiOpts
    FreesurferOpts = fsldisplay.FreesurferOpts
    LabelOpts      = fsldisplay.LabelOpts
    SHOpts         = fsldisplay.SHOpts
    MIPOpts        = fsldisplay.MIPOpts

    # A parser is created and returned
    # for each one of these types.
    parserTypes = [VolumeOpts, MaskOpts, LabelOpts,
                   MeshOpts, GiftiOpts, FreesurferOpts,
                   LineVectorOpts, RGBVectorOpts,
                   TensorOpts, SHOpts, MIPOpts]

    # Dictionary containing the Display parser,
    # and parsers for each overlay type. We use
    # an ordered dict to control the order in
    # which help options are printed.
    parsers = collections.OrderedDict()

    # The Display parser is used as a parent
    # for each of the DisplayOpts parsers
    otParser   = ArgumentParser(add_help=False)
    dispParser = ArgumentParser(add_help=False, epilog=groupEpilog(Display))
    dispProps  = list(OPTIONS[Display])

    if not forHelp:
        dispProps.remove('overlayType')

    _configParser(Display, dispParser, dispProps,       shortHelp=shortHelp)
    _configParser(Display, otParser,   ['overlayType'], shortHelp=shortHelp)

    # Create and configure
    # each of the parsers
    for target in parserTypes:

        if not forHelp: parents = [dispParser]
        else:           parents = []

        parser = ArgumentParser(prog='',
                                add_help=False,
                                parents=parents,
                                epilog=groupEpilog(target))

        parsers[target] = parser
        propNames       = list(it.chain(*OPTIONS.get(target, allhits=True)))
        specialOptions  = []

        # These classes are sub-classes of NiftiOpts, and as
        # such they have a volume property. But that property
        # is only used for data access (location panel,
        # histogram, time series etc). So we don't actually
        # want to expose it to the user.
        if target in (LineVectorOpts, RGBVectorOpts, TensorOpts, SHOpts):
            propNames.remove('volume')

        # The file options need
        # to be configured manually.
        fileOpts = FILE_OPTIONS.get(target, [])
        for propName in fileOpts:
            if propName in propNames:
                specialOptions.append(propName)
                propNames     .remove(propName)

        _configParser(target, parser, propNames, shortHelp=shortHelp)

        # We need to process the special options
        # manually, rather than using the props.cli
        # module - see the handleOverlayArgs function.
        for opt in specialOptions:
            shortArg, longArg = ARGUMENTS[target, opt][:2]
            helpText          = HELP.get((target, opt), 'no help')

            shortArg =  '-{}'.format(shortArg)
            longArg  = '--{}'.format(longArg)
            parser.add_argument(
                shortArg,
                longArg,
                metavar='FILE',
                help=helpText)

    return dispParser, otParser, parsers


def parseArgs(mainParser,
              argv,
              name,
              prolog=None,
              desc=None,
              usageProlog=None,
              argOpts=None,
              shortHelpExtra=None):
    """Parses the given command line arguments, returning an
    :class:`argparse.Namespace` object containing all the arguments.

    The display options for individual overlays are parsed separately. The
    :class:`~argparse.Namespace` objects for each overlay are returned in a
    list, stored as an attribute, called ``overlays``, of the returned
    top-level ``Namespace`` instance. Each of the overlay ``Namespace``
    instances also has an attribute, called ``overlay``, which contains the
    full path of the overlay file that was speciied.

    A ``SystemExit`` exception is raised if invalid arguments have been passed
    in or, for example, the user simply requested command line help.

    :arg mainParser:     A :class:`argparse.ArgumentParser` which should be
                         used as the top level parser.

    :arg argv:           The arguments as passed in on the command line.

    :arg name:           The name of the tool - this function might be called
                         by either the :mod:`~fsl.tools.fsleyes` tool or the
                         :mod:`~fsl.tools.render` tool.

    :arg prolog:         A string to print before any usage text is printed.

    :arg desc:           A description of the tool.

    :arg usageProlog:    A string describing the tool-specific options (those
                         options which are handled by the tool, not by this
                         module).

    :arg argOpts:        If the ``mainParser`` has already been configured to
                         parse arguments which accept one or more parameters,
                         you must provide a list of their short and long forms
                         here. Otherwise, the parameters may be incorrectly
                         identified as a path to an overlay.

    :arg shortHelpExtra: If the caller of this function has already added
                         arguments to the ``mainParser``, the long forms of
                         those arguemnts may be passed here as a list to
                         have them included in the short help text.
    """

    if argOpts is None: argOpts = []
    else:               argOpts = list(argOpts)

    log.debug('Parsing arguments for {}: {}'.format(name, argv))

    # I hate argparse. By default, it does not support
    # the command line interface that I want to provide,
    # as demonstrated in this usage string.
    if usageProlog is not None:
        usageProlog = ' [options] {}'.format(usageProlog)
    else:
        usageProlog = ' [options]'

    usageStr = 'Usage: {}{} file [displayOpts] file [displayOpts] ...'.format(
        name,
        usageProlog)

    if prolog is not None:
        usageStr = '{}\n{}'.format(prolog, usageStr)

    # So I'm using multiple argument parsers. First
    # of all, the mainParser parses application
    # options. We'll create additional parsers for
    # handling overlays a bit later on.

    mainParser.usage       = usageStr
    mainParser.epilog      = EXAMPLES.format(name, usageProlog)
    mainParser.prog        = name
    mainParser.description = desc

    _setupMainParser(mainParser)

    # Figure out where the overlay files
    # are in the argument list, accounting
    # for any options which accept file
    # names as arguments.
    #
    # Make a list of all the options which
    # expect an argument - we need to overlook
    # any arguments which look like file names,
    # but are actually values associated with
    # any of these arguments. We separate out
    # the main arguments, and overlay arguments,
    # because there might be overlap between
    # them.
    #
    # TODO This procedure does not support
    #      options which may expect more than
    #      one argument which may look like a
    #      file. You could fix this by
    #      changing the boolean expects flag
    #      in the ARGUMENTS dict to be the
    #      number of expected arguments (and
    #      then skipping over arguments as
    #      needed in the loop below). But
    #      this approach would not be able to
    #      handle options which accept a
    #      variable number of arguments.
    #      This is probably an acceptable
    #      limitation, to be honest.

    mainExpectsArgs = set(argOpts)
    ovlExpectsArgs  = set()
    mainGroups      = ['Main',
                       'SceneOpts',
                       'OrthoOpts',
                       'LightBoxOpts',
                       'Scene3DOpts']
    for key, (shortForm, longForm, expects) in ARGUMENTS.items():

        if key[0] in mainGroups: appendTo = mainExpectsArgs
        else:                    appendTo = ovlExpectsArgs

        if expects:
            appendTo.add( '-{}'.format(shortForm))
            appendTo.add('--{}'.format(longForm))

    log.debug('Identifying overlay paths (ignoring: {})'.format(
        list(mainExpectsArgs) + list(ovlExpectsArgs)))

    # Expand any fsleyes:// arguments
    copy = []
    for i, arg in enumerate(argv):
        if arg.startswith('fsleyes://'): copy.extend(fsleyesUrlToArgs(arg))
        else:                            copy.append(arg)

    argv = copy

    # Compile a list of arguments which
    # look like overlay file names
    ovlIdxs  = []
    ovlTypes = []

    for i in range(len(argv)):

        # If we have not yet identified
        # any overlays, we are still looking
        # through the main arguments.
        # Otherwise we are looking through
        # overlay arguments.
        if len(ovlIdxs) == 0: expectsArgs = mainExpectsArgs
        else:                 expectsArgs = ovlExpectsArgs

        # Check that this overlay file was
        # not a parameter to another argument
        if i > 0 and argv[i - 1] in expectsArgs:
            continue

        # See if the current argument looks like a data source
        dtype, fname = dutils.guessType(argv[i])

        # If the file name refers to a file that
        # does not exist, assume it is an argument
        if not op.exists(fname):
            continue

        # Unrecognised overlay type -
        # I don't know what to do
        if dtype is None:
            raise RuntimeError('Unrecognised overlay type: {}'.format(fname))

        # Otherwise, it's an overlay
        # file that needs to be loaded
        ovlIdxs .append(i)
        ovlTypes.append(dtype)

    # TODO Why is this here?
    ovlIdxs.append(len(argv))

    # Separate the program arguments
    # from the overlay display arguments
    progArgv = argv[:ovlIdxs[0]]
    ovlArgv  = argv[ ovlIdxs[0]:]

    log.debug('Main arguments:    {}'.format(progArgv))
    log.debug('Overlay arguments: {}'.format(ovlArgv))

    # Parse the application options with the mainParser
    try:
        namespace = mainParser.parse_args(progArgv)

    except ArgumentError as e:
        print(str(e))
        print()
        mainParser.print_usage()
        raise SystemExit(1)

    if namespace.help:
        _printShortHelp(mainParser, shortHelpExtra)
        raise SystemExit(0)

    if namespace.fullhelp:
        _printFullHelp(mainParser)
        raise SystemExit(0)

    if namespace.version:
        _printVersion(name)
        raise SystemExit(0)

    # Now, we'll create additiona parsers to handle
    # the Display and DisplayOpts options for each
    # overlay . Below we're going to manually step
    # through the list of arguments for each overlay,
    # and perform a two-pass parse on them.
    #
    # First, we use a parser which is only configured
    # to handle arguments for the Display.overlayType
    # property.
    #
    # Then, now that we know the overlay type, we can
    # then use the appropriate display opts parser to
    # handle the rest of the options.
    dispParser, otParser, optParsers = _setupOverlayParsers()

    # Parse each block of display options one by one,
    # and aggregate the results into a list attached
    # to the main parser namespace object.
    namespace.overlays = []

    for i in range(len(ovlIdxs) - 1):

        ovlArgv = argv[ovlIdxs[i]:ovlIdxs[i + 1]]
        ovlFile = ovlArgv[ 0]
        ovlType = ovlTypes[i]
        ovlArgv = ovlArgv[ 1:]

        # First use the overlay type parser
        # to see if the user has explicitly
        # specified an overlay type
        try:
            otArgs, remaining = otParser.parse_known_args(ovlArgv)

        except ArgumentError as e:
            print(str(e),          file=sys.stderr)
            print(                 file=sys.stderr)
            mainParser.print_usage(file=sys.stderr)
            raise SystemExit(1)

        # Did the user specify an
        # overlay type for this file?
        overlayTypeSet = otArgs.overlayType is not None

        # Check that it is a valid choice.
        # Note: This won't catch all invalid
        # choices, e.g. if 'tensor' is
        # specified for a nifti image that
        # doesn't have 6 volumes.
        if overlayTypeSet:
            if otArgs.overlayType not in fsldisplay.OVERLAY_TYPES[ovlType]:
                raise RuntimeError('Invalid overlay type "{}" '
                                   'for data type "{}"'.format(
                                       otArgs.overlayType, ovlType.__name__))

        # If the user did not specify an overlay type
        # for this overlay, use its default (see the
        # display.OVERLAY_TYPES) dictionary).
        else:
            otArgs.overlayType = fsldisplay.getOverlayTypes(ovlType)[0]

        # Now parse the Display/DisplayOpts
        # with the appropriate parser
        optType   = fsldisplay.DISPLAY_OPTS_MAP[ovlType, otArgs.overlayType]
        optParser = optParsers[optType]

        try: optArgs = optParser.parse_args(remaining)

        except ArgumentError as e:
            print(str(e),          file=sys.stderr)
            print(                 file=sys.stderr)
            mainParser.print_usage(file=sys.stderr)
            print(                 file=sys.stderr)
            print('Options for \'{}\' overlays'.format(otArgs.overlayType),
                  file=sys.stderr)
            optUsage = optParser.format_usage()

            # Remove the 'usage: ' prefix
            # generated by argparse
            optUsage = '      ' + optUsage[6:]

            print(optUsage, file=sys.stderr)
            raise SystemExit(1)

        # Attach the path and the overlay type
        # to the opts namespace object. If an
        # overlay type was not specified, make
        # sure that the namespace object reflects
        # this fact by setting the overlay type
        # to None, so that it does not override
        # the choice made by the Display class
        # when it is created.
        optArgs.overlay = ovlFile
        if overlayTypeSet: optArgs.overlayType = otArgs.overlayType
        else:              optArgs.overlayType = None

        # We just add a list of argparse.Namespace
        # objects, one for each overlay, to
        # the parent Namespace object.
        namespace.overlays.append(optArgs)

    # if logging is disabled, the logging
    # options were not added to the parser.
    # So we fudge the Namespace attributes
    # so none of the FSLeyes code needs to
    # know.
    if fsleyes.disableLogging:
        namespace.verbose = 0
        namespace.noisy   = []

    return namespace


def _printVersion(name):
    """Prints the current FSLeyes version.

    :arg name: Name of the tool (probably either ``fsleyes`` or ``render``).
    """

    from . import version

    print('{}/FSLeyes version {}'.format(name, version.__version__))


def _printShortHelp(mainParser, extra=None):
    """Prints out help for a selection of arguments.

    :arg mainParser: The top level ``ArgumentParser``.

    :arg extra:      List containing long forms of any extra main arguments
                     to be included in the short help text.
    """

    if extra is None:
        extra = []

    # First, we build a list of all arguments
    # that are handled by the main parser.
    # This is done so that we can differentiate
    # between arguments added by this module, and
    # arguments added by users of this module
    # (e.g. the render tool adds a few arguments
    # to the main parser before it is passed to
    # this module for configuration).

    allMain     = OPTIONS['Main']
    allScene    = OPTIONS['SceneOpts']
    allOrtho    = OPTIONS['OrthoOpts']
    allLightBox = OPTIONS['LightBoxOpts']

    allMainArgs =  \
        [ARGUMENTS['Main.{}'        .format(o)][:2] for o in allMain]  + \
        [ARGUMENTS['SceneOpts.{}'   .format(o)][:2] for o in allScene] + \
        [ARGUMENTS['OrthoOpts.{}'   .format(o)][:2] for o in allOrtho] + \
        [ARGUMENTS['LightBoxOpts.{}'.format(o)][:2] for o in allLightBox]
    allMainArgs = ['--{}'.format(a[1]) for a in allMainArgs]

    # Now we build a list of all arguments
    # that we want to show help for, in this
    # shortened help page.
    mainArgs = ['help', 'fullhelp']
    dispArgs = ['alpha']
    volArgs  = ['displayRange', 'clippingRange', 'cmap']

    mainArgs = [ARGUMENTS['Main.{}'         .format(a)][:2] for a in mainArgs]
    dispArgs = [ARGUMENTS['Display.{}'      .format(a)][:2] for a in dispArgs]
    volArgs  = [ARGUMENTS['ColourMapOpts.{}'.format(a)][:2] for a in volArgs]

    mainArgs = ['--{}'.format(a[1]) for a in mainArgs]
    dispArgs = ['--{}'.format(a[1]) for a in dispArgs]
    volArgs  = ['--{}'.format(a[1]) for a in volArgs]

    mainArgs    = mainArgs + extra

    allArgs = td.TypeDict({
        'Main'       : mainArgs,
        'Display'    : dispArgs,
        'VolumeOpts' : volArgs})

    # The public argparse API is quite inflexible
    # with respect to dynamic modification of
    # arguments and help text. Here I'm using
    # undocumented attributes and features to
    # suppress the help text for argument groups
    # and arguments...

    # Suppress all of the main parser argument groups
    for group in mainParser._action_groups:
        group.title       = argparse.SUPPRESS
        group.description = argparse.SUPPRESS

    # Suppress main parser arguments that we
    # don't want to show
    for action in mainParser._actions:

        # We don't want to show any other argument that
        # are not specified in the hard coded mainArgs
        # list above.
        if all([o not in allArgs['Main'] for o in action.option_strings]):
            action.help = argparse.SUPPRESS

    # Generate the help text for main options
    mainParser.description = None
    helpText = mainParser.format_help()

    # Now configure Display/DisplayOpts parsers
    dispParser, _, optParsers = _setupOverlayParsers(forHelp=True,
                                                     shortHelp=True)
    parsers = ([(fsldisplay.Display,    dispParser),
                (fsldisplay.VolumeOpts, optParsers[fsldisplay.VolumeOpts])])

    helpText += '\n' + GROUPNAMES[fsldisplay.Display] + '\n\n'

    for target, parser in parsers:

        parser.description = None
        parser.epilog      = None

        args = allArgs[target]

        # Suppress all arguments that
        # are not listed above
        for action in parser._actions:
            if all([o not in args for o in action.option_strings]):
                action.help = argparse.SUPPRESS

        ovlHelp   = parser.format_help()
        skipTo    = 'optional arguments:'
        optStart  = ovlHelp.index(skipTo)
        optStart += len(skipTo) + 1
        ovlHelp   = ovlHelp[optStart:]

        helpText += ovlHelp

    helpText += '\n' + groupEpilog(fsldisplay.VolumeOpts) + '\n'

    print(helpText)


def _printFullHelp(mainParser):
    """Prints out help for all arguments.

    :arg mainParser: The top level ``ArgumentParser``.
    """

    # The epilog contains EXAMPLES,
    # but we only want them displayed
    # in the short help.
    mainParser.epilog = None

    # Hide silly options
    silly = ['--bumMode']
    for action in mainParser._actions:
        if any([o in silly for o in action.option_strings]):
            action.help = argparse.SUPPRESS

    # Create a bunch of parsers for handling
    # overlay display options
    dispParser, _, optParsers = _setupOverlayParsers(forHelp=True)

    # Print help for the main parser first,
    # and then separately for the overlay parser
    helpText = mainParser.format_help()

    optParsers = ([(fsldisplay.Display, dispParser)] +
                  list(optParsers.items()))

    for target, parser in optParsers:

        groupName = GROUPNAMES.get(target, None)
        groupDesc = GROUPDESCS.get(target, None)

        groupDesc = '\n  '.join(textwrap.wrap(groupDesc, 60))

        nchars    = len(groupName)
        groupName = '#' * nchars + '\n' + \
                    groupName    + '\n' + \
                    '#' * nchars + '\n'

        helpText += '\n' + groupName + '\n'
        if groupDesc is not None:
            helpText += '  ' + groupDesc + '\n'

        ovlHelp = parser.format_help()

        skipTo    = 'optional arguments:'
        optStart  = ovlHelp.index(skipTo)
        optStart += len(skipTo) + 1
        ovlHelp   = ovlHelp[optStart:]

        helpText += '\n' + ovlHelp

    print(helpText)


def _applyArgs(args,
               overlayList,
               displayCtx,
               target,
               propNames=None,
               **kwargs):
    """Applies the given command line arguments to the given target object.
    The target object is added as a keyword argument to pass through to
    any transform functions.
    """

    if propNames is None:
        propNames = list(it.chain(*OPTIONS.get(target, allhits=True)))

    longArgs  = {name : ARGUMENTS[target, name][1] for name in propNames}
    xforms    = {}

    kwargs['target'] = target

    for name in propNames:
        xform = TRANSFORMS.get((target, name), None)
        if xform is not None:
            xforms[name] = xform

    log.debug('Applying arguments to {}: {}'.format(
        type(target).__name__,
        propNames))

    for name in list(propNames):
        applied = False
        if _isSpecialApplyOption(target, name) or not hasattr(target, name):

            applied = not _applySpecialOption(
                args, overlayList, displayCtx, target, name, longArgs[name])

        if not applied:
            props.applyArguments(target,
                                 args,
                                 propNames=[name],
                                 xformFuncs=xforms,
                                 longArgs=longArgs,
                                 **kwargs)


def _generateArgs(overlayList, displayCtx, source, propNames=None):
    """Does the opposite of :func:`_applyArgs` - generates command line
    arguments which can be used to configure another ``source`` instance
    in the same way as the provided one.
    """

    if propNames is None:
        propNames = list(it.chain(*OPTIONS.get(source, allhits=True)))

    # See the hack in the _setupOverlayParsers
    # function - the volume argument is not
    # exposed for these overlay types.
    if isinstance(source, (fsldisplay.LineVectorOpts,
                           fsldisplay.RGBVectorOpts,
                           fsldisplay.TensorOpts,
                           fsldisplay.SHOpts)):
        try:               propNames.remove('volume')
        except ValueError: pass

    longArgs  = {name : ARGUMENTS[source, name][1] for name in propNames}
    xforms    = {}
    args      = []

    for name in list(propNames):
        if _isSpecialGenerateOption(source, name) or \
           not hasattr(source, name):

            nargs = _generateSpecialOption(overlayList,
                                           displayCtx,
                                           source,
                                           name,
                                           longArgs[name])

            if nargs is not False:
                args += nargs
                propNames.remove(name)

    for name in propNames:
        xform = TRANSFORMS.get((source, name), None)
        if xform is not None:
            xforms[name] = xform

    # Arguments passed through
    # to the transform functions
    extraArgs = {'gen' : True}

    if isinstance(source, (fsldisplay.DisplayOpts, fsldisplay.Display)):
        extraArgs['overlay'] = source.overlay
        extraArgs['target']  = source

    args += props.generateArguments(source,
                                    xformFuncs=xforms,
                                    cliProps=propNames,
                                    longArgs=longArgs,
                                    **extraArgs)

    return args


def applyMainArgs(args, overlayList, displayCtx):
    """Applies top-level arguments that are not specific to the scene or
    any overlays. This should be called before either :func:`applySceneArgs`
    or :func:`applyOverlayArgs`.

    :arg args:        :class:`argparse.Namespace` object containing the parsed
                      command line arguments.

    :arg overlayList: A :class:`.OverlayList` instance.

    :arg displayCtx:  A :class:`.DisplayContext` instance.
    """

    from fsleyes.displaycontext.volumeopts import VolumeOpts
    VolumeOpts.setInitialDisplayRange(args.initialDisplayRange)

    if args.bigmem is not None:
        displayCtx.loadInMemory = args.bigmem

    if args.neuroOrientation is not None:
        displayCtx.radioOrientation = not args.neuroOrientation

    displayCtx.autoDisplay = args.autoDisplay


def applySceneArgs(args, overlayList, displayCtx, sceneOpts):
    """Configures the scene displayed by the given :class:`.DisplayContext`
    instance according to the arguments that were passed in on the command
    line.

    .. note:: The scene arguments are applied asynchronously using
              :func:`.idle.idle`. This is done because the
              :func:`.applyOverlayArgs` function also applies its
              arguments asynchrnously, and we want the order of
              application to match the order in which these functions
              were called.

    :arg args:        :class:`argparse.Namespace` object containing the parsed
                      command line arguments.

    :arg overlayList: A :class:`.OverlayList` instance.

    :arg displayCtx:  A :class:`.DisplayContext` instance.

    :arg sceneOpts:   A :class:`.SceneOpts` instance.
    """

    def apply():

        # Load standard underlays next,
        # as they will affect the display
        # space/location stuff below.
        fsldir = fslplatform.fsldir
        if any((args.standard,
                args.standard_brain,
                args.standard1mm,
                args.standard1mm_brain)) and fsldir is None:
            log.warning('$FSLDIR not set: -std/-stdb/-std1mm/-std1mmb '
                        'arguments will be ignored')

        if fslplatform.fsldir is not None:
            stds = []
            if args.standard:          stds.append('MNI152_T1_2mm')
            if args.standard_brain:    stds.append('MNI152_T1_2mm_brain')
            if args.standard1mm:       stds.append('MNI152_T1_1mm')
            if args.standard1mm_brain: stds.append('MNI152_T1_1mm_brain')

            for std in stds:
                std = op.join(fslplatform.fsldir, 'data', 'standard', std)
                std = fslimage.Image(std)
                overlayList.insert(0, std)

        # First apply all command line options
        # related to the display context...

        # Display space may be a string,
        # or a path to an image
        displaySpace = None

        if args.displaySpace == 'world':
            displaySpace = 'world'

        elif args.displaySpace is not None:
            try:
                displaySpace = _findOrLoad(overlayList,
                                           args.displaySpace,
                                           fslimage.Image)
            except Exception:
                log.warning('Unrecognised value for display space: {}'.format(
                    args.displaySpace))

        if displaySpace is not None:
            displayCtx.displaySpace = displaySpace

        # voxel/world location
        if (args.worldLoc or args.voxelLoc) and \
           len(overlayList) > 0             and \
           isinstance(overlayList[0], fslimage.Nifti):

            if args.worldLoc:
                loc = args.worldLoc
            elif args.voxelLoc:
                opts = displayCtx.getOpts(overlayList[0])
                loc  = opts.transformCoords(args.voxelLoc, 'voxel', 'world')

            displayCtx.worldLocation.xyz = loc

        # Now, apply arguments to the SceneOpts instance
        _applyArgs(args, overlayList, displayCtx, sceneOpts)

    idle.idle(apply)


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

    # Scene
    args += ['--{}'.format(ARGUMENTS['Main.scene'][1])]
    if   isinstance(sceneOpts, fsldisplay.OrthoOpts):    args += ['ortho']
    elif isinstance(sceneOpts, fsldisplay.LightBoxOpts): args += ['lightbox']
    elif isinstance(sceneOpts, fsldisplay.Scene3DOpts):  args += ['3d']
    else: raise ValueError('Unrecognised SceneOpts '
                           'type: {}'.format(type(sceneOpts).__name__))

    # World location (if there is one)
    if len(overlayList) > 0:
        worldLoc = displayCtx.worldLocation.xyz
        args    += ['--{}'.format(ARGUMENTS['Main.worldLoc'][1])]
        args    += ['{}'.format(c) for c in worldLoc]

    # display space
    ds = displayCtx.displaySpace
    args += ['--{}'.format(ARGUMENTS['Main.displaySpace'][1])]
    if isinstance(ds, fslimage.Nifti): args += [ds.dataSource]
    else:                              args += [ds]

    # Everything else
    props = OPTIONS.get(sceneOpts, allhits=True)
    props = [p for p in props if p not in exclude]
    args += _generateArgs(overlayList,
                          displayCtx,
                          sceneOpts,
                          list(it.chain(*props)))

    return args


def generateOverlayArgs(overlay, overlayList, displayCtx):
    """Generates command line arguments which describe the display
    of the current overlay.

    :arg overlay:     An overlay object.
    :arg overlayList: The :class:`.OverlayList`
    :arg displayCtx:  A :class:`.DisplayContext` instance.
    """
    display = displayCtx.getDisplay(overlay)
    opts    = display   .opts
    args    = _generateArgs(overlayList, displayCtx, display) + \
              _generateArgs(overlayList, displayCtx, opts)

    return args


def applyOverlayArgs(args,
                     overlayList,
                     displayCtx,
                     loadOverlays=True,
                     **kwargs):
    """Loads and configures any overlays which were specified on the
    command line.

    .. warning:: This function uses the :func:`.loadoverlay.loadOverlays`
                 function which in turn uses :func:`.idle.idle` to load the
                 overlays.  This means that the overlays are loaded and
                 configured asynchronously, meaning that they may not be
                 loaded by the time that this function returns. See the
                 :func:`.loadoverlay.loadOverlays` documentation for more
                 details.

    :arg args:         A :class:`~argparse.Namespace` instance, as returned
                       by the :func:`parseArgs` function.

    :arg overlayList:  An :class:`.OverlayList` instance, to which the
                       overlays should be added.

    :arg displayCtx:   A :class:`.DisplayContext` instance, which manages the
                       scene and overlay display.

    :arg loadOverlays: Defaults to ``True``.  If ``False``, it is assumed that
                       the overlays are already loaded - in this case, the
                       arguments are applied synchronously.

    All other keyword arguments are passed through to the
    :func:`.loadoverlay.loadOverlays` function (unless ``loadOverlays``is
    ``False``).
    """

    import fsleyes.actions.loadoverlay as loadoverlay

    overlayArgs = args.overlays
    paths       = [ns.overlay for ns in overlayArgs]

    if len(paths) == 0:
        return

    # The fsleyes.overlay.loadOverlay function
    # works asynchronously - this function will
    # get called once all of the overlays have
    # been loaded.
    def onLoad(pathIdxs, overlays):

        # Do an initial pass through the overlays and their
        # respective arguments, and build a dictionary of
        # initial overlay types where they have been specified

        overlayTypes = {}

        for idx, overlay in zip(pathIdxs, overlays):
            optArgs     = overlayArgs[idx]
            overlayType = getattr(optArgs, 'overlayType', None)

            if overlayType is not None:
                overlayTypes[overlay] = overlayType

        # Add the overlays to the list. This will
        # trigger the DisplayContext to create
        # Display/DisplayOpts instances for each
        # overlay.
        if loadOverlays:
            overlayList.extend(overlays, overlayTypes=overlayTypes)

        # Select the last image in the list
        selovl = args.selectedOverlay
        if selovl is None or selovl < 0 or selovl >= len(overlayList):
            displayCtx.selectedOverlay = len(overlayList) - 1
        else:
            displayCtx.selectedOverlay = selovl

        for idx, overlay in zip(pathIdxs, overlays):

            status.update('Applying display settings '
                          'to {}...'.format(overlay.name))

            optArgs = overlayArgs[idx]
            display = displayCtx.getDisplay(overlay)

            if hasattr(optArgs, 'overlay'):
                delattr(optArgs, 'overlay')

            # Figure out how many arguments
            # were passed in for this overlay
            allArgs = [v for k, v in vars(optArgs).items()
                       if k != 'overlayType']
            nArgs   = len([a for a in allArgs if a is not None])

            # If no arguments were passed,
            # apply default display settings
            if nArgs == 0 and args.autoDisplay:
                autodisplay.autoDisplay(overlay, overlayList, displayCtx)
                continue

            # Otherwise, we start by applying
            # arguments to the Display instance
            _applyArgs(optArgs, overlayList, displayCtx, display)

            # Retrieve the DisplayOpts instance
            # after applying arguments to the
            # Display instance - if the overlay
            # type is set on the command line, the
            # DisplayOpts instance will have been
            # re-created
            opts = display.opts

            # All options in the FILE_OPTIONS dictionary
            # are Choice properties, where the valid
            # choices are defined by the current
            # contents of the overlay list. So when
            # the user specifies one of these images,
            # we need to do an explicit check to see
            # if the specified image is valid.
            fileOpts = FILE_OPTIONS.get(opts, [])

            for fileOpt in fileOpts:
                value = getattr(optArgs, fileOpt, None)
                if value is None:
                    continue

                setattr(optArgs, fileOpt, None)

                try:
                    image = _findOrLoad(overlayList,
                                        value,
                                        fslimage.Image,
                                        overlay)
                except Exception as e:
                    log.warning('{}: {}'.format(fileOpt, str(e)))
                    continue

                # If the user specified both clipImage
                # arguments and linklow/high range
                # arguments, an error will be raised
                # when we try to set the link properties
                # on the VolumeOpts instance (because
                # they have been disabled). So we
                # clear themfrom the argparse namespace
                # to prevent this from occurring.
                if fileOpt == 'clipImage' and \
                   isinstance(opts, fsldisplay.VolumeOpts):

                    llr = ARGUMENTS['ColourMapOpts.linkLowRanges'][ 1]
                    lhr = ARGUMENTS['ColourMapOpts.linkHighRanges'][1]

                    setattr(optArgs, llr, None)
                    setattr(optArgs, lhr, None)

                setattr(opts, fileOpt, image)

            # After handling the special cases
            # above, we can apply the CLI
            # options to the Opts instance. The
            # overlay and gen flag is passed
            # through to any transform functions
            # (see the TRANSFORMS dict)
            _applyArgs(optArgs,
                       overlayList,
                       displayCtx,
                       opts,
                       gen=False,
                       overlay=overlay)

    if loadOverlays:
        loadoverlay.loadOverlays(paths,
                                 onLoad=onLoad,
                                 inmem=displayCtx.loadInMemory,
                                 **kwargs)
    else:
        onLoad(range(len(overlayList)), overlayList[:])


def wasSpecified(namespace, obj, propName):
    """Returns ``True`` if the given ``propName`` on the given object was
    specified on the command line, ``False`` otherwise.
    """

    optName = ARGUMENTS.get((obj, propName), [None, 'nonexistent'])[1]
    return getattr(namespace, optName, None) is not None


def _findOrLoad(overlayList, overlayFile, overlayType, relatedTo=None):
    """Searches for the given ``overlayFile`` in the ``overlayList``. If not
    present, it is created using the given ``overlayType`` constructor, and
    inserted into the ``overlayList``. The new overlay is inserted into the
    ``overlayList`` before the ``relatedTo`` overlay if provided, otherwise
    appended to the end of the list.
    """

    # Is there an overlay in the list with
    # a name or data source that matches?
    overlay = overlayList.find(overlayFile)

    if overlay is None:

        overlayFile = op.abspath(overlayFile)
        overlay     = overlayType(overlayFile)

        if relatedTo is not None:
            overlayList.insert(overlayList.index(relatedTo), overlay)
        else:
            overlayList.append(overlay)

    return overlay


def fsleyesUrlToArgs(url):
    """Parses a ``fsleyes://`` url and returns a list of equivalent command
    line arguments.
    """

    if not url.startswith('fsleyes://'):
        raise ValueError('Not a fsleyes url: {}'.format(url))

    url = url[10:]
    url = str(urllib.parse.unquote(url))

    return url.split()


def _configSpecialOption(target,
                         parser,
                         optName,
                         shortArg,
                         longArg,
                         helpText):
    """Called by the ``_configParser`` function for any options which do
    not map directly to a :class:`.SceneOpts` or :class:`.DisplayOpts`
    property. Calls the ``_configSpecial`` function for the option.

    :arg target:   The ``Opts`` class with which the option is associated
    :arg parser:   the ``ArgumentParser`` to be configured
    :arg optNmae:  Name of the option
    :arg shortArg: Short form argument for the option
    :arg longArg:  Long form argument for the option
    :arg helpText: Help text
    """

    cfgFunc = _getSpecialFunction(target, optName, '_configSpecial')
    if cfgFunc is None:
        raise ArgumentError(
            'Could not find configuration function for special '
            'argument {}.{}'.format(target.__name__, optName))

    log.debug('Configuring special argument {}.{}'
              .format(target.__name__, optName))

    shortArg = '-{}' .format(shortArg)
    longArg  = '--{}'.format(longArg)

    cfgFunc(target, parser, shortArg, longArg, helpText)


def _applySpecialOption(args,
                        overlayList,
                        displayCtx,
                        target,
                        optName,
                        longArg):
    """Called by the ``_applyArgs`` function for any options which do
    not map directly to a :class:`.SceneOpts` or :class:`.DisplayOpts`
    property. Calls the ``_applySpecial`` function for the option.


    :arg args:        The ``argparse.Namespace`` containing parsed arguments
    :arg overlayList: The ``OverlayList``
    :arg displayCtx:  The ``DisplayContext`` instance
    :arg target:      The ``Opts`` instance with which the option is associated
    :arg optNmae:     Name of the option
    :arg longArg:     Name of the corresponding command line argument
    """

    cls       = type(target)
    applyFunc = _getSpecialFunction(cls, optName, '_applySpecial')

    if applyFunc is None:
        raise ArgumentError(
            'Could not find apply function for special '
            'argument {} to {}'.format(optName, cls.__name__))

    if getattr(args, longArg) is None:
        return

    log.debug('Applying special argument {} to {}'
              .format(optName, cls.__name__))

    return applyFunc(args, overlayList, displayCtx, target)


def _generateSpecialOption(overlayList, displayCtx, source, optName, longArg):
    """Called by the :func:`_generateArgs` function for any options
    which do not map directly to a :class:`.SceneOpts`, :class:`.Display`
    or :class:`.DisplayOpts` instance. Calls the ``_generateSpecial``
    function for the option.

    :arg overlayList: The ``OverlayList``
    :arg displayCtx:  The ``DisplayContext`` instance
    :arg source:      The ``Opts`` instance with which the option is associated
    :arg optNmae:     Name of the option
    :arg longArg:     String to use as the long form argument
    """
    cls     = type(source)
    genFunc = _getSpecialFunction(cls, optName, '_generateSpecial')
    longArg = '--{}'.format(longArg)

    if genFunc is None:
        raise ArgumentError(
            'Could not find generate function for special '
            'argument {} to {}'.format(optName, cls.__name__))

    log.debug('Generate special argument {} to {}'
              .format(optName, cls.__name__))

    return genFunc(overlayList, displayCtx, source, longArg)


def _isSpecialConfigOption(target, optName):
    """
    Returns ``True`` if the given option has a special configuration function,
    ``False`` otherwise.
    """
    return _getSpecialFunction(target, optName, '_configSpecial') is not None


def _isSpecialApplyOption(target, optName):
    """
    Returns ``True`` if the given option has a special apply function,
    ``False`` otherwise.
    """
    return _getSpecialFunction(target, optName, '_applySpecial') is not None


def _isSpecialGenerateOption(target, optName):
    """
    Returns ``True`` if the given option has a special generation function,
    ``False`` otherwise.
    """
    return _getSpecialFunction(target, optName, '_generateSpecial') is not None


def _getSpecialFunction(target, optName, prefix):
    """Searches for a function in this module with the name
    ``_prefix_target_option``, searching the class hierarchy for ``target``.
    """

    if not isinstance(target, type):
        target = type(target)

    thismod = sys.modules[__name__]
    func    = getattr(thismod, '{}_{}_{}'.format(
        prefix, target.__name__, optName), None)

    if func is not None:
        return func

    bases = target.__bases__

    for b in bases:
        func = _getSpecialFunction(b, optName, prefix)
        if func is not None:
            return func

    return None


def _configSpecial_OrthoOpts_xcentre(
        target, parser, shortArg, longArg, helpText):
    """Configures the ``xcentre`` option for the ``OrthoOpts`` class. """
    parser.add_argument(
        shortArg, longArg, metavar=('Y', 'Z'),
        type=float, nargs=2, help=helpText)


def _configSpecial_OrthoOpts_ycentre(
        target, parser, shortArg, longArg, helpText):
    """Configures the ``ycentre`` option for the ``OrthoOpts`` class. """
    parser.add_argument(
        shortArg, longArg, metavar=('X', 'Z'),
        type=float, nargs=2, help=helpText)


def _configSpecial_OrthoOpts_zcentre(
        target, parser, shortArg, longArg, helpText):
    """Configures the ``zcentre`` option for the ``OrthoOpts`` class. """
    parser.add_argument(
        shortArg, longArg, metavar=('X', 'Y'),
        type=float, nargs=2, help=helpText)


def _applySpecial_OrthoOpts_xcentre(args, overlayList, displayCtx, target):
    """Applies the ``OrthoOpts.xcentre`` option. """
    _applySpecialOrthoOptsCentre(
        args.xcentre, displayCtx, 1, 2, target.panel.getGLCanvases()[0])


def _applySpecial_OrthoOpts_ycentre(args, overlayList, displayCtx, target):
    """Applies the ``OrthoOpts.ycentre`` option. """
    _applySpecialOrthoOptsCentre(
        args.ycentre, displayCtx, 0, 2, target.panel.getGLCanvases()[1])


def _applySpecial_OrthoOpts_zcentre(args, overlayList, displayCtx, target):
    """Applies the ``OrthoOpts.zcentre`` option. """
    _applySpecialOrthoOptsCentre(
        args.zcentre, displayCtx, 0, 1, target.panel.getGLCanvases()[2])

def _applySpecialOrthoOptsCentre(centre, displayCtx, xax, yax, canvas):
    """Shared by the ``xcentre``, ``ycentre``, and ``zcentre`` functions.
    """

    xlo  = displayCtx.bounds.getLo(xax)
    ylo  = displayCtx.bounds.getLo(yax)
    xlen = displayCtx.bounds.getLen(xax)
    ylen = displayCtx.bounds.getLen(yax)
    xmid = xlo  + 0.5 * xlen
    ymid = ylo  + 0.5 * ylen
    x    = xmid + 0.5 * xlen * centre[0]
    y    = ymid + 0.5 * ylen * centre[1]

    canvas.centreDisplayAt(x, y)


def _generateSpecial_OrthoOpts_xcentre(
        overlayList, displayCtx, source, longArg):
    """Generates CLI arguments for the ``OrthoOpts.xcentre`` option."""
    canvas = source.panel.getGLCanvases()[0]
    args   = _generateSpecialOrthoOptsCentre(displayCtx, 1, 2, canvas)
    return [longArg] + args


def _generateSpecial_OrthoOpts_ycentre(
        overlayList, displayCtx, source, longArg):
    """Generates CLI arguments for the ``OrthoOpts.ycentre`` option."""
    canvas = source.panel.getGLCanvases()[1]
    args   = _generateSpecialOrthoOptsCentre(displayCtx, 0, 2, canvas)
    return [longArg] + args


def _generateSpecial_OrthoOpts_zcentre(
        overlayList, displayCtx, source, longArg):
    """Generates CLI arguments for the ``OrthoOpts.zcentre`` option."""
    canvas = source.panel.getGLCanvases()[2]
    args   = _generateSpecialOrthoOptsCentre(displayCtx, 0, 1, canvas)
    return [longArg] + args


def _generateSpecialOrthoOptsCentre(displayCtx, xax, yax, canvas):
    """Used by the generation functions for the ``xcentre``, ``ycentre``,
    and ``zcentre`` options.
    """

    x, y = canvas.getDisplayCentre()
    xlo  = displayCtx.bounds.getLo( xax)
    ylo  = displayCtx.bounds.getLo( yax)
    xlen = displayCtx.bounds.getLen(xax)
    ylen = displayCtx.bounds.getLen(yax)
    x    = -1 + 2 * (x - xlo) / xlen
    y    = -1 + 2 * (y - ylo) / ylen

    return ['{: 0.5f}'.format(x), '{: 0.5f}'.format(y)]


def _applySpecial_SceneOpts_movieSyncRefresh(
        args, overlayList, displayCtx, target):
    """Applies the ``SceneOpts.movieSyncRefresh`` option. """

    if args.movieSync:
        target.movieSyncRefresh = not target.defaultMovieSyncRefresh


def _configSpecial_Volume3DOpts_clipPlane(
        target, parser, shortArg, longArg, helpText):
    """Configures the ``clipPlane`` option for the ``VolumeOpts`` class.
    This option allows a clip plane to be defined - the user provides
    the position, azimuth and inclination as a single argument.
    """
    parser.add_argument(shortArg,
                        longArg,
                        type=float,
                        nargs=3,
                        action='append',
                        metavar=('POS', 'AZI', 'INC'),
                        help=helpText)


def _applySpecial_Volume3DOpts_clipPlane(
        args, overlayList, displayCtx, target):
    """Applies the ``Volume3DOpts.clipPlane`` option. """

    ncp = len(args.clipPlane)

    target.numClipPlanes         = ncp
    target.clipPosition[   :ncp] = [cp[0] for cp in args.clipPlane]
    target.clipAzimuth[    :ncp] = [cp[1] for cp in args.clipPlane]
    target.clipInclination[:ncp] = [cp[2] for cp in args.clipPlane]


def _configSpecial_Volume3DOpts_dithering(
        target, parser, shortArg, longArg, helpText):
    """Handle the deprecated ``Volume3DOpts.dithering`` property. """
    parser.add_argument(shortArg,
                        longArg,
                        type=float,
                        help=helpText)


def _applySpecial_Volume3DOpts_dithering(
        args, overlayList, displayCtx, target):
    """Handle the deprecated ``Volume3DOpts.dithering`` property. """
    warnings.warn('dithering is deprecated - it is automatically calculated',
                  DeprecationWarning)


def _generateSpecial_Volume3DOpts_dithering(
        overlayList, displayCtx, source, longArg):
    """Handle the deprecated ``Volume3DOpts.dithering`` property. """
    return []


def _generateSpecial_Volume3DOpts_clipPlane(
        overlayList, displayCtx, source, longArg):
    """Generates arguemnts for the ``Volume3DOpts.clipPlane`` option. """

    args = []

    for i in range(source.numClipPlanes):
        args += [longArg,
                 '{:0.3f}'.format(source.clipPosition[   i]),
                 '{:0.3f}'.format(source.clipAzimuth[    i]),
                 '{:0.3f}'.format(source.clipInclination[i])]

    return args


def _configSpecial_Scene3DOpts_cameraRotation(
        target, parser, shortArg, longArg, helpText):
    """Configures the ``Scene3DOpts.cameraRotation`` option."""
    parser.add_argument(shortArg,
                        longArg,
                        type=float,
                        nargs=3,
                        metavar=('YAW', 'PITCH', 'ROLL'),
                        help=helpText)


def _applySpecial_Scene3DOpts_cameraRotation(
        args, overlayList, displayCtx, target):
    """Applies the ``Scene3DOpts.cameraRotation`` option."""

    yaw, pitch, roll = args.cameraRotation

    yaw   = yaw   * np.pi / 180
    pitch = pitch * np.pi / 180
    roll  = roll  * np.pi / 180

    xform           = transform.axisAnglesToRotMat(pitch, roll, yaw)
    target.rotation = transform.concat(xform, target.rotation)


def _generateSpecial_Scene3DOpts_cameraRotation(
        overlayList, displayCtx, source, longArg):
    """Generates arguments for the ``Scene3DOpts.cameraRotation`` option."""

    rot = source.rotation

    pitch, roll, yaw = transform.rotMatToAxisAngles(rot)

    yaw   = yaw   * 180 / np.pi
    pitch = pitch * 180 / np.pi
    roll  = roll  * 180 / np.pi

    return [longArg,
            '{: 0.2f}'.format(yaw),
            '{: 0.2f}'.format(pitch),
            '{: 0.2f}'.format(roll)]


def _applySpecial_VectorOpts_orientFlip(
        args, overlayList, displayCtx, target):
    """Applies the ``VectorOpts.orientFlip`` option.

    The :attr:`.VectorOpts.orientFlip` property is initialised to ``False``
    for images with a radiological storage order, and ``True`` for images with
    a neurological storage order. So if this argument is specified, we need to
    invert its initial value - apply the flip for radiologically stored
    images, but not for neurologically stored images.
    """
    target.orientFlip = not target.orientFlip


def _generateSpecial_VectorOpts_orientFlip(
        overlayList, displayCtx, source, longArg):
    """Generates the ``VectorOpts.orientFlip`` option. """

    flip = source.overlay.isNeurological() != source.orientFlip

    if flip: return [longArg]
    else:    return []


def _applySpecial_MeshOpts_vertexData(
        args, overlayList, displayCtx, target):
    """Applies the :attr:`.MeshOpts.vertexData` option. """
    import fsleyes.actions.loadvertexdata as loadvertexdata
    # Vertex data files need to be pre-loaded
    vertexData = list(args.vertexData)
    last       = len(args.vertexData) - 1
    for i, vd in enumerate(vertexData):
        vertexData[i] = loadvertexdata.loadVertexData(
            target.overlay, displayCtx, vd, select=(i == last))
    target.vertexData = vertexData[0]


def _applySpecial_MeshOpts_vertexSet(
        args, overlayList, displayCtx, target):
    """Applies the :attr:`.MeshOpts.vertexSet` option. """
    import fsleyes.actions.loadvertexdata as loadvertexdata
    # Vertex set files need to be pre-
    # loaded, similar to vertex data
    last = len(args.vertexSet) - 1
    for i, vd in enumerate(args.vertexSet):
        loadvertexdata.loadVertices(
            target.overlay, displayCtx, vd, select=(i == last))


def _applySpecial_VolumeOpts_overrideDataRange(
        args, overlayList, displayCtx, target):
    """Applies the :attr:`.VolumeOpts.overrideDataRange` option.

    If the ``overrideDataRange`` command line argument has been provided,
    we need to set the :attr:`.VolumeOpts.enableOverrideDataRange` property.
    """
    target.enableOverrideDataRange = True

    # But we can let props handle
    # the overrideDataRange parsing
    return True


def _generateSpecial_VolumeOpts_overrideDataRange(
        overlayList, displayCtx, source, longArg):
    """Generates the :attr:`.VolumeOpts.overrideDataRange` option.

    If the :attr:`.VolumeOpts.enableOverrideDataRange` property is ``False``,
    no arguments are generated.
    """
    if not source.enableOverrideDataRange:
        return []

    # otherwise we let props handle
    # the argument generation
    else:
        return False


def _applySpecial_VolumeOpts_clippingRange(
        args, overlayList, displayCtx, target):
    """Applies the :attr:`.VolumeOpts.clippingRange` option.

    The ``VolumeOpts.clippingRange`` property can be specified on the command
    line normally (as two numbers), or can be specified as a percentile by
    appending a ``'%'`` character to the high range value.
    """
    target.clippingRange = _applyVolumeOptsRange(args.clippingRange, target)


def _applySpecial_VolumeOpts_displayRange(
        args, overlayList, displayCtx, target):
    """Applies the :attr:`.VolumeOpts.displayRange` option.

    The ``VolumeOpts.displayRange`` property can be specified on the command
    line normally (as two numbers), or can be specified as a percentile by
    appending a ``'%'`` character to the high range value.
    """
    target.displayRange = _applyVolumeOptsRange(args.displayRange, target)


def _applyVolumeOptsRange(arange, target):
    """This function is used to parse display/clipping range arguments. """

    arange = list(arange)

    if arange[1][-1] == '%':

        arange[1] = arange[1][:-1]
        arange    = [float(r) for r in arange]
        arange    = np.nanpercentile(target.overlay[:], arange)

    else:
        arange = [float(r) for r in arange]

    return arange


def _applySpecial_ColourMapOpts_cmap(
        args, overlayList, displayCtx, target):
    """Handles the :attr:`.ColourMapOpts.cmap` option. See
    :func:`_applyColourMap`.
    """
    args.cmap = _applyColourMap(args.cmap, overlayList, displayCtx)
    return True


def _applySpecial_ColourMapOpts_negativeCmap(
        args, overlayList, displayCtx, target):
    """Handles the :attr:`.ColourMapOpts.negativeCmap` option. See
    :func:`_applyColourMap`.
    """
    args.negativeCmap = _applyColourMap(
        args.negativeCmap, overlayList, displayCtx)
    return True


def _applySpecial_VectorOpts_cmap(
        args, overlayList, displayCtx, target):
    """Handles the :attr:`.VectorOpts.cmap` option. See
    :func:`_applyColourMap`.
    """
    args.cmap = _applyColourMap(args.cmap, overlayList, displayCtx)
    return True


def _applyColourMap(cmap, overlayList, displayCtx):
    """Handles a colour map argument.  If the specified colour map is a file,
    it is loaded and registered with the :mod:`.colourmaps` module. Returns
    a new value for the colour map argument.
    """
    if op.exists(cmap):
        key = op.splitext(op.basename(cmap))[0]
        colourmaps.registerColourMap(cmap, overlayList, displayCtx, key)
        cmap = key
    return cmap


def _generateSpecial_ColourMapOpts_cmap(
        overlayList, displayCtx, source, longArg):
    """Generates arguments for the :attr:`.ColourMapOpts.cmap` argument. """
    return _generateColourMap(longArg, source.cmap)


def _generateSpecial_ColourMapOpts_negativeCmap(
        overlayList, displayCtx, source, longArg):
    """Generates arguments for the :attr:`.ColourMapOpts.negativeCmap`
    argument.
    """
    return _generateColourMap(longArg, source.negativeCmap)


def _generateSpecial_VectorOpts_cmap(
        overlayList, displayCtx, source, longArg):
    """Generates arguments for the :attr:`.VectorOpts.lut` argument. """
    return _generateColourMap(longArg, source.cmap)


def _generateColourMap(longArg, cmap):
    """Generates a command line argument for the given colour map. This be
    different depending on whether the colour map is installed as a FSLeyes
    colour map, or has been manualy specified from a colour map file.
    """

    cmap = cmap.name

    # if not registered with colourmaps module,
    # then it's a built-in matplotlib colour map
    if not colourmaps.isColourMapRegistered(cmap):
        return [longArg, cmap]

    # if installed, then it's a FSLeyes colour map
    if colourmaps.isColourMapInstalled(cmap):
        return [longArg, cmap]

    # otherwise, it is likely to have been
    # initially specified as a colour map file
    cmap = colourmaps.getColourMapFile(cmap)

    if cmap is not None:
        return [longArg, op.abspath(cmap)]

    # added by some other means (e.g. manually by
    # user in python shell) - don't know what to do
    else:
        return []


def _applySpecial_LabelOpts_lut(args, overlayList, displayCtx, target):
    """Handles the :attr:`.LabelOpts.lut` option. See
    :func:`_applyLookupTable`.
    """
    args.lut = _applyLookupTable(args.lut, overlayList, displayCtx)
    return True


def _applySpecial_MeshOpts_lut(args, overlayList, displayCtx, target):
    """Handles the :attr:`.MeshOpts.lut` option. See
    :func:`_applyLookupTable`.
    """
    args.lut = _applyLookupTable(args.lut, overlayList, displayCtx)
    return True


def _applyLookupTable(lut, overlayList, displayCtx):
    """Handles a lookup table argument.  If the specified lookup table is a
    file, it is loaded and registered with the :mod:`.colourmaps` module.
    Returns a new value for the lookup table argument.
    """
    if op.exists(lut):
        key = op.splitext(op.basename(lut))[0]
        colourmaps.registerLookupTable(lut, overlayList, displayCtx, key)
        lut = key
    return lut


def _generateSpecial_LabelOpts_lut(
        overlayList, displayCtx, source, longArg):
    """Generates arguments for the :attr:`.LabelOpts.lut` argument. """
    return _generateLookupTable(longArg, source.lut)


def _generateSpecial_MeshOpts_lut(
        overlayList, displayCtx, source, longArg):
    """Generates arguments for the :attr:`.MeshOpts.lut` argument. """
    return _generateLookupTable(longArg, source.lut)


def _generateLookupTable(longArg, lut):
    """Generates a command line argument for the given lookup table. This will
    be different depending on whether the lookup table is installed as a
    FSLeyes lookup tablea, or has been manualy specified from a lookup table
    file.
    """

    lut = lut.key

    # the lut has been installed into FSLeyes
    if colourmaps.isLookupTableInstalled(lut):
        return [longArg, lut]

    # otherwise the lut is likely to
    # have been specified as a file
    lut = colourmaps.getLookupTableFile(lut)

    if lut is not None:
        return [longArg, op.abspath(lut)]

    # lut was registered in some other
    # way - don't know what to do
    else:
        return []
