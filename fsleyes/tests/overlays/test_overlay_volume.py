#!/usr/bin/env python
#
# test_overlay_volume.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import pytest

try:
    from unittest import mock
except ImportError:
    import mock

import numpy as np

import fsl.transform.affine as affine
import fsl.data.image       as fslimage

from fsleyes.tests import (run_cli_tests,
                           translate,
                           zero_centre,
                           asrgb,
                           roi,
                           complex,
                           invert)


pytestmark = pytest.mark.overlayclitest


cli_tests = """
3d.nii.gz -dr 2000 7500
3d.nii.gz -dr 2000 7500 -i
3d.nii.gz -dr 2000 7500 -b 1 -c 5 # -dr should override -b/-c
3d.nii.gz -dr 2000 7500 -cr 4000 8000
3d.nii.gz -dr 2000 7500 -cr 4000 6000 -ic
3d.nii.gz -dr 2000 7500 -cr 4000 6000 -ll   # low ranges are linked - -cr overrides -dr
3d.nii.gz -dr 2000 7500 -cr 4000 6000 -ll -ic
3d.nii.gz -dr 2000 7500 -cr 4000 6000 -ll -lh  # high ranges are linked - -cr overrides -dr
3d.nii.gz -dr 5000 7500 -cr 4000 6000 -ll -lh -ic

3d.nii.gz -dr 20 80%
3d.nii.gz -cr 20 80%

3d.nii.gz -cm {{gen_cmap(custom_cmap)}}
3d.nii.gz -cm {{gen_cmap(custom_cmap)}} -inc

{{zero_centre('3d.nii.gz')}} -cm hot
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool # -nc should be ignored (TODO I should change this)
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un -dr -1000 2000
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un -dr  0    2000
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un -dr  1000 2000

{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un -dr  1000 2000 -cr 500 1500
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un -dr  1000 2000 -cr 500 1500 -ll
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un -dr  1000 2000 -cr 500 1500 -lh
{{zero_centre('3d.nii.gz')}} -cm hot -nc cool -un -dr  1000 2000 -cr 500 1500 -ll -lh

-xz 750 -yz 750 -zz 750 3d.nii.gz -in none
-xz 750 -yz 750 -zz 750 3d.nii.gz -in linear
-xz 750 -yz 750 -zz 750 3d.nii.gz -in spline

4d.nii.gz -v 0 -b 40 -c 90
4d.nii.gz -v 1 -b 40 -c 90
4d.nii.gz -v 2 -b 40 -c 90
4d.nii.gz -v 3 -b 40 -c 90
4d.nii.gz -v 4 -b 40 -c 90

3d.nii.gz                              -cl {{gen_indices('3d.nii.gz')}} -cr 1600 4000
3d.nii.gz                              -cl {{gen_indices('3d.nii.gz')}} -cr 1600 4000 -ic
{{zero_centre('3d.nii.gz')}}           -cl {{gen_indices('3d.nii.gz')}} -cr 1600 4000 -cm hot -nc cool -un
{{zero_centre('3d.nii.gz')}}           -cl {{gen_indices('3d.nii.gz')}} -cr 1600 4000 -cm hot -nc cool -un -ic
{{gen_indices('3d.nii.gz')}} 3d.nii.gz -cl {{gen_indices('3d.nii.gz')}} -cr 1600 4000

3d.nii.gz                    -cl {{translate('3d.nii.gz', 10, 10, 10)}} -cr 1600 4000   -cm hot
3d.nii.gz                    -cl {{translate('3d.nii.gz', 10, 10, 10)}} -cr 1600 4000   -cm hot -ic
{{zero_centre('3d.nii.gz')}} -cl {{translate('3d.nii.gz', 10, 10, 10)}} -cr 1600 4000   -cm hot -nc cool -un
{{zero_centre('3d.nii.gz')}} -cl {{translate('3d.nii.gz', 10, 10, 10)}} -cr 1600 4000   -cm hot -nc cool -un -ic

3d.nii.gz -cm hot -cmr 256
3d.nii.gz -cm hot -cmr 128
3d.nii.gz -cm hot -cmr 64
3d.nii.gz -cm hot -cmr 32
3d.nii.gz -cm hot -cmr 16
3d.nii.gz -cm hot -cmr 8
3d.nii.gz -cm hot -cmr 4
3d.nii.gz -cm hot -cmr 16  -i
3d.nii.gz -cm hot -cmr 8   -i
3d.nii.gz -cm hot -cmr 4   -i
3d.nii.gz -cm hot -cmr 256 -inc
3d.nii.gz -cm hot -cmr 128 -inc
3d.nii.gz -cm hot -cmr 64  -inc
3d.nii.gz -cm hot -cmr 32  -inc
3d.nii.gz -cm hot -cmr 16  -inc
3d.nii.gz -cm hot -cmr 8   -inc
3d.nii.gz -cm hot -cmr 4   -inc

{{zero_centre('3d.nii.gz')}} -cm red-yellow -un -nc blue-lightblue -cmr 6
{{zero_centre('3d.nii.gz')}} -cm red-yellow -un -nc blue-lightblue -cmr 6 -i
{{zero_centre('3d.nii.gz')}} -cm red-yellow -un -nc blue-lightblue -cmr 6 -inc
{{zero_centre('3d.nii.gz')}} -cm red-yellow -un -nc blue-lightblue -cmr 6 -inc -i

3d.nii.gz -cm hot -g -0.909
3d.nii.gz -cm hot -g 0
3d.nii.gz -cm hot -g 0.1111
3d.nii.gz -cm hot -g 0.2222
3d.nii.gz -cm hot -g 0.4444

{{asrgb('dti/dti_V1.nii.gz')}}
{{asrgb('dti/dti_V1.nii.gz')}} -ch R
{{asrgb('dti/dti_V1.nii.gz')}} -ch G
{{asrgb('dti/dti_V1.nii.gz')}} -ch B

-vl 0 0 0 -xc 0 0 -yc 0 0 -zc 0 0 {{roi('3d.nii.gz', (0, 17, 0, 14, 6,  7))}} {{roi('3d.nii.gz', (0, 17, 6,  7, 0, 14))}} {{roi('3d.nii.gz', (8,  9, 0, 14, 0, 14))}}

{{complex()}}  -ot volume # real component should be displayed

-bg 1 1 1 3d.nii.gz                    -ma               -cm red-yellow
-bg 1 1 1 3d.nii.gz                    -ma -mr 1993 5000 -cm red-yellow
-bg 1 1 1 3d.nii.gz                    -ma -mr 5000 7641 -cm red-yellow
-bg 1 1 1 3d.nii.gz                    -ma -mr 10   90%  -cm red-yellow
-bg 1 1 1 {{zero_centre('3d.nii.gz')}} -ma               -cm red-yellow -nc blue-lightblue -un
-bg 1 1 1 {{zero_centre('3d.nii.gz')}} -ma -mr 0    1500 -cm red-yellow -nc blue-lightblue -un
-bg 1 1 1 {{zero_centre('3d.nii.gz')}} -ma -mr 1500 3688 -cm red-yellow -nc blue-lightblue -un

-bg 1 1 1 3d.nii.gz                    -ma               -cm red-yellow -mi {{invert('3d.nii.gz')}} {{invert('3d.nii.gz')}} -d
-bg 1 1 1 3d.nii.gz                    -ma -mr 1993 5000 -cm red-yellow -mi {{invert('3d.nii.gz')}} {{invert('3d.nii.gz')}} -d
-bg 1 1 1 3d.nii.gz                    -ma -mr 5000 7641 -cm red-yellow -mi {{invert('3d.nii.gz')}} {{invert('3d.nii.gz')}} -d
-bg 1 1 1 3d.nii.gz                    -ma -mr 10   90%  -cm red-yellow -mi {{invert('3d.nii.gz')}} {{invert('3d.nii.gz')}} -d
"""  # noqa


def gen_indices(infile):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_indices.nii.gz'.format(basename)
    img      = fslimage.Image(infile, loadData=False)
    shape    = img.shape
    data     = np.arange(np.prod(shape)).reshape(shape)

    fslimage.Image(data, header=img.header).save(outfile)

    return outfile


custom_cmap = np.array([
    [0, 0, 0],
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1]])


def gen_cmap(cmap):
    np.savetxt('custom.cmap', cmap)
    return 'custom.cmap'


def test_overlay_volume():
    extras = {
        'gen_indices' : gen_indices,
        'zero_centre' : zero_centre,
        'translate'   : translate,
        'gen_cmap'    : gen_cmap,
        'custom_cmap' : custom_cmap,
        'swapdim'     : swapdim,
        'asrgb'       : asrgb,
        'roi'         : roi,
        'complex'     : complex,
        'invert'      : invert,
    }
    run_cli_tests('test_overlay_volume', cli_tests, extras=extras)


def test_overlay_volume_silly_range():
    with mock.patch('fsleyes.gl.textures.data.canUseFloatTextures',
                    return_value=(False, None, None)):
        run_cli_tests('test_overlay_volume_silly_range',
                      '{{silly_range()}}',
                      extras={'silly_range' : silly_range})


def test_overlay_volume_swapdim():
    run_cli_tests('test_overlay_volume_swapdim',
                  "3d.nii.gz {{swapdim('3d.nii.gz')}} -a 50 -cm hot",
                  extras={'swapdim' : swapdim})


def silly_range():

    data = np.arange(1000, dtype=np.float32).reshape((10, 10, 10))

    data[4, 4, 4:6] *= -10e10
    data[5, 5, 4:6] *=  10e10

    fslimage.Image(data).save('silly_range.nii.gz')
    return 'silly_range.nii.gz'





def swapdim(infile):
    basename = fslimage.removeExt(op.basename(infile))
    outfile  = '{}_swapdim.nii.gz'.format(basename)
    img      = fslimage.Image(infile)

    data     = img.data
    xform    = img.voxToWorldMat

    data = data.transpose((2, 0, 1))
    rot  = affine.rotMatToAffine(affine.concat(
        affine.axisAnglesToRotMat(np.pi / 2, 0, 0),
        affine.axisAnglesToRotMat(0, 0, 3 * np.pi / 2)))
    xform = affine.concat(
        xform,
        affine.scaleOffsetXform((1, -1, -1), (0, 0, 0)),
        rot)

    fslimage.Image(data, xform=xform, header=img.header).save(outfile)

    return outfile
