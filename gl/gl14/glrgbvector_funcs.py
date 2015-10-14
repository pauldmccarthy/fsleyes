#!/usr/bin/env python
#
# glrgbvector_funcs.py - OpenGL 1.4 functions used by the GLRGBVector class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLRGBVector`
class to render :class:`.Image` overlays as RGB vector images in an OpenGL 1.4
compatible manner.


Rendering of a ``GLRGBVector`` is very similar to that of a
:class:`.GLVolume`; therefore, the ``preDraw``, ``draw``, ``drawAll`` and
``postDraw`` functions defined in the :mod:`.gl14.glvolume_funcs` are re-used
by this module.
"""


import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp
import OpenGL.raw.GL._types           as gltypes

import                           glvolume_funcs
import fsl.fsleyes.gl.shaders as shaders


def init(self):
    """Calls the :func:`compileShaders` and :func:`updateShaderState`
    functions.
    """
    
    self.vertexProgram   = None
    self.fragmentProgram = None
    
    compileShaders(   self)
    updateShaderState(self)


def destroy(self):
    """Destroys the vertex/fragment shader programs created in :func:`init`.
    """ 
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 

    
def compileShaders(self):
    """Compiles the vertex/fragment shader programs used for drawing
    :class:`.GLRGBVector` instances. Stores references to the shader
    programs on the ``GLRGBVector`` instance. 
    """
    if self.vertexProgram is not None:
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        
    if self.fragmentProgram is not None:
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 

    vertShaderSrc = shaders.getVertexShader(  self,
                                              sw=self.display.softwareMode)
    fragShaderSrc = shaders.getFragmentShader(self,
                                              sw=self.display.softwareMode)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram        


def updateShaderState(self):
    """Updates all variables used by the vertex/fragment shader programs. """

    opts = self.displayOpts
    
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    voxValXform  = self.imageTexture.voxValXform
    cmapXform    = self.xColourTexture.getCoordinateTransform()
    shape        = list(self.image.shape[:3]) + [0]
    modThreshold = [opts.modThreshold / 100.0, 0.0, 0.0, 0.0]

    shaders.setFragmentProgramMatrix(0, voxValXform)
    shaders.setFragmentProgramMatrix(4, cmapXform)
    shaders.setFragmentProgramVector(8, shape + [0])
    shaders.setFragmentProgramVector(9, modThreshold)
    
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)


preDraw  = glvolume_funcs.preDraw
draw     = glvolume_funcs.draw
drawAll  = glvolume_funcs.drawAll
postDraw = glvolume_funcs.postDraw
