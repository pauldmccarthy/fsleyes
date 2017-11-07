#!/usr/bin/env python
#
# gllabel.py - The GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLLabel` class, which implements
functionality to render an :class:`.Image` overlay as a label/atlas image.
"""


import numpy            as np
import OpenGL.GL        as gl

import fsleyes.gl       as fslgl
import fsl.utils.idle   as idle
from . import resources as glresources
from . import              glimageobject
from . import              textures


class GLLabel(glimageobject.GLImageObject):
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


    def __init__(self, image, displayCtx, canvas, threedee):
        """Create a ``GLLabel``.

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

        lutTexName        = '{}_lut'.format(self.name)
        self.lutTexture   = textures.LookupTableTexture(lutTexName)
        self.imageTexture = None

        # The shader attribute will be created
        # by the gllabel_funcs module
        self.shader       = None

        self.__lut = self.opts.lut

        self.addListeners()
        self.registerLut()
        self.refreshLutTexture()
        self.refreshImageTexture()

        def init():
            fslgl.gllabel_funcs.init(self)
            self.notify()

        idle.idleWhen(init, self.textureReady)


    def destroy(self):
        """Must be called when this ``GLLabel`` is no longer needed. Destroys
        the :class:`.ImageTexture` and :class:`.LookupTableTexture`.
        """

        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.getTextureName())
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
        opts   .addListener('outline',      name, self.updateShaderState)
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


    def preDraw(self, xform=None, bbox=None):
        """Binds the :class:`.ImageTexture` and :class:`.LookupTableTexture`,
        and calls the version-dependent ``preDraw`` function.
        """

        self.imageTexture.bindTexture(gl.GL_TEXTURE0)
        self.lutTexture  .bindTexture(gl.GL_TEXTURE1)
        fslgl.gllabel_funcs.preDraw(self, xform, bbox)


    def draw2D(self, *args, **kwargs):
        """Calls the version-dependent ``draw2D`` function. """
        fslgl.gllabel_funcs.draw2D(self, *args, **kwargs)


    def draw3D(self, *args, **kwargs):
        """Calls the version-dependent ``draw3D`` function. """
        fslgl.gllabel_funcs.draw3D(self, *args, **kwargs)


    def drawAll(self, *args, **kwargs):
        """Calls the version-dependent ``drawAll`` function. """
        fslgl.gllabel_funcs.drawAll(self, *args, **kwargs)


    def postDraw(self, xform=None, bbox=None):
        """Unbinds the ``ImageTexture`` and ``LookupTableTexture``, and calls
        the version-dependent ``postDraw`` function.
        """
        self.imageTexture.unbindTexture()
        self.lutTexture  .unbindTexture()
        fslgl.gllabel_funcs.postDraw(self, xform, bbox)


    def calculateOutlineOffsets(self, axes):
        """Calculates offsets that are used by the label fragment shader
        programs to calculate whether a position in the image is on a label
        boundary. If the image is being shown on a 2D canvas orthogonal
        to the display coordinate system, we can ignore the depth axis and
        calculate boundaries in 2D. Otherwise we have to calculate boundaries
        in 3D.
        """

        zax            = axes[2]
        opts           = self.opts
        imageShape     = np.array(self.image.shape[:3])
        outlineOffsets = opts.outlineWidth / imageShape

        # If we are not orthogonal to the
        # display coordinate system, we use
        # the same outline offset along all
        # axes.
        if opts.transform in ('custom', 'affine'):
            minOffset      = outlineOffsets.min()
            outlineOffsets = np.array([minOffset] * 3)

        # Otherwise we can ignore the depth axis
        else:
            outlineOffsets[zax] = -1

        return outlineOffsets


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
