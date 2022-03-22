#!/usr/bin/env python
#
# test_overlay_tractogram.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from unittest import mock

import pytest

from fsleyes.tests import run_cli_tests, haveGL


pytestmark = pytest.mark.overlayclitest

prefix = '-s3d -z 40'

cli_tests = f"""
{prefix} tractogram/spirals.trk
{prefix} tractogram/spirals.trk -lw 3
{prefix} tractogram/spirals.trk -lw 5


# Colour/clip by data baked into the streamline file
{prefix} tractogram/spirals.trk -lw 5 -co vdata           -cm hsv -dr -0.75 0.75
{prefix} tractogram/spirals.trk -lw 5 -co vdata           -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} tractogram/spirals.trk -lw 5 -co sdata           -cm hsv -dr -0.75 0.75
{prefix} tractogram/spirals.trk -lw 5 -co sdata           -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} tractogram/spirals.trk -lw 5 -co vdata -cl sdata -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} tractogram/spirals.trk -lw 5 -co sdata -cl vdata -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} tractogram/spirals.trk -lw 5           -cl vdata -cm hsv                -cr -0.75 0.75

# neg cmap
{prefix} tractogram/spirals.trk -lw 5 -co vdata -cm red-yellow -nc blue-lightblue -un
{prefix} tractogram/spirals.trk -lw 5 -co vdata -cm red-yellow -nc blue-lightblue -un -dr 0.25 1

# code pathways for per-streamline/vertex data are
# more or less identical, so no need to test both
{prefix} tractogram/spirals.trk -lw 5 -co tractogram/spirals_streamline_data.txt
{prefix} tractogram/spirals.trk -lw 5 -co tractogram/spirals_vertex_data.txt
{prefix} tractogram/spirals.trk -lw 5 -co tractogram/spirals_vertex_data.txt -cm hsv
{prefix} tractogram/spirals.trk -lw 5 -co tractogram/spirals_vertex_data.txt -cm hsv -ll -dr 0 25 -cr 25 50
{prefix} tractogram/spirals.trk -lw 5 -co tractogram/spirals_vertex_data.txt -cl tractogram/spirals_streamline_data.txt -cm hsv -ll -dr 0 25 -cr 25 50

# colour/clip by image
{prefix} 3d -d tractogram/spirals.trk -lw 5 -co 3d
{prefix} 3d -d tractogram/spirals.trk -lw 5 -co 3d -cm hot
{prefix} 3d -d tractogram/spirals.trk -lw 5 -cl 3d -cr 5000 8000
{prefix} 3d -d tractogram/spirals.trk -lw 5 -co 3d -cl vdata -cm hot -dr 4000 8000 -cr -0.75 0.75
"""


cli_tube_tests = f"""
{prefix}     tractogram/spirals.trk -lw 10
{prefix}     tractogram/spirals.trk -lw 20
{prefix}     tractogram/spirals.trk -lw 50
{prefix}     tractogram/spirals.trk -lw 20 -r 3
{prefix}     tractogram/spirals.trk -lw 20 -r 6
{prefix}     tractogram/spirals.trk -lw 20 -r 10
{prefix} -dl tractogram/spirals.trk -lw 20 -r 3
{prefix} -dl tractogram/spirals.trk -lw 20 -r 6
{prefix} -dl tractogram/spirals.trk -lw 20 -r 10
"""


@pytest.mark.skipif('not haveGL(2.1)')
def test_overlay_tractogram():
    run_cli_tests('test_overlay_tractogram', cli_tests)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
def test_overlay_tractogram_tubes():
    run_cli_tests('test_overlay_tractogram_tubes', cli_tube_tests)
