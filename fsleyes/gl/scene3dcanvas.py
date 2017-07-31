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

import fsl.utils.transform as transform

import fsleyes.gl.routines as glroutines
import fsleyes.gl.globject as globject
import fsleyes.displaycontext.canvasopts as canvasopts


log = logging.getLogger(__name__)

class Scene3DCanvas(props.HasProperties):


    pos           = copy.copy(canvasopts.Scene3DCanvasOpts.pos)
    showCursor    = copy.copy(canvasopts.Scene3DCanvasOpts.showCursor)
    cursorColour  = copy.copy(canvasopts.Scene3DCanvasOpts.cursorColour)
    bgColour      = copy.copy(canvasopts.Scene3DCanvasOpts.bgColour)
    showLegend    = copy.copy(canvasopts.Scene3DCanvasOpts.showLegend)
    occlusion     = copy.copy(canvasopts.Scene3DCanvasOpts.occlusion)
    fadeOut       = copy.copy(canvasopts.Scene3DCanvasOpts.fadeOut)
    light         = copy.copy(canvasopts.Scene3DCanvasOpts.light)
    lightPos      = copy.copy(canvasopts.Scene3DCanvasOpts.lightPos)
    zoom          = copy.copy(canvasopts.Scene3DCanvasOpts.zoom)
    offset        = copy.copy(canvasopts.Scene3DCanvasOpts.offset)
    rotation      = copy.copy(canvasopts.Scene3DCanvasOpts.rotation)


    def __init__(self, overlayList, displayCtx):

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(self.__class__.__name__, id(self))
        self.__viewMat     = np.eye(4)
        self.__projMat     = np.eye(4)

        self.__glObjects   = {}

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        displayCtx.addListener('bounds',
                               self.__name,
                               self.__displayBoundsChanged)

        self.addListener('pos',          self.__name, self.Refresh)
        self.addListener('showCursor',   self.__name, self.Refresh)
        self.addListener('cursorColour', self.__name, self.Refresh)
        self.addListener('bgColour',     self.__name, self.Refresh)
        self.addListener('showLegend',   self.__name, self.Refresh)
        self.addListener('occlusion',    self.__name, self.Refresh)
        self.addListener('fadeOut',      self.__name, self.Refresh)
        self.addListener('zoom',         self.__name, self.Refresh)
        self.addListener('offset',       self.__name, self.Refresh)
        self.addListener('rotation',     self.__name, self.Refresh)


    def destroy(self):
        self.__overlayList.removeListener('overlays', self.__name)
        self.__displayCtx .removeListener('bounds',   self.__name)


    def getViewMatrix(self):
        return self.__viewMat


    def getViewScale(self):
        return self.__viewScale


    def getViewOffset(self):
        return self.__viewOffset


    def getViewRotation(self):
        return self.__viewRotate


    def getViewCamera(self):
        return self.__viewCamera


    def getProjectionMatrix(self):
        return self.__projMat


    def getGLObject(self, overlay):
        return self.__glObjects.get(overlay, None)


    def getGLObjects(self):

        from fsl.data.mesh  import TriangleMesh
        from fsl.data.image import Image

        overlays  = self.__displayCtx.getOrderedOverlays()

        surfs = [o for o in overlays if isinstance(o, TriangleMesh)]
        vols  = [o for o in overlays if isinstance(o, Image)]
        other = [o for o in overlays if o not in surfs and o not in vols]

        overlays = []
        globjs   = []
        for ovl in surfs + vols + other:
            globj = self.getGLObject(ovl)

            if globj is not None:
                overlays.append(ovl)
                globjs  .append(globj)

        return overlays, globjs


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
        xform = transform.invert(self.__viewMat)
        pos   = transform.transform(pos, xform)

        return pos


    def _initGL(self):
        self.__overlayListChanged()


    def __overlayListChanged(self, *a):
        """
        """

        # Destroy any GL objects for overlays
        # which are no longer in the list
        for ovl, globj in list(self.__glObjects.items()):
            if ovl not in self.__overlayList:
                self.__glObjects.pop(ovl)
                if globj:
                    globj.deregister(self.__name)
                    globj.destroy()

        # Create a GL object for any new overlays,
        # and attach a listener to their display
        # properties so we know when to refresh
        # the canvas.
        for overlay in self.__overlayList:

            # A GLObject already exists
            # for this overlay
            if overlay in self.__glObjects:
                continue

            globj = globject.createGLObject(overlay,
                                            self.__displayCtx,
                                            self,
                                            True)

            globj.register(self.__name, self.Refresh)
            self.__glObjects[overlay] = globj


    def __getGLObjects(self):
        pass


    def __displayBoundsChanged(self, *a):

        b        = self.__displayCtx.bounds
        centre = np.array([b.xlo + 0.5 * (b.xhi - b.xlo),
                           b.ylo + 0.5 * (b.yhi - b.ylo),
                           b.zlo + 0.5 * (b.zhi - b.zlo)])

        self.lightPos = centre + [b.xlen, b.ylen, 0]

        self.Refresh()


    def __genViewMatrix(self):
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
        eye[1] += 1
        up      = [0, 0, 1]
        camera  = glroutines.lookAt(eye, centre, up)

        # Order is very important!
        xform = transform.concat(offset, scale, camera, rotate)
        np.array(xform, dtype=np.float32)

        self.__viewOffset = offset
        self.__viewScale  = scale
        self.__viewRotate = rotate
        self.__viewCamera = camera
        self.__viewMat    = xform


    def __setViewport(self):
        """Called by :meth:`_draw`. Configures the viewport and calculates
        the model-view trasformation matrix.

        :returns: ``True`` if the viewport was successfully configured,
                  ``False`` otherwise.
        """

        width, height = self._getSize()
        b             = self.__displayCtx.bounds
        blo           = [b.xlo, b.ylo, b.zlo]
        bhi           = [b.xhi, b.yhi, b.zhi]
        zoom          = self.zoom / 100.0

        if width == 0 or height == 0:    return False
        if np.any(np.isclose(blo, bhi)): return False

        # Generate the view and projection matrices
        self.__genViewMatrix()
        self.__projMat = glroutines.ortho(blo, bhi, width, height, zoom)

        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(self.__projMat.ravel('F'))
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        return True


    def _draw(self):
        """
        """

        if not self._setGLContext():
            return

        if not self.__setViewport():
            return

        glroutines.clear(self.bgColour)

        if len(self.__overlayList) == 0:
            return

        # If occlusion is on, we offset the
        # depth of each overlay so that, where
        # a depth collision occurs, overlays
        # which are higher in the list will get
        # drawn above lower ones.
        depthOffset = transform.scaleOffsetXform(1, [0, 0, 0.1])
        xform       = self.__viewMat

        overlays, globjs = self.getGLObjects()

        if self.showCursor: self.__drawCursor()

        for ovl, globj in zip(overlays, globjs):

            if not self.occlusion:
                gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

            display = self.__displayCtx.getDisplay(ovl)

            if not globj.ready():
                continue
            if not display.enabled:
                continue

            if self.occlusion:
                xform = transform.concat(depthOffset, xform)

            globj.preDraw( xform=xform)
            globj.draw3D(  xform=xform)
            globj.postDraw(xform=xform)

        self.__drawBoundingBox()

        self.__drawLight()
        if self.showLegend:
            self.__drawLegend()


    def __drawCursor(self):

        b   = self.__displayCtx.bounds
        pos = self.pos

        points = np.array([
            [pos.x, pos.y, b.zlo],
            [pos.x, pos.y, b.zhi],
            [pos.x, b.ylo, pos.z],
            [pos.x, b.yhi, pos.z],
            [b.xlo, pos.y, pos.z],
            [b.xhi, pos.y, pos.z],
        ], dtype=np.float32)
        points = transform.transform(points, self.__viewMat)
        gl.glLineWidth(1)

        r, g, b = self.cursorColour[:3]

        gl.glColor4f(r, g, b, 1)
        gl.glBegin(gl.GL_LINES)
        for p in points:
            gl.glVertex3f(*p)
        gl.glEnd()


    def __drawLight(self):

        lightPos  = np.array(self.lightPos)
        lightPos *= (self.zoom / 100.0)

        gl.glColor4f(1, 1, 1, 1)
        gl.glPointSize(10)
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex3f(*lightPos)
        gl.glEnd()

        b = self.__displayCtx.bounds
        centre = np.array([b.xlo + 0.5 * (b.xhi - b.xlo),
                           b.ylo + 0.5 * (b.yhi - b.ylo),
                           b.zlo + 0.5 * (b.zhi - b.zlo)])

        centre = transform.transform(centre, self.__viewMat)

        gl.glColor4f(1, 0, 1, 1)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(*lightPos)
        gl.glVertex3f(*centre)
        gl.glEnd()


    def __drawBoundingBox(self):
        b = self.__displayCtx.bounds
        xlo, xhi = b.x
        ylo, yhi = b.y
        zlo, zhi = b.z
        xlo += 0.1
        xhi -= 0.1
        vertices = np.array([
            [xlo, ylo, zlo],
            [xlo, ylo, zhi],
            [xlo, yhi, zlo],
            [xlo, yhi, zhi],
            [xhi, ylo, zlo],
            [xhi, ylo, zhi],
            [xhi, yhi, zlo],
            [xhi, yhi, zhi],

            [xlo, ylo, zlo],
            [xlo, yhi, zlo],
            [xhi, ylo, zlo],
            [xhi, yhi, zlo],
            [xlo, ylo, zhi],
            [xlo, yhi, zhi],
            [xhi, ylo, zhi],
            [xhi, yhi, zhi],

            [xlo, ylo, zlo],
            [xhi, ylo, zlo],
            [xlo, ylo, zhi],
            [xhi, ylo, zhi],
            [xlo, yhi, zlo],
            [xhi, yhi, zlo],
            [xlo, yhi, zhi],
            [xhi, yhi, zhi],
        ])
        vertices = transform.transform(vertices, self.__viewMat)


        gl.glLineWidth(2)
        gl.glColor3f(0.5, 0, 0)
        gl.glBegin(gl.GL_LINES)
        for v in vertices:
            gl.glVertex3f(*v)
        gl.glEnd()


    def __drawLegend(self):
        """Draws a legend in the bottom left corner of the screen, showing
        anatomical orientation.
        """

        b          = self.__displayCtx.bounds
        w, h       = self._getSize()
        xlen, ylen = glroutines.adjust(b.xlen, b.ylen, w, h)

        # A line for each axis
        vertices       = np.zeros((6, 3), dtype=np.float32)
        vertices[0, :] = [-1,  0,  0]
        vertices[1, :] = [ 1,  0,  0]
        vertices[2, :] = [ 0, -1,  0]
        vertices[3, :] = [ 0,  1,  0]
        vertices[4, :] = [ 0,  0, -1]
        vertices[5, :] = [ 0,  0,  1]

        # Each axis line is scaled to
        # 60 pixels, and the legend is
        # offset from the bottom-left
        # corner by twice this amount.
        scale      = [xlen * 30.0 / w] * 3
        offset     = [-0.5 * xlen + 2.0 * scale[0],
                      -0.5 * ylen + 2.0 * scale[1],
                       0]

        # Apply the current camera
        # angle and rotation settings
        # to the legend vertices. Offset
        # anatomical labels off each
        # axis line by a small amount.
        rotation   = transform.decompose(self.__viewMat)[2]
        xform      = transform.compose(scale, offset, rotation)
        labelPoses = transform.transform(vertices * 1.2, xform)
        vertices   = transform.transform(vertices,       xform)

        # Draw the legend lines
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glColor3f(*self.cursorColour[:3])
        gl.glLineWidth(2)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(*vertices[0])
        gl.glVertex3f(*vertices[1])
        gl.glVertex3f(*vertices[2])
        gl.glVertex3f(*vertices[3])
        gl.glVertex3f(*vertices[4])
        gl.glVertex3f(*vertices[5])
        gl.glEnd()


        # Figure out the anatomical
        # labels for each axis.
        overlay = self.__displayCtx.getSelectedOverlay()
        opts    = self.__displayCtx.getOpts(overlay)
        labels  = opts.getLabels()[0]

        # getLabels returns (xlo, ylo, zlo, xhi, yhi, zhi) -
        # - rearrange them to (xlo, xhi, ylo, yhi, zlo, zhi)
        labels = [labels[0],
                  labels[3],
                  labels[1],
                  labels[4],
                  labels[2],
                  labels[5]]

        canvas = np.array([w, h])
        view   = np.array([xlen, ylen])

        # Draw each label
        for i in range(6):

            # Calculate pixel x/y
            # location for this label
            xx, xy = canvas * (labelPoses[i, :2] + 0.5 * view) / view

            # Calculate the size of the label
            # in pixels, so we can centre the
            # label
            tw, th = glroutines.text2D(labels[i], (xx, xy), 10, (w, h),
                                       calcSize=True)

            # Draw the text
            xx -= 0.5 * tw
            xy -= 0.5 * th
            glroutines.text2D(labels[i], (xx, xy), 10, (w, h))
