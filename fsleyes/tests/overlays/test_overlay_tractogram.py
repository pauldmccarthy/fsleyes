#!/usr/bin/env python
#
# test_overlay_tractogram.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from unittest import mock
import itertools as it
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
{prefix} {loc} {zoom40} tractogram/spirals.trk
{prefix} {loc} {zoom40} tractogram/spirals.trk -lw 3
{prefix} {loc} {zoom40} tractogram/spirals.trk -lw 5
{prefix} {loc} {zoom40} tractogram/spirals.trk -lw 10

{prefix} {loc} {zoom20} tractogram/spirals.trk
{prefix} {loc} {zoom20} tractogram/spirals.trk -lw 3
{prefix} {loc} {zoom20} tractogram/spirals.trk -lw 5
{prefix} {loc} {zoom20} tractogram/spirals.trk -lw 10

{prefix} {loc} {zoom200} tractogram/spirals.trk
{prefix} {loc} {zoom200} tractogram/spirals.trk -lw 3
{prefix} {loc} {zoom200} tractogram/spirals.trk -lw 5
{prefix} {loc} {zoom200} tractogram/spirals.trk -lw 10
"""

cli_tests = """
# Colour/clip by data baked into the streamline file
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata           -cm hsv -dr -0.75 0.75
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata           -cm hsv -dr -0.75 0.75 -cr -0.5  0.5  # should be no clipping
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata -cl vdata -cm hsv -dr -0.75 0.75 -cr -0.5  0.5  # should be clipping
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co sdata           -cm hsv -dr -0.75 0.75
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co sdata           -cm hsv -dr -0.75 0.75 -cr -0.5  0.5  # should be no clipping
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co sdata -cl sdata -cm hsv -dr -0.75 0.75 -cr -0.75 0.75 # should be clipping
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata -cl sdata -cm hsv -dr -0.75 0.75 -cr -0.75 0.75
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co sdata -cl vdata -cm hsv -dr -0.75 0.75 -cr -0.5  0.5
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth}           -cl vdata -cm hsv                -cr -0.5  0.5

# neg cmap
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata -cm red-yellow -nc blue-lightblue -un
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co vdata -cm red-yellow -nc blue-lightblue -un -dr 0.25 1

# code pathways for per-streamline/vertex data are
# more or less identical, so no need to test both
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_streamline_data.txt
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt -cm hsv
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt -cl tractogram/spirals_streamline_data.txt -cm hsv -ll -dr 0 25 -cr 25 50
{prefix} {loc} {zoom40}  tractogram/spirals.trk -lw {linewidth} -co tractogram/spirals_vertex_data.txt -cl tractogram/spirals_streamline_data.txt -cm hsv -ll -cr 17 34

# colour/clip by image
{prefix} {zoom40} 3d {opts3d} -a {alpha3d} tractogram/spirals.trk -ri 3d -lw {linewidth} -co 3d
{prefix} {zoom40} 3d {opts3d} -a {alpha3d} tractogram/spirals.trk -ri 3d -lw {linewidth} -co 3d -cm hot
{prefix} {zoom40} 3d {opts3d} -a {alpha3d} tractogram/spirals.trk -ri 3d -lw {linewidth} -cl 3d -cr 5000 8000
{prefix} {zoom40} 3d {opts3d} -a {alpha3d} tractogram/spirals.trk -ri 3d -lw {linewidth} -co 3d -cl vdata -cm hot -dr 4000 8000 -cr -0.5 0.5

# sub-sampling
{prefix} {loc} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 75
{prefix} {loc} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 50
{prefix} {loc} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 25
{prefix} {loc} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 75 -co vdata -cm hot
{prefix} {loc} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 50 -co vdata -cm hot
{prefix} {loc} {zoom40} {{{{reseed('tractogram/spirals.trk')}}}} -lw {linewidth} -s 25 -co vdata -cm hot
"""

cli_refImage_tests = """
tractogram/dipy_ref.nii.gz tractogram/dipy_tracks.trk              -lw 10
tractogram/dipy_ref.nii.gz tractogram/dipy_tracks.trk -ri dipy_ref -lw 10
tractogram/dipy_ref.nii.gz tractogram/dipy_tracks.trk              -lw 10
tractogram/dipy_ref.nii.gz tractogram/dipy_tracks.trk -ri dipy_ref -cs pixdim -lw 10
"""

cli_pseudo3d_tests = """
tractogram/dipy_tracks.trk -lw 5 -sw 1
tractogram/dipy_tracks.trk -lw 5 -sw 10
tractogram/dipy_tracks.trk -lw 5 -sw 1  -p -xcl slice -ycl slice  -zcl slice
tractogram/dipy_tracks.trk -lw 5 -sw 10 -p -xcl slice -ycl slice  -zcl slice

tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl none  -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl low   -ycl none  -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl high  -ycl none  -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl slice -ycl none  -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl none  -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl low   -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl high  -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl slice -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl none  -zcl none
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl none  -zcl low
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl none  -zcl high
tractogram/dipy_tracks.trk -lw 5 -p -xcl none  -ycl none  -zcl slice
-slightbox -bg 0.2 0.2 0.2 -zx 0 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -xcl slice
-slightbox -bg 0.2 0.2 0.2 -zx 1 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -ycl slice
-slightbox -bg 0.2 0.2 0.2 -zx 2 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -zcl slice
-slightbox -bg 0.2 0.2 0.2 -zx 0 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -xcl none
-slightbox -bg 0.2 0.2 0.2 -zx 1 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -ycl none
-slightbox -bg 0.2 0.2 0.2 -zx 2 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -zcl none
-slightbox -bg 0.2 0.2 0.2 -zx 0 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -xcl low
-slightbox -bg 0.2 0.2 0.2 -zx 1 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -ycl low
-slightbox -bg 0.2 0.2 0.2 -zx 2 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -zcl low
-slightbox -bg 0.2 0.2 0.2 -zx 0 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -xcl high
-slightbox -bg 0.2 0.2 0.2 -zx 1 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -ycl high
-slightbox -bg 0.2 0.2 0.2 -zx 2 -zr 0 1 tractogram/dipy_tracks.trk -ri tractogram/dipy_ref.nii.gz -lw 1 -p -zcl high
"""


# run on 3D, and ortho with the --pseudo3D flag (GL33 only)
cli_tube_tests = """
-s{view} -z 40      tractogram/spirals.trk -lw 20 -r 3  {extra}
-s{view} -z 40      tractogram/spirals.trk -lw 20 -r 6  {extra}
-s{view} -z 40      tractogram/spirals.trk -lw 20 -r 10 {extra}
-s{view} -z 40  -dl tractogram/spirals.trk -lw 20 -r 3  {extra}
-s{view} -z 40  -dl tractogram/spirals.trk -lw 20 -r 6  {extra}
-s{view} -z 40  -dl tractogram/spirals.trk -lw 20 -r 10 {extra}
"""

# hack to ensure the RNG is in the same
# state for every command (the --subsample
# option is non-deterministic in nature)
def reseed(f):
    np.random.seed(124)
    random   .seed(124)
    return f
extras  = {'reseed' : reseed}


@pytest.mark.skipif('(not haveGL(2.1)) or haveGL(3.3)')
def test_overlay_tractogram_2d_gl21():
    fmtargs = { 'prefix'    : '-sortho -hc -hl',
                'linewidth' : '10',
                'loc'       : '-wl 0 -10 25',
                'opts3d'    : '',
                'alpha3d'   : '50',
                **zoomsortho}
    tests   = cli_tests_linewidth + cli_tests
    tests   = tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_2d_gl21',
                  tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
def test_overlay_tractogram_2d_gl33():
    fmtargs = { 'prefix'    : '-sortho -hc -hl',
                'linewidth' : '10',
                'loc'       : '-wl 0 -10 25',
                'opts3d'    : '',
                'alpha3d'   : '50',
                **zoomsortho}
    tests   = cli_tests_linewidth + cli_tests
    tests   = tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_2d_gl33',
                  tests,
                  extras=extras)


@pytest.mark.skipif('(not haveGL(2.1)) or haveGL(3.3)')
def test_overlay_tractogram_3d_gl21():
    fmtargs = { 'prefix'    : '-s3d -dl',
                'linewidth' : '10',
                'loc'       : '-wl 0 -10 25',
                'opts3d'    : '-in none -cp 50 0 -90',
                'alpha3d'   : '85',
                **zooms3d}
    tests   = cli_tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_3d_gl21',
                  tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
def test_overlay_tractogram_3d_gl33():
    fmtargs = { 'prefix'    : '-s3d -dl',
                'linewidth' : '10',
                'loc'       : '-wl 0 -10 25',
                'opts3d'    : '-in none -cp 50 0 -90',
                'alpha3d'   : '85',
                **zooms3d}
    tests   = cli_tests_linewidth + cli_tests
    tests   = tests.format(**fmtargs)
    run_cli_tests('test_overlay_tractogram_3d_gl33',
                  tests,
                  extras=extras)


@pytest.mark.skipif('(not haveGL(2.1)) or haveGL(3.3)')
def test_overlay_tractogram_pseudo3d_gl21():
    run_cli_tests('test_overlay_tractogram_pseudo3d_gl21',
                  cli_pseudo3d_tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
def test_overlay_tractogram_pseudo3d_gl33():
    run_cli_tests('test_overlay_tractogram_pseudo3d_gl33',
                  cli_pseudo3d_tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(2.1)')
def test_overlay_tractogram_2d_refImage():
    run_cli_tests('test_overlay_tractogram_2d_refImage',
                  cli_refImage_tests,
                  extras=extras)


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
def test_overlay_tractogram_3d_tubes():
    run_cli_tests('test_overlay_tractogram_3d_tubes',
                  cli_tube_tests.format(view='3d', extra=''))


@pytest.mark.skipif('not haveGL(3.3)')
@pytest.mark.gl33test
def test_overlay_tractogram_pseudo3d_tubes():
    run_cli_tests('test_overlay_tractogram_pseudo3d_tubes',
                  cli_tube_tests.format(view='ortho', extra='-p'))
