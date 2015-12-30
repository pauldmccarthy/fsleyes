#!/usr/bin/env python
#
# glvector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp
import OpenGL.raw.GL._types           as gltypes

import fsl.fsleyes.gl.shaders         as shaders


def destroy(self):
    """Destroys the vertex/fragment shader programs created in :func:`init`.
    """ 
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))
    self.vertexProgram   = None
    self.fragmentProgram = None

    
def compileShaders(self, vertShader):
    """Compiles the vertex/fragment shader programs used for drawing
    :class:`.GLRGBVector` instances. Stores references to the shader
    programs on the ``GLRGBVector`` instance. 
    """
    if self.vertexProgram is not None:
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        
    if self.fragmentProgram is not None:
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 

    vertShaderSrc = shaders.getVertexShader(  vertShader)
    fragShaderSrc = shaders.getFragmentShader('glvector')

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram        


def updateFragmentShaderState(self):

    opts = self.displayOpts
    
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    voxValXform     = self.imageTexture.voxValXform
    invClipValXform = self.clipTexture.invVoxValXform

    cmapXform       = self.xColourTexture.getCoordinateTransform()
    shape           = list(self.vectorImage.shape[:3])
    clippingRange   = opts.clippingRange
    
    if opts.clipImage is not None:
        clipLow  = clippingRange[0] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
        clipHigh = clippingRange[1] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
    else:
        clipLow  = 0
        clipHigh = 1

    shaders.setFragmentProgramMatrix(0, voxValXform)
    shaders.setFragmentProgramMatrix(4, cmapXform)
    shaders.setFragmentProgramVector(8, shape + [0])
    shaders.setFragmentProgramVector(9, [clipLow, clipHigh, 0, 0])
    
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)    
