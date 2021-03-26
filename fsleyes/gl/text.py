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
        text.pos      = (0.5, 0.5)
        text.fgColour = '#FFFFFF'

        # activate your GL context, and call draw()
        text.draw()

        # call destroy() when you're finished
        text.destroy()
    """


    def __init__(self,
                 text=None,
                 pos=None,
                 off=None,
                 coordinates='proportions',
                 fontSize=10,
                 halign=None,
                 valign=None,
                 fgColour=None,
                 bgColour=None,
                 angle=None):
        """Create a ``Text`` object.

        :arg text:        The text to draw.

        :arg pos:         (x, y) position along the horizontal/vertical axes as
                          either a proportion between 0 (left/bottom) and 1
                          (right/top), or as absolute pixels.

        :arg off:         Fixed (x, y) horizontal/vertical offsets in pixels

        :arg coordinates: Whether to interpret ``pos`` as ``'proportions'``
                          (the default), or as absolute ``'pixels'``.

        :arg fontSize:    Font size in points.

        :arg halign:      Horizontal alignemnt - ``'left'``, ``'centre'``, or
                          ``right``.

        :arg valign:      Vertical alignemnt - ``'bottom'``, ``'centre'``, or
                          ``top``.

        :arg fgColour:    Colour to draw the text in (any
                          ``matplotlib``-compatible colour specification)

        :arg bgColour:    Background colour (default: transparent).

        :arg angle:       Angle, in degrees, by which to rotate the text.
                          NOT IMPLEMENTED YET AND PROBABLY NEVER WILL BE

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
        self.pos         = pos
        self.off         = off
        self.coordinates = coordinates
        self.halign      = halign
        self.valign      = valign
        self.angle       = angle
        self.__texture   = textures.Texture2D(
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


    def __clearBitmap(self, old, new):
        """Used by property setters to clear cached bitmap, if a value which
        requires the bitmap to be re-generated is changed.
        """
        if old != new:
            self.__bitmap = None


    @fgColour.setter
    def fgColour(self, value):
        """Set the foreground colour. """
        self.__clearBitmap(self.__fgColour, value)
        self.__fgColour = value


    @property
    def bgColour(self):
        """Return the current background colour. """
        return self.__bgColour


    @bgColour.setter
    def bgColour(self, value):
        """Set the background colour. """
        self.__clearBitmap(self.__bgColour, value)
        self.__bgColour = value


    @property
    def text(self):
        """Returns the current text value."""
        return self.__text


    @text.setter
    def text(self, value):
        """Update the text."""
        self.__clearBitmap(self.__text, value)
        self.__text = value


    @property
    def fontSize(self):
        """Returns the current font size."""
        return self.__fontSize


    @fontSize.setter
    def fontSize(self, value):
        """Update the font size."""
        self.__clearBitmap(self.__fontSize, value)
        self.__fontSize = value


    def __refreshBitmap(self):
        """Called when the text bitmap and texture data needs a refresh. """
        bmp = textbmp.textBitmap(self.text,
                                 fontSize=self.fontSize,
                                 fgColour=self.fgColour,
                                 bgColour=self.bgColour)
        bmp = np.flipud(bmp).transpose([2, 1, 0])

        self.__bitmap = bmp
        self.__texture.set(data=bmp)


    def draw(self, width, height):
        """Draws the texture onto the current GL canvas.

        :arg width:  Width of canvas in pixels
        :arg height: Height of canvas in pixels
        """

        if self.text is None or self.text == '':
            return

        if self.pos is None:
            return

        if (width == 0) or (height == 0):
            return

        if self.__bitmap is None:
            self.__refreshBitmap()

        if self.off is not None: off = list(self.off)
        else:                    off = [0, 0]

        pos = list(self.pos)
        if self.coordinates == 'proportions':
            pos[0] = pos[0] * width
            pos[1] = pos[1] * height

        bmp  = self.__bitmap
        size = bmp.shape[1:]

        if   self.halign == 'centre': pos[0] -= size[0] / 2.0
        elif self.halign == 'right':  pos[0] -= size[0]

        if   self.valign == 'centre': pos[1] -= size[1] / 2.0
        elif self.valign == 'top':    pos[1] -= size[1]

        pos[0] += off[0]
        pos[1] += off[1]

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
