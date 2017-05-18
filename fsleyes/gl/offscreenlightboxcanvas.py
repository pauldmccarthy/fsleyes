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
                 zax,
                 *args,
                 **kwargs):
        """Create an ``OffScreenLightBoxCanvas``.

        See the :class:`.SliceCanvas` and :class:`.OffscreenCanvasTarget`
        classes for details on the other arguments.
        """

        fslgl.OffScreenCanvasTarget  .__init__(self, *args, **kwargs)
        lightboxcanvas.LightBoxCanvas.__init__(self,
                                               overlayList,
                                               displayCtx,
                                               zax)

        # LightBoxCanvas only updates itself
        # when a slice property changes. So
        # we force an initialisation just
        # in case.
        self._slicePropsChanged()
