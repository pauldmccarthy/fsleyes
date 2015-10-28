#!/usr/bin/env python
#
# osmesacolourbarcanvas.py - The OSMesaColourBarCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OSMesaColourBarCanvas`, which is a
:class:`.ColourBarCanvas` for use with OSMesa (off-screen OpenGL rendering).
"""


import fsl.fsleyes.gl  as fslgl
import colourbarcanvas as cbarcanvas


class OSMesaColourBarCanvas(cbarcanvas.ColourBarCanvas,
                            fslgl.OSMesaCanvasTarget):
    """The ``OSMesaColourBarCanvas`` is a :class:`.ColourBarCanvas` which uses
    OSMesa for static off-screen OpenGL rendering.
    """ 

    
    def __init__(self, width=0, height=0):
        """Create a ``OSColourBarCanvas``.
        
        :arg width:  Canvas width in pixels
        
        :arg height: Canvas height in pixels
        """

        fslgl.OSMesaCanvasTarget  .__init__(self, width, height)
        cbarcanvas.ColourBarCanvas.__init__(self)
