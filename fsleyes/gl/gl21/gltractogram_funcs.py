#!/usr/bin/env python
#
# gltractogram_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy     as np
import OpenGL.GL as gl


import fsleyes.gl.shaders as shaders


def compileShaders(self):

    vertSrc = shaders.getVertexShader(  'gltractogram')
    fragSrc = shaders.getFragmentShader('gltractogram')

    self.shader = shaders.GLSLShader(vertSrc, fragSrc, indexed=True)


def preDraw(self, xform=None, bbox=None):
    self.shader.load()


def draw3D(self, xform=None, bbox=None):

    shader = self.shader

    ovl    = self.overlay
    verts   = ovl.tractFile.streamlines
    nstrms  = len(verts)
    offsets = np.asarray(verts._offsets,   dtype=np.int32)
    counts  = np.asarray(verts._lengths,   dtype=np.int32)
    verts   = np.asarray(verts.get_data(), dtype=np.float32)

    shader.setAtt('vertex', verts)

    shader.loadAtts()

    gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)

    shader.unloadAtts()


def postDraw(self, xform=None, bbox=None):
    self.shader.unload()
