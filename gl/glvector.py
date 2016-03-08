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
import fsl.utils.async          as async
import fsl.fsleyes.colourmaps   as fslcm
import resources                as glresources
import                             textures
import                             globject


class GLVector(globject.GLImageObject):
    """The :class:`GLVector` class, which encapsulates the logic for
    rendering 2D slices of a ``X*Y*Z*3`` :class:`.Image` as a vector image.
    The ``GLVector`` class is a sub-class of :class:`.GLImageObject`.


    The ``GLVector`` class is a base class which is not intended to be
    instantiated directly. The :class:`.GLRGBVector`,
    :class:`.GLLineVector` and :class:`.GLTensor` subclasses should be
    used instead.  These subclasses share the functionality provided
    by this class.


    The ``image`` overlay passed to :meth:`__init__` is assumed to be
    an :class:`.Image` instance which contains vector data. If this is not
    the case, the ``vectorImage`` parameter may be used to pass in the
    :class:`.Image` that contains the vector data.

    This vector image is stored on the GPU as a 3D RGB :class:`.ImageTexture`,
    where the ``R`` channel contains the ``x`` vector values, the ``G``
    channel the ``y`` values, and the ``B`` channel the ``z`` values.


    *Colouring*

    A ``GLVector`` can be coloured in one of two ways:

     - Each voxel is coloured according to the orientation of the vector.
       Three 1D :class:`.ColourMapTexture` instances are used to store a
       colour table for each of the ``x``, ``y`` and ``z`` components. A
       custom fragment shader program looks up the ``xyz`` vector values,
       looks up colours for each of them, and combines the three colours to
       form the final fragment colour. The colours for each component
       are specified by the :attr:`.VectorOpts.xColour`,
       :attr:`.VectorOpts.yColour`, and :attr:`.VectorOpts.zColour`
       properties.

     - Each voxel is coloured according to the values contained in another
       image, which are used to look up a colour in a colour map. The image
       and colour map are respectively specified by the
       :attr:`.VectorOpts.colourImage` and :attr:`.VectorOpts.cmap` properties.

    
    In either case, the brightness of each vector colour may be modulated by
    another image, specified by the :attr:`.VectorOpts.modulateImage`
    property.  This modulation image is stored as a 3D single-channel
    :class:`.ImageTexture`.

    Finally, vector voxels may be clipped according to the values of another
    image, specified by the :attr:`.VectorOpts.clipImage` property.  This
    clipping image is stored as a 3D single-channel :class:`.ImageTexture`, and
    the clipping thresholds specified by the :attr:`.VectorOpts.clippingRange`
    property.

    
    *Textures*

    The ``GLVector`` class configures its textures in the following manner:

    =================== ================== 
    ``imageTexture``    ``gl.GL_TEXTURE0``
    ``modulateTexture`` ``gl.GL_TEXTURE1``
    ``clipTexture``     ``gl.GL_TEXTURE2``
    ``colourTexture``   ``gl.GL_TEXTURE3``
    ``xColourTexture``  ``gl.GL_TEXTURE4``
    ``yColourTexture``  ``gl.GL_TEXTURE5``
    ``zColourTexture``  ``gl.GL_TEXTURE6``
    ``cmapTexture``     ``gl.GL_TEXTURE7``
    =================== ==================
    """

    
    def __init__(self,
                 image,
                 display,
                 xax,
                 yax,
                 prefilter=None,
                 vectorImage=None,
                 init=None):
        """Create a ``GLVector`` object bound to the given image and display.

        Initialises the OpenGL data required to render the given image.
        This method does the following:
        
          - Creates the vector image texture, the modulate, clipping and colour
            image textures, and the four colour map textures.

          - Adds listeners to the :class:`.Display` and :class:`.VectorOpts`
            instances, so the textures and geometry can be updated when
            necessary.

        :arg image:       An :class:`.Nifti1` object.
        
        :arg display:     A :class:`.Display` object which describes how the
                          image is to be displayed.

        :arg xax:         Initial display X axis

        :arg yax:         Initial display Y axis        

        :arg prefilter:   An optional function which filters the data before it
                          is stored as a 3D texture. See
                          :class:`.ImageTexture`. Whether or not this function
                          is provided, the data is transposed so that the 
                          fourth dimension is the fastest changing.

        :arg vectorImage: Optional. If ``None``, the ``image`` is assumed to
                          be a 4D :class:`.Image` instance which contains
                          the vector data. If this is not the case, the
                          ``vectorImage`` parameter can be used to specify
                          an ``Image`` instance which does contain the
                          vector data.

        :arg init:        An optional function to be called when all of the
                          :class:`.ImageTexture` instances associated with
                          this ``GLVector`` have been initialised. If this
                          function does any initialisation on one or more
                          separate threads, it should return references to
                          those threads so that this method is able to
                          determine when initialisation is complete.
        """

        if vectorImage is None: vectorImage = image
        if prefilter   is None: prefilter   = lambda d: d

        if len(vectorImage.shape) != 4 or vectorImage.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ vector angles')

        globject.GLImageObject.__init__(self, image, display, xax, yax)

        name = self.name

        self.vectorImage     = vectorImage
        self.xColourTexture  = textures.ColourMapTexture('{}_x' .format(name))
        self.yColourTexture  = textures.ColourMapTexture('{}_y' .format(name))
        self.zColourTexture  = textures.ColourMapTexture('{}_z' .format(name))
        self.cmapTexture     = textures.ColourMapTexture('{}_cm'.format(name))

        self.shader          = None
        self.modulateImage   = None
        self.clipImage       = None
        self.colourImage     = None
        self.modulateOpts    = None
        self.clipOpts        = None
        self.colourOpts      = None
        self.modulateTexture = None
        self.clipTexture     = None
        self.colourTexture   = None
        self.imageTexture    = None
        self.prefilter       = prefilter

        # Make sure we are registered with the
        # auxillary images if any of them are set.
        opts = self.displayOpts
        
        if opts.colourImage   is not None: self.registerAuxImage('colour')
        if opts.modulateImage is not None: self.registerAuxImage('modulate')
        if opts.clipImage     is not None: self.registerAuxImage('clip') 

        self.addListeners()
        self.refreshColourTextures()

        def texRefresh():
            if init is not None: async.wait(init(), self.notify)
            else:                self.notify()

        async.wait([self.refreshImageTexture(),
                    self.refreshAuxTexture('modulate'),
                    self.refreshAuxTexture('clip'),
                    self.refreshAuxTexture('colour')],
                   texRefresh)

        
    def destroy(self):
        """Must be called when this ``GLVector`` is no longer needed. Deletes
        the GL textures, and deregisters the listeners configured in
        :meth:`__init__`.
        """

        self.xColourTexture.destroy()
        self.yColourTexture.destroy()
        self.zColourTexture.destroy()
        self.cmapTexture   .destroy()

        for tex in (self.imageTexture,
                    self.modulateTexture,
                    self.clipTexture,
                    self.colourTexture):
            tex.deregister(self.name)
            glresources.delete(tex.getTextureName())

        self.removeListeners()
        self.deregisterAuxImage('modulate')
        self.deregisterAuxImage('clip')
        self.deregisterAuxImage('colour')

        self.imageTexture    = None
        self.modulateTexture = None
        self.clipTexture     = None
        self.colourTexture   = None
        self.modulateImage   = None
        self.clipImage       = None
        self.colourImage     = None
        self.modulateOpts    = None
        self.clipOpts        = None
        self.colourOpts      = None

        globject.GLImageObject.destroy(self)


    def ready(self):
        """Returns ``True`` if this ``GLVector`` is ready to be drawn,
        ``False`` otherwise.
        """
        return all((self.shader          is not None,
                    self.imageTexture    is not None,
                    self.modulateTexture is not None,
                    self.clipTexture     is not None,
                    self.colourTexture   is not None,
                    self.imageTexture   .ready(),
                    self.modulateTexture.ready(),
                    self.clipTexture    .ready(),
                    self.colourTexture  .ready()))


    def addListeners(self):
        """Called by :meth:`__init__`. Adds listeners to properties of the
        :class:`.Display` and :class:`.VectorOpts` instances, so that the GL
        representation can be updated when the display properties change.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        def update(*a):
            self.notify()
            
        def shaderUpdate(*a):
            if self.ready():
                self.updateShaderState()
                self.notify() 
        
        def modUpdate( *a):
            self.deregisterAuxImage('modulate')
            self.registerAuxImage(  'modulate')
            async.wait([self.refreshAuxTexture( 'modulate')], shaderUpdate)

        def clipUpdate( *a):
            self.deregisterAuxImage('clip')
            self.registerAuxImage(  'clip')
            async.wait([self.refreshAuxTexture( 'clip')], shaderUpdate)

        def colourUpdate( *a):
            self.deregisterAuxImage('colour')
            self.registerAuxImage(  'colour')

            def onRefresh():
                self.compileShaders()
                self.refreshColourTextures()
                shaderUpdate()
                
            async.wait([self.refreshAuxTexture( 'colour')], onRefresh)
            
        def cmapUpdate(*a):
            self.refreshColourTextures()
            shaderUpdate()

        def shaderCompile(*a):
            self.compileShaders()
            shaderUpdate()

        def imageRefresh(*a):
            async.wait([self.refreshImageTexture()], shaderUpdate)
            
        def imageUpdate(*a):
            self.imageTexture.set(resolution=opts.resolution)
            async.wait([self.imageTexture.refreshThread()], shaderUpdate)

        display.addListener('alpha',         name, cmapUpdate,   weak=False)
        display.addListener('brightness',    name, cmapUpdate,   weak=False)
        display.addListener('contrast',      name, cmapUpdate,   weak=False)
        opts   .addListener('xColour',       name, cmapUpdate,   weak=False)
        opts   .addListener('yColour',       name, cmapUpdate,   weak=False)
        opts   .addListener('zColour',       name, cmapUpdate,   weak=False)
        opts   .addListener('cmap',          name, cmapUpdate,   weak=False)
        opts   .addListener('suppressX',     name, cmapUpdate,   weak=False)
        opts   .addListener('suppressY',     name, cmapUpdate,   weak=False)
        opts   .addListener('suppressZ',     name, cmapUpdate,   weak=False)
        opts   .addListener('modulateImage', name, modUpdate,    weak=False)
        opts   .addListener('clipImage',     name, clipUpdate,   weak=False)
        opts   .addListener('colourImage',   name, colourUpdate, weak=False)
        opts   .addListener('clippingRange', name, shaderUpdate, weak=False)
        opts   .addListener('resolution',    name, imageUpdate,  weak=False)
        opts   .addListener('transform',     name, update,       weak=False)

        # See comment in GLVolume.addDisplayListeners about this
        self.__syncListenersRegistered = opts.getParent() is not None 

        if self.__syncListenersRegistered:
            opts.addSyncChangeListener(
                'resolution', name, imageRefresh, weak=False)


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all property listeners added
        by  the :meth:`addListeners` method.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        display.removeListener('alpha',         name)
        display.removeListener('brightness',    name)
        display.removeListener('contrast',      name)
        opts   .removeListener('xColour',       name)
        opts   .removeListener('yColour',       name)
        opts   .removeListener('zColour',       name)
        opts   .removeListener('cmap',          name)
        opts   .removeListener('suppressX',     name)
        opts   .removeListener('suppressY',     name)
        opts   .removeListener('suppressZ',     name)
        opts   .removeListener('modulateImage', name)
        opts   .removeListener('clipImage',     name)
        opts   .removeListener('colourImage',   name)
        opts   .removeListener('clippingRange', name)
        opts   .removeListener('volume',        name)
        opts   .removeListener('resolution',    name)
        opts   .removeListener('transform' ,    name)

        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('resolution', name)


    def refreshImageTexture(self, interp=gl.GL_NEAREST):
        """Called by :meth:`__init__`, and when the :class:`.ImageTexture`
        needs to be updated. (Re-)creates the ``ImageTexture``, using the
        :mod:`.resources` module so that the texture can be shared by other
        users.
        
        :arg interp: Interpolation method (``GL_NEAREST`` or ``GL_LINEAR``).
                     Used by sub-class implementations (see
                     :class:`.GLRGBVector`).
        """

        opts      = self.displayOpts
        prefilter = self.prefilter
        vecImage  = self.vectorImage
        texName   = '{}_{}'.format(type(self).__name__, id(vecImage))
        
        if self.imageTexture is not None:
            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.getTextureName())

        # the fourth dimension (the vector directions) 
        # must be the fastest changing in the texture data
        def realPrefilter(d):
            return prefilter(d.transpose((3, 0, 1, 2)))
            
        unsynced = (opts.getParent() is None                or 
                    not opts.isSyncedToParent('resolution') or
                    not opts.isSyncedToParent('volume'))

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))
        
        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            vecImage,
            nvals=3,
            interp=interp,
            normalise=True,
            prefilter=realPrefilter,
            notify=False)
        
        self.imageTexture.register(self.name, self.__textureChanged)

        return self.imageTexture.refreshThread()

    
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
        update the state of the vertex/fragment shader programs. It must return
        ``True`` if the shader state was updated, ``False`` otherwise.
        """
        raise NotImplementedError('updateShaderState must be implemented by '
                                  '{} subclasses'.format(type(self).__name__))



    def registerAuxImage(self, which):
        """Called when the :attr:`.VectorOpts.modulateImage`,
        :attr:`.VectorOpts.clipImage`, or :attr:`.VectorOpts.colourImage`
        properties change. Registers a listener with the
        :attr:`.Nifti1Opts.volume` property of the modulate/clip/colour image,
        so the modulate/clip/colour textures can be updated when the image
        volume changes.
        """

        imageAttr = '{}Image'  .format(which)
        optsAttr  = '{}Opts'   .format(which)
        texAttr   = '{}Texture'.format(which)
        
        image = getattr(self.displayOpts, imageAttr)
        tex   = getattr(self,             texAttr)

        if image is None or image == 'none':
            image = None

        setattr(self, optsAttr,  None)
        setattr(self, imageAttr, image)
        
        if image is None:
            return

        opts = self.displayOpts.displayCtx.getOpts(image)

        setattr(self, optsAttr, opts)

        def volumeChange(*a):
            
            def onRefresh():
                self.updateShaderState()
                self.notify()
                
            tex.set(volume=opts.volume)
            async.wait([tex.refreshThread()], onRefresh)

        # We set overwrite=True, because
        # the modulate/clip/colour images
        # may be the same.
        opts.addListener('volume',
                         self.name,
                         volumeChange,
                         overwrite=True,
                         weak=False) 

    
    def deregisterAuxImage(self, which):
        """Called when the :attr:`.VectorOpts.modulateImage`,
        :attr:`.VectorOpts.clipImage` or :attr:`.VectorOpts.colourImage`
        properties change.  Deregisters the :attr:`.Nifti1Opts.volume`
        listener that was registered in :meth:`registerAuxImage`.
        """

        imageAttr = '{}Image'.format(which)
        optsAttr  = '{}Opts' .format(which)

        opts = getattr(self, optsAttr)

        if opts is not None:
            opts.removeListener('volume', self.name)

        setattr(self, imageAttr, None)
        setattr(self, optsAttr,  None)
 
            
    def refreshAuxTexture(self, which):
        """Called when the :attr`.VectorOpts.modulateImage`,
        :attr`.VectorOpts.clipImage`, or :attr`.VectorOpts.colourImage`
        properties changes.  Reconfigures the modulation/clip/colour
        :class:`.ImageTexture`. If no image is selected, a 'dummy' texture is
        creatad, which contains all white values (and which result in the
        auxillary textures having no effect).
        """

        imageAttr = '{}Image'  .format(which)
        optsAttr  = '{}Opts'   .format(which)
        texAttr   = '{}Texture'.format(which)

        image = getattr(self, imageAttr)
        opts  = getattr(self, optsAttr)
        tex   = getattr(self, texAttr)

        if tex is not None:
            tex.deregister(self.name)
            glresources.delete(tex.getTextureName())

        if image is None:
            textureData    = np.zeros((5, 5, 5), dtype=np.uint8)
            textureData[:] = 255
            image          = fslimage.Image(textureData)
            norm           = False
            
        else:
            norm = True

        texName = '{}_{}_{}_{}'.format(
            type(self).__name__, id(self.image), id(image), which)

        if opts is not None:
            unsynced = (opts.getParent() is None                or
                        not opts.isSyncedToParent('resolution') or
                        not opts.isSyncedToParent('volume'))

            # TODO If unsynced, this GLVector needs to 
            # update the mod/clip/colour textures whenever
            # their volume/resolution properties change.
            # Right?
            if unsynced:
                texName = '{}_unsync_{}'.format(texName, id(opts))

        if opts is not None: volume = opts.volume
        else:                volume = 0
 
        tex = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            image,
            normalise=norm,
            volume=volume,
            notify=False)
        
        tex.register(self.name, self.__textureChanged)
        
        setattr(self, texAttr, tex)

        return tex.refreshThread()


    def refreshColourTextures(self, colourRes=256):
        """Called when the component colour maps need to be updated, when one
        of the :attr:`.VectorOpts.xColour`, ``yColour``, ``zColour``, ``cmap``,
        ``suppressX``, ``suppressY``, or ``suppressZ`` properties change.

        Regenerates the colour textures.
        """

        # Refresh the xColour/yColour/zColour
        # textures first
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

        # Now do the cmap texture
        if self.colourImage is None:
            dmin, dmax = 0.0, 1.0
        else:
            
            colourImageOpts = opts.displayCtx.getOpts(self.colourImage)

            dmin = colourImageOpts.dataMin
            dmax = colourImageOpts.dataMax

            dmin, dmax = fslcm.briconToDisplayRange(
                (dmin, dmax),
                display.brightness / 100.0,
                display.contrast   / 100.0)
            
        self.cmapTexture.set(cmap=opts.cmap,
                             alpha=display.alpha / 100.0,
                             displayRange=(dmin, dmax)) 
        
        
    def preDraw(self):
        """Must be called by subclass implementations.

        Ensures that all of the textures used by this ``GLVector`` are bound
        to their corresponding texture units.
        """
        
        self.imageTexture   .bindTexture(gl.GL_TEXTURE0)
        self.modulateTexture.bindTexture(gl.GL_TEXTURE1)
        self.clipTexture    .bindTexture(gl.GL_TEXTURE2)
        self.colourTexture  .bindTexture(gl.GL_TEXTURE3)
        self.xColourTexture .bindTexture(gl.GL_TEXTURE4)
        self.yColourTexture .bindTexture(gl.GL_TEXTURE5)
        self.zColourTexture .bindTexture(gl.GL_TEXTURE6)
        self.cmapTexture    .bindTexture(gl.GL_TEXTURE7)

        
    def postDraw(self):
        """Must be called by subclass implementations.

        Unbinds all of the textures used by this ``GLVector``.
        """

        self.imageTexture   .unbindTexture()
        self.modulateTexture.unbindTexture()
        self.clipTexture    .unbindTexture()
        self.colourTexture  .unbindTexture()
        self.xColourTexture .unbindTexture()
        self.yColourTexture .unbindTexture()
        self.zColourTexture .unbindTexture()
        self.cmapTexture    .unbindTexture()

        
    def __textureChanged(self, *a):
        """Called when any of the :class:`.ImageTexture` instances containing
        image, clipping, modulation or colour data, are refreshed. Notifies
        listeners of this ``GLVector`` (via the :class:`.Notifier` base class).
        """
        self.notify()
