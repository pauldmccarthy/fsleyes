#!/usr/bin/env python
#
# program.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp


log = logging.getLogger(__name__)


class ARBPShader(object):
    
    def __init__(self,
                 vertSrc,
                 fragSrc,
                 paramMap=None,
                 textureMap=None,
                 vertAttMap=None):

        self.__vertexProgram   = None
        self.__fragmentProgram = None

        if textureMap is None: textureMap = {}
        if paramMap   is None: paramMap   = {}
        if vertAttMap is None: vertAttMap = {}


    def delete(self):
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.__vertexProgram))
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.__fragmentProgram)) 


    def __compile(self, vertSrc, fragSrc):
        """Compiles the vertex and fragment programs and returns references
        to the compiled programs.
        """

        gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
        gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        fragProg = arbfp.glGenProgramsARB(1)
        vertProg = arbvp.glGenProgramsARB(1) 

        # vertex program
        try:
            arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB, vertProg)
            arbvp.glProgramStringARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                                     arbvp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                     len(vertSrc),
                                     vertSrc)

        except:

            position = gl.glGetIntegerv(arbvp.GL_PROGRAM_ERROR_POSITION_ARB)
            message  = gl.glGetString(  arbvp.GL_PROGRAM_ERROR_STRING_ARB)

            raise RuntimeError('Error compiling vertex program '
                               '({}): {}'.format(position, message)) 

        # fragment program
        try:
            arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                   fragProg)

            arbfp.glProgramStringARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                     arbfp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                     len(fragSrc),
                                     fragSrc)
        except:
            position = gl.glGetIntegerv(arbfp.GL_PROGRAM_ERROR_POSITION_ARB)
            message  = gl.glGetString(  arbfp.GL_PROGRAM_ERROR_STRING_ARB)

            raise RuntimeError('Error compiling fragment program '
                               '({}): {}'.format(position, message))

        gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
        gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        return vertProg, fragProg
