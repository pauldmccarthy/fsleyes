#!/usr/bin/env python
#
# gltractogram_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import OpenGL.GL as gl

import fsl.transform.affine as affine
import fsleyes.gl.routines  as glroutines
import fsleyes.gl.shaders   as shaders


def compileShaders(self):

    vertSrc = shaders.getVertexShader(  'gltractogram')
    fragSrc = shaders.getFragmentShader('gltractogram')
    geomSrc = shaders.getGeometryShader('gltractogram')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, geomSrc)


def draw3D(self, xform=None):

    shader  = self.shader
    canvas  = self.canvas
    mvp     = canvas.mvpMatrix
    mv      = canvas.viewMatrix
    ovl     = self.overlay
    opts    = self.opts
    nstrms  = ovl.nstreamlines

    offsets = self.offsets
    counts  = self.counts
    nstrms  = len(offsets)

    if xform is not None:
        mvp = affine.concat(mvp, xform)
        mv  = affine.concat(mv,  xform)

    cw, ch    = canvas.GetSize()
    lineWidth = opts.lineWidth * max((1 / cw, 1 / ch))

    with shader.loaded(), shader.loadedAtts():
        shader.set('MVP',        mvp)
        shader.set('lineWidth',  lineWidth)

        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        with glroutines.enabled(gl.GL_DEPTH_TEST):
            gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
