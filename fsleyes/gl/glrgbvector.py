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


    ========================================== ===============================
    ``init(GLRGBVector)``                      Perform any necessary
                                               initialisation.
    ``destroy(GLRGBVector)``                   Perform any necessary clean up.
    ``compileShaders(GLRGBVector)``            Compiles vertex/fragment
                                               shaders.
    ``updateShaderState(GLRGBVector)``         Updates vertex/fragment
                                               shaders.
    ``preDraw(GLRGBVector, xform, bbox)``      Prepare the GL state for
                                               drawing.
    ``draw2D(GLRGBVector, zpos, xform, bbox)`` Draw the slice specified by
                                               ``zpos``.
    ``draw3D(GLRGBVector, zpos, xform)``       Draw the volume in 3D
    ``drawAll(GLRGBVector, zposes, xforms)``   Draw all slices specified by
                                               ``zposes``.
    ``postDraw(GLRGBVector, xform, bbox)``     Clean up the GL state after
                                               drawing.
    ========================================== ===============================
    """


    def __init__(self, image, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLRGBVector``.

        :arg image:       An :class:`.Image` or :class:`.DTIFitTensor`
                          instance.
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg canvas:      The canvas doing the drawing.
        :arg threedee:    2D or 3D rendering
        """

        # If the overlay is a DTIFitTensor, use the
        # V1 image is the vector data. Otherwise,
        # assume that the overlay is the vector image.
        if isinstance(image, dtifit.DTIFitTensor): vecImage = image.V1()
        else:                                      vecImage = image

        def prefilter(data):
            # make absolute, and scale to unit
            # length if required. We must make
            # the data absolute, otherwise we
            # cannot perform interpolation on
            # the texture when displaying it.
            data = np.abs(data)
            if self.opts.unitLength:
                with np.errstate(invalid='ignore'):
                    x            = data[0, ...]
                    y            = data[1, ...]
                    z            = data[2, ...]
                    lens         = np.sqrt(x ** 2 + y ** 2 + z ** 2)
                    data[0, ...] = x / lens
                    data[1, ...] = y / lens
                    data[2, ...] = z / lens
            return data

        def prefilterRange(dmin, dmax):
            if self.opts.unitLength:
                return 0, 1
            else:
                return max((0, dmin)), max((abs(dmin), abs(dmax)))

        glvector.GLVector.__init__(self,
                                   image,
                                   overlayList,
                                   displayCtx,
                                   canvas,
                                   threedee,
                                   prefilter=prefilter,
                                   prefilterRange=prefilterRange,
                                   vectorImage=vecImage,
                                   init=lambda: fslgl.glrgbvector_funcs.init(
                                       self))

        self.opts.addListener('interpolation',
                              self.name,
                              self.__interpChanged)
        self.opts.addListener('unitLength',
                              self.name,
                              self.__unitLengthChanged)



    def destroy(self):
        """Must be called when this ``GLRGBVector`` is no longer needed.
        Removes some property listeners from the :class:`.RGBVectorOpts`
        instance, calls the OpenGL version-specific ``destroy``
        function, and calls the :meth:`.GLVector.destroy` method.
        """
        self.opts.removeListener('interpolation', self.name)
        self.opts.removeListener('unitLength',    self.name)
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


    def __unitLengthChanged(self, *a):
        """Called when :attr:`.RGBVectorOpts.unitLength` changes. Refreshes
        the texture data.
        """
        self.imageTexture.refresh()


    def compileShaders(self):
        """Overrides :meth:`.GLVector.compileShaders`. Calls the OpenGL
        version-specific ``compileShaders`` function.
        """
        fslgl.glrgbvector_funcs.compileShaders(self)


    def updateShaderState(self):
        """Overrides :meth:`.GLVector.compileShaders`. Calls the OpenGL
        version-specific ``updateShaderState`` function.
        """
        return fslgl.glrgbvector_funcs.updateShaderState(self)


    def preDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLVector.preDraw`. Calls the base class
        implementation, and the OpenGL version-specific ``preDraw`` function.
        """
        glvector.GLVector.preDraw(self, xform, bbox)
        fslgl.glrgbvector_funcs.preDraw(self, xform, bbox)


    def draw2D(self, *args, **kwargs):
        """Overrides :meth:`.GLVector.draw2D`. Calls the OpenGL
        version-specific ``draw2D`` function.
        """
        with glroutines.enabled((gl.GL_CULL_FACE)):
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glCullFace(gl.GL_BACK)
            gl.glFrontFace(self.frontFace())
            fslgl.glrgbvector_funcs.draw2D(self, *args, **kwargs)


    def draw3D(self, *args, **kwargs):
        """Overrides :meth:`.GLVector.draw3D`. Calls the OpenGL
        version-specific ``draw3D`` function.
        """
        fslgl.glrgbvector_funcs.draw3D(self, *args, **kwargs)


    def drawAll(self, *args, **kwargs):
        """Overrides :meth:`.GLVector.drawAll`. Calls the OpenGL
        version-specific ``drawAll`` function.
        """
        fslgl.glrgbvector_funcs.drawAll(self, *args, **kwargs)


    def postDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLVector.postDraw`. Calls the base class
        implementation, and the OpenGL version-specific ``postDraw``
        function.
        """
        glvector.GLVector.postDraw(self, xform, bbox)
        fslgl.glrgbvector_funcs.postDraw(self, xform, bbox)
