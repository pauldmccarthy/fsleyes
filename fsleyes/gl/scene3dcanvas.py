#!/usr/bin/env python
#
# scene3dcanvas.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import logging

import OpenGL.GL as gl

import fsleyes_props as props

import fsl.data.mesh as fslmesh

import fsleyes.gl.routines as glroutines


log = logging.getLogger(__name__)

class Scene3DCanvas(props.HasProperties):


    # TODO figure  out what properties you need
    eyePosition = props.Point(ndims=3)
    centre      = props.Point(ndims=3)
    zoom        = props.Percentage(minval=1.0, maxval=5000.0, default=50.0, clamped=True)


    def __init__(self, overlayList, displayCtx):

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx

        overlayList.addListener('overlays', 'blob', self.__overlayListChanged)
        displayCtx.addListener('bounds', 'blob', self.__displayBoundsChanged)

        self.addListener('zoom', 'blob', self.__zoomChanged)


    def _initGL(self):
        self.__displayBoundsChanged()


    def canvasToWorld(self, xpos, ypos):

        # TODO
        return [0, 0, 0]


    def __overlayListChanged(self, *a):
        pass


    def __displayBoundsChanged(self, *a):

        b      = self.__displayCtx.bounds
        size   = max((b.xlen, b.ylen, b.zlen))
        centre = [
            b.xlo + b.xlen / 2.0,
            b.ylo + b.ylen / 2.0,
            b.zlo + b.zlen / 2.0]

        eye    = [centre[0], centre[1] - 4 * size, centre[2]]

        self.eyePosition = eye
        self.centre      = centre
        self.zoom        = 50


    def __zoomChanged(self, *args):
        pass


    def _draw(self):

        width, height = self._getSize()
        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        b      = self.__displayCtx.bounds
        lo     = [b.xlo, b.ylo, b.zlo]
        hi     = [b.xhi, b.yhi, b.zhi]
        up     = [0, 0, 1]

        glroutines.show3D(width,
                          height,
                          lo, hi,
                          self.eyePosition,
                          self.centre,
                          up)
        glroutines.clear((0, 0, 0, 1))


        for ovl in self.__overlayList:
            if not isinstance(ovl, fslmesh.TriangleMesh):
                continue

            import numpy as np

            verts = np.array(ovl.vertices, dtype=np.float32)
            idxs  = np.array(ovl.indices, dtype=np.uint32)

            opts = self.__displayCtx.getOpts(ovl)

            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            gl.glLineWidth(1)
            gl.glColor3f(*opts.colour[:3])

            with glroutines.enabled(gl.GL_VERTEX_ARRAY):
                gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts.ravel('C'))
                gl.glDrawElements(gl.GL_TRIANGLES, len(idxs), gl.GL_UNSIGNED_INT, idxs)
