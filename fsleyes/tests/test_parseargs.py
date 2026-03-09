#!/usr/bin/env python


import os
import os.path as op
import shutil

import numpy as np
import pytest

from fsl.data.image import Image

from fsl.utils.tempdir import tempdir

from fsleyes.colourmaps import LookupTable

from fsleyes.tests import (run_cli_tests,
                           discretise,
                           run_with_fsleyes,
                           realYield)


pytestmark = pytest.mark.clitest


datadir = op.join(op.dirname(__file__), 'testdata')


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



def test_autoname():
    run_with_fsleyes(_test_autoname)

def _test_autoname(ortho, overlayList, displayCtx):

    displayCtx.autoNameOverlays = True

    with tempdir():

        os.makedirs('a/b')
        os.makedirs('a/c', exist_ok=True)

        shutil.copy(f'{datadir}/3d.nii.gz', 'a/b/')
        shutil.copy(f'{datadir}/3d.nii.gz', 'a/c/')

        i1 = Image('a/b/3d')
        i2 = Image('a/c/3d')

        overlayList.extend((i1, i2))
        realYield()

        assert displayCtx.getDisplay(i1).name == 'b/3d'
        assert displayCtx.getDisplay(i2).name == 'c/3d'

        overlayList[:] = []
        realYield()

        # fsl/fsleyes/fsleyes!497
        # don't auto rename  overlays that
        # have explicitly been given a name
        i1 = Image('a/b/3d')
        i2 = Image('a/c/3d')
        overlayList.extend((i1, i2), name={i1 : 'first', i2 : 'second'})
        realYield()
        assert displayCtx.getDisplay(i1).name == 'first'
        assert displayCtx.getDisplay(i2).name == 'second'
