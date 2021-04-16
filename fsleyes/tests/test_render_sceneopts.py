#!/usr/bin/env python
#
# test_render_sceneopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import pytest

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

# Colour bar for other overlay types
-cb gifti/white.surf.gii -vd gifti/data3d.txt -cm hot

-p 1 3d.nii.gz
-p 2 3d.nii.gz
-p 3 3d.nii.gz

# default display/clipping range as percentiles
-idr 50 100 3d.nii.gz

-vl  3   3  3  3d.nii.gz -cr 4000 5000
-wl 10 -26 16  3d.nii.gz -cr 4000 5000

# high-DPI (should have no effect in docker container)
-hd     3d.nii.gz
-hd -cb 3d.nii.gz
"""


# TODO either mock, or make sure FSL standards exist in CI
fsl_cli_tests = """
-idr 50 100 -std
-idr 50 100 -stdb
-idr 50 100 -std1mm
-idr 50 100 -std1mmb
"""



extras = {
    'zero_centre' : zero_centre
}


def test_render_sceneopts_ortho():
    run_cli_tests('test_render_sceneopts_ortho',
                  cli_tests,
                  extras=extras,
                  scene='ortho',
                  threshold=15)


def test_render_sceneopts_lightbox():
    run_cli_tests('test_render_sceneopts_lightbox',
                  cli_tests,
                  extras=extras,
                  scene='lightbox')


def test_render_sceneopts_3d():
    tests = []
    for t in cli_tests.split('\n'):
        if 'nii' in t:
            tests.append('-dl {}'.format(t))
        else:
            tests.append(t)
    tests = '\n'.join(tests)

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
