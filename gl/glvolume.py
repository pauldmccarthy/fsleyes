#!/usr/bin/env python
#
# glvolume.py - The GLVolume class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLVolume` class, which creates and
encapsulates the data and logic required to render 2D slice of an
:class:`.Image` instance.
"""


import logging

import OpenGL.GL       as gl

import fsl.fsleyes.gl  as fslgl
import fsl.utils.async as async
import                    textures
import                    globject
import resources       as glresources


log = logging.getLogger(__name__)


class GLVolume(globject.GLImageObject):
    """The ``GLVolume`` class is a :class:`.GLImageObject` which encapsulates
    the data and logic required to render 2D slices of an :class:`.Image`
    overlay.

    
    A ``GLVolume`` instance may be used to render an :class:`.Image` instance
    which has a :attr:`.Display.overlayType` equal to ``volume``. It is
    assumed that this ``Image`` instance is associated with a
    :class:`.Display` instance which, in turn, contains a :class:`.VolumeOpts`
    instance, containing display options specific to volume rendering.


    **Version dependent modules**

    
    The ``GLVolume`` class makes use of the functions defined in the
    :mod:`.gl14.glvolume_funcs` or the :mod:`.gl21.glvolume_funcs` modules,
    which provide OpenGL version specific details for creation/storage of
    vertex data, and for rendering.


    These version dependent modules must provide the following functions:

    ===================================== =====================================
    ``init(GLVolume)``                    Perform any necessary initialisation.

    ``destroy(GLVolume)``                 Perform any necessary clean up.

    ``compileShaders(GLVolume)``          (Re-)Compile the shader programs.

    ``updateShaderState(GLVolume)``       Updates the shader program states
                                          when display parameters are changed.

    ``preDraw(GLVolume)``                 Initialise the GL state, ready for
                                          drawing.

    ``draw(GLVolume, zpos, xform=None)``  Draw a slice of the image at the
                                          given ``zpos``. If ``xform`` is not
                                          ``None``, it must be applied as a
                                          transformation on the vertex
                                          coordinates.
 
    ``drawAll(Glvolume, zposes, xforms)`` Draws slices at each of the
                                          specified ``zposes``, applying the
                                          corresponding ``xforms`` to each.

    ``postDraw(GLVolume)``                Clear the GL state after drawing.
    ===================================== =====================================


    **Rendering**

    
    Images are rendered in essentially the same way, regardless of which
    OpenGL version-specific module is used.  The image data itself is stored
    as an :class:`.ImageTexture`. This ``ImageTexture`` is managed by the
    :mod:`.resources` module, so may be shared by many ``GLVolume`` instances.
    The current colour maps (defined by the :attr:`.VolumeOpts.cmap` and
    :attr:`.VolumeOpts.negativeCmap` properties) are stored as
    :class:`.ColourMapTexture` instances.  A slice through the texture is
    rendered using six vertices, located at the respective corners of the
    image bounds.

    
    Image voxels may be clipped according to the
    :attr:`.VolumeOpts.clippingRange` property. By default, the voxel value
    is compared against the clipping range, but the
    :attr:`.VolumeOpts.clipImage` property allows the data from a different
    image (of the same dimensions) to be used for clipping. If specified,
    this clipping image is stored as another :class:`.ImageTexture`.

    
    **Textures**


    The ``GLVolume`` class uses three textures:

     - An :class:`.ImageTexture`, a 3D texture which contains image data.
       This is bound to texture unit 0.
    
     - A :class:`.ColourMapTexture`, a 1D texture which contains the
       colour map defined by the :attr:`.VolumeOpts.cmap` property.
       This is bound to texture unit 1.
    
     - A :class:`.ColourMapTexture`, a 1D texture which contains the
       colour map defined by the :attr:`.VolumeOpts.negativeCmap` property.
       This is bound to texture unit 2.

     - An :class:`.ImageTexture` which contains the clippimg image data.
       This is bound to texture unit 3. If the :attr:`.VolumeOpts.clipImage`
       property is not specified (i.e. it has a value of ``None``), this
       texture will not be bound - in this case, the image texture is used
       for clipping.


    **Attributes**


    The following attributes are available on a ``GLVolume`` instance:

    ==================== ==================================================
    ``imageTexture``     The :class:`.ImageTexture` which stores the image
                         data.
    ``clipTexture``      The :class:`.ImageTexture` which stores the clip
                         image data.   If :attr:`.VolumeOpts.clipImage`
                         is ``None``, this attribute will also be ``None``.
    ``colourTexture``    The :class:`.ColourMapTexture` used to store the
                         colour map.
    ``negColourTexture`` The :class:`.ColourMapTexture` used to store the
                         negative colour map. 
    ``texName``          A name used for the ``imageTexture``,
                         ``colourTexture``, and ``negColourTexture`. The
                         name for the latter is suffixed with ``'_neg'``.
    ==================== ==================================================
    """

    
    def __init__(self, image, display):
        """Create a ``GLVolume`` object.

        :arg image:   An :class:`.Image` object.
        
        :arg display: A :class:`.Display` object which describes how the image
                      is to be displayed.
        """

        globject.GLImageObject.__init__(self, image, display)

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self.addDisplayListeners()

        # Create an image texture, clip texture, and a colour map texture
        self.texName  = '{}_{}'.format(type(self).__name__, id(self.image))

        # Ref to an OpenGL shader program -
        # the glvolume_funcs module will
        # create this for us.
        self.shader   = None

        # References to the clip image and
        # associated DisplayOpts instance,
        # if it is set.
        self.clipImage        = None
        self.clipOpts         = None

        # Refs to all of the texture objects.
        self.imageTexture     = None
        self.clipTexture      = None 
        self.colourTexture    = textures.ColourMapTexture(self.texName)
        self.negColourTexture = textures.ColourMapTexture(
            '{}_neg'.format(self.texName))

        # If the VolumeOpts instance has
        # inherited a clipImage value,
        # make sure we're registered with it.
        if self.displayOpts.clipImage is not None:
            self.registerClipImage()
            
        self.refreshColourTextures()

        # We can't initialise the shaders until
        # the image textures are ready to go.
        # The image textures are created
        # asynchronously, so we need to wait
        # for them to finish before initialising
        # the shaders.
        def onTextureReady():
            fslgl.glvolume_funcs.init(self)
            self.notify()
        
        async.wait((self.refreshImageTexture(), self.refreshClipTexture()),
                   onTextureReady)


    def destroy(self):
        """This must be called when this :class:`GLVolume` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles), calls :meth:`removeDisplayListeners`,
        and calls :meth:`.GLImageObject.destroy`.
        """

        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.getTextureName())

        if self.clipTexture is not None:
            self.clipTexture.deregister(self.name)
            glresources.delete(self.clipTexture.getTextureName())
        
        self.colourTexture   .destroy()
        self.negColourTexture.destroy()

        self.imageTexture     = None
        self.clipTexture      = None
        self.colourTexture    = None
        self.negColourTexture = None

        self.deregisterClipImage()
        self.removeDisplayListeners()
        
        fslgl.glvolume_funcs  .destroy(self)
        globject.GLImageObject.destroy(self)

        
    def ready(self):
        """Returns ``True`` if this ``GLVolume`` is ready to be drawn,
        ``False`` otherwise.
        """

        if self.displayOpts.clipImage is None:
            return (self.shader       is not None and
                    self.imageTexture is not None and
                    self.imageTexture.ready())
        else:
            return (self.shader       is not None and
                    self.imageTexture is not None and
                    self.clipTexture  is not None and
                    self.imageTexture.ready()     and
                    self.clipTexture .ready())

        
    def addDisplayListeners(self):
        """Called by :meth:`__init__`.

        Adds a bunch of listeners to the :class:`.Display` object, and the
        associated :class:`.VolumeOpts` instance, which define how the image
        should be displayed.

        This is done so we can update the colour, vertex, and image data when
        display properties are changed.
        """

        image   = self.image
        display = self.display
        opts    = self.displayOpts
        lName   = self.name

        def update(*a):
            self.notify()


        def shaderUpdate(*a):
            if self.ready():
                fslgl.glvolume_funcs.updateShaderState(self)
                self.notify()
        
        def colourUpdate(*a):
            self.refreshColourTextures()
            if self.ready():
                shaderUpdate()

        def imageRefresh(*a):
            async.wait([self.refreshImageTexture()], shaderUpdate)

        def imageUpdate(*a):
            volume     = opts.volume
            resolution = opts.resolution

            if opts.interpolation == 'none': interp = gl.GL_NEAREST
            else:                            interp = gl.GL_LINEAR
            
            self.imageTexture.set(volume=volume,
                                  interp=interp,
                                  resolution=resolution,
                                  notify=False)

            waitfor = [self.imageTexture.refreshThread()]

            if self.clipTexture is not None:
                self.clipTexture.set(interp=interp,
                                     resolution=resolution,
                                     notify=False)
                waitfor.append(self.clipTexture.refreshThread())

            async.wait(waitfor, shaderUpdate)

        def clipUpdate(*a):
            self.deregisterClipImage()
            self.registerClipImage()
            async.wait([self.refreshClipTexture()], shaderUpdate)

        display.addListener('alpha',          lName, colourUpdate,  weak=False)
        opts   .addListener('displayRange',   lName, colourUpdate,  weak=False)
        opts   .addListener('clippingRange',  lName, shaderUpdate,  weak=False)
        opts   .addListener('clipImage',      lName, clipUpdate,    weak=False)
        opts   .addListener('invertClipping', lName, shaderUpdate,  weak=False)
        opts   .addListener('cmap',           lName, colourUpdate,  weak=False)
        opts   .addListener('negativeCmap',   lName, colourUpdate,  weak=False)
        opts   .addListener('useNegativeCmap',
                            lName, colourUpdate,  weak=False)
        opts   .addListener('invert',         lName, colourUpdate,  weak=False)
        opts   .addListener('volume',         lName, imageUpdate,   weak=False)
        opts   .addListener('resolution',     lName, imageUpdate,   weak=False)
        opts   .addListener('interpolation',  lName, imageUpdate,   weak=False)
        opts   .addListener('transform',      lName, update,        weak=False)
        image  .addListener('data',           lName, update,        weak=False)

        # Save a flag so the removeDisplayListeners
        # method knows whether it needs to de-register
        # sync change listeners - using opts.getParent()
        # as the test in that method is dangerous, as
        # the DisplayOpts instance might have already
        # had its destroy method called on it, and might
        # have been detached from its parent.
        self.__syncListenersRegistered = opts.getParent() is not None

        if self.__syncListenersRegistered:
            opts.addSyncChangeListener(
                'volume',        lName, imageRefresh, weak=False)
            opts.addSyncChangeListener(
                'resolution',    lName, imageRefresh, weak=False)
            opts.addSyncChangeListener(
                'interpolation', lName, imageRefresh, weak=False)


    def removeDisplayListeners(self):
        """Called by :meth:`destroy`. Removes all the property listeners that
        were added by :meth:`addDisplayListeners`.
        """

        image   = self.image
        display = self.display
        opts    = self.displayOpts

        lName = self.name
        
        display.removeListener(          'alpha',           lName)
        opts   .removeListener(          'displayRange',    lName)
        opts   .removeListener(          'clippingRange',   lName)
        opts   .removeListener(          'clipImage',       lName)
        opts   .removeListener(          'invertClipping',  lName)
        opts   .removeListener(          'cmap',            lName)
        opts   .removeListener(          'negativeCmap',    lName)
        opts   .removeListener(          'useNegativeCmap', lName)
        opts   .removeListener(          'cmap',            lName)
        opts   .removeListener(          'invert',          lName)
        opts   .removeListener(          'volume',          lName)
        opts   .removeListener(          'resolution',      lName)
        opts   .removeListener(          'interpolation',   lName)
        opts   .removeListener(          'transform',       lName)
        image  .removeListener(          'data',            lName)
        
        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('volume',        lName)
            opts.removeSyncChangeListener('resolution',    lName)
            opts.removeSyncChangeListener('interpolation', lName)

        
    def testUnsynced(self):
        """Used by the :meth:`refreshImageTexture` method.
        
        Returns ``True`` if certain critical :class:`VolumeOpts` properties
        have been unsynced from the parent instance, meaning that this
        ``GLVolume`` instance needs to create its own image texture;
        returns ``False`` otherwise.
        """
        return (self.displayOpts.getParent() is None                or
                not self.displayOpts.isSyncedToParent('volume')     or
                not self.displayOpts.isSyncedToParent('resolution') or
                not self.displayOpts.isSyncedToParent('interpolation'))
        

    def refreshImageTexture(self):
        """Refreshes the :class:`.ImageTexture` used to store the
        :class:`.Image` data. This is performed through the :mod:`.resources`
        module, so the image texture can be shared between multiple
        ``GLVolume`` instances.

        :returns: A reference to the ``Thread`` instance which is
                  asynchronously updating the :class:`.ImageTexture`,
                  or ``None`` if the texture is updated - see the
                  :meth:`.ImageTexture.refreshThread` method.
        """

        opts     = self.displayOpts
        texName  = self.texName
        unsynced = self.testUnsynced()

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))

        if self.imageTexture is not None:
            
            if self.imageTexture.getTextureName() == texName:
                return None
            
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
            notify=False)

        self.imageTexture.register(self.name, self.__textureChanged)

        return self.imageTexture.refreshThread()


    def registerClipImage(self):
        """Called whenever the :attr:`.VolumeOpts.clipImage` property changes.
        Adds property listeners to the :class:`.Nifti1Opts` instance
        associated with the new clip image, if necessary.
        """

        clipImage = self.displayOpts.clipImage

        if clipImage is None:
            return

        clipOpts = self.displayOpts.displayCtx.getOpts(clipImage) 

        self.clipImage = clipImage
        self.clipOpts  = clipOpts
        
        def updateClipTexture(*a):

            def onRefresh():
                fslgl.glvolume_funcs.updateShaderState(self)
                self.notify()
            
            self.clipTexture.set(volume=clipOpts.volume)
            async.wait([self.clipTexture.refreshThread()], onRefresh)

        clipOpts.addListener('volume',
                             self.name,
                             updateClipTexture,
                             weak=False)

    
    def deregisterClipImage(self):
        """Called whenever the :attr:`.VolumeOpts.clipImage` property changes.
        Removes property listeners from the :class:`.Nifti1Opts` instance
        associated with the old clip image, if necessary.
        """

        if self.clipImage is None:
            return

        self.clipOpts.removeListener('volume', self.name)

        self.clipImage = None
        self.clipOpts  = None
        

    def refreshClipTexture(self):
        """Re-creates the :class:`.ImageTexture` used to store the
        :attr:`.VolumeOpts.clipImage`.
        """
        clipImage = self.clipImage
        opts      = self.displayOpts
        clipOpts  = self.clipOpts

        texName   = '{}_clip_{}'.format(type(self).__name__, id(clipImage))

        if self.clipTexture is not None:
            self.clipTexture.deregister(self.name)
            glresources.delete(self.clipTexture.getTextureName())
            self.clipTexture = None
            
        if clipImage is None:
            return None

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR 

        self.clipTexture = glresources.get(
            texName, 
            textures.ImageTexture,
            texName,
            clipImage,
            interp=interp,
            resolution=opts.resolution,
            volume=clipOpts.volume,
            notify=False)
        
        self.clipTexture.register(self.name, self.__textureChanged)

        return self.clipTexture.refreshThread()

    
    def refreshColourTextures(self):
        """Refreshes the :class:`.ColourMapTexture` instances used to colour
        image voxels.
        """

        display = self.display
        opts    = self.displayOpts
        alpha   = display.alpha / 100.0
        cmap    = opts.cmap
        negCmap = opts.negativeCmap
        invert  = opts.invert
        dmin    = opts.displayRange[0]
        dmax    = opts.displayRange[1]

        self.colourTexture.set(cmap=cmap,
                               invert=invert,
                               alpha=alpha,
                               displayRange=(dmin, dmax))

        self.negColourTexture.set(cmap=negCmap,
                                  invert=invert,
                                  alpha=alpha,
                                  displayRange=(dmin, dmax)) 

        
    def preDraw(self):
        """Binds the :class:`.ImageTexture` to ``GL_TEXTURE0`` and the
        :class:`.ColourMapTexture` to ``GL_TEXTURE1, and calls the
        version-dependent ``preDraw`` function.
        """
        
        # Set up the image and colour textures
        self.imageTexture    .bindTexture(gl.GL_TEXTURE0)
        self.colourTexture   .bindTexture(gl.GL_TEXTURE1)
        self.negColourTexture.bindTexture(gl.GL_TEXTURE2)

        if self.clipTexture is not None:
            self.clipTexture .bindTexture(gl.GL_TEXTURE3)

        fslgl.glvolume_funcs.preDraw(self)

        
    def draw(self, zpos, xform=None):
        """Draws a 2D slice of the image at the given Z location in the
        display coordinate system.
        
     .  This is performed via a call to the OpenGL version-dependent ``draw``
        function, contained in one of the :mod:`.gl14.glvolume_funcs` or
        :mod:`.gl21.glvolume_funcs` modules.

        If ``xform`` is not ``None``, it is applied as an affine
        transformation to the vertex coordinates of the rendered image data.

        .. note:: Calls to this method must be preceded by a call to
                  :meth:`preDraw`, and followed by a call to :meth:`postDraw`.
        """
        
        fslgl.glvolume_funcs.draw(self, zpos, xform)

        
    def drawAll(self, zposes, xforms):
        """Calls the version dependent ``drawAll`` function. """
        
        fslgl.glvolume_funcs.drawAll(self, zposes, xforms)

        
    def postDraw(self):
        """Unbinds the ``ImageTexture`` and ``ColourMapTexture``, and calls the
        version-dependent ``postDraw`` function.
        """

        self.imageTexture    .unbindTexture()
        self.colourTexture   .unbindTexture()
        self.negColourTexture.unbindTexture()

        if self.clipTexture is not None:
            self.clipTexture.unbindTexture()
        
        fslgl.glvolume_funcs.postDraw(self) 


    def __textureChanged(self, *a):
        """Called when either of the the :class:`.ImageTexture` instances,
        containing the image or clipping data are refreshed. Notifies
        listeners of this ``GLLabel`` (via the :class:`.Notifier` base
        class).
        """
        self.notify()
