#!/usr/bin/env python
#
# program.py - The GLSLShader class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLSLShader` class, which encapsulates
a GLSL shader program comprising a vertex shader and a fragment shader.
"""


import logging

import numpy                          as np
import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.instanced_arrays as arbia

import fsl.utils.memoize as memoize
from . import               parse


log = logging.getLogger(__name__)


GLSL_ATTRIBUTE_TYPES = {
    'bool'          : (gl.GL_BOOL,  1),
    'int'           : (gl.GL_INT,   1),
    'float'         : (gl.GL_FLOAT, 1),
    'vec2'          : (gl.GL_FLOAT, 2),
    'vec3'          : (gl.GL_FLOAT, 3),
    'vec4'          : (gl.GL_FLOAT, 3)
}
"""This dictionary contains mappings between GLSL data types, and their
corresponding GL types and sizes.
"""


class GLSLShader(object):
    """The ``GLSLShader`` class encapsulates information and logic about
    a GLSL 1.20 shader program, comprising a vertex shader and a fragment
    shader. It provides methods to set shader attribute and uniform values,
    to configure attributes, and to load/unload the program. Furthermore,
    the ``GLSLShader`` makes sure that all uniform and attribute variables
    are converted to the appropriate type. The following methods are available
    on a ``GLSLShader``:


    .. autosummary::
       :nosignatures:

       load
       unload
       destroy
       loadAtts
       unloadAtts
       set
       setAtt
       setIndices


    Typical usage of a ``GLSLShader`` will look something like the
    following::

        vertSrc = 'vertex shader source'
        fragSrc = 'fragment shader source'

        program = GLSLShader(vertSrc, fragSrc)

        # Load the program
        program.load()

        # Set some uniform values
        program.set('lighting', True)
        program.set('lightPos', [0, 0, -1])

        # Create and set vertex attributes
        vertices, normals = createVertices()

        program.setAtt('vertex', vertices)
        program.setAtt('normal', normals)

        # Load the attributes
        program.loadAtts()

        # Draw the scene
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(vertices))

        # Clear the GL state
        program.unload()
        program.unloadAtts()


        # Delete the program when
        # we no longer need it
        program.destroy()
    """


    def __init__(self, vertSrc, fragSrc, indexed=False):
        """Create a ``GLSLShader``.

        :arg vertSrc: String containing vertex shader source code.

        :arg fragSrc: String containing fragment shader source code.

        :arg indexed: If ``True``, it is assumed that the vertices processed
                      by this shader program will be drawn using an index
                      array.  A vertex buffer object is created to store
                      vertex indices - this buffer is expected to be populated
                      via the :meth:`setIndices` method.
        """

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

        self.vertUniforms    = vuNames
        self.vertAttributes  = vaNames
        self.fragUniforms    = fuNames

        self.vertAttDivisors = {}

        self.types     = allTypes
        self.positions = self.__getPositions(self.program,
                                             self.vertAttributes,
                                             self.vertUniforms,
                                             self.fragUniforms)

        # Buffers for vertex attributes
        self.buffers = {}

        for att in self.vertAttributes:
            self.buffers[att] = gl.glGenBuffers(1)

        if indexed: self.indexBuffer = gl.glGenBuffers(1)
        else:       self.indexBuffer = None

        log.memory('{}.init({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message. """
        if log:
            log.memory('{}.del({})'.format(type(self).__name__, id(self)))


    def load(self):
        """Loads this ``GLSLShader`` into the GL state.
        """
        gl.glUseProgram(self.program)


    def loadAtts(self):
        """Binds all of the shader program ``attribute`` variables - you
        must set the data for each attribute via :meth:`setAtt` before
        calling this method.
        """
        for att in self.vertAttributes:

            aPos           = self.positions[          att]
            aType          = self.types[              att]
            aBuf           = self.buffers[            att]
            aDivisor       = self.vertAttDivisors.get(att)
            glType, glSize = GLSL_ATTRIBUTE_TYPES[aType]

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, aBuf)
            gl.glEnableVertexAttribArray(aPos)
            gl.glVertexAttribPointer(    aPos,
                                         glSize,
                                         glType,
                                         gl.GL_FALSE,
                                         0,
                                         None)

            if aDivisor is not None:
                arbia.glVertexAttribDivisorARB(aPos, aDivisor)

        if self.indexBuffer is not None:
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)


    def unloadAtts(self):
        """Disables all vertex attributes, and unbinds associated vertex buffers.
        """
        for att in self.vertAttributes:
            gl.glDisableVertexAttribArray(self.positions[att])

            pos     = self.positions[          att]
            divisor = self.vertAttDivisors.get(att)

            if divisor is not None:
                arbia.glVertexAttribDivisorARB(pos, 0)

        if self.indexBuffer is not None:
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)


    def unload(self):
        """Unloads the GL shader program. """
        gl.glUseProgram(0)


    def destroy(self):
        """Deletes all GL resources managed by this ``GLSLShader``. """
        gl.glDeleteProgram(self.program)

        for buf in self.buffers.values():
            gl.glDeleteBuffers(1, gltypes.GLuint(buf))
        self.program = None


    @memoize.Instanceify(memoize.skipUnchanged)
    def set(self, name, value):
        """Sets the value for the specified GLSL ``uniform`` variable.

        The ``GLSLShader`` keeps a copy of the value of every uniform, to
        avoid unnecessary GL calls.


        .. note:: This method is decorated by the
                  :func:`.memoize.skipUnchanged` decorator, which returns
                  ``True`` if the value was changed, ``False`` otherwise.
        """

        vPos  = self.positions[name]
        vType = self.types[    name]

        setfunc = getattr(self, '_uniform_{}'.format(vType), None)

        if setfunc is None:
            raise RuntimeError('Unsupported shader program '
                               'type: {}'.format(vType))

        log.debug('Setting shader variable: {}({}) = {}'.format(
            vType, name, value))

        setfunc(vPos, value)


    def setAtt(self, name, value, divisor=None):
        """Sets the value for the specified GLSL ``attribute`` variable.

        :arg divisor: If specified, this value is used as a divisor for this
                      attribute via the ``glVetexAttribDivisor`` function.

        .. note:: If a ``divisor`` is specified, the OpenGL
                  ``ARB_instanced_arrays`` extension must be
                  available.
        """

        aType    = self.types[  name]
        aBuf     = self.buffers[name]

        castfunc = getattr(self, '_attribute_{}'.format(aType), None)

        if castfunc is None:
            raise RuntimeError('Unsupported shader program '
                               'type: {}'.format(aType))

        value = castfunc(value)

        log.debug('Setting shader attribute: {}({}): {}'.format(
            aType, name, value.shape))

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, aBuf)
        gl.glBufferData(gl.GL_ARRAY_BUFFER,
                        value.nbytes,
                        value,
                        gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

        if divisor is not None:
            self.vertAttDivisors[name] = divisor


    def setIndices(self, indices):
        """If an index array is to be used by this ``GLSLShader`` (see the
        ``indexed`` argument to :meth:`__init__`), the index array may be set
        via this method.
        """

        if self.indexBuffer is None:
            raise RuntimeError('Shader program was not '
                               'configured with index support')

        indices = np.array(indices, dtype=np.uint32)

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER,
                        self.indexBuffer)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                        indices.nbytes,
                        indices,
                        gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)


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
        gl.glUniform2fv(pos, 1, np.array(val, dtype=np.float32))


    def _uniform_vec3(self, pos, val):
        gl.glUniform3fv(pos, 1, np.array(val, dtype=np.float32))


    def _uniform_vec4(self, pos, val):
        gl.glUniform4fv(pos, 1, np.array(val, dtype=np.float32))


    def _uniform_mat2(self, pos, val):
        val = np.array(val, dtype=np.float32).ravel('F')
        gl.glUniformMatrix2fv(pos, 1, False, val)


    def _uniform_mat3(self, pos, val):
        val = np.array(val, dtype=np.float32).ravel('F')
        gl.glUniformMatrix3fv(pos, 1, False, val)


    def _uniform_mat4(self, pos, val):
        val = np.array(val, dtype=np.float32).ravel('F')
        gl.glUniformMatrix4fv(pos, 1, False, val)


    def _uniform_sampler1D(self, pos, val):
        gl.glUniform1i(pos, val)


    def _uniform_sampler2D(self, pos, val):
        gl.glUniform1i(pos, val)


    def _uniform_sampler3D(self, pos, val):
        gl.glUniform1i(pos, val)
