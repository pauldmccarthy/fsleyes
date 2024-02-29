#!/usr/bin/env python
#
# gllabel.py - The GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLLabel` class, which implements
functionality to render an :class:`.Image` overlay as a label/atlas image.
"""


import OpenGL.GL                 as gl

import fsl.utils.idle            as idle
import fsl.transform.affine      as affine
import fsleyes.gl                as fslgl
import fsleyes.gl.routines       as glroutines
import fsleyes.gl.shaders.filter as glfilter
import fsleyes.gl.resources      as glresources
import fsleyes.gl.glimageobject  as glimageobject
import fsleyes.gl.globject       as globject
import fsleyes.gl.textures       as textures


class GLLabel(glimageobject.GLImageObject, globject.GLObject):
    """The ``GLLabel`` class is a :class:`.GLImageObject` which encapsulates
    the logic required to render an :class:`.Image` overlay as a label image.
    Within the image, each contiguous region with the same label value is
    rendered in the same colour. Regions may be shown either with a filled
    colour, or with a border around them.

    When created, a ``GLLabel`` instance assumes that the provided
    :class:`.Image` instance has a :attr:`.Display.overlayType` of ``label``,
    and that its associated :class:`.Display` instance contains a
    :class:`.LabelOpts` instance, containing label-specific display
    properties.

    An :class:`.ImageTexture` is used to store the :class:`.Image` data, and
    a :class:`.LookupTableTexture` used to store the :class:`.LookupTable`
    (defined by the :attr:`.LabelOpts.lut` property). OpenGL version-specific
    modules (:mod:`.gl14.gllabel_funcs` and :mod:`.gl21.gllabel_funcs`) are
    used to configure the vertex/fragment shader programs used for rendering.

    The ``GLLabel`` class is modelled upon the :class:`.GLVolume` class, and
    the version specific modules for the ``GLLabel`` class must provide the
    same set of functions that are required by the ``GLVolume`` class.
    """


    def __init__(self, image, overlayList, displayCtx, threedee):
        """Create a ``GLLabel``.

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

        # The shader attribute will be created
        # by the gllabel_funcs module, and the
        # imageTexture by the refreshTexture
        # method
        self.shader       = None
        self.imageTexture = None
        self.lutTexture   = textures.LookupTableTexture(
            '{}_lut'.format(self.name))
        self.edgeFilter   = glfilter.Filter('edge', texture=0)
        self.renderTexture = textures.RenderTexture(
            self.name, interp=gl.GL_LINEAR, rttype='c')

        self.__lut = self.opts.lut

        self.addListeners()
        self.registerLut()
        self.refreshLutTexture()
        self.refreshImageTexture()

        def init():
            if not self.destroyed:
                fslgl.gllabel_funcs.init(self)
                self.notify()

        idle.idleWhen(init, self.textureReady)


    def destroy(self):
        """Must be called when this ``GLLabel`` is no longer needed. Destroys
        the :class:`.ImageTexture` and :class:`.LookupTableTexture`.
        """

        self.edgeFilter.destroy()
        self.renderTexture.destroy()
        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.name)
        self.lutTexture.destroy()

        self.removeListeners()
        fslgl.gllabel_funcs.destroy(self)
        glimageobject.GLImageObject.destroy(self)


    def ready(self):
        """Returns ``True`` if this ``GLLabel`` is ready to be drawn, ``False``
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
            if fslgl.gllabel_funcs.updateShaderState(self) or alwaysNotify:
                self.notify()

        idle.idleWhen(func,
                      self.ready,
                      name=self.name,
                      skipIfQueued=True)


    def addListeners(self):
        """Called by :meth:`__init__`. Adds listeners to several properties of
        the :class:`.Display` and :class:`.LabelOpts` instances, so the OpenGL
        representation can be updated when they change.
        """

        display = self.display
        opts    = self.opts
        name    = self.name

        display.addListener('alpha',        name, self.__colourPropChanged)
        display.addListener('brightness',   name, self.__colourPropChanged)
        display.addListener('contrast',     name, self.__colourPropChanged)
        opts   .addListener('outline',      name, self.notify)
        opts   .addListener('outlineWidth', name, self.notify)
        opts   .addListener('lut',          name, self.__lutChanged)
        opts   .addListener('volume',       name, self.__imagePropChanged)
        opts   .addListener('transform',    name, self.notify)

        # See comment in GLVolume.addDisplayListeners about this
        self.__syncListenersRegistered = opts.getParent() is not None

        if self.__syncListenersRegistered:
            opts.addSyncChangeListener(
                'volume',     name, self.__imageSyncChanged)


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all of the listeners that were
        added by :meth:`addListeners`.
        """

        display = self.display
        opts    = self.opts
        name    = self.name

        display.removeListener('alpha',        name)
        display.removeListener('brightness',   name)
        display.removeListener('contrast',     name)
        opts   .removeListener('outline',      name)
        opts   .removeListener('outlineWidth', name)
        opts   .removeListener('lut',          name)
        opts   .removeListener('volume',       name)
        opts   .removeListener('transform',    name)

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
                return None

            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.name)

        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            self.image,
            notify=False,
            volume=opts.index()[3:])

        self.imageTexture.register(self.name, self.__imageTextureChanged)


    def refreshLutTexture(self, *a):
        """Refreshes the :class:`.LookupTableTexture` which stores the
        :class:`.LookupTable` used to colour the overlay.
        """

        display = self.display
        opts    = self.opts

        self.lutTexture.set(alpha=display.alpha           / 100.0,
                            brightness=display.brightness / 100.0,
                            contrast=display.contrast     / 100.0,
                            lut=opts.lut)


    def registerLut(self):
        """Registers a listener on the current :class:`.LookupTable` instance.
        """
        opts = self.opts

        if self.__lut is not None:
            for topic in ['label', 'added', 'removed']:
                self.__lut.deregister(self.name, topic)

        self.__lut = opts.lut

        if self.__lut is not None:
            for topic in ['label', 'added', 'removed']:
                self.__lut.register(self.name, self.__colourPropChanged, topic)


    def preDraw(self):
        """Binds the :class:`.ImageTexture` and :class:`.LookupTableTexture`.
        """
        self.imageTexture.bindTexture(gl.GL_TEXTURE0)
        self.lutTexture  .bindTexture(gl.GL_TEXTURE1)


    def draw2D(self, canvas, zpos, axes, xform=None):
        """Calls the version-dependent ``draw2D`` function. """

        opts       = self.opts
        outline    = opts.outline
        owidth     = float(opts.outlineWidth)
        rtex       = self.renderTexture
        w, h       = canvas.GetSize()
        bbox       = canvas.viewport
        projmat    = canvas.projectionMatrix
        viewmat    = canvas.viewMatrix
        lo         = [ax[0] for ax in bbox]
        hi         = [ax[1] for ax in bbox]
        xax        = axes[0]
        yax        = axes[1]
        xmin, xmax = bbox[xax]
        ymin, ymax = bbox[yax]

        # If rendering to an off-screen texture, it is
        # likely that that texture has the same resolution
        # as the image. In this case, we need to scale
        # down the outline width (which is specified in
        # terms of display pixels), as otherwise the outline
        # width will effectively be interpreted as voxels,
        # which results in massive outlines. Dividing by
        # 10 (the maximum value the outlineWidth can take)
        # limits the outline size to max 1 voxel.
        if isinstance(canvas, textures.RenderTexture):
            owidth /= 10

        offsets = [owidth / w, owidth / h]

        rtex.shape = w, h

        # draw the labels to the offscreen texture
        with glroutines.disabled(gl.GL_BLEND), \
             rtex.target(xax, yax, lo, hi):
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            fslgl.gllabel_funcs.draw2D(self, rtex, zpos, axes, xform)

        # run the offscreen texture through the
        # edge filter, drawing the result to
        # the canvas
        xform = affine.concat(projmat, viewmat)

        self.edgeFilter.set(offsets=offsets, outline=outline)
        self.edgeFilter.apply(rtex, zpos, xmin, xmax,
                              ymin, ymax, xax, yax, xform)


    def draw3D(self, canvas, xform=None):
        """Not implemented."""


    def drawAll(self, canvas, axes, zposes, xforms):
        """Calls the version-dependent ``drawAll`` function. """

        opts       = self.opts
        outline    = opts.outline
        owidth     = float(opts.outlineWidth)
        rtex       = self.renderTexture
        w, h       = canvas.GetSize()
        bbox       = canvas.viewport
        projmat    = canvas.projectionMatrix
        viewmat    = canvas.viewMatrix
        lo         = [ax[0] for ax in bbox]
        hi         = [ax[1] for ax in bbox]
        xax        = axes[0]
        yax        = axes[1]
        xmin, xmax = bbox[xax]
        ymin, ymax = bbox[yax]
        offsets    = [owidth / w, owidth / h]

        rtex.shape = w, h

        # draw all slices to the offscreen texture
        with glroutines.disabled(gl.GL_BLEND), \
             rtex.target(xax, yax, lo, hi):
            gl.glClearColor(0, 0, 0, 0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            fslgl.gllabel_funcs.drawAll(self, rtex, axes, zposes, xforms)

        xform = affine.concat(projmat, viewmat)

        # run it through the edge filter
        self.edgeFilter.set(offsets=offsets, outline=outline)
        self.edgeFilter.apply(rtex, max(zposes), xmin, xmax,
                              ymin, ymax, xax, yax, xform)


    def postDraw(self):
        """Unbinds the ``ImageTexture`` and ``LookupTableTexture``.
        """
        self.imageTexture.unbindTexture()
        self.lutTexture  .unbindTexture()


    def __lutChanged(self, *a):
        """Called when the :attr:`.LabelOpts.lut` property changes. Re-creates
        the :class:`.LookupTableTexture`.
        """

        self.registerLut()
        self.refreshLutTexture()
        self.updateShaderState(alwaysNotify=True)


    def __colourPropChanged(self, *a):
        """Called when a :class:`.Display` property changes (e.g. ``alpha``).
        Refreshes the LUT texture.
        """
        self.refreshLutTexture()
        self.updateShaderState(alwaysNotify=True)


    def __imagePropChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.volume` property changes. Updates
        the ``imageTexture`` and calls :meth:`updateShaderState`.
        """
        opts = self.opts

        self.imageTexture.set(volume=opts.index()[3:])
        self.updateShaderState(alwaysNotify=True)


    def __imageSyncChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.volume` property is synchronised
        or un-synchronised. Calls :meth:`refreshImageTexture` and
        :meth:`updateShaderState`.
        """
        self.refreshImageTexture()
        self.updateShaderState(alwaysNotify=True)


    def __imageTextureChanged(self, *a):
        """Called when the :class:`.ImageTexture` containing the image data
        changes. Calls :meth:`updateShaderState`.
        """
        self.updateShaderState(alwaysNotify=True)
