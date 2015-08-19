#!/usr/bin/env python
#
# osmesaslicecanvas.py - A SliceCanvas which uses OSMesa for off-screen OpenGL
# rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides the :class:`OSMesaSliceCanvas` which supports off-screen
rendering.
"""

import logging
log = logging.getLogger(__name__)


import fsl.fsleyes.gl   as fslgl
import slicecanvas      as sc
       

class OSMesaSliceCanvas(sc.SliceCanvas,
                        fslgl.OSMesaCanvasTarget):
    """A :class:`.SliceCanvas` which uses OSMesa for static off-screen OpenGL
    rendering.
    """
    
    def __init__(self,
                 overlayList,
                 displayCtx,
                 zax=0,
                 width=0,
                 height=0):
        """See the :class:`.SliceCanvas` constructor for details on the other
        parameters.

        :arg width:    Canvas width in pixels
        
        :arg height:   Canvas height in pixels
        """

        fslgl.OSMesaCanvasTarget.__init__(self, width, height)
        sc.SliceCanvas          .__init__(self, overlayList, displayCtx, zax)
