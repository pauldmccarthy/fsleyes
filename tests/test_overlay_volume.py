#!/usr/bin/env python
#
# test_overlay_volume.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest


pytestmark = pytest.mark.overlaytest


from . import run_cli_tests


cli_tests = """
3d.nii.gz -dr -5000 500
3d.nii.gz -dr -5000 500 -i
3d.nii.gz -dr -5000 500 -b 1 -c 5 # -dr should override -b/-c
3d.nii.gz -dr -5000 500 -cr -3000  1000
3d.nii.gz -dr -5000 500 -cr -3000 -1000 -ic
3d.nii.gz -dr -5000 500 -cr -3000 -1000 -ll   # low ranges are linked - -cr overrides -dr
3d.nii.gz -dr -5000 500 -cr -3000 -1000 -ll -ic
3d.nii.gz -dr -5000 500 -cr -3000 -1000 -ll -lh  # high ranges are linked - -cr overrides -dr
3d.nii.gz -dr -5000 500 -cr -3000 -1000 -ll -lh -ic
"""

_ = """
-sortho MNI152_T1_2mm.nii.gz -dr 20 80%
-sortho MNI152_T1_2mm.nii.gz -cr 20 80%

-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un -dr -1000 3000
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un -dr  0    3000
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un -dr  1000 3000

-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un -dr  1000 3000 -cr 500 4000
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un -dr  1000 3000 -cr 500 4000 -ll
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un -dr  1000 3000 -cr 500 4000 -lh
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm hot -nc cool -un -dr  1000 3000 -cr 500 4000 -ll -lh

-sortho -xz 750 -yz 750 -zz 750 MNI152_T1_2mm.nii.gz -in none
-sortho -xz 750 -yz 750 -zz 750 MNI152_T1_2mm.nii.gz -in linear
-sortho -xz 750 -yz 750 -zz 750 MNI152_T1_2mm.nii.gz -in spline

-sortho MNI152_T1_2mm_4D.nii.gz -v 0
-sortho MNI152_T1_2mm_4D.nii.gz -v 1
-sortho MNI152_T1_2mm_4D.nii.gz -v 2
-sortho MNI152_T1_2mm_4D.nii.gz -v 3
-sortho MNI152_T1_2mm_4D.nii.gz -v 4

-sortho MNI152_T1_2mm.nii.gz             -cl MNI152_T1_2mm_indices.nii.gz -cr 500000 1000000
-sortho MNI152_T1_2mm.nii.gz             -cl MNI152_T1_2mm_indices.nii.gz -cr 500000 1000000 -ic
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cl MNI152_T1_2mm_indices.nii.gz -cr 500000 1000000 -cm hot -nc cool -un
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cl MNI152_T1_2mm_indices.nii.gz -cr 500000 1000000 -cm hot -nc cool -un -ic

-sortho MNI152_T1_2mm.nii.gz             -cl MNI152_T1_2mm_offset.nii.gz  -cr 1600   10000   -cm hot
-sortho MNI152_T1_2mm.nii.gz             -cl MNI152_T1_2mm_offset.nii.gz  -cr 1600   10000   -cm hot -ic
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cl MNI152_T1_2mm_offset.nii.gz  -cr 1600   10000   -cm hot -nc cool -un
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cl MNI152_T1_2mm_offset.nii.gz  -cr 1600   10000   -cm hot -nc cool -un -ic

-sortho MNI152_T1_2mm_indices.nii.gz MNI152_T1_2mm.nii.gz -cl MNI152_T1_2mm_indices.nii.gz -cr 500000 1000000


-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 256
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 128
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 64
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 32
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 16
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 8
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 4
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 16  -i
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 8   -i
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 4   -i
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 256 -inc
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 128 -inc
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 64  -inc
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 32  -inc
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 16  -inc
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 8   -inc
-sortho MNI152_T1_2mm.nii.gz -cm hot -cmr 4   -inc

-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm red-yellow -un -nc blue-lightblue -cmr 6
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm red-yellow -un -nc blue-lightblue -cmr 6 -i
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm red-yellow -un -nc blue-lightblue -cmr 6 -inc
-sortho MNI152_T1_2mm_zero_centre.nii.gz -cm red-yellow -un -nc blue-lightblue -cmr 6 -inc -i
"""



def test_overlay_volume():
    run_cli_tests('test_overlay_volume', cli_tests)
