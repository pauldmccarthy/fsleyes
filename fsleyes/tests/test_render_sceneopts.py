#!/usr/bin/env python
#
# test_render_sceneopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import pytest

import numpy   as np
import nibabel as nib

import fsl.data.image as fslimage

from fsleyes.tests import run_cli_tests, zero_centre, haveFSL


pytestmark = pytest.mark.clitest


cli_tests = """
-hc            3d.nii.gz -cr 4000 6000
-bg 1 0.8 0.76 3d.nii.gz -cr 4000 6000
-cc 1 0.8 0.76 3d.nii.gz -cr 4000 6000

-cb                               3d.nii.gz
-cb -cbl top                      3d.nii.gz
-cb -cbl left                     3d.nii.gz
-cb -cbl right                    3d.nii.gz
-cb -cbl bottom                   3d.nii.gz
-cb -cbl top    -cbs bottom-right 3d.nii.gz -cm hot
-cb -cbl top    -cbs top-left     3d.nii.gz -cm hot
-cb -cbl left   -cbs bottom-right 3d.nii.gz -cm hot
-cb -cbl left   -cbs top-left     3d.nii.gz -cm hot
-cb -cbl right  -cbs bottom-right 3d.nii.gz -cm hot
-cb -cbl right  -cbs top-left     3d.nii.gz -cm hot
-cb -cbl bottom -cbs bottom-right 3d.nii.gz -cm hot
-cb -cbl bottom -cbs top-left     3d.nii.gz -cm hot

-cb -ls 4  3d.nii.gz
-cb -ls 10 3d.nii.gz
-cb -ls 20 3d.nii.gz
-cb -ls 40 3d.nii.gz

-cb {{zero_centre('3d.nii.gz')}} -cm red-yellow -un -nc blue-lightblue
-cb {{zero_centre('3d.nii.gz')}} -cm red-yellow -un -nc blue-lightblue -i

-cb {{zero_centre('3d.nii.gz')}} -cm hot -cmr 4
-cb {{zero_centre('3d.nii.gz')}} -cm hot -cmr 4 -inc

# cmap has res 5
# default res is 256
-cb 3d.nii.gz -cm {{gen_cmap()}}
-cb 3d.nii.gz -cm {{gen_cmap()}} -cmr 16
-cb 3d.nii.gz -cm {{gen_cmap()}}         -inc
-cb 3d.nii.gz -cm {{gen_cmap()}} -cmr 16 -inc

# Colour bar for other overlay types
-cb gifti/white.surf.gii -vd gifti/data3d.txt -cm hot
-cb tractogram/spirals.trk -co vdata -cm hsv

# default display/clipping range as percentiles
-idr 50   100% 3d.nii.gz
-idr 1993 5000 3d.nii.gz

-vl  3   3  3  3d.nii.gz -cr 4000 5000
-wl 10 -26 16  3d.nii.gz -cr 4000 5000

# cmapCycle
-cy 3d.nii.gz 3d.nii.gz -cr 4500 8000 3d.nii.gz -cr 6000 8000

# ungroup overlays
   -ni 3d.nii.gz -in linear 3d.nii.gz -cm red-yellow -cr 5000 8000
-u -ni 3d.nii.gz -in linear 3d.nii.gz -cm red-yellow -cr 5000 8000
"""


fsl_cli_tests = """
-idr 2500 7500 -std
-idr 50   100% -std
-idr 50   100% -stdb
-idr 50   100% -std1mm
-idr 50   100% -std1mmb
"""


def gen_cmap():
    cmap = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1]])
    np.savetxt('custom.cmap', cmap)
    return 'custom.cmap'


extras = {
    'zero_centre' : zero_centre,
    'gen_cmap'    : gen_cmap,
}


def test_render_sceneopts_ortho():
    tests = [t for t in cli_tests.split('\n') if 'tractogram' not in t]
    tests = '\n'.join(tests)
    run_cli_tests('test_render_sceneopts_ortho',
                  tests,
                  extras=extras,
                  scene='ortho',
                  threshold=15)


def test_render_sceneopts_lightbox():
    tests = [t for t in cli_tests.split('\n') if 'tractogram' not in t]
    tests = '\n'.join(tests)
    run_cli_tests('test_render_sceneopts_lightbox',
                  tests,
                  extras=extras,
                  scene='lightbox')


def test_render_sceneopts_3d():
    tests = [t.strip() for t in cli_tests.split('\n')]
    tests = [t for t in tests if (t != '') and (t[0] != '#')]
    tests = '\n'.join(['-dl {}'.format(t) for t in tests])

    run_cli_tests('test_render_sceneopts_3d',
                  tests,
                  extras=extras,
                  scene='3d')


@pytest.mark.skipif('not haveFSL()')
def test_render_fsl_sceneopts_ortho():
    run_cli_tests('test_render_fsl_sceneopts_ortho',
                  fsl_cli_tests,
                  extras=extras,
                  scene='ortho')


@pytest.mark.skipif('not haveFSL()')
def test_render_fsl_sceneopts_lightbox():
    run_cli_tests('test_render_fsl_sceneopts_lightbox',
                  fsl_cli_tests,
                  extras=extras,
                  scene='lightbox')


@pytest.mark.skipif('not haveFSL()')
def test_render_fsl_sceneopts_3d():
    tests = [t.strip() for t in fsl_cli_tests.split('\n')]
    tests = [t for t in tests if (t != '') and (t[0] != '#')]
    tests = '\n'.join(['-dl {}'.format(t) for t in tests])

    run_cli_tests('test_render_fsl_sceneopts_3d',
                  tests,
                  extras=extras,
                  scene='3d')
