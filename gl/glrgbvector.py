#!/usr/bin/env python
#
# glrgbvector.py - The GLRGBVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This mdoule provides the :class:`GLRGBVector` class, for displaying 3D
vector :class:`.Image` overlays in RGB mode.
"""


import numpy                   as np
import OpenGL.GL               as gl

import fsl.data.tensorimage    as tensorimage
import fsl.fsleyes.gl          as fslgl
import fsl.fsleyes.gl.glvector as glvector


class GLRGBVector(glvector.GLVector):
    """The ``GLRGBVector`` class encapsulates the logic required to render a
    ``x*y*z*3`` :class:`.Image` instance as a vector image, where the
    direction of the vector at each voxel is represented by a combination of
    three colours (one colour per axis).  The ``GLRGBVector`` class assumes
    that the :class:`.Display` instance associated with the ``Image`` overlay
    holds a reference to a :class:`.RGBVectorOpts` instance, which contains
    ``GLRGBVector``-specific display settings. The ``GLRGBVector`` is a
    sub-class of the :class:`.GLVector` class, and uses the functionality
    provided by ``GLVector``.

    
    A ``GLRGBVector`` can only show the magnitude of a vector, not its
    orientation. Therefore, the absolute values of the :class:`.Image`
    instance are stored in the :class:`.ImageTexture`. This is accomplished
    by passing a ``prefilter`` function to :meth:`.GLVector.__init__`, which
    forces the image values to be unsigned.

    
    The ``GLRGBVector`` uses two OpenGL version-specific modules, the
    :mod:`.gl14.glrgbvector_funcs` and :mod:`.gl21.glrgbvector_funcs` modules,
    to manage the vertex/fragment shader programs that are used in rendering.
    These modules are assumed to provide the following functions:

    ======================================== =================================
    ``init(GLRGBVector)``                    Perform any necessary
                                             initialisation.
    ``destroy(GLRGBVector)``                 Perform any necessary clean up.
    ``compileShaders(GLRGBVector)``          Compiles vertex/fragment shaders.
    ``updateShaderState(GLRGBVector)``       Updates vertex/fragment shaders.
    ``preDraw(GLRGBVector)``                 Prepare the GL state for drawing.
    ``draw(GLRGBVector, zpos, xform)``       Draw the slice specified by
                                             ``zpos``.
    ``drawAll(GLRGBVector, zposes, xforms)`` Draw all slices specified by
                                             ``zposes``.
    ``postDraw(GLRGBVector)``                Clean up the GL state after
                                             drawing.
    ======================================== =================================
    """


    def __init__(self, image, display):
        """Create a ``GLRGBVector``.

        :arg image:   An :class:`.Image` or :class:`.TensorImage` instance.
        :arg display: The associated :class:`.Display` instance.
        """

        # If the overlay is a TensorImage, use the
        # V1 image is the vector data. Otherwise,
        # assume that the overlay is the vector image.
        if isinstance(image, tensorimage.TensorImage): vecImage = image.V1()
        else:                                          vecImage = image

        glvector.GLVector.__init__(self,
                                   image,
                                   display,
                                   prefilter=np.abs,
                                   vectorImage=vecImage)
        
        fslgl.glrgbvector_funcs.init(self)

        self.displayOpts.addListener('interpolation',
                                     self.name,
                                     self.__interpChanged)
        self.vectorImage.addListener('data',
                                     self.name,
                                     self.__dataChanged)
                          

    def destroy(self):
        """Must be called when this ``GLRGBVector`` is no longer needed.
        Removes some property listeners from the :class:`.RGBVectorOpts`
        instance, calls the OpenGL version-specific ``destroy``
        function, and calls the :meth:`.GLVector.destroy` method.
        """
        self.displayOpts.removeListener('interpolation', self.name)
        fslgl.glrgbvector_funcs.destroy(self)
        glvector.GLVector.destroy(self)


    def refreshImageTexture(self):
        """Overrides :meth:`.GLVector.refreshImageTexture`. Calls the base
        class implementation, and calls :meth:`__setInterp`.
        """
        glvector.GLVector.refreshImageTexture(self)
        self.__setInterp()

        
    def __setInterp(self):
        """Updates the interpolation setting on the :class:`.ImageTexture`
        that contains the vector :class:`.Image` being displayed.
        """
        opts = self.displayOpts

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR 
        
        self.imageTexture.set(interp=interp)


    def __dataChanged(self, *a):
        """Called when the :attr:`.Image.data` of the vector image
        changes. Calls :meth:`.GLObject.notify`. 
        """
        self.notify()
        

    def __interpChanged(self, *a):
        """Called when the :attr:`.RGBVectorOpts.interpolation` property
        changes. Updates the :class:`.ImageTexture` interpolation.
        """
        self.__setInterp()
        self.updateShaderState()
        self.notify()


    def compileShaders(self):
        """Overrides :meth:`.GLVector.compileShaders`. Calls the OpenGL
        version-specific ``compileShaders`` function.
        """
        fslgl.glrgbvector_funcs.compileShaders(self)
        

    def updateShaderState(self):
        """Overrides :meth:`.GLVector.compileShaders`. Calls the OpenGL
        version-specific ``updateShaderState`` function.
        """ 
        fslgl.glrgbvector_funcs.updateShaderState(self)


    def preDraw(self):
        """Overrides :meth:`.GLVector.preDraw`. Calls the base class
        implementation, and the OpenGL version-specific ``preDraw`` function.
        """
        glvector.GLVector.preDraw(self)
        fslgl.glrgbvector_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        """Overrides :meth:`.GLVector.draw`. Calls the OpenGL version-specific
        ``draw`` function.
        """ 
        fslgl.glrgbvector_funcs.draw(self, zpos, xform)

    
    def drawAll(self, zposes, xforms):
        """Overrides :meth:`.GLVector.drawAll`. Calls the OpenGL
        version-specific ``drawAll`` function.
        """ 
        fslgl.glrgbvector_funcs.drawAll(self, zposes, xforms) 

    
    def postDraw(self):
        """Overrides :meth:`.GLVector.postDraw`. Calls the base class
        implementation, and the OpenGL version-specific ``postDraw``
        function.
        """ 
        glvector.GLVector.postDraw(self)
        fslgl.glrgbvector_funcs.postDraw(self) 
