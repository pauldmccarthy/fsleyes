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

        self.addDisplayListeners()
        self.refreshImageTexture()

        def init():
            fslgl.glrgbvolume_funcs.init(self)
            self.notify()

        idle.idleWhen(init, self.textureReady)


    def destroy(self):
        """Must be called when this ``GLRGBVolume`` is no longer needed. """
        fslgl.glvolume_funcs.destroy(self)
        glresources.delete(self.imageTexture.name)
        glimageobject.GLImageObject.destroy(self)
        self.imageTexture = None


    def addDisplayListeners(self):
        """
        """
        pass


    def removeDisplayListeners(self):
        """
        """
        pass


    def ready(self):
        """
        """
        return (self.shader is not None) and self.textureReady()


    def textureReady(self):
        """
        """
        return ((self.imageTexture is not None) and
                (self.imageTexture.ready()))


    def updateShaderState(self, *args, **kwargs):
        """
        """
        fslgl.glrgbvolume_funcs.updateShaderState()
        self.notify()


    def refreshImageTexture(self):
        """
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


    def preDraw(self, xform=None, bbox=None):
        """
        """
        self.imageTexture.bindTexture(gl.GL_TEXTURE0)


    def draw2D(self, zpos, axes, xform=None, bbox=None):
        """
        """
        fslgl.glrgbvolume_funcs.draw2D(self, zpos, axes, xform, bbox)


    def drawAll(self, axes, zposes, xforms):
        """
        """
        fslgl.glrgbvolume_funcs.drawAll(self, axes, zposes, xforms)


    def draw3D(self, xform=None, bbox=None):
        """
        """
        pass


    def postDraw(self, xform=None, bbox=None):
        """
        """
        self.imageTexture.unbindTexture()
