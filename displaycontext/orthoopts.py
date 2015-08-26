#!/usr/bin/env python
#
# orthoopts.py - Options controlling an ortho view layout.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import copy

import props

import sceneopts


class OrthoOpts(sceneopts.SceneOpts):

    
    showXCanvas = props.Boolean(default=True)
    """Toggles display of the X canvas."""

    
    showYCanvas = props.Boolean(default=True)
    """Toggles display of the Y canvas."""

    
    showZCanvas = props.Boolean(default=True)
    """Toggles display of the Z canvas."""

    
    showLabels = props.Boolean(default=True)
    """If ``True``, labels showing anatomical orientation are displayed on
    each of the canvases.
    """
    

    layout = props.Choice(('horizontal', 'vertical', 'grid'))
    """How should we lay out each of the three canvases?"""


    xzoom = copy.copy(sceneopts.SceneOpts.zoom)
    """Controls zoom on the X canvas."""

    
    yzoom = copy.copy(sceneopts.SceneOpts.zoom)
    """Controls zoom on the Y canvas."""

    
    zzoom = copy.copy(sceneopts.SceneOpts.zoom)
    """Controls zoom on the Z canvas.

    Note that the :class:`OrthoOpts` class also inherits a ``zoom`` property
    from the :class:`.CanvasOpts` class - this 'global' property can be used
    to adjust all canvas zoom levels simultaneously.
    """
