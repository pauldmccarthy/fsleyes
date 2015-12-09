#!/usr/bin/env python
#
# tensoropts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import volumeopts


log = logging.getLogger(__name__)


class TensorOpts(volumeopts.ImageOpts):

    
    def __init__(self, *args, **kwargs):
        
        volumeopts.ImageOpts.__init__(self, *args, **kwargs)
