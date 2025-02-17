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
    pointgsrc  = shaders.getGeometryShader('gltractogram_point')

    # We create separate shader programs for each
    # combination of:
    #  - Geometry (3D: lines or tubes, 2D: points)
    #  - Colouring (orientation, vertex data, image data)
    #  - Clipping (vertex data, image data)

    # So for 3D rendering we create a total of 18 shader programs,
    # for each of the following, for both lines and tubes. For 2D
    # rendering we create a total of 9 shader programs.
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
    geomSources = {
        'line'  : linegsrc,
        'point' : pointgsrc,
        'tube'  : tubegsrc
    }

    colourModes = ['orientation', 'vertexData', 'imageData']
    clipModes   = ['none',        'vertexData', 'imageData']
    dims        = ['2D', '3D']
    geoms       = ['line', 'tube', 'point']

    # Share the "in vec3 vertex"
    # buffer across all shaders
    kwa = {'resourceName' : f'GLTractogram_{id(self)}',
           'shared'       : ['vertex']}

    for dim, geom, colourMode, clipMode in it.product(
            dims, geoms, colourModes, clipModes):

        fsrc  = colourSources[colourMode]
        gsrc  = geomSources[geom]
        const = {
            'colourMode' : colourMode,
            'clipMode'   : clipMode,
            'lighting'   : (dim == '3D') and (geom == 'tube')
        }
        prog = shaders.GLSLShader(vsrc, fsrc, gsrc, const, **kwa)
        self.shaders[dim][colourMode][clipMode][geom] = prog


def draw2D(self, canvas, mvp):
    """Called by :class:`.GLTractogram.draw2D`. """
    opts       = self.opts
    colourMode = opts.effectiveColourMode
    clipMode   = opts.effectiveClipMode
    shader     = self.shaders['2D'][colourMode][clipMode]['point']
    scales     = self.normalisedLineWidth(canvas, mvp, False)

    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

    with shader.loaded(), shader.loadedAtts():
        shader.set('MVP',    mvp)
        shader.set('xscale', scales[0])
        shader.set('yscale', scales[1])
        shader.draw(gl.GL_POINTS, 0, len(self.vertices))


def drawPseudo3D(self, canvas, mvp):
    """Called by :class:`.GLTractogram.drawPseudo3D`. """

    dctx          = self.displayCtx
    xax           = canvas.opts.xax
    yax           = canvas.opts.yax
    zax           = canvas.opts.zax
    xmin, xmax    = dctx.bounds.x
    ymin, ymax    = dctx.bounds.y
    zmin, zmax    = dctx.bounds.z
    xmid          = xmin + (xmax - xmin) / 2
    ymid          = ymin + (ymax - ymin) / 2
    lightPos      = [0, 0, 0]
    lightPos[xax] = xmid
    lightPos[yax] = ymid
    lightPos[zax] = zmin - 5 * (zmax - zmin)

    lightPos = affine.transform(lightPos, mvp)

    if lightPos[2] > 0:
        lightPos[2] *= -1

    draw3D(self, canvas, mvp, True, lightPos, threedee=False)


def draw3D(self,
           canvas,
           mvp,
           lighting,
           lightPos,
           threedee=True,
           xform=None):
    """Called by :class:`.GLTractogram.draw3D`. """

    opts      = self.opts
    ovl       = self.overlay
    display   = self.display
    colMode   = opts.effectiveColourMode
    clipMode  = opts.effectiveClipMode
    nstrms    = ovl.nstreamlines
    lineWidth = self.normalisedLineWidth(canvas, mvp, threedee)
    offsets   = self.offsets
    counts    = self.counts
    nstrms    = len(offsets)

    if opts.resolution <= 2: geom = 'line'
    else:                    geom = 'tube'

    shader = self.shaders['3D'][colMode][clipMode][geom]

    if xform is not None:
        mvp = affine.concat(mvp, xform)

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
            gl.glFrontFace(gl.GL_CCW)
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
