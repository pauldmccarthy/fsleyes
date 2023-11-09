#!/usr/bin/env python

import os.path as op

from fsl.utils.tempdir import tempdir

from fsleyes.actions.loadoverlay import loadOverlays
from fsleyes.controls.overlaylistpanel import OverlayListPanel

from fsleyes.tests import (run_with_orthopanel,
                           run_with_scene3dpanel,
                           complex,
                           realYield,
                           waitUntilIdle)

# test all overlay types

DATADIR = op.join(op.dirname(__file__), '..', 'testdata')
OVERLAYS = [

    ('3d.nii.gz',              'volume'),
    ('3d.nii.gz',              'mask'),
    ('3d.nii.gz',              'label'),
    ('3d.nii.gz',              'mip'),
    ('dti/',                   'tensor'),
    ('dti/dti_V1.nii.gz',      'rgbvector'),
    ('dti/dti_V1.nii.gz',      'linevector'),
    ('dti/dti_V1.nii.gz',      'rgb'),
    ('sh_sym.nii.gz',          'sh'),
    ('mesh_l_thal.vtk',        'mesh'),
    ('tractogram/spirals.trk', 'tractogram'),
    (complex,                  'complex'),
]

def test_OverlayDisplayPanel_ortho():
    run_with_orthopanel(_test_OverlayDisplayPanel)

def test_OverlayDisplayPanel_3D():
    run_with_scene3dpanel(_test_OverlayDisplayPanel)

def _test_OverlayDisplayPanel(panel, overlayList, displayCtx):

    with tempdir():
        for filename, overlayType in OVERLAYS:
            print('TESTING', filename, overlayType)
            if callable(filename):
                filename = filename()
            else:
                filename = op.join(DATADIR, filename)

            overlay = loadOverlays([filename], blocking=True)[0]

            overlayList.append(overlay, overlayType=overlayType)

            waitUntilIdle()
            panel.togglePanel(OverlayListPanel)
            waitUntilIdle()
            panel.togglePanel(OverlayListPanel)
            waitUntilIdle()
            overlayList.clear()
            waitUntilIdle()
