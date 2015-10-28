#!/usr/bin/env python
#
# glmodel_funcs.py - OpenGL 1.4 functions used by the GLModel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions which are used by the :class:`.GLModel`
class to render :class:`.Model` overlays in an OpenGL 1.4 compatible manner.
"""


import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.fsleyes.gl.shaders         as shaders


def compileShaders(self):
    """Compiles vertex and fragment shader programs for the given
    :class:`.GLModel` instance. The shaders are added as attributes of the
    instance.
    """
    
    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram    


def destroy(self):
    """Deletes the vertex/fragment shader programs that were compiled by
    :func:`compileShaders`.
    """    
    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram)) 


def updateShaders(self):
    """Updates the state of the vertex/fragment shaders. This involves
    setting the parameter values used by the shaders.
    """ 
    offsets = self.getOutlineOffsets()
    
    loadShaders(self)
    shaders.setFragmentProgramVector(0, list(offsets) + [0, 0])
    unloadShaders(self)


def loadShaders(self):
    """Loads the :class:`.GLModel` vertex/fragment shader programs. """
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)    


def unloadShaders(self):
    """Un-loads the :class:`.GLModel` vertex/fragment shader programs. """
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)     
