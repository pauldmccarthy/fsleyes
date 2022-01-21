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


import functools as ft

import OpenGL.GL as gl

import OpenGL.GL.EXT.framebuffer_object as glfbo

import fsleyes.gl as fslgl


def findGLSymbol(funcName,
                 minGLVersion,
                 fallbackExtension,
                 extensionSuffix=None):
    """Returns a decorator which will call the given OpenGL function via
    the OpenGL.GL namespace, or via the specified fallback GL extension,
    depending on the OpenGL compatibility level.
    """

    if extensionSuffix is None:
        extensionSuffix = ''

    def decorator(*args, **kwargs):
        if float(fslgl.GL_COMPATIBILITY) >= minGLVersion:
            func = getattr(gl, funcName)
        else:
            func = getattr(fallbackExtension, funcName + extensionSuffix)
        return func(*args, **kwargs)
    return decorator


_glfboFunction = ft.partial(findGLSymbol,
                            minGLVersion=3.0,
                            fallbackExtension=glfbo,
                            extensionSuffix='EXT')
_glfboConstant = ft.partial(findGLSymbol,
                            minGLVersion=3.0,
                            fallbackExtension=glfbo,
                            extensionSuffix='_EXT')

glGenFramebuffers         = _glfboFunction('glGenFramebuffers')
glGenRenderbuffers        = _glfboFunction('glGenRenderbuffers')
glDeleteFramebuffers      = _glfboFunction('glDeleteFramebuffers')
glDeleteRenderbuffers     = _glfboFunction('glDeleteRenderbuffers')
glBindFramebuffer         = _glfboFunction('glBindFramebuffer')
glBindRenderbuffer        = _glfboFunction('glBindRenderbuffer')
glFramebufferTexture2D    = _glfboFunction('glFramebufferTexture2D')
glRenderbufferStorage     = _glfboFunction('glRenderbufferStorage')
glFramebufferRenderbuffer = _glfboFunction('glFramebufferRenderbuffer')
glCheckFramebufferStatus  = _glfboFunction('glCheckFramebufferStatus')

GL_FRAMEBUFFER            = _glfboConstant('GL_FRAMEBUFFER')
GL_RENDERBUFFER           = _glfboConstant('GL_RENDERBUFFER')
GL_FRAMEBUFFER_BINDING    = _glfboConstant('GL_FRAMEBUFFER_BINDING')
GL_RENDERBUFFER_BINDING   = _glfboConstant('GL_RENDERBUFFER_BINDING')
GL_FRAMEBUFFER_COMPLETE   = _glfboConstant('GL_FRAMEBUFFER_COMPLETE')
GL_COLOR_ATTACHMENT0      = _glfboConstant('GL_COLOR_ATTACHMENT0')
GL_DEPTH_ATTACHMENT       = _glfboConstant('GL_DEPTH_ATTACHMENT')
