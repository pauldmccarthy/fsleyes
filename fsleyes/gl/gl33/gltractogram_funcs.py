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

    vertSrc       = shaders.getVertexShader(  'gltractogram')
    orientFragSrc = shaders.getFragmentShader('gltractogram_orient')
    dataFragSrc   = shaders.getFragmentShader('gltractogram_data')
    lineGeomSrc   = shaders.getGeometryShader('gltractogram_line')
    tubeGeomSrc   = shaders.getGeometryShader('gltractogram_tube')

    # four shaders - one for each combination of
    # colouring by orientation vs colouring by data,
    # and drawing as lines vs drawing as tubes.
    self.lineOrientShader = shaders.GLSLShader(vertSrc,
                                               orientFragSrc,
                                               lineGeomSrc)
    self.tubeOrientShader = shaders.GLSLShader(vertSrc,
                                               orientFragSrc,
                                               tubeGeomSrc)
    self.lineDataShader   = shaders.GLSLShader(vertSrc,
                                               dataFragSrc,
                                               lineGeomSrc)
    self.tubeDataShader   = shaders.GLSLShader(vertSrc,
                                               dataFragSrc,
                                               tubeGeomSrc)

    allShaders = [self.lineOrientShader,
                  self.tubeOrientShader,
                  self.lineDataShader,
                  self.tubeDataShader]

    for shader in allShaders:
        with shader.loaded():
            shader.setAtt('vertex', self.vertices)
            shader.setAtt('orient', self.orients)
    updateShaderState(self)


def destroy(self):
    allShaders = [self.lineOrientShader,
                  self.tubeOrientShader,
                  self.lineDataShader,
                  self.tubeDataShader]
    for shader in allShaders:
        if shader is not None:
            shader.destroy()
    self.lineOrientShader = None
    self.tubeOrientShader = None
    self.lineDatShader    = None
    self.tubeDataShader   = None


def updateShaderState(self):
    opts           = self.opts
    loshader       = self.lineOrientShader
    toshader       = self.tubeOrientShader
    ldshader       = self.lineDataShader
    tdshader       = self.tubeDataShader
    colours, xform = opts.getVectorColours()
    scale          = xform[0, 0]
    offset         = xform[0, 3]

    for shader in (loshader, toshader):
        with shader.loaded():
            shader.set('xColour',      colours[0])
            shader.set('yColour',      colours[1])
            shader.set('zColour',      colours[2])
            shader.set('colourScale',  scale)
            shader.set('colourOffset', offset)
            shader.set('resolution',   opts.resolution)

    for shader in (ldshader, tdshader):
        #todo
        pass


def draw3D(self, xform=None):

    canvas    = self.canvas
    opts      = self.opts
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

    if opts.colourMode == 'orientation':
        if geom == 'line': shader = self.lineOrientShader
        else:              shader = self.tubeOrientShader
    else:
        if geom == 'line': shader = self.lineDataShader
        else:              shader = self.tubeDataShader


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
