#!/usr/bin/env python
#
# gltractogram_funcs.py - GL21 functions for drawing tractogram overlays.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module comtains functions for drawing tractogram overlays with OpenGL
2.1. These functions are used by :class:`.GLTractogram` instances.
"""

import itertools as it
import OpenGL.GL as gl
import numpy     as np

import fsl.transform.affine  as affine
import fsleyes.gl.routines   as glroutines
import fsleyes.gl.extensions as glexts
import fsleyes.gl.shaders    as shaders


def compileShaders(self):
    """Called by :meth:`.GLTractogram.compileShaders`.
    Compiles shader programs.
    """

    # See comments in gl33.gltractogram_funcs.compileShaders
    vsrc       = shaders.getVertexShader(  'gltractogram')
    orientfsrc = shaders.getFragmentShader('gltractogram_orient')
    vdatafsrc  = shaders.getFragmentShader('gltractogram_vertex_data')
    idatafsrc  = shaders.getFragmentShader('gltractogram_image_data')

    colourSources = {
        'orientation' : orientfsrc,
        'vertexData'  : vdatafsrc,
        'imageData'   : idatafsrc,
    }

    dims        = ['2D', '3D']
    colourModes = ['orientation', 'vertexData', 'imageData']
    clipModes   = ['none',        'vertexData', 'imageData']
    kwa         = {'resourceName' : f'GLTractogram_{id(self)}',
                   'shared'       : ['vertex']}

    for dim, colourMode, clipMode in it.product(dims, colourModes, clipModes):

        fsrc   = colourSources[colourMode]
        consts = {
            'colourMode' : colourMode,
            'clipMode'   : clipMode,
            'lighting'   : False,
            'twod'       : dim == '2D'
        }
        shader = shaders.GLSLShader(vsrc, fsrc, constants=consts, **kwa)

        self.shaders[dim][colourMode][clipMode]['geom'] = shader


def draw2D(self, canvas, mvp):
    """Called by :class:`.GLTractogram.draw2D`. """

    opts       = self.opts
    colourMode = opts.effectiveColourMode
    clipMode   = opts.effectiveClipMode
    res        = max((opts.resolution, 3))
    shader     = self.shaders['2D'][colourMode][clipMode]['geom']

    # each vertex is drawn as a circle,
    # using instanced rendering.
    vertices         = glroutines.unitCircle(res)
    scales           = self.normalisedLineWidth(canvas, mvp, False)
    vertices[:, :2] *= scales[:2]

    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

    with shader.loaded(), shader.loadedAtts():
        shader.set(   'MVP',          mvp)
        shader.setAtt('circleVertex', vertices)
        glexts.glDrawArraysInstanced(gl.GL_TRIANGLE_FAN,
                                     0,
                                     len(vertices),
                                     len(self.vertices))


def drawPseudo3D(self, canvas, mvp):
    """Called by :class:`.GLTractogram.drawPseudo3D`. """
    draw3D(self, canvas, mvp, None, None, None)


def draw3D(self,
           canvas,
           mvp,
           lighting,
           lightPos,
           xform=None):
    """Called by :class:`.GLTractogram.draw3D`.
    The lighting arguments are ignored.
    """
    opts       = self.opts
    display    = self.display
    colourMode = opts.effectiveColourMode
    clipMode   = opts.effectiveClipMode
    lineWidth  = opts.lineWidth
    offsets    = self.offsets
    counts     = self.counts
    nstrms     = len(offsets)
    shader     = self.shaders['3D'][colourMode][clipMode]['geom']

    if xform is not None:
        mvp = affine.concat(mvp, xform)

    with shader.loaded(), shader.loadedAtts():
        shader.set('MVP', mvp)
        # we don't implement proper line width in
        # gl21 - we would need to use instanced
        # rendering to draw each line segment as a
        # rectangle (see gl33.gltractogram_funcs.draw3D)
        gl.glLineWidth(lineWidth)
        if display.alpha < 100 or opts.modulateAlpha:
            gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
        with glroutines.enabled(gl.GL_DEPTH_TEST):
            gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
