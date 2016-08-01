#!/usr/bin/env python
#
# offscreenslicecanvas.py - The OffScreenSliceCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OffScreenSliceCanvas`, which is a
:class:`.SliceCanvas` for use in off-screen OpenGL rendering.
"""


import fsleyes.gl         as fslgl
from . import slicecanvas as sc


class OffScreenSliceCanvas(sc.SliceCanvas, fslgl.OffScreenCanvasTarget):
    """The ``OffScreenSliceCanvas`` is a :class:`.SliceCanvas` which uses
    a :class:`.RenderTexture` as its target, for static off-screen OpenGL
    rendering.
    """
    
    def __init__(self,
                 overlayList,
                 displayCtx,
                 zax=0,
                 width=0,
                 height=0):
        """Create an ``OffScreenSliceCanvas``.
        
        :arg width:    Canvas width in pixels
        
        :arg height:   Canvas height in pixels

        See :meth:`.SliceCanvas.__init__` for details on the other arguments.
        """

        fslgl.OffScreenCanvasTarget.__init__(self, width, height)
        sc.SliceCanvas             .__init__(self,
                                             overlayList,
                                             displayCtx,
                                             zax)
