#!/usr/bin/env python
#
# test_overlay_complex.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from .. import run_cli_tests, complex


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
