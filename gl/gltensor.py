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
    :class:`.TensorImage` overlays.
    """

    
    def __init__(self, image, display):
        glvector.GLVector.__init__(self,
                                   image,
                                   display,
                                   prefilter=np.abs,
                                   vectorImage=image.V1())
        fslgl.gltensor_funcs.init(self)


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
            self.updateShaderState()
            self.onUpdate()

        opts.addListener('lighting',         name, shaderUpdate, weak=False)
        opts.addListener('tensorResolution', name, shaderUpdate, weak=False)
        

    def removeListeners(self):
        """Overrides :meth:`.GLVector.removeListeners`. Calls the base class
        implementation, and removes some property listeners.
        """
        glvector.GLVector.removeListeners(self)

        name = self.name
        opts = self.displayOpts
        
        opts.removeListener('lighting',         name)
        opts.removeListener('tensorResolution', name)

        
    def getDataResolution(self, xax, yax):
        """Overrides :meth:`.GLVector.getDataResolution`. Returns a pixel
        resolution suitable for off-screen rendering of this ``GLTensor``.
        """

        res       = list(glvector.GLVector.getDataResolution(self, xax, yax))
        res[xax] *= 20
        res[yax] *= 20
        
        return res


    def compileShaders(self):
        """Overrides :meth:`.GLVector.compileShaders`.
        """
        fslgl.gltensor_funcs.compileShaders(self)


    def updateShaderState(self):
        """Overrides :meth:`.GLVector.updateShaderState`.
        """ 
        fslgl.gltensor_funcs.updateShaderState(self)

        
    def preDraw(self):
        """Overrides :meth:`.GLVector.preDraw`.
        """ 
        glvector.GLVector.preDraw(self)
        fslgl.gltensor_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        """
        """
        fslgl.gltensor_funcs.draw(self, zpos, xform)


    def postDraw(self):
        """Overrides :meth:`.GLVector.postDraw`.
        """ 
        glvector.GLVector.postDraw(self)
        fslgl.gltensor_funcs.postDraw(self)
