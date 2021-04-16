#!/usr/bin/env python


import pytest

import numpy as np

from fsleyes.tests import run_cli_tests, discretise


pytestmark = pytest.mark.overlayclitest

cli_tests = """
{{discretise('3d.nii.gz', 500)}} -ot label
{{discretise('3d.nii.gz', 500)}} -ot label -o
{{discretise('3d.nii.gz', 500)}} -ot label -o -l harvard-oxford-cortical

{{discretise('3d.nii.gz', 500)}} -ot label    -w 0
{{discretise('3d.nii.gz', 500)}} -ot label    -w 1
{{discretise('3d.nii.gz', 500)}} -ot label    -w 5
{{discretise('3d.nii.gz', 500)}} -ot label    -w 10
{{discretise('3d.nii.gz', 500)}} -ot label -o -w 0
{{discretise('3d.nii.gz', 500)}} -ot label -o -w 1
{{discretise('3d.nii.gz', 500)}} -ot label -o -w 5
{{discretise('3d.nii.gz', 500)}} -ot label -o -w 10

{{discretise('3d.nii.gz', 500)}} -ot label -l {{gen_lut(custom_lut,   'custom1')}}
{{discretise('3d.nii.gz', 500)}} -ot label -l {{gen_lut(custom_lut,   'custom2')}} -o
{{discretise('3d.nii.gz', 500)}} -ot label -l {{gen_cmap('cmap1')}}


{{discretise('4d.nii.gz', 1000, 6000, 11000)}} -ot label -v 0 -l random
{{discretise('4d.nii.gz', 1000, 6000, 11000)}} -ot label -v 1 -l random
{{discretise('4d.nii.gz', 1000, 6000, 11000)}} -ot label -v 2 -l random
{{discretise('4d.nii.gz', 1000, 6000, 11000)}} -ot label -v 3 -l random
"""



custom_lut = {
    1 : ([1, 0,     0], 'one'),
    2 : ([0, 1,     0], 'two'),
    3 : ([0, 0,     1], 'three'),
    4 : ([1, 1,     0], 'four'),
    5 : ([1, 0,     1], 'five'),
    6 : ([0, 1,     1], 'six'),
    7 : ([1, 0.5,   0], 'seven'),
    8 : ([1, 0,   0.5], 'eight'),
    9 : ([0, 0.5, 0.5], 'nine'),
}

def gen_lut(lut, name):
    fname = '{}.lut'.format(name)
    with open(fname, 'wt') as f:
        for label, (colour, name) in lut.items():
            r, g, b = colour
            f.write('{} {} {} {} {}\n'.format(label, r, g, b, name))
    return fname


def gen_cmap(name):
    np.random.seed(1234)
    cmap = np.random.random((10, 3))

    fname = '{}.cmap'.format(name)
    np.savetxt(fname, cmap)
    return fname


def test_overlay_label():
    extras = {
        'discretise'  : discretise,
        'gen_lut'     : gen_lut,
        'gen_cmap'    : gen_cmap,
        'custom_lut'  : custom_lut,
    }
    run_cli_tests('test_overlay_label', cli_tests, extras=extras)
