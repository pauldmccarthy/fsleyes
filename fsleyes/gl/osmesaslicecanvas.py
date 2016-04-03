#!/usr/bin/env python
#
# osmesaslicecanvas.py - The OSMesaSliceCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OSMesaSliceCanvas`, which is a
:class:`.SliceCanvas` for use with OSMesa (off-screen OpenGL rendering).
"""


import fsl.fsleyes.gl   as fslgl
import slicecanvas      as sc


class OSMesaSliceCanvas(sc.SliceCanvas, fslgl.OSMesaCanvasTarget):
    """The ``OSMesaSliceCanvas`` is a :class:`.SliceCanvas` which uses OSMesa
    for static off-screen OpenGL rendering.
    """
    
    def __init__(self,
                 overlayList,
                 displayCtx,
                 zax=0,
                 width=0,
                 height=0):
        """Create an ``OSMesaSliceCanvas``.
        
        :arg width:    Canvas width in pixels
        
        :arg height:   Canvas height in pixels

        See :meth:`.SliceCanvas.__init__` for details on the other arguments.
        """

        fslgl.OSMesaCanvasTarget.__init__(self, width, height)
        sc.SliceCanvas          .__init__(self, overlayList, displayCtx, zax)
