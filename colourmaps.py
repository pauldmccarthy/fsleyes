#!/usr/bin/env python
#
# colourmaps.py - Manage colour maps and lookup tables for overlay rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module manages the colour maps and lookup tables available for overlay
rendering in *FSLeyes*.


The :func:`init` function must be called before any colour maps or lookup
tables can be accessed. When :func:`init` is called, it searches in the
``fsl/fsleyes/colourmaps/`` and ``fsl/fsleyes/luts/`` directories, and
attempts to load all files within which have the suffix ``.cmap`` or ``.lut``
respectively.


-----------
Colour maps
-----------


A ``.cmap`` file defines a colour map which may be used to display a range of
intensity values - see the :attr:`.VolumeOpts.cmap` property for an example. A
``.cmap`` file must contain a list of RGB colours, one per line, with each
colour specified by three space-separated floating point values in the range
``0.0 - 1.0``, for example::


        1.000000 0.260217 0.000000
        0.000000 0.687239 1.000000
        0.738949 0.000000 1.000000


This list of RGB values is used to create a :class:`.ListedColormap` object,
which is then registered with the :mod:`matplotlib.cm` module (using the file
name prefix as the colour map name), and thus made available for rendering
purposes.


If a file named ``order.txt`` exists in the ``fsl/fsleyes/colourmaps/``
directory, it is assumed to contain a list of colour map names, and colour map
identifiers, defining the order in which the colour maps should be displayed
to the user. Any colour maps which are not listed in the ``order.txt`` file
will be appended to the end of the list, and their name will be derived from
the file name.


The following functions are available for managing and accessing colour maps:

.. autosummary::
   :nosignatures:

   getColourMaps
   registerColourMap
   installColourMap
   isColourMapRegistered
   isColourMapInstalled


-------------
Lookup tables
-------------


A ``.lut`` file defines a lookup table which may be used to display images
wherein each voxel has a discrete integer label. Each of the possible voxel
values such an image has an associated colour and name. Each line in a
``.lut`` file must specify the label value, RGB colour, and associated name.
The first column (where columns are space-separated) defines the label value,
the second to fourth columns specify the RGB values, and all remaining columns
give the label name. For example::


        1  0.00000 0.93333 0.00000 Frontal Pole
        2  0.62745 0.32157 0.17647 Insular Cortex
        3  1.00000 0.85490 0.72549 Superior Frontal Gyrus


This list of label, colour, and name mappings is used to create a
:class:`LookupTable` instance, which can be used to access the colours and
names associated with each label value.


Once created, ``LookupTable`` instances may be modified - labels can be
added/removed, and the name/colour of existing labels can be modified.  The
:func:`.installLookupTable` method will install a new lookup table, or save
any changes made to an existing one.


The following functions are available to access and manage
:class:`LookupTable` instances:

.. autosummary::
   :nosignatures:

   getLookupTables
   registerLookupTable
   installLookupTable
   isLookupTableRegistered
   isLookupTableInstalled


-------------
Miscellaneous
-------------


Some utility functions are also kept in this module, related to calculating
the relationship between a data display range and brightness/contrast scales,
and generating/manipulating colours.:

.. autosummary::
   :nosignatures:

   displayRangeToBricon
   briconToDisplayRange
   applyBricon
   randomColour
   randomBrightColour
   randomDarkColour
"""


import logging
import glob
import bisect
import colorsys
import os.path as op

from collections import OrderedDict

import numpy as np

import props


log = logging.getLogger(__name__)


def init():
    """This function must be called before any of the other functions in this
    module can be used.

    It initialises the colour map and lookup table registers, loading all
    colour map and lookup table files that exist.
    """

    global _cmaps
    global _luts

    registers = []

    if _cmaps is None:
        _cmaps = OrderedDict()
        registers.append((_cmaps, _cmapDir, 'cmap'))

    if _luts is None:
        _luts = OrderedDict()
        registers.append((_luts, _lutDir, 'lut'))

    if len(registers) == 0:
        return

    for register, rdir, suffix in registers:

        # Build up a list of key -> name mappings,
        # from the order.txt file, and any other
        # colour map/lookup table  files in the
        # cmap/lut directory
        allmaps   = OrderedDict()
        orderFile = op.join(rdir, 'order.txt')

        if op.exists(orderFile):
            with open(orderFile, 'rt') as f:
                lines = f.read().split('\n')

                for line in lines:
                    if line.strip() == '':
                        continue
                    
                    # The order.txt file is assumed to
                    # contain one row per cmap/lut,
                    # where the first word is the key
                    # (the cmap/lut file name prefix),
                    # and the remainder of the line is
                    # the cmap/lut name
                    key, name = line.split(' ', 1)

                    allmaps[key.strip()] = name.strip()

        # Search through all cmap/lut files that exist -
        # any which were not specified in order.txt
        # are added to the end of the list, and their
        # name is just set to the file name prefix
        for mapFile in sorted(glob.glob(op.join(rdir, '*.{}'.format(suffix)))):

            name = op.basename(mapFile).split('.')[0]

            if name not in allmaps:
                allmaps[name] = name

        # Now load all of the cmaps/luts
        for key, name in allmaps.items():
            mapFile = op.join(rdir, '{}.{}'.format(key, suffix))

            try:
                kwargs = {'key' : key, 'name' : name}
                
                if   suffix == 'cmap': registerColourMap(  mapFile, **kwargs)
                elif suffix == 'lut':  registerLookupTable(mapFile, **kwargs)
                
                register[key].installed    = True
                register[key].mapObj.saved = True

            except Exception as e:
                log.warn('Error processing custom {} '
                         'file {}: {}'.format(suffix, mapFile, str(e)),
                         exc_info=True)


def registerColourMap(cmapFile,
                      overlayList=None,
                      displayCtx=None,
                      key=None,
                      name=None):
    """Loads RGB data from the given file, and registers
    it as a :mod:`matplotlib` :class:`~matplotlib.colors.ListedColormap`
    instance.

    .. note:: If the ``overlayList`` and ``displayContext`` arguments are
              provided, the ``cmap`` property of all :class:`.VolumeOpts`
              instances are updated to support the new colour map.

    :arg cmapFile:    Name of a file containing RGB values

    :arg overlayList: A :class:`.OverlayList` instance which contains all
                      overlays that are being displayed (can be ``None``).
    
    :arg displayCtx:  A :class:`.DisplayContext` instance describing how
                      the overlays in ``overlayList`` are being displayed.
                      Must be provided if ``overlayList`` is provided.

    :arg key:         Name to give the colour map. If ``None``, defaults
                      to the file name prefix.

    :arg name:        Display name for the colour map. If ``None``, defaults
                      to the ``name``. 
    """

    import matplotlib.cm     as mplcm
    import matplotlib.colors as colors
    
    if key         is None: key         = op.basename(cmapFile).split('.')[0]
    if name        is None: name        = key
    if overlayList is None: overlayList = []

    data = np.loadtxt(cmapFile)
    cmap = colors.ListedColormap(data, name)

    log.debug('Loading and registering custom '
              'colour map: {}'.format(cmapFile))

    mplcm.register_cmap(key, cmap)

    _cmaps[key] = _Map(key, name, cmap, None, False)

    log.debug('Patching DisplayOpts instances and class '
              'to support new colour map {}'.format(key))

    import fsl.fsleyes.displaycontext as fsldisplay
    
    # A list of all DisplayOpts colour map properties
    # 
    # TODO Any new DisplayOpts sub-types which have a 
    #      colour map will need to be patched here
    cmapProps = []
    cmapProps.append((fsldisplay.VolumeOpts, 'cmap'))
    cmapProps.append((fsldisplay.VolumeOpts, 'negativeCmap'))
    cmapProps.append((fsldisplay.VectorOpts, 'cmap'))

    # Update the colour map properties
    # for any existing instances 
    for overlay in overlayList:
        opts = displayCtx.getOpts(overlay)

        for cls, propName in cmapProps:
            if isinstance(opts, cls):
                prop = opts.getProp(propName)
                prop.addColourMap(key, opts)

    # and for all future overlays
    for cls, propName in cmapProps:
        
        prop = cls.getProp(propName)
        prop.addColourMap(key)
                

def registerLookupTable(lut,
                        overlayList=None,
                        displayCtx=None,
                        key=None,
                        name=None):
    """Registers the given ``LookupTable`` instance (if ``lut`` is a string,
    it is assumed to be the name of a ``.lut`` file, which is loaded).

    .. note:: If the ``overlayList`` and ``displayContext`` arguments are
              provided, the ``lut`` property of all :class:`.LabelOpts`
              instances are updated to support the new lookup table.

    :arg lut:         A :class:`LookupTable` instance, or the name of a
                      ``.lut`` file.

    :arg overlayList: A :class:`.OverlayList` instance which contains all
                      overlays that are being displayed (can be ``None``).
    
    :arg displayCtx:  A :class:`.DisplayContext` instance describing how
                      the overlays in ``overlayList`` are being displayed.
                      Must be provided if ``overlayList`` is provided. 
    
    :arg key:         Name to give the lookup table. If ``None``, defaults
                      to the file name prefix.
    
    :arg name:        Display name for the lookup table. If ``None``, defaults
                      to the ``name``. 
    """

    if isinstance(lut, basestring): lutFile = lut
    else:                           lutFile = None

    if overlayList is None:
        overlayList = []

    # lut may be either a file name
    # or a LookupTable instance
    if lutFile is not None:

        if key  is None: key  = op.basename(lutFile).split('.')[0]
        if name is None: name = key

        log.debug('Loading and registering custom '
                  'lookup table: {}'.format(lutFile)) 
        
        lut = LookupTable(key, name, lutFile)
    else:
        if key  is None: key  = lut.name
        if name is None: name = key

        lut.key  = key
        lut.name = name

    # Even though the lut may have been loaded from
    # a file, it has not necessarily been installed
    lut.saved = False
            
    _luts[key] = _Map(key, name, lut, None, False)

    log.debug('Patching LabelOpts classes to support '
              'new LookupTable {}'.format(key))

    import fsl.fsleyes.displaycontext as fsldisplay

    # Update the lut property for
    # any existing label overlays
    for overlay in overlayList:
        opts = displayCtx.getOpts(overlay)

        if not isinstance(opts, fsldisplay.LabelOpts):
            continue

        lutChoice = opts.getProp('lut')
        lutChoice.addChoice(lut,
                            alternate=[lut.name, key],
                            instance=opts)

    # and for any future label overlays
    fsldisplay.LabelOpts.lut.addChoice(
        lut,
        alternate=[lut.name, key])
    
    return lut


def getLookupTables():
    """Returns a list containing all available lookup tables."""
    return [_luts[lutName].mapObj for lutName in _luts.keys()]


def getLookupTable(lutName):
    """Returns the :class:`LookupTable` instance of the specified name."""
    return _caseInsensitiveLookup(_luts, lutName).mapObj

        
def getColourMaps():
    """Returns a list containing the names of all available colour maps."""
    return  _cmaps.keys()


def getColourMap(cmapName):
    """Returns the colour map instance of the specified name."""
    return _caseInsensitiveLookup(_cmaps, cmapName).mapObj


def isColourMapRegistered(cmapName):
    """Returns ``True`` if the specified colourmap is registered, ``False``
    otherwise. 
    """ 
    return cmapName in _cmaps


def isLookupTableRegistered(lutName):
    """Returns ``True`` if the specified lookup table is registered, ``False``
    otherwise. 
    """ 
    return lutName in _luts


def isColourMapInstalled(cmapName):
    """Returns ``True`` if the specified colourmap is installed, ``False``
    otherwise.  A :exc:`KeyError` is raised if the colourmap is not registered.
    """
    return _cmaps[cmapName].installed


def isLookupTableInstalled(lutName):
    """Returns ``True`` if the specified loolup table is installed, ``False``
    otherwise.  A :exc:`KeyError` is raised if the lookup tabler is not
    registered.
    """
    return _luts[lutName].installed 


def installColourMap(cmapName):
    """Attempts to install a previously registered colourmap into the
    ``fsl/fsleyes/colourmaps`` directory.
    """

    # keyerror if not registered
    cmap = _cmaps[cmapName]

    if cmap.mapFile is not None:
        destFile = cmap.mapFile
    else:
        destFile = op.join(op.dirname(__file__),
                           'colourmaps',
                           '{}.cmap'.format(cmapName))

    log.debug('Installing colour map {} to {}'.format(cmapName, destFile))

    # I think the colors attribute is only
    # available on ListedColormap instances ...
    data = cmap.mapObj.colors
    np.savetxt(destFile, data, '%0.6f')
    
    cmap.installed = True


def installLookupTable(lutName):
    """Attempts to install/save a previously registered lookup table into
    the ``fsl/fsleyes/luts`` directory.
    """
    
    # keyerror if not registered
    lut = _luts[lutName]

    if lut.mapFile is not None:
        destFile = lut.mapFile
    else:
        destFile = op.join(
            _lutDir,
            '{}.lut'.format(lutName.lower().replace(' ', '_')))

    log.debug('Installing lookup table {} to {}'.format(lutName, destFile))

    lut.mapObj._save(destFile)

    lut.mapFile      = destFile
    lut.installed    = True
    lut.mapObj.saved = True
    

###############
# Miscellaneous
###############


def _briconToScaleOffset(brightness, contrast, drange):
    """Used by the :func:`briconToDisplayRange` and the :func:`applyBricon`
    functions.

    Calculates a scale and offset which can be used to transform a display
    range of the given size so that the given brightness/contrast settings
    are applied.

    :arg brightness: Brightness, between 0.0 and 1.0.
    :arg contrast:   Contrast, between 0.0 and 1.0.
    :arg drange:     Data range.
    """
    
    # The brightness is applied as a linear offset,
    # with 0.5 equivalent to an offset of 0.0.                
    offset = (brightness * 2 - 1) * drange

    # If the contrast lies between 0.0 and 0.5, it is
    # applied to the colour as a linear scaling factor.
    if contrast <= 0.5:
        scale = contrast * 2

    # If the contrast lies between 0.5 and 1, it
    # is applied as an exponential scaling factor,
    # so lower values (closer to 0.5) have less of
    # an effect than higher values (closer to 1.0).
    else:
        scale = 20 * contrast ** 4 - 0.25

    return scale, offset
    

def briconToDisplayRange(dataRange, brightness, contrast):
    """Converts the given brightness/contrast values to a display range,
    given the data range.

    :arg dataRange:  The full range of the data being displayed, a
                     (min, max) tuple.
    
    :arg brightness: A brightness value between 0 and 1.
    
    :arg contrast:   A contrast value between 0 and 1.
    """

    # Turn the given bricon values into
    # values between 1 and 0 (inverted)
    brightness = 1.0 - brightness
    contrast   = 1.0 - contrast

    dmin, dmax = dataRange
    drange     = dmax - dmin
    dmid       = dmin + 0.5 * drange

    scale, offset = _briconToScaleOffset(brightness, contrast, drange)

    # Calculate the new display range, keeping it
    # centered in the middle of the data range
    # (but offset according to the brightness)
    dlo = (dmid + offset) - 0.5 * drange * scale 
    dhi = (dmid + offset) + 0.5 * drange * scale

    return dlo, dhi


def displayRangeToBricon(dataRange, displayRange):
    """Converts the given brightness/contrast values to a display range,
    given the data range.

    :arg dataRange:    The full range of the data being displayed, a
                       (min, max) tuple.
    
    :arg displayRange: A (min, max) tuple containing the display range.
    """    

    dmin, dmax = dataRange
    dlo,  dhi  = displayRange
    drange     = dmax - dmin
    dmid       = dmin + 0.5 * drange

    # These are inversions of the equations in
    # the _briconToScaleOffset function above,
    # which calculate the display ranges from
    # the bricon offset/scale
    offset = dlo + 0.5 * (dhi - dlo) - dmid
    scale  = (dhi - dlo) / drange

    brightness = 0.5 * (offset / drange + 1)

    if scale <= 1: contrast = scale / 2.0
    else:          contrast = ((scale + 0.25)  / 20.0) ** 0.25

    brightness = 1.0 - brightness
    contrast   = 1.0 - contrast

    return brightness, contrast


def applyBricon(rgb, brightness, contrast):
    """Applies the given ``brightness`` and ``contrast`` levels to
    the given ``rgb`` colour(s).

    Passing in ``0.5`` for both the ``brightness``  and ``contrast`` will
    result in the colour being returned unchanged.

    :arg rgb:        A sequence of three or four floating point numbers in 
                     the range ``[0, 1]`` specifying an RGB(A) value, or a
                     :mod:`numpy` array of shape ``(n, 3)`` or ``(n, 4)``
                     specifying ``n`` colours. If alpha values are passed
                     in, they are returned unchanged.

    :arg brightness: A brightness level in the range ``[0, 1]``.

    :arg contrast:   A contrast level in the range ``[0, 1]``.
    """
    rgb       = np.array(rgb)
    oneColour = len(rgb.shape) == 1
    rgb       = rgb.reshape(-1, rgb.shape[-1])

    scale, offset = _briconToScaleOffset(brightness, contrast, 1)

    # The contrast factor scales the existing colour
    # range, but keeps the new range centred at 0.5.
    rgb[:, :3] += offset
  
    rgb[:, :3]  = np.clip(rgb[:, :3], 0.0, 1.0)
    rgb[:, :3]  = (rgb[:, :3] - 0.5) * scale + 0.5
    
    rgb[:, :3]  = np.clip(rgb[:, :3], 0.0, 1.0)

    if oneColour: return rgb[0]
    else:         return rgb


def randomColour():
    """Generates a random RGB colour. """
    return np.random.random(3)


def randomBrightColour():
    """Generates a random saturated RGB colour. """
    colour                  = np.random.random(3)
    colour[colour.argmax()] = 1
    colour[colour.argmin()] = 0

    np.random.shuffle(colour)

    return colour


def randomDarkColour():
    """Generates a random saturated and darkened RGB colour."""

    return applyBricon(randomBrightColour(), 0.35, 0.5)


def complementaryColour(rgb):
    """Generate a colour which can be used as a complement/opposite
    to the given colour.

    If the given ``rgb`` sequence contains four values, the fourth
    value (e.g. alpha) is returned unchanged.
    """

    if len(rgb) >= 4:
        a   = rgb[3:]
        rgb = rgb[:3]
    else:
        a   = []

    h, l, s = colorsys.rgb_to_hls(*rgb)

    # My ad-hoc complementary colour calculation:
    # create a new colour with the opposite hue
    # and opposite lightness, but the same saturation.
    nh = 1.0 - h
    nl = 1.0 - l
    ns = s

    # If the two colours have similar lightness
    # (according to some arbitrary threshold),
    # force the new one to have a different
    # lightness
    if abs(nl - l) < 0.3:
        if l > 0.5: nl = 0.0
        else:       nl = 1.0

    nr, ng, nb = colorsys.hls_to_rgb(nh, nl, ns)

    return [nr, ng, nb] + a


_cmapDir = op.join(op.dirname(__file__), 'colourmaps')
"""The directory in which all colour map files are stored. """


_lutDir = op.join(op.dirname(__file__), 'luts')
"""The directory in which all lookup table files are stored. """

_cmaps = None
"""An ``OrderedDict`` which contains all registered colour maps as
``{key : _Map}`` mappings.
"""


_luts = None
"""An ``OrderedDict`` which contains all registered lookup tables as
``{key : _Map}`` mappings.
"""


def _caseInsensitiveLookup(d, k, default=None):
    """Performs a case-insensitive lookup on the dictionary ``d``,
    with the key ``k``.

    This function is used to allow case-insensitive retrieval of colour maps
    and lookup tables.
    """

    v = d.get(k, None)

    if v is not None:
        return v

    keys  = d.keys()
    lKeys = map(str.lower, keys)

    try:
        idx = lKeys.index(k.lower())
    except:
        if default is not None: return default
        else:                   raise  KeyError(k)

    return d[keys[idx]]


class _Map(object):
    """A little class for storing details on registered colour maps and lookup
    tables. This class is only used internally.
    """

    
    def __init__(self, key, name, mapObj, mapFile, installed):
        """Create a ``_Map``.
        
        :arg key:         The identifier name of the colour map/lookup table,
                          which must be passed to the :func:`getColourMap` and
                          :func:`getLookupTable` functions to look up this
                          map object.

        :arg name:        The display name of the colour map/lookup table.

        :arg mapObj:      The colourmap/lut object, either a
                          :class:`matplotlib.colors..Colormap`, or a
                          :class:`LookupTable` instance.

        :arg mapFile:     The file from which this map was loaded,
                          or ``None`` if this cmap/lookup table only
                          exists in memory, or is a built in :mod:`matplotlib`
                          colourmap.

        :arg installed:   ``True`` if this is a built in :mod:`matplotlib`
                          colourmap or is installed in the
                          ``fsl/fsleyes/colourmaps/`` or ``fsl/fsleyes/luts/``
                          directory, ``False`` otherwise.
        """
        self.key       = key
        self.name      = name
        self.mapObj    = mapObj
        self.mapFile   = mapFile
        self.installed = installed

        
    def __str__(self):
        """Returns a string representation of this ``_Map``. """
        if self.mapFile is not None: return self.mapFile
        else:                        return self.key

        
    def __repr__(self):
        """Returns a string representation of this ``_Map``. """
        return self.__str__()


class LutLabel(object):
    """This class represents a mapping from a value to a colour and name.
    ``LutLabel`` instances are created and managed by :class:`LookupTable`
    instances.


    .. note:: When a ``LutLabel`` is created, the specified name is converted
              to lower case. This is done to make comparisons easier. The
              original name is still accessible through the :meth:`displayName`
              method.


    .. note:: ``LutLabel`` instances are only intended to be created by
              :class:`LookupTable` instances. They are intended to be used
              externally, however.


    .. note:: ``LutLabel`` instances are immutable - this makes the logic
              in the :class:`LookupTable` a bit easier. So instead of
              modifying an existing ``LutLabel``, you need to create a new
              one based on the existing one.
    """

    
    def __init__(self, value, name, colour, enabled):
        """Create a ``LutLabel``.

        :arg value:   The label value.
        :arg name:    The label name.
        :arg colour:  The label colour.
        :arg enabled: Whether the label is enabled/disabled.
        """

        if value   is None: raise ValueError('LutLabel value cannot be None')
        if name    is None: name    = 'Label'
        if colour  is None: colour  = (0, 0, 0)
        if enabled is None: enabled = True
        
        self.__value       = value
        self.__displayName = name
        self.__name        = name.lower()
        self.__colour      = colour
        self.__enabled     = enabled


    def value(self):
        """Returns the value of this ``LutLabel``. """ 
        return self.__value

    
    def name(self):
        """Returns the name of this ``LutLabel``. """ 
        return self.__name


    def displayName(self):
        """Returns the display name of this ``LutLabel``. """
        return self.__displayName

    
    def colour(self):
        """Returns the colour of this ``LutLabel``. """ 
        return self.__colour

    
    def enabled(self):
        """Returns the enabled state of this ``LutLabel``. """ 
        return self.__enabled


    def __eq__(self, other):
        """Equality operator - returns ``True`` if this ``LutLabel``
        has the same  value, name, colour, and enabled state as the
        given one.
        """
        
        return (self.__value   == other.__value  and
                self.__name    == other.__name   and
                self.__colour  == other.__colour and
                self.__enabled == other.__enabled)

    
    def __cmp__(self, other):
        """Comparison operator - compares two ``LutLabel`` instances
        based on their value.
        """
        return self.__value.__cmp__(other.__value)

    
    def __hash__(self):
        """The hash of a ``LutLabel`` is a combination of its
        value, name, and colour, but not its enabled state.
        """
        return (hash(self.__value) ^
                hash(self.__name)  ^
                hash(self.__colour))

    
    def __str__(self):
        """Returns a string representation of this ``LutLabel``."""
        return '{}: {} / {} ({})'.format(self.__value,
                                         self.__name,
                                         self.__colour,
                                         self.__enabled)


    def __repr__(self):
        """Returns a string representation of this ``LutLabel``."""
        return self.__str__()
    

class LookupTable(props.HasProperties):
    """A ``LookupTable`` encapsulates a list of label values and associated
    colours and names, defining a lookup table to be used for colouring label
    images.

    A label value typically corresponds to an anatomical region (as in
    e.g. atlas images), or a classification (as in e.g. white/grey matter/csf
    segmentations).


    The label values, and their associated names/colours, in a ``LookupTable``
    are stored in ``LutLabel`` instances. These are accessible via the
    :meth:`get` method. New label values can be added, and existing label
    names/colours modified, via the :meth:`set` method. Label values can be
    removed via the meth:`delete` method.


    .. note:: All label names are converted to lower case internally, but the
              name that is initially specified is still available - see the
              :class:`LutLabel` class documentation.

    .. warning:: Do not directly modify the :attr:`labels` list. If you do,
                 it will be your fault when things break. Use the :meth:`set`
                 and :meth:`delete` methods instead.

                 You can, however, read the :attr:`labels` list, and register
                 to be notified when it changes. I'm not that unreasonable.
    """

    
    name = props.String()
    """The name of this lut. """

    
    labels = props.List()
    """A list of :class:`LutLabel` instances, defining the label ->
    colour/name mappings. This list is sorted in increasing order
    by the label value.

    If you modify this list directly, you will probably break things. Use
    the :meth:`set`/:meth:`delete` methods instead, to add/change/remove
    labels.
    """


    saved = props.Boolean(default=False)
    """A read only property which contains the current saved state of this
    ``LookupTable`` - it is ``True``, if the current state of this
    ``LookupTable`` has been saved to a file, ``False`` otherwise.
    """

    
    def __init__(self, key, name, lutFile=None):
        """Create a ``LookupTable``.

        :arg key:     The identifier for this ``LookupTable``.

        :arg name:    The display name for this ``LookupTable``.

        :arg lutFile: A file to load lookup table label values, names, and
                      colours from. If ``None``, this ``LookupTable`` will
                      be empty - labels can be added with the :meth:`set`
                      method.
        """

        self.key  = key
        self.name = name

        if lutFile is not None:
            self._load(lutFile)


    def __str__(self):
        """Returns the name of this ``LookupTable``. """
        return self.name

    
    def __repr__(self):
        """Returns the name of this ``LookupTable``. """
        return self.name 
        

    def __len__(self):
        """Returns the number of labels in this ``LookupTable``. """
        return len(self.labels)


    def max(self):
        """Returns the maximum label value in this lookup table. """

        if len(self.labels) == 0: return 0
        else:                     return max([l.value() for l in self.labels])


    def __find(self, value):
        """Finds the :class:`LutLabel` instance associated with the specified
        value.  Returns a tuple containing the index of the ``LutLabel`` in
        the :attr:`labels` list, and the ``LutLabel`` instance itself.

        Otherwise, if there is no label associated with the given value,
        ``(-1, None)`` is returned.
        """

        for i, label in enumerate(self.labels):
            if label.value() == value:
                return i, label

        return (-1, None)


    def get(self, value):
        """Returns the :class:`LutLabel` instance associated with the given
        ``value``, or ``None`` if there is no label.
        """
        return self.__find(value)[1]


    def getByName(self, name):
        """Returns the :class:`LutLabel` instance associated with the given
        ``name``, or ``None`` if there is no ``LutLabel``. The name comparison
        is case-insensitive.
        """
        name = name.lower()
        
        for i, ll in enumerate(self.labels):
            if ll.name() == name:
                return ll
            
        return None


    def new(self, name, colour=None, enabled=True):
        """Create a new label. The new label is given the value ``max() + 1``.

        :arg name:    Label name
        :arg colour:  Label colour. If not previded, a random colour is used.
        :arg enabled: Label enabled state .
        """
        if colour is None:
            colour = randomBrightColour()
            
        return self.set(self.max() + 1,
                        name=name,
                        colour=colour,
                        enabled=enabled)


    def set(self, value, **kwargs):
        """Create a new label with the given value, or updates the
        colour/name/enabled states associated with the given value.

        :arg value:   The label value to add/update. Must be an integer.
        :arg name:    Label name
        :arg colour:  Label colour
        :arg enabled: Label enabled state
        """

        # At the moment, we are restricting
        # lookup tables to be unsigned 16 bit.
        # See gl/textures/lookuptabletexture.py
        if not isinstance(value, (int, long)) or \
           value < 0 or value > 65535:
            raise ValueError('Lookup table values must be '
                             '16 bit unsigned integers.')

        idx, label = self.__find(value)

        # No label exists for the given value,
        # so create a new LutLabel instance
        # with default values
        if idx == -1:
            label = LutLabel(value, None, None, None)

        # Create a new LutLabel instance with the
        # new, existing, or default label settings
        name    = kwargs.get('name',    label.displayName())
        colour  = kwargs.get('colour',  label.colour())
        enabled = kwargs.get('enabled', label.enabled())
        label   = LutLabel(value, name, colour, enabled)

        # Use the bisect module to
        # maintain the list order
        # when inserting new labels
        if idx == -1:
            
            log.debug('Adding new label to {}: {}'.format(
                self.name, label))
            
            lutChanged = True
            bisect.insort(self.labels, label)
        else:
            lutChanged = not (self.labels[idx].name()   == label.name() and 
                              self.labels[idx].colour() == label.colour())

            log.debug('Updating label in {}: {} -> {} (changed: {})'.format(
                self.name, self.labels[idx], label, lutChanged))
            
            self.labels[idx] = label            

        # Update the saved state if a new label has been added,
        # or an existing label name/colour has been changed
        if lutChanged:
            self.saved = False

        return label


    def delete(self, value):
        """Removes the given label value from the lookup table."""

        idx, label = self.__find(value)

        if idx == -1:
            raise ValueError('Value {} is not in lookup table')

        self.labels.pop(idx)
        self.saved = False

        
    def _load(self, lutFile):
        """Loads a ``LookupTable`` specification from the given file."""
        
        with open(lutFile, 'rt') as f:
            lines = f.readlines()

            for line in lines:
                tkns = line.split()

                label = int(     tkns[0])
                r     = float(   tkns[1])
                g     = float(   tkns[2])
                b     = float(   tkns[3])
                lName = ' '.join(tkns[4:])

                self.set(label, name=lName, colour=(r, g, b), enabled=True)


    def _save(self, lutFile):
        """Saves this ``LookupTable`` instance to the specified ``lutFile``.
        """

        with open(lutFile, 'wt') as f:
            for label in self.labels:
                value  = label.value()
                colour = label.colour()
                name   = label.displayName()

                tkns   = [value, colour[0], colour[1], colour[2], name]
                line   = ' '.join(map(str, tkns))

                f.write('{}\n'.format(line))
