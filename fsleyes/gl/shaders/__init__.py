#!/usr/bin/env python
#
# __init__.py - Funtions for managing OpenGL shader programs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``shaders`` package contains classes and functions for finding,
parsing, compiling, and managing OpenGL shader programs. The following
types of shader program are supported:


 - GLSL 1.20 vertex and fragment shaders.
 - GLSL 3.30 vertex, geometry, and fragment shaders.
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
     getGeometryShader
     getFragmentShader
"""


import os.path              as op

import                         fsleyes
import fsleyes.gl           as fslgl
from   .glsl import parse   as glslparse
from   .glsl import program as glslprogram
from   .arbp import program as arbpprogram


GLSLShader = glslprogram.GLSLShader
ARBPShader = arbpprogram.ARBPShader


def getShaderDir():
    """Returns the directory in which the ``ARB`` and ``glsl`` shader program
    source files can be found. A different directory will be returned depending
    on which OpenGL version is in use.
    """

    if   fslgl.GL_COMPATIBILITY == '3.3': subdir = 'gl33'
    if   fslgl.GL_COMPATIBILITY == '2.1': subdir = 'gl21'
    elif fslgl.GL_COMPATIBILITY == '1.4': subdir = 'gl14'

    return op.join(fsleyes.assetDir, 'gl', subdir)


def getFallbackShaderDir():
    """Return a fall-back shader source directory, used if a version-specific
    file does not exist. This is only used when ``GL_COMPATIBILITY`` is 3.3,
    as most of the GL 2.1 source files are re-used.
    """
    if fslgl.GL_COMPATIBILITY != '3.3':
        raise RuntimeError('No fallback shaders for GL version ' +
                           fslgl.GL_COMPATIBILITY)
    return op.join(fsleyes.assetDir, 'gl', 'gl21')


def getShaderSuffix():
    """Returns the shader program file suffix to use. A different suffix will be
    returned depending on which OpenGL version is in use.
    """

    if float(fslgl.GL_COMPATIBILITY) < 2.1: return 'prog'
    else:                                   return 'glsl'


def getVertexShader(prefix):
    """Returns the vertex shader source for the given GL type (e.g.
    'glvolume').
    """
    return _getShader(prefix, 'vert')


def getGeometryShader(prefix):
    """Returns the geometry shader source for the given GL type (e.g.
    'glvolume').
    """
    return _getShader(prefix, 'geom')


def getFragmentShader(prefix):
    """Returns the fragment shader source for the given GL type."""
    return _getShader(prefix, 'frag')


def _getShader(prefix, shaderType):
    """Returns the shader source for the given GL type and the given
    shader type (``'vert'``, ``'geom'``, or ``'frag'``).
    """
    shaderDir = getShaderDir()
    fname     = _getFileName(prefix, shaderType, shaderDir)

    # For gl33, we use shader files in the gl33 sub
    # dir if they exist, or fall back to gl21 if not,
    # running them through a converter to make them
    # gl33 compatbile.
    if not op.exists(fname):
        shaderDir   = getFallbackShaderDir()
        fname       = _getFileName(prefix, shaderType, shaderDir)

    with open(fname, 'rt', encoding='utf-8') as f:
        src = f.read()

    return preprocess(src, shaderType, shaderDir)


def _getFileName(prefix, shaderType, shaderDir):
    """Returns the file name of the shader program for the given GL type
    and shader type.
    """

    suffix = getShaderSuffix()

    if shaderType not in ('vert', 'geom', 'frag'):
        raise RuntimeError('Invalid shader type: {}'.format(shaderType))

    return op.join(shaderDir, '{}_{}.{}'.format(prefix, shaderType, suffix))


def preprocess(src, shaderType, shaderDir=None):
    """'Preprocess' the given shader source.

    This amounts to:

      - searching for lines containing '#pragma include filename',
        and replacing those lines with the contents of the specified
        files.

      - If ``fsleyes.gl.GL_COMPATIBILITY == '3.3'``, and the shader source
        is GLSL version 120 (from the ``'2.1'`` shader sources),
        updating it to be compatible with GLSL 330.
    """

    if shaderDir is None:
        shaderDir = getShaderDir()

    lines = src.split('\n')

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
        fname = op.join(shaderDir, fname)
        with open(fname, 'rt', encoding='utf-8') as f:
            lines[linei] = f.read()

    src = '\n'.join(lines)

    if fslgl.GL_COMPATIBILITY == '3.3' and '#version 120' in src:
        src = glslparse.convert120to330(src, shaderType)

    return src
