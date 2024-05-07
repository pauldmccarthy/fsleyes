#!/usr/bin/env python

import itertools as it

from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image
from fsleyes.tests     import (run_with_lightboxpanel,
                               random_image)


def test_asVoxels():
    run_with_lightboxpanel(_test_asVoxels)
def _test_asVoxels(panel, overlayList, displayCtx):

    with tempdir():
        random_image('image.nii.gz', (100, 100, 100))
        img = Image('image.nii.gz')
        overlayList.append(img)

    opts = panel.sceneOpts

    displayCtx.displaySpace = img
    opts.sampleSlices       = 'start'

    # round trip for setSlicesFromVoxels <-> getSlicesAsVoxels
    # for a range of zranges/slice spacings
    zranges = [(0, 100), (3, 97), (10, 90), (24, 83)]
    spacings = [1, 2, 7, 10, 12]

    for (zlo, zhi), spacing in it.product(zranges, spacings):

        opts.setSlicesFromVoxels(img, zlo, zhi, spacing)

        assert opts.getSlicesAsVoxels(img) == (zlo, zhi, spacing)
