#!/usr/bin/env python
#
# test_imagewrapper.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>


from __future__ import print_function

import              collections
import              random
import itertools as it
import numpy     as np
import nibabel   as nib
import              pytest

import fsl.utils.naninfrange     as nir
import fsleyes.data.imagewrapper as imagewrap


real_print = print
def print(*args, **kwargs):
    pass


def setup_module():
    pass

def teardown_module():
    pass


def random_voxels(shape, nvoxels=1):
    randVoxels = np.vstack(
        [np.random.randint(0, s, nvoxels) for s in shape[:3]]).T

    if nvoxels == 1:
        return randVoxels[0]
    else:
        return randVoxels


def random_coverage(shape, vol_limit=None):

    ndims = len(shape) - 1
    nvols = shape[-1]

    # Generate a random coverage.
    # We use the same coverage for
    # each vector/slice/volume, so
    # are not fully testing the function.
    coverage = np.zeros((2, ndims, nvols), dtype=np.float32)

    for dim in range(ndims):
        dsize = shape[dim]

        # Random low/high indices for each dimension.
        low  = np.random.randint(0, dsize)

        # We have to make sure that the coverage is not
        # complete, as some of the tests will fail if
        # the coverage is complete.
        if low == 0: high = np.random.randint(low + 1, dsize)
        else:        high = np.random.randint(low + 1, dsize + 1)

        coverage[0, dim, :] = low
        coverage[1, dim, :] = high

    if vol_limit is not None:
        coverage[:, :, vol_limit:] = np.nan

    return coverage


def random_slices(coverage, shape, mode):

    shape    = np.array(shape)
    ndims    = len(shape) - 1
    nvols    = shape[-1]
    slices   = np.zeros((2, len(shape)))
    origMode = mode

    if coverage is None:
        coverage          = np.zeros((2, ndims, nvols), dtype=np.float32)
        coverage[0, :, :] = 0
        coverage[1, :, :] = shape[:-1].reshape(ndims, 1).repeat(nvols, 1)

    # If we're generating an 'out' slice (i.e.
    # a slice which is not covered by the coverage),
    # then only one dimension needs to be out. The
    # other dimensions don't matter.
    if mode == 'out':
        dimModes = [random.choice(('in', 'out', 'overlap')) for i in range(ndims)]
        if not any([m == 'out' for m in dimModes]):
            dimModes[random.randint(0, ndims - 1)] = 'out'

    for dim, size in enumerate(shape):

        # Volumes
        if dim == ndims:
            lowCover  = np.random.randint(0,            nvols)
            highCover = np.random.randint(lowCover + 1, nvols + 1)

            slices[:, dim] = lowCover, highCover
            continue

        if origMode == 'out':
            mode = dimModes[dim]

        # Assuming that coverage is same for each volume
        lowCover  = coverage[0, dim, 0]
        highCover = coverage[1, dim, 0]

        if (np.isnan(lowCover) or np.isnan(highCover)) and mode in ('in', 'overlap'):
            if origMode == 'out':
                mode = 'out'
            else:
                raise RuntimeError('Can\'t generate in/overlapping slices on an empty coverage')

        # Generate some slices that will
        # be contained within the coverage
        if mode == 'in':
            lowSlice  = np.random.randint(lowCover,     highCover)
            highSlice = np.random.randint(lowSlice + 1, highCover + 1)

        # Generate some indices which will
        # randomly overlap with the coverage
        # (if it is possible to do so)
        elif mode == 'overlap':

            if highCover == size: lowSlice = np.random.randint(0, lowCover)
            else:                 lowSlice = np.random.randint(0, highCover)

            if lowSlice < lowCover: highSlice = np.random.randint(lowCover  + 1, size + 1)
            else:                   highSlice = np.random.randint(highCover + 1, size + 1)

        elif mode == 'out':

            # No coverage, anything that
            # we generate will be outside
            if np.isnan(lowCover) or np.isnan(highCover):
                lowSlice  = np.random.randint(0,            size)
                highSlice = np.random.randint(lowSlice + 1, size + 1)

            # The coverage is full, so we can't
            # generate an outside range
            elif lowCover == 0 and highCover == size:
                lowSlice  = np.random.randint(lowCover,     highCover)
                highSlice = np.random.randint(lowSlice + 1, highCover + 1)

            # If low coverage is 0, the slice
            # must be above the coverage
            elif lowCover == 0:
                lowSlice  = np.random.randint(highCover,    size)
                highSlice = np.random.randint(lowSlice + 1, size + 1)

            # If high coverage is size, the
            # slice must be below the coverage
            elif highCover == size:
                lowSlice  = np.random.randint(0,            lowCover)
                highSlice = np.random.randint(lowSlice + 1, lowCover + 1)

            # Otherwise the slice could be
            # below or above the coverage
            else:
                lowSlice = random.choice((np.random.randint(0,         lowCover),
                                          np.random.randint(highCover, size)))

                if    lowSlice < lowCover: highSlice = np.random.randint(lowSlice + 1, lowCover + 1)
                else:                      highSlice = np.random.randint(lowSlice + 1, size     + 1)


        slices[0, dim] = lowSlice
        slices[1, dim] = highSlice

    slices = [tuple(map(int, pair)) for pair in slices.T]
    return slices


def rfloat(lo, hi):
    return lo + np.random.random() * (hi - lo)

def applyCoverage(wrapper, coverage):

    ndims = coverage.shape[1]
    nvols = coverage.shape[2]

    wrapper.reset()
    # 'Apply' that coverage to the image
    # wrapper by accessing the data in it

    for vol in range(nvols):
        if np.any(np.isnan(coverage[..., vol])):
            continue

        sliceobjs = []
        for dim in range(ndims):
            sliceobjs.append(
                slice(int(coverage[0, dim, vol]),
                      int(coverage[1, dim, vol]), 1))
        sliceobjs.append(vol)

        wrapper[tuple(sliceobjs)]
        _ImageWraper_busy_wait(wrapper)

    # Check that the image wrapper
    # has covered what we just told
    # it to cover

    for vol in range(nvols):

        uncovered = np.any(np.isnan(coverage[..., vol]))

        wcov = wrapper.coverage(vol)

        if uncovered:
            assert np.any(np.isnan(wcov))

        else:

            for dim in range(ndims):
                assert coverage[0, dim, vol] == wcov[0, dim]
                assert coverage[1, dim, vol] == wcov[1, dim]


def coverageDataRange(data, coverage, slices=None):

    # Assuming that adjustCoverage is working.
    ndims = coverage.shape[1]
    nvols = coverage.shape[2]

    origcoverage = coverage

    if slices is not None:

        coverage = np.copy(coverage)

        lowVol, highVol = slices[-1]

        for vol in range(lowVol, highVol):
            coverage[..., vol] = imagewrap.adjustCoverage(
                coverage[..., vol], slices[:ndims])

    volmin = []
    volmax = []

    for vol in range(nvols):

        cov = coverage[..., vol]

        if np.any(np.isnan(cov)):
            continue

        sliceobj = []

        for d in range(ndims):
            sliceobj.append(slice(int(cov[0, d]), int(cov[1, d]), 1))
        sliceobj.append(vol)

        voldata = data[tuple(sliceobj)]
        volmin.append(voldata.min())
        volmax.append(voldata.max())

    return np.min(volmin), np.max(volmax)


def test_sliceObjToSliceTuple():

    func  = imagewrap.sliceObjToSliceTuple
    shape = (10, 10, 10)


    assert func( 2,                                       shape) == ((2, 3),  (0, 10), (0, 10))
    assert func( slice(None),                             shape) == ((0, 10), (0, 10), (0, 10))
    assert func((slice(None), slice(None),  slice(None)), shape) == ((0, 10), (0, 10), (0, 10))
    assert func((9,           slice(None),  slice(None)), shape) == ((9, 10), (0, 10), (0, 10))
    assert func((slice(None), 5,            slice(None)), shape) == ((0, 10), (5, 6),  (0, 10))
    assert func((slice(None), slice(None),  3),           shape) == ((0, 10), (0, 10), (3, 4))
    assert func((slice(4, 6), slice(None),  slice(None)), shape) == ((4, 6),  (0, 10), (0, 10))
    assert func((8,           slice(1, 10), slice(None)), shape) == ((8, 9),  (1, 10), (0, 10))



def test_sliceTupleToSliceObj():

    func  = imagewrap.sliceTupleToSliceObj
    shape = (10, 10, 10)

    for x1, y1, z1 in it.product(*[range(d - 1) for d in shape]):

        for x2, y2, z2 in it.product(*[range(s + 1, d) for s, d in zip((x1, y1, z1), shape)]):

            slices   = [[x1, x2], [y1, y2], [z1, z2]]
            sliceobj = (slice(x1, x2, 1), slice(y1, y2, 1), slice(z1, z2, 1))

            assert func(slices) == sliceobj



def test_adjustCoverage():

    # TODO Randomise

    n = np.nan

    # Each test is a tuple of (coverage, expansion, expectedResult)
    tests = [([[3, 5], [2, 6]], [[6, 7], [8,  10]],         [[3, 7], [2,  10]]),
             ([[0, 0], [0, 0]], [[1, 2], [3,  5]],          [[0, 2], [0,  5]]),
             ([[2, 3], [0, 6]], [[1, 5], [4,  10]],         [[1, 5], [0,  10]]),
             ([[0, 1], [0, 1]], [[0, 7], [19, 25], [0, 1]], [[0, 7], [0,  25]]),
             ([[n, n], [n, n]], [[0, 7], [19, 25], [0, 1]], [[0, 7], [19, 25]]),
    ]

    for coverage, expansion, result in tests:

        result   = np.array(result)  .T
        coverage = np.array(coverage).T

        assert np.all(imagewrap.adjustCoverage(coverage, expansion) == result)


def test_sliceOverlap(niters):

    # A bunch of random coverages
    for _ in range(niters):

        # 2D, 3D or 4D?
        # ndims is the number of dimensions
        # in one vector/slice/volume
        ndims = random.choice((2, 3, 4)) - 1

        # Shape of one vector[2D]/slice[3D]/volume[4D]
        shape = np.random.randint(5, 100, size=ndims + 1)

        # Number of vectors/slices/volumes
        nvols = shape[-1]

        coverage = random_coverage(shape)

        # Generate some slices that should
        # be contained within the coverage
        for _ in range(niters):
            slices = random_slices(coverage, shape, 'in')
            assert imagewrap.sliceOverlap(slices, coverage) == imagewrap.OVERLAP_ALL

        # Generate some slices that should
        # overlap with the coverage
        for _ in range(niters):
            slices = random_slices(coverage, shape, 'overlap')
            assert imagewrap.sliceOverlap(slices, coverage) == imagewrap.OVERLAP_SOME

        # Generate some slices that should
        # be outside of the coverage
        for _ in range(niters):
            slices = random_slices(coverage, shape, 'out')
            assert imagewrap.sliceOverlap(slices, coverage)  == imagewrap.OVERLAP_NONE


def test_sliceCovered(niters):

    # A bunch of random coverages
    for _ in range(niters):

        # 2D, 3D or 4D?
        # ndims is the number of dimensions
        # in one vector/slice/volume
        ndims = random.choice((2, 3, 4)) - 1

        # Shape of one vector[2D]/slice[3D]/volume[4D]
        shape = np.random.randint(5, 100, size=ndims + 1)

        # Number of vectors/slices/volumes
        nvols = shape[-1]

        coverage = random_coverage(shape)

        # Generate some slices that should
        # be contained within the coverage
        for _ in range(niters):
            slices = random_slices(coverage, shape, 'in')
            assert imagewrap.sliceCovered(slices, coverage)

        # Generate some slices that should
        # overlap with the coverage
        for _ in range(niters):
            slices = random_slices(coverage, shape, 'overlap')
            assert not imagewrap.sliceCovered(slices, coverage)

        # Generate some slices that should
        # be outside of the coverage
        for _ in range(niters):
            slices = random_slices(coverage, shape, 'out')
            assert not imagewrap.sliceCovered(slices, coverage)


# The sum of the coverage ranges + the
# expansion ranges should be equal to
# the coverage, expanded to include the
# original slices (or the expansions
# - should be equivalent). Note that
# if imagewrapper.adjustCoverage is
# broken, this validation will also be
# broken.
def _test_expansion(coverage, slices, volumes, expansions):
    ndims = coverage.shape[1]

    print()
    print('Slice:    "{}"'.format(" ".join(["{:2d} {:2d}".format(l, h) for l, h in slices])))

    # Figure out what the adjusted
    # coverage should look like (assumes
    # that adjustCoverage is working, and
    # the coverage is the same on all
    # volumes)
    oldCoverage  = coverage[..., 0]
    newCoverage  = imagewrap.adjustCoverage(oldCoverage, slices)

    nc = newCoverage

    # We're goint to test that every point
    # in the expected (expanded) coverage
    # is contained either in the original
    # coverage, or in one of the expansions.
    dimranges = []
    for d in range(ndims):
        dimranges.append(np.linspace(nc[0, d],
                                     nc[1, d],
                                     int(nc[1, d] / 5),
                                     dtype=np.uint32))

    points = it.product(*dimranges)

    # Bin the expansions by volume
    expsByVol = collections.defaultdict(list)
    for vol, exp in zip(volumes, expansions):
        print('  {:3d}:    "{}"'.format(
            int(vol),
            " ".join(["{:2d} {:2d}".format(int(l), int(h)) for l, h in exp])))
        expsByVol[vol].append(exp)

    for point in points:

        # Is this point in the old coverage?
        covered = True
        for dim in range(ndims):
            covLow, covHigh = oldCoverage[:, dim]

            if np.isnan(covLow)    or \
               np.isnan(covHigh)   or \
               point[dim] < covLow or \
               point[dim] > covHigh:
                covered = False
                break

        if covered:
            continue

        for vol, exps in expsByVol.items():

            # Is this point in any of the expansions
            coveredInExp = [False] * len(exps)
            for i, exp in enumerate(exps):

                coveredInExp[i] = True

                for dim in range(ndims):

                    expLow, expHigh = exp[dim]
                    if point[dim] < expLow or point[dim] > expHigh:
                        coveredInExp[i] = False
                        break

        if not (covered or any(coveredInExp)):
            raise AssertionError(point)


def test_calcExpansionNoCoverage(niters):

    for _ in range(niters):
        ndims       = random.choice((2, 3, 4)) - 1
        shape       = np.random.randint(5, 100, size=ndims + 1)
        shape[-1]   = np.random.randint(1, 8)
        coverage    = np.zeros((2, ndims, shape[-1]))
        coverage[:] = np.nan

        print()
        print('-- Out --' )
        for _ in range(niters):
            slices     = random_slices(coverage, shape, 'out')
            vols, exps = imagewrap.calcExpansion(slices, coverage)
            _test_expansion(coverage, slices, vols, exps)


def test_calcExpansion(niters):

    for _ in range(niters):

        ndims     = random.choice((2, 3, 4)) - 1
        shape     = np.random.randint(5, 60, size=ndims + 1)
        shape[-1] = np.random.randint(1, 6)
        coverage  = random_coverage(shape)

        cov = [(lo, hi) for lo, hi in coverage[:, :, 0].T]

        print('Shape:    {}'.format(shape))
        print('Coverage: {}'.format(cov))

        print()
        print('-- In --')
        for _ in range(niters):
            slices     = random_slices(coverage, shape, 'in')
            vols, exps = imagewrap.calcExpansion(slices, coverage)

            # There should be no expansions for a
            # slice that's inside the coverage
            assert len(vols) == 0 and len(exps) == 0

        print()
        print('-- Overlap --' )
        for _ in range(niters):
            slices     = random_slices(coverage, shape, 'overlap')
            vols, exps = imagewrap.calcExpansion(slices, coverage)
            _test_expansion(coverage, slices, vols, exps)

        print()
        print('-- Out --' )
        for _ in range(niters):
            slices     = random_slices(coverage, shape, 'out')
            vols, exps = imagewrap.calcExpansion(slices, coverage)
            _test_expansion(coverage, slices, vols, exps)


def _ImageWraper_busy_wait(wrapper, v=0):
    tt = wrapper.getTaskThread()
    if tt is not None:
        tt.waitUntilIdle()


def test_ImageWrapper_read_threaded(niters, seed):
    _test_ImageWrapper_read(niters, seed, True)
def test_ImageWrapper_read_unthreaded(niters, seed):
    _test_ImageWrapper_read(niters, seed, False)
def test_ImageWrapper_read_nans_threaded(niters, seed):
    _test_ImageWrapper_read(niters, seed, True, True)
def test_ImageWrapper_read_nans_unthreaded(niters, seed):
    _test_ImageWrapper_read(niters, seed, False, True)

def _test_ImageWrapper_read(niters, seed, threaded, addnans=False):

    for _ in range(niters):

        # Generate an image with a number of volumes
        ndims     = random.choice((2, 3, 4)) - 1
        shape     = np.random.randint(5, 60, size=ndims + 1)
        shape[-1] = np.random.randint(5, 15)
        nvols     = shape[-1]

        data = np.zeros(shape)

        # The data range of each volume
        # increases sequentially
        data[..., 0] = np.random.randint(-5, 6, shape[:-1])
        for vol in range(1, nvols):
            data[..., vol] = data[..., 0] * (vol + 1)

        # Add 10-50% infs/nans to the image
        if addnans:

            infprop = 0.10 + 0.2 * np.random.random()
            nanprop = 0.10 + 0.2 * np.random.random()

            ninfs = int(infprop * np.prod(shape[:-1]))
            nnans = int(nanprop * np.prod(shape[:-1]))

            for vol in range(nvols):
                coords = random_voxels(shape[:-1], int(ninfs))
                coords = tuple([coords[..., i] for i in range(ndims)] + [vol])
                data[coords] = np.inf

                coords = random_voxels(shape[:-1], int(nnans))
                coords = tuple([coords[..., i] for i in range(ndims)] + [vol])
                data[coords] = np.nan


        volRanges = [nir.naninfrange(data[..., v]) for v in range(nvols)]

        rrs = []
        for vol in range(nvols):
            rrs.append('{:3d}: {: 3.0f} - {: 3.0f}'.format(
                vol, *volRanges[vol]))

        img     = nib.Nifti1Image(data, np.eye(4))
        wrapper = imagewrap.ImageWrapper(threaded=threaded)
        wrapper.setImage(img)

        # We're going to access data volumes
        # through the image wrapper with a
        # bunch of random volume orderings.
        for _ in range(niters):

            ordering = list(range(nvols))
            random.shuffle(ordering)

            ranges = [volRanges[o] for o in ordering]

            wrapper.reset()

            assert wrapper.dataRange == (0.0, 0.0)

            for j, (vol, r) in enumerate(zip(ordering, ranges)):

                # Access the volume
                if len(data.shape) >= 3: wrapper[..., vol]
                else:                    wrapper[:, vol, 0]

                _ImageWraper_busy_wait(wrapper, vol)

                # The current known data range
                # should be the min/max of
                # all acccessed volumes so far
                expMin = min([r[0] for r in ranges[:j + 1]])
                expMax = max([r[1] for r in ranges[:j + 1]])

                assert wrapper.dataRange == (expMin, expMax)

                if j < nvols - 1: assert not wrapper.covered
                else:             assert     wrapper.covered


def test_ImageWrapper_write_out_threaded(niters, seed):
    _test_ImageWrapper_write_out(niters, seed, True)
def test_ImageWrapper_write_out_unthreaded(niters, seed):
    _test_ImageWrapper_write_out(niters, seed, False)
def _test_ImageWrapper_write_out(niters, seed, threaded):
    # This is HORRIBLE

    loop = 0


    # Generate a bunch of random coverages
    for _ in range(niters):

        # Generate an image with just two volumes. We're only
        # testing within-volume modifications here.
        ndims     = random.choice((2, 3, 4)) - 1
        shape     = np.random.randint(5, 60, size=ndims + 1)
        shape[-1] = np.random.randint(2, 3)
        nvols     = shape[-1]

        data = np.zeros(shape)

        # The data range of each volume
        # increases sequentially
        data[..., 0] = np.random.randint(-5, 6, shape[:-1])
        for vol in range(1, nvols):
            data[..., vol] = data[..., 0] * (vol + 1)

        # Generate a random coverage
        cov = random_coverage(shape, vol_limit=1)

        img     = nib.Nifti1Image(data, np.eye(4))
        wrapper = imagewrap.ImageWrapper(threaded=threaded)
        wrapper.setImage(img)
        applyCoverage(wrapper, cov)
        clo, chi = wrapper.dataRange

        loop += 1

        # Now, we'll simulate some writes
        # outside of the coverage area.
        for _ in range(niters):

            # Generate some slices outside
            # of the coverage area, making
            # sure that the slice covers
            # at least one element
            while True:
                slices     = random_slices(cov, shape, 'out')
                slices[-1] = [0, 1]
                sliceshape = [hi - lo for lo, hi in slices]

                if np.prod(sliceshape) == 0:
                    continue

                sliceobjs = imagewrap.sliceTupleToSliceObj(slices)
                sliceobjs  = tuple(list(sliceobjs[:-1]) + [0])
                sliceshape = sliceshape[:-1]
                break

            # print('---------------')
            # print('Slice {}'.format(slices))

            # Expected wrapper coverage after the write
            expCov = imagewrap.adjustCoverage(cov[..., 0], slices)

            # Figure out the data range of the
            # expanded coverage (the original
            # coverage expanded to include this
            # slice).
            elo, ehi = coverageDataRange(data, cov, slices)

            # Test all data range possibilities:
            #  - inside the existing range       (clo < rlo < rhi < chi)
            #  - encompassing the existing range (rlo < clo < chi < rhi)
            #  - Overlapping the existing range  (rlo < clo < rhi < chi)
            #                                    (clo < rlo < chi < rhi)
            #  - Outside of the existing range   (clo < chi < rlo < rhi)
            #                                    (rlo < rhi < clo < chi)
            loRanges = [rfloat(clo,         chi),
                        rfloat(elo - 100,   elo),
                        rfloat(elo - 100,   elo),
                        rfloat(clo,         chi),
                        rfloat(ehi,         ehi + 100),
                        rfloat(elo - 100,   elo)]

            hiRanges = [rfloat(loRanges[0], chi),
                        rfloat(ehi,         ehi + 100),
                        rfloat(clo,         chi),
                        rfloat(ehi,         ehi + 100),
                        rfloat(loRanges[4], ehi + 100),
                        rfloat(loRanges[5], elo)]

            for rlo, rhi in zip(loRanges, hiRanges):

                img     = nib.Nifti1Image(np.copy(data), np.eye(4))
                wrapper = imagewrap.ImageWrapper()
                wrapper.setImage(img)
                applyCoverage(wrapper, cov)

                # print('ndims', ndims)
                # print('sliceshape', sliceshape)
                # print('sliceobjs', sliceobjs)

                newData = np.linspace(rlo, rhi, np.prod(sliceshape))
                newData = newData.reshape(sliceshape)

                # Make sure that the expected low/high values
                # are present in the data being written

                # print('Writing data (shape: {})'.format(newData.shape))

                oldCov = wrapper.coverage(0)

                wrapper[tuple(sliceobjs)] = newData
                _ImageWraper_busy_wait(wrapper)

                expLo, expHi = coverageDataRange(np.asanyarray(img.dataobj), cov, slices)
                newLo, newHi = wrapper.dataRange

                # print('Old    range: {} - {}'.format(clo,   chi))
                # print('Sim    range: {} - {}'.format(rlo,   rhi))
                # print('Exp    range: {} - {}'.format(expLo, expHi))
                # print('NewDat range: {} - {}'.format(newData.min(), newData.max()))
                # print('Data   range: {} - {}'.format(data.min(),   data.max()))
                # print('Expand range: {} - {}'.format(elo, ehi))
                # print('New    range: {} - {}'.format(newLo, newHi))

                newCov = wrapper.coverage(0)
                # print('Old coverage:      {}'.format(oldCov))
                # print('New coverage:      {}'.format(newCov))
                # print('Expected coverage: {}'.format(expCov))
                # print()
                # print()

                assert np.all(newCov == expCov)

                assert np.isclose(newLo, expLo)
                assert np.isclose(newHi, expHi)
            # print('--------------')


def test_ImageWrapper_write_in_overlap_threaded(niters, seed):
    _test_ImageWrapper_write_in_overlap(niters, seed, True)
def test_ImageWrapper_write_in_overlap_unthreaded(niters, seed):
    _test_ImageWrapper_write_in_overlap(niters, seed, False)
def _test_ImageWrapper_write_in_overlap(niters, seed, threaded):

    # Generate a bunch of random coverages
    for _ in range(niters):

        # Generate an image with just two volumes. We're only
        # testing within-volume modifications here.
        ndims     = random.choice((2, 3, 4)) - 1
        shape     = np.random.randint(5, 60, size=ndims + 1)
        shape[-1] = np.random.randint(2, 3)
        nvols     = shape[-1]

        data = np.zeros(shape)

        # The data range of each volume
        # increases sequentially
        data[..., 0] = np.random.randint(-5, 6, shape[:-1])
        for vol in range(1, nvols):
            data[..., vol] = data[..., 0] * (vol + 1)

        # Generate a random coverage
        cov = random_coverage(shape, vol_limit=1)

        print('Shape:    {}'.format(shape))
        print('Coverage: {}'.format(cov))
        print('Data:     {}'.format(data))

        # Now, we'll simulate some writes
        # which are contained within, or
        # overlap with, the initial coverage
        for _ in range(niters):

            # Generate some slices outside
            # of the coverage area, making
            # sure that the slice covers
            # at least one element
            while True:
                slices     = random_slices(cov, shape, random.choice(('in', 'overlap')))
                slices[-1] = [0, 1]
                sliceshape = [hi - lo for lo, hi in slices]

                if np.prod(sliceshape) == 0:
                    continue

                sliceobjs = imagewrap.sliceTupleToSliceObj(slices)
                sliceobjs  = tuple(list(sliceobjs[:-1]) + [0])
                sliceshape = sliceshape[:-1]
                break

            # Expected wrapper coverage after the
            # write is the union of the original
            # coverage and the write slice.
            expCov = imagewrap.adjustCoverage(cov[..., 0], slices)

            for _ in range(10):

                rlo = rfloat(data.min() - 100, data.max() + 100)
                rhi = rfloat(rlo,              data.max() + 100)

                if np.prod(sliceshape) == 1:
                    rhi = rlo

                img     = nib.Nifti1Image(np.copy(data), np.eye(4))
                wrapper = imagewrap.ImageWrapper(threaded=threaded)
                wrapper.setImage(img)
                applyCoverage(wrapper, cov)

                newData = np.linspace(rlo, rhi, np.prod(sliceshape))
                newData = newData.reshape(sliceshape)

                print('Old coverage:      {}'.format(cov[..., 0]))
                print('Slice:             {}'.format(sliceobjs[:-1]))
                print('Expected coverage: {}'.format(expCov))
                print('Old range:         {} - {}'.format(*wrapper.dataRange))
                print('New data range:    {} - {}'.format(newData.min(), newData.max()))

                # We figure out the expected data
                # range by creating a copy of the
                # data, and doing the same write
                expData = np.copy(data[..., 0])
                expData[sliceobjs[:-1]] = newData

                # Then calcultaing the min/max
                # on this copy
                expCovSlice = [slice(int(lo), int(hi)) for lo, hi in expCov.T]

                expLo = expData[tuple(expCovSlice)].min()
                expHi = expData[tuple(expCovSlice)].max()

                wrapper[tuple(sliceobjs)] = newData
                _ImageWraper_busy_wait(wrapper)

                newCov       = wrapper.coverage(0)
                newLo, newHi = wrapper.dataRange

                print('Expected range:    {} - {}'.format(expLo, expHi))
                print('New range:         {} - {}'.format(newLo, newHi))
                print('Slice min/max:     {} - {}'.format(np.asanyarray(img.dataobj)[tuple(sliceobjs)].min(),
                                                          np.asanyarray(img.dataobj)[tuple(sliceobjs)].max()))
                print('Data min/max:      {} - {}'.format(np.asanyarray(img.dataobj).min(),
                                                          np.asanyarray(img.dataobj).max()))

                assert np.all(newCov == expCov)

                assert np.isclose(newLo, expLo)
                assert np.isclose(newHi, expHi)


def test_ImageWrapper_write_different_volume_threaded(niters, seed):
    _test_ImageWrapper_write_different_volume(niters, seed, True)
def test_ImageWrapper_write_different_volume_unthreaded(niters, seed):
    _test_ImageWrapper_write_different_volume(niters, seed, False)
def _test_ImageWrapper_write_different_volume(niters, seed, threaded):

    for _ in range(niters):

        # Generate an image with several volumes.
        ndims     = random.choice((2, 3, 4)) - 1
        nvols     = np.random.randint(10, 40)
        shape     = np.random.randint(5, 60, size=ndims + 1)
        shape[-1] = nvols

        data = np.zeros(shape)

        # The data range of each volume
        # increases sequentially
        data[..., 0] = np.random.randint(-5, 6, shape[:-1])
        for vol in range(1, nvols):
            data[..., vol] = data[..., 0] * (vol + 1)


        # Generate a random coverage
        fullcov = random_coverage(shape)
        cov     = np.copy(fullcov)

        # Choose some consecutive volumes
        # to limit that coverage to.
        while True:
            covvlo = np.random.randint(0,          nvols - 1)
            covvhi = np.random.randint(covvlo + 1, nvols + 1)

            # Only include up to 4
            # volumes in the coverage
            if covvhi - covvlo <= 3:
                break

        for v in range(nvols):
            if v < covvlo or v >= covvhi:
                cov[..., v] = np.nan

        covlo, covhi = coverageDataRange(data, cov)

        print('Coverage: {} [{} - {}]'.format(
            [(lo, hi) for lo, hi in cov[:, :, covvlo].T],
            covvlo, covvhi))

        # Now, we'll simulate some writes
        # on volumes that are not in the
        # coverage
        for _ in range(niters):

            # Generate a slice, making
            # sure that the slice covers
            # at least one element
            while True:
                slices = random_slices(fullcov,
                                       shape,
                                       random.choice(('out', 'in', 'overlap')))

                # print(slices)

                # Clobber the slice volume range
                # so it does not overlap with the
                # coverage volume range
                while True:
                    vlo = np.random.randint(0,       nvols)
                    vhi = np.random.randint(vlo + 1, nvols + 1)

                    if vhi < covvlo or vlo > covvhi:
                        break

                slices[-1] = vlo, vhi

                sliceshape = [hi - lo for lo, hi in slices]

                if np.prod(sliceshape) == 0:
                    continue

                sliceobjs = imagewrap.sliceTupleToSliceObj(slices)
                break

            # Calculate what we expect the
            # coverage to be after the write
            expCov = np.copy(cov)
            for vol in range(slices[-1][0], slices[-1][1]):
                expCov[..., vol] = imagewrap.adjustCoverage(
                    expCov[..., vol], slices)

            # Test all data range possibilities:
            #  - inside the existing range       (clo < rlo < rhi < chi)
            #  - encompassing the existing range (rlo < clo < chi < rhi)
            #  - Overlapping the existing range  (rlo < clo < rhi < chi)
            #                                    (clo < rlo < chi < rhi)
            #  - Outside of the existing range   (clo < chi < rlo < rhi)
            #                                    (rlo < rhi < clo < chi)

            loRanges = [rfloat(covlo,         covhi),
                        rfloat(covlo - 100,   covlo),
                        rfloat(covlo - 100,   covlo),
                        rfloat(covlo,         covhi),
                        rfloat(covhi,         covhi + 100),
                        rfloat(covlo - 100,   covlo)]

            hiRanges = [rfloat(loRanges[0], covhi),
                        rfloat(covhi,       covhi + 100),
                        rfloat(covlo,       covhi),
                        rfloat(covhi,       covhi + 100),
                        rfloat(loRanges[4], covhi + 100),
                        rfloat(loRanges[5], covlo)]

            # What we expect the range to
            # be after the data write
            expected = [(covlo,       covhi),
                        (loRanges[1], hiRanges[1]),
                        (loRanges[2], covhi),
                        (covlo,       hiRanges[3]),
                        (covlo,       hiRanges[4]),
                        (loRanges[5], covhi)]

            for rlo, rhi, (elo, ehi) in zip(loRanges, hiRanges, expected):

                img     = nib.Nifti1Image(np.copy(data), np.eye(4))
                wrapper = imagewrap.ImageWrapper(threaded=threaded)
                wrapper.setImage(img)
                applyCoverage(wrapper, cov)

                oldLo, oldHi = wrapper.dataRange


                newData = np.linspace(rlo, rhi, np.prod(sliceshape))
                newData = newData.reshape(sliceshape)

                if np.prod(sliceshape) == 1:
                    ehi = max(newData.max(), oldHi)

                wrapper[tuple(sliceobjs)] = newData
                _ImageWraper_busy_wait(wrapper)

                newLo, newHi = wrapper.dataRange

                for vol in range(nvols):
                    np.all(wrapper.coverage(vol) == expCov[..., vol])

                print('Old range:      {} - {}'.format(oldLo, oldHi))
                print('Newdata range:  {} - {}'.format(newData.min(), newData.max()))
                print('Expected range: {} - {}'.format(elo,   ehi))
                print('New range:      {} - {}'.format(newLo, newHi))

                assert np.isclose(newLo, elo)
                assert np.isclose(newHi, ehi)


def test_collapseExpansions(niters):

    def expEq(exp1, exp2):

        if len(exp1) != len(exp2):
            return False

        for (e1lo, e1hi), (e2lo, e2hi) in zip(exp1, exp2):
            if e1lo != e2lo: return False
            if e1hi != e2hi: return False
        return True

    def rangesOverlapOrAdjacent(r1, r2):

        r1lo, r1hi = r1
        r2lo, r2hi = r2

        return not ((r1lo > r2hi) or (r1hi < r2lo) or \
                    (r2lo > r1hi) or (r2hi < r1lo))

    for _ in range(niters):

        # Generate a random coverage shape
        ndims     = random.choice((2, 3, 4)) - 1
        nvols     = np.random.randint(10, 40)
        shape     = np.random.randint(5, 60, size=ndims + 1)
        shape[-1] = nvols

        # Generate a bunch of random slices, and
        # split each of them up by volume to
        # turn them each into a set of expansions
        exps     = []
        expected = []

        for _ in range(10):

            # Generate a random slice with a volume
            # range that doesn't overlap with, and
            # is not adjacent to, any of the other
            # generated random slices.
            #
            # The only reason I'm doing this is to
            # overocme a chicken-and-egg problem -
            # if I want to test overlapping/adjacent
            # region, I basically have to
            # re-implement the collapseExpansions
            # function.
            while True:
                slices = random_slices(None, shape, 'in')
                vlo, vhi = slices[-1]

                for exp in expected:

                    if not expEq(exp[:-1], slices[:-1]):
                        continue

                    evlo, evhi = exp[-1]

                    # Overlap
                    if rangesOverlapOrAdjacent((vlo, vhi), (evlo, evhi)):
                        break
                else:
                    break

            expected.append(slices)

            for vol in range(slices[-1][0], slices[-1][1]):

                exp = tuple(list(slices[:-1]) + [(vol, vol + 1)])
                exps.append(exp)

        # Now shuffle them up randomly
        np.random.shuffle(exps)

        # And attempt to collapse them
        collapsed = imagewrap.collapseExpansions(exps, ndims)

        collapsed = sorted(collapsed)
        expected  = sorted(expected)

        assert len(expected) == len(collapsed)

        for exp, col in zip(expected, collapsed):
            assert expEq(exp, col)
