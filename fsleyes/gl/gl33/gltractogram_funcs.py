#!/usr/bin/env python
#
# gltractogram_funcs.py - OpenGL 3.3 functions used by the GLTractogram class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions used by the :class:`.GLTractogram` class
when rendering in an OpenGL 3.3 compatible manner.
"""


import OpenGL.GL as gl

import fsl.transform.affine as affine
import fsleyes.gl.routines  as glroutines
import fsleyes.gl.shaders   as shaders


def compileShaders(self):
    """Called by :meth:`.GLTractogram.compileShaders`.
    Compiles shader programs.
    """

    vsrc       = shaders.getVertexShader(  'gltractogram')
    ivsrc      = shaders.getVertexShader(  'gltractogram_image_data')
    orientfsrc = shaders.getFragmentShader('gltractogram_orient')
    vdatafsrc  = shaders.getFragmentShader('gltractogram_vertex_data')
    idatafsrc  = shaders.getFragmentShader('gltractogram_image_data')
    linegsrc   = shaders.getGeometryShader('gltractogram_line')
    tubegsrc   = shaders.getGeometryShader('gltractogram_tube')

    oconst = {'dataType' : 'vec3'}
    dconst = {'dataType' : 'float'}

    # six shaders - one for each combination of
    # colouring by orientation vs colouring by data
    # vs colouring by image, and drawing as lines
    # vs drawing as tubes.
    lineOrientShader = shaders.GLSLShader(vsrc,  orientfsrc, linegsrc, oconst)
    tubeOrientShader = shaders.GLSLShader(vsrc,  orientfsrc, tubegsrc, oconst)
    lineVDataShader  = shaders.GLSLShader(vsrc,  vdatafsrc,  linegsrc, dconst)
    tubeVDataShader  = shaders.GLSLShader(vsrc,  vdatafsrc,  tubegsrc, dconst)
    lineIDataShader  = shaders.GLSLShader(ivsrc, idatafsrc,  linegsrc, oconst)
    tubeIDataShader  = shaders.GLSLShader(ivsrc, idatafsrc,  tubegsrc, oconst)

    self.shaders['orient'].extend([lineOrientShader, tubeOrientShader])
    self.shaders['vdata'] .extend([lineVDataShader,  tubeVDataShader])
    self.shaders['idata'] .extend([lineIDataShader,  tubeIDataShader])


def draw3D(self, xform=None):
    """Called by :class:`.GLTractogram.draw3D`. """

    canvas    = self.canvas
    opts      = self.opts
    cmode     = opts.effectiveColourMode
    mvp       = canvas.mvpMatrix
    mv        = canvas.viewMatrix
    ovl       = self.overlay
    nstrms    = ovl.nstreamlines
    lineWidth = self.normalisedLineWidth
    offsets   = self.offsets
    counts    = self.counts
    nstrms    = len(offsets)

    if opts.resolution <= 2: geom = 'line'
    else:                    geom = 'tube'

    if cmode == 'orient':
        if geom == 'line': shader = self.shaders['orient'][0]
        else:              shader = self.shaders['orient'][1]
    elif cmode == 'vdata':
        if geom == 'line': shader = self.shaders['vdata'][0]
        else:              shader = self.shaders['vdata'][1]
    elif cmode == 'idata':
        if geom == 'line': shader = self.shaders['idata'][0]
        else:              shader = self.shaders['idata'][1]

    if xform is not None:
        mvp = affine.concat(mvp, xform)
        mv  = affine.concat(mv,  xform)

    with shader.loaded(), shader.loadedAtts():
        shader.set('MVP',        mvp)
        shader.set('lineWidth',  lineWidth)

        if geom == 'line':
            camera    = [0, 0, 1]
            cameraRot = glroutines.rotate(90, *camera)[:3, :3]
            shader.set('camera',         camera)
            shader.set('cameraRotation', cameraRot)

        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        with glroutines.enabled(gl.GL_DEPTH_TEST):
            gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
