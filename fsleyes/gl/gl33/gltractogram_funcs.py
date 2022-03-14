#!/usr/bin/env python
#
# gltractogram_funcs.py - OpenGL 3.3 functions used by the GLTractogram class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions used by the :class:`.GLTractogram` class
when rendering in an OpenGL 3.3 compatible manner.
"""

import itertools as it

import OpenGL.GL as gl

import fsl.transform.affine as affine
import fsleyes.gl.routines  as glroutines
import fsleyes.gl.shaders   as shaders


def compileShaders(self):
    """Called by :meth:`.GLTractogram.compileShaders`.
    Compiles shader programs.
    """

    # We share shader sources across the shader
    # types, and do things slightly differently
    # depending on the shader type (via jinja2
    # preprocessing).
    vsrc       = shaders.getVertexShader(  'gltractogram')
    orientfsrc = shaders.getFragmentShader('gltractogram_orient')
    vdatafsrc  = shaders.getFragmentShader('gltractogram_vertex_data')
    idatafsrc  = shaders.getFragmentShader('gltractogram_image_data')
    linegsrc   = shaders.getGeometryShader('gltractogram_line')
    tubegsrc   = shaders.getGeometryShader('gltractogram_tube')

    # We create separate shader programs for each
    # combination of:
    #  - Geometry (lines or tubes)
    #  - Colouring (orientation, vertex data, image data)
    #  - Clipping (vertex data, image data)

    # So in total we create 18 shader programs - each
    # of the following, for both lines and tubes.
    #  - Colour by orientation, no clipping
    #  - Colour by orientation, clip by vertex data
    #  - Colour by orientation, clip by image data
    #  - Colour by vertex data, clip by same vertex data
    #  - Colour by vertex data, clip by different vertex data
    #  - Colour by vertex data, clip by image data
    #  - Colour by image data, clip by same image data
    #  - Colour by image data, clip by different image data
    #  - Colour by image data, clip by vertex data data

    colourSources = {
        'orientation' : orientfsrc,
        'vertexData'  : vdatafsrc,
        'imageData'   : idatafsrc,
    }

    colourModes = ['orientation', 'vertexData', 'imageData']
    clipModes   = ['none',        'vertexData', 'imageData']

    # Share the "in vec3 vertex"
    # buffer across all shaders
    kwa = {'resourceName' : f'GLTractogram_{id(self)}',
           'shared'       : ['vertex']}

    for colourMode, clipMode in it.product(colourModes, clipModes):

        fsrc   = colourSources[colourMode]
        consts = {
            'colourMode' : colourMode,
            'clipMode'   : clipMode,
            'lighting'   : True
        }

        lshader = shaders.GLSLShader(vsrc,  fsrc, linegsrc, consts, **kwa)
        tshader = shaders.GLSLShader(vsrc,  fsrc, tubegsrc, consts, **kwa)

        self.shaders[colourMode][clipMode].extend((lshader, tshader))


def draw3D(self, xform=None):
    """Called by :class:`.GLTractogram.draw3D`. """

    canvas     = self.canvas
    opts       = self.opts
    ovl        = self.overlay
    display    = self.display
    colourMode = opts.effectiveColourMode
    clipMode   = opts.effectiveClipMode
    vertXform  = ovl.affine
    mvp        = canvas.mvpMatrix
    mv         = canvas.viewMatrix
    lighting   = canvas.opts.light
    lightPos   = affine.transform(canvas.lightPos, mvp)
    nstrms     = ovl.nstreamlines
    lineWidth  = self.normalisedLineWidth
    offsets    = self.offsets
    counts     = self.counts
    nstrms     = len(offsets)

    if opts.resolution <= 2: geom = 'line'
    else:                    geom = 'tube'

    if geom == 'line': shader = self.shaders[colourMode][clipMode][0]
    else:              shader = self.shaders[colourMode][clipMode][1]

    if xform is None: xform = vertXform
    else:             xform = affine.concat(xform,  vertXform)

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
