#!/usr/bin/env python
#
# colourbarcanvas.py - Render a colour bar using OpenGL and matplotlib.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBarCanvas`.

The :class:`ColourBarCanvas` contains logic to draw a colour bar (with
labels), and then renders said colour bar as a texture using OpenGL.

See the :mod:`~fsl.utils.colourbarbitmap` module for details on how
the colour bar is created.
"""

import logging

import OpenGL.GL as gl
import numpy     as np

import props

import fsl.utils.colourbarbitmap as cbarbmp
import fsl.fsleyes.gl.textures   as textures


log = logging.getLogger(__name__)


class ColourBarCanvas(props.HasProperties):
    """Contains logic to render a colour bar as an OpenGL texture.
    """

    cmap = props.ColourMap()
    """The :mod:`matplotlib` colour map to use."""

    
    vrange = props.Bounds(ndims=1)
    """The minimum/maximum values to display."""

    
    label = props.String()
    """A label to display under the centre of the colour bar."""

    
    orientation = props.Choice(('horizontal', 'vertical'))
    """Whether the colour bar should be vertical or horizontal. """

    
    labelSide = props.Choice(('top-left', 'bottom-right'))
    """Whether the colour bar labels should be on the top/left, or bottom/right
    of the colour bar (depending upon whether the colour bar orientation is
    horizontal/vertical).
    """

    
    textColour = props.Colour(default=(1, 1, 1, 1))
    """Colour to use for the colour bar label. """

    
    def __init__(self):
        """Adds a few listeners to the properties of this object, to update
        the colour bar when they change.
        """

        self._tex  = None
        self._name = '{}_{}'.format(self.__class__.__name__, id(self))

        self.addGlobalListener(self._name, self.__updateTexture)

            
    def __updateTexture(self, *a):
        self._genColourBarTexture()
        self._refresh()
        

    def _initGL(self):
        """Called automatically by the OpenGL canvas target superclass (see the
        :class:`.WXGLCanvasTarget` and :class:`.OSMesaCanvasTarget` for
        details).

        Generates the colour bar texture.
        """
        self._genColourBarTexture()


    def destroy(self):
        """Should be called when this ``ColourBarCanvas`` is no longer needed.
        Destroys the :class:`.Texture2D` instance used to render the colour
        bar.
        """
        self.removeGlobalListener(self._name)
        self._tex.destroy()


    def _genColourBarTexture(self):
        """Generates a texture containing an image of the colour bar,
        according to the current property values.
        """

        if not self._setGLContext():
            return

        w, h = self._getSize()

        if w == 0 or h == 0:
            if self.orientation == 'horizontal': w, h = 600, 200
            else:                                w, h = 200, 600

        if self.orientation == 'horizontal':
            if  self.labelSide == 'top-left': labelSide = 'top'
            else:                             labelSide = 'bottom'
        else:
            if  self.labelSide == 'top-left': labelSide = 'left'
            else:                             labelSide = 'right'

        if self.cmap is None:
            bitmap = np.zeros((w, h, 4), dtype=np.uint8)
        else:
            bitmap = cbarbmp.colourBarBitmap(
                cmap=self.cmap,
                vmin=self.vrange.xlo,
                vmax=self.vrange.xhi,
                width=w,
                height=h,
                label=self.label,
                orientation=self.orientation,
                labelside=labelSide,
                textColour=self.textColour)

        if self._tex is None:
            self._tex = textures.Texture2D('{}_{}'.format(
                type(self).__name__, id(self)), gl.GL_LINEAR)

        # The bitmap has shape W*H*4, but the
        # Texture2D instance needs it in shape
        # 4*W*H
        bitmap = np.fliplr(bitmap).transpose([2, 0, 1])
            
        self._tex.setData(bitmap)
        self._tex.refresh()


    def _draw(self):
        """Renders the colour bar texture using all available canvas space."""

        if not self._setGLContext():
            return
        
        width, height = self._getSize()

        # viewport
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, 1, 0, 1, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glShadeModel(gl.GL_FLAT)

        self._tex.drawOnBounds(0, 0, 1, 0, 1, 0, 1)
        
        self._postDraw()
