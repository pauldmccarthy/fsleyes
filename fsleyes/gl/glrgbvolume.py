#!/usr/bin/env python
#
# glrgbvolume.py - The GLRGBVolume class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLRGBVolume` class, used for rendering
RGB(A) :class:`.Image` overlays.
"""

import numpy                    as np
import OpenGL.GL                as gl

import fsl.utils.idle           as idle
import fsl.transform.affine     as affine

import fsleyes.gl               as fslgl
import fsleyes.gl.routines      as glroutines
import fsleyes.gl.textures      as textures
import fsleyes.gl.resources     as glresources
import fsleyes.gl.glimageobject as glimageobject
import fsleyes.gl.globject      as globject


class GLRGBVolume(glimageobject.GLImageObject, globject.GLObject):
    """The ``GLRGBVolume`` class is used to render RGB(A) :class:`.Image`
    overlays. The RGB(A) value at each voxel is directly used as the colour
    for that voxel.
    """


    def __init__(self, image, overlayList, displayCtx, threedee):
        """Create a ``GLRGBVolume``.

        :arg image:       The :class:`.Image` instance.
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg threedee:    2D or 3D rendering
        """
        globject.GLObject.__init__(self,
                                   image,
                                   overlayList,
                                   displayCtx,
                                   threedee)
        glimageobject.GLImageObject.__init__(self)

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
        opts   .addListener('rColour',       name, shader, weak=False)
        opts   .addListener('gColour',       name, shader, weak=False)
        opts   .addListener('bColour',       name, shader, weak=False)
        opts   .addListener('suppressR',     name, shader, weak=False)
        opts   .addListener('suppressG',     name, shader, weak=False)
        opts   .addListener('suppressB',     name, shader, weak=False)
        opts   .addListener('suppressA',     name, shader, weak=False)
        opts   .addListener('suppressMode',  name, shader, weak=False)
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
        opts   .removeListener('rColour',       name)
        opts   .removeListener('gColour',       name)
        opts   .removeListener('bColour',       name)
        opts   .removeListener('suppressR',     name)
        opts   .removeListener('suppressG',     name)
        opts   .removeListener('suppressB',     name)
        opts   .removeListener('suppressA',     name)
        opts   .removeListener('suppressMode',  name)
        opts   .removeListener('transform',     name)
        opts   .removeListener('displayXform',  name)


    def ready(self):
        """Returns ``True`` if this ``GLRGBVolume`` is ready to be used,
        ``False`` otherwise.
        """
        return (self.shader is not None) and self.textureReady()


    def textureReady(self):
        """Returns ``True`` if the image texture is ready to be used,
        ``False`` otherwise.
        """
        return ((self.imageTexture is not None) and
                (self.imageTexture.ready()))


    def updateShaderState(self, *args, **kwargs):
        """Calls :func:`.gl14.glrgbvolume_funcs.updateShaderState` or
        :func:`.gl12.glrgbvolume_funcs.updateShaderState`.
        """
        fslgl.glrgbvolume_funcs.updateShaderState(self)
        self.notify()


    def refreshImageTexture(self):
        """(Re-)creates an :class:`.ImageTexture` or :class:`.ImageTexture2D`
        to store the image data.
        """

        texName = '{}_{}' .format(type(self).__name__, id(self.image))
        nvals   = self.overlay.nvals
        interp  = self.opts.interpolation

        if interp == 'true_spline': prefilter = textures.splineFilter
        else:                       prefilter = None

        if interp == 'none': interp = gl.GL_NEAREST
        else:                interp = gl.GL_LINEAR

        if nvals == 1:
            nvals = self.overlay.shape[-1]

        self.imageTexture = glresources.get(
            texName,
            textures.createImageTexture,
            texName,
            self.overlay,
            nvals=nvals,
            interp=interp,
            prefilter=prefilter,
            notify=False)

        self.imageTexture.register(self.name, self.__imageTextureChanged)


    def _interpChanged(self, *a):
        """Called when the :attr:`.VolumeRGBOpts.interpolation` changes.
        Updates the image texture.
        """

        interp = self.opts.interpolation

        if interp == 'true_spline': prefilter = textures.splineFilter
        else:                       prefilter = None

        if interp == 'none': interp = gl.GL_NEAREST
        else:                interp = gl.GL_LINEAR

        self.imageTexture.set(interp=interp, prefilter=prefilter)


    def __imageTextureChanged(self, *a):
        """Called when the ``imageTexture`` changes. Calls
        :meth:`updateShaderState`.
        """
        self.updateShaderState()


    def generateVertices2D(self, zpos, axes, bbox=None):
        """Overrides :meth:`.GLImageObject.generateVertices2D`.

        Appliies the :meth:`.ImageTextureBase.texCoordXform` to the texture
        coordinates - this is performed to support 2D images/textures.
        """

        vertices, voxCoords, texCoords = \
            glimageobject.GLImageObject.generateVertices2D(
                self, zpos, axes, bbox)

        texCoords = affine.transform(
            texCoords, self.imageTexture.texCoordXform(self.overlay.shape))

        return vertices, voxCoords, texCoords


    def channelColours(self):
        """Returns a ``numpy`` array of shape ``(3, 4)``, containing the
        colours to use for each of the three channels.
        """

        opts     = self.opts
        display  = self.display
        alpha    = display.alpha / 100

        colours        = np.zeros((3, 4), dtype=np.float32)
        colours[0, :3] = opts.rColour[:3]
        colours[1, :3] = opts.gColour[:3]
        colours[2, :3] = opts.bColour[:3]
        colours[:,  3] = alpha

        if   opts.suppressMode == 'white':       suppress = [1, 1, 1, alpha]
        elif opts.suppressMode == 'black':       suppress = [0, 0, 0, alpha]
        elif opts.suppressMode == 'transparent': suppress = [0, 0, 0, 0]

        if opts.suppressR: colours[0, :] = suppress
        if opts.suppressG: colours[1, :] = suppress
        if opts.suppressB: colours[2, :] = suppress

        return colours


    def preDraw(self):
        """Called before a draw. Binds the image texture. """
        self.imageTexture.bindTexture(gl.GL_TEXTURE0)


    def draw2D(self, canvas, *args, **kawrgs):
        """Calls ``glrgbvolume_funcs.draw2D``. """
        with glroutines.enabled((gl.GL_CULL_FACE)):
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glCullFace(gl.GL_BACK)
            gl.glFrontFace(self.frontFace(canvas))
            fslgl.glrgbvolume_funcs.draw2D(self, canvas, *args, **kawrgs)


    def drawAll(self, *args, **kawrgs):
        """Calls ``glrgbvolume_funcs.drawAll``. """
        fslgl.glrgbvolume_funcs.drawAll(self, *args, **kawrgs)


    def draw3D(self, *args, **kawrgs):
        """Does nothing. """


    def postDraw(self):
        """Called after a draw. Unbinds the image texture. """
        self.imageTexture.unbindTexture()
