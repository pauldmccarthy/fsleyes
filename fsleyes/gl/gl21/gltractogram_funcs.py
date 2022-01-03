#!/usr/bin/env python
#
# gltractogram_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy     as np
import OpenGL.GL as gl

import fsleyes.gl.routines as glroutines
import fsleyes.gl.shaders  as shaders


def compileShaders(self):

    vertSrc = shaders.getVertexShader(  'gltractogram')
    fragSrc = shaders.getFragmentShader('gltractogram')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, indexed=True)



def updateShaderState(self):

    shader = self.shader
    shader.load()
    shader.setAtt('vertex', self.vertices)
    shader.setAtt('orient', self.orients)
    shader.unload()



def draw3D(self, xform=None, bbox=None):

    shader  = self.shader
    ovl     = self.overlay
    opts    = self.opts
    nstrms  = ovl.numStreamlines

    offsets = self.offsets
    counts  = self.counts
    nstrms  = len(offsets)

    shader.load()
    shader.loadAtts()

    if xform is not None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('F'))

    with glroutines.enabled(gl.GL_DEPTH_TEST):
        gl.glLineWidth(opts.lineWidth)
        gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)

    if xform is not None:
        gl.glPopMatrix()
    shader.unloadAtts()
    shader.unload()
