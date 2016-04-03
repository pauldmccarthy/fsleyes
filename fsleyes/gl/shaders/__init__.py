#!/usr/bin/env python
#
# __init__.py - Funtions for managing OpenGL shader programs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``shaders`` package contains classes and functions for parsing,
compiling, and managing OpenGL shader programs. Two types of shader
program are supported:


 - GLSL 1.20 vertex and fragment shaders.

 - ``ARB_vertex_program`` and ``ARB_fragment_program`` shader programs.


The :mod:`.glsl` and :mod:`.arbp` packages respectively define the
:class:`.GLSLShader` and :class:`.ARBPShader` classes, which may be
used to manage shader programs of the corresponding type.


Some package-level functions are defined here, for finding and loading
shader source code:


 - :func:`getVertexShader`:   Locate and load the source code for a specific
                              vertex shader.

 - :func:`getFragmentShader`: Locate and load the source code for a specific
                              fragment shader.


Each of these functions locate shader source files, load the source code, and
run them through the :func:`preprocess` function, which performs some simple
preprocessing on the source. This applies to both GLSL and ARB assembly
shader programs.
"""


import os.path        as op

import fsl.fsleyes.gl as fslgl

import glsl.program   as glslprogram
import arbp.program   as arbpprogram


GLSLShader = glslprogram.GLSLShader
ARBPShader = arbpprogram.ARBPShader


def getVertexShader(prefix):
    """Returns the vertex shader source for the given GL type (e.g.
    'glvolume').
    """
    return _getShader(prefix, 'vert')


def getFragmentShader(prefix):
    """Returns the fragment shader source for the given GL type.""" 
    return _getShader(prefix, 'frag')


def _getShader(prefix, shaderType):
    """Returns the shader source for the given GL type and the given
    shader type ('vert' or 'frag').
    """
    fname = _getFileName(prefix, shaderType)
    with open(fname, 'rt') as f: src = f.read()
    return preprocess(src)    


def _getFileName(prefix, shaderType):
    """Returns the file name of the shader program for the given GL type
    and shader type.
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
 

def preprocess(src):
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
