#!/usr/bin/env python
#
# test_overlay_displayprops.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

from fsleyes.tests import run_cli_tests, discretise


pytestmark = pytest.mark.overlayclitest


cli_tests = """
3d.nii.gz
3d.nii.gz -ot volume
3d.nii.gz -d
3d.nii.gz -a 50
3d.nii.gz -a 50 -b 75
3d.nii.gz -a 50       -c 25
3d.nii.gz -a 50 -b 75 -c 25
3d.nii.gz       -b 75
3d.nii.gz       -b 75 -c 25
3d.nii.gz             -c 25

3d.nii.gz -ot mask
3d.nii.gz -ot mask -d
3d.nii.gz -ot mask -a 50
3d.nii.gz -ot mask -a 50 -b 75
3d.nii.gz -ot mask -a 50       -c 25
3d.nii.gz -ot mask -a 50 -b 75 -c 25
3d.nii.gz -ot mask       -b 75
3d.nii.gz -ot mask       -b 75 -c 25
3d.nii.gz -ot mask             -c 25

{{discretise('3d.nii.gz', 500)}} -ot label
{{discretise('3d.nii.gz', 500)}} -ot label -d
{{discretise('3d.nii.gz', 500)}} -ot label -a 50
{{discretise('3d.nii.gz', 500)}} -ot label -a 50 -b 75
{{discretise('3d.nii.gz', 500)}} -ot label -a 50       -c 25
{{discretise('3d.nii.gz', 500)}} -ot label -a 50 -b 75 -c 25
{{discretise('3d.nii.gz', 500)}} -ot label       -b 75
{{discretise('3d.nii.gz', 500)}} -ot label       -b 75 -c 25
{{discretise('3d.nii.gz', 500)}} -ot label             -c 25

dti/dti_V1 -ot rgbvector
dti/dti_V1 -ot rgbvector -d
dti/dti_V1 -ot rgbvector -a 50
dti/dti_V1 -ot rgbvector -a 50 -b 75
dti/dti_V1 -ot rgbvector -a 50 -b 75 -c 25
dti/dti_V1 -ot rgbvector       -b 75
dti/dti_V1 -ot rgbvector       -b 75 -c 25
dti/dti_V1 -ot rgbvector             -c 25


dti/dti_V1 -ot linevector
dti/dti_V1 -ot linevector -d
dti/dti_V1 -ot linevector -a 50
dti/dti_V1 -ot linevector -a 50 -b 75
dti/dti_V1 -ot linevector -a 50 -b 75 -c 25
dti/dti_V1 -ot linevector       -b 75
dti/dti_V1 -ot linevector       -b 75 -c 25
dti/dti_V1 -ot linevector             -c 25

dti -ot tensor
dti -ot tensor -d
dti -ot tensor -a 50
dti -ot tensor -a 50 -b 75
dti -ot tensor -a 50 -b 75 -c 25
dti -ot tensor       -b 75
dti -ot tensor       -b 75 -c 25
dti -ot tensor             -c 25

mesh_l_thal.vtk          -mc 1 0 0
mesh_l_thal.vtk -ot mesh -mc 1 0 0
mesh_l_thal.vtk -ot mesh -mc 1 0 0  -d
mesh_l_thal.vtk -ot mesh -mc 1 0 0  -a 50
mesh_l_thal.vtk -ot mesh -mc 1 0 0  -a 50 -b 75
mesh_l_thal.vtk -ot mesh -mc 1 0 0  -a 50 -b 75 -c 25
mesh_l_thal.vtk -ot mesh -mc 1 0 0        -b 75
mesh_l_thal.vtk -ot mesh -mc 1 0 0        -b 75 -c 25
mesh_l_thal.vtk -ot mesh -mc 1 0 0              -c 25

sh -ot sh
sh -ot sh -d
sh -ot sh -a 50
sh -ot sh -a 50 -b 75
sh -ot sh -a 50 -b 75 -c 25
sh -ot sh       -b 75
sh -ot sh       -b 75 -c 25
sh -ot sh             -c 25

gifti/white.surf.gii          -mc 1 0 0
gifti/white.surf.gii -ot mesh -mc 1 0 0
gifti/white.surf.gii -ot mesh -mc 1 0 0  -d
gifti/white.surf.gii -ot mesh -mc 1 0 0  -a 50
gifti/white.surf.gii -ot mesh -mc 1 0 0  -a 50 -b 75
gifti/white.surf.gii -ot mesh -mc 1 0 0  -a 50 -b 75 -c 25
gifti/white.surf.gii -ot mesh -mc 1 0 0        -b 75
gifti/white.surf.gii -ot mesh -mc 1 0 0        -b 75 -c 25
gifti/white.surf.gii -ot mesh -mc 1 0 0              -c 25

freesurfer/lh.pial          -mc 1 0 0
freesurfer/lh.pial -ot mesh -mc 1 0 0
freesurfer/lh.pial -ot mesh -mc 1 0 0 -d
freesurfer/lh.pial -ot mesh -mc 1 0 0 -a 50
freesurfer/lh.pial -ot mesh -mc 1 0 0 -a 50 -b 75
freesurfer/lh.pial -ot mesh -mc 1 0 0 -a 50 -b 75 -c 25
freesurfer/lh.pial -ot mesh -mc 1 0 0       -b 75
freesurfer/lh.pial -ot mesh -mc 1 0 0       -b 75 -c 25
freesurfer/lh.pial -ot mesh -mc 1 0 0             -c 25
"""


def test_overlay_displayprops():
    extras = {
        'discretise' : discretise,
    }
    run_cli_tests('test_overlay_displayprops', cli_tests, extras=extras)
