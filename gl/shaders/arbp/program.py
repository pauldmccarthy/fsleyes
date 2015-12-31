#!/usr/bin/env python
#
# program.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                          as np

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import                                   parse


log = logging.getLogger(__name__)


class ARBPShader(object):
    
    def __init__(self, vertSrc, fragSrc, textureMap=None):

        decs = parse.parseARBP(vertSrc, fragSrc)

        vParams = decs['vertParam']
        fParams = decs['fragParam']

        if len(vParams) > 0: vParams, vLens = zip(*vParams)
        else:                vParams, vLens = [], []
        if len(fParams) > 0: fParams, fLens = zip(*fParams)
        else:                fParams, fLens = [], []

        vLens = {name : length for name, length in zip(vParams, vLens)}
        fLens = {name : length for name, length in zip(fParams, fLens)}

        self.vertParams    = vParams
        self.vertParamLens = vLens
        self.fragParams    = fParams
        self.fragParamLens = fLens
        self.textures      = decs['texture']
        self.attrs         = decs['attr']

        poses = self.__generatePositions(textureMap)
        vpPoses, fpPoses, texPoses, attrPoses = poses

        self.vertParamPositions = vpPoses
        self.fragParamPositions = fpPoses
        self.texturePositions   = texPoses
        self.attrPositions      = attrPoses

        vertSrc, fragSrc = parse.fillARBP(vertSrc,
                                          fragSrc,
                                          self.vertParamPositions,
                                          self.vertParamLens,
                                          self.fragParamPositions,
                                          self.fragParamLens,
                                          self.texturePositions,
                                          self.attrPositions)

        vp, fp = self.__compile(vertSrc, fragSrc)
        
        self.vertexProgram   = vp
        self.fragmentProgram = fp
        

    def delete(self):
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))


    def load(self):
        gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
        gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                               self.vertexProgram)
        arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                               self.fragmentProgram)

        for attr in self.attrs:
            texUnit = self.__getAttrTexUnit(attr)

            gl.glClientActiveTexture(texUnit)
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY) 


    def unload(self):
        gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
        gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)

        for attr in self.attrs:
            texUnit = self.__getAttrTexUnit(attr)

            gl.glClientActiveTexture(texUnit)
            gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)


    def setVertParam(self, name, value):

        pos   = self.vertParamPositions[name]
        value = np.array(value, dtype=np.float32).reshape((-1, 4))
        
        for i, row in enumerate(value):
            arbvp.glProgramLocalParameter4fARB(
                arbvp.GL_VERTEX_PROGRAM_ARB, pos + i,
                row[0], row[1], row[2], row[3]) 

    
    def setFragParam(self, name, value):

        pos   = self.fragParamPositions[name]
        value = np.array(value, dtype=np.float32).reshape((-1, 4))
    
        for i, row in enumerate(value):
            arbfp.glProgramLocalParameter4fARB(
                arbfp.GL_FRAGMENT_PROGRAM_ARB, pos + i,
                row[0], row[1], row[2], row[3]) 


    def setAttr(self, name, value):

        texUnit = self.__getAttrTexUnit(name)
        size    = value.shape[1]
        value   = np.array(value, dtype=np.float32)
        value   = value.ravel('C')
        
        gl.glClientActiveTexture(texUnit)
        gl.glTexCoordPointer(size, gl.GL_FLOAT, 0, value)


    def __getAttrTexUnit(self, attr):

        pos     = self.attrPositions[attr]
        texUnit = 'GL_TEXTURE{}'.format(pos)
        texUnit = getattr(gl, texUnit)

        return texUnit


    def __generatePositions(self, textureMap=None):

        vpPoses   = {}
        fpPoses   = {}
        texPoses  = {}
        attrPoses = {}

        # Vertex parameters
        pos = 0
        for name in self.vertParams:
            vpPoses[name]  = pos
            pos           += self.vertParamLens[name]

        # Fragment parameters
        pos = 0
        for name in self.fragParams:
            fpPoses[name]  = pos
            pos           += self.fragParamLens[name]

        # Vertex attributes
        for i, name in enumerate(self.attrs):
            attrPoses[name]  = i
            
        # Texture positions. If the caller did
        # not provide a texture map in __init__,
        # we'll generate some positions.
        if textureMap is None:

            names    = self.textures
            poses    = range(len(names))
            texPoses = {n : p for n, p in zip(names, poses)}
        else:
            texPoses = dict(textureMap)
        
        return vpPoses, fpPoses, texPoses, attrPoses


    def __compile(self, vertSrc, fragSrc):
        """Compiles the vertex and fragment programs and returns references
        to the compiled programs.
        """

        gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
        gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        fragProg = arbfp.glGenProgramsARB(1)
        vertProg = arbvp.glGenProgramsARB(1)

        # Make sure the source is plain
        # ASCII - not unicode
        vertSrc = str(vertSrc)
        fragSrc = str(fragSrc)

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
