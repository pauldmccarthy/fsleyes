#!/usr/bin/env python

import numpy as np

import fsleyes.gl.routines as glroutines


def test_voxelBox_pixdim_precision():
    # fsl/fsleyes/fsleyes!270
    # Make sure that box is at least
    # one voxel along each axis
    expect = np.array([[40, 40, 40],
                       [40, 40, 41],
                       [40, 41, 40],
                       [40, 41, 41],
                       [41, 40, 40],
                       [41, 40, 41],
                       [41, 41, 40],
                       [41, 41, 41]])

    result1 = glroutines.voxelBox([40, 40, 40],
                                  [100, 100, 100],
                                  (1.0, 1.0, 1.0),
                                  1.0,
                                  (0, 1), bias='high')

    result2 = glroutines.voxelBox([40, 40, 40],
                                  [100, 100, 100],
                                  (1.0000001, 1.0, 1.0),
                                  1.0,
                                  (0, 1), bias='high')

    assert np.all(np.isclose(result1, expect))
    assert np.all(np.isclose(result2, expect))
