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
import fsl.utils.transform as transform

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
        self.__initXform   = None

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        displayCtx.addListener('bounds',
                               self.__name,
                               self.__displayBoundsChanged)
        displayCtx.addListener('overlayOrder',
                               self.__name,
                               self.Refresh)

        self.addListener('pos',      self.__name, self.Refresh)
        self.addListener('centre',   self.__name, self.Refresh)
        self.addListener('zoom',     self.__name, self.Refresh)
        self.addListener('rotation', self.__name, self.Refresh)


    def destroy(self):
        self.__overlayList.removeListener('overlays',     self.__name)
        self.__displayCtx .removeListener('bounds',       self.__name)
        self.__displayCtx .removeListener('overlayOrder', self.__name)


    def _initGL(self):
        self.__displayBoundsChanged()


    def __overlayListChanged(self, *a):
        pass


    def __displayBoundsChanged(self, *a):
        b      = self.__displayCtx.bounds
        centre = [
            b.xlo + b.xlen / 2.0,
            b.ylo + b.ylen / 2.0,
            b.zlo + b.zlen / 2.0]

        self.centre = centre


    def canvasToWorld(self, xpos, ypos):

        xba, yba = xpos, ypos

        b             = self.__displayCtx.bounds
        width, height = self._getSize()
        ratio         = width / float(height)

        xlo, xhi = b.x
        ylo, yhi = b.y
        xlen     = b.xlen
        ylen     = b.ylen

        if   ratio > 1: xlen *= ratio
        elif ratio < 1: ylen /= ratio

        xhalf = 0.5 * xlen
        yhalf = 0.5 * ylen

        # Transform the mouse coordinates into
        # projected viewport coordinates - canvas x
        # corresponds to (-xhalf, xhalf), and
        # canvas y corresponds to (-yhalf, yhalf) -
        # see routines.show3D.
        xpos = xlen * (xpos / float(width))  - xhalf
        ypos = ylen * (ypos / float(height)) - yhalf

        # The camera is offset by 1 on
        # the depth axis (see __setViewport)
        pos  = np.array([xpos, ypos, -1])

        # The __initXform contains the initial
        # orientation code, and the
        # makeViewTransform method generates
        # the current rotate/scale/pan matrix
        xform = transform.concat(
            self.__initXform,
            self.__makeViewTransform())

        xform = transform.invert(xform)

        pos   = transform.transform(pos, xform)

        return pos


    def __makeViewTransform(self):

        b      = self.__displayCtx.bounds
        scale  = self.zoom / 100.0

        oldmid = np.array([b.xlo + 0.5 * b.xlen,
                           b.ylo + 0.5 * b.ylen,
                           b.zlo + 0.5 * b.zlen])

        newmid = oldmid * scale
        offset = (oldmid - newmid)

        return transform.compose([scale] * 3,
                                 offset,
                                 self.rotation,
                                 newmid)


    def __setViewport(self):

        width, height = self._getSize()

        if width == 0 or height == 0:
            return False

        b     = self.__displayCtx.bounds
        blo   = [b.xlo, b.ylo, b.zlo]
        bhi   = [b.xhi, b.yhi, b.zhi]

        if np.any(np.isclose(blo, bhi)):
            return False

        xmid  = b.xlo + 0.5 * b.xlen
        ymid  = b.ylo + 0.5 * b.ylen
        zmid  = b.zlo + 0.5 * b.zlen

        centre = (xmid, ymid,     zmid)
        eye    = (xmid, ymid - 1, zmid)
        up     = (0,    0,        1)

        np.set_printoptions(precision=7, suppress=True)

        self.__initXform = glroutines.lookAt(eye, centre, up)
        xform            = self.__makeViewTransform()
        xform            = transform.concat(self.__initXform, xform)

        glroutines.show3D(width,
                          height,
                          blo,
                          bhi,
                          xform)
        return True


    def _draw(self):

        if not self._setGLContext():
            return

        if not self.__setViewport():
            return

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

        if self.showCursor:
            with glroutines.enabled(gl.GL_DEPTH_TEST):
                self.__drawCursor()


    def __drawCursor(self):

        b   = self.__displayCtx.bounds
        pos = self.pos

        gl.glLineWidth(1)

        points = [
            (pos.x, pos.y, b.zlo),
            (pos.x, pos.y, b.zhi),
            (pos.x, b.ylo, pos.z),
            (pos.x, b.yhi, pos.z),
            (b.xlo, pos.y, pos.z),
            (b.xhi, pos.y, pos.z),
        ]

        gl.glColor3f(*self.cursorColour[:3])
        gl.glBegin(gl.GL_LINES)
        for p in points:
            gl.glVertex3f(*p)
        gl.glEnd()
        return

        # this code draws a bounding box
        # b = self.__displayCtx.bounds
        # gl.glLineWidth(1)
        # gl.glColor3f(0, 1, 0)
        # gl.glBegin(gl.GL_LINES)
        # gl.glVertex3f(b.xlo, b.ylo, b.zlo)
        # gl.glVertex3f(b.xlo, b.ylo, b.zhi)
        # gl.glVertex3f(b.xlo, b.yhi, b.zlo)
        # gl.glVertex3f(b.xlo, b.yhi, b.zhi)
        # gl.glVertex3f(b.xhi, b.ylo, b.zlo)
        # gl.glVertex3f(b.xhi, b.ylo, b.zhi)
        # gl.glVertex3f(b.xhi, b.yhi, b.zlo)
        # gl.glVertex3f(b.xhi, b.yhi, b.zhi)

        # gl.glVertex3f(b.xlo, b.ylo, b.zlo)
        # gl.glVertex3f(b.xlo, b.yhi, b.zlo)
        # gl.glVertex3f(b.xhi, b.ylo, b.zlo)
        # gl.glVertex3f(b.xhi, b.yhi, b.zlo)
        # gl.glVertex3f(b.xlo, b.ylo, b.zhi)
        # gl.glVertex3f(b.xlo, b.yhi, b.zhi)
        # gl.glVertex3f(b.xhi, b.ylo, b.zhi)
        # gl.glVertex3f(b.xhi, b.yhi, b.zhi)

        # gl.glVertex3f(b.xlo, b.ylo, b.zlo)
        # gl.glVertex3f(b.xhi, b.ylo, b.zlo)
        # gl.glVertex3f(b.xlo, b.ylo, b.zhi)
        # gl.glVertex3f(b.xhi, b.ylo, b.zhi)
        # gl.glVertex3f(b.xlo, b.yhi, b.zlo)
        # gl.glVertex3f(b.xhi, b.yhi, b.zlo)
        # gl.glVertex3f(b.xlo, b.yhi, b.zhi)
        # gl.glVertex3f(b.xhi, b.yhi, b.zhi)
        # gl.glEnd()
