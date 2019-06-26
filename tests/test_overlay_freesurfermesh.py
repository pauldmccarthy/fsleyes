#!/usr/bin/env python
#
# test_overlay_freesurfermesh.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

from . import run_cli_tests


pytestmark = pytest.mark.overlayclitest


cli_tests = """
freesurfer/lh.pial -mc 1 0 0
freesurfer/lh.pial -mc 1 0 0 -o
freesurfer/lh.pial -mc 1 0 0    -w 1
freesurfer/lh.pial -mc 1 0 0    -w 5
freesurfer/lh.pial -mc 1 0 0    -w 10
freesurfer/lh.pial -mc 1 0 0 -o -w 1
freesurfer/lh.pial -mc 1 0 0 -o -w 5
freesurfer/lh.pial -mc 1 0 0 -o -w 10
freesurfer/lh.pial -mc 1 0 0 -o -w 10 -cm hot -vd freesurfer/lh.curv
freesurfer/lh.pial -mc 1 0 0 -o -w 10 -cm hot -vd freesurfer/lh.curv
"""

def test_overlay_freesurfermesh():
    extras = {}
    run_cli_tests('test_overlay_freesurfermesh',
                  cli_tests,
                  extras=extras,
                  threshold=25)
