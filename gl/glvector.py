#!/usr/bin/env python
#
# glvector.py - The GLVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLVector` class, which encapsulates the
logic for rendering 2D slices of a ``X*Y*Z*3`` :class:`.Image` as a vector
image.
"""


import numpy                    as np
import OpenGL.GL                as gl

import fsl.data.image           as fslimage
import fsl.fsleyes.colourmaps   as fslcm
import resources                as glresources
import                             textures
import                             globject


class GLVector(globject.GLImageObject):
    """The :class:`GLVector` class, which encapsulates the logic for
    rendering 2D slices of a ``X*Y*Z*3`` :class:`.Image` as a vector image.
    The ``GLVector`` class is a sub-class of :class:`.GLImageObject`.


    The ``GLVector`` class is a base class which is not intended to be
    instantiated directly. The :class:`.GLRGBVector` and
    :class:`.GLLineVector` subclasses should be used instead.  These two
    subclasses share the functionality provided by this class.


    The :class:`.Image` is stored on the GPU as a 3D RGB
    :class:`.ImageTexture`, where the ``R`` channel contains the ``x`` vector
    values, the ``G`` channel the ``y`` values, and the ``B`` channel the
    ``z`` values.


    Three 1D :class:`.ColourMapTexture` instances are used to store a colour
    table for each of the ``x``, ``y`` and ``z`` components. A custom fragment
    shader program looks up the ``xyz`` vector values, looks up colours for
    each of them, and combines the three colours to form the final fragment
    colour.


    The colour of each vector may be modulated by another image, specified by
    the :attr:`.VectorOpts.modulate` property.  This modulation image is
    stored as a 3D single-channel :class:`.ImageTexture`.
    """

    
    def __init__(self, image, display, prefilter=None):
        """Create a ``GLVector`` object bound to the given image and display.

        Initialises the OpenGL data required to render the given image.
        This method does the following:
        
          - Creates the image texture, the modulate texture, and the three
            colour map textures.

          - Adds listeners to the :class:`.Display` and :class:`.VectorOpts`
            instances, so the textures and geometry can be updated when
            necessary.

        :arg image:     An :class:`.Image` object.
        
        :arg display:   A :class:`.Display` object which describes how the
                        image is to be displayed.

        :arg prefilter: An optional function which filters the data before it
                        is stored as a 3D texture. See :class:`.ImageTexture`.
                        Whether or not this function is provided, the data is
                        transposed so that the fourth dimension is the fastest
                        changing.
        """

        if not image.is4DImage() or image.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ vector angles')

        globject.GLImageObject.__init__(self, image, display)

        name = self.name

        self.xColourTexture = textures.ColourMapTexture('{}_x'.format(name))
        self.yColourTexture = textures.ColourMapTexture('{}_y'.format(name))
        self.zColourTexture = textures.ColourMapTexture('{}_z'.format(name))
        self.modTexture     = None
        self.imageTexture   = None
        self.prefilter      = prefilter

        self.addListeners()
        self.refreshImageTexture()
        self.refreshModulateTexture()
        self.refreshColourTextures()

        
    def destroy(self):
        """Must be called when this ``GLVector`` is no longer needed. Deletes
        the GL textures, and deregisters the listeners configured in
        :meth:`__init__`.
        """

        self.xColourTexture.destroy()
        self.yColourTexture.destroy()
        self.zColourTexture.destroy()

        glresources.delete(self.imageTexture.getTextureName())
        glresources.delete(self.modTexture  .getTextureName())

        self.imageTexture = None
        self.modTexture   = None

        self.removeListeners()

        globject.GLImageObject.destroy(self)


    def addListeners(self):
        """Called by :meth:`__init__`. Adds listeners to properties of the
        :class:`.Display` and :class:`.VectorOpts` instances, so that the GL
        representation can be updated when the display properties change.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name
        
        def modUpdate( *a):
            self.refreshModulateTexture()
            self.updateShaderState()
            self.onUpdate()

        def cmapUpdate(*a):
            self.refreshColourTextures()
            self.updateShaderState()
            self.onUpdate()
            
        def shaderUpdate(*a):
            self.updateShaderState()
            self.onUpdate() 

        def shaderCompile(*a):
            self.compileShaders()
            self.updateShaderState()
            self.onUpdate()

        def imageRefresh(*a):
            self.refreshImageTexture()
            self.updateShaderState()
            self.onUpdate()
            
        def imageUpdate(*a):

            self.imageTexture.set(resolution=opts.resolution)
            self.updateShaderState()
            self.onUpdate()

        display.addListener('softwareMode',  name, shaderCompile, weak=False)
        display.addListener('alpha',         name, cmapUpdate,    weak=False)
        display.addListener('brightness',    name, cmapUpdate,    weak=False)
        display.addListener('contrast',      name, cmapUpdate,    weak=False)
        opts   .addListener('xColour',       name, cmapUpdate,    weak=False)
        opts   .addListener('yColour',       name, cmapUpdate,    weak=False)
        opts   .addListener('zColour',       name, cmapUpdate,    weak=False)
        opts   .addListener('suppressX',     name, cmapUpdate,    weak=False)
        opts   .addListener('suppressY',     name, cmapUpdate,    weak=False)
        opts   .addListener('suppressZ',     name, cmapUpdate,    weak=False)
        opts   .addListener('modulate',      name, modUpdate,     weak=False)
        opts   .addListener('modThreshold',  name, shaderUpdate,  weak=False)
        opts   .addListener('resolution',    name, imageUpdate,   weak=False)

        if opts.getParent() is not None:
            opts.addSyncChangeListener(
                'resolution', name, imageRefresh, weak=False)


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all property listeners added
        by  the :meth:`addListeners` method.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        display.removeListener('softwareMode', name)
        display.removeListener('alpha',        name)
        display.removeListener('brightness',   name)
        display.removeListener('contrast',     name)
        opts   .removeListener('xColour',      name)
        opts   .removeListener('yColour',      name)
        opts   .removeListener('zColour',      name)
        opts   .removeListener('suppressX',    name)
        opts   .removeListener('suppressY',    name)
        opts   .removeListener('suppressZ',    name)
        opts   .removeListener('modulate',     name)
        opts   .removeListener('modThreshold', name)
        opts   .removeListener('volume',       name)
        opts   .removeListener('resolution',   name)

        if opts.getParent() is not None:
            opts.removeSyncChangeListener('resolution', name)


    def refreshImageTexture(self):
        """Called by :meth:`__init__`, and when the :class:`.ImageTexture`
        needs to be updated. (Re-)creates the ``ImageTexture``, using the
        :mod:`.resources` module so that the texture can be shared by other
        users.
        """

        opts      = self.displayOpts
        prefilter = self.prefilter
        texName   = '{}_{}'.format(type(self).__name__, id(self.image))
        
        if self.imageTexture is not None:
            glresources.delete(self.imageTexture.getTextureName())
            
        # the fourth dimension (the vector directions) 
        # must be the fastest changing in the texture data
        if prefilter is None:
            realPrefilter = lambda d:           d.transpose((3, 0, 1, 2))
        else:
            realPrefilter = lambda d: prefilter(d.transpose((3, 0, 1, 2)))

        unsynced = (opts.getParent() is None                or 
                    not opts.isSyncedToParent('resolution') or
                    not opts.isSyncedToParent('volume'))

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))
        
        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            self.image,
            nvals=3,
            normalise=True,
            prefilter=realPrefilter) 

    
    def compileShaders(self):
        """This method must be provided by subclasses (the
        :class:`.GLRGBVector` and :class:`.GLLineVector` classes), and must
        compile the vertex/fragment shaders used to render this ``GLVector``.
        .""" 
        raise NotImplementedError('compileShaders must be implemented by '
                                  '{} subclasses'.format(type(self).__name__)) 


    def updateShaderState(self):
        """This method must be provided by subclasses (the
        :class:`.GLRGBVector` and :class:`.GLLineVector` classes), and must
        update the state of the vertex/fragment shader programs.
        """
        raise NotImplementedError('updateShaderState must be implemented by '
                                  '{} subclasses'.format(type(self).__name__))

    
    def refreshModulateTexture(self):
        """Called when the :attr`.VectorOpts.modulate` property changes.

        Reconfigures the modulation :class:`.ImageTexture`. If no modulation
        image is selected, a 'dummy' texture is creatad, which contains all
        white values (and which result in the modulation texture having no
        effect).
        """

        if self.modTexture is not None:
            glresources.delete(self.modTexture.getTextureName())

        modImage = self.displayOpts.modulate

        if modImage is None or modImage == 'none':
            textureData = np.zeros((5, 5, 5), dtype=np.uint8)
            textureData[:] = 255
            modImage   = fslimage.Image(textureData)
            modOpts    = None
            norm       = False
            
        else:
            modOpts = self.displayOpts.displayCtx.getOpts(modImage)
            norm    = True

        texName = '{}_{}_{}_modulate'.format(
            type(self).__name__, id(self.image), id(modImage))

        if modOpts is not None:
            unsynced = (modOpts.getParent() is None                or
                        not modOpts.isSyncedToParent('resolution') or
                        not modOpts.isSyncedToParent('volume'))

            # TODO If unsynced, this GLVector needs to 
            # update the modulate texture whenever its
            # volume/resolution properties change.
            # Right?
            if unsynced:
                texName = '{}_unsync_{}'.format(texName, id(modOpts))
 
        self.modTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            modImage,
            normalise=norm)


    def refreshColourTextures(self, colourRes=256):
        """Called when the component colour maps need to be updated, when one
        of the :attr:`.VectorOpts.xColour`, ``yColour``, ``zColour``,
        ``suppressX``, ``suppressY``, or ``suppressZ`` properties change.

        Regenerates the colour textures.
        """

        display = self.display
        opts    = self.displayOpts

        xcol = opts.xColour
        ycol = opts.yColour
        zcol = opts.zColour

        xcol[3] = 1.0
        ycol[3] = 1.0
        zcol[3] = 1.0

        xsup = opts.suppressX
        ysup = opts.suppressY
        zsup = opts.suppressZ 

        xtex = self.xColourTexture
        ytex = self.yColourTexture
        ztex = self.zColourTexture

        drange = fslcm.briconToDisplayRange(
            (0.0, 1.0),
            display.brightness / 100.0,
            display.contrast   / 100.0)
        
        for colour, texture, suppress in zip(
                (xcol, ycol, zcol),
                (xtex, ytex, ztex),
                (xsup, ysup, zsup)):

            if not suppress:
                
                cmap = np.array(
                    [np.linspace(0.0, i, colourRes) for i in colour]).T
                
                # Component magnitudes of 0 are
                # transparent, but any other
                # magnitude is fully opaque
                cmap[:, 3] = display.alpha / 100.0
                cmap[0, 3] = 0.0 
            else:
                cmap = np.zeros((colourRes, 4))

            texture.set(cmap=cmap, displayRange=drange)
        
        
    def preDraw(self):
        """Must be called by subclass implementations.

        Ensures that the five textures (the vector and modulation images,
        and the three colour textures) are bound to texture units 0-4
        respectively.
        """
        
        self.imageTexture  .bindTexture(gl.GL_TEXTURE0)
        self.modTexture    .bindTexture(gl.GL_TEXTURE1)
        self.xColourTexture.bindTexture(gl.GL_TEXTURE2)
        self.yColourTexture.bindTexture(gl.GL_TEXTURE3)
        self.zColourTexture.bindTexture(gl.GL_TEXTURE4)

        
    def postDraw(self):
        """Must be called by subclass implementations.

        Unbindes the five GL textures.
        """

        self.imageTexture  .unbindTexture()
        self.modTexture    .unbindTexture()
        self.xColourTexture.unbindTexture()
        self.yColourTexture.unbindTexture()
        self.zColourTexture.unbindTexture()
