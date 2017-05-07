#!/usr/bin/env python
#
# gllabel.py - The GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLLabel` class, which implements
functionality to render an :class:`.Image` overlay as a label/atlas image.
"""


import OpenGL.GL        as gl

import fsleyes.gl       as fslgl
import fsl.utils.async  as async
from . import resources as glresources
from . import              globject
from . import              textures


class GLLabel(globject.GLImageObject):
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


    def __init__(self, image, display, xax, yax):
        """Create a ``GLLabel``.

        :arg image:   The :class:`.Image` instance.
        :arg display: The associated :class:`.Display` instance.
        :arg xax:     Initial display X axis
        :arg yax:     Initial display Y axis
        """

        globject.GLImageObject.__init__(self, image, display, xax, yax)

        lutTexName        = '{}_lut'.format(self.name)
        self.lutTexture   = textures.LookupTableTexture(lutTexName)
        self.imageTexture = None

        # The shader attribute will be created
        # by the gllabel_funcs module
        self.shader       = None

        self.__lut = self.displayOpts.lut

        self.addListeners()
        self.registerLut()
        self.refreshLutTexture()
        self.refreshImageTexture()

        def init():
            fslgl.gllabel_funcs.init(self)
            self.notify()

        async.idleWhen(init, self.textureReady)


    def destroy(self):
        """Must be called when this ``GLLabel`` is no longer needed. Destroys
        the :class:`.ImageTexture` and :class:`.LookupTableTexture`.
        """

        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.getTextureName())
        self.lutTexture.destroy()

        self.removeListeners()
        fslgl.gllabel_funcs.destroy(self)
        globject.GLImageObject.destroy(self)


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
        :meth:`.Notifier.notify`. Uses :func:`.async.idleWhen` to ensure that
        they don't get called until :meth:`ready` returns ``True``.
        """
        alwaysNotify = kwargs.pop('alwaysNotify', None)

        def func():
            if fslgl.gllabel_funcs.updateShaderState(self) or alwaysNotify:
                self.notify()

        async.idleWhen(func,
                       self.ready,
                       name=self.name,
                       skipIfQueued=True)


    def addListeners(self):
        """Called by :meth:`__init__`. Adds listeners to several properties of
        the :class:`.Display` and :class:`.LabelOpts` instances, so the OpenGL
        representation can be updated when they change.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        display.addListener('alpha',        name, self.__colourPropChanged)
        display.addListener('brightness',   name, self.__colourPropChanged)
        display.addListener('contrast',     name, self.__colourPropChanged)
        opts   .addListener('outline',      name, self.updateShaderState)
        opts   .addListener('outlineWidth', name, self.updateShaderState)
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
        opts    = self.displayOpts
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


    def setAxes(self, xax, yax):
        """Overrides :meth:`.GLImageObject.setAxes`. Updates the shader
        program state.
        """
        globject.GLImageObject.setAxes(self, xax, yax)
        self.updateShaderState()


    def refreshImageTexture(self):
        """Makes sure that the :class:`.ImageTexture`, used to store the
        :class:`.Image` data, is up to date.
        """

        opts     = self.displayOpts
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
            volume=opts.volume)

        self.imageTexture.register(self.name, self.__imageTextureChanged)


    def refreshLutTexture(self, *a):
        """Refreshes the :class:`.LookupTableTexture` which stores the
        :class:`.LookupTable` used to colour the overlay.
        """

        display = self.display
        opts    = self.displayOpts

        self.lutTexture.set(alpha=display.alpha           / 100.0,
                            brightness=display.brightness / 100.0,
                            contrast=display.contrast     / 100.0,
                            lut=opts.lut)


    def registerLut(self):
        """Registers a listener on the current :class:`.LookupTable` instance.
        """
        opts = self.displayOpts

        if self.__lut is not None:
            for topic in ['label', 'added', 'removed']:
                self.__lut.deregister(self.name, topic)

        self.__lut = opts.lut

        if self.__lut is not None:
            for topic in ['label', 'added', 'removed']:
                self.__lut.register(self.name, self.__colourPropChanged, topic)


    def preDraw(self):
        """Binds the :class:`.ImageTexture` and :class:`.LookupTableTexture`,
        and calls the version-dependent ``preDraw`` function.
        """

        self.imageTexture.bindTexture(gl.GL_TEXTURE0)
        self.lutTexture  .bindTexture(gl.GL_TEXTURE1)
        fslgl.gllabel_funcs.preDraw(self)


    def draw(self, zpos, xform=None, bbox=None):
        """Calls the version-dependent ``draw`` function. """
        fslgl.gllabel_funcs.draw(self, zpos, xform, bbox)


    def drawAll(self, zpos, xform=None):
        """Calls the version-dependent ``drawAll`` function. """
        fslgl.gllabel_funcs.drawAll(self, zpos, xform)


    def postDraw(self):
        """Unbinds the ``ImageTexture`` and ``LookupTableTexture``, and calls
        the version-dependent ``postDraw`` function.
        """
        self.imageTexture.unbindTexture()
        self.lutTexture  .unbindTexture()
        fslgl.gllabel_funcs.postDraw(self)


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
        opts = self.displayOpts

        self.imageTexture.set(volume=opts.volume)
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
