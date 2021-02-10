#!/usr/bin/env python
#
# text.py - The Text class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Text` class, which uses the
:mod:`fsleyes_widgets.utils.textbitmap` module, and a :class:`.Texture2D`
object to render text to a GL canvas.
"""


import OpenGL.GL as gl
import numpy     as np

import fsleyes.gl.textures              as textures
import fsleyes_widgets.utils.textbitmap as textbmp


class Text:
    """A ``Text`` object manages a RGBA :class:`.Texture2D` object, allowing
    text to be drawn to a GL canvas.

    The :mod:`fsleyes_widgets.utils.textbitmap` module is used to render the
    text, using ``matplotlib``.

    Usage::

        # create and maintain a reference to a Text object
        import fsleyes.gl.text as gltext
        text = gltext.Text('hello')

        # modify various properties by direct attribute
        # assignment - see __init__ for definitions
        text.xpos     = 0.5
        text.ypos     = 0.5
        text.fgColour = '#FFFFFF'

        # activate your GL context, and call draw()
        text.draw()

        # call destroy() when you're finished
        text.destroy()
    """


    def __init__(self,
                 text=None,
                 xpos=None,
                 ypos=None,
                 fontSize=10,
                 xoff=None,
                 yoff=None,
                 halign=None,
                 valign=None,
                 fgColour=None,
                 bgColour=None,
                 angle=None):
        """Create a ``Text`` object.

        :arg text:     The text to draw.

        :arg xpos:     Position along the horizontal axis as a proportion
                       between 0 (left) and 1 (right).

        :arg xpos:     Position along the vertial axis as a proportion
                       between 0 (bottom) and 1 (top).

        :arg xoff:     Fixed horizontal offset in pixels

        :arg yoff:     Fixed vertical offset in pixels

        :arg fontSize: Font size in points.

        :arg halign:   Horizontal alignemnt - ``'left'``, ``'centre'``, or
                       ``right``.

        :arg valign:   Vertical alignemnt - ``'bottom'``, ``'centre'``, or
                       ``top``.

        :arg fgColour: Colour to draw the text in (any
                       ``matplotlib``-compatible colour specification)

        :arg bgColour: Background colour (default: transparent).

        :arg angle:    Angle, in degrees, by which to rotate the text.
                       NOT IMPLEMENTED YET
        """

        # Every time any display properties change,
        # the text bitmap is re-generated and cached.
        # (see __refreshBitmap). Re-generating the
        # bitmap on every call to draw would be
        # unnecessarily expensive.
        self.__bitmap   = None

        # Access to these attributes is protected,
        # as they induce a bitmap refresh
        self.__text     = text
        self.__fontSize = fontSize
        self.__fgColour = fgColour
        self.__bgColour = bgColour

        # All othjer attributes can be assigned directly
        self.xpos       = xpos
        self.ypos       = ypos
        self.xoff       = xoff
        self.yoff       = yoff
        self.halign     = halign
        self.valign     = valign
        self.angle      = angle
        self.__texture  = textures.Texture2D(
            '{}_{}'.format(type(self).__name__, id(self)),
            interp=gl.GL_LINEAR)


    def destroy(self):
        """Must be called when this ``Text`` is no longer needed. Frees
        texture resources.
        """
        self.__texture.destroy()
        self.__texture = None


    @property
    def fgColour(self):
        """Return the current foreground colour. """
        return self.__fgColour


    @fgColour.setter
    def fgColour(self, value):
        """Set the foreground colour. """
        self.__fgColour = value
        self.__bitmap   = None


    @property
    def bgColour(self):
        """Return the current background colour. """
        return self.__bgColour


    @bgColour.setter
    def bgColour(self, value):
        """Set the background colour. """
        self.__bgColour = value
        self.__bitmap   = None


    @property
    def text(self):
        """Returns the current text value."""
        return self.__text


    @text.setter
    def text(self, value):
        """Update the text."""
        self.__text   = value
        self.__bitmap = None


    @property
    def fontSize(self):
        """Returns the current font size."""
        return self.__fontSize


    @fontSize.setter
    def fontSize(self, value):
        """Update the font size."""
        self.__fontSize = value
        self.__bitmap   = None


    def __refreshBitmap(self):
        """Called when the text bitmap and texture data needs a refresh. """
        bmp = textbmp.textBitmap(self.text,
                                 fontSize=self.fontSize,
                                 fgColour=self.fgColour,
                                 bgColour=self.bgColour)
        bmp = np.fliplr(bmp).transpose([2, 0, 1])

        self.__bitmap = bmp
        self.__texture.set(data=bmp)


    def draw(self, width, height):
        """Draws the texture onto the current GL canvas.

        :arg width:  Width of canvas in pixels
        :arg height: Height of canvas in pixels
        """

        if self.text is None or self.text == '':
            return

        if (width == 0) or (height == 0):
            return

        if self.__bitmap is None:
            self.__refreshBitmap()

        pos  = [self.xpos * width, self.ypos * height]
        bmp  = self.__bitmap
        size = bmp.shape[1:]

        if   self.halign == 'centre': pos[0] -= size[0] / 2.0
        elif self.halign == 'right':  pos[0] -= size[0]

        if   self.valign == 'centre': pos[1] -= size[1] / 2.0
        elif self.valign == 'top':    pos[1] -= size[1]

        if self.xoff is not None: pos[0] += self.xoff
        if self.yoff is not None: pos[1] += self.yoff

        # Set up an ortho view where the
        # display coordinates correspond
        # to the canvas pixel coordinates.
        mm = gl.glGetInteger(gl.GL_MATRIX_MODE)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, width, 0, height, -1, 1)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self.__texture.drawOnBounds(0,
                                    pos[0],
                                    pos[0] + size[0],
                                    pos[1],
                                    pos[1] + size[1],
                                    0, 1)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(mm)
