#!/usr/bin/env python
#
# gllabel.py - The GLLabel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLLabel` class, which implements
functionality to render an :class:`.Image` overlay as a label/atlas image.
"""


import OpenGL.GL       as gl

import fsl.fsleyes.gl  as fslgl
import fsl.utils.async as async
import resources       as glresources
import                    globject
import                    textures


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

    
    def __init__(self, image, display):
        """Create a ``GLLabel``.

        :arg image:   The :class:`.Image` instance.
        :arg display: The associated :class:`.Display` instance.
        """

        globject.GLImageObject.__init__(self, image, display)

        lutTexName   = '{}_lut'.format(self.name)

        self.lutTexture   = textures.LookupTableTexture(lutTexName)
        self.imageTexture = None

        self.refreshImageTexture()
        self.refreshLutTexture()
 
        fslgl.gllabel_funcs.init(self)
        self.addListeners()

        
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
        return self.imageTexture is not None and self.imageTexture.ready()


    def addListeners(self):
        """Called by :meth:`__init__`. Adds listeners to several properties of
        the :class:`.Display` and :class:`.LabelOpts` instances, so the OpenGL
        representation can be updated when they change.
        """

        image   = self.image
        display = self.display
        opts    = self.displayOpts
        name    = self.name

        def update(*a):
            self.notify()

        def shaderUpdate(*a):
            if self.ready():
                fslgl.gllabel_funcs.updateShaderState(self)
                self.notify()
            
        def shaderCompile(*a):
            fslgl.gllabel_funcs.compileShaders(self)
            shaderUpdate()

        def lutUpdate(*a):
            self.refreshLutTexture()
            shaderUpdate()

        def lutChanged(*a):
            if self.__lut is not None:
                self.__lut.removeListener('labels', self.name)
                
            self.__lut = opts.lut

            if self.__lut is not None:
                self.__lut.addListener('labels', self.name, lutUpdate)
 
            lutUpdate()

        def imageRefresh(*a):
            async.wait([self.refreshImageTexture()], shaderUpdate)
            
        def imageUpdate(*a):
            self.imageTexture.set(volume=opts.volume,
                                  resolution=opts.resolution)

            async.wait([self.imageTexture.refreshThread()], shaderUpdate)

        self.__lut = opts.lut

        display .addListener('alpha',        name, lutUpdate,     weak=False)
        display .addListener('brightness',   name, lutUpdate,     weak=False)
        display .addListener('contrast',     name, lutUpdate,     weak=False)
        opts    .addListener('outline',      name, shaderUpdate,  weak=False)
        opts    .addListener('outlineWidth', name, shaderUpdate,  weak=False)
        opts    .addListener('lut',          name, lutChanged,    weak=False)
        opts    .addListener('volume',       name, imageUpdate,   weak=False)
        opts    .addListener('resolution',   name, imageUpdate,   weak=False)
        opts    .addListener('transform',    name, update,        weak=False)
        image   .addListener('data',         name, update,        weak=False)
        opts.lut.addListener('labels',       name, lutUpdate,     weak=False)

        # See comment in GLVolume.addDisplayListeners about this
        self.__syncListenersRegistered = opts.getParent() is not None

        if self.__syncListenersRegistered: 
            opts.addSyncChangeListener(
                'volume',     name, imageRefresh, weak=False)
            opts.addSyncChangeListener(
                'resolution', name, imageRefresh, weak=False)


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all of the listeners that were
        added by :meth:`addListeners`.
        """

        image   = self.image
        display = self.display
        opts    = self.displayOpts
        name    = self.name

        display .removeListener(          'alpha',        name)
        display .removeListener(          'brightness',   name)
        display .removeListener(          'contrast',     name)
        opts    .removeListener(          'outline',      name)
        opts    .removeListener(          'outlineWidth', name)
        opts    .removeListener(          'lut',          name)
        opts    .removeListener(          'volume',       name)
        opts    .removeListener(          'resolution',   name)
        opts    .removeListener(          'transform',    name)
        image   .removeListener(          'data',         name)
        opts.lut.removeListener(          'labels',       name)

        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('volume',     name)
            opts.removeSyncChangeListener('resolution', name)


    def setAxes(self, xax, yax):
        """Overrides :meth:`.GLImageObject.setAxes`. Updates the shader
        program state.
        """
        globject.GLImageObject.setAxes(self, xax, yax)
        if self.ready():
            fslgl.gllabel_funcs.updateShaderState(self)


    def refreshImageTexture(self):
        """Makes sure that the :class:`.ImageTexture`, used to store the
        :class:`.Image` data, is up to date.
        """
        
        opts     = self.displayOpts
        texName  = '{}_{}' .format(type(self).__name__, id(self.image))

        unsynced = (opts.getParent() is None            or
                    not opts.isSyncedToParent('volume') or
                    not opts.isSyncedToParent('resolution'))

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
            notify=False)
        
        self.imageTexture.register(self.name, self.__imageTextureChanged)

        return self.imageTexture.refreshThread()


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
        
    def preDraw(self):
        """Binds the :class:`.ImageTexture` and :class:`.LookupTableTexture`,
        and calls the version-dependent ``preDraw`` function.
        """

        self.imageTexture.bindTexture(gl.GL_TEXTURE0)
        self.lutTexture  .bindTexture(gl.GL_TEXTURE1)
        fslgl.gllabel_funcs.preDraw(self)

    
    def draw(self, zpos, xform=None):
        """Calls the version-dependent ``draw`` function. """
        fslgl.gllabel_funcs.draw(self, zpos, xform)

        
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

        
    def __imageTextureChanged(self, *a):
        """Called when the :class:`.ImageTexture` containing the image data
        is refreshed. Notifies listeners of this ``GLLabel`` (via the
        :class:`.Notifier` base class).
        """
        self.notify()
