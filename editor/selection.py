#!/usr/bin/env python
#
# selection.py - The Selection class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Selection` class, which represents a
selection of voxels in a 3D :class:`.Image`.
"""

import logging
import collections

import numpy                       as np
import scipy.ndimage.measurements  as ndimeas

import props


log = logging.getLogger(__name__)


class Selection(props.HasProperties):
    """The ``Selection`` class represents a selection of voxels in a 3D
    :class:`.Image`. The selection is stored as a ``numpy`` mask array,
    the same shape as the image. Methods are available to query and update
    the selection.

    
    Changes to a ``Selection`` can be made through *blocks*, which are 3D
    cuboid regions. The following methods allow a block to be
    selected/deselected, where the block is specified by a voxel coordinate,
    and a block size:

    .. autosummary::
       :nosignatures:

       selectBlock
       deselectBlock


    The following methods offer more fine grained control over selection
    blocks - with these methods, you pass in a block that you have created
    yourself, and an offset into the selection, specifying its location:

    .. autosummary::
       :nosignatures:

       setSelection
       replaceSelection
       addToSelection
       removeFromSelection

    
    A third approach to making a selection is provided by the
    :meth:`selectByValue` method, which allows a selection to be made
    in a manner similar to a *bucket fill* technique found in any image
    editor.

    A ``Selection`` object keeps track of the most recent change made
    through any of the above methods. The most recent change can be retrieved
    through the :meth:`getLastChange` method.


    Finally, the ``Selection`` class offers a few other methods for
    convenience:
    
    .. autosummary::
       :nosignatures:

       getSelectionSize
       clearSelection
       getBoundedSelection
       getIndices
       generateBlock
    """
    

    selection = props.Object()
    """The ``numpy`` mask array containing the current selection is stored
    in a :class:`props.Object`, so that listeners can register to be notified
    whenever it changes.

    .. warning:: Do not modify the selection directly through this attribute -
                 use the ``Selection`` instance methods
                 (e.g. :meth:`setSelection`) instead.  If you modify the
                 selection directly through this attribute, the
                 :meth:`getLastChange` method will break.
    """

    
    def __init__(self, image, display, selection=None):
        """Create a ``Selection`` instance.

        :arg image:     The :class:`.Image` instance  associated with this
                        ``Selection``.
        
        :arg display:   The :class:`.Display` instance for the ``image``.
        
        :arg selection: Selection array. If not provided, one is created.
                        Must be a ``numpy.uint8`` array with the same shape
                        as ``image``. This array is *not* copied.
        """
    
        self.__image              = image
        self.__display            = display
        self.__opts               = display.getDisplayOpts()
        self.__clear              = False
        self.__lastChangeOffset   = None
        self.__lastChangeOldBlock = None
        self.__lastChangeNewBlock = None

        if selection is None:
            selection = np.zeros(image.shape[:3], dtype=np.uint8)
            
        elif selection.shape != image.shape[:3] or \
             selection.dtype != np.uint8:
            raise ValueError('Incompatible selection array: {} ({})'.format(
                selection.shape, selection.dtype))

        self.selection = selection

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.memory('{}.del ({})'.format(type(self).__name__, id(self)))



    def selectBlock(self, voxel, blockSize, axes=(0, 1, 2)):
        """Selects the block (sets all voxels to 1) specified by the given
        voxel and block size.

        :arg voxel:     Starting voxel coordinates of the block.
        :arg blockSize: Size of the block along each axis.
        :arg axes:      Limit the block to the specified axes.

        """
        self.addToSelection(*self.generateBlock(voxel,
                                                blockSize,
                                                self.selection.shape,
                                                axes))

        
    def deselectBlock(self, voxel, blockSize, axes=(0, 1, 2)):
        """De-selects the block (sets all voxels to 0) specified by the given
        voxel and block size.

        :arg voxel:     Starting voxel coordinates of the block.
        :arg blockSize: Size of the block along each axis.
        :arg axes:      Limit the block to the specified axes.        
        """ 
        self.removeFromSelection(*self.generateBlock(voxel,
                                                     blockSize,
                                                     self.selection.shape,
                                                     axes)) 

        
    def setSelection(self, block, offset):
        """Copies the given ``block`` into the selection, starting at
        ``offset``.

        :arg block:  A ``numpy.uint8`` array containing a selection.
        :arg offset: Voxel coordinates specifying the block location.
        """
        self.__updateSelectionBlock(block, offset) 
        
    
    def replaceSelection(self, block, offset):
        """Clears the entire selection, then copies the given ``block``
        into the selection, starting at ``offset``.
        
        :arg block:  A ``numpy.uint8`` array containing a selection.
        :arg offset: Voxel coordinates specifying the block location. 
        """
        self.clearSelection()
        self.__updateSelectionBlock(block, offset)

        
    def addToSelection(self, block, offset):
        """Adds the selection (via a boolean OR operation) in the given
        ``block`` to the current selection, starting at ``offset``.

        :arg block:  A ``numpy.uint8`` array containing a selection.
        :arg offset: Voxel coordinates specifying the block location. 
        """
        existing = self.__getSelectionBlock(block.shape, offset)
        block    = np.logical_or(block, existing)
        
        self.__updateSelectionBlock(block, offset)


    def removeFromSelection(self, block, offset):
        """Clears all voxels in the selection where the values in ``block``
        are non-zero.
        
        :arg block:  A ``numpy.uint8`` array containing a selection.
        :arg offset: Voxel coordinates specifying the block location. 
        """
        existing             = self.__getSelectionBlock(block.shape, offset)
        existing[block != 0] = False
        self.__updateSelectionBlock(existing, offset)

    
    def getSelectionSize(self):
        """Returns the number of voxels that are currently selected. """
        return self.selection.sum()


    def getBoundedSelection(self):
        """Extracts the smallest region from the :attr:`selection` which
        contains all selected voxels.

        Returns a tuple containing the region, as a ``numpy.uint8`` array, and
        the coordinates specifying its location in the full :attr:`selection`
        array.
        """
        
        xs, ys, zs = np.where(self.selection > 0)

        if len(xs) == 0:
            return np.array([]).reshape(0, 0, 0), (0, 0, 0)

        xlo = xs.min()
        ylo = ys.min()
        zlo = zs.min()
        xhi = xs.max() + 1
        yhi = ys.max() + 1
        zhi = zs.max() + 1

        selection = self.selection[xlo:xhi, ylo:yhi, zlo:zhi]

        return selection, (xlo, ylo, zlo)

        
    def clearSelection(self):
        """Clears (sets to 0) the entire selection. """

        if self.__clear:
            return

        log.debug('Clearing selection ({})'.format(id(self)))
        
        self.__lastChangeOffset     = [0, 0, 0]
        self.__lastChangeOldBlock   = np.array(self.selection)
        self.selection[:]           = False
        self.__lastChangeNewBlock   = np.array(self.selection)

        self.__clear = True

        self.notify('selection')


    def getLastChange(self):
        """Returns the most recent change made to this ``Selection``.

        A tuple is returned, containing the following:

         - A ``numpy.uint8`` array containing the old block value
         - A ``numpy.uint8`` array containing the new block value
         - Voxel coordinates denoting the block location in the full
           :attr:`selection` array.
        """
        return (self.__lastChangeOldBlock,
                self.__lastChangeNewBlock,
                self.__lastChangeOffset)


    def getIndices(self, restrict=None):
        """Returns a :math:`N \\times 3` array which contains the
        coordinates of all voxels that are currently selected.

        If the ``restrict`` argument is not provided, the entire
        selection image is searched.

        :arg restrict: A ``slice`` object specifying a sub-set of the
                       full selection to consider.
        """

        if restrict is None: selection = self.selection
        else:                selection = self.selection[restrict]

        xs, ys, zs = np.where(selection)

        result = np.vstack((xs, ys, zs)).T

        if restrict is not None:

            for ax in range(3):
                off = restrict[ax].start
                if off is None: off = 0
                result[:, ax] += off

        return result

    
    def selectByValue(self,
                      seedLoc,
                      precision=None,
                      searchRadius=None,
                      local=False):
        """A *bucket fill* style selection routine. Given a seed location,
        finds all voxels which have a value similar to that of that location.
        The current selection is replaced with all voxels that were found.

        :arg seedLoc:      Voxel coordinates specifying the seed location

        :arg precision:    Voxels which have a value that is less than
                           ``precision`` from the seed location value will
                           be selected.

        :arg searchRadius: May be either a single value, or a sequence of
                           three values - one for each axis. If provided, the
                           search is limited to a sphere (in the voxel
                           coordinate system), centred on the seed location,
                           with the specified ``searchRadius`` (in voxels). If
                           not provided, the search will cover the entire
                           image space.

        :arg local:        If ``True``, a voxel will only be selected if it
                           is adjacent to an already selected voxel (using
                           8-neighbour connectivity).
        """

        if   len(self.__image.shape) == 3:
            data = self.__image.data
        elif len(self.__image.shape) == 4:
            data = self.__image.data[:, :, :, self.__opts.volume]
        else:
            raise RuntimeError('Only 3D and 4D images are currently supported')

        seedLoc = np.array(seedLoc)
        value   = data[seedLoc[0], seedLoc[1], seedLoc[2]]

        # Search radius may be either None, a scalar value,
        # or a sequence of three values (one for each axis).
        # If it is one of the first two options (None/scalar),
        # turn it into the third.
        if searchRadius is None:
            searchRadius = np.array([0, 0, 0])
        elif not isinstance(searchRadius, collections.Sequence):
            searchRadius = np.array([searchRadius] * 3)

        searchRadius = np.ceil(searchRadius)

        # No search radius - search
        # through the entire image
        if np.any(searchRadius == 0):
            searchSpace  = data
            searchOffset = (0, 0, 0)
            searchMask   = None

        # Search radius specified - limit
        # the search space, and specify
        # an ellipsoid mask with the
        # specified per-axis radii
        else:            
            ranges = [None, None, None]
            slices = [None, None, None]

            # Calculate xyz indices 
            # of the search space
            shape = data.shape
            for ax in range(3):

                idx = seedLoc[     ax]
                rad = searchRadius[ax]

                lo = idx - rad
                hi = idx + rad + 1

                if lo < 0:             lo = 0
                if hi > shape[ax] - 1: hi = shape[ax] - 1

                ranges[ax] = np.arange(lo, hi)
                slices[ax] = slice(    lo, hi)

            xs, ys, zs = np.meshgrid(*ranges, indexing='ij')

            # Centre those indices and the
            # seed location at (0, 0, 0)
            xs         -= seedLoc[0]
            ys         -= seedLoc[1]
            zs         -= seedLoc[2]
            seedLoc[0] -= ranges[0][0]
            seedLoc[1] -= ranges[1][0]
            seedLoc[2] -= ranges[2][0]

            # Distances from each point in the search
            # space to the centre of the search space
            dists = ((xs / searchRadius[0]) ** 2 +
                     (ys / searchRadius[1]) ** 2 +
                     (zs / searchRadius[2]) ** 2)

            # Extract the search space, and
            # create the ellipsoid mask
            searchSpace  = data[slices]
            searchOffset = (ranges[0][0], ranges[1][0], ranges[2][0])
            searchMask   = dists <= 1
            
        if precision is None: hits = searchSpace == value
        else:                 hits = np.abs(searchSpace - value) < precision

        if searchMask is not None:
            hits[~searchMask] = False

        # If local is true, limit the selection to
        # adjacent points with the same/similar value
        # (using scipy.ndimage.measurements.label)
        #
        # If local is not True, any same or similar 
        # values are part of the selection
        if local:
            hits, _   = ndimeas.label(hits)
            seedLabel = hits[seedLoc[0], seedLoc[1], seedLoc[2]]
            hits      = hits == seedLabel

        self.replaceSelection(hits, searchOffset)

    
    def transferSelection(self, destImg, destDisplay):
        """Re-samples the current selection into the destination image
        space. 

        Each ``Selection`` instance is in terms of a specific :class:`.Image`
        instance, which has a specific dimensionality. In order to apply
        a ``Selection`` which is in terms of one ``Image``, the selection
        array needs to be re-sampled.
        
        :arg destImg:     The :class:`.Image` that the selection is to be
                          transferred to.

        :arg destDisplay: The :class:`.Display` instance associated with
                          ``destImg``.

        :returns: a new ``numpy.uint8`` array, suitable for creating a new
                 ``Selection`` object for use with the given ``destImg``.
        """
        raise NotImplementedError('todo')
        

    def __updateSelectionBlock(self, block, offset):
        """Replaces the current selection at the specified ``offset`` with the
        given ``block``.

        The old values for the block are stored, and can be retrieved via the
        :meth:`getLastChange` method.

        :arg block:  A ``numpy.uint8`` array containing the new selection
                     values.

        :arg offset: Voxel coordinates specifying the location of ``block``.
        """

        block = np.array(block, dtype=np.uint8)

        if block.size == 0:
            return

        if offset is None:
            offset = (0, 0, 0)

        xlo, ylo, zlo = offset

        xhi = xlo + block.shape[0]
        yhi = ylo + block.shape[1]
        zhi = zlo + block.shape[2]

        self.__lastChangeOffset   = offset
        self.__lastChangeOldBlock = np.array(self.selection[xlo:xhi,
                                                            ylo:yhi,
                                                            zlo:zhi])
        self.__lastChangeNewBlock = np.array(block)

        log.debug('Updating selection ({}) block [{}:{}, {}:{}, {}:{}]'.format(
            id(self), xlo, xhi, ylo, yhi, zlo, zhi))

        self.selection[xlo:xhi, ylo:yhi, zlo:zhi] = block

        self.__clear = False
        
        self.notify('selection') 

        
    def __getSelectionBlock(self, size, offset):
        """Extracts a block from the selection image starting from the
        specified ``offset``, and of the specified ``size``.
        """
        
        xlo, ylo, zlo = offset
        xhi, yhi, zhi = size

        xhi = xlo + size[0]
        yhi = ylo + size[1]
        zhi = zlo + size[2]

        return np.array(self.selection[xlo:xhi, ylo:yhi, zlo:zhi])

    
    @classmethod
    def generateBlock(cls, voxel, blockSize, shape, axes=(0, 1, 2)):
        """Convenience method to generates a square/cube of ones, with the
        specified voxel at its centre, to fit in an image of the given shape.

        If the specified voxel would result in part of the block being located
        outside of the image shape, the block is truncated to fit inside
        the image bounds.

        :arg voxel:     Coordinates of the voxel around which the block is to
                        be centred.
        
        :arg blockSize: Desired width/height/depth
        
        :arg shape:     Shape of the image in which the block is to be located.
        
        :arg axes:      Axes along which the block is to be located.

        :returns:       A tuple containing the block - a ``numpy.uint8`` array
                        filled with ones, and an offset specifying the block
                        location within an image of the specified ``shape``.
        """

        if blockSize == 1:
            return np.array([True], dtype=np.uint8).reshape(1, 1, 1), voxel

        blockLo = [v - int(np.floor((blockSize - 1) / 2.0)) for v in voxel]
        blockHi = [v + int(np.ceil(( blockSize - 1) / 2.0)) for v in voxel]

        for i in range(3):
            if i not in axes:
                blockLo[i] = voxel[i]
                blockHi[i] = voxel[i] + 1
            else:
                blockLo[i] = max(blockLo[i],     0)
                blockHi[i] = min(blockHi[i] + 1, shape[i])

            if blockHi[i] <= blockLo[i]:
                return np.ones((0, 0, 0), dtype=np.uint8), voxel

        block = np.ones((blockHi[0] - blockLo[0],
                         blockHi[1] - blockLo[1],
                         blockHi[2] - blockLo[2]), dtype=np.uint8)

        offset = blockLo

        return block, offset
