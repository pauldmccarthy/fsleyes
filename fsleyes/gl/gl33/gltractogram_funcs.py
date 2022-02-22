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

    # The geometry shaders just pass
    # through data of this type
    oconst = {'passThru' : ['vec3']}
    dconst = {'passThru' : ['float']}

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

    self.shaders['orientation'].extend([lineOrientShader, tubeOrientShader])
    self.shaders['vertexData'] .extend([lineVDataShader,  tubeVDataShader])
    self.shaders['imageData']  .extend([lineIDataShader,  tubeIDataShader])


def draw3D(self, xform=None):
    """Called by :class:`.GLTractogram.draw3D`. """

    canvas    = self.canvas
    opts      = self.opts
    display   = self.display
    cmode     = opts.effectiveColourMode
    mvp       = canvas.mvpMatrix
    mv        = canvas.viewMatrix
    lighting  = canvas.opts.light
    lightPos  = affine.transform(canvas.lightPos, mvp)
    ovl       = self.overlay
    nstrms    = ovl.nstreamlines
    lineWidth = self.normalisedLineWidth
    offsets   = self.offsets
    counts    = self.counts
    nstrms    = len(offsets)

    if opts.resolution <= 2: geom = 'line'
    else:                    geom = 'tube'

    if geom == 'line': shader = self.shaders[cmode][0]
    else:              shader = self.shaders[cmode][1]

    if xform is not None:
        mvp = affine.concat(mvp, xform)
        mv  = affine.concat(mv,  xform)

    with shader.loaded(), shader.loadedAtts():
        shader.set('MVP',        mvp)
        shader.set('lineWidth',  lineWidth)

        # Line geometry shader needs to know
        # the camera direction so it can
        # position line/rectangle vertices
        if geom == 'line':
            camera    = [0, 0, 1]
            cameraRot = glroutines.rotate(90, *camera)[:3, :3]
            shader.set('camera',         camera)
            shader.set('cameraRotation', cameraRot)

        # Only use lighting on tube geometry,
        # as it looks rubbish on lines
        else:
            shader.set('lighting', lighting)
            shader.set('lightPos', lightPos)

        with glroutines.enabled(gl.GL_CULL_FACE):
            gl.glCullFace(gl.GL_BACK)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            # Alpha blending does not work with glMultiDrawArrays,
            # because the order in which streamlines are drawn is
            # arbitrary, so streamlines which are drawn first will
            # be blended with the background, and streamlines which
            # are drawn later will be blended with those already
            # drawn. But the former streamlines may be positioned
            # in front of the latter ones :(
            #
            # To work around this and to get a tractogram that looks
            # ok from any angle, we draw the tractogram twice - first
            # without, and then with depth testing.
            if display.alpha < 100 or opts.modulateAlpha:
                gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
            with glroutines.enabled(gl.GL_DEPTH_TEST):
                gl.glMultiDrawArrays(gl.GL_LINE_STRIP, offsets, counts, nstrms)
