#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import os.path            as op

import fsl.fsleyes.gl     as fslgl

import glsl.parse         as glslparse
import glsl.program       as glslprogram
import arbp.parse         as arbpparse
import arbp.program       as arbpprogram


log = logging.getLogger(__name__)


GLSLShader = glslprogram.GLSLShader
ARBPShaer  = arbpprogram.ARBPShader
parseGLSL  = glslparse  .parseGLSL
parseARBP  = arbpparse  .parseARBP



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


def getVertexShader(prefix):
    """Returns the vertex shader source for the given GL object."""
    return _getShader(prefix, 'vert')


def getFragmentShader(prefix):
    """Returns the fragment shader source for the given GL object.""" 
    return _getShader(prefix, 'frag')


def _getShader(prefix, shaderType):
    """Returns the shader source for the given GL object and the given
    shader type ('vert' or 'frag').
    """
    fname = _getFileName(prefix, shaderType)
    with open(fname, 'rt') as f: src = f.read()
    return _preprocess(src)    


def _getFileName(prefix, shaderType):
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

    return op.join(op.dirname(__file__), '..', subdir, '{}_{}.{}'.format(
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
        fname = op.join(op.dirname(__file__), '..', subdir, fname)
        with open(fname, 'rt') as f:
            lines[linei] = f.read()

    return '\n'.join(lines)
