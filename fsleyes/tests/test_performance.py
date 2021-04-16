#!/usr/bin/env python
#
# test_performance.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from fsleyes.tests import run_cli_tests, discretise


cli_tests = """
3d.nii.gz
3d.nii.gz -ot mask -t 4000 10000
3d.nii.gz -ot mip
{{discretise('3d.nii.gz', 500)}} -ot label
dti
dti/dti_V1 -ot rgbvector
dti/dti_V1 -ot linevector
sh -ot sh
mesh_l_thal.vtk -mc 1 0 0
"""


extras = {'discretise' : discretise}


def add_prefix(prefix):
    tests = list(cli_tests.strip().split('\n'))
    tests = [prefix + t for t in tests]
    return '\n'.join(tests)


def test_performance_p1_ortho():
    tests = add_prefix('-p 1 -s ortho ')
    run_cli_tests('test_performance', tests, extras=extras)


def test_performance_p2_ortho():
    tests = add_prefix('-p 2 -s ortho ')
    run_cli_tests('test_performance', tests, extras=extras)


def test_performance_p1_lightbox():
    tests = add_prefix('-p 1 -s lightbox ')
    run_cli_tests('test_performance', tests, extras=extras)


def test_performance_p2_lightbox():
    tests = add_prefix('-p 2 -s lightbox ')
    run_cli_tests('test_performance', tests, extras=extras)
