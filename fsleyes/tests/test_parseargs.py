#!/usr/bin/env python


import os.path as op

import numpy as np
import pytest

from fsl.utils.tempdir import tempdir

from fsleyes.colourmaps import LookupTable

from fsleyes.tests import run_cli_tests, discretise


pytestmark = pytest.mark.clitest


def cmap(fname):
    np.random.seed(1234)
    if not op.exists(fname):
        cmap = np.random.random((10, 3))
        np.savetxt(fname, cmap)
    return fname


def lut(fname):

    np.random.seed(1234)

    if op.exists(fname):
        return fname

    name = op.splitext(fname)[0]
    lut  = LookupTable(name, name)

    for val in list(range(1, 11)):
        name   = f'label {val}'
        colour = np.random.random(3)
        lut.insert(val, name=name, colour=colour)

    lut.save(fname)
    return fname


# fsl/fsleyes/fsleyes#196
# fsl/fsleyes/fsleyes!278
def test_multiple_cmap_lut_files():

    tests = """
    3d -cm {{cmap('cmapfile.cmap')}} 3d -cm {{cmap('cmapfile.cmap')}} -a 50 -b 20
    {{discretise('3d', 500)}} -ot label -l {{lut('lutfile.lut')}} {{discretise('3d', 500)}} -ot label -l {{lut('lutfile.lut')}} -a 50 -b 15
    """

    extras = {
        'discretise' : discretise,
        'cmap'       : cmap,
        'lut'        : lut
    }

    run_cli_tests('test_parseargs', tests, extras=extras)
