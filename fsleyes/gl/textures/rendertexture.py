#!/usr/bin/env python
#
# rendertexture.py - The RenderTexture and GLObjectRenderTexture classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RenderTexture` and
:class:`GLObjectRenderTexture` classes, which are :class:`.Texture2D`
sub-classes intended to be used as targets for off-screen rendering.

These classes are used by the :class:`.SliceCanvas` and
:class:`.LightBoxCanvas` classes for off-screen rendering. See also the
:class:`.RenderTextureStack`, which uses :class:`RenderTexture` instances.
"""


import logging

import OpenGL.GL                        as gl
import OpenGL.raw.GL._types             as gltypes
import OpenGL.GL.EXT.framebuffer_object as glfbo

import fsleyes.gl.routines as glroutines
from . import                 texture


log = logging.getLogger(__name__)


class RenderTexture(texture.Texture2D):
    """The ``RenderTexture`` class encapsulates a 2D texture, a frame buffer,
    and a render buffer, intended to be used as a target for off-screen
    rendering. Using a ``RenderTexture`` (``tex`` in the example below)
    as the rendering target is easy::

        # Set the texture size in pixels
        tex.setSize(1024, 768)

        # Bind the texture/frame buffer, and configure
        # the viewport for orthoghraphic display.
        lo = (0.0, 0.0, 0.0)
        hi = (1.0, 1.0, 1.0)
        tex.bindAsRenderTarget()
        tex.setRenderViewport(0, 1, lo, hi)

        # ...
        # draw the scene
        # ...

        # Unbind the texture/frame buffer,
        # and restore the previous viewport.
        tex.unbindAsRenderTarget()
        tex.restoreViewport()


    The contents of the ``RenderTexture`` can later be drawn to the screen
    via the :meth:`.Texture2D.draw` or :meth:`.Texture2D.drawOnBounds`
    methods.
    """

    def __init__(self, name, interp=gl.GL_NEAREST):
        """Create a ``RenderTexture``.

        :arg name:   A unique name for this ``RenderTexture``.

        :arg interp: Texture interpolation - either ``GL_NEAREST`` (the
                     default) or ``GL_LINEAR``.

        .. note:: A rendering target must have been set for the GL context
                  before a frame buffer can be created ... in other words,
                  call ``context.SetCurrent`` before creating a
                  ``RenderTexture``.
        """

        texture.Texture2D.__init__(self, name, interp)

        self.__frameBuffer  = glfbo.glGenFramebuffersEXT(1)
        self.__renderBuffer = glfbo.glGenRenderbuffersEXT(1)

        log.debug('Created fbo {} and render buffer {}'.format(
            self.__frameBuffer, self.__renderBuffer))

        self.__oldSize         = None
        self.__oldProjMat      = None
        self.__oldMVMat        = None
        self.__oldFrameBuffer  = None
        self.__oldRenderBuffer = None


    def destroy(self):
        """Must be called when this ``RenderTexture`` is no longer needed.
        Destroys the frame buffer and render buffer, and calls
        :meth:`.Texture2D.destroy`.
        """

        texture.Texture2D.destroy(self)

        log.debug('Deleting RB{}/FBO{}'.format(
            self.__renderBuffer,
            self.__frameBuffer))
        glfbo.glDeleteFramebuffersEXT(    gltypes.GLuint(self.__frameBuffer))
        glfbo.glDeleteRenderbuffersEXT(1, gltypes.GLuint(self.__renderBuffer))


    def setData(self, data):
        """Raises a :exc:`NotImplementedError`. The ``RenderTexture`` derives
        from the :class:`.Texture2D` class, but is not intended to have its
        texture data manually set - see the :class:`.Texture2D` documentation.
        """
        raise NotImplementedError('Texture data cannot be set for {} '
                                  'instances'.format(type(self).__name__))


    def setRenderViewport(self, xax, yax, lo, hi):
        """Configures the GL viewport for a 2D orthographic display. See the
        :func:`.routines.show2D` function.

        The existing viewport settings are cached, and can be restored via
        the :meth:`restoreViewport` method.

        :arg xax: The display coordinate system axis which corresponds to the
                  horizontal screen axis.

        :arg yax: The display coordinate system axis which corresponds to the
                  vertical screen axis.

        :arg lo:  A tuple containing the minimum ``(x, y, z)`` display
                  coordinates.

        :arg hi:  A tuple containing the maximum ``(x, y, z)`` display
                  coordinates.
        """

        if self.__oldSize    is not None or \
           self.__oldProjMat is not None or \
           self.__oldMVMat   is not None:
            raise RuntimeError('RenderTexture RB{}/FBO{} has already '
                               'configured the viewport'.format(
                                   self.__renderBuffer,
                                   self.__frameBuffer))

        log.debug('Configuring viewport for RB{}/FBO{}'.format(
            self.__renderBuffer,
            self.__frameBuffer))

        width, height = self.getSize()

        self.__oldSize    = gl.glGetIntegerv(gl.GL_VIEWPORT)
        self.__oldProjMat = gl.glGetFloatv(  gl.GL_PROJECTION_MATRIX)
        self.__oldMVMat   = gl.glGetFloatv(  gl.GL_MODELVIEW_MATRIX)

        glroutines.show2D(xax, yax, width, height, lo, hi)


    def restoreViewport(self):
        """Restores the GL viewport settings which were saved via a prior call
        to :meth:`setRenderViewport`.
        """

        if self.__oldSize    is None or \
           self.__oldProjMat is None or \
           self.__oldMVMat   is None:
            raise RuntimeError('RenderTexture RB{}/FBO{} has not '
                               'configured the viewport'.format(
                                   self.__renderBuffer,
                                   self.__frameBuffer))

        log.debug('Clearing viewport (from RB{}/FBO{})'.format(
            self.__renderBuffer,
            self.__frameBuffer))

        gl.glViewport(*self.__oldSize)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(self.__oldProjMat)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(self.__oldMVMat)

        self.__oldSize    = None
        self.__oldProjMat = None
        self.__oldMVMat   = None


    def bindAsRenderTarget(self):
        """Configures the frame buffer and render buffer of this
        ``RenderTexture`` as the targets for rendering.

        The existing farme buffer and render buffer are cached, and can be
        restored via the :meth:`unbindAsRenderTarget` method.
        """

        if self.__oldFrameBuffer  is not None or \
           self.__oldRenderBuffer is not None:
            raise RuntimeError('RenderTexture RB{}/FBO{} is not bound'.format(
                self.__renderBuffer,
                self.__frameBuffer))

        self.__oldFrameBuffer  = gl.glGetIntegerv(
            glfbo.GL_FRAMEBUFFER_BINDING_EXT)
        self.__oldRenderBuffer = gl.glGetIntegerv(
            glfbo.GL_RENDERBUFFER_BINDING_EXT)

        log.debug('Setting RB{}/FBO{} as render target'.format(
            self.__renderBuffer,
            self.__frameBuffer))

        glfbo.glBindFramebufferEXT( glfbo.GL_FRAMEBUFFER_EXT,
                                    self.__frameBuffer)
        glfbo.glBindRenderbufferEXT(glfbo.GL_RENDERBUFFER_EXT,
                                    self.__renderBuffer)


    def unbindAsRenderTarget(self):
        """Restores the frame buffer and render buffer which were saved via a
        prior call to :meth:`bindAsRenderTarget`.
        """

        if self.__oldFrameBuffer  is None or \
           self.__oldRenderBuffer is None:
            raise RuntimeError('RenderTexture RB{}/FBO{} '
                               'has not been bound'.format(
                                   self.__renderBuffer,
                                   self.__frameBuffer))

        log.debug('Restoring render target to RB{}/FBO{} '
                  '(from RB{}/FBO{})'.format(
                      self.__oldRenderBuffer,
                      self.__oldFrameBuffer,
                      self.__renderBuffer,
                      self.__frameBuffer))

        glfbo.glBindFramebufferEXT( glfbo.GL_FRAMEBUFFER_EXT,
                                    self.__oldFrameBuffer)
        glfbo.glBindRenderbufferEXT(glfbo.GL_RENDERBUFFER_EXT,
                                    self.__oldRenderBuffer)

        self.__oldFrameBuffer  = None
        self.__oldRenderBuffer = None


    def refresh(self):
        """Overrides :meth:`.Texture2D.refresh`. Calls the base-class
        implementation, and ensures that the frame buffer and render buffer
        of this ``RenderTexture`` are configured correctly.
        """
        texture.Texture2D.refresh(self)

        width, height = self.getSize()

        # Configure the frame buffer
        self.bindTexture()
        self.bindAsRenderTarget()
        glfbo.glFramebufferTexture2DEXT(
            glfbo.GL_FRAMEBUFFER_EXT,
            glfbo.GL_COLOR_ATTACHMENT0_EXT,
            gl   .GL_TEXTURE_2D,
            self.getTextureHandle(),
            0)

        # and the render buffer
        glfbo.glRenderbufferStorageEXT(
            glfbo.GL_RENDERBUFFER_EXT,
            gl.GL_DEPTH24_STENCIL8,
            width,
            height)

        glfbo.glFramebufferRenderbufferEXT(
            glfbo.GL_FRAMEBUFFER_EXT,
            gl.GL_DEPTH_STENCIL_ATTACHMENT,
            glfbo.GL_RENDERBUFFER_EXT,
            self.__renderBuffer)

        # Get the FBO status before unbinding it -
        # the Apple software renderer will return
        # FRAMEBUFFER_UNDEFINED otherwise.
        status = glfbo.glCheckFramebufferStatusEXT(glfbo.GL_FRAMEBUFFER_EXT)

        self.unbindAsRenderTarget()
        self.unbindTexture()

        # Complain if something is not right
        if status != glfbo.GL_FRAMEBUFFER_COMPLETE_EXT:
            raise RuntimeError('An error has occurred while '
                               'configuring the frame buffer')


class GLObjectRenderTexture(RenderTexture):
    """The ``GLObjectRenderTexture`` is a :class:`RenderTexture` intended to
    be used for rendering :class:`.GLObject` instances off-screen.


    The advantage of using a ``GLObjectRenderTexture`` over a
    :class:`.RenderTexture` is that a ``GLObjectRenderTexture`` will
    automatically adjust its size to suit the resolution of the
    :class:`.GLObject` - see the :meth:`.GLObject.getDataResolution` method.


    In order to accomplish this, the :meth:`setAxes` method must be called
    whenever the display orientation changes, so that the render texture
    size can be re-calculated.
    """

    def __init__(self, name, globj, xax, yax, maxResolution=2048):
        """Create a ``GLObjectRenderTexture``.

        :arg name:          A unique name for this ``GLObjectRenderTexture``.

        :arg globj:         The :class:`.GLObject` instance which is to be
                            rendered.

        :arg xax:           Index of the display coordinate system axis to be
                            used as the horizontal render texture axis.

        :arg yax:           Index of the display coordinate system axis to be
                            used as the vertical render texture axis.

        :arg maxResolution: Maximum resolution in pixels, along either the
                            horizontal or vertical axis, for this
                            ``GLObjectRenderTexture``.
        """

        self.__globj         = globj
        self.__xax           = xax
        self.__yax           = yax
        self.__maxResolution = maxResolution

        RenderTexture.__init__(self, name)

        name = '{}_{}'.format(self.getTextureName(), id(self))
        globj.register(name, self.__updateSize)

        self.__updateSize()


    def destroy(self):
        """Must be called when this ``GLObjectRenderTexture`` is no longer
        needed. Removes the update listener from the :class:`.GLObject`, and
        calls :meth:`.RenderTexture.destroy`.
        """

        name = '{}_{}'.format(self.getTextureName(), id(self))
        self.__globj.deregister(name)
        RenderTexture.destroy(self)


    def setAxes(self, xax, yax):
        """This method must be called when the display orientation of the
        :class:`GLObject` changes. It updates the size of this
        ``GLObjectRenderTexture`` so that the resolution and aspect ratio
        of the ``GLOBject`` are maintained.
        """
        self.__xax = xax
        self.__yax = yax
        self.__updateSize()


    def setSize(self, width, height):
        """Raises a :exc:`NotImplementedError`. The size of a
        ``GLObjectRenderTexture`` is set automatically.
        """
        raise NotImplementedError(
            'Texture size cannot be set for {} instances'.format(
                type(self).__name__))


    def __updateSize(self, *a):
        """Updates the size of this ``GLObjectRenderTexture``, basing it
        on the resolution returned by the :meth:`.GLObject.getDataResolution`
        method. If that method returns ``None``, a default resolution is used.
        """
        globj  = self.__globj
        maxRes = self.__maxResolution

        resolution = globj.getDataResolution(self.__xax, self.__yax)

        # Default resolution is based on the canvas size
        if resolution is None:

            size                   = gl.glGetIntegerv(gl.GL_VIEWPORT)
            width                  = size[2]
            height                 = size[3]
            resolution             = [100] * 3
            resolution[self.__xax] = width
            resolution[self.__yax] = height

            log.debug('Using default resolution '
                      'for GLObject {}: {}'.format(
                          type(globj).__name__,
                          resolution))

        width  = resolution[self.__xax]
        height = resolution[self.__yax]

        if any((width <= 0, height <= 0)):
            raise ValueError('Invalid GLObject resolution: {}'.format(
                (width, height)))

        if width > maxRes or height > maxRes:
            ratio = min(width, height) / float(max(width, height))

            if width > height:
                width  = maxRes
                height = width * ratio
            else:
                height = maxRes
                width  = height * ratio

            width  = int(round(width))
            height = int(round(height))

        log.debug('Setting {} texture resolution to {}x{}'.format(
            type(globj).__name__, width, height))

        RenderTexture.setSize(self, width, height)
