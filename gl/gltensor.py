#!/usr/bin/env python
#
# gltensor.py - The GLTensor class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLTensor` class, for displaying tensor
ellipsoids in a :class:`.TensorImage` overlay.

See :mod:`.gl21.gltensor_funcs`.
"""


import numpy as np

import glvector

import fsl.fsleyes.gl as fslgl


class GLTensor(glvector.GLVector):
    """The ``GLTensor`` class encapsulates the logic required to render
    :class:`.TensorImage` overlays.  Most of the functionality is in the
    :mod:`.gl21.gltensor_funcs` module.

    .. note:: The ``GLTensor``  is not supported on versions of OpenGL older
              than 2.1.
    """

    
    def __init__(self, image, display):
        """Create a ``GLTensor``. Calls the :func:`.gl21.gltensor_funcs.init`
        function.

        :arg image:   A :class:`.TensorImage` overlay.
        
        :arg display: The :class:`.Display` instance associated with the
                      ``image``.
        """
        glvector.GLVector.__init__(self,
                                   image,
                                   display,
                                   prefilter=np.abs,
                                   vectorImage=image.V1(),
                                   init=lambda: fslgl.gltensor_funcs.init(
                                       self))


    def destroy(self):
        """Must be called when this ``GLTensor`` is no longer needed. Performs
        cleanup tasks.
        """
        glvector.GLVector.destroy(self)
        fslgl.gltensor_funcs.destroy(self)


    def addListeners(self):
        """Overrides :meth:`.GLVector.addListeners`. Calls the base class
        implementation, and adds some property listeners to the
        :class:`.TensorOpts` instance associated with the 
        :class:`.TensorImage` being displayed.
        """
        glvector.GLVector.addListeners(self)

        name = self.name
        opts = self.displayOpts

        def shaderUpdate(*a):
            if self.ready():
                self.updateShaderState()
                self.notify()

        opts.addListener('lighting',         name, shaderUpdate, weak=False)
        opts.addListener('tensorResolution', name, shaderUpdate, weak=False)
        opts.addListener('tensorScale',      name, shaderUpdate, weak=False)
        

    def removeListeners(self):
        """Overrides :meth:`.GLVector.removeListeners`. Calls the base class
        implementation, and removes some property listeners.
        """
        glvector.GLVector.removeListeners(self)

        name = self.name
        opts = self.displayOpts
        
        opts.removeListener('lighting',         name)
        opts.removeListener('tensorResolution', name)
        opts.removeListener('tensorScale',      name)

        
    def getDataResolution(self, xax, yax):
        """Overrides :meth:`.GLVector.getDataResolution`. Returns a pixel
        resolution suitable for off-screen rendering of this ``GLTensor``.
        """

        res       = list(glvector.GLVector.getDataResolution(self, xax, yax))
        res[xax] *= 20
        res[yax] *= 20
        
        return res


    def compileShaders(self):
        """Overrides :meth:`.GLVector.compileShaders`. Calls the
        :func:`.gl21.gltensor_funcs.compileShaders` function.
        """
        fslgl.gltensor_funcs.compileShaders(self)


    def updateShaderState(self):
        """Overrides :meth:`.GLVector.updateShaderState`. Calls the
        :func:`.gl21.gltensor_funcs.updateShaderState` function.
        """ 
        fslgl.gltensor_funcs.updateShaderState(self)

        
    def preDraw(self):
        """Overrides :meth:`.GLVector.preDraw`. Calls the
        :meth:`.GLVector.preDraw` method, and the
        :func:`.gl21.gltensor_funcs.preDraw` function.
        """ 
        glvector.GLVector.preDraw(self)
        fslgl.gltensor_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        """Overrides :meth:`.GLVector.draw`. Calls the
        :func:`.gl21.gltensor_funcs.draw` function.
        """
        fslgl.gltensor_funcs.draw(self, zpos, xform)


    def postDraw(self):
        """Overrides :meth:`.GLVector.postDraw`. Calls the
        :meth:`.GLVector.postDraw` method, and the
        :func:`.gl21.gltensor_funcs.postDraw` function.
        """ 
        glvector.GLVector.postDraw(self)
        fslgl.gltensor_funcs.postDraw(self)
