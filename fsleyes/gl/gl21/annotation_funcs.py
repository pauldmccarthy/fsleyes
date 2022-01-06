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


def init(self):
    """
    """
    # Find the vertex shader for this annotation type.
    # Some annotation types have a custom shader,
    # called "annotations_<annotationType>_vert.glsl",
    # but some use a default shader called
    # "annotations_vert.glsl".
    candidates = [
        'annotations_{}'.format(type(self).__name__.lower()),
        'annotations'
    ]

    # todo remove outer try/except when all
    # annotation types are supported
    try:
        for c in candidates:
            try:
                vertSrc = shaders.getVertexShader(c)
            except Exception:
                pass
        fragSrc     = shaders.getFragmentShader('annotations')
        self.shader = shaders.GLSLShader(vertSrc, fragSrc)
    except:
        print('Annotation initialisation fail ', self)


def draw2D(self, zpos, axes):
    """
    """
    # Some annotation types have custom draw functions,
    # whereas others use a default draw function.
    thisMod    = sys.modules[__name__]
    candidates = [
        'draw2D_{}'.format(type(self).__name__),
        'draw2D_default'
    ]

    for name in candidates:
        try:
            drawFunc = getattr(thisMod, name)
        except AttributeError:
            pass

    # todo remove try/except when all
    # annotation types are supported
    try:
        drawFunc(self, zpos, axes)
    except Exception as e:
        print('annotation draw func error', type(self), e)


def draw2D_default(self, zpos, axes):
    """Default draw function for most annotation types. """

    canvas     = self.canvas
    shader     = self.shader
    projmat    = canvas.projectionMatrix
    viewmat    = canvas.viewMatrix
    vertices   = self.vertices2D(zpos, axes)
    primitives = [v[0] for v in vertices]
    vertices   = [v[1] for v in vertices]

    if self.lineWidth is not None:
        gl.glLineWidth(self.lineWidth)

    if self.colour is not None:
        if len(self.colour) == 3: colour = list(self.colour) + [1.0]
        else:                     colour = list(self.colour)
        colour[3] = self.alpha / 100.0

    if self.xform is not None:
        viewmat = affine.concat(self.xform, viewmat)

    shader.load()
    shader.set('P',      projmat)
    shader.set('MV',     viewmat)
    shader.set('colour', self.colour)

    # load all vertex types, and use offsets
    # to draw each vertex group separately
    lens     = [len(v) for v in vertices]
    offsets  = [0] + lens[:-1]
    vertices = np.vstack(vertices)

    shader.setAtt('vertex', vertices)
    shader.loadAtts()

    for primitive, length, offset in zip(primitives, lens, offsets):
        gl.glDrawArrays(primitive, offset, length)

    shader.unloadAtts()
    shader.unload()
