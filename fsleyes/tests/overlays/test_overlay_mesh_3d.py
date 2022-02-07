#!/usr/bin/env python
#
# test_overlay_mesh_3d.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests, invert


pytestmark = pytest.mark.overlayclitest


cli_tests = """
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -wf

-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100 -ic
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100     -dc
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data3d.txt -cr 50 100 -ic -dc

# timeseries
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data4d.txt
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv -vd gifti/data4d.txt -vdi 2

# modulate alpha options
-s3d gifti/white.surf.gii -vd gifti/data3d.txt -mc 0.7 0.7 0.7 -cm hot -ma
-s3d gifti/white.surf.gii -vd gifti/data3d.txt -mc 0.7 0.7 0.7 -cm hot -ma -mr  1 50
-s3d gifti/white.surf.gii -vd gifti/data3d.txt -mc 0.7 0.7 0.7 -cm hot -ma -mr 50 99

-s3d gifti/white.surf.gii -vd gifti/data3d.txt -mc 0.7 0.7 0.7 -cm hot -ma           -md {{invert('gifti/data3d.txt')}}
-s3d gifti/white.surf.gii -vd gifti/data3d.txt -mc 0.7 0.7 0.7 -cm hot -ma -mr  1 50 -md {{invert('gifti/data3d.txt')}}
-s3d gifti/white.surf.gii -vd gifti/data3d.txt -mc 0.7 0.7 0.7 -cm hot -ma -mr 50 99 -md {{invert('gifti/data3d.txt')}}

# nn interp
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv       -vd gifti/data3d.txt -in nearest
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -ul -l random -vd gifti/data3d.txt -in nearest
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv       -vd gifti/data4d.txt -in nearest
-s3d gifti/white.surf.gii -mc 0.7 0.7 0.7 -cm hsv       -vd gifti/data4d.txt -in nearest -vdi 2

# 2D meshes. We disable lighting, because
# the GL14 lighting model is unable to
# distinguish between front and back
# faces (this is not possible with the
# ARB_fragment_program extension)
-s3d -dl -rot  45  45  45 mesh_2d_x.vtk -mc 1 0 0 mesh_2d_y.vtk -mc 0 1 0 mesh_2d_z.vtk -mc 0 0 1
-s3d -dl -rot -45 -45 -45 mesh_2d_x.vtk -mc 1 0 0 mesh_2d_y.vtk -mc 0 1 0 mesh_2d_z.vtk -mc 0 0 1
-s3d -dl -rot  45  45  45 mesh_2d_x.vtk -cm blue-lightblue -vd mesh_2d_data.txt mesh_2d_y.vtk -cm red-yellow -vd mesh_2d_data.txt  mesh_2d_z.vtk -cm green -vd mesh_2d_data.txt
-s3d -dl -rot -45 -45 -45 mesh_2d_x.vtk -cm blue-lightblue -vd mesh_2d_data.txt mesh_2d_y.vtk -cm red-yellow -vd mesh_2d_data.txt  mesh_2d_z.vtk -cm green -vd mesh_2d_data.txt
"""

def test_overlay_mesh_3d():
    extras = {
        'invert' : invert
    }
    run_cli_tests('test_overlay_mesh_3d', cli_tests, extras=extras)
