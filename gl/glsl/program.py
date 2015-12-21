#!/usr/bin/env python
#
# program.py - Class which encapsulates a GLSL shader program.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides he :class:`ShaderProgram` class, which encapsulates
a GLSL shader program comprising a vertex shader and a fragment shader.
"""


import logging

import numpy                as np
import OpenGL.GL            as gl
import OpenGL.raw.GL._types as gltypes

import parse


log = logging.getLogger(__name__)


GLSL_ATTRIBUTE_TYPES = {
    'bool'          : (gl.GL_BOOL,  1),
    'int'           : (gl.GL_INT,   1),
    'float'         : (gl.GL_FLOAT, 1),
    'vec2'          : (gl.GL_FLOAT, 2),
    'vec3'          : (gl.GL_FLOAT, 3),
    'vec4'          : (gl.GL_FLOAT, 3)
}


class ShaderProgram(object):

    def __init__(self, vertSrc, fragSrc):

        self.program     = self.__compile(vertSrc, fragSrc)
        
        vertDecs         = parse.parseGLSL(vertSrc)
        fragDecs         = parse.parseGLSL(fragSrc)

        vertUnifs = vertDecs['uniform']
        vertAtts  = vertDecs['attribute']
        fragUnifs = fragDecs['uniform']

        if len(vertUnifs)  > 0: vuNames, vuTypes = zip(*vertUnifs)
        else:                   vuNames, vuTypes = [], []
        if len(vertAtts)  > 0:  vaNames, vaTypes = zip(*vertAtts)
        else:                   vaNames, vaTypes = [], []
        if len(fragUnifs) > 0:  fuNames, fuTypes = zip(*fragUnifs)
        else:                   fuNames, fuTypes = [], []

        allTypes = {}

        for n, t in zip(vuNames, vuTypes): allTypes[n] = t
        for n, t in zip(vaNames, vaTypes): allTypes[n] = t
        for n, t in zip(fuNames, fuTypes): allTypes[n] = t

        # Remove duplicate uniform definitions
        # between the vertex/fragment shader -
        # they only need to be set once.
        vertUnifs = [vu for vu in vertUnifs if vu not in fragUnifs]

        self.vertUniforms   = vuNames
        self.vertAttributes = vaNames
        self.fragUniforms   = fuNames

        self.types     = allTypes
        self.positions = self.__getPositions(self.program,
                                             self.vertAttributes,
                                             self.vertUniforms,
                                             self.fragUniforms)

        self.buffers = {}

        for att in self.vertAttributes:
            self.buffers[att] = gl.glGenBuffers(1)

            
    def load(self):
        gl.glUseProgram(self.program)


    def loadAtts(self):
        for att in self.vertAttributes:
            gl.glEnableVertexAttribArray(self.positions[att])

            
    def unloadAtts(self):
        for att in self.vertAttributes:
            gl.glDisableVertexAttribArray(self.positions[att])
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

        
    def unload(self):
        gl.glUseProgram(0)


    def delete(self):
        gl.glDeleteProgram(self.program)

        for buf in self.buffers.values():
            gl.glDeleteBuffers(1, gltypes.GLuint(buf))
        self.program = None
        
        
    def set(self, name, value):

        vPos  = self.positions[name]
        vType = self.types[    name]

        setfunc = getattr(self, '_uniform_{}'.format(vType), None)

        if setfunc is None:
            raise RuntimeError('Unsupported shader program '
                               'type: {}'.format(vType))

        log.debug('Setting shader variable: {}({}) = {}'.format(
            vType, name, value))

        setfunc(vPos, value)


    def setAtt(self, name, value):

        aPos  = self.positions[name]
        aType = self.types[    name]
        aBuf  = self.buffers[  name]

        glType, glSize = GLSL_ATTRIBUTE_TYPES[aType]

        castfunc = getattr(self, '_attribute_{}'.format(aType), None)

        if castfunc is None:
            raise RuntimeError('Unsupported shader program '
                               'type: {}'.format(aType))

        value = castfunc(value)

        log.debug('Setting shader attribute: {}({}): {}'.format(
            aType, name, value.shape)) 

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, aBuf)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, value.nbytes, value, gl.GL_STATIC_DRAW)
        gl.glVertexAttribPointer(
            aPos, glSize, glType, gl.GL_FALSE, 0, None) 

        
    def __getPositions(self, shaders, vertAtts, vertUniforms, fragUniforms):
        """Gets the position indices for all vertex shader attributes,
        uniforms, and fragment shader uniforms for the given shader
        programs.

        :arg shaders:      Reference to the compiled shader program.
        :arg vertAtts:     List of attributes required by the vertex shader.
        :arg vertUniforms: List of uniforms required by the vertex shader.
        :arg fragUniforms: List of uniforms required by the fragment shader.

        :returns:  A dictionary of ``{name : position}`` mappings.
        """

        import OpenGL.GL as gl

        shaderVars = {}

        for v in vertUniforms:
            shaderVars[v] = gl.glGetUniformLocation(shaders, v)

        for v in vertAtts:
            shaderVars[v] = gl.glGetAttribLocation(shaders, v)

        for v in fragUniforms:
            if v in shaderVars:
                continue
            shaderVars[v] = gl.glGetUniformLocation(shaders, v)

        return shaderVars


    def __compile(self, vertShaderSrc, fragShaderSrc):
        """Compiles and links the OpenGL GLSL vertex and fragment shader
        programs, and returns a reference to the resulting program. Raises
        an error if compilation/linking fails.

        .. note:: I'm explicitly not using the PyOpenGL
                  :func:`OpenGL.GL.shaders.compileProgram` function, because
                  it attempts to validate the program after compilation, which
                  fails due to texture data not being bound at the time of
                  validation.
        """

        # vertex shader
        vertShader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertShader, vertShaderSrc)
        gl.glCompileShader(vertShader)
        vertResult = gl.glGetShaderiv(vertShader, gl.GL_COMPILE_STATUS)

        if vertResult != gl.GL_TRUE:
            raise RuntimeError('{}'.format(gl.glGetShaderInfoLog(vertShader)))

        # fragment shader
        fragShader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragShader, fragShaderSrc)
        gl.glCompileShader(fragShader)
        fragResult = gl.glGetShaderiv(fragShader, gl.GL_COMPILE_STATUS)

        if fragResult != gl.GL_TRUE:
            raise RuntimeError('{}'.format(gl.glGetShaderInfoLog(fragShader)))

        # link all of the shaders!
        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertShader)
        gl.glAttachShader(program, fragShader)

        gl.glLinkProgram(program)

        gl.glDeleteShader(vertShader)
        gl.glDeleteShader(fragShader)

        linkResult = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)

        if linkResult != gl.GL_TRUE:
            raise RuntimeError('{}'.format(gl.glGetProgramInfoLog(program)))

        return program

    
    def _attribute_bool(self, val):
        return np.array(val, dtype=np.bool)

    
    def _attribute_int(self, val):
        return np.array(val, dtype=np.int32)

    
    def _attribute_float(self, val):
        return np.array(val, dtype=np.float32)

    
    def _attribute_vec2(self, val):
        return np.array(val, dtype=np.float32).ravel('C')

    
    def _attribute_vec3(self, val):
        return np.array(val, dtype=np.float32).ravel('C')

    
    def _attribute_vec4(self, val):
        return np.array(val, dtype=np.float32).ravel('C')
    

    def _uniform_bool(self, pos, val):
        gl.glUniform1i(pos, bool(val))

        
    def _uniform_int(self, pos, val):
        gl.glUniform1i(pos, int(val))


    def _uniform_float(self, pos, val):
        gl.glUniform1f(pos, float(val))


    def _uniform_vec2(self, pos, val):
        gl.glUniform2fv(pos, np.array(val, dtype=np.float32))


    def _uniform_vec3(self, pos, val):
        gl.glUniform3fv(pos, 1, np.array(val, dtype=np.float32))


    def _uniform_vec4(self, pos, val):
        gl.glUniform4fv(pos, 1, np.array(val, dtype=np.float32))


    def _uniform_mat2(self, pos, val):
        val = np.array(val, dtype=np.float32).ravel('C')
        gl.glUniformMatrix2fv(pos, 1, False, val)


    def _uniform_mat3(self, pos, val):
        val = np.array(val, dtype=np.float32).ravel('C')
        gl.glUniformMatrix3fv(pos, 1, False, val)


    def _uniform_mat4(self, pos, val):
        val = np.array(val, dtype=np.float32).ravel('C')
        gl.glUniformMatrix4fv(pos, 1, False, val)


    def _uniform_sampler1D(self, pos, val):
        gl.glUniform1i(pos, val)


    def _uniform_sampler2D(self, pos, val):
        gl.glUniform1i(pos, val)


    def _uniform_sampler3D(self, pos, val):
        gl.glUniform1i(pos, val)
