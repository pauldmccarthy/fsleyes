#!/usr/bin/env python
#
# test_overlay_tensor.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest
import fsl.data.image as fslimage

from . import run_cli_tests


pytestmark = pytest.mark.overlaytest


cli_tests = """
# Test tensors displayed as rgb/line vectors
dti -ot rgbvector
dti -ot linevector

dti -dl
dti -tr 4
dti -tr 10
dti -tr 20

dti -s 50
dti -s 100
dti -s 600
"""


def test_overlay_tensor():
    extras = {
    }
    run_cli_tests('test_overlay_tensor', cli_tests, extras=extras)
