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
    showLegend    = copy.copy(canvasopts.Scene3DCanvasOpts.showLegend)
    zoom          = copy.copy(canvasopts.Scene3DCanvasOpts.zoom)
    offset        = copy.copy(canvasopts.Scene3DCanvasOpts.offset)
    rotation      = copy.copy(canvasopts.Scene3DCanvasOpts.rotation)


    def __init__(self, overlayList, displayCtx):

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(self.__class__.__name__, id(self))
        self.__xform       = None

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
        self.addListener('offset',   self.__name, self.Refresh)
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
        pass


    def canvasToWorld(self, xpos, ypos):
        """Transform the given x/y canvas coordinates into the display
        coordinate system.
        """

        b             = self.__displayCtx.bounds
        width, height = self._getSize()

        # The first step is to invert the mouse
        # coordinates w.r.t. the viewport.
        #
        # The canvas x axis corresponds to
        # (-xhalf, xhalf), and the canvas y
        # corresponds to (-yhalf, yhalf) -
        # see routines.show3D.
        xlen, ylen = glroutines.adjust(b.xlen, b.ylen, width, height)
        xhalf      = 0.5 * xlen
        yhalf      = 0.5 * ylen

        # Pixels to viewport coordinates
        xpos = xlen * (xpos / float(width))  - xhalf
        ypos = ylen * (ypos / float(height)) - yhalf

        # The second step is to transform from
        # viewport coords into model-view coords.
        # This is easy - transform by the inverse
        # MV matrix.
        #
        # z=-1 because the camera is offset by 1
        # on the depth axis (see __setViewport).
        pos   = np.array([xpos, ypos, -1])
        xform = transform.invert(self.__xform)
        pos   = transform.transform(pos, xform)

        return pos


    def __genModelViewMatrix(self):
        """Generate and return a transformation matrix to be used as the
        model-view matrix. This includes applying the current :attr:`zoom`,
        :attr:`rotation` and :attr:`offset` settings, and configuring
        the camera. This method is called by :meth:`__setViewport`.
        """

        b      = self.__displayCtx.bounds
        w, h   = self._getSize()
        centre = [b.xlo + 0.5 * b.xlen,
                  b.ylo + 0.5 * b.ylen,
                  b.zlo + 0.5 * b.zlen]

        # The MV matrix comprises (in this order):
        #
        #    - A rotation (the rotation property)
        #
        #    - Camera configuration. With no rotation, the
        #      camera will be looking towards the positive
        #      Y axis (i.e. +y is forwards), and oriented
        #      towards the positive Z axis (i.e. +z is up)
        #
        #    - A translation (the offset property)
        #    - A scaling (the zoom property)

        # Scaling and rotation matrices. Rotation
        # is always around the centre of the
        # displaycontext bounds (the bounding
        # box which contains all loaded overlays).
        scale  = self.zoom / 100.0
        scale  = transform.scaleOffsetXform([scale] * 3, 0)
        rotate = transform.rotMatToAffine(self.rotation, centre)

        # The offset property is defined in x/y
        # pixels. We need to conver them into
        # viewport space, where the horizontal
        # axis maps to (-xhalf, xhalf), and the
        # vertical axis maps to (-yhalf, yhalf).
        # See gl.routines.show3D.
        offset     = np.array(self.offset[:] + [0])
        xlen, ylen = glroutines.adjust(b.xlen, b.ylen, w, h)
        offset[0]  = xlen * offset[0] / w
        offset[1]  = ylen * offset[1] / h
        offset     = transform.scaleOffsetXform(1, offset)

        # And finally the camera.
        eye     = list(centre)
        eye[1] -= 1
        up      = [0, 0, 1]
        camera  = glroutines.lookAt(eye, centre, up)

        # Order is very important!
        return transform.concat(offset, scale, camera, rotate)


    def __setViewport(self):
        """Called by :meth:`_draw`. Configures the viewport and model-view
        trasformatiobn matrix.

        :returns: ``True`` if the viewport was successfully configured,
                  ``False`` otherwise.
        """

        width, height = self._getSize()

        if width == 0 or height == 0:
            return False

        b   = self.__displayCtx.bounds
        blo = [b.xlo, b.ylo, b.zlo]
        bhi = [b.xhi, b.yhi, b.zhi]

        if np.any(np.isclose(blo, bhi)):
            return False

        # We save the transform so it
        # can be used by canvasToWorld
        self.__xform = self.__genModelViewMatrix()

        glroutines.show3D(width, height, blo, bhi, self.__xform)

        return True


    def _draw(self):
        """
        """

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
