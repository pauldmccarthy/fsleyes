#!/usr/bin/env python
#
# test_overlay_sh.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest


from fsleyes.tests import run_cli_tests, haveGL21


pytestmark = pytest.mark.overlayclitest


cli_tests = """
# FOD resolution
sh -ot sh -sr 3
sh -ot sh -sr 4
sh -ot sh -sr 5
sh -ot sh -sr 6
sh -ot sh -sr 7
sh -ot sh -sr 8
sh -ot sh -sr 9
sh -ot sh -sr 10

# FOD SH order
sh -ot sh -so 0
sh -ot sh -so 1
sh -ot sh -so 2
sh -ot sh -so 3
sh -ot sh -so 4
sh -ot sh -so 5
sh -ot sh -so 6
sh -ot sh -so 7
sh -ot sh -so 8

# SH order for symmetric FODs.
sh_sym -ot sh -so 0
sh_sym -ot sh -so 2
sh_sym -ot sh -so 4
sh_sym -ot sh -so 6
sh_sym -ot sh -so 8

# FOD size
sh -ot sh -s 10
sh -ot sh -s 50
sh -ot sh -s 100
sh -ot sh -s 250
sh -ot sh -s 500

# normalise FOD size
sh -ot sh -no
sh -ot sh -no -s 50
sh -ot sh -no -s 100
sh -ot sh -no -s 250

# Radius threshold
sh -ot sh -t 0.0
sh -ot sh -t 0.25
sh -ot sh -t 0.5
sh -ot sh -t 0.8

# Lighting
sh -ot sh -l # Normal vectors are currently broken

# Regression test - make sure radii are scaled correctly at all zoom levels
-xz 100  -yz 100  -zz 100  sh_sym_FA sh_sym -ot sh
-xz 500  -yz 500  -zz 500  sh_sym_FA sh_sym -ot sh
-xz 1000 -yz 1000 -zz 1000 sh_sym_FA sh_sym -ot sh
-xz 2500 -yz 2500 -zz 2500 sh_sym_FA sh_sym -ot sh

# Colour by radius instead of direction
sh -ot sh -m radius -cm hot
"""


@pytest.mark.skipif('not haveGL21()')
def test_overlay_sh():
    extras = {
    }
    run_cli_tests('test_overlay_sh', cli_tests, extras=extras)
