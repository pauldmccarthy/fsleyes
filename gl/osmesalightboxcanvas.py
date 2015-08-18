#!/usr/bin/env python
#
# osmesalightboxcanvas.py - A LightBoxCanvas which uses OSMesa for off-screen
# OpenGL rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides the :class:`OSMesaLightBoxCanvas` which supports off-screen
rendering.
"""

import logging
log = logging.getLogger(__name__)


import fsl.fsleyes.gl as fslgl
import lightboxcanvas
       

class OSMesaLightBoxCanvas(lightboxcanvas.LightBoxCanvas,
                           fslgl.OSMesaCanvasTarget):
    """A :class:`.LightBoxCanvas` which uses OSMesa for static off-screen Open
    GL rendering.
    """
    
    def __init__(self,
                 overlayList,
                 displayCtx,
                 zax=0,
                 width=0,
                 height=0,
                 bgColour=(0, 0, 0, 255)):
        """See the :class:`.LightBoxCanvas` constructor for details on the other
        parameters.

        :arg width:    Canvas width in pixels
        
        :arg height:   Canvas height in pixels

        :arg bgColour: Canvas background colour

        """

        fslgl.OSMesaCanvasTarget     .__init__(self, width, height, bgColour)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               overlayList,
                                               displayCtx,
                                               zax)
