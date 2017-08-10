#!/usr/bin/env python
#
# offscreenscene3dcanvas.py - The OffScreenScene3DCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OffScreenScene3DCanvas`, which is a
:class:`.Scene3DCanvas` for use in off-screen OpenGL rendering.
"""


import fsleyes.gl           as fslgl
from . import scene3dcanvas as sc


class OffScreenScene3DCanvas(sc.Scene3DCanvas, fslgl.OffScreenCanvasTarget):
    """The ``OffScreensScene3DCanvas`` is a :class:`.Scene3DCanvas` which uses
    a :class:`.RenderTexture` as its target, for static off-screen OpenGL
    rendering.
    """

    def __init__(self,
                 overlayList,
                 displayCtx,
                 *args,
                 **kwargs):
        """Create an ``OffScreenScene3DCanvas``.

        See the :class:`.Scene3DCanvas` and :class:`.OffscreenCanvasTarget`
        classes for details on the other arguments.
        """

        fslgl.OffScreenCanvasTarget.__init__(self, *args, **kwargs)
        sc.Scene3DCanvas           .__init__(self,
                                             overlayList,
                                             displayCtx)
