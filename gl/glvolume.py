#!/usr/bin/env python
#
# glvolume.py - OpenGL vertex/texture creation for 2D slice rendering of a 3D
#               image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`GLVolume` class, which creates and encapsulates the
data and logic required to render 2D slice of a 3D image. The
:class:`GLVolume` class provides the interface defined in the
:class:`.GLObject` class.

A :class:`GLVolume` instance may be used to render an :class:`.Image` instance
which has an ``overlayType`` of ``volume``. It is assumed that this ``Image``
instance is associated with a :class:`.Display` instance which, in turn,
contains a :class:`.VolumeOpts` instance, containing display options specific
to volume rendering.

The :class:`GLVolume` class makes use of the functions defined in the
:mod:`.gl14.glvolume_funcs` or the :mod:`.gl21.glvolume_funcs` modules, which
provide OpenGL version specific details for creation/storage of vertex data,
and for rendering.

These version dependent modules must provide the following functions:

  - ``init(GLVolume)``: Perform any necessary initialisation.

  - ``destroy(GLVolume)``: Perform any necessary clean up.

  - ``compileShaders(GLVolume)``: (Re-)Compile the shader programs.

  - ``updateShaderState(GLVolume)``: Updates the shader program states
    when display parameters are changed.

  - ``preDraw(GLVolume)``: Initialise the GL state, ready for drawing.

  - ``draw(GLVolume, zpos, xform=None)``: Draw a slice of the image at the
    given Z position. If xform is not None, it must be applied as a 
    transformation on the vertex coordinates.

  - ``drawAll(Glvolume, zposes, xforms)`` - Draws slices at each of the
    specified ``zposes``, applying the corresponding ``xforms`` to each.

  - ``postDraw(GLVolume)``: Clear the GL state after drawing.

Images are rendered in essentially the same way, regardless of which OpenGL
version-specific module is used.  The image data itself is stored on the GPU
as a 3D texture, and the current colour map as a 1D texture. A slice through
the texture is rendered using six vertices, located at the respective corners
of the image bounds.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL      as gl

import fsl.fsleyes.gl as fslgl
import                   textures
import                   globject
import resources      as glresources


class GLVolume(globject.GLImageObject):
    """The :class:`GLVolume` class encapsulates the data and logic required to
    render 2D slices of a 3D image.
    """
 
    def __init__(self, image, display):
        """Creates a GLVolume object bound to the given image, and associated
        image display.

        Initialises the OpenGL data required to render the given image.

        :arg image:   An :class:`.Image` object.
        
        :arg display: A :class:`.Display` object which describes how the image
                      is to be displayed.
        """

        globject.GLImageObject.__init__(self, image, display)

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self.addDisplayListeners()

        # Create an image texture and a colour map texture
        self.texName = '{}_{}'.format(type(self).__name__, id(self.image))

        self.imageTexture  = None
        self.colourTexture = textures.ColourMapTexture(self.texName)
 
        self.refreshImageTexture()
        self.refreshColourTexture()
        
        fslgl.glvolume_funcs.init(self)


    def destroy(self):
        """This should be called when this :class:`GLVolume` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles).
        """

        glresources.delete(self.imageTexture.getTextureName())
        
        self.colourTexture.destroy()
        
        self.imageTexture  = None
        self.colourTexture = None
        
        self.removeDisplayListeners()
        fslgl.glvolume_funcs.destroy(self)
        
        globject.GLImageObject.destroy(self)

        
    def testUnsynced(self):
        """Used by the :meth:`refreshImageTexture` method.
        
        Returns ``True`` if certain critical :class:`VolumeOpts` properties
        have been unsynced from the parent instance, meaning that this
        :class:`GLVolume` instance needs to create its own image texture;
        returns ``False`` otherwise.
        """
        return (self.displayOpts.getParent() is None                or
                not self.displayOpts.isSyncedToParent('volume')     or
                not self.displayOpts.isSyncedToParent('resolution') or
                not self.displayOpts.isSyncedToParent('interpolation'))
        

    def refreshImageTexture(self):

        opts     = self.displayOpts
        texName  = self.texName
        unsynced = self.testUnsynced()

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))

        if self.imageTexture is not None:
            glresources.delete(self.imageTexture.getTextureName())

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        # The image texture may be used elsewhere,
        # so we'll use the resource management
        # module rather than creating one directly
        self.imageTexture = glresources.get(
            texName, 
            textures.ImageTexture,
            texName,
            self.image,
            interp=interp) 

    
    def refreshColourTexture(self):
        """Configures the colour texture used to colour image voxels."""

        display = self.display
        opts    = self.displayOpts

        alpha  = display.alpha / 100.0
        cmap   = opts.cmap
        invert = opts.invert
        dmin   = opts.displayRange[0]
        dmax   = opts.displayRange[1]

        self.colourTexture.set(cmap=cmap,
                               invert=invert,
                               alpha=alpha,
                               displayRange=(dmin, dmax))

        
    def addDisplayListeners(self):
        """Called by :meth:`init`.

        Adds a bunch of listeners to the :class:`.Display` object, and the
        associated :class:`.VolumeOpts` instance, which define how the image
        should be displayed.

        This is done so we can update the colour, vertex, and image data when
        display properties are changed.
        """

        display = self.display
        opts    = self.displayOpts
        lName   = self.name
        
        def colourUpdate(*a):
            self.refreshColourTexture()
            fslgl.glvolume_funcs.updateShaderState(self)
            self.onUpdate()

        def shaderUpdate(*a):
            fslgl.glvolume_funcs.updateShaderState(self)
            self.onUpdate()

        def shaderCompile(*a):
            fslgl.glvolume_funcs.compileShaders(   self)
            fslgl.glvolume_funcs.updateShaderState(self)
            self.onUpdate()

        def imageRefresh(*a):
            self.refreshImageTexture()
            fslgl.glvolume_funcs.updateShaderState(self)
            self.onUpdate()

        def imageUpdate(*a):
            volume     = opts.volume
            resolution = opts.resolution

            if opts.interpolation == 'none': interp = gl.GL_NEAREST
            else:                            interp = gl.GL_LINEAR
            
            self.imageTexture.set(volume=volume,
                                  interp=interp,
                                  resolution=resolution)
            
            fslgl.glvolume_funcs.updateShaderState(self)
            self.onUpdate()

        display.addListener('softwareMode',   lName, shaderCompile, weak=False)
        display.addListener('alpha',          lName, colourUpdate,  weak=False)
        opts   .addListener('displayRange',   lName, colourUpdate,  weak=False)
        opts   .addListener('clippingRange',  lName, shaderUpdate,  weak=False)
        opts   .addListener('invertClipping', lName, shaderUpdate,  weak=False)
        opts   .addListener('cmap',           lName, colourUpdate,  weak=False)
        opts   .addListener('invert',         lName, colourUpdate,  weak=False)
        opts   .addListener('volume',         lName, imageUpdate,   weak=False)
        opts   .addListener('resolution',     lName, imageUpdate,   weak=False)
        opts   .addListener('interpolation',  lName, imageUpdate,   weak=False)

        if opts.getParent() is not None:
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

        display = self.display
        opts    = self.displayOpts

        lName = self.name
        
        display.removeListener(          'softwareMode',   lName)
        display.removeListener(          'alpha',          lName)
        opts   .removeListener(          'displayRange',   lName)
        opts   .removeListener(          'clippingRange',  lName)
        opts   .removeListener(          'invertClipping', lName)
        opts   .removeListener(          'cmap',           lName)
        opts   .removeListener(          'invert',         lName)
        opts   .removeListener(          'volume',         lName)
        opts   .removeListener(          'resolution',     lName)
        opts   .removeListener(          'interpolation',  lName)
        if opts.getParent() is not None:
            opts.removeSyncChangeListener('volume',        lName)
            opts.removeSyncChangeListener('resolution',    lName)
            opts.removeSyncChangeListener('interpolation', lName)

        
    def preDraw(self):
        """Sets up the GL state to draw a slice from this :class:`GLVolume`
        instance.
        """
        
        # Set up the image and colour textures
        self.imageTexture .bindTexture(gl.GL_TEXTURE0)
        self.colourTexture.bindTexture(gl.GL_TEXTURE1)

        fslgl.glvolume_funcs.preDraw(self)

        
    def draw(self, zpos, xform=None):
        """Draws a 2D slice of the image at the given real world Z location.
        This is performed via a call to the OpenGL version-dependent `draw`
        function, contained in one of the :mod:`.gl14` or :mod:`.gl21`
        packages.

        If `xform` is not None, it is applied as an affine transformation to
        the vertex coordinates of the rendered image data.

        Note: Calls to this method must be preceded by a call to
        :meth:`preDraw`, and followed by a call to :meth:`postDraw`.
        """
        
        fslgl.glvolume_funcs.draw(self, zpos, xform)

        
    def drawAll(self, zposes, xforms):
        """Calls the module-specific ``drawAll`` function. """
        
        fslgl.glvolume_funcs.drawAll(self, zposes, xforms)

        
    def postDraw(self):
        """Clears the GL state after drawing from this :class:`GLVolume`
        instance.
        """

        self.imageTexture .unbindTexture()
        self.colourTexture.unbindTexture()
        
        fslgl.glvolume_funcs.postDraw(self) 
