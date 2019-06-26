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

import OpenGL.GL                 as gl

import fsl.utils.idle            as idle
import fsleyes.colourmaps        as colourmaps
import fsleyes.gl                as fslgl
import fsleyes.gl.textures       as textures
import fsleyes.gl.routines       as glroutines
import fsleyes.gl.resources      as glresources
import fsleyes.gl.shaders.filter as glfilter
from . import                       glimageobject


log = logging.getLogger(__name__)


class GLMask(glimageobject.GLImageObject):
    """The ``GLMask`` class encapsulates logic to render an :class:`.Image`
    instance as a binary mask in OpenGL.

    When created, a ``GLMask`` instance assumes that the provided
    :class:`.Image` instance has a :attr:`.Display.overlayType` of ``mask``,
    and that its associated :class:`.Display` instance contains a
    :class:`.MaskOpts` instance, containing mask-specific display properties.


    **Textures**

    A ``GLMask`` will use up to two textures:

      - An :class:`.ImageTexture` for storing the 3D image data. This texture
        is bound to texture unit 0.

      - A :class:`.RenderTexture`, used for edge filtering if necessary. This
        texture will be bound to texture unit 1.


    **2D rendering**


    On 2D canvases, A ``GLMask`` is rendered similarly to a :class:`.GLVolume`
    - a 2D slice is taken through the 3D image texture. If the
    :attr:`.MaskOpts.outline` property is active, this slice is rendered to
    an off-screen texture, which is then passed through an edge filter (see
    the :mod:`.filters` module).


    **Version dependent modules**


    The ``GLMask`` class makes use of the functions defined in the
    :mod:`.gl14.glmask_funcs` or the :mod:`.gl21.glmask_funcs` modules,
    which provide OpenGL version specific details for rendering.


    These version dependent modules must provide the following functions:

    ============================= =====================================
    ``init(GLMask)``              Perform any necessary initialisation.
    ``destroy(GLMask)``           Perform any necessary cleanup
    ``compileShaders(GLMask)``    (Re-)compile the shader program
    ``updateShaderState(GLMask)`` Update the shader program state
    ``draw2D(GLMask, ...)``       Draw a slice of the image
    ``drawAll(GLMask, ...)``      Draw multiple slices of the image
    ============================= =====================================
    """


    def __init__(self, image, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLMask``.

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

        # The shader attribute will be created
        # by the glmask_funcs module
        self.shader        = None
        self.imageTexture  = None
        self.edgeFilter    = glfilter.Filter('edge', texture=1)
        self.renderTexture = textures.RenderTexture(
            self.name, interp=gl.GL_LINEAR, rttype='c')

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
        self.edgeFilter.destroy()
        self.renderTexture.destroy()
        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.name)

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
        opts   .addListener('outlineWidth',  name, update, weak=False)
        opts   .addListener('outline',       name, self.notify)
        opts   .addListener('transform',     name, self.notify)
        opts   .addListener('volume',        name, self.__volumeChanged)
        opts   .addListener('interpolation', name, self.__interpChanged)

        # See comment in GLVolume.addDisplayListeners about this
        self.__syncListenersRegistered = opts.getParent() is not None

        if self.__syncListenersRegistered:
            opts.addSyncChangeListener(
                'volume', name, self.refreshImageTexture)


    def removeDisplayListeners(self):
        """Removes all the listeners added by :meth:`addDisplayListeners`. """

        display = self.display
        opts    = self.opts
        name    = self.name

        display.removeListener('alpha',         name)
        display.removeListener('brightness',    name)
        display.removeListener('contrast',      name)
        opts   .removeListener('colour',        name)
        opts   .removeListener('threshold',     name)
        opts   .removeListener('invert',        name)
        opts   .removeListener('outline',       name)
        opts   .removeListener('outlineWidth',  name)
        opts   .removeListener('transform',     name)
        opts   .removeListener('volume',        name)
        opts   .removeListener('interpolation', name)

        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('volume', name)


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
            if self.imageTexture.name == texName:
                return

            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.name)

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            self.image,
            interp=interp,
            volume=opts.index()[3:],
            notify=False)

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
        opts  = self.opts
        xform = self.imageTexture.invVoxValXform
        lo    = opts.threshold[0] * xform[0, 0] + xform[0, 3]
        hi    = opts.threshold[1] * xform[0, 0] + xform[0, 3]
        return (lo, hi)


    def preDraw(self, xform=None, bbox=None):
        """Binds the :class:`.ImageTexture` and calls the version-dependent
        ``preDraw`` function.
        """

        w, h = self.canvas.GetSize()
        rtex = self.renderTexture

        rtex.shape = w, h
        with rtex.target():
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.imageTexture.bindTexture(gl.GL_TEXTURE0)


    def draw2D(self, zpos, axes, xform=None, bbox=None):
        """Calls the version-dependent ``draw2D`` function, then applies
        the edge filter if necessary.
        """

        opts = self.opts

        if not opts.outline:
            fslgl.glmask_funcs.draw2D(self, zpos, axes, xform, bbox)
            return

        owidth     = float(opts.outlineWidth)
        rtex       = self.renderTexture
        w, h       = self.canvas.GetSize()
        lo, hi     = self.canvas.getViewport()
        xax        = axes[0]
        yax        = axes[1]
        xmin, xmax = lo[xax], hi[xax]
        ymin, ymax = lo[yax], hi[yax]
        offsets    = [owidth / w, owidth / h]

        # Draw the mask to the off-screen texture
        with glroutines.disabled(gl.GL_BLEND), rtex.target(xax, yax, lo, hi):
            fslgl.glmask_funcs.draw2D(self, zpos, axes, xform, bbox)

        # Run the texture through an edge detection
        # filter, drawing the result to screen
        self.edgeFilter.set(offsets=offsets, outline=1)
        self.edgeFilter.apply(
            rtex, zpos, xmin, xmax, ymin, ymax, xax, yax,
            textureUnit=gl.GL_TEXTURE1)


    def drawAll(self, axes, zposes, xforms):
        """Calls the version-dependent ``drawAll`` function, then applies
        the edge filter if necessary.
        """

        opts = self.opts
        rtex = self.renderTexture

        # Is taking max(z) hacky? It seems to work ok.
        zpos       = max(zposes)
        owidth     = opts.outlineWidth
        w, h       = self.canvas.GetSize()
        lo, hi     = self.canvas.getViewport()
        xax        = axes[0]
        yax        = axes[1]
        xmin, xmax = lo[xax], hi[xax]
        ymin, ymax = lo[yax], hi[yax]
        offsets    = [owidth / w, owidth / h]

        # Draw all slices to the off-screen texture
        with glroutines.disabled(gl.GL_BLEND), rtex.target(xax, yax, lo, hi):
            fslgl.glmask_funcs.drawAll(self, axes, zposes, xforms)

        # if no outline, draw the texture directly
        if not opts.outline:
            rtex.drawOnBounds(
                zpos, xmin, xmax, ymin, ymax, xax, yax,
                textureUnit=gl.GL_TEXTURE1)

        else:
            # Run the texture through an edge detection
            # filter, drawing the result to screen
            self.edgeFilter.set(offsets=offsets, outline=1)
            self.edgeFilter.apply(
                rtex, zpos, xmin, xmax, ymin, ymax, xax, yax,
                textureUnit=gl.GL_TEXTURE1)


    def draw3D(self, *args, **kwargs):
        """Does nothing. """
        pass


    def postDraw(self, xform=None, bbox=None):
        """Unbinds the ``ImageTexture``. """
        self.imageTexture.unbindTexture()


    def __volumeChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.volume` changes. Updates the
        image texture.
        """
        self.imageTexture.set(volume=self.opts.index()[3:])


    def __interpChanged(self, *a):
        """Called when the :attr:`.MaskOpts.interpolation` changes. Updates the
        image texture.
        """
        if self.opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                                 interp = gl.GL_LINEAR
        self.imageTexture.set(interp=interp)


    def __imageTextureChanged(self, *a):
        """Called when the image texture data has changed. Triggers a refresh.
        """
        self.updateShaderState(alwaysNotify=True)


    def __imageSyncChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.volume` property is synchronised
        or un-synchronised. Calls :meth:`refreshImageTexture` and
        :meth:`updateShaderState`.
        """
        self.refreshImageTexture()
        self.updateShaderState(alwaysNotify=True)
