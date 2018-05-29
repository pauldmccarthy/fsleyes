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


    def __init__(self, overlayList, displayCtx, *args, **kwargs):
        """Create an ``OffScreenColourBarCanvas``.

        See the :class:`.OffscreenCanvasTarget` class for details on the
        parameters.
        """

        fslgl.OffScreenCanvasTarget.__init__(self, *args, **kwargs)
        cbarcanvas.ColourBarCanvas .__init__(self, overlayList, displayCtx)
