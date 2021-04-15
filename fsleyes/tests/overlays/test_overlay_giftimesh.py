#!/usr/bin/env python
#
# test_overlay_giftimesh.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

import nibabel as nib
import numpy   as np

from fsleyes.tests import run_cli_tests


pytestmark = pytest.mark.overlayclitest


cli_tests = """
gifti/white.surf.gii -mc 1 0 0
gifti/white.surf.gii -mc 1 0 0 -o
gifti/white.surf.gii -mc 1 0 0    -w 1
gifti/white.surf.gii -mc 1 0 0    -w 5
gifti/white.surf.gii -mc 1 0 0    -w 10
gifti/white.surf.gii -mc 1 0 0 -o -w 1
gifti/white.surf.gii -mc 1 0 0 -o -w 5
gifti/white.surf.gii -mc 1 0 0 -o -w 10
gifti/white.surf.gii -mc 1 0 0 -o -w 10 -cm hot -vd gifti/data3d.txt
gifti/white.surf.gii -mc 1 0 0 -o -w 10 -cm hot -vd gifti/data4d.txt
gifti/white.surf.gii -mc 1 0 0 -o -w 10 -cm hot -vd gifti/data4d.txt -vdi 3
{{vertexsets()}}     -mc 1 0 0
{{vertexsets()}}     -mc 1 0 0 -vs vertexsets.gii
{{vertexsets()}}     -mc 1 0 0 -vs vertexsets.gii_1
{{vertexsets()}}     -mc 1 0 0 -vs vertexsets.gii_1 -vd vertexsetdata.txt
{{vertexsets()}}     -mc 1 0 0 -vs vertexsets.gii   vertexsets.gii -mc 0 1 0 -vs vertexsets.gii_1
{{vertexsets()}}     -mc 1 0 0 -vd vertexsets.gii
"""  # noqa

def gen_multiple_vertexSets():
    verts1 = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]])
    verts2 = np.array(verts1 + 0.25)
    verts2[3, :] = [0.5, 0.5, 1.0]
    idxs = np.array([
        [0, 1, 2],
        [0, 3, 1],
        [0, 2, 3],
        [1, 3, 2]])
    vdata = np.array([1, 2, 3, 4])
    xdata = np.array([1, 2, 3, 4])

    verts1 = nib.gifti.GiftiDataArray(verts1, intent='NIFTI_INTENT_POINTSET')
    verts2 = nib.gifti.GiftiDataArray(verts2, intent='NIFTI_INTENT_POINTSET')
    idxs   = nib.gifti.GiftiDataArray(idxs,   intent='NIFTI_INTENT_TRIANGLE')
    vdata  = nib.gifti.GiftiDataArray(vdata,  intent='NIFTI_INTENT_SHAPE')
    gimg   = nib.gifti.GiftiImage(darrays=[verts1, verts2, idxs, vdata])

    gimg.to_filename('vertexsets.gii')

    np.savetxt('vertexsetdata.txt', xdata)

    return 'vertexsets.gii'


def test_overlay_giftimesh():
    extras = {
        'vertexsets' : gen_multiple_vertexSets
    }
    run_cli_tests('test_overlay_giftimesh',
                  cli_tests,
                  extras=extras,
                  threshold=25)
