#!/usr/bin/env python
#
# scene3dcanvas.py - The Scene3DCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.Scene3DCanvas` class, which is used by
FSLeyes for its 3D view.
"""


import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.data.mesh       as fslmesh
import fsl.data.image      as fslimage
import fsl.utils.idle      as idle
import fsl.utils.transform as transform

import fsleyes.gl.routines               as glroutines
import fsleyes.gl.globject               as globject
import fsleyes.displaycontext            as fsldisplay
import fsleyes.displaycontext.canvasopts as canvasopts


log = logging.getLogger(__name__)


class Scene3DCanvas(object):


    def __init__(self, overlayList, displayCtx):

        self.__name           = '{}_{}'.format(type(self).__name__, id(self))
        self.__opts           = canvasopts.Scene3DCanvasOpts()
        self.__overlayList    = overlayList
        self.__displayCtx     = displayCtx
        self.__viewMat        = np.eye(4)
        self.__projMat        = np.eye(4)
        self.__invViewProjMat = np.eye(4)
        self.__viewport       = None
        self.__resetLightPos  = True
        self.__glObjects      = {}

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        displayCtx.addListener('bounds',
                               self.__name,
                               self.__displayBoundsChanged)

        opts = self.opts
        opts.addListener('pos',          self.__name, self.Refresh)
        opts.addListener('showCursor',   self.__name, self.Refresh)
        opts.addListener('cursorColour', self.__name, self.Refresh)
        opts.addListener('bgColour',     self.__name, self.Refresh)
        opts.addListener('showLegend',   self.__name, self.Refresh)
        opts.addListener('occlusion',    self.__name, self.Refresh)
        opts.addListener('zoom',         self.__name, self.Refresh)
        opts.addListener('offset',       self.__name, self.Refresh)
        opts.addListener('rotation',     self.__name, self.Refresh)
        opts.addListener('highDpi',      self.__name, self.__highDpiChanged)


    def destroy(self):
        """
        """
        self.__overlayList.removeListener('overlays', self.__name)
        self.__displayCtx .removeListener('bounds',   self.__name)

        for ovl in list(self.__glObjects.keys()):
            self.__deregisterOverlay(ovl)

        self.__opts        = None
        self.__displayCtx  = None
        self.__overlayList = None
        self.__glObjects   = None


    def destroyed(self):
        """
        """
        return self.__overlayList is None


    @property
    def opts(self):
        """Returns a reference to the :class:`.Scene3DCanvasOpts` instance.
        """
        return self.__opts

    @property
    def resetLightPos(self):
        """By default, the :attr:`lightPos` is updated whenever the
        :attr:`.DisplayContext.bounds` change. This flag can be used to
        disable this behaviour.
        """
        return self.__resetLightPos


    @resetLightPos.setter
    def resetLightPos(self, reset):
        """Control whether the :attr:`lightPos` property is reset whenever
        the :attr:`.DisplayContext.bounds` change.
        """
        self.__resetLightPos = reset


    def defaultLightPos(self):
        """Resets the :attr:`lightPos` property to a sensible value. """
        b      = self.__displayCtx.bounds
        centre = np.array([b.xlo + 0.5 * (b.xhi - b.xlo),
                           b.ylo + 0.5 * (b.yhi - b.ylo),
                           b.zlo + 0.5 * (b.zhi - b.zlo)])
        self.opts.lightPos = centre + [b.xlen, b.ylen, 0]


    @property
    def viewMatrix(self):
        """Returns the view matrix for the current scene - this is an affine
        matrix which encodes the current :attr:`.Scene3DCanvasOpts.offset`,
        :attr:`.Scene3DCanvasOpts.zoom`,
        :attr:`.Scene3DCanvasOpts.rotation` and camera settings.

        See :meth:`__genViewMatrix`.
        """
        return self.__viewMat


    @property
    def viewScale(self):
        """Returns an affine matrix which encodes the current
        :attr:`.Scene3DCanvasOpts.zoom` setting.
        """
        return self.__viewScale


    @property
    def viewOffset(self):
        """Returns an affine matrix which encodes the current
        :attr:`.Scene3DCanvasOpts.offset` setting.
        """
        return self.__viewOffset


    @property
    def viewRotation(self):
        """Returns an affine matrix which encodes the current
        :attr:`.Scene3DCanvasOpts.rotation` setting.
        """
        return self.__viewRotate


    @property
    def viewCamera(self):
        """Returns an affine matrix which encodes the current camera.
        transformation. The initial camera orientation in the view shown by a
        :class:`Scene3DCanvas` is located on the positive Y axis, is oriented
        towards the positive Z axis, and is pointing towards the centre of the
        :attr:`.DisplayContext.displayBounds`.
        """
        return self.__viewCamera


    @property
    def projectionMatrix(self):
        """Returns the projection matrix. This is an affine matrix which
        converts from normalised device coordinates (NDCs, coordinates between
        -1 and +1) into viewport coordinates. The initial viewport for a
        :class:`Scene3DCanvas` is configured by the :func:`.routines.ortho`
        function.

        See :meth:`__setViewport`.
        """
        return self.__projMat


    @property
    def invViewProjectionMatrix(self):
        """Returns the inverse of the model-view-projection matrix, the
        equivalent of:

        ``invert(projectionMatrix * viewMatrix)``
        """
        return self.__invViewProjMat


    @property
    def viewport(self):
        """Returns a list of three ``(min, max)`` tuples which specify the
        viewport limits of the currently displayed scene.
        """
        return self.__viewport


    def canvasToWorld(self, xpos, ypos, near=True):
        """Transform the given x/y canvas coordinates into the display
        coordinate system. The calculated coordinates will be located on
        the near clipping plane.

        :arg near: If ``True`` (the default), the returned coordinate will
                   be located on the near clipping plane. Otherwise, the
                   coordinate will be located on the far clipping plane.
        """

        width, height = self.GetSize()

        # Normalise pixels to [-1, 1]
        xp = -1 + 2.0 * xpos / width
        yp = -1 + 2.0 * ypos / height

        # We set the Z coord so the resulting
        # coordinates will be located on either
        # the  near or clipping planes.
        if near: pos = [xp, yp, -1]
        else:    pos = [xp, yp,  1]

        # The first step is to convert mouse
        # coordinates from [-1, 1] to viewport
        # coodinates via the inverse projection
        # matrix.

        # The second step is to transform from
        # viewport coords into model-view coords.
        # This is easy - transform by the inverse
        # MV matrix.

        # We perform both of these steps in one
        # by concatenating then inverting the
        # view/projection matrices. This is
        # calculated and cached for us in the
        # __setViewport method.
        pos = transform.transform(pos, self.__invViewProjMat)

        return pos


    def getGLObject(self, overlay):
        """Returns the :class:`.GLObject` associated with the given overlay,
        or ``None`` if there is not one.
        """
        return self.__glObjects.get(overlay, None)


    def getGLObjects(self):
        """Returns two lists:

         - A list of overlays to be drawn
         - A list of corresponding :class:`GLObject` instances

        The lists are in the order that they should be drawn.

        This method also creates ``GLObject`` instances for any overlays
        in the :class:`.OverlayList` that do not have one.
        """

        overlays = self.__displayCtx.getOrderedOverlays()

        surfs = [o for o in overlays if isinstance(o, fslmesh.Mesh)]
        vols  = [o for o in overlays if isinstance(o, fslimage.Image)]
        other = [o for o in overlays if o not in surfs and o not in vols]

        overlays = []
        globjs   = []

        # If occlusion is on, we draw all surfaces first,
        # so they are on the scene regardless of volume
        # opacity.
        #
        # If occlusion is off, we draw all volumes
        # (without depth testing) first, and draw all
        # surfaces (with depth testing) afterwards.
        # In this way, the surfaces will be occluded
        # by the last drawn volume. I figure that this
        # is better than being occluded by *all* volumes,
        # regardless of depth or camera orientation.
        #
        # The one downside to this is that if a
        # transparent volume is in front of a surface,
        # the surface won't be shown.
        #
        # The only way to overcome this would be to
        # sort by depth on every render which, given
        # the possibility of volume clipping planes,
        # is a bit too complicated for my liking.
        if self.opts.occlusion: ovlOrder = surfs + vols + other
        else:                   ovlOrder = vols + surfs + other

        for ovl in ovlOrder:
            globj = self.getGLObject(ovl)

            # If there is no GLObject for this
            # overlay, create one, but don't
            # add it to the list (as creation
            # is done asynchronously).
            if globj is None:
                self.__registerOverlay(ovl)

            # Otherwise, if the value for this
            # overlay evaluates to False, that
            # means that it has been scheduled
            # for creation, but is not ready
            # yet.
            elif globj:
                overlays.append(ovl)
                globjs  .append(globj)

        return overlays, globjs


    def _initGL(self):
        """Called when the canvas is ready to be drawn on. """
        self.__overlayListChanged()
        self.__displayBoundsChanged()


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Destroys/creates
        :class:`.GLObject` instances as necessary.
        """

        # Destroy any GL objects for overlays
        # which are no longer in the list
        for ovl, globj in list(self.__glObjects.items()):
            if ovl not in self.__overlayList:
                self.__deregisterOverlay(ovl)

        # Create GLObjects for any
        # newly added overlays
        for ovl in self.__overlayList:
            if ovl not in self.__glObjects:
                self.__registerOverlay(ovl)


    def __highDpiChanged(self, *a):
        """Called when the :attr:`.Scene3DCanvasOpts.highDpi` property
        changes. Calls the :meth:`.GLCanvasTarget.EnableHighDPI` method.
        """
        self.EnableHighDPI(self.opts.highDpi)


    def __displayBoundsChanged(self, *a):
        """Called when the :attr:`.DisplayContext.bounds` change. Resets
        the :attr:`.Scene3DCanvasOpts.lightPos` property.
        """

        if self.resetLightPos:
            self.defaultLightPos()

        self.Refresh()


    def __registerOverlay(self, overlay):
        """
        """

        if not isinstance(overlay, (fslmesh.Mesh, fslimage.Image)):
            return

        log.debug('Registering overlay {}'.format(overlay))

        display = self.__displayCtx.getDisplay(overlay)

        if not self.__genGLObject(overlay):
            return

        display.addListener('enabled', self.__name, self.Refresh)
        display.addListener('overlayType',
                            self.__name,
                            self.__overlayTypeChanged)


    def __deregisterOverlay(self, overlay):
        """
        """

        log.debug('Deregistering overlay {}'.format(overlay))

        try:
            display = self.__displayCtx.getDisplay(overlay)
            display.removeListener('overlayType', self.__name)
            display.removeListener('enabled',     self.__name)
        except fsldisplay.InvalidOverlayError:
            pass

        globj = self.__glObjects.pop(overlay, None)

        if globj is not None:
            globj.deregister(self.__name)
            globj.destroy()


    def __genGLObject(self, overlay):
        """
        """

        if overlay in self.__glObjects:
            return False

        display = self.__displayCtx.getDisplay(overlay)

        if display.overlayType not in ('volume', 'mesh'):
            return False

        self.__glObjects[overlay] = False

        def create():

            if not self or self.destroyed():
                return

            if overlay not in self.__glObjects:
                return

            if not self._setGLContext():
                self.__glObjects.pop(overlay)
                return

            log.debug('Creating GLObject for {}'.format(overlay))

            globj = globject.createGLObject(overlay,
                                            self.__overlayList,
                                            self.__displayCtx,
                                            self,
                                            True)

            if globj is not None:
                globj.register(self.__name, self.Refresh)
                self.__glObjects[overlay] = globj

        idle.idle(create)
        return True


    def __overlayTypeChanged(self, value, valid, display, name):
        """
        """

        overlay = display.overlay
        globj   = self.__glObjects.pop(overlay, None)

        if globj is not None:
            globj.deregister(self.__name)
            globj.destroy()

        self.__genGLObject(overlay)
        self.Refresh()


    def __genViewMatrix(self, w, h):
        """Generate and return a transformation matrix to be used as the
        model-view matrix. This includes applying the current :attr:`zoom`,
        :attr:`rotation` and :attr:`offset` settings, and configuring
        the camera. This method is called by :meth:`__setViewport`.

        :arg w: Canvas width in pixels
        :arg h: Canvas height in pixels
        """

        opts   = self.opts
        b      = self.__displayCtx.bounds
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
        scale  = opts.zoom / 100.0
        scale  = transform.scaleOffsetXform([scale] * 3, 0)
        rotate = transform.rotMatToAffine(opts.rotation, centre)

        # The offset property is defined in x/y
        # pixels, normalised to [-1, 1]. We need
        # to convert them into viewport space,
        # where the horizontal axis maps to
        # (-xhalf, xhalf), and the vertical axis
        # maps to (-yhalf, yhalf). See
        # gl.routines.ortho.
        offset     = np.array(opts.offset[:] + [0])
        xlen, ylen = glroutines.adjust(b.xlen, b.ylen, w, h)
        offset[0]  = xlen * offset[0] / 2
        offset[1]  = ylen * offset[1] / 2
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

        width, height = self.GetScaledSize()
        b             = self.__displayCtx.bounds
        blo           = [b.xlo, b.ylo, b.zlo]
        bhi           = [b.xhi, b.yhi, b.zhi]
        zoom          = self.opts.zoom / 100.0

        if width == 0 or height == 0:
            return False

        # We allow one dimension to be
        # flat, so we can display 2D
        # meshes (e.g. flattened surfaces)
        if np.sum(np.isclose(blo, bhi)) > 1:
            return False

        # Generate the view and projection matrices
        self.__genViewMatrix(width, height)
        projmat, viewport     = glroutines.ortho(blo, bhi, width, height, zoom)
        self.__projMat        = projmat
        self.__viewport       = viewport
        self.__invViewProjMat = transform.concat(self.__projMat,
                                                 self.__viewMat)
        self.__invViewProjMat = transform.invert(self.__invViewProjMat)

        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(self.__projMat.ravel('F'))
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        return True


    def _draw(self):
        """Draws the scene to the canvas. """

        if not self._setGLContext():
            return

        opts = self.opts
        glroutines.clear(opts.bgColour)

        if not self.__setViewport():
            return

        overlays, globjs = self.getGLObjects()

        if len(overlays) == 0:
            return

        # If occlusion is on, we offset the
        # depth of each overlay so that, where
        # a depth collision occurs, overlays
        # which are higher in the list will get
        # drawn above (closer to the screen)
        # than lower ones.
        depthOffset = transform.scaleOffsetXform(1, [0, 0, 0.1])
        depthOffset = np.array(depthOffset,    dtype=np.float32, copy=False)
        xform       = np.array(self.__viewMat, dtype=np.float32, copy=False)

        for ovl, globj in zip(overlays, globjs):

            display = self.__displayCtx.getDisplay(ovl)

            if not globj.ready():
                continue
            if not display.enabled:
                continue

            if opts.occlusion:
                xform = transform.concat(depthOffset, xform)
            elif isinstance(ovl, fslimage.Image):
                gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

            log.debug('Drawing {} [{}]'.format(ovl, globj))

            globj.preDraw( xform=xform)
            globj.draw3D(  xform=xform)
            globj.postDraw(xform=xform)

        if opts.showCursor:
            with glroutines.enabled((gl.GL_DEPTH_TEST)):
                self.__drawCursor()

        if opts.showLegend:
            self.__drawLegend()

        # Testing click-to-near/far clipping plane transformation
        if hasattr(self, 'points'):
            colours = [(1, 0, 0, 1), (0, 0, 1, 1)]
            gl.glPointSize(5)

            gl.glBegin(gl.GL_LINES)
            for i, p in enumerate(self.points):
                gl.glColor4f(*colours[i % 2])
                p = transform.transform(p, self.viewMatrix)
                gl.glVertex3f(*p)
            gl.glEnd()


    def __drawCursor(self):
        """Draws three lines at the current :attr:`.DisplayContext.location`.
        """

        opts = self.opts
        b    = self.__displayCtx.bounds
        pos  = opts.pos

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

        r, g, b = opts.cursorColour[:3]

        gl.glColor4f(r, g, b, 1)
        gl.glBegin(gl.GL_LINES)
        for p in points:
            gl.glVertex3f(*p)
        gl.glEnd()


    def __drawLegend(self):
        """Draws a legend in the bottom left corner of the screen, showing
        anatomical orientation.
        """

        copts      = self.opts
        b          = self.__displayCtx.bounds
        w, h       = self.GetSize()
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
        gl.glColor3f(*copts.cursorColour[:3])
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
        dopts   = self.__displayCtx.getOpts(overlay)
        labels  = dopts.getLabels()[0]

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
            gl.glColor3f(*copts.legendColour[:3])
            glroutines.text2D(labels[i], (xx, xy), 10, (w, h))


    def __drawLight(self):

        opts      = self.opts
        lightPos  = np.array(opts.lightPos)
        lightPos *= (opts.zoom / 100.0)

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
