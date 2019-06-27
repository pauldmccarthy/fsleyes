#!/usr/bin/env python
#
# colourbarcanvas.py - Render a colour bar using OpenGL and matplotlib.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBarCanvas`.

The :class:`ColourBarCanvas` uses a :class:`.ColourBar` draw a colour bar
(with labels), and then renders said colour bar as a texture using OpenGL.

See the :mod:`~fsleyes.controls.colourbar` and
:mod:`fsleyes_widgets.utils.colourbarbitmap` modules for details on how the
colour bar is created.
"""


import logging

import numpy     as np
import OpenGL.GL as gl

import fsleyes_props                         as props
import fsl.utils.idle                        as idle
import fsleyes.controls.colourbar            as cbar
import fsleyes.gl.textures                   as textures


log = logging.getLogger(__name__)


class ColourBarCanvas(props.HasProperties):
    """Contains logic to render a colour bar as an OpenGL texture. """


    highDpi = props.Boolean(default=False)
    """Scale colour bar canvas for high-resolution screens. """


    barSize = props.Percentage(default=100)
    """Size of the colour bar along its major axis, as a proportion of
    the available space.
    """


    def __init__(self, overlayList, displayCtx):
        """Adds a few listeners to the properties of this object, to update
        the colour bar when they change.
        """

        self.__tex  = None
        self.__name = '{}_{}'.format(self.__class__.__name__, id(self))
        self.__cbar = cbar.ColourBar(overlayList, displayCtx)
        self.__cbar.register(self.__name, self.updateColourBarTexture)

        self.addListener('barSize', self.__name, self.updateColourBarTexture)
        self.addListener('highDpi', self.__name, self.__highDpiChanged)


    @property
    def colourBar(self):
        """Returns a reference to the :class:`.ColourBar` object that actually
        generates the colour bar bitmap.
        """
        return self.__cbar


    def updateColourBarTexture(self, *a):
        """Called whenever the colour bar texture needs to be updated. """

        def update():
            self.__genColourBarTexture()
            self.Refresh()

        name = '{}_updateColourBarTexture'.format(id(self))

        idle.idle(update, name=name, skipIfQueued=True)


    def _initGL(self):
        """Called automatically by the OpenGL canvas target superclass (see the
        :class:`.WXGLCanvasTarget` and :class:`.OSMesaCanvasTarget` for
        details).

        Generates the colour bar texture.
        """
        self.__genColourBarTexture()


    def __highDpiChanged(self, *a):
        """Called when the :attr:`highDpi` property changes. Calls the
        :meth:`.GLCanvasTarget.EnableHighDPI` method.
        """
        self.EnableHighDPI(self.highDpi)
        self.updateColourBarTexture()


    def destroy(self):
        """Should be called when this ``ColourBarCanvas`` is no longer needed.
        Destroys the :class:`.Texture2D` and :class:`.ColourBar` instances
        used to render the colour bar.
        """
        self.__cbar.deregister(self.__name)
        self.__cbar.destroy()

        if self.__tex is not None:
            self.__tex.destroy()

        self.removeListener('barSize', self.__name)
        self.removeListener('highDpi', self.__name)

        self.__tex  = None
        self.__cbar = None


    def __genColourBarTexture(self):
        """Retrieves a colour bar bitmap from the :class:`.ColourBar`, and
        copies it to a :class:`.Texture2D`.
        """

        if not self._setGLContext():
            return

        # we may have already
        # been destroyed
        if self.__cbar is None:
            return

        w, h = self.GetSize()

        if w < 50 or h < 50:
            return

        if self.__cbar.orientation == 'vertical': h = h * self.barSize / 100.0
        else:                                     w = w * self.barSize / 100.0

        scale  = self.GetScale()
        bitmap = self.__cbar.colourBar(w, h, scale)

        # The bitmap has shape W*H*4, but
        # Texture2D instances need it in
        # shape 4*W*H
        if bitmap is None:
            return

        bitmap = np.fliplr(bitmap).transpose([2, 0, 1])

        if self.__tex is None:
            self.__tex = textures.Texture2D('{}_{}'.format(
                type(self).__name__, id(self)), interp=gl.GL_LINEAR)

        self.__tex.set(data=bitmap)


    def _draw(self):
        """Renders the colour bar texture using all available canvas space."""

        if self.__tex is None or not self._setGLContext():
            return

        width, height = self.GetScaledSize()

        # viewport
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, 1, 0, 1, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glClearColor(*self.__cbar.bgColour)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glShadeModel(gl.GL_FLAT)

        xmin, xmax = 0, 1
        ymin, ymax = 0, 1
        off        = (100 - self.barSize) / 100.0

        if self.colourBar.orientation == 'vertical':
            ymin += off / 2.0
            ymax -= off / 2.0
        else:
            xmin += off / 2.0
            xmax -= off / 2.0

        self.__tex.drawOnBounds(0, xmin, xmax, ymin, ymax, 0, 1)
