#!/usr/bin/env python
#
# test_render_3d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from unittest import mock

import pytest

from fsleyes.tests import run_cli_tests, haveGL21


pytestmark = pytest.mark.clitest


# we add -in linear, because GL21 defaults to spline,
# which is not available in GL14 (and add -dl because
# lighthing is not implemented in GL14 either)
cli_tests = """
-dl -z 25   3d.nii.gz -in linear
-dl -z 50   3d.nii.gz -in linear
-dl -z 100  3d.nii.gz -in linear
-dl -z 1500 3d.nii.gz -in linear
-dl -he     3d.nii.gz -in linear

-dl -cb -ls 20 3d.nii.gz -in linear

                  gifti/white.surf.gii -mc 1 0 0
-dl               gifti/white.surf.gii -mc 1 0 0
-lp  200  0   0   gifti/white.surf.gii -mc 1 0 0
-lp -200  0   0   gifti/white.surf.gii -mc 1 0 0
-lp  0    200 0   gifti/white.surf.gii -mc 1 0 0
-lp  0   -200 0   gifti/white.surf.gii -mc 1 0 0
-lp  0    0   200 gifti/white.surf.gii -mc 1 0 0
-lp  0    0  -200 gifti/white.surf.gii -mc 1 0 0

-off  0    0   mesh_l_thal.vtk -mc 1 0 0
-off  0.5  0.5 mesh_l_thal.vtk -mc 1 0 0
-off  0.5 -0.5 mesh_l_thal.vtk -mc 1 0 0
-off -0.5  0.5 mesh_l_thal.vtk -mc 1 0 0
-off -0.5 -0.5 mesh_l_thal.vtk -mc 1 0 0

-rot  45   0   0 gifti/white.surf.gii -mc 1 0 0
-rot -45   0   0 gifti/white.surf.gii -mc 1 0 0
-rot   0  45   0 gifti/white.surf.gii -mc 1 0 0
-rot   0 -45   0 gifti/white.surf.gii -mc 1 0 0
-rot   0   0  45 gifti/white.surf.gii -mc 1 0 0
-rot   0   0 -45 gifti/white.surf.gii -mc 1 0 0

-rot  45  45   0 gifti/white.surf.gii -mc 1 0 0
-rot  45 -45   0 gifti/white.surf.gii -mc 1 0 0
-rot -45 -45  45 gifti/white.surf.gii -mc 1 0 0
-rot -45 -45 -45 gifti/white.surf.gii -mc 1 0 0
"""

cli_blend_tests = """
-dl                  3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
-dl -rot  45   0   0 3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
-dl -rot  45   45  0 3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
-dl -rot -45   0   0 3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
-dl -rot   0  45   0 3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
-dl -rot   0 -45   0 3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
-dl -rot   0   0  45 3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
-dl -rot   0   0 -45 3d.nii.gz -in linear  3d.nii.gz -in linear -cr 6300 8000 -cm red-yellow
"""


def test_render_3d():
    extras = {
    }
    run_cli_tests('test_render_3d', cli_tests, extras=extras, scene='3d')


# 3D overlay blending not implemented in GL14
@pytest.mark.skipif('not haveGL21()')
def test_render_3d_blending():
    extras = {
    }
    run_cli_tests('test_render_3d_blending',
                  cli_blend_tests, extras=extras, scene='3d')


# regression test - use of depth texture on
# environments without float textures would
# cause an error because the texture normalise
# flag would not be set
def test_render_3d_no_float_textures():

    with mock.patch('fsleyes.gl.textures.data.canUseFloatTextures',
                    return_value=(False, None, None)):
        run_cli_tests('test_render_3d_no_float_textures',
                      '-dl 3d.nii.gz -in linear',
                      scene='3d')
