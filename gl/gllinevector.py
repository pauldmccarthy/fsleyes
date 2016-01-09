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

import numpy                   as np

import fsl.utils.transform     as transform
import fsl.data.tensorimage    as tensorimage
import fsl.fsleyes.gl          as fslgl
import fsl.fsleyes.gl.glvector as glvector
import fsl.fsleyes.gl.routines as glroutines


log = logging.getLogger(__name__)


class GLLineVector(glvector.GLVector):
    """The ``GLLineVector`` class encapsulates the logic required to render a
    ``x*y*z*3`` :class:`.Image` instance as a vector image, where the vector
    at each voxel is drawn as a line, and coloured in the same way that voxels
    in the :class:`.GLRGBVector` are coloured.  The ``GLLineVector`` class
    assumes that the :class:`.Display` instance associated with the ``Image``
    overlay holds a reference to a :class:`.LineVectorOpts` instance, which
    contains ``GLLineVector``-specific display settings.  The ``GLLineVector``
    class is a sub-class of the :class:`.GLVector` class, and uses the
    functionality provided by ``GLVector``.


    In a similar manner to the :class:`.GLRGBVector`, the ``GLLineVector`` uses
    two OpenGL version-specific modules, the :mod:`.gl14.gllinevector_funcs`
    and :mod:`.gl21.gllinevector_funcs` modules. It is assumed that these
    modules define the same functions that are defined by the
    :class:`.GLRGBVector` version specific modules.

    
    A ``GLLineVector`` instance is rendered in different ways depending upon
    the rendering environment, so most of the rendering functionality is
    implemented in the version-specific modules mentioned above.
    """


    def __init__(self, image, display):
        """Create a ``GLLineVector`` instance.

        :arg image:   An :class:`.Image` or :class:`.TensorImage` instance.

        :arg display: The associated :class:`.Display` instance.
        """
        
        # If the overlay is a TensorImage, use the
        # V1 image is the vector data. Otherwise,
        # assume that the overlay is the vector image.
        if isinstance(image, tensorimage.TensorImage): vecImage = image.V1()
        else:                                          vecImage = image

        glvector.GLVector.__init__(self, image, display, vectorImage=vecImage)
        
        fslgl.gllinevector_funcs.init(self)

        def update(*a):
            self.notify()

        self.displayOpts.addListener('lineWidth',
                                     self.name,
                                     update,
                                     weak=False)
        self.vectorImage.addListener('data',
                                     self.name,
                                     update,
                                     weak=False) 

        
    def destroy(self):
        """Must be called when this ``GLLineVector`` is no longer needed.
        Removes some property listeners from the :class:`.LineVectorOpts`
        instance, calls the OpenGL version-specific ``destroy``
        function, and calls the :meth:`.GLVector.destroy` method.
        """ 
        self.displayOpts.removeListener('lineWidth', self.name)
        self.vectorImage.removeListener('data',      self.name)
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
        fslgl.gllinevector_funcs.updateShaderState(self)
 

    def preDraw(self):
        """Overrides :meth:`.GLVector.preDraw`. Calls the base class
        implementation, and then calls the OpenGL version-specific ``preDraw``
        function. 
        """ 
        glvector.GLVector.preDraw(self)
        fslgl.gllinevector_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        """Overrides :meth:`.GLObject.draw`. Calls the OpenGL version-specific
        ``draw`` function.
        """         
        fslgl.gllinevector_funcs.draw(self, zpos, xform)

    
    def drawAll(self, zposes, xforms):
        """Overrides :meth:`.GLObject.drawAll`. Calls the OpenGL
        version-specific ``drawAll`` function.
        """         
        fslgl.gllinevector_funcs.drawAll(self, zposes, xforms) 

    
    def postDraw(self):
        """Overrides :meth:`.GLVector.postDraw`. Calls the base class
        implementation, and then calls the OpenGL version-specific ``postDraw``
        function. 
        """         
        glvector.GLVector.postDraw(self)
        fslgl.gllinevector_funcs.postDraw(self) 


class GLLineVertices(object):
    """The ``GLLineVertices`` class is used in some cases when rendering a
    :class:`GLLineVector`. It contains logic to generate vertices for every
    vector in the vector :class:`.Image` that is being displayed by a
    ``GLLineVector`` instance.

    
    After a ``GLLineVertices`` instance has been created, the :meth:`refresh`
    method can be used to generate line vector vertices and texture
    coordinates for every voxel in the :class:`Image`. These vertices and
    coordinates are stored as attributes of the ``GLLineVertices`` instance.


    Later, when the line vectors from a 2D slice  of the image need to be
    displayed, the :meth:`getVertices` method can be used to extract the
    vertices and coordinates from the slice.


    A ``GLLineVertices`` instance is not associated with a specific
    ``GLLineVector`` instance. This is so that a single  ``GLLineVertices``
    instance can be shared between more than one ``GLLineVector``, avoiding
    the need to store multiple copies of the vertices and texture
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
        self.texCoords = None
        self.starts    = None
        self.steps     = None

        
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
        opts = glvec.displayOpts
        return (hash(opts.transform)  ^
                hash(opts.resolution) ^
                hash(opts.directed)) 

        
    def refresh(self, glvec):
        """(Re-)calculates the vertices and texture coordinates of this
        ``GLLineVertices`` instance.

        For each voxel, in the :class:`.Image` overlay being displayed by the
        :class:`GLLineVector` associated with this ``GLLineVertices``
        instance, two vertices are generated, which define a line that
        represents the vector at the voxel.

        Texture coordinates are also generated for every vertex, corresponding
        to the centre of the associated voxel.

        The vertices are stored as a :math:`X\\times Y\\times Z\\times
        2\\times 3` ``numpy`` array, as an attribute of this instance,
        called ``vertices``. The texture coordinates are stored as a
        ``numpy`` array of the same shape, as an attribute called
        ``texCoords``.

        .. note:: The vertex/texture coordinate generation takes into
                  account the current value of the
                  :attr:`.Nifti1Opts.resolution` property of the
                  :class:`.LineVectorOpts` instance; if this is set to
                  something other than the image resolution, the
                  sub-sampled starting indices and steps are stored
                  as attributes ``starts`` and ``steps`` respectively.
                  See the :func:`.routines.subsample` function for more
                  details.
        """

        opts  = glvec.displayOpts
        image = glvec.vectorImage

        # Extract a sub-sample of the vector image
        # at the current display resolution
        data, starts, steps = glroutines.subsample(image.data,
                                                   opts.resolution,
                                                   image.pixdim)

        # Pull out the xyz components of the 
        # vectors, and calculate vector lengths
        vertices = np.array(data, dtype=np.float32)
        x        = vertices[:, :, :, 0]
        y        = vertices[:, :, :, 1]
        z        = vertices[:, :, :, 2]
        lens     = np.sqrt(x ** 2 + y ** 2 + z ** 2)

        # scale the vector lengths to 0.5
        vertices[:, :, :, 0] = 0.5 * x / lens
        vertices[:, :, :, 1] = 0.5 * y / lens
        vertices[:, :, :, 2] = 0.5 * z / lens

        # Scale the vector data by the minimum
        # voxel length, so it is a unit vector
        # within real world space
        vertices /= (image.pixdim[:3] / min(image.pixdim[:3]))
        
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
            
        vertices = vertices.reshape((data.shape[0],
                                     data.shape[1],
                                     data.shape[2],
                                     2,
                                     3))

        # Offset each vertex by the corresponding
        # voxel coordinates, making sure to
        # transform from the sub-sampled indices
        # to the original data indices (offseting
        # and scaling by the starts and steps)
        for i in range(data.shape[0]):
            vertices[i, :, :, :, 0] += starts[0] + i * steps[0]
            
        for i in range(data.shape[1]):
            vertices[:, i, :, :, 1] += starts[1] + i * steps[1]
            
        for i in range(data.shape[2]):
            vertices[:, :, i, :, 2] += starts[2] + i * steps[2]

        texCoords = vertices.round()
        texCoords = (texCoords + 0.5) / np.array(image.shape[:3],
                                                 dtype=np.float32)

        self.vertices  = vertices
        self.texCoords = texCoords
        self.starts    = starts
        self.steps     = steps
        self.__hash    = self.calculateHash(glvec)
 

    def getVertices(self, zpos, glvec):
        """Extracts and returns a slice of line vertices, and the associated
        texture coordinates, which are in a plane located at the given
        Z position (in display coordinates).

        This method assumes that the :meth:`refresh` method has already been
        called.
        """

        opts  = glvec.displayOpts
        image = glvec.image
        xax   = glvec.xax
        yax   = glvec.yax
        zax   = glvec.zax

        vertices  = self.vertices
        texCoords = self.texCoords
        starts    = self.starts
        steps     = self.steps
        
        # If in id/pixdim space, the display
        # coordinate system axes are parallel
        # to the voxel coordinate system axes
        if opts.transform in ('id', 'pixdim'):

            # Turn the z position into a voxel index
            if opts.transform == 'pixdim':
                zpos = zpos / image.pixdim[zax]

            zpos = np.floor(zpos)

            # Return no vertices if the requested z
            # position is out of the image bounds
            if zpos < 0 or zpos >= image.shape[zax]:
                return (np.array([], dtype=np.float32),
                        np.array([], dtype=np.float32))

            # Extract a slice at the requested
            # z position from the vertex matrix
            coords      = [slice(None)] * 3
            coords[zax] = np.floor((zpos - starts[zax]) / steps[zax])

        # If in affine space, the display
        # coordinate system axes may not
        # be parallel to the voxel
        # coordinate system axes
        else:
            # Create a coordinate grid through
            # a plane at the requested z pos 
            # in the display coordinate system
            coords = glroutines.calculateSamplePoints(
                image.shape[ :3],
                [opts.resolution] * 3,
                opts.getTransform('voxel', 'display'),
                xax,
                yax)[0]
            
            coords[:, zax] = zpos

            # transform that plane of display
            # coordinates into voxel coordinates
            coords = transform.transform(
                coords, opts.getTransform('display', 'voxel'))

            # The voxel vertex matrix may have
            # been sub-sampled (see the
            # refresh method), so we need to
            # transform the image data voxel
            # coordinates to the sub-sampled
            # data voxel coordinates.
            coords = (coords - starts) / steps
            
            # remove any out-of-bounds voxel coordinates
            shape  = vertices.shape[:3]
            coords = np.array(coords.round(), dtype=np.int32)
            coords = coords[((coords >= [0, 0, 0]) &
                             (coords <  shape)).all(1), :].T

        # pull out the vertex data, and the
        # corresponding texture coordinates
        vertices  = vertices[ coords[0], coords[1], coords[2], :, :]
        texCoords = texCoords[coords[0], coords[1], coords[2], :, :]
        
        return vertices, texCoords
