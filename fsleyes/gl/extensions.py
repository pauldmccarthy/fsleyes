#!/usr/bin/env python
#
# extensions.py - OpenGL that may be provided by extensions, or in core GL.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module houses OpenGL functions and constants which are used by FSLeyes
and which, depending on the version of OpenGL in use, may need to be accessed
through ``ARB`` or ``EXT`` extensions.
"""


import              sys
import functools as ft
import OpenGL.GL as gl

import OpenGL.GL.EXT.framebuffer_object as glfbo
import OpenGL.GL.ARB.instanced_arrays   as arbia
import OpenGL.GL.ARB.draw_instanced     as arbdi


import fsleyes.gl as fslgl


class GLSymbolResolver:
    """Class which accumulates a list of GL symbols (functions or constants)
    that need to be resolved from either core GL (OpenGL.GL), or a particular
    GL extension.

    The :meth:`resolve` method resolves all symbols, and adds them as
    attributes to this module.

    This pattern (build a list of all symbols, and then resolve them later) is
    followed, because it is not possible to query the available GL version
    until a GL context has been created.  The :func:`initialise` function
    (which in turn calls ``resolve``) is called by the
    :func:`fsleyes.gl.bootstrap` function.
    """

    def __init__(self):
        self.__symbols = []


    def register(self,
                 name,
                 minGLVersion,
                 fallbackExtension,
                 extensionSuffix=None):
        """Queue a GL symbol to be resolved later.

        :arg name:              Name of the symbol, e.g. ``glGenFrameBuffers``

        :arg minGLVersion:      Version of OpenGL that the symbol was added
                                to core GL, e.g. ``3.0``.

        :arg fallbackExtension: GL extension module to fall back to, if an
                                older GL version is in use, e.g.
                                ``OpenGL.GL.EXT.framebuffer_object``.

        :arg extensionSuffix:   Suffix to add to the symbol name, if accessing
                                it via the fallback extension, e.g. ``EXT``
                                (thus changing the name to
                                ``glGenFrameBuffersEXT``.
        """

        self.__symbols.append((name,
                               minGLVersion,
                               fallbackExtension,
                               extensionSuffix))


    def resolve(self):
        """Resolves all registered GL symbols, adding them as attributes to
        this module.
        """

        thismod = sys.modules[__name__]

        for name, minGLVer, fallbackExt, extSuffix in self.__symbols:
            if float(fslgl.GL_COMPATIBILITY) >= minGLVer:
                sym = getattr(gl, name)
            else:
                sym = getattr(fallbackExt, name + extSuffix)

            setattr(thismod, name, sym)


_resolver = GLSymbolResolver()


def initialise():
    """Intended to be called by :func:`fsleyes.gl.bootstrap`, once a GL
    context has been created, and the available GL version identified.
    """
    _resolver.resolve()


def register(*args, **kwargs):
    """Wrapper around  :meth:`GLSymbolResolver.register`. """
    _resolver.register(*args, **kwargs)


register('glGenFramebuffers',         3.0, glfbo, 'EXT')
register('glGenRenderbuffers',        3.0, glfbo, 'EXT')
register('glDeleteFramebuffers',      3.0, glfbo, 'EXT')
register('glDeleteRenderbuffers',     3.0, glfbo, 'EXT')
register('glBindFramebuffer',         3.0, glfbo, 'EXT')
register('glBindRenderbuffer',        3.0, glfbo, 'EXT')
register('glFramebufferTexture2D',    3.0, glfbo, 'EXT')
register('glRenderbufferStorage',     3.0, glfbo, 'EXT')
register('glFramebufferRenderbuffer', 3.0, glfbo, 'EXT')
register('glCheckFramebufferStatus',  3.0, glfbo, 'EXT')
register('GL_FRAMEBUFFER',            3.0, glfbo, '_EXT')
register('GL_RENDERBUFFER',           3.0, glfbo, '_EXT')
register('GL_FRAMEBUFFER_BINDING',    3.0, glfbo, '_EXT')
register('GL_RENDERBUFFER_BINDING',   3.0, glfbo, '_EXT')
register('GL_FRAMEBUFFER_COMPLETE',   3.0, glfbo, '_EXT')
register('GL_COLOR_ATTACHMENT0',      3.0, glfbo, '_EXT')
register('GL_DEPTH_ATTACHMENT',       3.0, glfbo, '_EXT')

register('glVertexAttribDivisor',   3.3, arbia, 'ARB')
register('glDrawElementsInstanced', 3.1, arbdi, 'ARB')
register('glDrawArraysInstanced',   3.1, arbdi, 'ARB')
