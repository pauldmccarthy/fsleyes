#!/usr/bin/env python
#
# test_render_ortho.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests


pytestmark = pytest.mark.clitest


cli_tests = """
                             3d.nii.gz
-lo grid                     3d.nii.gz
-lo grid       -xh           3d.nii.gz
-lo grid       -xh -yh       3d.nii.gz
-lo grid       -xh -yh -zh   3d.nii.gz
-lo grid           -yh       3d.nii.gz
-lo grid           -yh -zh   3d.nii.gz
-lo grid               -zh   3d.nii.gz
-lo horizontal               3d.nii.gz
-lo horizontal -xh           3d.nii.gz
-lo horizontal -xh -yh       3d.nii.gz
-lo horizontal -xh -yh -zh   3d.nii.gz
-lo horizontal     -yh       3d.nii.gz
-lo horizontal     -yh -zh   3d.nii.gz
-lo horizontal         -zh   3d.nii.gz
-lo vertical                 3d.nii.gz
-lo vertical   -xh           3d.nii.gz
-lo vertical   -xh -yh       3d.nii.gz
-lo vertical   -xh -yh -zh   3d.nii.gz
-lo vertical       -yh       3d.nii.gz
-lo vertical       -yh -zh   3d.nii.gz
-lo vertical           -zh   3d.nii.gz

# alpha blending
mesh_ref mesh_l_thal.vtk -mc 0 1 0 -r mesh_ref -a 50

-cb -ls 20 3d.nii.gz

-cg -xz 2000 -yz 2000 -zz 2000 3d.nii.gz

-hl                        3d.nii.gz
-xz 1000                   3d.nii.gz
         -yz 1000          3d.nii.gz
                  -zz 1000 3d.nii.gz
-xz 1000 -yz 1000 -zz 1000 3d.nii.gz

-xz 1000 -xc   0.5 0.5 3d.nii.gz
-yz 1000 -yc  -0.5 0.2 3d.nii.gz
-zz 1000 -zc  -0.8 0.6 3d.nii.gz

-hl    3d.nii.gz # Labels should be hidden
-ls 4  3d.nii.gz # Labels should be tiny
-ls 4  3d.nii.gz # Labels should be tiny
-ls 20 3d.nii.gz # Labels should be big
-ls 96 3d.nii.gz # Labels should be huge
-ls 96 3d.nii.gz # Labels should be huge

         -no -ls 96 3d.nii.gz # Neuro orientation
-lo grid     -ls 96 3d.nii.gz # Sagittal plane should be a/p flipped
-lo grid -no -ls 96 3d.nii.gz # Neuro orientation, and sagittal plane should be a/p flipped

-hl -z 50 -c 0  -bg 0.2 0.2 0.2 3d.nii.gz
-hl -z 50 -c 10 -bg 0.2 0.2 0.2 3d.nii.gz

-ixh -ixv -iyh -iyv -izh -izv 3d.nii.gz

-a annotations.txt 3d
"""


def test_render_ortho():
    extras = {
    }
    run_cli_tests('test_render_ortho', cli_tests, extras=extras, scene='ortho')
