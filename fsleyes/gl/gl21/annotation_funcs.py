#!/usr/bin/env python

#
# annotation_funcs.py - OpenGL 2.1 logic used by fsleyes.gl.annotations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This moduyle contains OpenGL 2.1 logic used by the
:mod:`fsleyes.gl.annotations` module.
"""

import sys

import numpy     as np
import OpenGL.GL as gl

import fsl.transform.affine as affine

import fsleyes.gl.shaders   as shaders


def dispatch(self, prefix, *args, **kwargs):
    """Used by :func:`init`, :func:`draw2D`, and :func:`destroy`. Searches for
     and calls the function specific to the :class:`.AnnotationObject`, or
    calls the default implementation if a specific one does not exist.
    """

    # Some annotation types have custom  functions,
    # whereas others use a default function.
    thisMod    = sys.modules[__name__]
    candidates = [
        '{}_{}'     .format(prefix, type(self).__name__),
        '{}_default'.format(prefix)
    ]
    for name in candidates:
        try:
            func = getattr(thisMod, name)
            break
        except AttributeError:
            continue

    # todo remove try/except when all
    # annotation types are supported
    try:
        func(self, *args, **kwargs)
    except Exception as e:
        print('annotation {} func error'.format(prefix), type(self), e)


def init(self):
    """Must be called when an :class:`.AnnotationObject` is created.
    Compiles shader programs and performs some other initialisation steps.
    """
    dispatch(self, 'init')


def destroy(self):
    """Must be called when an :class:`.AnnotationObject` is created. Clears
    any resources used by the ``AnnotationObject``.
    """
    dispatch(self, 'destroy')


def draw2D(self, zpos, axes):
    """Draw this :class:`.AnnotationObject`. """
    dispatch(self, 'draw2D', zpos, axes)


def init_default(self):
    """Default initialisation. Compiles the default annotation shader program.
    """
    vertSrc     = shaders.getVertexShader(  'annotations')
    fragSrc     = shaders.getFragmentShader('annotations')
    self.shader = shaders.GLSLShader(vertSrc, fragSrc)


def destroy_default(self):
    """Default clean-up. Frees the shader program. """
    self.shader.destroy()
    self.shader = None


def stackVertices(vertices):
    """Convenience function to concatenate several arrays of vertices into
    a single array.
    """
    # load all vertex types, and use offsets
    # to draw each vertex group separately
    lens     = [len(v) for v in vertices]
    offsets  = [0] + lens[:-1]
    vertices = np.vstack(vertices)

    return vertices, lens, offsets


def draw2D_default(self, zpos, axes):
    """Default draw routine, used for :class:`.Point`, :class:`.Line`, and
    :class:`.Arrow` annotations.
    """

    shader   = self.shader
    canvas   = self.canvas
    projmat  = canvas.projectionMatrix
    viewmat  = canvas.viewMatrix
    vertices = self.vertices2D(zpos, axes)

    if vertices is None or len(vertices) == 0:
        return

    if self.lineWidth is not None:
        gl.glLineWidth(self.lineWidth)

    colour = list(self.colour[:3]) + [self.alpha / 100.0]

    # load all vertex types, and use offsets
    # to draw each vertex group separately
    primitives              = [v[0] for v in vertices]
    vertices                = [v[1] for v in vertices]
    vertices, lens, offsets = stackVertices(vertices)

    shader.load()
    shader.set(   'P',      projmat)
    shader.set(   'MV',     viewmat)
    shader.set(   'colour', colour)
    shader.setAtt('vertex', vertices)
    shader.loadAtts()

    for primitive, length, offset in zip(primitives, lens, offsets):
        gl.glDrawArrays(primitive, offset, length)

    self.shader.unloadAtts()
    self.shader.unload()


def draw2D_Rect(self, zpos, axes):
    """Draw routine used for :class:`.Rect`and :class:`.Ellipse` annotations.
    """

    shader   = self.shader
    canvas   = self.canvas
    projmat  = canvas.projectionMatrix
    viewmat  = canvas.viewMatrix
    vertices = self.vertices2D(zpos, axes)

    if vertices is None or len(vertices) == 0:
        return

    primitives              = [v[0] for v in vertices]
    vertices                = [v[1] for v in vertices]
    vertices, lens, offsets = stackVertices(vertices)

    if self.lineWidth is not None:
        gl.glLineWidth(self.lineWidth)

    colour = list(self.colour[:3])
    alpha  = self.alpha / 100.0

    shader.load()
    shader.set(   'P',      projmat)
    shader.set(   'MV',     viewmat)
    shader.setAtt('vertex', vertices)
    shader.loadAtts()

    if self.border:
        if self.filled: shader.set('colour', colour + [1.0])
        else:           shader.set('colour', colour + [alpha])
        gl.glDrawArrays(primitives.pop(0), offsets.pop(0), lens.pop(0))
    if self.filled:
        shader.set('colour', colour + [alpha])
        gl.glDrawArrays(primitives.pop(0), offsets.pop(0), lens.pop(0))

    self.shader.unloadAtts()
    self.shader.unload()


draw2D_Ellipse = draw2D_Rect
