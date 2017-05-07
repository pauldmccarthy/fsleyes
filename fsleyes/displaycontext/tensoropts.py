#!/usr/bin/env python
#
# tensoropts.py - The TensorOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TensorOpts` class, which defines
options for displaying :class:`.GLTensor` instances.
"""


import fsleyes_props as props
from . import           vectoropts


class TensorOpts(vectoropts.VectorOpts):
    """The ``TensorOpts`` class defines options for displaying :class:`.GLTensor`
    instances.
    """


    lighting = props.Boolean(default=True)
    """Enables a basic lighting model on the tensor ellipsoids. """


    tensorResolution = props.Int(minval=4, maxval=20, default=10)
    """Tensor ellipsoid resolution - this value controls the number of vertices
    used to represent each tensor. It is ultimately passed to the
    :func:`.routines.unitSphere` function.
    """


    tensorScale = props.Percentage(minval=50, maxval=600, default=100)
    """Scaling factor - by default, the tensor ellipsoids are scaled such that
    the biggest tensor (as defined by the first principal eigenvalue) fits
    inside a voxel. This parameter can be used to adjust this scale.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``TensorOpts`` instance. All arguments are passed through
        to :meth:`.VectorOpts.__init__`.
        """

        vectoropts.VectorOpts.__init__(self, *args, **kwargs)
