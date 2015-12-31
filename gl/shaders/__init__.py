#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import os.path        as op

import fsl.fsleyes.gl as fslgl

import glsl.program   as glslprogram
import arbp.program   as arbpprogram


log = logging.getLogger(__name__)


GLSLShader = glslprogram.GLSLShader
ARBPShader = arbpprogram.ARBPShader


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
