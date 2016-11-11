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

  - Must be supported by the :mod:`~fsleyes.gl` package .. ok, this is a
    pretty big requirement .. See the :mod:`.globject` and the
    :data:`.displaycontext.OVERLAY_TYPES` documentation for details on how to
    get started with this one.


One further requirement is imposed on overlay types which derive from the
:class:`.Image` class:

 -  The ``__init__`` method fo ll sub-classes of the ``Image`` class must
    accept the ``loadData``, ``calcRange``, ``indexed`` , and ``threaded``
    parameters, and pass them through to the base class ``__init__`` method.
 

Currently (``fsleyes`` version |version|) the only overlay types in existence
(and able to be rendered) are:

.. autosummary::
   :nosignatures:

   ~fsl.data.image.Image
   ~fsl.data.featimage.FEATImage
   ~fsl.data.melodicimage.MelodicImage
   ~fsl.data.dtifit.DTIFitTensor
   ~fsl.data.model.Model


This module also provides a few convenience fnctions:


.. autosummary::
   :nosignatures:

   guessDataSourceType
   findFEATImage
"""

import logging
import os.path as op

import props

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


class OverlayList(props.HasProperties):
    """Class representing a collection of overlays to be displayed together.

    Contains a :class:`props.properties_types.List` property called
    :attr:`overlays`, containing overlay objects (e.g. :class:`.Image`
    or :class:`.Model`objects). Listeners can be registered on the
    ``overlays`` property, so they are notified when the overlay list changes.

    An :class:`OverlayList` object has a few wrapper methods around the
    :attr:`overlays` property, allowing the :class:`OverlayList` to be used as
    if it were a list itself.

    The :mod:`.loadoverlay` module contains some convenience functions for
    loading and adding overlays.
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


    def initOverlayType(self, overlay):
        """Returns the initial type for the given ``overlay``, if it was
        specified via the :meth:`append` or :meth:`insert` methods. Returns
        ``None`` otherwise.
        """
        return self.__initOverlayType.get(overlay, None)


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

        :arg base: The :class:`Image` instance upon which this ``ProxyImage``
                   is based.
        """

        if not isinstance(base, fslimage.Image):
            raise ValueError('Base image must be an Image instance')

        self.__base = base

        kwargs['header'] = base.nibImage.get_header()

        fslimage.Image.__init__(self, base[:], *args, **kwargs)
        

    def getBase(self):
        """Returns the base :class:`Image` of this ``ProxyImage``. """
        return self.__base
    

def guessDataSourceType(path):
    """A convenience function which, given the name of a file or directory,
    figures out a suitable overlay type.

    Returns a tuple containing two values - a type which should be able to
    load the path, and the path itself, possibly adjusted. If the type
    is unrecognised, the first tuple value will be ``None``.
    """

    import fsl.data.model           as fslmodel
    import fsl.data.featimage       as featimage
    import fsl.data.melodicimage    as melimage
    import fsl.data.dtifit          as dtifit
    import fsl.data.melodicanalysis as melanalysis
    import fsl.data.featanalysis    as featanalysis

    path = op.abspath(path)

    # VTK files are easy
    if path.endswith('.vtk'):
        return fslmodel.Model, path

    # Analysis directory?
    if op.isdir(path):
        if melanalysis.isMelodicDir(path):
            return melimage.MelodicImage, path

        elif featanalysis.isFEATDir(path):
            return featimage.FEATImage, path

        elif dtifit.isDTIFitPath(path):
            return dtifit.DTIFitTensor, path

    # Assume it's a NIFTI image
    try:                       path = fslimage.addExt(path, mustExist=True)
    except fslimage.PathError: return None, path

    if   melanalysis .isMelodicImage(path): return melimage.MelodicImage, path
    elif featanalysis.isFEATImage(   path): return featimage.FEATImage,   path
    else:                                   return fslimage.Image,        path
        
    # Otherwise, I don't
    # know what to do
    return None, path


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
