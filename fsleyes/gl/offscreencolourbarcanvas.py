#!/usr/bin/env python
#
# offscreencolourbarcanvas.py - The OffScreenColourBarCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OffScreenColourBarCanvas`, which is a
:class:`.ColourBarCanvas` for use in off-screen OpenGL rendering.
"""


import fsleyes.gl             as fslgl
from . import colourbarcanvas as cbarcanvas


class OffScreenColourBarCanvas(cbarcanvas.ColourBarCanvas,
                               fslgl.OffScreenCanvasTarget):
    """The ``OffScreenColourBarCanvas`` is a :class:`.ColourBarCanvas` which 
    uses a :class:`.RenderTexture` for static off-screen OpenGL rendering.
    """ 

    
    def __init__(self, width=0, height=0):
        """Create an ``OffScreenColourBarCanvas``.
        
        :arg width:  Canvas width in pixels
        
        :arg height: Canvas height in pixels
        """

        fslgl.OffScreenCanvasTarget.__init__(self, width, height)
        cbarcanvas.ColourBarCanvas .__init__(self)
