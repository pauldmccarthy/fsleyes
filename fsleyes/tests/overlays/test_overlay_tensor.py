#!/usr/bin/env python
#
# test_overlay_tensor.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest

from fsleyes.tests import run_cli_tests, haveGL21


pytestmark = pytest.mark.overlayclitest


cli_tests = """
# Test tensors displayed as rgb/line vectors
dti -ot rgbvector
dti -ot linevector

# default should be tensor
dti

dti -ot tensor -dl
dti -ot tensor -tr 4
dti -ot tensor -tr 10
dti -ot tensor -tr 20

dti -ot tensor -s 50
dti -ot tensor -s 100
dti -ot tensor -s 600
"""


@pytest.mark.skipif('not haveGL21()')
def test_overlay_tensor():
    extras = {
    }
    run_cli_tests('test_overlay_tensor', cli_tests, extras=extras)
