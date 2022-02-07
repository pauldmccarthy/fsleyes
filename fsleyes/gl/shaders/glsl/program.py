#!/usr/bin/env python
#
# program.py - The GLSLShader class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLSLShader` class, which encapsulates
a GLSL shader program comprising a vertex shader, a fragment shader, and
optionally a geometry shader (for OpenGL >= 3.3).
"""


import logging
import contextlib

import jinja2                as j2
import numpy                 as np
import OpenGL.GL             as gl
import OpenGL.raw.GL._types  as gltypes

import fsleyes.gl.extensions as glexts
import fsleyes.gl            as fslgl
import fsl.utils.memoize     as memoize
from . import                   parse


log = logging.getLogger(__name__)


GLSL_ATTRIBUTE_TYPES = {
    'bool'  : (gl.GL_BOOL,  1),
    'int'   : (gl.GL_INT,   1),
    'float' : (gl.GL_FLOAT, 1),
    'vec2'  : (gl.GL_FLOAT, 2),
    'vec3'  : (gl.GL_FLOAT, 3),
    'vec4'  : (gl.GL_FLOAT, 4)
}
"""This dictionary contains mappings between GLSL data types, and their
corresponding GL types and sizes.
"""


class GLSLShader:
    """The ``GLSLShader`` class encapsulates information and logic about a GLSL
    shader program, comprising a vertex shader, a fragment shader, and
    optionally a geometry shader (if OpenGL >= 3.3 is available). It provides
    methods to set shader attribute and uniform values, to configure
    attributes, and to load/unload the program. Furthermore, the
    ``GLSLShader`` makes sure that all uniform and attribute variables are
    converted to the appropriate type. The following methods are available on
    a ``GLSLShader``:


    .. autosummary::
       :nosignatures:

       load
       unload
       loaded
       destroy
       set
       setAtt
       setIndices
       draw


    Typical usage of a ``GLSLShader`` will look something like the
    following::

        vertSrc = 'vertex shader source'
        fragSrc = 'fragment shader source'

        program = GLSLShader(vertSrc, fragSrc)

        # Load the program
        with shader.loaded():

            # Set some uniform values
            program.set('lighting', True)
            program.set('lightPos', [0, 0, -1])

            # Create and set vertex attributes
            vertices, normals = createVertices()

            program.setAtt('vertex', vertices)
            program.setAtt('normal', normals)

            # Draw the scene
            program.draw(gl.GL_TRIANGLES, len(vertices))

        # Delete the program when
        # we no longer need it
        program.destroy()
    """


    def __init__(self,
                 vertSrc,
                 fragSrc,
                 geomSrc=None,
                 constants=None):
        """Create a ``GLSLShader``.

        The source is passed through ``jinja2``, replacing any expressions on
        the basis of ``constants``.

        :arg vertSrc:   String containing vertex shader source code.

        :arg fragSrc:   String containing fragment shader source code.

        :arg geomSrc:   String containing geometry shader source code.

        :arg constants: Key-value pairs to be used when passing the source
                        through ``jinja2``.
        """

        if constants is None:
            constants = {}

        vertSrc = j2.Template(vertSrc).render(**constants)
        fragSrc = j2.Template(fragSrc).render(**constants)
        if geomSrc is not None:
            geomSrc = j2.Template(geomSrc).render(**constants)

        self.program = self.__compile(vertSrc, fragSrc, geomSrc)

        vertDecs  = parse.parseGLSL(vertSrc)
        fragDecs  = parse.parseGLSL(fragSrc)
        vertUnifs = vertDecs['uniform']
        vertAtts  = vertDecs['attribute']
        fragUnifs = fragDecs['uniform']

        if len(vertUnifs)  > 0: vuNames, vuTypes, vuSizes = zip(*vertUnifs)
        else:                   vuNames, vuTypes, vuSizes = [], [], []
        if len(vertAtts)  > 0:  vaNames, vaTypes, vaSizes = zip(*vertAtts)
        else:                   vaNames, vaTypes, vaSizes = [], [], []
        if len(fragUnifs) > 0:  fuNames, fuTypes, fuSizes = zip(*fragUnifs)
        else:                   fuNames, fuTypes, fuSizes = [], [], []

        allTypes = {}
        allSizes = {}

        for n, t in zip(vuNames, vuTypes): allTypes[n] = t
        for n, t in zip(vaNames, vaTypes): allTypes[n] = t
        for n, t in zip(fuNames, fuTypes): allTypes[n] = t
        for n, s in zip(vuNames, vuSizes): allSizes[n] = s
        for n, s in zip(vaNames, vaSizes): allSizes[n] = s
        for n, s in zip(fuNames, fuSizes): allSizes[n] = s

        # Remove duplicate uniform definitions
        # between the vertex/fragment shader -
        # they only need to be set once.
        vertUnifs = [vu for vu in vertUnifs if vu not in fragUnifs]

        self.vertUniforms    = vuNames
        self.vertAttributes  = vaNames
        self.fragUniforms    = fuNames

        self.vertAttDivisors = {}

        self.types     = allTypes
        self.sizes     = allSizes
        self.positions = self.__getPositions(self.program,
                                             self.vertAttributes,
                                             self.vertUniforms,
                                             self.fragUniforms)

        # Buffers for vertex attributes
        self.buffers = {}

        for att in self.vertAttributes:
            self.buffers[att] = gl.glGenBuffers(1)

        # Buffers for storing vertices and
        # (optionally) vertex indices.
        # A vertex array is required in
        # GL >= 3.0, but not supported in
        # older GL versions.
        #
        # A vertex index buffer is created
        # on the first call to  setIndices.
        if float(fslgl.GL_COMPATIBILITY) >= 3: self.vao = gl.glGenVertexArrays(1)
        else:                                  self.vao = None
        self.indexBuffer = None
        self.nindices    = None

        # The loadAtts/unloadAtts methods add
        # to this counter to allow re-entrance
        # (so we don't try to load/unload more
        # than once).
        self.attsLoaded = 0

        log.debug('{}.init({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message. """
        if log:
            log.debug('{}.del({})'.format(type(self).__name__, id(self)))


    @contextlib.contextmanager
    def loaded(self):
        """Context manager which calls :meth:`load`, yields, then
        calls :meth:`unload`.
        """
        self.load()
        try:
            yield
        finally:
            self.unload()


    @contextlib.contextmanager
    def loadedAtts(self):
        """Context manager which calls :meth:`loadAtts`, yields, then
        calls :meth:`unloadAtts`.

        This is called automatically by :meth:`draw`, so there is no need
        to explicitly call it.
        """
        self.loadAtts()
        try:
            yield
        finally:
            self.unloadAtts()


    def load(self):
        """Loads this ``GLSLShader`` into the GL state. """
        gl.glUseProgram(self.program)


    def loadAtts(self):
        """Binds all of the shader program ``attribute`` variables - you
        must set the data for each attribute via :meth:`setAtt` before
        calling this method.

        This is called automatically by :meth:`draw`, so there is no need
        to explicitly call it.

        Attributes may be set before or after this method is called.
        """
        self.attsLoaded += 1
        if self.attsLoaded > 1:
            return
        if self.vao is not None:
            gl.glBindVertexArray(self.vao)
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
                glexts.glVertexAttribDivisor(aPos, aDivisor)

        if self.indexBuffer is not None:
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)


    def unloadAtts(self):
        """Disables all vertex attributes, and unbinds associated vertex buffers.
        This is called automatically by :meth:`draw`, so there is no need
        to explicitly call it.
        """
        self.attsLoaded -= 1
        if self.attsLoaded > 0:
            return
        for att in self.vertAttributes:
            gl.glDisableVertexAttribArray(self.positions[att])

            pos     = self.positions[          att]
            divisor = self.vertAttDivisors.get(att)

            if divisor is not None:
                glexts.glVertexAttribDivisor(pos, 0)

        if self.indexBuffer is not None:
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
        if self.vao is not None:
            gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)


    def unload(self):
        """Unloads the GL shader program. """
        gl.glUseProgram(0)


    def destroy(self):
        """Deletes all GL resources managed by this ``GLSLShader``. """
        gl.glDeleteProgram(self.program)
        if self.vao is not None:
            gl.glDeleteVertexArrays(1, self.vao)
        if self.indexBuffer is not None:
            gl.glDeleteBuffers(1, self.indexBuffer)
        for buf in self.buffers.values():
            gl.glDeleteBuffers(1, gltypes.GLuint(buf))

        self.program     = None
        self.vao         = None
        self.indexBuffer = None
        self.buffers     = None


    @memoize.Instanceify(memoize.skipUnchanged)
    def set(self, name, value, size=None):
        """Sets the value for the specified GLSL ``uniform`` variable.

        The ``GLSLShader`` keeps a copy of the value of every uniform, to
        avoid unnecessary GL calls.


        .. note:: This method is decorated by the
                  :func:`.memoize.skipUnchanged` decorator, which returns
                  ``True`` if the value was changed, ``False`` otherwise.
        """

        vPos  = self.positions[name]
        vType = self.types[    name]
        vSize = self.sizes[    name]

        if size is None:
            size = 1

        setfunc = getattr(self, '_uniform_{}'.format(vType), None)

        if size > vSize:
            raise RuntimeError('Specified size ({}) is greater than '
                               'uniform size {} ({})'.format(
                                   size, name, vSize))

        if setfunc is None:
            raise RuntimeError('Unsupported shader program '
                               'type: {}'.format(vType))

        log.debug('Setting shader variable: {}({})[{}] = {}'.format(
            vType, size, name, value))

        setfunc(vPos, value, size)


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
        """If an index array is to be used by this ``GLSLShader``, the index
        array may be set via this method.
        """

        if indices is None:
            if self.indexBuffer is not None:
                gl.glDeleteBuffers(1, self.indexBuffer)
            self.indexBuffer = None
            self.nindices    = None
            return

        if self.indexBuffer is None:
            self.indexBuffer = gl.glGenBuffers(1)

        self.nindices = indices.size

        indices = np.asarray(indices, dtype=np.uint32)

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER,
                        self.indexBuffer)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                        indices.nbytes,
                        indices,
                        gl.GL_STATIC_DRAW)

        # Don't unbind if loadAtts is active.
        # This allows setIndices to be called
        # either before or after loadAtts.
        if not self.attsLoaded:
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)


    def draw(self, prim, *args):
        """Submits a GL draw call for the specified primitive type.
        If vertex indices have been provided via the :meth:`setIndices` method,
        ``glDrawElements`` is used, and all other arguments are ignored.
        Otherwise, ``glDrawArrays`` is used, and is passed all other arguments.
        """

        with self.loadedAtts():
            if self.indexBuffer is not None:
                gl.glDrawElements(prim,
                                  self.nindices,
                                  gl.GL_UNSIGNED_INT,
                                  None)
            else:
                gl.glDrawArrays(prim, *args)


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


    def __compile(self, vertShaderSrc, fragShaderSrc, geomShaderSrc=None):
        """Compiles and links the OpenGL GLSL vertex, fragment, and optionally
        geometry shader programs, and returns a reference to the resulting
        program. Raises an error if compilation/linking fails.

        .. note:: I'm explicitly not using the PyOpenGL
                  :func:`OpenGL.GL.shaders.compileProgram` function, because
                  it attempts to validate the program after compilation, which
                  fails due to texture data not being bound at the time of
                  validation.
        """

        program = gl.glCreateProgram()
        srcs     = [(vertShaderSrc, gl.GL_VERTEX_SHADER),
                    (fragShaderSrc, gl.GL_FRAGMENT_SHADER),
                    (geomShaderSrc, gl.GL_GEOMETRY_SHADER)]

        for src, srcType in srcs:
            if src is None:
                continue

            shader = gl.glCreateShader(srcType)
            gl.glShaderSource(shader, src)
            gl.glCompileShader(shader)
            result = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
            if result != gl.GL_TRUE:
                raise RuntimeError(gl.glGetShaderInfoLog(shader))
            gl.glAttachShader(program, shader)
            gl.glDeleteShader(shader)

        gl.glLinkProgram(program)
        linkResult = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)

        if linkResult != gl.GL_TRUE:
            raise RuntimeError(gl.glGetProgramInfoLog(program))

        return program


    def _attribute_bool(self, val):
        return np.array(val, dtype=np.bool, copy=False)


    def _attribute_int(self, val):
        return np.array(val, dtype=np.int32, copy=False)


    def _attribute_float(self, val):
        return np.array(val, dtype=np.float32, copy=False)


    def _attribute_vec2(self, val):
        return np.array(val, dtype=np.float32, copy=False).ravel('C')


    def _attribute_vec3(self, val):
        return np.array(val, dtype=np.float32, copy=False).ravel('C')


    def _attribute_vec4(self, val):
        return np.array(val, dtype=np.float32, copy=False).ravel('C')


    def _uniform_bool(self, pos, val, size):
        val = np.array(val, dtype=np.int32)
        gl.glUniform1iv(pos, size, val)


    def _uniform_int(self, pos, val, size):
        val = np.array(val, dtype=np.int32)
        gl.glUniform1iv(pos, size, val)


    def _uniform_float(self, pos, val, size):
        val = np.array(val, dtype=np.float32)
        gl.glUniform1fv(pos, size, val)


    def _uniform_vec2(self, pos, val, size):
        val = np.array(val, dtype=np.float32, copy=False).ravel('C')
        gl.glUniform2fv(pos, size, val)


    def _uniform_vec3(self, pos, val, size):
        val = np.array(val, dtype=np.float32, copy=False).ravel('C')
        gl.glUniform3fv(pos, size, val)


    def _uniform_vec4(self, pos, val, size):
        val = np.array(val, dtype=np.float32, copy=False).ravel('C')
        gl.glUniform4fv(pos, size, val)


    def _uniform_mat2(self, pos, val, size):
        val = np.array(val, dtype=np.float32, copy=False).ravel('C')
        gl.glUniformMatrix2fv(pos, size, True, val)


    def _uniform_mat3(self, pos, val, size):
        val = np.array(val, dtype=np.float32, copy=False).ravel('C')
        gl.glUniformMatrix3fv(pos, size, True, val)


    def _uniform_mat4(self, pos, val, size):
        val = np.array(val, dtype=np.float32, copy=False).ravel('C')
        gl.glUniformMatrix4fv(pos, 1, True, val)


    def _uniform_sampler1D(self, pos, val, size):
        val = np.array(val, dtype=np.int32, copy=False).ravel('C')
        gl.glUniform1iv(pos, size, val)


    def _uniform_sampler2D(self, pos, val, size):
        val = np.array(val, dtype=np.int32, copy=False).ravel('C')
        gl.glUniform1iv(pos, size, val)


    def _uniform_sampler3D(self, pos, val, size):
        val = np.array(val, dtype=np.int32, copy=False).ravel('C')
        gl.glUniform1iv(pos, size, val)
