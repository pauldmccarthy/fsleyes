#!/usr/bin/env python
#
# scene3dcanvas.py - The Scene3DCanvas class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.Scene3DCanvas` class, which is used by
FSLeyes for its 3D view.

On each refresh the ``Scene3DCanvas`` draws each
overlay to an offscreen 2D texture.
For OpenGL 2.1 and newer, all of these textures are then blended together
according to their depth using a custom shader program.

For OpenGL 1.4, the textures are then just drawn directly to the screen
according to the current overlay order.
"""


import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.data.mesh        as fslmesh
import fsl.data.image       as fslimage
import fsl.utils.idle       as idle
import fsl.transform.affine as affine

import fsleyes.data.tractogram           as fsltractogram
import fsleyes.gl                        as fslgl
import fsleyes.gl.routines               as glroutines
import fsleyes.gl.globject               as globject
import fsleyes.gl.annotations            as annotations
import fsleyes.gl.shaders                as shaders
import fsleyes.gl.text                   as gltext
import fsleyes.gl.textures               as textures
import fsleyes.displaycontext            as fsldisplay
import fsleyes.displaycontext.canvasopts as canvasopts


log = logging.getLogger(__name__)


class Scene3DCanvas:
    """The ``Scene3DCanvas`` is an OpenGL canvas used to draw overlays in a 3D
    view. Currently only ``volume``, ``mesh``, and ``tractogram`` overlay
    types are supported.
    """

    def __init__(self, overlayList, displayCtx):

        self.__name           = '{}_{}'.format(type(self).__name__, id(self))
        self.__opts           = canvasopts.Scene3DCanvasOpts()
        self.__overlayList    = overlayList
        self.__displayCtx     = displayCtx
        self.__annotations    = annotations.Annotations(self)
        self.__viewMat        = np.eye(4)
        self.__projMat        = np.eye(4)
        self.__invViewProjMat = np.eye(4)
        self.__viewport       = None
        self.__resetLightPos  = True

        # Dictionary of GLObjects and off-screen
        # RenderTextures for every overlay
        self.__glObjects      = {}
        self.__globjTextures  = {}

        # Shader program used to blend overlays,
        # only used for OpenGL >= 2.1. The number
        # of overlays that the shader program can
        # blend is hard-coded, so we maintain a
        # a set of them, one for each possible
        # number of overlays.
        #
        # n.b. It should be possible to do this
        # this for GL14, but would require a
        # sorting algorithm to be implemented
        # in ARB assembly, so has been left as
        # a possible future task.
        self.__shaders = {}
        self.__compileShaders()

        # gl.text.Text objects containing anatomical
        # orientation labels ordered
        # (xlo, xhi, ylo, yhi, zlo, zhi) where xyz
        # are the display coordinate system axes.
        # Created in __refreshLegendLabels
        self.__legendLabels = None

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        displayCtx.addListener('bounds',
                               self.__name,
                               self.__displayBoundsChanged)

        displayCtx.addListener('overlayOrder', self.__name, self.Refresh)

        opts = self.opts
        opts.addListener('pos',           self.__name, self.Refresh)
        opts.addListener('showCursor',    self.__name, self.Refresh)
        opts.addListener('cursorColour',  self.__name, self.Refresh)
        opts.addListener('bgColour',      self.__name, self.Refresh)
        opts.addListener('showLegend',    self.__name, self.Refresh)
        opts.addListener('legendColour',  self.__name,
                         self.__refreshLegendLabels)
        opts.addListener('labelSize',     self.__name,
                         self.__refreshLegendLabels)
        opts.addListener('zoom',          self.__name, self.Refresh)
        opts.addListener('offset',        self.__name, self.Refresh)
        opts.addListener('rotation',      self.__name, self.Refresh)
        opts.addListener('showLight',     self.__name, self.Refresh)
        opts.addListener('light',         self.__name, self.Refresh)
        opts.addListener('lightPos',      self.__name, self.Refresh)
        opts.addListener('lightDistance', self.__name, self.Refresh)


    def __compileShaders(self):
        """(Re-)compiles the shader programs which are used to blend overlays
        together. The shader programs are only used for OpenGL 2.1 and newer.

        This method is called every time the overlay list changes as the
        number of overlays is hard-coded into the shader programs.
        """

        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            return

        noverlays = len(self.__overlayList)
        if noverlays == 0:
            return

        vertSrc = shaders.getVertexShader(  'scene3dcanvas')
        fragSrc = shaders.getFragmentShader('scene3dcanvas')

        # We maintain separate shader prorgams
        # for any possible number of overlays
        # (as not all loaded overlays may be
        # displayed)
        for n in range(1, noverlays + 1):
            if n in self.__shaders:
                continue

            env    = {'noverlays' : n}
            shader = shaders.GLSLShader(vertSrc, fragSrc, constants=env)
            self.__shaders[n] = shader

            with shader.loaded():
                for i in range(n):
                    shader.set(f'rgba_{i}',  i * 2)
                    shader.set(f'depth_{i}', i * 2 + 1)


    def destroy(self):
        """Must be called when this Scene3DCanvas is no longer used. """

        if self.destroyed:
            return

        self.__overlayList.removeListener('overlays', self.__name)
        self.__displayCtx .removeListener('bounds',   self.__name)

        for ovl in list(self.__glObjects.keys()):
            self.__deregisterOverlay(ovl)

        if self.__legendLabels is not None:
            for lbl in self.__legendLabels:
                lbl.destroy()

        self.__annotations.destroy()

        for shader in self.__shaders.values():
            shader.destroy()

        self.__annotations  = None
        self.__shaders      = None
        self.__opts         = None
        self.__displayCtx   = None
        self.__overlayList  = None
        self.__glObjects    = None
        self.__legendLabels = None


    @property
    def destroyed(self):
        """Returns ``True`` if :meth:`destroy` has been called. """
        return self.__overlayList is None


    @property
    def opts(self):
        """Returns a reference to the :class:`.Scene3DCanvasOpts` instance.
        """
        return self.__opts


    @property
    def displayCtx(self):
        """Returns a reference to the :class:`.DisplayContext` for this canvas.
        """
        return self.__displayCtx


    def getAnnotations(self):
        """Return the :class:`.Annotations` object, for drawing annotations
        on this ``Scene3DCanvas``.
        """
        return self.__annotations


    @property
    def lightPos(self):
        """Takes the values of :attr:`.Scene3DOpts.lightPos` and
        :attr:`.Scene3DOpts.lightDistance`, and converts it to a position in
        the display coordinate system. The ``Scene3DOpts.lightPos`` property
        contains rotations about the centre of the display bounding box,
        and the :attr:`.Scene3DOpts.lightDistance` property specifies the
        distance of the light from the bounding box centre.
        """
        b        = self.__displayCtx.bounds
        centre   = np.array([b.xlo + 0.5 * (b.xhi - b.xlo),
                             b.ylo + 0.5 * (b.yhi - b.ylo),
                             b.zlo + 0.5 * (b.zhi - b.zlo)])

        yaw, pitch, roll = self.opts.lightPos
        distance         = self.opts.lightDistance
        yaw              = yaw   * np.pi / 180
        pitch            = pitch * np.pi / 180
        roll             = roll  * np.pi / 180

        rotmat = affine.axisAnglesToRotMat(pitch, roll, yaw)
        xform  = affine.compose([1, 1, 1],
                                [0, 0, 0],
                                rotmat,
                                origin=centre)

        lightPos = centre + [0, 0, distance * b.zlen]
        lightPos = affine.transform(lightPos, xform)

        return lightPos


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
        self.opts.lightPos = [0, 0, 0]


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
        :class:`Scene3DCanvas` is configured by the :func:`.routines.ortho3D`
        function.

        See :meth:`__setViewport`.
        """
        return self.__projMat


    @property
    def mvpMatrix(self):
        """Returns the current model*view*projection matrix. """
        return affine.concat(self.__projMat, self.__viewMat)


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


    def pixelSize(self):
        """Returns the (approximate) size (as a tuple containing
        ``(width, height)`` of one pixel in the display coordinate system.
        """

        # The right thing to do would be to transform
        # a vector by the inverse mvp matrix. But just
        # using the initial X/Y bounds (before
        # rotatoin/scaling), then applying the zoom/
        # scaling factor should work.
        w, h     = self.GetSize()
        zoom     = self.viewScale[0, 0]
        xlo, xhi = self.viewport[0]
        ylo, yhi = self.viewport[1]

        pw = (xhi - xlo) / zoom / w
        ph = (yhi - ylo) / zoom / h

        return pw, ph


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
        pos = affine.transform(pos, self.__invViewProjMat)

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

        This method also creates ``GLObject`` instances for any overlays
        in the :class:`.OverlayList` that do not have one.
        """

        # Sort the overlays so that volumes come last.
        # This will normally makes no difference (when
        # using OpenGL >= 2.1), but is important in
        # OpenGL 1.4 fallback mode to get somewhat
        # sensible blending.
        overlays = self.__displayCtx.getOrderedOverlays()
        vols     = [o for o in overlays if isinstance(o, fslimage.Image)]
        others   = [o for o in overlays if o not in vols]

        overlays = []
        globjs   = []

        for ovl in others + vols:
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

        self.__compileShaders()
        self.__refreshLegendLabels(refresh=False)


    def __refreshLegendLabels(self, *a, refresh=True):
        """Called when the legend labels (anatomical orientations) need
        to be refreshed - when the selected overlay changes, or when
        the :attr:`.Scene3DCanvasOpts.legendColour` is changed.
        """

        # Update legend labels. Figure out the
        # anatomical labels for each axis.
        overlay = self.__displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        if self.__legendLabels is None:
            self.__legendLabels = [gltext.Text(coordinates='pixels')
                                   for _ in range(6)]

        dopts  = self.__displayCtx.getOpts(overlay)
        labels = dopts.getLabels()[0]

        # getLabels returns (xlo, ylo, zlo, xhi, yhi, zhi) -
        # - rearrange them to (xlo, xhi, ylo, yhi, zlo, zhi)
        labels = [labels[0],
                  labels[3],
                  labels[1],
                  labels[4],
                  labels[2],
                  labels[5]]

        for label, text in zip(labels, self.__legendLabels):
            text.text     = label
            text.colour   = self.opts.legendColour
            text.fontSize = self.opts.labelSize
            text.halign   = 'centre'
            text.valign   = 'centre'

        if refresh:
            self.Refresh()


    def __displayBoundsChanged(self, *a):
        """Called when the :attr:`.DisplayContext.bounds` change. Resets
        the :attr:`.Scene3DCanvasOpts.lightPos` property.
        """

        if self.resetLightPos:
            self.defaultLightPos()

        self.Refresh()


    def __registerOverlay(self, overlay):
        """Called when a new overlay has been added to the overlay list.
        Creates a ``GLObject`` for it, and registers property listeners.
        """

        if not isinstance(overlay, (fslmesh.Mesh,
                                    fslimage.Image,
                                    fsltractogram.Tractogram)):
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
        """Called when an overlay has been removed from the overlay list.
        Dstroys the ``GLObject`` for it, and de-registers property listeners.
        """

        log.debug('Deregistering overlay {}'.format(overlay))

        try:
            display = self.__displayCtx.getDisplay(overlay)
            display.removeListener('overlayType', self.__name)
            display.removeListener('enabled',     self.__name)
        except fsldisplay.InvalidOverlayError:
            pass

        globj = self.__glObjects    .pop(overlay, None)
        tex   = self.__globjTextures.pop(overlay, None)

        if globj is not None:
            globj.deregister(self.__name)
            globj.destroy()
        if tex is not None:
            tex.destroy()


    def __genGLObject(self, overlay):
        """Create a ``GLObject`` for the given overlay, if one doesn't already
        exist.
        """

        if overlay in self.__glObjects:
            return False

        display = self.__displayCtx.getDisplay(overlay)

        if display.overlayType not in ('volume', 'mesh', 'tractogram'):
            return False

        self.__glObjects[overlay] = False

        def create():

            if not self or self.destroyed:
                return

            if overlay not in self.__glObjects:
                return

            if not self._setGLContext():
                self.__glObjects.pop(overlay)
                return

            log.debug('Creating GLObject for %s', overlay)

            globj = globject.createGLObject(overlay,
                                            self.__overlayList,
                                            self.__displayCtx,
                                            True)

            if globj is not None:
                globj.register(self.__name, self.Refresh)
                tex = textures.RenderTexture(globj.name, 'cd')
                self.__globjTextures[overlay] = tex
                self.__glObjects[    overlay] = globj

        idle.idle(create)
        return True


    def __overlayTypeChanged(self, value, valid, display, name):
        """Called when the :attr:`.Display.overlayType` of an overlay
        has changed. Re-generates a :class:`.GLObject` for it.
        """

        overlay = display.overlay
        globj   = self.__glObjects    .pop(overlay, None)
        tex     = self.__globjTextures.pop(overlay, None)

        if globj is not None:
            globj.deregister(self.__name)
            globj.destroy()
        if tex is not None:
            tex.destroy()

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
        scale  = affine.scaleOffsetXform([scale] * 3, 0)
        rotate = affine.rotMatToAffine(opts.rotation, centre)

        # The offset property is defined in x/y
        # pixels, normalised to [-1, 1]. We need
        # to convert them into viewport space,
        # where the horizontal axis maps to
        # (-xhalf, xhalf), and the vertical axis
        # maps to (-yhalf, yhalf). See
        # gl.routines.ortho3D.
        offset     = np.array(opts.offset[:] + [0])
        xlen, ylen = glroutines.adjust(b.xlen, b.ylen, w, h)
        offset[0]  = xlen * offset[0] / 2
        offset[1]  = ylen * offset[1] / 2
        offset     = affine.scaleOffsetXform(1, offset)

        # And finally the camera. Typically
        # the Z axis is inferior-superior,
        # so we want that to be pointing up.
        eye     = list(centre)
        eye[1] += 1
        up      = [0, 0, 1]
        camera  = glroutines.lookAt(eye, centre, up)

        # Order is very important!
        xform = affine.concat(offset, scale, camera, rotate)
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
        projmat, viewport     = glroutines.ortho3D(blo, bhi,
                                                   width, height, zoom)
        self.__projMat        = projmat
        self.__viewport       = viewport
        self.__invViewProjMat = affine.concat(self.__projMat, self.__viewMat)
        self.__invViewProjMat = affine.invert(self.__invViewProjMat)

        return True


    def _draw(self):
        """Draws the scene to the canvas. """

        if self.destroyed:
            return

        if not self._setGLContext():
            return

        opts          = self.opts
        width, height = self.GetScaledSize()

        if not self.__setViewport():
            return

        overlays, globjs = self.getGLObjects()
        rtexs            = []

        if len(overlays) == 0:
            return

        # Draw each overlay to an
        # off-screen render texture.
        for ovl, globj in zip(overlays, globjs):

            rtex    = self.__globjTextures.get(ovl, None)
            display = self.__displayCtx.getDisplay(ovl)

            if not globj.ready():   continue
            if not display.enabled: continue
            if rtex is None:        continue

            log.debug('Drawing %s [%s]', ovl, globj)

            rtexs.append(rtex)
            with rtex.target():
                rtex.shape = width, height
                gl.glViewport(0, 0, width, height)

                # We draw each overlay to a separate offscreen
                # texture, then blend them together (along
                # with the canvas background colour) below.
                # We need to adjust the blend equation so
                # that the clear colour here does not affect
                # the colours from the overlay render, and that
                # alpha blending within the overlay render
                # (specifically w.r.t. tractograms, i.e.
                # transparent streamlines drawn on top of each
                # other) works correctly.
                #
                # I don't understand alpha blending well enough,
                # but these are some good resources:
                #   - http://www.realtimerendering.com/blog/gpus-prefer-premultiplication/
                #   - http://www.adriancourreges.com/blog/2017/05/09/beware-of-transparent-pixels/
                #   - https://developer.nvidia.com/content/alpha-blending-pre-or-not-pre
                #   - https://limnu.com/webgl-blending-youre-probably-wrong/
                glroutines.clear((0, 0, 0, 0))
                gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA,
                                       gl.GL_ONE_MINUS_SRC_ALPHA,
                                       gl.GL_ONE,
                                       gl.GL_ONE_MINUS_SRC_ALPHA)

                globj.preDraw()
                globj.draw3D(self)
                globj.postDraw()

        # draw those off-screen
        # textures to screen
        gl.glViewport(0, 0, width, height)
        glroutines.clear(opts.bgColour)

        texCoords = textures.Texture2D.generateTextureCoords()
        vertices  = np.array([[-1, -1, 0],
                              [-1,  1, 0],
                              [ 1, -1, 0],
                              [ 1, -1, 0],
                              [-1,  1, 0],
                              [ 1,  1, 0]], dtype=np.float32)

        # Use a shader program to sort overlays
        # by depth at every pixel, so they are
        # drawn from farthest to nearest.
        shader = self.__shaders.get(len(rtexs), None)
        if shader is not None:

            # For fragments of equal depth, the blending shader
            # will give precedence to the first one. This would
            # correspond to an overlay which is earlier in the
            # overlay list, whcih should be drawn on the bottom.
            # So here we flip the overlay order.
            for i, rtex in enumerate(reversed(rtexs)):
                rtex             .bindTexture(int(gl.GL_TEXTURE0) + i * 2)
                rtex.depthTexture.bindTexture(int(gl.GL_TEXTURE0) + i * 2 + 1)

            with shader.loaded(), glroutines.enabled(gl.GL_DEPTH_TEST):
                shader.set(   'bgColour', opts.bgColour)
                shader.setAtt('vertex',   vertices)
                shader.setAtt('texCoord', texCoords)
                shader.draw(gl.GL_TRIANGLES, 0, 6)

            for i, rtex in enumerate(rtexs):
                rtex             .unbindTexture()
                rtex.depthTexture.unbindTexture()

        # GL14 fallback - just draw the textures
        # directly to screen according to overlay
        # order (see getGLObjects - volumes are
        # always drawn last).
        else:
            with glroutines.enabled(gl.GL_DEPTH_TEST):
                for rtex in rtexs:
                    rtex.draw(vertices, useDepth=True)

        if opts.showCursor:
            self.__drawCursor()

        if opts.showLegend:
            self.__drawLegend()

        if opts.showLight:
            self.__drawLight()

        self.getAnnotations().draw3D()


    def __drawCursor(self):
        """Draws three lines at the current :attr:`.DisplayContext.location`.
        """

        opts  = self.opts
        b     = self.__displayCtx.bounds
        pos   = opts.pos
        annot = self.getAnnotations()
        args  = {'colour'    : opts.cursorColour[:3],
                 'lineWidth' : 1,
                 'occlusion' : True}

        annot.line(pos.x, pos.y, pos.x, pos.y, b.zlo, b.zhi, **args)
        annot.line(pos.x, b.ylo, pos.x, b.yhi, pos.z, pos.z, **args)
        annot.line(b.xlo, pos.y, b.xhi, pos.y, pos.z, pos.z, **args)


    def __drawLegend(self):
        """Draws a legend in the bottom left corner of the screen, showing
        anatomical orientation.
        """

        copts      = self.opts
        annot      = self.getAnnotations()
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
        rotation   = affine.decompose(self.viewMatrix)[2]
        labelxform = affine.compose(scale, offset, rotation)
        linexform  = affine.concat(self.projectionMatrix, labelxform)
        labelverts = affine.transform(vertices * 1.2, labelxform)
        lineverts  = affine.transform(vertices,       linexform)
        kwargs     = {
            'colour'    : copts.cursorColour[:3],
            'lineWidth' : 2,
            'occlusion' : False,
            'applyMvp'  : False
        }

        for i in [0, 2, 4]:
            x1, y1, z1 = lineverts[i,     :]
            x2, y2, z2 = lineverts[i + 1, :]
            annot.line(x1, y1, x2, y2, z1, z2, **kwargs)

        canvas = np.array([w, h])
        view   = np.array([xlen, ylen])

        # Draw each label
        for i, label in enumerate(self.__legendLabels):

            # Calculate pixel x/y
            # location for this label
            xx, xy    = canvas * (labelverts[i, :2] + 0.5 * view) / view
            label.pos = (xx, xy)
            label.draw(w, h)


    def __drawLight(self):
        """Draws a representation of the light source. """

        lightPos = self.lightPos
        annot    = self.getAnnotations()
        bounds   = self.__displayCtx.bounds
        centre   = np.array([bounds.xlo + 0.5 * (bounds.xhi - bounds.xlo),
                             bounds.ylo + 0.5 * (bounds.yhi - bounds.ylo),
                             bounds.zlo + 0.5 * (bounds.zhi - bounds.zlo)])

        lx, ly, lz = lightPos
        cx, cy, cz = centre

        annot.point(lx, ly, lz,             colour=(1, 1, 0), lineWidth=3)
        annot.line( lx, ly, cx, cy, lz, cz, colour=(1, 1, 0))
