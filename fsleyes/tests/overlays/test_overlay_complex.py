#!/usr/bin/env python
#
# test_overlay_complex.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from unittest import mock

import numpy as np

from fsl.utils.tempdir import tempdir
from fsl.data.image    import Image

from fsleyes.tests import (run_cli_tests,
                           run_with_orthopanel,
                           complex,
                           realYield)



cli_tests = """
{{complex()}} -ot complex
{{complex()}} -ot complex -co real
{{complex()}} -ot complex -co imag
{{complex()}} -ot complex -co mag
{{complex()}} -ot complex -co phase

# overlay type should actually be set
# automatically to "complex", so we
# don't need to specify it on the
# command-line.
{{complex()}}             -co phase

# check that volume/component are
# honoured, for 4D volumes
{{complex((10, 10, 10, 5))}} -co real  -v 2
{{complex((10, 10, 10, 5))}} -co imag  -v 2
{{complex((10, 10, 10, 5))}} -co mag   -v 2
{{complex((10, 10, 10, 5))}} -co phase -v 2
{{complex((10, 10, 10, 5))}} -co real  -v 4
{{complex((10, 10, 10, 5))}} -co imag  -v 4
{{complex((10, 10, 10, 5))}} -co mag   -v 4
{{complex((10, 10, 10, 5))}} -co phase -v 4
"""


@pytest.mark.overlayclitest
def test_overlay_complex():
    extras = {
        'complex' : complex,
    }
    run_cli_tests('test_overlay_complex', cli_tests, extras=extras)



# Emulate a restricted GL environment
@pytest.mark.overlayclitest
def test_overlay_complex_ssh_vnc():
    extras = {
        'complex' : complex,
    }
    with mock.patch('fsleyes.gl.textures.data.canUseFloatTextures',
                    return_value=(False, None, None)):
        run_cli_tests('test_overlay_complex', cli_tests, extras=extras)


# fsl/fsleyes/fsleyes!498
# Make sure that correct component (real/imag/mag/phase)
# is displayed when the volume is changed
def test_complex_4D_component_refresh():
    with tempdir():
        imgfile = complex((10, 10, 10, 10))
        run_with_orthopanel(_test_complex_4D_component_refresh, imgfile)

def _test_complex_4D_component_refresh(ortho, overlayList, displayCtx, imgfile):
    img = Image(imgfile)
    overlayList.append(img)
    opts = displayCtx.getOpts(img)

    realYield()

    globj = ortho.getXCanvas().getGLObject(img)

    texdata = globj.imageTexture.preparedData
    expdata = opts.getReal(img[..., 0])
    assert np.all(np.isclose(texdata, expdata))

    opts.component = "imag"
    realYield()
    texdata = globj.imageTexture.preparedData
    expdata = opts.getImaginary(img[..., 0])
    assert np.all(np.isclose(texdata, expdata))

    opts.volume = 1
    realYield()
    texdata = globj.imageTexture.preparedData
    expdata = opts.getImaginary(img[..., 1])
    assert np.all(np.isclose(texdata, expdata))

    opts.component = "mag"
    opts.volume = 3
    realYield()
    texdata = globj.imageTexture.preparedData
    expdata = opts.getMagnitude(img[..., 3])
    assert np.all(np.isclose(texdata, expdata))

    opts.volume = 4
    realYield()
    texdata = globj.imageTexture.preparedData
    expdata = opts.getMagnitude(img[..., 4])
    assert np.all(np.isclose(texdata, expdata))

    opts.component = 'phase'
    opts.volume = 5
    realYield()
    texdata = globj.imageTexture.preparedData
    expdata = opts.getPhase(img[..., 5])
    assert np.all(np.isclose(texdata, expdata))

    opts.volume = 6
    realYield()
    texdata = globj.imageTexture.preparedData
    expdata = opts.getPhase(img[..., 6])
    assert np.all(np.isclose(texdata, expdata))
