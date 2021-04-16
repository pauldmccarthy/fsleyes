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
   ~fsl.data.bitmap.Bitmap


This module also provides a few convenience classes and functions:


.. autosummary::
   :nosignatures:

   ProxyImage
   findFEATImage
"""


import os.path as op
import            logging
import            weakref
import            collections

import fsl.data.utils as dutils
import fsl.data.image as fslimage
import fsleyes_props  as props


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

        # The append/insert methods allow display/opts
        # property values to be specified for newly
        # added overlays. These can be queried via
        # the initProps method (and is done so by
        # DisplayContext/Display instances).
        # It is a dict of dicts:
        #
        #    {
        #      overlay : {
        #        propName: value,
        #        propName: value,
        #      },
        #      ...
        #    }
        self.__initProps = collections.defaultdict(dict)

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


    def initProps(self, overlay):
        """Returns a dict containing initial :class:`.Display` and
        :class:`.DisplayOpts` property values to be used for the given
        ``overlay``, if they were specified via the :meth:`append` or
        :meth:`insert` methods.

        This method requires that there is no overlap between the property
        names used in :class:`.Display` and :class:`.DisplayOpts` classes.
        """
        return self.__initProps[overlay]


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
            self.__initProps.pop(ovl, None)

        return self.overlays.__delitem__(key)

    def index(self, item):
        return self.overlays.index(item)

    def count(self, item):
        return self.overlays.count(item)

    def insert(self, index, item, **initProps):
        """Insert a new overlay into the overlay list.

        Any initial :class:`.Display`/:class:`.DisplayOpts` property values
        may be passed in as keyword arguments.
        """

        with props.suppress(self, 'overlays', notify=True):
            self.overlays.insert(index, item)
            self.__initProps[item] = initProps

    def append(self, item, **initProps):
        """Add a new overlay to the end of the overlay list.

        Any initial :class:`.Display`/:class:`.DisplayOpts` property values
        may be passed in as keyword arguments.
        """
        self.insert(len(self), item, **initProps)

    def extend(self, iterable, **initProps):
        """Add new overlays to the overlay list.

        Any initial :class:`.Display`/:class:`.DisplayOpts` property values
        may be passed in as keyword arguments, where the argument name is the
        property name, and the argument value is a dict of
        ``{overlay : value}`` mappings.
        """

        with props.suppress(self, 'overlays', notify=True):

            result = self.overlays.extend(iterable)

            for propName, overlayProps in initProps.items():
                for overlay, val in overlayProps.items():
                    self.__initProps[overlay][propName] = val

        return result

    def insertAll(self, index, items):
        return self.overlays.insertAll(index, items)

    def pop(self, index=-1):
        ovl = self.overlays.pop(index)
        self.__initProps.pop(ovl, None)
        return ovl

    def move(self, from_, to):
        return self.overlays.move(from_, to)

    def remove(self, item):
        self.overlays.remove(item)
        self.__initProps.pop(item, None)

    def clear(self):
        del self[:]


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
