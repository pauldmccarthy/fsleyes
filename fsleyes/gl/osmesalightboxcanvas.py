#!/usr/bin/env python
#
# osmesalightboxcanvas.py - The OSMesaLightBoxCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OSMesaLightBoxCanvas`, which is a
:class:`.LightBoxCanvas` for use with OSMesa (off-screen OpenGL rendering).
"""


import fsl.fsleyes.gl as fslgl
import lightboxcanvas


class OSMesaLightBoxCanvas(lightboxcanvas.LightBoxCanvas,
                           fslgl.OSMesaCanvasTarget):
    """The ``OSMesaLightBoxCanvas`` is a :class:`.LightBoxCanvas` which uses
    OSMesa for static off-screen Open GL rendering.
    """
    
    def __init__(self,
                 overlayList,
                 displayCtx,
                 zax=0,
                 width=0,
                 height=0):
        """Create an ``OSMesaLightBoxCanvas``.
        
        :arg width:    Canvas width in pixels
        
        :arg height:   Canvas height in pixels

        See :meth:`.LightBoxCanvas.__init__` for details on the other
        arguments.
        """

        fslgl.OSMesaCanvasTarget     .__init__(self, width, height)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               overlayList,
                                               displayCtx,
                                               zax)
