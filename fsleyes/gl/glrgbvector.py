#!/usr/bin/env python
#
# glrgbvector.py - The GLRGBVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This mdoule provides the :class:`GLRGBVector` class, for displaying 3D
vector :class:`.Image` overlays in RGB mode.
"""


import numpy               as np
import OpenGL.GL           as gl

import fsl.data.dtifit     as dtifit
import fsleyes.gl          as fslgl
import fsleyes.gl.routines as glroutines
import fsleyes.gl.glvector as glvector


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


    ======================================== ===============================
    ``init(GLRGBVector)``                    Perform any necessary
                                             initialisation.
    ``destroy(GLRGBVector)``                 Perform any necessary clean up.
    ``compileShaders(GLRGBVector)``          Compiles vertex/fragment
                                             shaders.
    ``updateShaderState(GLRGBVector)``       Updates vertex/fragment
                                             shaders.
    ``preDraw(GLRGBVector)``                 Prepare the GL state for
                                             drawing.
    ``draw2D(GLRGBVector, zpos, xform)``     Draw the slice specified by
                                             ``zpos``.
    ``drawAll(GLRGBVector, zposes, xforms)`` Draw all slices specified by
                                             ``zposes``.
    ``postDraw(GLRGBVector)``                Clean up the GL state after
                                             drawing.
    ======================================== ===============================
    """


    def __init__(self, image, overlayList, displayCtx, threedee):
        """Create a ``GLRGBVector``.

        :arg image:       An :class:`.Image` or :class:`.DTIFitTensor`
                          instance.
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg threedee:    2D or 3D rendering
        """

        # If the overlay is a DTIFitTensor, use the
        # V1 image is the vector data. Otherwise,
        # assume that the overlay is the vector image.
        if isinstance(image, dtifit.DTIFitTensor): vecImage = image.V1()
        else:                                      vecImage = image

        def prefilter(data):

            # Vector images stored as RGB24 data type
            # contain values from [0, 255] so cannot
            # be made absolute
            if vecImage.nvals > 1:
                return data

            # We must make the vector values absolute,
            # otherwise we cannot perform interpolation
            # on the texture when displaying it.
            return np.abs(data)

        def prefilterRange(dmin, dmax):
            return max((0, dmin)), max((abs(dmin), abs(dmax)))

        glvector.GLVector.__init__(self,
                                   image,
                                   overlayList,
                                   displayCtx,
                                   threedee,
                                   prefilter=prefilter,
                                   prefilterRange=prefilterRange,
                                   vectorImage=vecImage,
                                   init=lambda: fslgl.glrgbvector_funcs.init(
                                       self))

        self.opts.addListener('interpolation',
                              self.name,
                              self.__interpChanged)
        self.opts.addListener('normaliseColour',
                              self.name,
                              self.asyncUpdateShaderState)


    def destroy(self):
        """Must be called when this ``GLRGBVector`` is no longer needed.
        Removes some property listeners from the :class:`.RGBVectorOpts`
        instance, calls the OpenGL version-specific ``destroy``
        function, and calls the :meth:`.GLVector.destroy` method.
        """
        self.opts.removeListener('interpolation',   self.name)
        self.opts.removeListener('normaliseColour', self.name)
        fslgl.glrgbvector_funcs.destroy(self)
        glvector.GLVector.destroy(self)


    def refreshImageTexture(self):
        """Overrides :meth:`.GLVector.refreshImageTexture`. Calls the base
        class implementation.
        """
        opts = self.opts

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        glvector.GLVector.refreshImageTexture(self, interp)


    def registerAuxImage(self, which, image, onReady=None):
        """Overrides :meth:`.GLVector.refreshAuxTexture`. Calls the base
        class implementation.
        """
        opts = self.opts

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        glvector.GLVector.registerAuxImage(
            self, which, image, onReady, interp=interp)


    def __interpChanged(self, *a):
        """Called when the :attr:`.RGBVectorOpts.interpolation` property
        changes. Updates the :class:`.ImageTexture` interpolation.
        """
        opts = self.opts

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        self.imageTexture   .set(interp=interp)
        self.modulateTexture.set(interp=interp)
        self.clipTexture    .set(interp=interp)
        self.colourTexture  .set(interp=interp)
        self.asyncUpdateShaderState(alwaysNotify=True)


    def compileShaders(self):
        """Overrides :meth:`.GLVector.compileShaders`. Calls the OpenGL
        version-specific ``compileShaders`` function.
        """
        fslgl.glrgbvector_funcs.compileShaders(self)


    def updateShaderState(self):
        """Overrides :meth:`.GLVector.updateShaderState`. Calls the OpenGL
        version-specific ``updateShaderState`` function.
        """
        return fslgl.glrgbvector_funcs.updateShaderState(self)


    def preDraw(self):
        """Overrides :meth:`.GLVector.preDraw`. Calls the base class
        implementation, and the OpenGL version-specific ``preDraw`` function.
        """
        glvector.GLVector.preDraw(self)
        fslgl.glrgbvector_funcs.preDraw(self)


    def draw2D(self, canvas, *args, **kwargs):
        """Overrides :meth:`.GLVector.draw2D`. Calls the OpenGL
        version-specific ``draw2D`` function.
        """
        with glroutines.enabled((gl.GL_CULL_FACE)):
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glCullFace(gl.GL_BACK)
            gl.glFrontFace(self.frontFace(canvas))
            fslgl.glrgbvector_funcs.draw2D(self, canvas, *args, **kwargs)


    def draw3D(self, *args, **kwargs):
        """Does nothing. """


    def drawAll(self, *args, **kwargs):
        """Overrides :meth:`.GLVector.drawAll`. Calls the OpenGL
        version-specific ``drawAll`` function.
        """
        fslgl.glrgbvector_funcs.drawAll(self, *args, **kwargs)


    def postDraw(self):
        """Overrides :meth:`.GLVector.postDraw`. Calls the base class
        implementation, and the OpenGL version-specific ``postDraw``
        function.
        """
        glvector.GLVector.postDraw(self)
        fslgl.glrgbvector_funcs.postDraw(self)
