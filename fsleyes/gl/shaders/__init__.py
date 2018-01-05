#!/usr/bin/env python
#
# __init__.py - Funtions for managing OpenGL shader programs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``shaders`` package contains classes and functions for finding,
parsing, compiling, and managing OpenGL shader programs. Two types of shader
program are supported:


 - GLSL 1.20 vertex and fragment shaders.

 - ``ARB_vertex_program`` and ``ARB_fragment_program`` shader programs.


The :mod:`.glsl` and :mod:`.arbp` packages respectively define the
:class:`.GLSLShader` and :class:`.ARBPShader` classes, which may be
used to manage shader programs of the corresponding type.


Some package-level functions are defined here, for finding and loading
shader source code:


  .. autosummary::
     :nosignatures:

     getShaderDir
     getShaderSuffix
     getVertexShader
     getFragmentShader
"""


# Import open from the io module, because it gives
# us an interface compatible across python 2 and 3
# (i.e. it allows us to specify the file encoding,
# and thus allows shader files to contain non-ascii
# characters).
from io import                 open
import os.path              as op

import                         fsleyes
import fsleyes.gl           as fslgl
from   .glsl import program as glslprogram
from   .arbp import program as arbpprogram


GLSLShader = glslprogram.GLSLShader
ARBPShader = arbpprogram.ARBPShader


def getShaderDir():
    """Returns the directory in which the ``ARB`` and ``glsl`` shader program
    source files can be found. A different directory will be returned depending
    on which OpenGL version is in use.
    """

    if   fslgl.GL_VERSION == '2.1': subdir = 'gl21'
    elif fslgl.GL_VERSION == '1.4': subdir = 'gl14'

    return op.join(fsleyes.assetDir, 'assets', 'gl', subdir)


def getShaderSuffix():
    """Returns the shader program file suffix to use. A different suffix will be
    returned depending on which OpenGL version is in use.
    """

    if   fslgl.GL_VERSION == '2.1': return 'glsl'
    elif fslgl.GL_VERSION == '1.4': return 'prog'


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
    with open(fname, 'rt', encoding='utf-8') as f:
        src = f.read()

    return preprocess(src)


def _getFileName(prefix, shaderType):
    """Returns the file name of the shader program for the given GL type
    and shader type.
    """

    suffix = getShaderSuffix()

    if shaderType not in ('vert', 'frag'):
        raise RuntimeError('Invalid shader type: {}'.format(shaderType))

    return op.join(getShaderDir(), '{}_{}.{}'.format(
        prefix, shaderType, suffix))


def preprocess(src):
    """'Preprocess' the given shader source.

    This amounts to searching for lines containing '#pragma include filename',
    and replacing those lines with the contents of the specified files.
    """

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
        fname = op.join(getShaderDir(), fname)
        with open(fname, 'rt', encoding='utf-8') as f:
            lines[linei] = f.read()

    return '\n'.join(lines)
