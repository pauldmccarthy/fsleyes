#!/usr/bin/env python
#
# test_overlay_complex.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from unittest import mock

from fsleyes.tests import run_cli_tests, complex


pytestmark = pytest.mark.overlayclitest


cli_tests = """
{{complex()}} -ot complex
{{complex()}} -ot complex -co real
{{complex()}} -ot complex -co imag
{{complex()}} -ot complex -co mag
{{complex()}} -ot complex -co phase
"""



def test_overlay_complex():
    extras = {
        'complex' : complex,
    }
    run_cli_tests('test_overlay_complex', cli_tests, extras=extras)



# Emulate a restricted GL environment
def test_overlay_complex_ssh_vnc():
    extras = {
        'complex' : complex,
    }
    with mock.patch('fsleyes.gl.textures.data.canUseFloatTextures',
                    return_value=(False, None, None)):
        run_cli_tests('test_overlay_complex', cli_tests, extras=extras)
