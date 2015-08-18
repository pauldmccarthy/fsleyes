#!/usr/bin/env python
#
# gllinevector.py - Displays vector data as lines.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                   as np

import fsl.utils.transform     as transform
import fsl.fsleyes.gl          as fslgl
import fsl.fsleyes.gl.glvector as glvector
import fsl.fsleyes.gl.routines as glroutines


log = logging.getLogger(__name__)

class GLLineVertices(object):
    
    def __init__(self, glvec):
        
        self.__hash = None
        self.refresh(glvec)


    def destroy(self):
        self.vertices  = None
        self.texCoords = None
        self.starts    = None
        self.steps     = None

        
    def __hash__(self):
        return self.__hash

        
    def refresh(self, glvec):

        opts  = glvec.displayOpts
        image = glvec.image

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
        self.__hash    = (hash(opts.transform)  ^
                          hash(opts.resolution) ^
                          hash(opts.directed))
 

    def getVertices(self, glvec, zpos):

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
        # to the voxeld coordinate system axes
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
            # generateLineVertices method),
            # so we need to transform the image
            # data voxel coordinates to the
            # sub-sampled data voxel coordinates.
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


class GLLineVector(glvector.GLVector):


    def __init__(self, image, display):
        
        glvector.GLVector.__init__(self, image, display)
        
        fslgl.gllinevector_funcs.init(self)

        def update(*a):
            self.onUpdate()

        self.displayOpts.addListener(
            'lineWidth', self.name, update, weak=False)

        
    def destroy(self):
        
        self.displayOpts.removeListener('lineWidth', self.name)
        fslgl.gllinevector_funcs.destroy(self)
        glvector.GLVector.destroy(self)


    def getDataResolution(self, xax, yax):

        res       = list(glvector.GLVector.getDataResolution(self, xax, yax))
        res[xax] *= 16
        res[yax] *= 16
        
        return res


    def compileShaders(self):
        fslgl.gllinevector_funcs.compileShaders(self)
        

    def updateShaderState(self):
        fslgl.gllinevector_funcs.updateShaderState(self)
 

    def preDraw(self):
        glvector.GLVector.preDraw(self)
        fslgl.gllinevector_funcs.preDraw(self)


    def draw(self, zpos, xform=None):
        fslgl.gllinevector_funcs.draw(self, zpos, xform)

    
    def drawAll(self, zposes, xforms):
        fslgl.gllinevector_funcs.drawAll(self, zposes, xforms) 

    
    def postDraw(self):
        glvector.GLVector.postDraw(self)
        fslgl.gllinevector_funcs.postDraw(self) 
