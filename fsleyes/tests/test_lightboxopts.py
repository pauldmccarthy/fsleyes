#!/usr/bin/env python

import itertools as it

from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image
from fsleyes.tests     import (run_with_lightboxpanel,
                               random_image)


def test_asVoxels():
    run_with_lightboxpanel(_test_asVoxels)
def _test_asVoxels(panel, overlayList, displayCtx):

    opts    = panel.sceneOpts
    pixdims = [0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 2.4]

    with tempdir():
        for pixdim in pixdims:
            fname = f'image_{pixdim:0.1f}.nii.gz'
            random_image(fname, (100, 100, 100))
            overlayList.append(Image(fname))

    # round trip for setSlicesFromVoxels <-> getSlicesAsVoxels
    # for a range of zranges/slice spacings/pixdims

    zranges  = [(0, 99), (3, 97), (10, 90), (24, 83)]
    spacings = [1, 2, 7, 10, 12]

    for image, (zlo, zhi), spacing in it.product(overlayList, zranges, spacings):

        displayCtx.displaySpace = image
        opts.sampleSlices       = 'start'

        opts.setSlicesFromVoxels(image, zlo, zhi, spacing)
        assert opts.getSlicesAsVoxels(image) == (zlo, zhi, spacing)
