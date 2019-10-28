#!/usr/bin/env python
#
# gllinevector.py - The GLLineVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLLineVector` class, for displaying 3D
vector :class:`.Image` overlays in line mode.


The :class:`.GLLineVertices` class is also defined in this module, and is used
in certain rendering situations - specifically, when running in OpenGL
1.4. See the :mod:`.gl14.gllinevector_funcs` and
:mod:`.gl21.gllinevector_funcs` modules for more details.
"""

import logging

import numpy                as np

import fsl.data.dtifit      as dtifit
import fsleyes.gl           as fslgl
import fsleyes.gl.glvector  as glvector


log = logging.getLogger(__name__)


class GLLineVector(glvector.GLVector):
    """The ``GLLineVector`` class encapsulates the logic required to render an
    :class:`.Image` instance of shape ``x*y*z*3``, or type
    ``NIFTI_TYPE_RGB24``, as a vector image, where the vector at each voxel is
    drawn as a line, and coloured in the same way that voxels in the
    :class:`.GLRGBVector` are coloured.  The ``GLLineVector`` class assumes
    that the :class:`.Display` instance associated with the ``Image`` overlay
    holds a reference to a :class:`.LineVectorOpts` instance, which contains
    ``GLLineVector``-specific display settings.  The ``GLLineVector`` class is
    a sub-class of the :class:`.GLVector` class, and uses the functionality
    provided by ``GLVector``.


    In a similar manner to the :class:`.GLRGBVector`, the ``GLLineVector`` uses
    two OpenGL version-specific modules, the :mod:`.gl14.gllinevector_funcs`
    and :mod:`.gl21.gllinevector_funcs` modules. It is assumed that these
    modules define the same functions that are defined by the
    :class:`.GLRGBVector` version specific modules.


    A ``GLLineVector`` instance is rendered in different ways depending upon
    the rendering environment (GL 1.4 vs GL 2.1), so most of the rendering
    functionality is implemented in the version-specific modules mentioned
    above.
    """


    def __init__(self, image, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLLineVector`` instance.

        :arg image:       An :class:`.Image` or :class:`.DTIFitTensor`
                          instance.
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg canvas:      The canvas doing the drawing.
        :arg threedee:    2D or 3D rendering.
        """

        # If the overlay is a DTIFitTensor, use the
        # V1 image is the vector data. Otherwise,
        # assume that the overlay is the vector image.
        if isinstance(image, dtifit.DTIFitTensor): vecImage = image.V1()
        else:                                      vecImage = image

        glvector.GLVector.__init__(self,
                                   image,
                                   overlayList,
                                   displayCtx,
                                   canvas,
                                   threedee,
                                   vectorImage=vecImage,
                                   init=lambda: fslgl.gllinevector_funcs.init(
                                       self))

        self.opts.addListener('lineWidth', self.name, self.notify)


    def destroy(self):
        """Must be called when this ``GLLineVector`` is no longer needed.
        Removes some property listeners from the :class:`.LineVectorOpts`
        instance, calls the OpenGL version-specific ``destroy``
        function, and calls the :meth:`.GLVector.destroy` method.
        """
        self.opts.removeListener('lineWidth', self.name)
        fslgl.gllinevector_funcs.destroy(self)
        glvector.GLVector.destroy(self)


    def getDataResolution(self, xax, yax):
        """Overrides :meth:`.GLImageObject.getDataResolution`. Returns a pixel
        resolution suitable for rendering this ``GLLineVector``.
        """

        res       = list(glvector.GLVector.getDataResolution(self, xax, yax))
        res[xax] *= 20
        res[yax] *= 20

        return res


    def compileShaders(self):
        """Overrides :meth:`.GLVector.compileShaders`. Calls the OpenGL
        version-specific ``compileShaders`` function.
        """
        fslgl.gllinevector_funcs.compileShaders(self)


    def updateShaderState(self):
        """Overrides :meth:`.GLVector.updateShaderState`. Calls the OpenGL
        version-specific ``updateShaderState`` function.
        """
        return fslgl.gllinevector_funcs.updateShaderState(self)


    def preDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLVector.preDraw`. Calls the base class
        implementation, and then calls the OpenGL version-specific ``preDraw``
        function.
        """
        glvector.GLVector.preDraw(self, xform, bbox)
        fslgl.gllinevector_funcs.preDraw(self, xform, bbox)


    def draw2D(self, *args, **kwargs):
        """Overrides :meth:`.GLObject.draw2D`. Calls the OpenGL
        version-specific ``draw2D`` function.
        """
        fslgl.gllinevector_funcs.draw2D(self, *args, **kwargs)


    def draw3D(self, *args, **kwargs):
        """Overrides :meth:`.GLObject.draw3D`. Calls the OpenGL
        version-specific ``draw3D`` function.
        """
        fslgl.gllinevector_funcs.draw3D(self, *args, **kwargs)


    def drawAll(self, *args, **kwargs):
        """Overrides :meth:`.GLObject.drawAll`. Calls the OpenGL
        version-specific ``drawAll`` function.
        """
        fslgl.gllinevector_funcs.drawAll(self, *args, **kwargs)


    def postDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLVector.postDraw`. Calls the base class
        implementation, and then calls the OpenGL version-specific ``postDraw``
        function.
        """
        glvector.GLVector.postDraw(self, xform, bbox)
        fslgl.gllinevector_funcs.postDraw(self, xform, bbox)


class GLLineVertices(object):
    """The ``GLLineVertices`` class is used in some cases when rendering a
    :class:`GLLineVector`. It contains logic to generate vertices for every
    vector in the vector :class:`.Image` that is being displayed by a
    ``GLLineVector`` instance.


    After a ``GLLineVertices`` instance has been created, the :meth:`refresh`
    method can be used to generate line vector vertices and voxel
    coordinates for every voxel in the :class:`Image`. These vertices and
    coordinates are stored as attributes of the ``GLLineVertices`` instance.


    Later, when the line vectors from a 2D slice  of the image need to be
    displayed, the :meth:`getVertices2D` method can be used to extract the
    vertices and coordinates from the slice.


    A ``GLLineVertices`` instance is not associated with a specific
    ``GLLineVector`` instance. This is so that a single  ``GLLineVertices``
    instance can be shared between more than one ``GLLineVector``, avoiding
    the need to store multiple copies of the vertices and voxel
    coordinates. This means that a ``GLLineVector`` instance needs to be
    passed to most of the methods of a ``GLLineVertices`` instance.
    """

    def __init__(self, glvec):
        """Create a ``GLLineVertices``. Vertices are calculated for the
        given :class:`.GLLineVector` instance.

        :arg glvec: A :class:`GLLineVector` which is using this
                    ``GLLineVertices`` instance.
        """

        self.__hash = None
        self.refresh(glvec)


    def destroy(self):
        """Should be called when this ``GLLineVertices`` instance is no
        longer needed. Clears references to cached vertices/coordinates.
        """
        self.vertices  = None
        self.voxCoords = None


    def __hash__(self):
        """Returns a hash of this ``GLLineVertices`` instance. The hash value
        is calculated and cached on every call to :meth:`refresh`, using the
        :meth:`calculateHash` method.  This method returns that cached value.
        """
        return self.__hash


    def calculateHash(self, glvec):
        """Calculates and returns a hash value that can be used to determine
        whether the vertices of this this ``GLLineVertices`` instance need to
        be recalculated. The hash value is based on some properties of the
        :class:`.LineVectorOpts` instance, associated with the given
        :class:`.GLLineVector`.

        For a ``GLLineVertices`` instance called ``verts``, if the following
        test::

            hash(verts) != verts.calculateHash(glvec)

        evaluates to ``False``, the vertices need to be refreshed (via a
        call to :meth:`refresh`).
        """
        opts = glvec.opts
        return (hash(opts.transform)  ^
                hash(opts.orientFlip) ^
                hash(opts.directed)   ^
                hash(opts.unitLength) ^
                hash(opts.lengthScale))


    def refresh(self, glvec):
        """(Re-)calculates the vertices  of this ``GLLineVertices`` instance.

        For each voxel, in the :class:`.Image` overlay being displayed by the
        :class:`GLLineVector` associated with this ``GLLineVertices``
        instance, two vertices are generated, which define a line that
        represents the vector at the voxel.

        The vertices are stored as a :math:`X\\times Y\\times Z\\times
        2\\times 3` ``numpy`` array, as an attribute of this instance,
        called ``vertices``.
        """

        opts  = glvec.opts
        image = glvec.vectorImage
        data  = image.data
        shape = image.shape

        # Pull out the xyz components of the
        # vectors, and calculate vector lengths.

        # The image may either
        # have shape (X, Y, Z, 3)

        if image.nvals == 1:
            vertices = np.array(data, dtype=np.float32)
        # Or (we assume) a RGB
        # structured array
        else:
            vertices         = np.zeros(list(data.shape) + [3],
                                        dtype=np.float32)
            vertices[..., 0] = (data['R'].astype(np.float32) / 127.5) - 1
            vertices[..., 1] = (data['G'].astype(np.float32) / 127.5) - 1
            vertices[..., 2] = (data['B'].astype(np.float32) / 127.5) - 1

        x    = vertices[..., 0]
        y    = vertices[..., 1]
        z    = vertices[..., 2]
        lens = np.sqrt(x ** 2 + y ** 2 + z ** 2)

        # Flip vectors about the x axis if necessary
        if opts.orientFlip:
            x = -x

        if opts.unitLength:

            # scale the vector lengths to 0.5
            with np.errstate(invalid='ignore'):
                vertices[..., 0] = 0.5 * x / lens
                vertices[..., 1] = 0.5 * y / lens
                vertices[..., 2] = 0.5 * z / lens

            # Scale the vector data by the minimum
            # voxel length, so it is a unit vector
            # within real world space
            vertices /= (image.pixdim[:3] / min(image.pixdim[:3]))

        # Scale the vectors by the length scaling factor
        vertices *= opts.lengthScale / 100.0

        # Duplicate vector data so that each
        # vector is represented by two vertices,
        # representing a line through the origin.
        # Or, if displaying directed vectors,
        # add an origin point for each vector.
        if opts.directed:
            origins  = np.zeros(vertices.shape, dtype=np.float32)
            vertices = np.concatenate((origins, vertices), axis=3)
        else:
            vertices = np.concatenate((-vertices, vertices), axis=3)

        vertices = vertices.reshape((shape[0],
                                     shape[1],
                                     shape[2],
                                     2,
                                     3))

        self.vertices = vertices
        self.__hash   = self.calculateHash(glvec)


    def getVertices2D(self, glvec, zpos, axes, bbox=None):
        """Extracts and returns a slice of line vertices, and the associated
        voxel coordinates, which are in a plane located at the given Z
        position (in display coordinates).

        This method assumes that the :meth:`refresh` method has already been
        called.
        """

        image    = glvec.image
        shape    = image.shape[:3]
        xax, yax = axes[:2]

        vertices  = self.vertices
        voxCoords = glvec.generateVoxelCoordinates2D(zpos, axes, bbox)

        # Turn the voxel coordinates into
        # indices suitable for looking up
        # the corresponding vertices
        coords = np.array(np.floor(voxCoords + 0.5), dtype=np.int32)

        # remove any out-of-bounds voxel coordinates
        shape     = np.array(vertices.shape[:3])
        inBounds  = ((coords >= [0, 0, 0]) & (coords < shape)).all(1)
        coords    = coords[   inBounds, :].T
        voxCoords = voxCoords[inBounds, :]

        # pull out the vertex data
        # corresponding to the voxels
        vertices = vertices[coords[0], coords[1], coords[2], :, :]
        vertices = vertices.reshape(-1, 3)

        if not vertices.flags['C_CONTIGUOUS']:
            vertices = np.ascontiguousarray(vertices)

        voxCoords = voxCoords.repeat(repeats=2, axis=0)

        return vertices, voxCoords
