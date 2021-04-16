#!/usr/bin/env python
#
# test_group.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import fsl.data.image as fslimage

from fsleyes.tests import run_with_fsleyes


datadir = op.join(op.dirname(__file__), 'testdata')


def _test_group(frame, overlayList, displayCtx):

    # Currently there is always only one group
    group = displayCtx.overlayGroups[0]
    img1  = fslimage.Image(op.join(datadir, '3d'))
    img2  = fslimage.Image(op.join(datadir, '4d'))

    # all new images should be
    # added to the overlay group
    overlayList.append(img1)
    assert img1 in group

    # Overlays should be automatically
    # removed from the group
    del overlayList[:]
    assert len(group) == 0

    overlayList.append(img1)
    overlayList.append(img2)
    assert img1 in group
    assert img2 in group

    del overlayList[0]
    assert img1 not in group
    assert img2     in group
    del overlayList[0]
    assert img1 not in group
    assert img2 not in group


def test_group():
    run_with_fsleyes(_test_group)
