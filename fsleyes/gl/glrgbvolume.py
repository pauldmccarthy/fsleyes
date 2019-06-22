#!/usr/bin/env python
#
# glrgbvolume.py - The GLRGBVolume class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLRGBVolume` class, used for rendering
RGB(A) :class:`.Image` overlays.
"""


import OpenGL.GL            as gl

import fsl.utils.idle       as idle

import fsleyes.gl           as fslgl
import fsleyes.gl.textures  as textures
import fsleyes.gl.resources as glresources
from . import                  glimageobject


class GLRGBVolume(glimageobject.GLImageObject):
    """The ``GLRGBVolume`` class is used to render RGB(A) :class:`.Image`
    overlays. The RGB(A) value at each voxel is directly used as the colour
    for that voxel.
    """


    def __init__(self, image, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLRGBVolume``.

        :arg image:       The :class:`.Image` instance.
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg canvas:      The canvas doing the drawing.
        :arg threedee:    2D or 3D rendering
        """
        glimageobject.GLImageObject.__init__(self,
                                             image,
                                             overlayList,
                                             displayCtx,
                                             canvas,
                                             threedee)

        self.shader       = None
        self.imageTexture = None

        self.addListeners()
        self.refreshImageTexture()

        def init():
            fslgl.glrgbvolume_funcs.init(self)
            self.notify()

        idle.idleWhen(init, self.textureReady)


    def destroy(self):
        """Must be called when this ``GLRGBVolume`` is no longer needed. """
        self.removeListeners()
        fslgl.glvolume_funcs.destroy(self)
        glresources.delete(self.imageTexture.name)
        glimageobject.GLImageObject.destroy(self)
        self.imageTexture = None


    def addListeners(self):
        """Adds listeners to :class:`.Display` and :class:`.VolumeRGBOpts`
        properties which should result in the display being refreshed.
        """
        display = self.display
        opts    = self.opts
        name    = self.name

        def shader(*a):
            self.updateShaderState()

        def notify(*a):
            self.notify()

        display.addListener('brightness',    name, shader, weak=False)
        display.addListener('contrast',      name, shader, weak=False)
        display.addListener('alpha',         name, shader, weak=False)
        opts   .addListener('interpolation', name, self._interpChanged)
        opts   .addListener('transform',     name, notify, weak=False)
        opts   .addListener('displayXform',  name, notify, weak=False)


    def removeListeners(self):
        """Removes the property listeners that were added in
        :meth:`addListeners`.
        """

        display = self.display
        opts    = self.opts
        name    = self.name

        display.removeListener('brightness',    name)
        display.removeListener('contrast',      name)
        display.removeListener('alpha',         name)
        opts   .removeListener('interpolation', name)
        opts   .removeListener('transform',     name)
        opts   .removeListener('displayXform',  name)


    def ready(self):
        """Returns ``True`` if this ``GLRGBVolume`` is ready to be used,
        ``False`` otherwise.
        """
        return (self.shader is not None) and self.textureReady()


    def textureReady(self):
        """Returns ``True`` if the image texture is ready to be used,
        ``False``otherwise.
        """
        return ((self.imageTexture is not None) and
                (self.imageTexture.ready()))


    def updateShaderState(self, *args, **kwargs):
        """Calls :func:`.glrgbvolume_funcs.updateShaderState`. """
        fslgl.glrgbvolume_funcs.updateShaderState(self)
        self.notify()


    def refreshImageTexture(self):
        """(Re-)creates an :class:`.ImageTexture` or :class:`.ImageTexture2D`
        to store the image data.
        """

        texName = '{}_{}' .format(type(self).__name__, id(self.image))
        nvals   = len(self.overlay.dtype)

        self.imageTexture = glresources.get(
            texName,
            textures.createImageTexture,
            texName,
            self.image,
            nvals=nvals,
            notify=False)

        self.imageTexture.register(self.name, self.__imageTextureChanged)


    def _interpChanged(self, *a):
        """Called when the :attr:`.VolumeRGBOpts.interpolation` changes.
        Updates the image texture.
        """

        opts = self.opts

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        self.imageTexture.set(interp=interp)


    def __imageTextureChanged(self, *a):
        """Called when the ``imageTexture`` changes. Calls
        :meth:`updateShaderState`.
        """
        self.updateShaderState()


    def preDraw(self, xform=None, bbox=None):
        """Called before a draw. Binds the image texture. """
        self.imageTexture.bindTexture(gl.GL_TEXTURE0)


    def draw2D(self, zpos, axes, xform=None, bbox=None):
        """Calls :func:`.glrgbvolume_funcs.draw2D`. """
        fslgl.glrgbvolume_funcs.draw2D(self, zpos, axes, xform, bbox)


    def drawAll(self, axes, zposes, xforms):
        """Calls :func:`.glrgbvolume_funcs.drawAll`. """
        fslgl.glrgbvolume_funcs.drawAll(self, axes, zposes, xforms)


    def draw3D(self, xform=None, bbox=None):
        """Does nothing. """
        pass


    def postDraw(self, xform=None, bbox=None):
        """Called after a draw. Unbinds the image texture. """
        self.imageTexture.unbindTexture()
