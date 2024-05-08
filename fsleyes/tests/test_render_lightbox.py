#!/usr/bin/env python
#
# test_render_lightbox.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np

import pytest

from fsl.data.image import Image, removeExt

from fsleyes.tests import run_cli_tests, roi, swapdim



pytestmark = pytest.mark.clitest


cli_tests = """
# zaxis
-zr 0 1 -zx 0 3d.nii.gz
-zr 0 1 -zx 1 3d.nii.gz
-zr 0 1 -zx 2 3d.nii.gz
-zr 0 1 -zx x 3d.nii.gz
-zr 0 1 -zx y 3d.nii.gz
-zr 0 1 -zx z 3d.nii.gz
-zr 0 1 -zx X 3d.nii.gz
-zr 0 1 -zx Y 3d.nii.gz
-zr 0 1 -zx Z 3d.nii.gz

# show grid/highlight slice
-zr 0 1 -sg     3d.nii.gz
-zr 0 1     -hs 3d.nii.gz
-zr 0 1 -sg -hs 3d.nii.gz

# cursor width
-zr 0 1 -cw 5  3d
-zr 0 1 -cw 10 3d

# fsl/fsleyes/fsleyes!333
# L/R flip for neuro-orientation option in lightbox view was being applied
# around the centre of each overlay's FOV, rather than around the centre of
# the display coordinate system
-zx 2 -zr 0 1     3d -cm blue-lightblue {{roi('3d', (0, 6, 0, 14, 0, 14))}}
-zx 2 -zr 0 1 -no 3d -cm blue-lightblue {{roi('3d', (0, 6, 0, 14, 0, 14))}}
-zx 1 -zr 0 1 -no 3d
-zx 1 -zr 0 1     3d
-zx 2 -zr 0 1 -no 3d
-zx 2 -zr 0 1     3d

# Check that cursor position is correct
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  2  -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  7  -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  12 -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  17 -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  22 -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  27 -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  32 -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  37 -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  42 -cw 10 numbers
-nr 1 -ss 0.1 -zr 0 1 -vl 50 50  47 -cw 10 numbers

# sampleSlices. Unlikely to be used directly,
# but is internally/indirectly used via --asVoxels
-zx 2 -zr 0 1 -ss 0.08 -sa centre numbers
-zx 2 -zr 0 1 -ss 0.08 -sa start  numbers
"""

cli_tests_parametrize_zax = """
# zrange
-zx {{zax}} -zr 0    1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0    1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0    1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0    1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0    0.5  {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0    0.5  {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0    0.5  {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0    0.5  {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.5  1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.5  1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.5  1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.5  1    {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.25 0.75 {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.25 0.75 {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.25 0.75 {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -zr 0.25 0.75 {{set_zax('numbers.nii.gz', zax)}}

# nrows/ncols
-zx {{zax}} -zr 0 1 -nr 1                 3d
-zx {{zax}} -zr 0 1 -nr 2                 3d
-zx {{zax}} -zr 0 1 -nr 3                 3d
-zx {{zax}} -zr 0 1       -nc 1           3d
-zx {{zax}} -zr 0 1       -nc 2           3d
-zx {{zax}} -zr 0 1       -nc 3           3d
-zx {{zax}} -zr 0 1 -nr 1 -nc 1           3d
-zx {{zax}} -zr 0 1 -nr 1 -nc 2           3d
-zx {{zax}} -zr 0 1 -nr 1 -nc 3           3d
-zx {{zax}} -zr 0 1 -nr 1 -nc 1 -ss 0.143 3d
-zx {{zax}} -zr 0 1 -nr 1 -nc 2 -ss 0.143 3d
-zx {{zax}} -zr 0 1 -nr 1 -nc 3 -ss 0.143 3d

# slice labels
-zx {{zax}}           -ll       -zr 0 1 3d -b 30
-zx {{zax}}           -sp none  -zr 0 1 3d -b 30
-zx {{zax}}           -sp voxel -zr 0 1 3d -b 30
-zx {{zax}}           -sp world -zr 0 1 3d -b 30
-zx {{zax}} -ds world -sp voxel -zr 0 1 3d -b 30
-zx {{zax}} -ds world -sp world -zr 0 1 3d -b 30

# slice labels with weird voxel2world affine
-zx {{zax}}           -sp voxel -zr 0 1 {{swapdim('3d', '-z', 'x',  'y')}} -b 30
-zx {{zax}}           -sp world -zr 0 1 {{swapdim('3d', '-z', 'x',  'y')}} -b 30
-zx {{zax}} -ds world -sp voxel -zr 0 1 {{swapdim('3d', '-z', 'x',  'y')}} -b 30
-zx {{zax}} -ds world -sp world -zr 0 1 {{swapdim('3d', '-z', 'x',  'y')}} -b 30
-zx {{zax}}           -sp voxel -zr 0 1 {{swapdim('3d', '-y', 'z', '-x')}} -b 30
-zx {{zax}}           -sp world -zr 0 1 {{swapdim('3d', '-y', 'z', '-x')}} -b 30
-zx {{zax}} -ds world -sp voxel -zr 0 1 {{swapdim('3d', '-y', 'z', '-x')}} -b 30
-zx {{zax}} -ds world -sp world -zr 0 1 {{swapdim('3d', '-y', 'z', '-x')}} -b 30

# slice overlap+reverse
-zx {{zax}} -so 30 -zr 0 1     3d
-zx {{zax}} -so 30 -zr 0 1 -hs 3d
-zx {{zax}} -so 30 -zr 0 1 -sg 3d
-zx {{zax}} -so 30 -zr 0 1 -ro 3d

# overlap regression test (see fsl/fsleyes/fsleyes!403)
-zx {{zax}} -so 50 -zr 0 1 3d 3d -cm red-yellow -cr 5000 10000
# overlap regression test (see fsl/fsleyes/fsleyes!424)
-zx {{zax}} -so 50 -zr 0 1 3d 3d -ot mask -o -mc 0.7 0.1 0.1 -w 4 -t 5000 8000

# reverse slices
-zx {{zax}} -so 30 -zr 0 1 -rs 3d
-zx {{zax}} -nr 1  -zr 0 1 -rs 3d

# zrange/spacing as voxels (--asVoxels / -av)
-zx {{zax}} -av -zr  0 25       {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -av -zr 10 30       {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -av -zr 25 49       {{set_zax('numbers.nii.gz', zax)}}

-zx {{zax}} -av -zr  0 25 -ss 2 {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -av -zr 10 30 -ss 2 {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -av -zr 25 49 -ss 2 {{set_zax('numbers.nii.gz', zax)}}

-zx {{zax}} -av -zr  0 25 -ss 3 {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -av -zr 10 30 -ss 3 {{set_zax('numbers.nii.gz', zax)}}
-zx {{zax}} -av -zr 25 49 -ss 3 {{set_zax('numbers.nii.gz', zax)}}
"""

def set_zax(fname, zax):

    zax  = int(zax)
    data = Image(fname).data

    if   zax == 0: data = np.flip(data.transpose((2, 0, 1)), 1)
    elif zax == 1: data = data.transpose((0, 2, 1))
    else:          return fname

    fname = f'{removeExt(fname)}_zax_{zax}.nii.gz'
    Image(data).save(fname)

    return fname


def test_render_lightbox_1():
    extras = {
        'roi' : roi,
    }
    run_cli_tests('test_render_lightbox_1', cli_tests,
                  extras=extras, scene='lightbox', threshold=5)


@pytest.mark.parametrize('zax', '012')
def test_render_lightbox_2(zax):
    extras = {
        'roi'     : roi,
        'set_zax' : set_zax,
        'zax'     : zax,
        'swapdim' : swapdim

    }
    run_cli_tests('test_render_lightbox_2', cli_tests_parametrize_zax,
                  extras=extras, scene='lightbox', threshold=1)
