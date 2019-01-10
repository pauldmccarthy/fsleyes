#!/usr/bin/env python
#
# overlay.py - Defines the OverlayList class, and a few utility functions
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`OverlayList` class, which is a simple but
fundamental class in *FSLeyes* - it is a container for all loaded overlays.
Only one ``OverlayList`` ever exists, and it is shared throughout the entire
application.


**What is an overlay?**


The definition of an *overlay* is fairly broad; any object can be added to
the ``OverlayList``  - there is no ``Overlay`` base class, nor any interface
which must be provided by an overlay object. The only requirements imposed on
an overlay type are:

  - Must be able to be created with a single ``__init__`` parameter, which
    is a string specifying the data source location (e.g. a file name) (but
    see the note below about ``Image`` overlays).

  - Must have an attribute called ``name``, which is used as the initial
    display name for the overlay.

  - Must have an attribute called ``dataSource``, which is used to identify
    the source of the overlay data.

  - Must be hashable (i.e. usable as a dictionary key).

  - Must be supported by the :mod:`~fsleyes.gl` package .. ok, this is a
    pretty big requirement .. See the :mod:`.globject` and the
    :data:`.displaycontext.OVERLAY_TYPES` documentation for details on how to
    get started with this one.


One further requirement is imposed on overlay types which derive from the
:class:`.Image` class:

 -  The ``__init__`` method for sub-classes of the ``Image`` class must
    accept the ``loadData``, ``calcRange``, ``indexed`` , and ``threaded``
    parameters, and pass them through to the base class ``__init__`` method.


Currently (``fsleyes`` version |version|) the only overlay types in existence
(and able to be rendered) are:

.. autosummary::
   :nosignatures:

   ~fsl.data.image.Image
   ~fsl.data.featimage.FEATImage
   ~fsl.data.melodicimage.MelodicImage
   ~fsl.data.mghimage.MGHImage
   ~fsl.data.dtifit.DTIFitTensor
   ~fsl.data.vtk.VTKMesh
   ~fsl.data.gifti.GiftiMesh
   ~fsl.data.freesurfer.FreesurferMesh


This module also provides a few convenience classes and functions:


.. autosummary::
   :nosignatures:

   ProxyImage
   findFEATImage
"""


import os.path as op
import            logging
import            weakref

import fsl.utils.deprecated as deprecated
import fsl.data.utils       as dutils
import fsl.data.image       as fslimage
import fsleyes_props        as props


log = logging.getLogger(__name__)


class OverlayList(props.HasProperties):
    """Class representing a collection of overlays to be displayed together.

    Contains a :class:`props.properties_types.List` property called
    :attr:`overlays`, containing overlay objects (e.g. :class:`.Image` or
    :class:`.Mesh` objects). Listeners can be registered on the
    ``overlays`` property, so they are notified when the overlay list changes.

    An :class:`OverlayList` object has a few wrapper methods around the
    :attr:`overlays` property, allowing the :class:`OverlayList` to be used as
    if it were a list itself.

    The :mod:`.loadoverlay` module contains some convenience functions for
    loading and adding overlays.

    The :meth:`getData` and :meth:`setData` methods allow arbitrary bits
    of data associated with an overlay to be stored and retrieved.
    """


    def __validateOverlay(self, atts, overlay):
        """Makes sure that the given overlay object is valid."""
        return (hasattr(overlay, 'name')      and
                hasattr(overlay, 'dataSource'))


    overlays = props.List(
        listType=props.Object(allowInvalid=False,
                              validateFunc=__validateOverlay))
    """A list of overlay objects to be displayed."""


    def __init__(self, overlays=None):
        """Create an ``OverlayList`` object from the given sequence of
        overlays."""

        if overlays is None: overlays = []
        self.overlays.extend(overlays)

        # The append/insert methods allow an initial
        # overlay type to be specified for newly
        # added overlays. This can be queried via
        # the initOverlayType method (and is done so
        # by DisplayContext instances).
        self.__initOverlayType = {}

        # This dictionary may be used throughout FSLeyes,
        # via the getData/setData methods, to store
        # any sort of data associated with an overlay.
        # It is a dict of dicts:
        #
        #   {
        #      overlay : {
        #        key : value,
        #        key : value,
        #      },
        #      overlay : {
        #        key : value,
        #        key : value,
        #      }
        #   }
        self.__overlayData = weakref.WeakKeyDictionary()


    def initOverlayType(self, overlay):
        """Returns the initial type for the given ``overlay``, if it was
        specified via the :meth:`append` or :meth:`insert` methods. Returns
        ``None`` otherwise.
        """
        return self.__initOverlayType.get(overlay, None)


    def getData(self, overlay, key, *args):
        """Returns any stored value associated with the specified ``overlay``
        and ``key``.

        :arg default: Default value if there is no value associated with the
                      given ``key``. If not specified, and an unknown key is
                      given, a ``KeyError`` is raised.
        """
        if len(args) not in (0, 1):
            raise RuntimeError('Invalid arguments: {}'.format(args))

        ovlDict = self.__overlayData.get(overlay, {})

        if len(args) == 1:
            return ovlDict.get(key, args[0])
        else:
            return ovlDict[key]


    def setData(self, overlay, key, value):
        """Stores the given value via the specified ``overlay`` and ``key``.
        """
        ovlDict = self.__overlayData.get(overlay, None)

        if ovlDict is not None:
            ovlDict[key] = value
        else:
            self.__overlayData[overlay] = {key : value}


    def find(self, name):
        """Returns the first overlay with the given ``name`` or ``dataSource``,
        or ``None`` if there is no overlay with said ``name``/``dataSource``.
        """

        if name is None:
            return None

        absname = op.abspath(name)

        for overlay in self.overlays:

            if overlay.name == name:
                return overlay

            if overlay.dataSource is None:
                continue

            # Ignore file extensions for NIFTI images.
            if isinstance(overlay, fslimage.Image):
                if fslimage.removeExt(overlay.dataSource) == \
                   fslimage.removeExt(absname):
                    return overlay
            else:
                if overlay.dataSource == absname:
                    return overlay

        return None


    def __str__(self):
        return self.overlays.__str__()

    def __repr__(self):
        return self.overlays.__str__()


    # Wrappers around the overlays list property, allowing this
    # OverlayList object to be used as if it is actually a list.
    def __len__(self):
        return self.overlays.__len__()

    def __getitem__(self, key):
        return self.overlays.__getitem__(key)

    def __iter__(self):
        return self.overlays.__iter__()

    def __contains__(self, item):
        return self.overlays.__contains__(item)

    def __setitem__(self, key, val):
        return self.overlays.__setitem__(key, val)

    def __delitem__(self, key):

        if   isinstance(key, slice): pass
        elif isinstance(key, int):   key = slice(key, key + 1, None)
        else:                        raise IndexError('Invalid key type')

        ovls = self[key]
        for ovl in ovls:
            self.__initOverlayType.pop(ovl, None)

        return self.overlays.__delitem__(key)

    def index(self, item):
        return self.overlays.index(item)

    def count(self, item):
        return self.overlays.count(item)

    def append(self, item, overlayType=None):

        with props.suppress(self, 'overlays', notify=True):

            self.overlays.append(item)

            if overlayType is not None:
                self.__initOverlayType[item] = overlayType


    def extend(self, iterable, overlayTypes=None):

        with props.suppress(self, 'overlays', notify=True):

            result = self.overlays.extend(iterable)

            if overlayTypes is not None:
                for overlay, overlayType in overlayTypes.items():
                    self.__initOverlayType[overlay] = overlayType

        return result

    def pop(self, index=-1):
        ovl = self.overlays.pop(index)
        self.__initOverlayType.pop(ovl, None)
        return ovl

    def move(self, from_, to):
        return self.overlays.move(from_, to)

    def remove(self, item):
        self.__initOverlayType.pop(item, None)
        self.overlays.remove(item)

    def clear(self):
        del self[:]

    def insert(self, index, item, overlayType=None):

        with props.suppress(self, 'overlays', notify=True):

            self.overlays.insert(index, item)

            if overlayType is not None:
                self.__initOverlayType[item] = overlayType


    def insertAll(self, index, items):
        return self.overlays.insertAll(index, items)


class ProxyImage(fslimage.Image):
    """The ``ProxyImage`` class is a simple wrapper around an :class:`Image`
    instance. It is intended to be used to represent images or data which
    are derived from another image.
    """

    def __init__(self, base, *args, **kwargs):
        """Create a ``ProxyImage``.

        :arg base:   The :class:`Image` instance upon which this ``ProxyImage``
                     is based.

        :arg volume: Must be passed as a keyword argument. If provided, is a
                     slice into the image data specifying the 3D volume to
                     copy. If not provided, the entire image is copied.
        """

        if not isinstance(base, fslimage.Image):
            raise ValueError('Base image must be an Image instance')

        self.__base = base

        kwargs['header'] = base.header

        volume = kwargs.pop('volume', None)
        if volume is not None: data = base[volume]
        else:                  data = base[:]

        fslimage.Image.__init__(self, data, *args, **kwargs)


    def getBase(self):
        """Returns the base :class:`Image` of this ``ProxyImage``. """
        return self.__base


class PropCache(object):
    """Deprecated - use :class:`fsleyes_props.PropCache` instead.

    A little convenience class which can be used to track and cache
    property values, related to each overlay in the :class:`.OverlayList`,
    on some :class:`.HasProperties` object.


    Whenever the selected overlay changes, the property values of the
    previously selected overlay are cached. Later on, when that overlay
    is re-selected, the cached property values may be retrieved via
    the :meth:`get` method.
    """


    @deprecated.deprecated(
        '0.22.0', '1.0.0', 'Use fsleyes_props.PropCache instead')
    def __init__(self, overlayList, displayCtx, target, propNames):
        """Create a ``PropCache``.

        :arg overlayList: The :class:`.OverlayList`.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg target:      The :class:`.HasProperties` instance containing
                          the properties that are to be cached.

        :arg propNames:   List containing the names of ``target`` properties
                          to be cached.
        """

        self.__name           = '{}_{}'.format(type(self).__name__, id(self))
        self.__overlayList    = overlayList
        self.__displayCtx     = displayCtx
        self.__target         = target
        self.__propNames      = propNames
        self.__currentOverlay = None

        # { (overlay, propName) : value }
        self.__cache          = {}

        self.__overlayList.addListener('overlays',
                                       self.__name,
                                       self.__selectedOverlayChanged)
        self.__displayCtx .addListener('selectedOverlay',
                                       self.__name,
                                       self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``PropCache`` is no longer needed.
        Removes property listeners and clears references.
        """
        self.__overlayList.removeListener('overlays',        self.__name)
        self.__displayCtx .removeListener('selectedOverlay', self.__name)

        self.__overlayList    = None
        self.__displayCtx     = None
        self.__currentOverlay = None
        self.__cache          = None


    def get(self, overlay, propName, *args):
        """Returns the cached property value for the specified ``overlay``.
        If there is no cached property value for the overlay, the specified
        ``default`` value is returned. If a ``default`` value is not
        provided, the current property value is returned.

        :arg overlay:  Overlay to retrieve the property value for

        :arg propName: Name of the property to return a value for

        :arg default:  Value to return if a value for the the
                       overlay/property is not cached
        """

        if len(args) not in (0, 1):
            raise ValueError('Invalid arguments passed to PropCache.get')

        defaultProvided = len(args) == 1

        val = self.__cache.get((overlay, propName), None)

        if val is None:
            if defaultProvided: val = args[0]
            else:               val = getattr(self.__target, propName)

        return val


    def __selectedOverlayChanged(self, *a):
        """Called when either the :attr:`.DisplayContext.selectedOverlay`,
        or the :attr:`.OverlayList.overlays` change. Caches property values
        pertaining to the previously selected overlay.
        """

        self.__cacheGC()

        oldOverlay = self.__currentOverlay
        newOverlay = self.__displayCtx.getSelectedOverlay()

        self.__currentOverlay = newOverlay

        if oldOverlay     is None       or \
           oldOverlay     is newOverlay or \
           oldOverlay not in self.__overlayList:
            return

        for prop in self.__propNames:
            self.__cache[oldOverlay, prop] = getattr(self.__target, prop)


    def __cacheGC(self):
        """Removes any obsolete entries (those pertaining to overlays which
        are no longer present in the :class:`.OverlayList`) from the cache.
        """

        keys = list(self.__cache.keys())

        for overlay, prop in keys:
            if overlay not in self.__overlayList:
                self.__cache.pop((overlay, prop))


@deprecated.deprecated(
    '0.28.0', '1.0.0', 'Use fsl.data.utils.guessType instead')
def guessDataSourceType(path):
    """Deprecated - use `fsl.data.utils.guessType` instead. """
    return dutils.guessType(path)


def findFEATImage(overlayList, overlay):
    """Searches the given :class:`.OverlayList` to see if there is a
    :class:`.FEATImage` associated with the given ``overlay``. Returns the
    ``FEATImage`` if found, otherwise returns ``None``.
    """

    import fsl.data.featanalysis as featanalysis
    import fsl.data.featimage    as featimage

    if isinstance(overlay, featimage.FEATImage): return overlay
    if overlay            is None:               return None
    if overlay.dataSource is None:               return None

    featPath = featanalysis.getAnalysisDir(overlay.dataSource)

    if featPath is None:
        return None

    dataPath  = featanalysis.getDataFile(featPath)
    featImage = overlayList.find(dataPath)

    return featImage


def findMeshReferenceImage(overlayList, overlay):
    """Searches the :class:`.OverlayList` and tries to identify a reference
    image for the given :class:`.Mesh` overlay. Returns the identified
    overlay, or ``None`` if one can't be found.
    """

    import fsl.data.vtk as fslvtk

    # TODO support for gifti/freesurfer

    if not isinstance(overlay, fslvtk.VTKMesh):
        return None

    try:
        prefix = fslvtk.getFIRSTPrefix(overlay.dataSource)

        for ovl in overlayList:
            if prefix.startswith(ovl.name):
                return ovl

    except Exception:
        pass

    return None
