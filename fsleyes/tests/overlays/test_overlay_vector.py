#!/usr/bin/env python
#
# test_overlay_vector.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import pytest
import fsl.data.image as fslimage

from fsleyes.tests import run_cli_tests


pytestmark = pytest.mark.overlayclitest


cli_tests = """
############
# RGB vector
############

# X/Y/Z colours and suppression
dti/dti_V1 -ot rgbvector -xc 1 1 0
dti/dti_V1 -ot rgbvector -yc 1 1 0
dti/dti_V1 -ot rgbvector -zc 1 1 0
dti/dti_V1 -ot rgbvector -xs
dti/dti_V1 -ot rgbvector -xs -ys
dti/dti_V1 -ot rgbvector     -ys
dti/dti_V1 -ot rgbvector     -ys -zs
dti/dti_V1 -ot rgbvector         -zs
dti/dti_V1 -ot rgbvector -xs -sm white
dti/dti_V1 -ot rgbvector -xs -sm black
dti/dti_V1 -ot rgbvector -xs -sm transparent

# Clipping
              dti/dti_V1 -ot rgbvector -cl dti/dti_FA -cr 0.5 1.0
dti/dti_FA -d dti/dti_V1 -ot rgbvector -cl dti_FA     -cr 0.5 1.0
              dti/dti_V1 -ot rgbvector -cl dti/dti_FA

# Colouring
              dti/dti_V1 -ot rgbvector -co dti/dti_FA -b 70 -c 90
dti/dti_FA -d dti/dti_V1 -ot rgbvector -co dti_FA     -b 70 -c 90

# Modulation
           dti/dti_V1 -ot rgbvector -mo dti/dti_FA -mr 0 0.5
dti/dti_FA dti/dti_V1 -ot rgbvector -mo dti_FA     -mr 0 0.5
dti/dti_FA dti/dti_V1 -ot rgbvector -mo dti_FA

           dti/dti_V1 -ot rgbvector -mo dti/dti_FA -mr 0 0.5 -mm alpha
dti/dti_FA dti/dti_V1 -ot rgbvector -mo dti_FA     -mr 0 0.5 -mm alpha
dti/dti_FA dti/dti_V1 -ot rgbvector -mo dti_FA               -mm alpha

#############
# Line vector
#############


# X/Y/Z colours and suppression
dti/dti_V1 -ot linevector -xc 1 1 0
dti/dti_V1 -ot linevector -yc 1 1 0
dti/dti_V1 -ot linevector -zc 1 1 0
dti/dti_V1 -ot linevector -xs
dti/dti_V1 -ot linevector -xs -ys
dti/dti_V1 -ot linevector     -ys
dti/dti_V1 -ot linevector     -ys -zs
dti/dti_V1 -ot linevector         -zs
dti/dti_V1 -ot linevector -xs -sm white
dti/dti_V1 -ot linevector -xs -sm black
dti/dti_V1 -ot linevector -xs -sm transparent

# Clipping
              dti/dti_V1 -ot linevector -cl dti/dti_FA -cr 0.5 1.0
dti/dti_FA -d dti/dti_V1 -ot linevector -cl dti_FA     -cr 0.5 1.0
              dti/dti_V1 -ot linevector -cl dti/dti_FA

# Colouring
              dti/dti_V1 -ot linevector -co dti/dti_FA -b 70 -c 90
dti/dti_FA -d dti/dti_V1 -ot linevector -co dti_FA     -b 70 -c 90

# Modulation
           dti/dti_V1 -ot linevector -mo dti/dti_FA -mr 0 0.5
dti/dti_FA dti/dti_V1 -ot linevector -mo dti_FA     -mr 0 0.5
dti/dti_FA dti/dti_V1 -ot linevector -mo dti_FA

           dti/dti_V1 -ot linevector -mo dti/dti_FA -mr 0 0.5 -mm alpha
dti/dti_FA dti/dti_V1 -ot linevector -mo dti_FA     -mr 0 0.5 -mm alpha
dti/dti_FA dti/dti_V1 -ot linevector -mo dti_FA               -mm alpha

########
# Tensor
########

# X/Y/Z colours and suppression
dti -ot tensor -xc 1 1 0
dti -ot tensor -yc 1 1 0
dti -ot tensor -zc 1 1 0
dti -ot tensor -xs
dti -ot tensor -xs -ys
dti -ot tensor     -ys
dti -ot tensor     -ys -zs
dti -ot tensor         -zs
dti -ot tensor -xs -sm white
dti -ot tensor -xs -sm black
dti -ot tensor -xs -sm transparent

# Clipping
              dti -ot tensor -cl dti/dti_FA -cr 0.5 1.0
dti/dti_FA -d dti -ot tensor -cl dti_FA     -cr 0.5 1.0
              dti -ot tensor -cl dti/dti_FA

# Colouring
              dti -ot tensor -co dti/dti_FA -b 70 -c 90
dti/dti_FA -d dti -ot tensor -co dti_FA     -b 70 -c 90

# Modulation
           dti -ot tensor -mo dti/dti_FA -mr 0 0.5
dti/dti_FA dti -ot tensor -mo dti_FA     -mr 0 0.5
dti/dti_FA dti -ot tensor -mo dti_FA
           dti -ot tensor -mo dti/dti_FA -mr 0 0.5 -mm alpha
dti/dti_FA dti -ot tensor -mo dti_FA     -mr 0 0.5 -mm alpha
dti/dti_FA dti -ot tensor -mo dti_FA               -mm alpha

####
# SH
####

# X/Y/Z colours and suppression
sh -ot sh -xc 1 1 0
sh -ot sh -yc 1 1 0
sh -ot sh -zc 1 1 0
sh -ot sh -xs
sh -ot sh -xs -ys
sh -ot sh     -ys
sh -ot sh     -ys -zs
sh -ot sh         -zs
sh -ot sh -xs -sm white
sh -ot sh -xs -sm black
sh -ot sh -xs -sm transparent

# Clipping
             sh_sym -ot sh -cl sh_sym_FA -cr 0.5 1.0
sh_sym_FA -d sh_sym -ot sh -cl sh_sym_FA -cr 0.5 1.0
             sh_sym -ot sh -cl sh_sym_FA

# Colouring
             sh_sym -ot sh -co sh_sym_FA -b 70 -c 90
sh_sym_FA -d sh_sym -ot sh -co sh_sym_FA -b 70 -c 90

# Modulation
          sh_sym -ot sh -mo sh_sym_FA -mr 0 0.5
sh_sym_FA sh_sym -ot sh -mo sh_sym_FA -mr 0 0.5
sh_sym_FA sh_sym -ot sh -mo sh_sym_FA
          sh_sym -ot sh -mo sh_sym_FA -mr 0 0.5 -mm alpha
sh_sym_FA sh_sym -ot sh -mo sh_sym_FA -mr 0 0.5 -mm alpha
sh_sym_FA sh_sym -ot sh -mo sh_sym_FA           -mm alpha
"""


def test_overlay_vector():
    extras = {
    }
    run_cli_tests('test_overlay_vector', cli_tests, extras=extras)
