#!/usr/bin/env python
#
# program.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


class ARBProgram(object):
    
    def __init__(self,
                 vertSrc,
                 fragSrc,
                 paramMap=None,
                 textureMap=None,
                 vertAttMap=None):

        if textureMap is None: textureMap = {}
        if paramMap   is None: paramMap   = {}
        if vertAttMap is None: vertAttMap = {}
