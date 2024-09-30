#!/usr/bin/env python

import            glob
import os.path as op
import            os
import            shutil

import numpy as np
import          wx

from fsl.data.image    import Image
from fsl.utils.tempdir import tempdir

from fsleyes.plugins.controls import clusterpanel as cp

from fsleyes.tests import (__file__ as testfile,
                           simselect,
                           simclick,
                           realYield,
                           run_with_orthopanel)


testdir = op.dirname(testfile)


def test_clusterpanel():
    run_with_orthopanel(_test_clusterpanel)


def random_image(path, shape=None):
    if shape is None:
        shape = (10, 10, 10)
    data = np.random.random(shape).astype(np.float32)
    Image(data).save(path)


def make_mock_feat_analysis(path):
    path = op.abspath(path)

    shapes = {
        'filtered_func_data.nii.gz' : (10, 10, 10, 10),
        'res4d.nii.gz'              : (10, 10, 10, 10),
    }

    os.makedirs(op.dirname(path), exist_ok=True)
    template = op.join(testdir, 'testdata', 'analysis.feat')
    shutil.copytree(template, path)
    for imgfile in glob.glob(op.join(path, '**', '*.nii.gz'),
                             recursive=True):
        shape = shapes.get(op.basename(imgfile))
        random_image(imgfile, shape)



def _test_clusterpanel(panel, overlayList, displayCtx):
    with tempdir():

        sim     = wx.UIActionSimulator()
        featdir = op.abspath('analysis.feat')

        make_mock_feat_analysis(featdir)

        func = Image(op.join(featdir, 'filtered_func_data'))
        overlayList.append(func)

        panel.togglePanel(cp.ClusterPanel)
        cpanel = panel.getPanel(cp.ClusterPanel)
        realYield()

        simclick(sim, cpanel.addZStats)
        simselect(sim, cpanel.statSelect, 'zstat2')
        simclick(sim, cpanel.addClustMask)

        exp = ['filtered_func_data.nii.gz',
               op.join('stats', 'zstat1.nii.gz'),
               op.join('cluster_mask_zstat2.nii.gz')]
        exp = [op.join(featdir, e) for e in exp]
        got = [o.dataSource for o in overlayList]

        assert sorted(exp) == sorted(got)
