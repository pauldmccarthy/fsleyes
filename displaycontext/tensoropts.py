#!/usr/bin/env python
#
# tensoropts.py - The TensorOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TensorOpts` class, which defines 
options for displaying :class:`.GLTensor` instances.
"""


import props
import vectoropts


class TensorOpts(vectoropts.VectorOpts):
    """The ``TensorOpts`` class defines options for displaying :class:`.GLTensor`
    instances.
    """


    # Enable/disable lighting effects
    lighting = props.Boolean(default=True)
    """Enables a basic lighting model on the tensor ellipsoids. """


    # Tensor ellipsoid resolution
    tensorResolution = props.Int(minval=4, maxval=20, default=10)
    """Tensor ellipsoid resolution - this value controls the number of vertices
    used to represent each tensor. It is ultimately passed to the
    :func:`.routines.unitSphere` function.
    """

    
    def __init__(self, *args, **kwargs):
        """Create a ``TensorOpts`` instance. All arguments are passed through
        to :meth:`.VectorOpts.__init__`.
        """
        
        vectoropts.VectorOpts.__init__(self, *args, **kwargs)
