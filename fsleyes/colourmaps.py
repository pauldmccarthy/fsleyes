#!/usr/bin/env python
#
# colourmaps.py - Manage colour maps and lookup tables for overlay rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module manages the colour maps and lookup tables available for overlay
rendering in *FSLeyes*.


The :func:`init` function must be called before any colour maps or lookup
tables can be accessed [*]_.


FSLeyes colour maps and lookup tables are stored in the following locations:


   - ``[assetsbase]/assets/colourmaps/``
   - ``[assetsbase]/assets/luts/``
   - ``[settingsbase]/colourmaps/``
   - ``[settingsbase]/luts/``


where ``[assetsbase]`` is the location of the FSLeyes assets directory (see
the :attr:`fsleyes.assetDir` attribute), and ``[settingsbase]`` is the base
directory use by the :mod:`fsl.utils.settings` module for storing FSLeyes
application settings and data. "Built-in" colour maps and lookup tables are
stored underneath ``[assetsbase]``, and user-added ones are stored under
``[settingsbase]``.


When :func:`init` is called, it searches in the above locations, and attempts
to load all files within which have the suffix ``.cmap`` or ``.lut``
respectively. If a user-added map file has the same name as a built-in map
file, the user-added one will override the built-in.


.. [*] Only the :func:`scanColourMaps` and :func:`scanLookupTables` functions
       may be called before :func:`init` is called.


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


The following functions are available for managing and accessing colour maps:

.. autosummary::
   :nosignatures:

   scanColourMaps
   getColourMaps
   getColourMap
   getColourMapLabel
   getColourMapFile
   loadColourMapFile
   registerColourMap
   installColourMap
   isColourMapRegistered
   isColourMapInstalled


Display name and ordering
^^^^^^^^^^^^^^^^^^^^^^^^^


For built-in colour maps, a file named ``[assetsbase]/colourmaps/order.txt``
is assumed to contain a list of colour map names, and colour map identifiers,
defining the order in which the colour maps should be displayed to the
user. Any colour maps which are present in ``[assetsbase]/colourmaps/``, but
are not listed in the ``order.txt``, file will be appended to the end of the
list, and their name will be derived from the file name.


If a file ``[settingsbase]/colourmaps/order.txt`` exists, then it will be used
in place of the ``order.txt`` file in ``[assetsbase]``.


User-added colour maps
^^^^^^^^^^^^^^^^^^^^^^


An identifier and display name for all user-added colour maps are added to a
persistent setting called ``fsleyes.colourmaps``, which is a dictionary of ``{
cmapid : displayName }`` mappings. The ``cmapid`` is typically the display
name, converted to lower case, with spaces replaced with underscores. A
user-added colour map with id ``cmapid`` will be saved as
``[settingsbase]/colourmaps/cmapid.cmap``.  All user-added colour maps wll be
displayed after all built-in colour maps, and their order cannot be
customised. Any user-added colour map files which are not present in the
``fsleyes.colourmaps`` dictionary will be given a display name the same as
the colour map ID (which is taken from the file name).


Installing a user-added colour map is a two-step process:

 1. First, the colour map must be *registered*, via the
    :func:`registerColourMap` function. This adds the colour map to the
    register, but does not persist it beyond the current execution
    environment.

 2. Calling the :func:`installColourMap` function will add the colour map
    permanently.


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

Built-in and user-added lookup tables are managed in the same manner as
described for colour maps above.  The following functions are available to
access and manage :class:`LookupTable` instances:

.. autosummary::
   :nosignatures:

   scanLookupTables
   getLookupTables
   getLookupTable
   getLookupTableFile
   loadLookupTableFile
   registerLookupTable
   installLookupTable
   isLookupTableRegistered
   isLookupTableInstalled


-------------
Miscellaneous
-------------


Some utility functions are also kept in this module.  These functions are used
for querying installed colour maps and lookup tables,

.. autosummary::
   :nosignatures:

   fileType
   getCmapDir
   getLutDir
   scanBuiltInCmaps
   scanBuiltInLuts
   scanUserAddedCmaps
   scanUserAddedLuts
   makeValidMapKey
   isValidMapKey

The following functions may be used for calculating the relationship between a
data display range and brightness/contrast scales, and generating/manipulating
colours:


.. autosummary::
   :nosignatures:

   displayRangeToBricon
   briconToDisplayRange
   briconToScaleOffset
   applyBricon
   randomColour
   randomBrightColour
   randomDarkColour
   complementaryColour
"""


import itertools as it
import functools as ft
import os.path   as op
import              os
import              bisect
import              string
import              logging
import              colorsys

import numpy             as np
import matplotlib        as mpl
import matplotlib.cm     as mplcm
import matplotlib.colors as colors

import fsl.version            as fslversion
import fsl.utils.settings     as fslsettings
import fsl.utils.notifier     as notifier
import fsl.data.vest          as vest
import fsleyes_props          as props
import                           fsleyes
import fsleyes.displaycontext as fsldisplay


log = logging.getLogger(__name__)


def getCmapDir():
    """Returns the directory in which all built-in colour map files are stored.
    """
    return op.join(fsleyes.assetDir, 'assets', 'colourmaps')


def getLutDir():
    """Returns the directory in which all built-in lookup table files are stored.
    """
    return op.join(fsleyes.assetDir, 'assets', 'luts')


def _walk(dirname, suffix):
    """Recursively searches ``dirname``, returning a list of all files with the
    specified ``suffix``.
    """
    matches = []
    for dirpath, dirnames, filenames in os.walk(dirname):
        for filename in filenames:
            if filename.endswith(suffix):
                matches.append(op.join(dirpath, filename))
    return matches


def _find(mapid, dirname):
    """Finds the file associated with the given (built-in) colour map or lookup
    table ID.
    """

    divs     = [i for i, c in enumerate(mapid) if c == '_']
    pathopts = it.chain(*[it.combinations(divs, n)
                          for n in range(len(divs) + 1)])

    for pathidxs in pathopts:

        path = mapid
        for i in pathidxs:
            path = path[:i] + op.sep + path[i + 1:]

        path = op.join(dirname, path)

        if op.exists(path):
            return path

    raise ValueError('Cannot find {} in {}'.format(mapid, dirname))


def scanBuiltInCmaps():
    """Returns a list of IDs for all built-in colour maps. """

    basedir = getCmapDir()
    cmapIDs = _walk(basedir, '.cmap')
    cmapIDs = [op.splitext(i)[0]      for i in cmapIDs]
    cmapIDs = [op.relpath(i, basedir) for i in cmapIDs]
    cmapIDs = [i.replace(op.sep, '_') for i in cmapIDs]

    return list(sorted(cmapIDs))


def scanBuiltInLuts():
    """Returns a list of IDs for all built-in lookup tables. """

    basedir = getLutDir()
    lutIDs  = _walk(basedir, '.lut')
    lutIDs  = [op.splitext(i)[0]      for i in lutIDs]
    lutIDs  = [op.relpath(i, basedir) for i in lutIDs]
    lutIDs  = [i.replace(op.sep, '_') for i in lutIDs]

    return list(sorted(lutIDs))


def scanUserAddedCmaps():
    """Returns a list of IDs for all user-added colour maps. """

    cmapFiles = fslsettings.listFiles('colourmaps/*.cmap')
    cmapFiles = [op.basename(f)    for f in cmapFiles]
    cmapIDs   = [op.splitext(f)[0] for f in cmapFiles]
    cmapIDs   = [m.lower()         for m in cmapIDs]

    return list(sorted(cmapIDs))


def scanUserAddedLuts():
    """Returns a list of IDs for all user-added lookup tables. """

    lutFiles = fslsettings.listFiles('luts/*.lut')
    lutFiles = [op.basename(f)    for f in lutFiles]
    lutIDs   = [op.splitext(f)[0] for f in lutFiles]
    lutIDs   = [m.lower()         for m in lutIDs]

    return list(sorted(lutIDs))


def makeValidMapKey(name):
    """Turns the given string into a valid key for use as a colour map
    or lookup table identifier.
    """

    valid = string.ascii_lowercase + string.digits + '_-'
    key   = name.lower().replace(' ', '_')
    key   = ''.join([c for c in key if c in valid])

    return key


def isValidMapKey(key):
    """Returns ``True`` if the given string is a valid key for use as a colour
    map or lookup table identifier, ``False`` otherwise. A valid key comprises
    lower case letters, numbers, underscores and hyphens.
    """

    valid = string.ascii_lowercase + string.digits + '_-'
    return all(c in valid for c in key)


def scanColourMaps():
    """Scans the colour maps directories, and returns a list containing the
    names of all colour maps contained within. This function may be called
    before :func:`init`.
    """
    return scanBuiltInCmaps() + scanUserAddedCmaps()


def scanLookupTables():
    """Scans the lookup tables directories, and returns a list containing the
    names of all lookup tables contained within. This function may be called
    before :func:`init`.
    """
    return scanBuiltInLuts() + scanUserAddedLuts()


_cmaps = None
"""A dict which contains all registered colour maps as ``{key : _Map}``
mappings.
"""


_luts = None
"""A dict which contains all registered lookup tables as ``{key : _Map}``
mappings.
"""


def init(force=False):
    """This function must be called before any of the other functions in this
    module can be used.

    It initialises the colour map and lookup table registers, loading all
    built-in and user-added colour map and lookup table files that exist.

    :arg force: Forces the registers to be re-initialised, even if they
                have already been initialised.
    """

    global _cmaps
    global _luts

    # Already initialised
    if not force and (_cmaps is not None) and (_luts is not None):
        return

    _cmaps = {}
    _luts  = {}

    # Reads the order.txt file from the built-in
    # /colourmaps/ or /luts/ directory. This file
    # contains display names and defines the order
    # in which built-in maps should be displayed.
    def readOrderTxt(filename):
        maps = {}

        if not op.exists(filename):
            return maps

        with open(filename, 'rt') as f:
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
                key, name         = line.split(' ', 1)
                maps[key.strip()] = name.strip()
        return maps

    # Reads any display names that have been
    # defined for user-added colourmaps/luts
    # (mapType is either 'cmap' or 'lut').
    def readDisplayNames(mapType):
        if   mapType == 'cmap': key = 'fsleyes.colourmaps'
        elif mapType == 'lut':  key = 'fsleyes.luts'
        return fslsettings.read(key, {})

    # Get all colour map/lut IDs and
    # paths to the cmap/lut files. We
    # process cmaps/luts in the same
    # way, so we loop over all of
    # these lists, doing colour maps
    # first, then luts second.
    mapTypes    = ['cmap',               'lut']
    builtinDirs = [getCmapDir(),         getLutDir()]
    userDirs    = ['colourmaps',         'luts']
    allBuiltins = [scanBuiltInCmaps(),   scanBuiltInLuts()]
    allUsers    = [scanUserAddedCmaps(), scanUserAddedLuts()]
    registers   = [_cmaps,               _luts]

    for mapType, builtinDir, userDir, builtinIDs, userIDs, register in zip(
            mapTypes, builtinDirs, userDirs, allBuiltins, allUsers, registers):

        builtinFiles = ['{}.{}'.format(m, mapType) for m in builtinIDs]
        builtinFiles = [_find(m, builtinDir)       for m in builtinFiles]
        userFiles    = ['{}.{}'.format(m, mapType) for m in userIDs]
        userFiles    = [op.join(userDir, m)        for m in userFiles]
        userFiles    = [fslsettings.filePath(m)    for m in userFiles]

        allIDs   = builtinIDs   + userIDs
        allFiles = builtinFiles + userFiles
        allFiles = dict(zip(allIDs, allFiles))

        # Read order/display names from order.txt -
        # if an order.txt file exists in the user
        # dir, it takes precednece over built-in
        # order/display names.
        #
        # User-added display names may also be in
        # fslsettings. Any user-added maps with
        # the same ID as a builtin will override
        # the builtin.
        builtinOrder = op.join(builtinDir, 'order.txt')
        userOrder    = op.join(userDir,    'order.txt')

        if op.exists(userOrder): names = readOrderTxt(userOrder)
        else:                    names = readOrderTxt(builtinOrder)

        names.update(readDisplayNames(mapType))

        # any maps which did not have a name
        # specified in order.txt (or, for
        # user-added maps, in fslsettings)
        # are added to the end of the list,
        # and their name is just set to the
        # ID (which is equal to the file name
        # prefix).
        for mid in allIDs:
            if mid not in names:
                names[mid] = mid

        # Now register all of those maps,
        # in the order defined by order.txt
        for mapID, mapName in names.items():

            # The user-added {id:name} dict
            # might contain obsolete/invalid
            # names, so we ignore keyerrors
            try:
                mapFile = allFiles[mapID]
            except KeyError:
                continue

            try:
                kwargs = {'key' : mapID, 'name' : mapName}

                if   mapType == 'cmap': registerColourMap(  mapFile, **kwargs)
                elif mapType == 'lut':  registerLookupTable(mapFile, **kwargs)

                register[mapID].installed    = True
                register[mapID].mapObj.saved = True

            except Exception as e:
                log.warn('Error processing custom {} '
                         'file {}: {}'.format(mapType, mapFile, str(e)),
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

    :returns:         The key that the ``ColourMap`` was registered under.
    """

    if key is not None and not isValidMapKey(key):
        raise ValueError('{} is not a valid colour map identifier'.format(key))

    if key is None:
        key = op.basename(cmapFile).split('.')[0]
        key = makeValidMapKey(key)

    if name        is None: name        = key
    if overlayList is None: overlayList = []

    data = loadColourMapFile(cmapFile)
    cmap = colors.ListedColormap(data, key)

    log.debug('Loading and registering custom '
              'colour map: {}'.format(cmapFile))

    # matplotlib 3.3.4 and newer will raise an error
    # when trying to register a colour map with the
    # same name as a built-in, unless override_builtin
    # (also added in that version) is set to True.
    if fslversion.compareVersions(mpl.__version__, '3.3.4') > 0:
        mplcm.register_cmap(key, cmap, override_builtin=True)
    else:
        mplcm.register_cmap(key, cmap)

    _cmaps[key] = _Map(key, name, cmap, cmapFile, False)

    log.debug('Patching DisplayOpts instances and class '
              'to support new colour map {}'.format(key))

    # A list of all DisplayOpts colour map properties.
    # n.b. We can't simply list the ColourMapOpts class
    # here, because it is a mixin, and does not actually
    # derive from props.HasProperties.
    #
    # TODO Any new DisplayOpts sub-types which have a
    #      colour map will need to be patched here
    cmapProps = []
    cmapProps.append((fsldisplay.VolumeOpts, 'cmap'))
    cmapProps.append((fsldisplay.VolumeOpts, 'negativeCmap'))
    cmapProps.append((fsldisplay.VectorOpts, 'cmap'))
    cmapProps.append((fsldisplay.MeshOpts,   'cmap'))
    cmapProps.append((fsldisplay.MeshOpts,   'negativeCmap'))

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

    return key


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

    :returns:         The :class:`LookupTable` object
    """

    if isinstance(lut, str): lutFile = lut
    else:                    lutFile = None

    if overlayList is None:
        overlayList = []

    # lut may be either a file name
    # or a LookupTable instance
    if lutFile is not None:

        if key is None:
            key = op.basename(lutFile).split('.')[0]
            key = makeValidMapKey(key)

        if name is None:
            name = key

        log.debug('Loading and registering custom '
                  'lookup table: {}'.format(lutFile))

        lut = LookupTable(key, name, lutFile)

    else:
        if key  is None: key  = lut.key
        if name is None: name = lut.name

        lut.key  = key
        lut.name = name

    # Even though the lut may have been loaded from
    # a file, it has not necessarily been installed
    lut.saved = False

    _luts[key] = _Map(key, name, lut, lutFile, False)

    log.debug('Patching LabelOpts classes to support '
              'new LookupTable {}'.format(key))

    # See similar situation in the registerColourMap
    # function above. All DisplayOpts classes which
    # have a lut property (assumed to be a props.Choice)
    # must have the new LUT added as an option.
    lutProps = []
    lutProps.append((fsldisplay.LabelOpts, 'lut'))
    lutProps.append((fsldisplay.MeshOpts,  'lut'))

    # Update the lut property for
    # any existing label overlays
    for overlay in overlayList:
        opts = displayCtx.getOpts(overlay)

        for cls, propName in lutProps:
            if isinstance(opts, cls):
                prop = opts.getProp(propName)
                prop.addChoice(lut,
                               alternate=list(set((lut.name, key))),
                               instance=opts)

    # and for any future label overlays
    for cls, propName in lutProps:
        prop = cls.getProp(propName)
        prop.addChoice(lut, alternate=list(set((lut.name, key))))

    return lut


def getLookupTables():
    """Returns a list containing all available lookup tables."""
    return [_luts[lutName].mapObj for lutName in _luts.keys()]


def getLookupTable(key):
    """Returns the :class:`LookupTable` instance of the specified key/ID."""
    return _caseInsensitiveLookup(_luts, key).mapObj


def getColourMaps():
    """Returns a list containing the names of all available colour maps."""
    return list(_cmaps.keys())


def getColourMap(key):
    """Returns the colour map instance of the specified key."""
    return _caseInsensitiveLookup(_cmaps, key).mapObj


def getColourMapLabel(key):
    """Returns a label/display name for the specified colour map. """
    return _caseInsensitiveLookup(_cmaps, key).name


def getColourMapFile(key):
    """Returns the file associated with the specified colour map, or ``None``
    if the colour map is registered but not installed.
    """
    return _cmaps[key].mapFile


def getLookupTableFile(key):
    """Returns the file associated with the specified lookup table, or ``None``
    if the lookup table is registered but not installed.
    """
    return _luts[key].mapFile


def isColourMapRegistered(key):
    """Returns ``True`` if the specified colourmap is registered, ``False``
    otherwise.
    """
    return key in _cmaps


def isLookupTableRegistered(key):
    """Returns ``True`` if the specified lookup table is registered, ``False``
    otherwise.
    """
    return key in _luts


def isColourMapInstalled(key):
    """Returns ``True`` if the specified colourmap is installed, ``False``
    otherwise.  A :exc:`KeyError` is raised if the colourmap is not registered.
    """
    return _cmaps[key].installed


def isLookupTableInstalled(key):
    """Returns ``True`` if the specified loolup table is installed, ``False``
    otherwise.  A :exc:`KeyError` is raised if the lookup tabler is not
    registered.
    """
    return _luts[key].installed


def installColourMap(key):
    """Attempts to install a previously registered colourmap into the
    ``[settingsbase]/colourmaps/`` directory.
    """

    # keyerror if not registered
    cmap = _cmaps[key]

    # TODO I think the colors attribute is only
    #      available on ListedColormap instances,
    #      so if you ever start using different
    #      mpl types, you might need to revisit
    #      this.
    data = cmap.mapObj.colors

    destFile = op.join('colourmaps', '{}.cmap'.format(key))

    log.debug('Installing colour map {} to {}'.format(key, destFile))

    # Numpy under python 3 will break if
    # we give it a file opened with mode='wt'.
    with fslsettings.writeFile(destFile, mode='b') as f:
        np.savetxt(f, data, '%0.6f')

    # Update user-added settings
    cmapNames      = fslsettings.read('fsleyes.colourmaps', {})
    cmapNames[key] = cmap.name

    fslsettings.write('fsleyes.colourmaps', cmapNames)

    cmap.installed = True


def installLookupTable(key):
    """Attempts to install/save a previously registered lookup table into
    the ``[settingsbase]/luts`` directory.
    """

    # keyerror if not registered
    lut      = _luts[key]
    destFile = op.join('luts', '{}.lut'.format(key))
    destFile = fslsettings.filePath(destFile)
    destDir  = op.dirname(destFile)

    log.debug('Installing lookup table {} to {}'.format(key, destFile))

    if not op.exists(destDir):
        os.makedirs(destDir)

    lut.mapObj.save(destFile)

    # Update user-added settings
    lutNames      = fslsettings.read('fsleyes.luts', {})
    lutNames[key] = lut.name
    fslsettings.write('fsleyes.luts', lutNames)

    lut.mapFile   = destFile
    lut.installed = True


##########
# File I/O
##########


def fileType(fname):
    """Attempts to guess the type of ``fname``.

    ``fname`` is assumed to be a FSLeyes colour map or lookup table file,
    or a FSLView-style VEST lookup table file.

    A ``ValueError`` is raised if the file type cannot be determined.

    :arg fname: Name of file to check

    :returns:   One of ``'vest'``, ``'cmap'``, or ``'lut'``, depending on
                what the contents of ``fname`` look like.
    """

    if vest.looksLikeVestLutFile(fname):
        return 'vest'

    with open(fname, 'rt') as f:
        for line in f:
            line = f.readline().strip()
            if (line != '') and (not line.startswith('#')):
                break

    tkns = list(line.split())

    # cmap file
    if len(tkns) == 3:
        try:
            [float(t) for t in tkns]
            return 'cmap'
        except ValueError:
            pass

    # lut file
    elif len(tkns) >= 4:
        try:
            [float(t) for t in tkns[:4]]
            return 'lut'
        except ValueError:
            pass

    raise ValueError('Cannot determine type of {}'.format(fname))


def loadColourMapFile(fname, aslut=False):
    """Load the given file, assumed to be a colour map.

    :arg fname: FSLeyes or FSLView (VEST) colour map file

    :arg aslut: If ``True``, the returned array will contain a label for
                each colour, ranging from ``1`` to ``N``, where ``N`` is
                the number of colours in the file.

    :returns:   A ``numpy`` array of shape ``(N, 3)`` containing the
                RGB values for ``N`` colours. Or, if ``aslut is True``,
                A ``numpy`` array of shape ``(N, 4)`` containing a
                label, and the RGB values for ``N`` colours.
    """

    # The file could be a FSLView style VEST LUT
    if vest.looksLikeVestLutFile(fname):
        data = vest.loadVestLutFile(fname, normalise=False)

    # Or just a plain 2D text array
    else:
        data = np.loadtxt(fname)

    if aslut:
        lbls = np.arange(1, data.shape[0] + 1).reshape(-1, 1)
        data = np.hstack((lbls, data))

    return data


def loadLookupTableFile(fname):
    """Loads the given file, assumed to be a lookup table.

    :arg fname: Name of a FSLeyes lookup table file.

    :returns:   A tuple containing:

                 - A ``numpy`` array of shape ``(N, 4)`` containing the
                   label and RGB values for ``N`` colours.
                 - A list containin the name for each label

    .. note:: The provided file may also be a colour map file (see
              :func:`loadColourMapFile`), in which case the labels will range
              from ``1`` to ``N``, and the names will be strings containing
              the label values.
    """

    # Accept cmap file, auto-generate labels/names
    if fileType(fname) in ('vest', 'cmap'):
        lut   = loadColourMapFile(fname, aslut=True)
        names = ['{}'.format(int(l)) for l in lut[:, 0]]
        return lut, names

    # Otherwise assume a FSLeyes lut file
    with open(fname, 'rt') as f:

        # Read the LUT label/colours on
        # a first pass through the file
        struclut = np.genfromtxt(
            f,
            usecols=(0, 1, 2, 3),
            dtype={
                'formats' : (int, float, float, float),
                'names'   : ('label', 'r', 'g', 'b')})

        # Save the label ordering -
        # we'll use it below
        order     = struclut.argsort(order='label')

        # Convert from a structured
        # array into a regular array
        lut       = np.zeros((len(struclut), 4), dtype=np.float32)
        lut[:, 0] = struclut['label']
        lut[:, 1] = struclut['r']
        lut[:, 2] = struclut['g']
        lut[:, 3] = struclut['b']

        # Read the names on a second pass
        f.seek(0)
        names = []
        for i, line in enumerate(f):
            tkns = line.split(None, 4)
            if len(tkns) < 5: name = '{}'.format(int(lut[i, 0]))
            else:             name = tkns[4].strip()
            names.append(name)

    # Sort by ascending label value
    lut   = lut[order, :]
    names = [names[o] for o in order]

    return lut, names


###############
# Miscellaneous
###############


def briconToScaleOffset(brightness, contrast, drange):
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

    scale, offset = briconToScaleOffset(brightness, contrast, drange)

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

    if drange == 0:
        return 0, 0

    # These are inversions of the equations in
    # the briconToScaleOffset function above,
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

    scale, offset = briconToScaleOffset(brightness, contrast, 1)

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
    values = [randomColour.random.rand() for i in range(3)]
    return np.array(values)


# The randomColour function uses a generator
# with a fixed seed for reproducibility
randomColour.random = np.random.RandomState(seed=1)


def randomBrightColour():
    """Generates a random saturated RGB colour. """
    colour                  = randomColour()
    colour[colour.argmax()] = 1
    colour[colour.argmin()] = 0

    randomColour.random.shuffle(colour)

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
        a   = list(rgb[3:])
        rgb = list(rgb[:3])
    else:
        a   = []
        rgb = list(rgb)

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


def _caseInsensitiveLookup(d, k, default=None):
    """Performs a case-insensitive lookup on the dictionary ``d``,
    with the key ``k``.

    This function is used to allow case-insensitive retrieval of colour maps
    and lookup tables.
    """

    v = d.get(k, None)

    if v is not None:
        return v

    keys  = list(d.keys())
    lKeys = [k.lower() for k in keys]

    try:
        idx = lKeys.index(k.lower())
    except Exception:
        if default is not None: return default
        else:                   raise  KeyError(k)

    return d[keys[idx]]


class _Map:
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

        :arg installed: ``True`` if this is a built in :mod:`matplotlib`
                          colourmap or is installed in the
                          ``fsleyes/colourmaps/`` or ``fsleyes/luts/``
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


class LutLabel(props.HasProperties):
    """This class represents a mapping from a value to a colour and name.
    ``LutLabel`` instances are created and managed by :class:`LookupTable`
    instances.

    Listeners may be registered on the :attr:`name`, :attr:`colour`, and
    :attr:`enabled` properties to be notified when they change.
    """

    name = props.String(default='Label')
    """The display name for this label. Internally (for comparison), the
    :meth:`internalName` is used, which is simply this name, converted to
    lower case.
    """

    colour = props.Colour(default=(0, 0, 0))
    """The colour for this label. """


    enabled = props.Boolean(default=True)
    """Whether this label is currently enabled or disabled. """


    def __init__(self,
                 value,
                 name=None,
                 colour=None,
                 enabled=None):
        """Create a ``LutLabel``.

        :arg value:   The label value.
        :arg name:    The label name.
        :arg colour:  The label colour.
        :arg enabled: Whether the label is enabled/disabled.
        """

        if value is None:
            raise ValueError('LutLabel value cannot be None')

        if name is None:
            name = LutLabel.getProp('name').getAttribute(None, 'default')

        if colour is None:
            colour = LutLabel.getProp('colour').getAttribute(None, 'default')

        if enabled is None:
            enabled = LutLabel.getProp('enabled').getAttribute(None, 'default')

        self.__value = value
        self.name    = name
        self.colour  = colour
        self.enabled = enabled


    @property
    def value(self):
        """Returns the value of this ``LutLabel``. """
        return self.__value


    @property
    def internalName(self):
        """Returns the *internal* name of this ``LutLabel``, which is just
        its :attr:`name`, converted to lower-case. This is used by
        :meth:`__eq__` and :meth:`__hash__`, and by the
        :class:`LookupTable` class.
        """
        return self.name.lower()


    def __eq__(self, other):
        """Equality operator - returns ``True`` if this ``LutLabel``
        has the same  value as the given one.
        """

        return self.value == other.value


    def __lt__(self, other):
        """Less-than operator - compares two ``LutLabel`` instances
        based on their value.
        """
        return self.value < other.value


    def __hash__(self):
        """The hash of a ``LutLabel`` is a combination of its
        value, name, and colour, but not its enabled state.
        """
        return hash(      self.value)        ^ \
               hash(      self.internalName) ^ \
               hash(tuple(self.colour))


    def __str__(self):
        """Returns a string representation of this ``LutLabel``."""
        return '{}: {} / {} ({})'.format(self.value,
                                         self.internalName,
                                         self.colour,
                                         self.enabled)


    def __repr__(self):
        """Returns a string representation of this ``LutLabel``."""
        return self.__str__()


class LookupTable(notifier.Notifier):
    """A ``LookupTable`` encapsulates a list of label values and associated
    colours and names, defining a lookup table to be used for colouring label
    images.


    A label value typically corresponds to an anatomical region (as in
    e.g. atlas images), or a classification (as in e.g. white/grey matter/csf
    segmentations).


    The label values, and their associated names/colours, in a ``LookupTable``
    are stored in ``LutLabel`` instances, ordered by their value in ascending
    order. These are accessible by label value via the :meth:`get` method, by
    index, by directly indexing the ``LookupTable`` instance, or by name, via
    the :meth:`getByName` method.  New label values can be added via the
    :meth:`insert` and :meth:`new` methods. Label values can be removed via
    the meth:`delete` method.


    *Notifications*


    The ``LookupTable`` class implements the :class:`.Notifier` interface.
    If you need to be notified when a ``LookupTable`` changes, you may
    register to be notified on the following topics:


    =========== ====================================================
    *Topic*     *Meaning*
    ``label``   The properties of a :class:`.LutLabel` have changed.
    ``saved``   The saved state of this ``LookupTable`` has changed.
    ``added``   A new ``LutLabel`` has been added.
    ``removed`` A ``LutLabel`` has been removed.
    =========== ====================================================
    """


    def __init__(self, key, name, lutFile=None):
        """Create a ``LookupTable``.

        :arg key:     The identifier for this ``LookupTable``. Must be
                      a valid key (see :func:`isValidMapKey`).

        :arg name:    The display name for this ``LookupTable``.

        :arg lutFile: A file to load lookup table label values, names, and
                      colours from. If ``None``, this ``LookupTable`` will
                      be empty - labels can be added with the :meth:`new` or
                      :meth:`insert` methods.
        """

        if not isValidMapKey(key):
            raise ValueError('{} is not a valid lut identifier'.format(key))

        self.key      = key
        self.name     = name
        self.__labels = []
        self.__name   = 'LookupTable({})_{}'.format(self.name, id(self))

        # The LUT is loaded now, but parsed
        # lazily on first access
        self.__saved   = False
        self.__parsed  = False
        self.__toParse = None

        if lutFile is not None:
            self.__toParse = loadLookupTableFile(lutFile)
            self.__saved   = True


    def lazyparse(func):
        """Decorator which is used to lazy-parse the LUT file only when it is
        first needed.
        """

        def wrapper(self, *args, **kwargs):
            if not self.__parsed and self.__toParse is not None:
                self.__parse(*self.__toParse)
                self.__toParse = None
                self.__parsed  = True
            return func(self, *args, **kwargs)
        return ft.update_wrapper(wrapper, func)


    def __str__(self):
        """Returns the name of this ``LookupTable``. """
        return self.name


    def __repr__(self):
        """Returns the name of this ``LookupTable``. """
        return self.name


    @lazyparse
    def __len__(self):
        """Returns the number of labels in this ``LookupTable``. """
        return len(self.__labels)


    @lazyparse
    def __getitem__(self, i):
        """Access the ``LutLabel`` at index ``i``. Use the :meth:`get` method
        to determine the index of a ``LutLabel`` from its value.
        """
        return self.__labels[i]


    @lazyparse
    def max(self):
        """Returns the maximum current label value in this ``LookupTable``. """
        if len(self.__labels) == 0: return 0
        else:                       return self.__labels[-1].value


    @property
    def saved(self):
        """Returns ``True`` if this ``LookupTable`` is registered and saved,
        ``False`` if it is not registered, or has been modified.
        """
        return self.__saved


    @saved.setter
    def saved(self, val):
        """Change the saved state of this ``LookupTable``, and trigger
        notification on the ``saved`` topic. This property should not
        be set outside of this module.
        """
        self.__saved = val
        self.notify(topic='saved')


    @lazyparse
    def index(self, value):
        """Returns the index in this ``LookupTable`` of the ``LutLabel`` with
        the specified value. Raises a :exc:`ValueError` if no ``LutLabel``
        with this value is present.

        .. note:: The ``value`` which is passed in can be either an integer
                  specifying the label value, or a ``LutLabel`` instance.
        """
        if not isinstance(value, LutLabel):
            value = LutLabel(value)

        return self.__labels.index(value)


    @lazyparse
    def labels(self):
        """Returns an iterator over all :class:`LutLabel` instances in this
        ``LookupTable``.
        """
        return iter(self.__labels)


    @lazyparse
    def get(self, value):
        """Returns the :class:`LutLabel` instance associated with the given
        ``value``, or ``None`` if there is no label.
        """
        try:               return self.__labels[self.index(value)]
        except ValueError: return None


    @lazyparse
    def getByName(self, name):
        """Returns the :class:`LutLabel` instance associated with the given
        ``name``, or ``None`` if there is no ``LutLabel``. The name comparison
        is case-insensitive.
        """
        name = name.lower()

        for i, ll in enumerate(self.__labels):
            if ll.internalName == name:
                return ll

        return None


    @lazyparse
    def new(self, name=None, colour=None, enabled=None):
        """Add a new :class:`LutLabel` with value ``max() + 1``, and add it
        to this ``LookupTable``.
        """
        return self.insert(self.max() + 1, name, colour, enabled)


    @lazyparse
    def insert(self, value, name=None, colour=None, enabled=None):
        """Create a new :class:`LutLabel` associated with the given
        ``value`` and insert it into this ``LookupTable``. Internally, the
        labels are stored in ascending (by value) order.

        :returns: The newly created ``LutLabel`` instance.
        """
        if not isinstance(value, (int, np.integer)) or \
           value < 0 or value > 65535:
            raise ValueError('Lookup table values must be '
                             '16 bit unsigned integers ({}: {}).'.format(
                                 type(value), value))

        if self.get(value) is not None:
            raise ValueError('Value {} is already in '
                             'lookup table'.format(value))

        label = LutLabel(value, name, colour, enabled)
        label.addGlobalListener(self.__name, self.__labelChanged)

        idx = bisect.bisect(self.__labels, label)
        self.__labels.insert(idx, label)

        self.saved = False
        self.notify(topic='added', value=(label, idx))

        return label


    @lazyparse
    def delete(self, value):
        """Removes the label with the given value from the lookup table.

        Raises a :exc:`ValueError` if no label with the given value is
        present.
        """

        idx   = self.index(value)
        label = self.__labels.pop(idx)

        label.removeGlobalListener(self.__name)

        self.notify(topic='removed', value=(label, idx))
        self.saved = False


    @lazyparse
    def save(self, lutFile):
        """Saves this ``LookupTable`` instance to the specified ``lutFile``.
        """

        with open(lutFile, 'wt') as f:
            for label in self:
                value  = label.value
                colour = label.colour
                name   = label.name
                tkns   = [value, colour[0], colour[1], colour[2], name]
                line   = ' '.join(map(str, tkns))

                f.write('{}\n'.format(line))

        self.saved = True


    def __parse(self, lut, names):
        """Parses ``lut``, a numpy array containing a LUT. """

        labels = [LutLabel(int(l), name, (r, g, b), l > 0)
                  for ((l, r, g, b), name) in zip(lut, names)]

        self.__labels = labels

        for label in labels:
            label.addGlobalListener(self.__name, self.__labelChanged)


    def __labelChanged(self, value, valid, label, propName):
        """Called when the properties of any ``LutLabel`` change. Triggers
        notification on the ``label`` topic.
        """

        if propName in ('name', 'colour'):
            self.saved = False

        self.notify(topic='label', value=(label, self.index(label)))
