#!/usr/bin/env python
#
# offscreenlightboxcanvas.py - The OffScreenLightBoxCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OffScreenLightBoxCanvas`, which is a
:class:`.LightBoxCanvas` for use in off-screen OpenGL rendering.
"""


import fsleyes.gl as fslgl
from . import        lightboxcanvas


class OffScreenLightBoxCanvas(lightboxcanvas.LightBoxCanvas,
                              fslgl.OffScreenCanvasTarget):
    """The ``OffScreenLightBoxCanvas`` is a :class:`.LightBoxCanvas` which uses
    a :class:`.RenderTexture` as its target, for static off-screen Open GL
    rendering.
    """
    
    def __init__(self,
                 overlayList,
                 displayCtx,
                 zax=0,
                 width=0,
                 height=0):
        """Create an ``OffScreenLightBoxCanvas``.
        
        :arg width:    Canvas width in pixels
        
        :arg height:   Canvas height in pixels

        See :meth:`.LightBoxCanvas.__init__` for details on the other
        arguments.
        """

        fslgl.OffScreenCanvasTarget  .__init__(self, width, height)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               overlayList,
                                               displayCtx,
                                               zax)
