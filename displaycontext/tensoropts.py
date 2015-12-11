#!/usr/bin/env python
#
# tensoropts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import props

import vectoropts


log = logging.getLogger(__name__)


class TensorOpts(vectoropts.VectorOpts):


    # Only show 2D ellipses around 
    # the three primary tensor axes
    outline  = props.Boolean(default=False)


    # Enable/disable lighting effects
    lighting = props.Boolean(default=False)


    # Tensor ellipsoid resolution
    tensorResolution = props.Int(default=10)

    
    def __init__(self, *args, **kwargs):
        
        vectoropts.VectorOpts.__init__(self, *args, **kwargs)
