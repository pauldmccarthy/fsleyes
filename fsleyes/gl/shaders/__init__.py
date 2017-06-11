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
     getVertexShader
     getFragmentShader


The :class:`Filter` class also gives a simple interface to loading and
running simple filter shader programs, which require a 2D
:class:`.RenderTexture` as their input.
"""


# Import open from the io module, because it gives
# us an interface compatible across python 2 and 3
# (i.e. it allows us to specify the file encoding,
# and thus allows shader files to contain non-ascii
# characters).
from io import                 open
import os.path              as op
import OpenGL.GL            as gl

import                         fsleyes
import fsleyes.gl           as fslgl
from   .glsl import program as glslprogram
from   .arbp import program as arbpprogram


GLSLShader = glslprogram.GLSLShader
ARBPShader = arbpprogram.ARBPShader


def getShaderDir():
    """Returns the irectory in which the ``ARB`` and ``glsl`` source files
    can be found.  ``ARB`` files are assumed to be in a sub-directory called
    ``gl14``, and ``glsl`` files in a sub-directory called ``gl21``.
    """
    return op.join(fsleyes.assetDir, 'assets', 'gl')


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

    if   fslgl.GL_VERSION == '2.1':
        subdir = 'gl21'
        suffix = 'glsl'
    elif fslgl.GL_VERSION == '1.4':
        subdir = 'gl14'
        suffix = 'prog'

    if shaderType not in ('vert', 'frag'):
        raise RuntimeError('Invalid shader type: {}'.format(shaderType))

    return op.join(getShaderDir(), subdir, '{}_{}.{}'.format(
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
        fname = op.join(getShaderDir(), subdir, fname)
        with open(fname, 'rt', encoding='utf-8') as f:
            lines[linei] = f.read()

    return '\n'.join(lines)


class Filter(object):
    """
    """

    def __init__(self, filterName):

        filterName = 'filter_{}'.format(filterName)

        vertSrc = getVertexShader( 'filter')
        fragSrc = getFragmentShader(filterName)

        # TODO gl14
        self.__shader = GLSLShader(vertSrc, fragSrc)


    def destroy(self):
        self.__shader.destroy()
        self.__shader = None


    def apply(self,
              source,
              zpos,
              xmin,
              xmax,
              ymin,
              ymax,
              xax,
              yax,
              xform=None,
              **kwargs):

        self.__shader.load()
        self.__shader.set('texture', 0)

        for name, value in kwargs.items():
            self.__shader.set(name, value)

        source.drawOnBounds(zpos, xmin, xmax, ymin, ymax, xax, yax, xform)

        self.__shader.unload()


    def osApply(self, source, dest, clearDest=True, **kwargs):

        dest.bindAsRenderTarget()
        dest.setRenderViewport(0, 1, (0, 0, 0), (1, 1, 1))

        if clearDest:
            gl.glClear(gl.GL_COLOR_BUFFER_BIT |
                       gl.GL_DEPTH_BUFFER_BIT |
                       gl.GL_STENCIL_BUFFER_BIT)

        self.apply(source, 0.5, 0, 1, 0, 1, 0, 1, **kwargs)

        dest.unbindAsRenderTarget()
        dest.restoreViewport()
