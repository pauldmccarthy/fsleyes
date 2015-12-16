#!/usr/bin/env python
#
# shaders.py - Convenience functions for managing vertex/fragment shaders.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines convenience functions for managing vertex and fragment
shader source code.


The rendering code for some :class:`.GLObject` types use vertex and fragment
shader programs. These programs can be accessed and compiled with the 
following functions:


.. autosummary::
   :nosignatures:

   getVertexShader
   getFragmentShader
   compilePrograms
   compileShaders


Some functions are also provided for use with OpenGL 1.4, which make setting
program variables a bit less painful:


.. autosummary::
   :nosignatures:

   setVertexProgramVector
   setVertexProgramMatrix
   setFragmentProgramVector
   setFragmentProgramMatrix


**Shader program file locations**


All shader programs and associated files are assumed to be located in one of
the OpenGL version specific packages, i.e. :mod:`.gl14`
(``ARB_vertex_program``/``ARB_fragment_program`` shaders) or :mod:`.gl21`
(GLSL shaders).


**Preprocessing**


When a shader file is loaded, a simple preprocessor is applied to the source -
any lines of the form '#pragma include filename', will be replaced with the
contents of the specified file.


**Resources**


 - http://oss.sgi.com/projects/ogl-sample/registry/ARB/vertex_program.txt
 - http://oss.sgi.com/projects/ogl-sample/registry/ARB/fragment_program.txt
 - http://www.renderguild.com/gpuguide.pdf
 - https://www.opengl.org/registry/doc/GLSLangSpec.Full.1.20.8.pdf
"""


import logging

import os.path as op

import fsl.fsleyes.gl     as fslgl
import fsl.utils.typedict as td


log = logging.getLogger(__name__)


def setVertexProgramVector(index, vector):
    """Convenience function which sets the vertex program local parameter
    at the given index to the given 4 component vector.
    """
    import OpenGL.GL.ARB.vertex_program as arbvp
    
    arbvp.glProgramLocalParameter4fARB(
        arbvp.GL_VERTEX_PROGRAM_ARB, index, *vector) 


def setVertexProgramMatrix(index, matrix):
    """Convenience function which sets four vertex program local parameters,
    starting at the given index, to the given ``4*4`` matrix.
    """ 
    
    import OpenGL.GL.ARB.vertex_program as arbvp
    
    for i, row in enumerate(matrix):
        arbvp.glProgramLocalParameter4fARB(
            arbvp.GL_VERTEX_PROGRAM_ARB, i + index,
            row[0], row[1], row[2], row[3])    

        
def setFragmentProgramVector(index, vector):
    """Convenience function which sets the fragment program local parameter
    at the given index to the given 4 component vector.
    """    
    
    import OpenGL.GL.ARB.fragment_program as arbfp
    
    arbfp.glProgramLocalParameter4fARB(
        arbfp.GL_FRAGMENT_PROGRAM_ARB, index, *vector) 


def setFragmentProgramMatrix(index, matrix):
    """Convenience function which sets four fragment program local parameters,
    starting at the given index, to the given ``4*4`` matrix.
    """ 
    
    import OpenGL.GL.ARB.fragment_program as arbfp
    
    for i, row in enumerate(matrix):
        arbfp.glProgramLocalParameter4fARB(
            arbfp.GL_FRAGMENT_PROGRAM_ARB, i + index,
            row[0], row[1], row[2], row[3])


def getShaderVars(shaders, vertAtts, vertUniforms, fragUniforms):
    """
    """

    import OpenGL.GL as gl

    shaderVars = {}

    for vu in vertUniforms:
        shaderVars[vu] = gl.glGetUniformLocation(shaders, vu)
        
    for va in vertAtts:
        shaderVars[va] = gl.glGetAttribLocation(shaders, va)

    for fu in fragUniforms:
        if fu in shaderVars:
            continue
        shaderVars[fu] = gl.glGetUniformLocation(shaders, fu)

    return shaderVars


def compilePrograms(vertexProgramSrc, fragmentProgramSrc):
    """Compiles the given vertex and fragment programs (written according
    to the ``ARB_vertex_program`` and ``ARB_fragment_program`` extensions),
    and returns references to the compiled programs.
    """
    
    import OpenGL.GL                      as gl
    import OpenGL.GL.ARB.fragment_program as arbfp
    import OpenGL.GL.ARB.vertex_program   as arbvp
    
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    fragmentProgram = arbfp.glGenProgramsARB(1)
    vertexProgram   = arbvp.glGenProgramsARB(1) 

    # vertex program
    try:
        arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                               vertexProgram)

        arbvp.glProgramStringARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                                 arbvp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                 len(vertexProgramSrc),
                                 vertexProgramSrc)

    except:

        position = gl.glGetIntegerv(arbvp.GL_PROGRAM_ERROR_POSITION_ARB)
        message  = gl.glGetString(  arbvp.GL_PROGRAM_ERROR_STRING_ARB)

        raise RuntimeError('Error compiling vertex program '
                           '({}): {}'.format(position, message)) 

    # fragment program
    try:
        arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                               fragmentProgram)

        arbfp.glProgramStringARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                 arbfp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                 len(fragmentProgramSrc),
                                 fragmentProgramSrc)
    except:
        position = gl.glGetIntegerv(arbfp.GL_PROGRAM_ERROR_POSITION_ARB)
        message  = gl.glGetString(  arbfp.GL_PROGRAM_ERROR_STRING_ARB)

        raise RuntimeError('Error compiling fragment program '
                           '({}): {}'.format(position, message))

    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    return vertexProgram, fragmentProgram


def compileShaders(vertShaderSrc, fragShaderSrc):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and returns a reference to the resulting program. Raises
    an error if compilation/linking fails.

    .. note:: I'm explicitly not using the PyOpenGL
              :func:`OpenGL.GL.shaders.compileProgram` function, because it
              attempts to validate the program after compilation, which fails
              due to texture data not being bound at the time of validation.
    """
    import OpenGL.GL as gl
    
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


def getVertexShader(globj):
    """Returns the vertex shader source for the given GL object."""
    return _getShader(globj, 'vert')


def getFragmentShader(globj):
    """Returns the fragment shader source for the given GL object.""" 
    return _getShader(globj, 'frag')



_shaderTypePrefixMap = td.TypeDict({
    
    ('GLVolume',     'vert') : 'glvolume',
    ('GLVolume',     'frag') : 'glvolume',

    ('GLLabel',      'vert') : 'glvolume',
    ('GLLabel',      'frag') : 'gllabel',
    
    ('GLRGBVector',  'vert') : 'glrgbvector',
    ('GLRGBVector',  'frag') : 'glvector',

    ('GLLineVector', 'vert') : 'gllinevector',
    ('GLLineVector', 'frag') : 'glvector',

    ('GLModel',      'vert') : 'glmodel',
    ('GLModel',      'frag') : 'glmodel',

    ('GLTensor',     'vert') : 'gltensor',
    ('GLTensor',     'frag') : 'glvector', 
})
"""This dictionary provides a mapping between :class:`.GLObject` types,
and file name prefixes, identifying the shader programs to use.
"""


def _getShaderPrefix(globj, shaderType):
    """Returns the prefix identifying the vertex/fragment shader programs to use
    for the given :class:`.GLObject` instance. If ``globj`` is a string, it is
    returned unchanged.
    """
    
    if isinstance(globj, str):
        return globj
    
    return _shaderTypePrefixMap[globj, shaderType]


def _setShaderPrefix(globj, shaderType, prefix):
    """Updates the prefix identifying the vertex/fragment shader programs to use
    for the given :class:`.GLObject` type or instance.
    """
    
    _shaderTypePrefixMap[globj, shaderType] = prefix


def _getShader(globj, shaderType):
    """Returns the shader source for the given GL object and the given
    shader type ('vert' or 'frag').
    """
    fname = _getFileName(globj, shaderType)
    with open(fname, 'rt') as f: src = f.read()
    return _preprocess(src)    


def _getFileName(globj, shaderType):
    """Returns the file name of the shader program for the given GL object
    and shader type. The ``globj`` parameter may alternately be a string,
    in which case it is used as the prefix for the shader program file name.
    """

    if   fslgl.GL_VERSION == '2.1':
        subdir = 'gl21'
        suffix = 'glsl'
    elif fslgl.GL_VERSION == '1.4':
        subdir = 'gl14'
        suffix = 'prog'

    if shaderType not in ('vert', 'frag'):
        raise RuntimeError('Invalid shader type: {}'.format(shaderType))

    prefix = _getShaderPrefix(globj, shaderType)

    return op.join(op.dirname(__file__), subdir, '{}_{}.{}'.format(
        prefix, shaderType, suffix))
 

def _preprocess(src):
    """'Preprocess' the given shader source.

    This amounts to searching for lines containing '#pragma include filename',
    and replacing those lines with the contents of the specified files.
    """

    if   fslgl.GL_VERSION == '2.1': subdir = 'gl21'
    elif fslgl.GL_VERSION == '1.4': subdir = 'gl14'

    lines    = src.split('\n')
    lines    = [l.strip() for l in lines]

    pragmas = []
    for linei, line in enumerate(lines):
        if line.startswith('#pragma'):
            pragmas.append(linei)

    includes = []
    for linei in pragmas:

        line = lines[linei].split()
        
        if len(line) != 3:       continue
        if line[1] != 'include': continue

        includes.append((linei, line[2]))

    for linei, fname in includes:
        fname = op.join(op.dirname(__file__), subdir, fname)
        with open(fname, 'rt') as f:
            lines[linei] = f.read()

    return '\n'.join(lines)
