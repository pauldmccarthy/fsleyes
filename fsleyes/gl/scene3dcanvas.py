#!/usr/bin/env python
#
# scene3dcanvas.py - The Scene3DCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""


import logging

import copy

import numpy     as np
import OpenGL.GL as gl

import fsleyes_props as props

import fsl.data.mesh       as fslmesh

import fsleyes.gl.routines as glroutines
import fsleyes.displaycontext.canvasopts as canvasopts


log = logging.getLogger(__name__)

class Scene3DCanvas(props.HasProperties):


    pos           = copy.copy(canvasopts.Scene3DCanvasOpts.pos)
    showCursor    = copy.copy(canvasopts.Scene3DCanvasOpts.showCursor)
    cursorColour  = copy.copy(canvasopts.Scene3DCanvasOpts.cursorColour)
    bgColour      = copy.copy(canvasopts.Scene3DCanvasOpts.bgColour)
    zoom          = copy.copy(canvasopts.Scene3DCanvasOpts.zoom)
    showLegend    = copy.copy(canvasopts.Scene3DCanvasOpts.showLegend)
    centre        = copy.copy(canvasopts.Scene3DCanvasOpts.centre)
    rotation      = copy.copy(canvasopts.Scene3DCanvasOpts.rotation)


    def __init__(self, overlayList, displayCtx):

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(self.__class__.__name__, id(self))

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        displayCtx.addListener('bounds',
                               self.__name,
                               self.__displayBoundsChanged)
        displayCtx.addListener('overlayOrder',
                               self.__name,
                               self.Refresh)

        self.addListener('pos',    self.__name, self.Refresh)
        self.addListener('centre', self.__name, self.Refresh)
        self.addListener('zoom',   self.__name, self.Refresh)

        self.xform = np.eye(4)


    def destroy(self):
        self.__overlayList.removeListener('overlays',     self.__name)
        self.__displayCtx .removeListener('bounds',       self.__name)
        self.__displayCtx .removeListener('overlayOrder', self.__name)


    def _initGL(self):
        self.__displayBoundsChanged()


    def canvasToWorld(self, xpos, ypos):

        # TODO
        return [0, 0, 0]


    def __overlayListChanged(self, *a):
        pass


    def __displayBoundsChanged(self, *a):
        b      = self.__displayCtx.bounds
        centre = [
            b.xlo + b.xlen / 2.0,
            b.ylo + b.ylen / 2.0,
            b.zlo + b.zlen / 2.0]

        self.centre = centre


    def _draw(self):

        width, height = self._getSize()
        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        b      = self.__displayCtx.bounds
        blo    = np.array([b.xlo, b.ylo, b.zlo])
        bhi    = np.array([b.xhi, b.yhi, b.zhi])
        blen   = bhi - blo
        bmid   = blo + 0.5 * blen
        blen  *= (self.zoom / 100.0)

        blo    = bmid - 0.5 * blen
        bhi    = bmid + 0.5 * blen

        if np.any(np.isclose(blen, 0)):
            return

        glroutines.show3D(width,
                          height,
                          blo,
                          bhi,
                          self.xform)
        glroutines.clear((0, 0, 0, 1))

        for ovl in self.__overlayList:
            if not isinstance(ovl, fslmesh.TriangleMesh):
                continue

            verts = np.array(ovl.vertices, dtype=np.float32)
            idxs  = np.array(ovl.indices, dtype=np.uint32)

            xs = verts[:, 0]
            ys = verts[:, 1]
            zs = verts[:, 2]

            xs = 0.25 + 0.75 * (xs - xs.min()) / (xs.max() - xs.min())
            ys = 0.25 + 0.75 * (ys - ys.min()) / (ys.max() - ys.min())
            zs = 0.25 + 0.75 * (zs - zs.min()) / (zs.max() - zs.min())

            colours = np.vstack((xs, ys, zs)).T

            opts = self.__displayCtx.getOpts(ovl)

            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            gl.glLineWidth(2)
            gl.glColor3f(*opts.colour[:3])

            with glroutines.enabled((gl.GL_VERTEX_ARRAY,
                                     gl.GL_DEPTH_TEST)):

                idxs = idxs.ravel('C')

                gl.glColorPointer( 3, gl.GL_FLOAT, 0, colours.ravel('C'))
                gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts  .ravel('C'))
                gl.glDrawElements(gl.GL_TRIANGLES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


        gl.glPointSize(10)
        gl.glColor3f(1, 0, 0)
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex3f(*self.pos[:])
        gl.glEnd()

        b = self.__displayCtx.bounds
        gl.glLineWidth(1)
        gl.glColor3f(0, 1, 0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(b.xlo, b.ylo, b.zlo)
        gl.glVertex3f(b.xlo, b.ylo, b.zhi)
        gl.glVertex3f(b.xlo, b.yhi, b.zlo)
        gl.glVertex3f(b.xlo, b.yhi, b.zhi)
        gl.glVertex3f(b.xhi, b.ylo, b.zlo)
        gl.glVertex3f(b.xhi, b.ylo, b.zhi)
        gl.glVertex3f(b.xhi, b.yhi, b.zlo)
        gl.glVertex3f(b.xhi, b.yhi, b.zhi)

        gl.glVertex3f(b.xlo, b.ylo, b.zlo)
        gl.glVertex3f(b.xlo, b.yhi, b.zlo)
        gl.glVertex3f(b.xhi, b.ylo, b.zlo)
        gl.glVertex3f(b.xhi, b.yhi, b.zlo)
        gl.glVertex3f(b.xlo, b.ylo, b.zhi)
        gl.glVertex3f(b.xlo, b.yhi, b.zhi)
        gl.glVertex3f(b.xhi, b.ylo, b.zhi)
        gl.glVertex3f(b.xhi, b.yhi, b.zhi)

        gl.glVertex3f(b.xlo, b.ylo, b.zlo)
        gl.glVertex3f(b.xhi, b.ylo, b.zlo)
        gl.glVertex3f(b.xlo, b.ylo, b.zhi)
        gl.glVertex3f(b.xhi, b.ylo, b.zhi)
        gl.glVertex3f(b.xlo, b.yhi, b.zlo)
        gl.glVertex3f(b.xhi, b.yhi, b.zlo)
        gl.glVertex3f(b.xlo, b.yhi, b.zhi)
        gl.glVertex3f(b.xhi, b.yhi, b.zhi)
        gl.glEnd()
