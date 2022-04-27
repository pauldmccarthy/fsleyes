#!/usr/bin/env python
#
# test_overlay_tractogram.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from unittest import mock
import random
import numpy as np

import pytest

from fsleyes.tests import run_cli_tests, haveGL


pytestmark = pytest.mark.overlayclitest


# 3d/ortho views have diffferent cli
# flags and scalings for zoom factor
zooms3d = {
    'zoom20'  : '-z 20',
    'zoom40'  : '-z 40',
    'zoom200' : '-z 200',
}
zoomsortho = {
    'zoom20'  : '-xz   75 -yz   75 -zz   75',
    'zoom40'  : '-xz   90 -yz   90 -zz   90',
    'zoom200' : '-xz 1500 -yz 1500 -zz 1500',
}

# GL21 3D does not support line width
# scaling (it just uses glLineWidth).
# So these tests are only run on gl33,
# and linewidth is adapted in the
# remaining tests below.
cli_tests_linewidth = """
{prefix} {zoom40} tractogram/spirals.trk
{prefix} {zoom40} tractogram/spirals.trk -lw 3
{prefix} {zoom40} tractogram/spirals.trk -lw 5
{prefix} {zoom40} tractogram/spirals.trk -lw 10

{prefix} {zoom20} tractogram/spirals.trk
{prefix} {zoom20} tractogram/spirals.trk -lw 3
{prefix} {zoom20} tractogram/spirals.trk -lw 5
{prefix} {zoom20} tractogram/spirals.trk -lw 10

{prefix} {zoom200} tractogram/spirals.trk
{prefix} {zoom200} tractogram/spirals.trk -lw 3
{prefix} {zoom200} tractogram/spirals.trk -lw 5
{prefix} {zoom200} tractogram/spirals.trk -lw 10
"""

cli_tests = """
# Colour/clip by data baked into the streamline file
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata           -cm hsv -dr -0.75 0.75
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata           -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co sdata           -cm hsv -dr -0.75 0.75
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co sdata           -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata -cl sdata -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co sdata -cl vdata -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth}           -cl vdata -cm hsv                -cr -0.75 0.75

# neg cmap
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata -cm red-yellow -nc blue-lightblue -un
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata -cm red-yellow -nc blue-lightblue -un -dr 0.25 1

# code pathways for per-streamline/vertex data are
# more or less identical, so no need to test both
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_streamline_data.txt
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt -cm hsv
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt -cm hsv -ll -dr 0 25 -cr 25 50
{prefix} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt -cl tractogram/spirals_streamline_data.txt -cm hsv -ll -dr 0 25 -cr 25 50

# colour/clip by image
{prefix} {zoom40}  3d -d tractogram/spirals.trk -lw {linewidth} -co 3d
{prefix} {zoom40}  3d -d tractogram/spirals.trk -lw {linewidth} -co 3d -cm hot
{prefix} {zoom40}  3d -d tractogram/spirals.trk -lw {linewidth} -cl 3d -cr 5000 8000
{prefix} {zoom40}  3d -d tractogram/spirals.trk -lw {linewidth} -co 3d -cl vdata -cm hot -dr 4000 8000 -cr -0.75 0.75

# sub-sampling
{prefix} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 75
{prefix} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 50
{prefix} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 25
{prefix} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 75 -co vdata -cm hot
{prefix} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 50 -co vdata -cm hot
{prefix} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 25 -co vdata -cm hot
"""


cli_tube_tests = """
-s3d -z 40      tractogram/spirals.trk -lw 20 -r 3
-s3d -z 40      tractogram/spirals.trk -lw 20 -r 6
-s3d -z 40      tractogram/spirals.trk -lw 20 -r 10
-s3d -z 40  -dl tractogram/spirals.trk -lw 20 -r 3
-s3d -z 40  -dl tractogram/spirals.trk -lw 20 -r 6
-s3d -z 40  -dl tractogram/spirals.trk -lw 20 -r 10
"""

# hack to ensure the RNG is in the same
# state for every command (the --subsample
# option is non-deterministic in nature)
def reseed(f):
    np.random.seed(124)
    random   .seed(124)
    return f
extras  = {'reseed' : reseed}

@pytest.mark.skipif('not haveGL(2.1)')
def test_overlay_tractogram_2d_gl21():
    fmtargs = { 'prefix'    : '-sortho -wl 0 -10 25',
                'linewidth' : '10',
                **zoomsortho}
    tests   = cli_tests_linewidth + cli_tests
    tests   = tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_2d_gl21',
                  tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
@pytest.mark.overlayclitest
def test_overlay_tractogram_2d_gl33():
    fmtargs = { 'prefix'    : '-sortho -wl 0 -10 25',
                'linewidth' : '10',
                **zoomsortho}
    tests   = cli_tests_linewidth + cli_tests
    tests   = tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_2d_gl33',
                  tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(2.1)')
def test_overlay_tractogram_3d_gl21():
    fmtargs = { 'prefix'    : '-s3d',
                'linewidth' : '10',
                **zooms3d}
    tests   = cli_tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_3d_gl21',
                  tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
@pytest.mark.overlayclitest
def test_overlay_tractogram_3d_gl33():
    fmtargs = { 'prefix'    : '-s3d',
                'linewidth' : '5',
                **zooms3d}
    tests   = cli_tests_linewidth + cli_tests
    tests   = tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_3d_gl33',
                  tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
@pytest.mark.overlayclitest
def test_overlay_tractogram_3d_tubes():
    run_cli_tests('test_overlay_tractogram_3d_tubes', cli_tube_tests)
