#!/usr/bin/env python
#
# glmask.py - The GLMask class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLMask` class, which implements
functionality for rendering an :class:`.Image` overlay as a binary mask.
"""

import logging

import numpy                as np
import OpenGL.GL            as gl

import fsl.utils.idle       as idle
import fsleyes.colourmaps   as colourmaps
import fsleyes.gl           as fslgl
import fsleyes.gl.resources as glresources
import fsleyes.gl.textures  as textures
from . import                  glimageobject
from . import                  gllabel


log = logging.getLogger(__name__)


class GLMask(glimageobject.GLImageObject):
    """The ``GLMask`` class encapsulates logic to render an :class:`.Image`
    instance as a binary mask in OpenGL.

    When created, a ``GLMask`` instance assumes that the provided
    :class:`.Image` instance has a :attr:`.Display.overlayType` of ``mask``,
    and that its associated :class:`.Display` instance contains a
    :class:`.MaskOpts` instance, containing mask-specific display properties.
    """


    def __init__(self, image, displayCtx, canvas, threedee):
        """Create a ``GLMask``.

        :arg image:      The :class:`.Image` instance.
        :arg displayCtx: The :class:`.DisplayContext` managing the scene.
        :arg canvas:     The canvas doing the drawing.
        :arg threedee:   2D or 3D rendering
        """
        glimageobject.GLImageObject.__init__(self,
                                             image,
                                             displayCtx,
                                             canvas,
                                             threedee)

        # The shader attribute will be created
        # by the glmask_funcs module
        self.shader       = None
        self.imageTexture = None

        self.addDisplayListeners()
        self.refreshImageTexture()

        def init():
            fslgl.glmask_funcs.init(self)
            self.notify()

        idle.idleWhen(init, self.textureReady)


    def destroy(self):
        """Must be called when this ``GLMask`` is no longer needed. Destroys
        the :class:`.ImageTexture`.
        """
        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.getTextureName())

        self.removeDisplayListeners()
        fslgl.glmask_funcs.destroy(self)
        glimageobject.GLImageObject.destroy(self)


    def ready(self):
        """Returns ``True`` if this ``GLMask`` is ready to be drawn, ``False``
        otherwise.
        """
        return self.shader is not None and self.textureReady()


    def textureReady(self):
        """Returns ``True`` if the ``imageTexture`` is ready to be used,
        ``False`` otherwise.
        """
        return self.imageTexture is not None and self.imageTexture.ready()


    def updateShaderState(self, *args, **kwargs):
        """Calls :func:`.gl14.gllabel_funcs.updateShaderState` or
        :func:`.gl21.gllabel_funcs.updateShaderState`, and
        :meth:`.Notifier.notify`. Uses :func:`.idle.idleWhen` to ensure that
        they don't get called until :meth:`ready` returns ``True``.
        """
        alwaysNotify = kwargs.pop('alwaysNotify', None)

        def func():
            if fslgl.glmask_funcs.updateShaderState(self) or alwaysNotify:
                self.notify()

        idle.idleWhen(func,
                      self.ready,
                      name=self.name,
                      skipIfQueued=True)


    def addDisplayListeners(self):
        """Adds a bunch of listeners to the :class:`.Display` object, and the
        associated :class:`.MaskOpts` instance, which define how the mask
        image should be displayed.
        """

        display = self.display
        opts    = self.opts
        name    = self.name

        def update(*a):
            self.updateShaderState(alwaysNotify=True)

        display.addListener('alpha',         name, update, weak=False)
        display.addListener('brightness',    name, update, weak=False)
        display.addListener('contrast',      name, update, weak=False)
        opts   .addListener('colour',        name, update, weak=False)
        opts   .addListener('threshold',     name, update, weak=False)
        opts   .addListener('invert',        name, update, weak=False)
        opts   .addListener('volume',        name, self.refreshImageTexture)
        opts   .addListener('transform',     name, update, weak=False)

        # See comment in GLVolume.addDisplayListeners about this
        self.__syncListenersRegistered = opts.getParent() is not None

        if self.__syncListenersRegistered:
            opts.addSyncChangeListener(
                'volume', name, self.refreshImageTexture)


    def removeDisplayListeners(self):
        """Overrides :meth:`.GLVolume.removeDisplayListeners`.

        Removes all the listeners added by :meth:`addDisplayListeners`.
        """

        display = self.display
        opts    = self.opts
        name    = self.name

        display.removeListener(          'alpha',         name)
        display.removeListener(          'brightness',    name)
        display.removeListener(          'contrast',      name)
        opts   .removeListener(          'colour',        name)
        opts   .removeListener(          'threshold',     name)
        opts   .removeListener(          'invert',        name)
        opts   .removeListener(          'volume',        name)
        opts   .removeListener(          'transform',     name)

        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('volume',     name)


    def refreshImageTexture(self):
        """Makes sure that the :class:`.ImageTexture`, used to store the
        :class:`.Image` data, is up to date.
        """

        opts     = self.opts
        texName  = '{}_{}' .format(type(self).__name__, id(self.image))
        unsynced = (opts.getParent() is None or
                    not opts.isSyncedToParent('volume'))

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))

        if self.imageTexture is not None:

            if self.imageTexture.getTextureName() == texName:
                return None

            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.getTextureName())

        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            self.image,
            notify=False,
            volume=opts.index()[3:])

        self.imageTexture.register(self.name, self.__imageTextureChanged)


    def getColour(self):
        """Prepares and returns the mask colour for use in the fragment shader.
        """
        display = self.display
        opts    = self.opts
        alpha   = display.alpha / 100.0
        colour  = opts.colour

        colour = colour[:3]
        colour = colourmaps.applyBricon(colour,
                                        display.brightness / 100.0,
                                        display.contrast   / 100.0)

        return list(colour) + [alpha]


    def getThreshold(self):
        """Prepares and returns the mask thresholds for use in the fragment
        shader.
        """
        return (0, 1)


    def calculateOutlineOffsets(self, axes):
        """See the :func:`calculateOutlineOffsets` function. """
        return gllabel.calculateOutlineOffsets(self.image, self.opts, axes)


    def preDraw(self, xform=None, bbox=None):
        """Binds the :class:`.ImageTexture` and calls the version-dependent
        ``preDraw`` function.
        """
        self.imageTexture.bindTexture(gl.GL_TEXTURE0)
        fslgl.glmask_funcs.preDraw(self, xform, bbox)


    def draw2D(self, *args, **kwargs):
        """Calls the version-dependent ``draw2D`` function. """
        fslgl.glmask_funcs.draw2D(self, *args, **kwargs)


    def draw3D(self, *args, **kwargs):
        """Calls the version-dependent ``draw3D`` function. """
        fslgl.glmask_funcs.draw3D(self, *args, **kwargs)


    def drawAll(self, *args, **kwargs):
        """Calls the version-dependent ``drawAll`` function. """
        fslgl.glmask_funcs.drawAll(self, *args, **kwargs)


    def postDraw(self, xform=None, bbox=None):
        """Unbinds the ``ImageTexture`` and calls the version-dependent
        ``postDraw`` function.
        """
        self.imageTexture.unbindTexture()
        fslgl.glmask_funcs.postDraw(self, xform, bbox)


    def __imageTextureChanged(self, *a):
        """Called when the image texture has changed. """
        self.updateShaderState(alwaysNotify=True)


    def __imageSyncChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.volume` property is synchronised
        or un-synchronised. Calls :meth:`refreshImageTexture` and
        :meth:`updateShaderState`.
        """
        self.refreshImageTexture()
        self.updateShaderState(alwaysNotify=True)
