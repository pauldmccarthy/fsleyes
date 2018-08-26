#!/usr/bin/env python
#
# glmip.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import OpenGL.GL                 as gl


import fsl.utils.idle            as idle

import fsleyes.gl                as fslgl
import fsleyes.gl.textures       as textures
import fsleyes.gl.resources      as glresources
from . import                       glimageobject


class GLMIP(glimageobject.GLImageObject):

    def __init__(self, image, overlayList, displayCtx, canvas, threedee):

        glimageobject.GLImageObject.__init__(self,
                                             image,
                                             overlayList,
                                             displayCtx,
                                             canvas,
                                             threedee)

        self.shader         = None
        self.imageTexture   = None
        self.cmapTexture    = textures.ColourMapTexture(self.name)
        self.negCmapTexture = textures.ColourMapTexture(self.name)

        self.addDisplayListeners()
        self.refreshImageTexture()
        self.refreshCmapTextures()

        def init():
            fslgl.glmip_funcs.init(self)
            self.notify()

        idle.idleWhen(init, self.textureReady)


    def destroy(self):

        self.cmapTexture   .destroy()
        self.negCmapTexture.destroy()

        self.removeDisplayListeners()
        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.getTextureName())

        fslgl.glmip_funcs.destroy(self)
        glimageobject.GLImageObject.destroy(self)

        self.shader         = None
        self.cmapTexture    = None
        self.negCmapTexture = None
        self.imageTexture   = None


    def addDisplayListeners(self):
        """Adds a bunch of listeners to the :class:`.Display` object, and the
        associated :class:`.MaskOpts` instance, which define how the mask
        image should be displayed.
        """
        display = self.display
        opts    = self.opts
        name    = self.name

        def shader(*a):
            self.updateShaderState()
            self.notify()

        def cmap(*a):
            self.refreshCmapTextures()
            self.updateShaderState()
            self.notify()

        opts    .addListener('window',           name, shader,  weak=False)
        opts    .addListener('displayRange',     name, cmap,    weak=False)
        opts    .addListener('clippingRange',    name, shader,  weak=False)
        opts    .addListener('invertClipping',   name, shader,  weak=False)
        display .addListener('alpha',            name, cmap,    weak=False)
        opts    .addListener('cmap',             name, cmap,    weak=False)
        opts    .addListener('gamma',            name, cmap,    weak=False)
        opts    .addListener('interpolateCmaps', name, cmap,    weak=False)
        opts    .addListener('negativeCmap',     name, cmap,    weak=False)
        opts    .addListener('cmapResolution',   name, cmap,    weak=False)
        opts    .addListener('useNegativeCmap',  name, cmap,    weak=False)
        opts    .addListener('invert',           name, cmap,    weak=False)
        opts    .addListener('volume',           name, self.__volumeChanged)
        opts    .addListener('interpolation',    name, self.__interpChanged)
        opts    .addListener('transform',        name, self.notify)
        opts    .addListener('displayXform',     name, self.notify)

        # See comment in GLVolume.addDisplayListeners about this
        self.__syncListenersRegistered = opts.getParent() is not None

        if self.__syncListenersRegistered:
            opts.addSyncChangeListener(
                'volume', name, self.refreshImageTexture)


    def removeDisplayListeners(self):

        display = self.display
        opts    = self.opts
        name    = self.name

        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('volume', name)

        opts    .removeListener('window',           name)
        opts    .removeListener('displayRange',     name)
        opts    .removeListener('clippingRange',    name)
        opts    .removeListener('invertClipping',   name)
        display .removeListener('alpha',            name)
        opts    .removeListener('cmap',             name)
        opts    .removeListener('gamma',            name)
        opts    .removeListener('interpolateCmaps', name)
        opts    .removeListener('negativeCmap',     name)
        opts    .removeListener('cmapResolution',   name)
        opts    .removeListener('useNegativeCmap',  name)
        opts    .removeListener('invert',           name)
        opts    .removeListener('volume',           name)
        opts    .removeListener('interpolation',    name)
        opts    .removeListener('transform',        name)
        opts    .removeListener('displayXform',     name)


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
                return

            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.getTextureName())

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


    def refreshCmapTextures(self):
        display = self.display
        opts    = self.opts
        alpha   = display.alpha / 100.0
        cmap    = opts.cmap
        interp  = opts.interpolateCmaps
        res     = opts.cmapResolution
        gamma   = opts.realGamma(opts.gamma)
        negCmap = opts.negativeCmap
        invert  = opts.invert
        dmin    = opts.displayRange[0]
        dmax    = opts.displayRange[1]

        if interp: interp = gl.GL_LINEAR
        else:      interp = gl.GL_NEAREST

        self.cmapTexture.set(cmap=cmap,
                             invert=invert,
                             alpha=alpha,
                             resolution=res,
                             gamma=gamma,
                             interp=interp,
                             displayRange=(dmin, dmax))

        self.negCmapTexture.set(cmap=negCmap,
                                invert=invert,
                                alpha=alpha,
                                resolution=res,
                                gamma=gamma,
                                interp=interp,
                                displayRange=(dmin, dmax))


    def updateShaderState(self, *args, **kwargs):
        """Calls :func:`.gl14.glmip_funcs.updateShaderState` or
        :func:`.gl21.glmip_funcs.updateShaderState`, and
        :meth:`.Notifier.notify`. Uses :func:`.idle.idleWhen` to ensure that
        they don't get called until :meth:`ready` returns ``True``.
        """
        alwaysNotify = kwargs.pop('alwaysNotify', None)

        def func():
            if fslgl.glmip_funcs.updateShaderState(self) or alwaysNotify:
                self.notify()

        idle.idleWhen(func,
                      self.ready,
                      name=self.name,
                      skipIfQueued=True)


    def ready(self):
        """Returns ``True`` if this ``GLMIP`` is ready to be drawn, ``False``
        otherwise.
        """
        return self.shader is not None and self.textureReady()


    def textureReady(self):
        """Returns ``True`` if the ``imageTexture`` is ready to be used,
        ``False`` otherwise.
        """
        return self.imageTexture is not None and self.imageTexture.ready()


    def preDraw(self, xform=None, bbox=None):
        self.imageTexture  .bindTexture(gl.GL_TEXTURE0)
        self.cmapTexture   .bindTexture(gl.GL_TEXTURE1)
        self.negCmapTexture.bindTexture(gl.GL_TEXTURE2)


    def draw2D(self, zpos, axes, xform=None, bbox=None):
        fslgl.glmip_funcs.draw2D(self, zpos, axes, xform, bbox)


    def draw3D(self, xform=None, bbox=None):
        pass


    def postDraw(self, xform=None, bbox=None):
        self.imageTexture  .unbindTexture()
        self.cmapTexture   .unbindTexture()
        self.negCmapTexture.unbindTexture()


    def __volumeChanged(self, *a):
        self.imageTexture.set(volume=self.opts.index()[3:])


    def __interpChanged(self, *a):
        """Called when the :attr:`.MIPOpts.interpolation` changes. Updates the
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
