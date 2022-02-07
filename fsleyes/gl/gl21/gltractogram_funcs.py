#!/usr/bin/env python
#
# gltractogram_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy     as np
import OpenGL.GL as gl

import fsl.transform.affine as affine
import fsleyes.gl.routines  as glroutines
import fsleyes.gl.shaders   as shaders


def compileShaders(self):

    vertSrc = shaders.getVertexShader(  'gltractogram')
    fragSrc = shaders.getFragmentShader('gltractogram')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, indexed=True)


def updateShaderState(self):

    shader = self.shader
    with shader.loaded():
        shader.setAtt('vertex', self.vertices)
        shader.setAtt('orient', self.orients)


def draw3D(self, xform=None):

    shader  = self.shader
    canvas  = self.canvas
    mvp     = canvas.mvpMatrix
    mv      = canvas.viewMatrix
    ovl     = self.overlay
    opts    = self.opts
    nstrms  = ovl.numStreamlines

    offsets = self.offsets
    counts  = self.counts
    nstrms  = len(offsets)

    if xform is not None:
        mvp = affine.concat(mvp, xform)
        mv  = affine.concat(mv,  xform)

    with shader.loaded(), shader.loadedAtts():
        shader.set('MV',  mv)
        shader.set('MVP', mvp)

        with glroutines.enabled(gl.GL_DEPTH_TEST):
            gl.glLineWidth(opts.lineWidth)
            gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
