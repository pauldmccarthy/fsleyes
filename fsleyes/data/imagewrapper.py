#!/usr/bin/env python
#
# imagewrapper.py - The ImageWrapper class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImageWrapper` class, which can be used
to manage data access to ``nibabel`` NIFTI images. The ``ImageWrapper`` class
is intended to be used with large 4D compresed NIFTI images, where loading
data from disk is expensive.


Terminology
-----------


There are some confusing terms used in this module, so it may be useful to
get their definitions straight:

  - *Coverage*:    The portion of an image that has been covered in the data
                   range calculation. The ``ImageWrapper`` keeps track of
                   the coverage for individual volumes within a 4D image (or
                   slices in a 3D image).

  - *Slice*:       Portion of the image data which is being accessed. A slice
                   comprises either a tuple of ``slice`` objects (or integers),
                   or a sequence of ``(low, high)`` tuples, specifying the
                   index range into each image dimension that is covered by
                   the slice.

  - *Expansion*:   A sequence of ``(low, high)`` tuples, specifying an
                   index range into each image dimension, that is used to
                   *expand* the *coverage* of an image, based on a given set
                   of *slices*.

  - *Fancy slice*: Any object which is used to slice an array, and is not
                   an ``int``, ``slice``, or ``Ellipsis``, or sequence of
                   these.
"""


import                    logging
import                    collections
import collections.abc as abc
import itertools       as it
import contextlib      as ctxlib

from typing import Tuple

import numpy           as np
import nibabel         as nib

import fsl.data.image        as fslimage
import fsl.utils.notifier    as notifier
import fsl.utils.naninfrange as nir
import fsl.utils.idle        as idle


log = logging.getLogger(__name__)


class ImageWrapper(fslimage.DataManager, notifier.Notifier):
    """The ``ImageWrapper`` class is a convenience class which manages data
    access to ``nibabel`` NIFTI images. The ``ImageWrapper`` class can be
    used to incrementally update the known image data range, as more image
    data is read in.


    *Data access*


    The ``ImageWrapper`` can be indexed with basic ``numpy``-like multi-
    dimensional array slicing (with step sizes of 1)

    See https://docs.scipy.org/doc/numpy/reference/arrays.indexing.html for
    more details on numpy indexing.


    *In memory or on disk?*

    The image data will be kept on disk, and accessed through the
    ``nibabel.Nifti1Image.dataobj`` array proxy, unless the image data is
    modified via :meth:`__setitem__`. If the image data is modified, it
    is loaded into memory.

    If any of these conditions do not hold, the image data will be loaded into
    memory and accessed directly.


    *Data range*


    In order to avoid the computational overhead of calculating the image data
    range (its minimum/maximum values) when an image is first loaded in, an
    ``ImageWrapper`` incrementally updates the known image data range as data
    is accessed. The ``ImageWrapper`` keeps track of the image data *coverage*,
    the portion of the image which has already been considered in the data
    range calculation. When data from a region of the image not in the coverage
    is accessed, the coverage is expanded to include this region. The coverage
    is always expanded in a rectilinear manner, i.e. the coverage is always
    rectangular for a 2D image, or cuboid for a 3D image.


    For a 4D image, the ``ImageWrapper`` internally maintains a separate
    coverage and known data range for each 3D volume within the image. For a 3D
    image, separate coverages and data ranges are stored for each 2D slice.


    The ``ImageWrapper`` implements the :class:`.Notifier` interface.
    Listeners can register to be notified whenever the known image data range
    is updated. The data range can be accessed via the :attr:`dataRange`
    property.


    The ``ImageWrapper`` class uses the following functions (also defined in
    this module) to keep track of the portion of the image that has currently
    been included in the data range calculation:

    .. autosummary::
       :nosignatures:

       sliceObjToSliceTuple
       sliceTupleToSliceObj
       sliceCovered
       calcExpansion
       adjustCoverage
    """


    def __init__(self, threaded : bool = False):
        """Create an ``ImageWrapper``. The image must be specified by a
        subsequent call to :meth:`setImage`.

        :arg threaded:  If ``True``, the data range is updated on a
                        :class:`.TaskThread`. Otherwise (the default), the
                        data range is updated directly on reads/writes.
        """

        self.__image      = None
        self.__taskThread = None

        # Information about image dimensionality
        # is initialised in the setImage method.
        self.__numRealDims = None
        self.__numPadDims  = None

        # The internal state is stored in these
        # attributes - they're initialised in the
        # reset method.
        self.__range     = None
        self.__coverage  = None
        self.__volRanges = None
        self.__covered   = False

        # The data is kept on disk and accessed
        # through nibimg.dataobj , unless/untill
        # a request to modify the data is made
        # through __setitem__, at which point it
        # is loaded into memory.
        self.__data = None

        if threaded:
            self.__taskThread        = idle.TaskThread()
            self.__taskThread.daemon = True
            self.__taskThread.start()


    def setImage(self,
                 image     : nib.Nifti1Image,
                 dataRange : Tuple[float, float] = None):
        """Set the image being wrapped by this ``ImageWrapper``.

        :arg image:     A ``nibabel.Nifti1Image`` or ``nibabel.Nifti2Image``.
        :arg dataRange: A tuple containing the initial ``(min, max)``  data
                        range to use. See the :meth:`reset` method for
                        important information about this parameter.
        """
        self.__image = image

        # Save the number of 'real' dimensions,
        # that is the number of dimensions minus
        # any trailing dimensions of length 1
        self.__numRealDims = len(image.shape)
        for d in reversed(image.shape):
            if d == 1: self.__numRealDims -= 1
            else:      break

        # Degenerate case - less
        # than three real dimensions
        if self.__numRealDims < 3:
            self.__numRealDims = min(3, len(image.shape))

        # And save the number of
        # 'padding' dimensions too.
        self.__numPadDims = len(image.shape) - self.__numRealDims

        self.reset(dataRange)


    def copy(self, image : nib.Nifti1Image):
        """Return a new ``ImageWrapper`` configued in the same manner as
        this ``ImageWrapper``, for managing the new ``image``.

        :arg image:     A ``nibabel.Nifti1Image`` or ``nibabel.Nifti2Image``.
        """
        new = ImageWrapper(self.__taskThread is not None)
        new.setImage(image, self.__range)
        return new


    def __del__(self):
        """If this ``ImageWrapper`` was created with ``threaded=True``,
        the :class:`.TaskThread` is stopped.
        """
        self.__image = None
        self.__data  = None
        if self.__taskThread is not None:
            self.__taskThread.stop()
            self.__taskThread = None


    def getTaskThread(self):
        """If this ``ImageWrapper`` was created with ``threaded=True``,
        this method returns the ``TaskThread`` that is used for running
        data range calculation tasks. Otherwise, this method returns
        ``False``.
        """
        return self.__taskThread


    @ctxlib.contextmanager
    def unthreaded(self):
        """Context manager which temporarily disables threading. """
        try:
            tt                = self.__taskThread
            self.__taskThread = None
            yield
        finally:
            self.__taskThread = tt


    def reset(self, dataRange=None):
        """Reset the internal state and known data range of this
        ``ImageWrapper``.


        :arg dataRange: A tuple containing the initial ``(min, max)``  data
                        range to use.


        .. note:: The ``dataRange`` parameter is intended for situations where
                  the image data range is known in advance (e.g. it was
                  calculated earlier, and the image is being re-loaded). If a
                  ``dataRange`` is passed in, it will *not* be overwritten by
                  any range calculated from the data, unless the calculated
                  data range is wider than the provided ``dataRange``.
        """

        if dataRange is None:
            dataRange = None, None

        image =             self.__image
        ndims =             self.__numRealDims - 1
        nvols = image.shape[self.__numRealDims - 1]

        # The current known image data range. This
        # gets updated as more image data gets read.
        self.__range = dataRange

        # The coverage array is used to keep track of
        # the portions of the image which have been
        # considered in the data range calculation.
        # We use this coverage to avoid unnecessarily
        # re-calculating the data range on the same
        # part of the image.
        #
        # First of all, we're going to store a separate
        # 'coverage' for each 2D slice in the 3D image
        # (or 3D volume for 4D images). This effectively
        # means a seaprate coverage for each index in the
        # last 'real' image dimension (see above).
        #
        # For each slice/volume, the the coverage is
        # stored as sequences of (low, high) indices, one
        # for each dimension in the slice/volume (e.g.
        # row/column for a slice, or row/column/depth
        # for a volume).
        #
        # All of these indices are stored in a numpy array:
        #   - first dimension:  low/high index
        #   - second dimension: image dimension
        #   - third dimension:  slice/volume index
        self.__coverage = np.zeros((2, ndims, nvols), dtype=np.float32)

        # Internally, we calculate and store the
        # data range for each volume/slice/vector
        #
        # We use nan as a placeholder, so the
        # dtype must be non-integral. The
        # len(dtype) check takes into account
        # structured data (e.g. RGB)
        dtype = self.__image.get_data_dtype()
        if np.issubdtype(dtype, np.integer) or len(dtype) > 0:
            dtype = np.float32

        self.__volRanges    = np.zeros((nvols, 2), dtype=dtype)
        self.__coverage[ :] = np.nan
        self.__volRanges[:] = np.nan

        # This flag is set to true if/when the
        # full image data range becomes known
        # (i.e. when all data has been loaded in).
        self.__covered = False


    @property
    def dataRange(self):
        """Returns the currently known data range as a tuple of ``(min, max)``
        values.
        """
        # If no image data has been accessed, we
        # default to whatever is stored in the
        # header (which may or may not contain
        # useful values).
        low, high = self.__range
        hdr       = self.__image.header

        if low  is None: low  = float(hdr['cal_min'])
        if high is None: high = float(hdr['cal_max'])

        return low, high


    @property
    def covered(self):
        """Returns ``True`` if this ``ImageWrapper`` has read the entire
        image data, ``False`` otherwise.
        """
        return self.__covered


    def coverage(self, vol):
        """Returns the current image data coverage for the specified volume
        (for a 4D image, slice for a 3D image, or vector for a 2D images).

        :arg vol: Index of the volume/slice/vector to return the coverage
                  for.

        :returns: The coverage for the specified volume, as a ``numpy``
                  array of shape ``(nd, 2)``, where ``nd`` is the number
                  of dimensions in the volume.

        .. note:: If the specified volume is not covered, the returned array
                  will contain ``np.nan`` values.
        """
        return np.array(self.__coverage[..., vol])


    def __getData(self, sliceobj, isTuple=False):
        """Retrieves the image data at the location specified by ``sliceobj``.

        :arg sliceobj: Something which can be used to slice an array, or
                       a sequence of (low, high) index pairs.

        :arg isTuple:  Set to ``True`` if ``sliceobj`` is a sequence of
                       (low, high) index pairs.
        """

        if isTuple:
            sliceobj = sliceTupleToSliceObj(sliceobj)

        # If the image has not been loaded
        # into memory, we can use the nibabel
        # ArrayProxy. Otheriwse if it is in
        # memory, we can access it directly.
        #
        # Note also that if the caller has
        # given us a 'fancy' slice object (a
        # boolean numpy array), but the image
        # data is not in memory, we can't access
        # the data, as the nibabel ArrayProxy
        # (the dataobj attribute) cannot handle
        # fancy indexing. In this case an error
        # will be raised.
        if self.__data is not None: return self.__data[         sliceobj]
        else:                       return self.__image.dataobj[sliceobj]


    def __imageIsCovered(self):
        """Returns ``True`` if all portions of the image have been covered
        in the data range calculation, ``False`` otherwise.
        """

        shape  = self.__image.shape
        slices = [[0, s] for s in shape]
        return sliceCovered(slices, self.__coverage)


    def __expandCoverage(self, slices):
        """Expands the current image data range and coverage to encompass the
        given ``slices``.
        """

        _, expansions = calcExpansion(slices, self.__coverage)
        expansions    = collapseExpansions(expansions, self.__numRealDims - 1)

        log.debug('Updating image data range [slice: %s] '
                  '(current range: [%s, %s]; '
                  'number of expansions: %s; '
                  'current coverage: %s; '
                  'volume ranges: %s)',
                  slices,
                  self.__range[0],
                  self.__range[1],
                  len(expansions),
                  self.__coverage,
                  self.__volRanges)

        # As we access the data for each expansions,
        # we want it to have the same dimensionality
        # as the full image, so we can access data
        # for each volume in the image separately.
        # So we squeeze out the padding dimensions,
        # but not the volume dimension.
        squeezeDims = tuple(range(self.__numRealDims,
                                  self.__numRealDims + self.__numPadDims))

        # The calcExpansion function splits up the
        # expansions on volumes - here we calculate
        # the min/max per volume/expansion, and
        # iteratively update the stored per-volume
        # coverage and data range.
        for exp in expansions:

            data     = self.__getData(exp, isTuple=True)
            data     = data.squeeze(squeezeDims)
            vlo, vhi = exp[self.__numRealDims - 1]

            for vi, vol in enumerate(range(vlo, vhi)):

                oldvlo, oldvhi = self.__volRanges[vol, :]
                voldata        = data[..., vi]
                newvlo, newvhi = nir.naninfrange(voldata)

                if np.isnan(newvlo) or \
                   (not np.isnan(oldvlo) and oldvlo < newvlo):
                    newvlo = oldvlo
                if np.isnan(newvhi) or \
                   (not np.isnan(oldvhi) and oldvhi > newvhi):
                    newvhi = oldvhi

                # Update the stored range and
                # coverage for each volume
                self.__volRanges[vol, :]  = newvlo, newvhi
                self.__coverage[..., vol] = adjustCoverage(
                    self.__coverage[..., vol], exp)

        # Calculate the new known data
        # range over the entire image
        # (i.e. over all volumes).
        newmin, newmax = nir.naninfrange(self.__volRanges)

        oldmin, oldmax = self.__range
        self.__range   = (newmin, newmax)
        self.__covered = self.__imageIsCovered()

        if any((oldmin is None, oldmax is None)) or \
           not np.all(np.isclose([oldmin, oldmax], [newmin, newmax])):
            log.debug('Image range changed: [%s, %s] -> [%s, %s]',
                      oldmin,
                      oldmax,
                      newmin,
                      newmax)
            self.notify()


    def __updateDataRangeOnRead(self, slices, data):
        """Called by :meth:`__getitem__`. Calculates the minimum/maximum
        values of the given data (which has been extracted from the portion of
        the image specified by ``slices``), and updates the known data range
        of the image.

        :arg slices: A tuple of tuples, each tuple being a ``(low, high)``
                     index pair, one for each dimension in the image.

        :arg data:   The image data at the given ``slices`` (as a ``numpy``
                     array).
        """

        # TODO You could do something with
        #      the provided data to avoid
        #      reading it in again.

        if self.__taskThread is None:
            self.__expandCoverage(slices)
        else:
            name = f'{id(self)}_read_{slices}'
            if not self.__taskThread.isQueued(name):
                self.__taskThread.enqueue(
                    self.__expandCoverage, slices, taskName=name)


    def __updateDataRangeOnWrite(self, slices, data):
        """Called by :meth:`__setitem__`. Assumes that the image data has
        been changed (the data at ``slices`` has been replaced with ``data``.
        Updates the image data coverage, and known data range accordingly.

        :arg slices: A tuple of tuples, each tuple being a ``(low, high)``
                     index pair, one for each dimension in the image.

        :arg data:   The image data at the given ``slices`` (as a ``numpy``
                     array).
        """

        overlap = sliceOverlap(slices, self.__coverage)

        # If there's no overlap between the written
        # area and the current coverage, then it's
        # easy - we just expand the coverage to
        # include the newly written area.
        #
        # But if there is overlap between the written
        # area and the current coverage, things are
        # more complicated, because the portion of
        # the image that has been written over may
        # have contained the currently known data
        # minimum/maximum. We have no way of knowing
        # this, so we have to reset the coverage (on
        # the affected volumes), and recalculate the
        # data range.
        if overlap in (OVERLAP_SOME, OVERLAP_ALL):

            # TODO Could you store the location of the
            #      data minimum/maximum (in each volume),
            #      so you know whether resetting the
            #      coverage is necessary?
            lowVol, highVol = slices[self.__numRealDims - 1]

            # We create a single slice which
            # encompasses the given slice, and
            # all existing coverages for each
            # volume in the given slice. The
            # data range for this slice will
            # be recalculated.
            slices = adjustCoverage(self.__coverage[:, :, lowVol], slices)
            for vol in range(lowVol + 1, highVol):
                slices = adjustCoverage(slices, self.__coverage[:, :, vol].T)

            slices = np.array(slices.T, dtype=np.uint32)
            slices = tuple(it.chain(map(tuple, slices), [(lowVol, highVol)]))

            log.debug('Image data written - clearing known data '
                      'range on volumes %s - %s (write slice: %s; '
                      'coverage: %s; volRanges: %s)',
                      lowVol,
                      highVol,
                      slices,
                      self.__coverage[:, :, lowVol:highVol],
                      self.__volRanges[lowVol:highVol, :])

            for vol in range(lowVol, highVol):
                self.__coverage[:, :, vol]    = np.nan
                self.__volRanges[     vol, :] = np.nan


        if self.__taskThread is None:
            self.__expandCoverage(slices)
        else:
            name = f'{id(self)}_write_{slices}'
            if not self.__taskThread.isQueued(name):
                self.__taskThread.enqueue(
                    self.__expandCoverage, slices, taskName=name)


    def __getitem__(self, sliceobj):
        """Returns the image data for the given ``sliceobj``, and updates
        the known image data range if necessary.

        :arg sliceobj: Something which can slice the image data.
        """

        log.debug('Getting image data: %s', sliceobj)

        shape    = self.__image.shape
        sliceobj = fslimage.canonicalSliceObj(sliceobj, shape)
        data     = self.__getData(sliceobj)

        # Update data range for the
        # data that we just read in
        if not self.__covered:

            slices = sliceObjToSliceTuple(sliceobj, shape)

            if not sliceCovered(slices, self.__coverage):
                self.__updateDataRangeOnRead(slices, data)

        return data


    def __setitem__(self, sliceobj, values):
        """Writes the given ``values`` to the image at the given ``sliceobj``.

        :arg sliceobj: Something which can be used to slice the array.
        :arg values:   Data to write to the image.

        .. note:: Modifying image data will cause the entire image to be
                  loaded into memory.
        """

        shape  = self.__image.shape
        slices = sliceObjToSliceTuple(sliceobj, shape)

        # The image data has to be in memory
        # for the data to be changed.
        if self.__data is None:
            self.__data = np.asanyarray(self.__image.dataobj)

        self.__data[sliceobj] = values
        self.__updateDataRangeOnWrite(slices, values)


def sliceObjToSliceTuple(sliceobj, shape):
    """Turns a sequence of slice objects into a tuple of (low, high) index
    pairs, one pair for each dimension in the given shape

    :arg sliceobj: Something which can be used to slice an array of shape
                   ``shape``.

    :arg shape:    Shape of the array being sliced.
    """

    if fslimage.isValidFancySliceObj(sliceobj, shape):
        return tuple((0, s) for s in shape)

    indices = []

    # The sliceobj could be a single sliceobj
    # or integer, instead of a tuple
    if not isinstance(sliceobj, abc.Sequence):
        sliceobj = [sliceobj]

    # Turn e.g. array[6] into array[6, :, :]
    if len(sliceobj) != len(shape):
        missing  = len(shape) - len(sliceobj)
        sliceobj = list(sliceobj) + [slice(None) for i in range(missing)]

    for dim, s in enumerate(sliceobj):

        # each element in the slices tuple should
        # be a slice object or an integer
        if isinstance(s, slice): i = [s.start, s.stop]
        else:                    i = [s,       s + 1]

        if i[0] is None: i[0] = 0
        if i[1] is None: i[1] = shape[dim]

        indices.append(tuple(i))

    return tuple(indices)


def sliceTupleToSliceObj(slices):
    """Turns a sequence of (low, high) index pairs into a tuple of array
    ``slice`` objects.

    :arg slices: A sequence of (low, high) index pairs.
    """

    sliceobj = []

    for lo, hi in slices:
        sliceobj.append(slice(lo, hi, 1))

    return tuple(sliceobj)


def adjustCoverage(oldCoverage, slices):
    """Adjusts/expands the given ``oldCoverage`` so that it covers the
    given set of ``slices``.

    :arg oldCoverage: A ``numpy`` array of shape ``(2, n)`` containing
                      the (low, high) index pairs for ``n`` dimensions of
                      a single slice/volume in the image.

    :arg slices:      A sequence of (low, high) index pairs. If ``slices``
                      contains more dimensions than are specified in
                      ``oldCoverage``, the trailing dimensions are ignored.

    :return: A ``numpy`` array containing the adjusted/expanded coverage.
    """

    newCoverage = np.zeros(oldCoverage.shape, dtype=oldCoverage.dtype)

    for dim in range(oldCoverage.shape[1]):

        low,      high      = slices[        dim]
        lowCover, highCover = oldCoverage[:, dim]

        if np.isnan(lowCover)  or low  < lowCover:  lowCover  = low
        if np.isnan(highCover) or high > highCover: highCover = high

        newCoverage[:, dim] = lowCover, highCover

    return newCoverage


OVERLAP_ALL = 0
"""Indicates that the slice is wholly contained within the coverage.  This is
a return code for the :func:`sliceOverlap` function.
"""


OVERLAP_SOME = 1
"""Indicates that the slice partially overlaps with the coverage. This is a
return code for the :func:`sliceOverlap` function.
"""


OVERLAP_NONE = 2
"""Indicates that the slice does not overlap with the coverage. This is a
return code for the :func:`sliceOverlap` function.
"""


def sliceOverlap(slices, coverage):
    """Determines whether the given ``slices`` overlap with the given
    ``coverage``.

    :arg slices:    A sequence of (low, high) index pairs, assumed to cover
                    all image dimensions.
    :arg coverage:  A ``numpy`` array of shape ``(2, nd, nv)`` (where ``nd``
                    is the number of dimensions being covered, and ``nv`` is
                    the number of volumes (or vectors/slices) in the image,
                    which contains the (low, high) index pairs describing
                    the current image coverage.

    :returns: One of the following codes:

              .. autosummary::

              OVERLAP_ALL
              OVERLAP_SOME
              OVERLAP_NONE
    """

    numDims         = coverage.shape[1]
    lowVol, highVol = slices[numDims]

    # Overlap state is calculated for each volume
    overlapStates = np.zeros(highVol - lowVol)

    for i, vol in enumerate(range(lowVol, highVol)):

        state = OVERLAP_ALL

        for dim in range(numDims):

            lowCover, highCover = coverage[:, dim, vol]
            lowSlice, highSlice = slices[     dim]

            # No coverage
            if np.isnan(lowCover) or np.isnan(highCover):
                state = OVERLAP_NONE
                break

            # The slice is contained within the
            # coverage on this dimension - check
            # the other dimensions.
            if lowSlice >= lowCover and highSlice <= highCover:
                continue

            # The slice does not overlap at all
            # with the coverage on this dimension
            # (or at all). No overlap - no need
            # to check the other dimensions.
            if lowSlice >= highCover or highSlice <= lowCover:
                state = OVERLAP_NONE
                break

            # There is some overlap between the
            # slice and coverage on this dimension
            # - check the other dimensions.
            state = OVERLAP_SOME

        overlapStates[i] = state

    if   np.any(overlapStates == OVERLAP_SOME): return OVERLAP_SOME
    elif np.all(overlapStates == OVERLAP_NONE): return OVERLAP_NONE
    elif np.all(overlapStates == OVERLAP_ALL):  return OVERLAP_ALL


def sliceCovered(slices, coverage):
    """Returns ``True`` if the portion of the image data calculated by
    the given ``slices` has already been calculated, ``False`` otherwise.

    :arg slices:    A sequence of (low, high) index pairs, assumed to cover
                    all image dimensions.
    :arg coverage:  A ``numpy`` array of shape ``(2, nd, nv)`` (where ``nd``
                    is the number of dimensions being covered, and ``nv`` is
                    the number of volumes (or vectors/slices) in the image,
                    which contains the (low, high) index pairs describing
                    the current image coverage.
    """

    numDims         = coverage.shape[1]
    lowVol, highVol = slices[numDims]

    for vol in range(lowVol, highVol):

        for dim in range(numDims):

            lowCover, highCover = coverage[:, dim, vol]
            lowSlice, highSlice = slices[     dim]

            if np.isnan(lowCover) or np.isnan(highCover):
                return False

            if lowSlice  < lowCover:  return False
            if highSlice > highCover: return False

    return True


def calcExpansion(slices, coverage):
    """Calculates a series of *expansion* slices, which can be used to expand
    the given ``coverage`` so that it includes the given ``slices``.

    :arg slices:   Slices that the coverage needs to be expanded to cover.
    :arg coverage: Current image coverage.

    :returns: A list of volume indices, and a corresponding list of
              expansions.
    """

    numDims         = coverage.shape[1]
    padDims         = len(slices) - numDims - 1
    lowVol, highVol = slices[numDims]

    expansions = []
    volumes    = []

    # Finish off an expansion by
    # adding indices for the vector/
    # slice/volume dimension, and for
    # 'padding' dimensions of size 1.
    def finishExpansion(exp, vol):
        exp.append((vol, vol + 1))
        for _ in range(padDims):
            exp.append((0, 1))
        return exp

    for vol in range(lowVol, highVol):

        # No coverage of this volume -
        # we need the whole slice.
        if np.any(np.isnan(coverage[:, :, vol])):
            exp = [(s[0], s[1]) for s in slices[:numDims]]
            exp = finishExpansion(exp, vol)
            volumes   .append(vol)
            expansions.append(exp)
            continue

        # First we'll figure out the index
        # range for each dimension that
        # needs to be added to the coverage.
        # We build a list of required ranges,
        # where each entry is a tuple
        # containing:
        #   (dimension, lowIndex, highIndex)
        reqRanges = []

        for dim in range(numDims):

            lowCover, highCover = coverage[:, dim, vol]
            lowSlice, highSlice = slices[     dim]

            # The slice covers a region
            # below the current coverage
            if lowCover - lowSlice > 0:
                reqRanges.append((dim, int(lowSlice), int(lowCover)))

            # The slice covers a region
            # above the current coverage
            if highCover - highSlice < 0:
                reqRanges.append((dim, int(highCover), int(highSlice)))

        # Now we generate an expansion for
        # each of those ranges.
        volExpansions = []
        for dimx, xlo, xhi in reqRanges:

            expansion = [[np.nan, np.nan] for d in range(numDims)]

            # The expansion for each
            # dimension will span the range
            # for that dimension...
            expansion[dimx][0] = xlo
            expansion[dimx][1] = xhi

            # And will span the union of
            # the coverage, and calculated
            # range for every other dimension.
            for dimy, ylo, yhi in reqRanges:
                if dimy == dimx:
                    continue

                yLowCover, yHighCover = coverage[:, dimy, vol]
                expLow,    expHigh    = expansion[  dimy]

                if np.isnan(expLow):  expLow  = yLowCover
                if np.isnan(expHigh): expHigh = yHighCover

                expLow  = min((ylo, yLowCover,  expLow))
                expHigh = max((yhi, yHighCover, expHigh))

                expansion[dimy][0] = int(expLow)
                expansion[dimy][1] = int(expHigh)

            # If no range exists for any of the
            # other dimensions, the range for
            # all expansions will be the current
            # coverage
            for dimy in range(numDims):
                if dimy == dimx:
                    continue

                if np.any(np.isnan(expansion[dimy])):
                    expansion[dimy] = [int(c) for c in coverage[:, dimy, vol]]

            # Finish off this expansion
            expansion = finishExpansion(expansion, vol)

            volumes.      append(vol)
            volExpansions.append(expansion)

        # We do a final run through all pairs
        # of expansions, and adjust their
        # range if they overlap with each other.
        for exp1, exp2 in it.product(volExpansions, volExpansions):

            # Check each dimension
            for dimx in range(numDims):

                xlo1, xhi1 = exp1[dimx]
                xlo2, xhi2 = exp2[dimx]

                # These expansions do not
                # overlap with each other
                # on this dimension (or at
                # all). No need to check
                # the other dimensions.
                if xhi1 <= xlo2: break
                if xlo1 >= xhi2: break

                # These expansions overlap on
                # this dimension - check to see
                # if exp1 is wholly contained
                # within exp2 in all other
                # dimensions.
                adjustable = True

                for dimy in range(numDims):

                    if dimy == dimx:
                        continue

                    ylo1, yhi1 = exp1[dimy]
                    ylo2, yhi2 = exp2[dimy]

                    # Exp1 is not contained within
                    # exp2 on another dimension -
                    # we can't reduce the overlap.
                    if ylo1 < ylo2 or yhi1 > yhi2:
                        adjustable = False
                        break

                # The x dimension range of exp1
                # can be reduced, as it is covered
                # by exp2.
                if adjustable:
                    if   xlo1 <  xlo2 and xhi1 <= xhi2 and xhi1 > xlo2:
                        xhi1 = xlo2

                    elif xlo1 >= xlo2 and xhi1 >  xhi2 and xlo1 < xhi2:
                        xlo1 = xhi2

                    exp1[dimx] = xlo1, xhi1

        expansions.extend(volExpansions)

    return volumes, expansions


def collapseExpansions(expansions, numDims):
    """Scans through the given list of expansions (each assumed to pertain
    to a single 3D image), and combines any which cover the same
    image area, and cover adjacent volumes.

    :args expansions: A list of expansion slices - see :func:`calcExpansions`.

    :args numDims:    Number of dimensions covered by each expansion,
                      not including the volume dimension (i.e. 3 for a 4D
                      image).

    :returns: A list of expansions, with equivalent expansions that cover
              adjacent images collapsed down.

    .. note:: For one expansion ``exp`` in the ``expansions`` list, this
              function assumes that the range at ``exp[numDims]`` contains
              the image to which ``exp`` pertains (i.e.
              ``exp[numDims] == (vol, vol + 1)``).
    """
    if len(expansions) == 0:
        return []

    commonExpansions = collections.OrderedDict()
    expansions       = sorted(expansions)

    for exp in expansions:

        vol        = exp[numDims][0]
        exp        = tuple(exp[:numDims])
        commonExps = commonExpansions.get(exp, None)

        if commonExps is None:
            commonExps            = []
            commonExpansions[exp] = commonExps

        for i, (vlo, vhi) in enumerate(commonExps):

            if vol >= vlo and vol < vhi:
                break

            elif vol == vlo - 1:
                commonExps[i] = vol, vhi
                break
            elif vol == vhi:
                commonExps[i] = vlo, vol + 1
                break

        else:
            commonExps.append((vol, vol + 1))

    collapsed = []

    for exp, volRanges in commonExpansions.items():
        for vlo, vhi in volRanges:
            newExp = list(exp) + [(vlo, vhi)]
            collapsed.append(newExp)

    return collapsed
