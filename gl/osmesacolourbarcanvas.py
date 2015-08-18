#!/usr/bin/env python
#
# osmesacolourbarcanvas.py - A ColourBarCanvas which uses OSMesa for
# off-screen rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

"""Provides the :class:`OSMesaColourBarCanvas` for off-screen
rendering of colour bars.
"""

import logging
log = logging.getLogger(__name__)


import fsl.fsleyes.gl  as fslgl
import colourbarcanvas as cbarcanvas
       

class OSMesaColourBarCanvas(cbarcanvas.ColourBarCanvas,
                            fslgl.OSMesaCanvasTarget):
    """A :class:`.SliceCanvas` which uses OSMesa for static off-screen OpenGL
    rendering.
    """
    
    def __init__(self,
                 width=0,
                 height=0):
        """Create a colour bar canvas for off-screen rendering.
        :arg width:  Canvas width in pixels
        
        :arg height: Canvas height in pixels
        """

        fslgl.OSMesaCanvasTarget  .__init__(self, width, height)
        cbarcanvas.ColourBarCanvas.__init__(self)

ColourBarCanvas = OSMesaColourBarCanvas
