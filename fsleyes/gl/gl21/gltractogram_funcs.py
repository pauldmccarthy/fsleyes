#!/usr/bin/env python
#
# gltractogram_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import itertools as it
import OpenGL.GL as gl

import fsl.transform.affine as affine
import fsleyes.gl.routines  as glroutines
import fsleyes.gl.shaders   as shaders


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

    colourModes = ['orientation', 'vertexData', 'imageData']
    clipModes   = ['none',        'vertexData', 'imageData']
    kwa         = {'resourceName' : f'GLTractogram_{id(self)}',
                   'shared'       : ['vertex']}

    for colourMode, clipMode in it.product(colourModes, clipModes):
        print('SHD', colourMode, clipMode)

        fsrc   = colourSources[colourMode]
        consts = {
            'colourMode' : colourMode,
            'clipMode'   : clipMode,
            'lighting'   : False
        }
        shader = shaders.GLSLShader(vsrc,  fsrc, constants=consts, **kwa)

        self.shaders[colourMode][clipMode].append(shader)


def draw3D(self, xform=None):
    """Called by :class:`.GLTractogram.draw3D`. """
    canvas     = self.canvas
    opts       = self.opts
    display    = self.display
    colourMode = opts.effectiveColourMode
    clipMode   = opts.effectiveClipMode
    mvp        = canvas.mvpMatrix
    mv         = canvas.viewMatrix
    ovl        = self.overlay
    nstrms     = ovl.nstreamlines
    lineWidth  = opts.lineWidth
    offsets    = self.offsets
    counts     = self.counts
    nstrms     = len(offsets)

    shader = self.shaders[colourMode][clipMode][0]

    if xform is not None:
        mvp = affine.concat(mvp, xform)
        mv  = affine.concat(mv,  xform)

    with shader.loaded(), shader.loadedAtts():
        shader.set('MVP', mvp)
        # See comments in gl33.gltractogram_funcs.draw3D
        with glroutines.enabled(gl.GL_CULL_FACE):
            gl.glLineWidth(lineWidth)
            gl.glCullFace(gl.GL_BACK)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            if display.alpha < 100 or opts.modulateAlpha:
                gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
            with glroutines.enabled(gl.GL_DEPTH_TEST):
                gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
