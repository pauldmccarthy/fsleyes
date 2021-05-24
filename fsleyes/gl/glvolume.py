#!/usr/bin/env python
#
# glvolume.py - The GLVolume class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLVolume` class, which creates and
encapsulates the data and logic required to render 2D slice of an
:class:`.Image` instance.
"""


import logging

import numpy                     as np
import OpenGL.GL                 as gl

import fsl.utils.idle            as idle
import fsl.transform.affine      as affine
import fsleyes.gl                as fslgl
import fsleyes.gl.routines       as glroutines
import fsleyes.gl.shaders.filter as glfilter
from . import                       textures
from . import                       glimageobject
from . import resources          as glresources


log = logging.getLogger(__name__)


class GLVolume(glimageobject.GLImageObject):
    """The ``GLVolume`` class is a :class:`.GLImageObject` which encapsulates
    the data and logic required to render  :class:`.Image` overlays in 2D and
    3D.


    A ``GLVolume`` instance may be used to render an :class:`.Image` instance
    which has a :attr:`.Display.overlayType` equal to ``volume``. It is
    assumed that this ``Image`` instance is associated with a
    :class:`.Display` instance which, in turn, contains a :class:`.VolumeOpts`
    instance, containing display options specific to volume rendering.


    **Version dependent modules**


    The ``GLVolume`` class makes use of the functions defined in the
    :mod:`.gl14.glvolume_funcs` or the :mod:`.gl21.glvolume_funcs` modules,
    which provide OpenGL version specific details for creation/storage of
    vertex data, and for rendering.


    These version dependent modules must provide the following functions:

    ===================================== =====================================
    ``init(GLVolume)``                    Perform any necessary initialisation.

    ``destroy(GLVolume)``                 Perform any necessary clean up.

    ``compileShaders(GLVolume)``          (Re-)Compile the shader programs.

    ``updateShaderState(GLVolume)``       Updates the shader program states
                                          when display parameters are changed.

    ``preDraw(GLVolume, xform, bbox)``    Initialise the GL state, ready for
                                          drawing.

    ``draw2D(GLVolume, zpos, xform)``     Draw a slice of the image at the
                                          given ``zpos``. If ``xform`` is not
                                          ``None``, it must be applied as a
                                          transformation on the vertex
                                          coordinates.

    ``draw3D(GLVolume, xform, bbox)``     Draw the image in 3D. If ``xform``
                                          is not ``None``, it must be applied
                                          as a transformation on the vertex
                                          coordinates.

    ``drawAll(Glvolume, zposes, xforms)`` Draws slices at each of the
                                          specified ``zposes``, applying the
                                          corresponding ``xforms`` to each.

    ``postDraw(GLVolume, xform, bbox)``   Clear the GL state after drawing.
    ===================================== =====================================


    **2D rendering**


    Images are rendered in essentially the same way, regardless of which
    OpenGL version-specific module is used.  The image data itself is stored
    as an :class:`.ImageTexture`. This ``ImageTexture`` is managed by the
    :mod:`.resources` module, so may be shared by many ``GLVolume`` instances.
    The current colour maps (defined by the :attr:`.VolumeOpts.cmap` and
    :attr:`.VolumeOpts.negativeCmap` properties) are stored as
    :class:`.ColourMapTexture` instances.  A slice through the texture is
    rendered using six vertices, located at the respective corners of the
    image bounds.


    Image voxels may be clipped according to the
    :attr:`.VolumeOpts.clippingRange` property. By default, the voxel value
    is compared against the clipping range, but the
    :attr:`.VolumeOpts.clipImage` property allows the data from a different
    image (of the same dimensions) to be used for clipping. If specified,
    this clipping image is stored as another :class:`.ImageTexture`.


    If the :attr:`.ColourMapOpts.modulateAlpha` setting is active, the opacity
    of rendered voxels is modulated by the voxel intensity.  If
    :attr:`.VolumeOpts.modulateImage` is also set, the opacity is modulated by
    the values in a different image - in this case, this image is stored in
    another :class:`.ImageTexture`.

    An :class:`.AuxImageTextureManager` is used to manage the clip and modulate
    textures.


    **3D rendering**


    In 3D, images are rendered using a ray-casting approach. The image
    bounding box is drawn as a cuboid. Then for each pixel, a ray is cast
    from the 'camera' through the image texture. The resulting colour
    is generated from sampling points along the ray.

    The ``glvolume_funcs`` modules are expected to perform this rendering
    off-screen, using two :class:`.RenderTexture` instances, available as
    attributes ``renderTexture1`` and``renderTexture2``.  After a call to
    ``draw3D``, the final result is assuemd to be contained in
    ``renderTexture1``.


    **Textures**


    The ``GLVolume`` class uses the following textures:

     - An :class:`.ImageTexture`, a 3D texture which contains image data.
       This is bound to texture unit 0.

     - A :class:`.ColourMapTexture`, a 1D texture which contains the
       colour map defined by the :attr:`.VolumeOpts.cmap` property.
       This is bound to texture unit 1.

     - A :class:`.ColourMapTexture`, a 1D texture which contains the
       colour map defined by the :attr:`.VolumeOpts.negativeCmap` property.
       This is bound to texture unit 2.

     - An :class:`.ImageTexture` which contains the clippimg image data.
       This is bound to texture unit 3. If the :attr:`.VolumeOpts.clipImage`
       property is not specified (i.e. it has a value of ``None``), this
       texture will not be bound - in this case, the image texture is used
       for clipping.

     - Two :class:`.RenderTexture` instances which are used for 3D rendering.
       Both of these textures have depth buffers. When one of these textures
       is being drawn it is bound to texture units 4 (for RGBA) and 5 (for
       depth).


    **Attributes**


    The following attributes are available on a ``GLVolume`` instance:

    ==================== ==================================================
    ``imageTexture``     The :class:`.ImageTexture` which stores the image
                         data.
    ``clipTexture``      The :class:`.ImageTexture` which stores the clip
                         image data.
    ``modulateTexture``  The :class:`.ImageTexture` which stores the
                         modulate image data.
    ``colourTexture``    The :class:`.ColourMapTexture` used to store the
                         colour map.
    ``negColourTexture`` The :class:`.ColourMapTexture` used to store the
                         negative colour map.
    ``renderTexture1``   The first :class:`.RenderTexture` used for 3D
                         rendering.
    ``renderTexture2``   The first :class:`.RenderTexture` used for 3D
                         rendering.
    ``texName``          A name used for the ``imageTexture``,
                         ``colourTexture``, and ``negColourTexture`. The
                         name for the latter is suffixed with ``'_neg'``.
    ==================== ==================================================
    """


    def __init__(self, image, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLVolume`` object.

        :arg image:       An :class:`.Image` object.

        :arg overlayList: The :class:`.OverlayList`

        :arg displayCtx:  The :class:`.DisplayContext` object managing the
                          scene.

        :arg canvas:      The canvas doing the drawing.

        :arg threedee:    Set up for 2D or 3D rendering.
        """

        glimageobject.GLImageObject.__init__(self,
                                             image,
                                             overlayList,
                                             displayCtx,
                                             canvas,
                                             threedee)

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self.addDisplayListeners()

        # Create an image texture, clip texture, and a colour map texture
        #
        # We use the gl.resources module to manage texture
        # creation, because ImageTexture instances can
        # potentially be shared between GLVolumes. So all
        # GLVolumes use the same name, defined here, to
        # refer to the ImageTexture for a given image.
        self.texName  = '{}_{}'.format(type(self).__name__, id(self.image))

        # Ref to an OpenGL shader program -
        # the glvolume_funcs module will
        # create this for us.
        self.shader = None

        # aux texture manager takes care
        # of clip+modulate textures
        self.auxmgr = glimageobject.AuxImageTextureManager(
            self, clip=None, modulate=None)
        self.auxmgr.registerAuxImage('clip',     self.opts.clipImage)
        self.auxmgr.registerAuxImage('modulate', self.opts.modulateImage)

        # Refs to all of the texture objects.
        self.imageTexture     = None
        self.colourTexture    = textures.ColourMapTexture(self.texName)
        self.negColourTexture = textures.ColourMapTexture(
            '{}_neg'.format(self.texName))

        if self.threedee:

            self.smoothFilter = glfilter.Filter('smooth', texture=0)
            self.smoothFilter.set(kernSize=self.opts.smoothing * 2)

            self.renderTexture1 = textures.RenderTexture(
                self.name, interp=gl.GL_LINEAR, rttype='cd')
            self.renderTexture2 = textures.RenderTexture(
                self.name, interp=gl.GL_LINEAR, rttype='cd')

        # This attribute is used by the
        # updateShaderState method to
        # make sure that the Notifier.notify()
        # method gets called when needed.
        # See that method for details.
        self.__alwaysNotify = False

        self.refreshColourTextures()
        self.refreshImageTexture()

        # Call glvolume_funcs.init when the image
        # and clip textures are ready to be used.
        def init():

            # In some crazy circumstances,
            # a just-created GLVolume can
            # get destroyed immediately
            if not self.destroyed:
                fslgl.glvolume_funcs.init(self)
                self.notify()

        idle.idleWhen(init, self.texturesReady)


    def destroy(self):
        """This must be called when this :class:`GLVolume` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles), calls :meth:`removeDisplayListeners`,
        and calls :meth:`.GLImageObject.destroy`.
        """

        self.removeDisplayListeners()

        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.name)

        self.colourTexture   .destroy()
        self.negColourTexture.destroy()
        self.auxmgr          .destroy()

        self.auxmgr           = None
        self.imageTexture     = None
        self.colourTexture    = None
        self.negColourTexture = None

        if self.threedee:
            self.renderTexture1.destroy()
            self.renderTexture2.destroy()
            self.smoothFilter  .destroy()
            self.renderTexture1 = None
            self.renderTexture2 = None
            self.smoothFilter   = None

        fslgl.glvolume_funcs       .destroy(self)
        glimageobject.GLImageObject.destroy(self)


    def ready(self):
        """Returns ``True`` if this ``GLVolume`` is ready to be drawn,
        ``False`` otherwise.
        """
        return (not self.destroyed      and
                self.shader is not None and
                self.texturesReady())


    def texturesReady(self):
        """Returns ``True`` if the ``imageTexture`` and ``clipTexture`` (if
        applicable) are both ready to be used, ``False`` otherwise.
        """
        imageTexReady = (self.imageTexture is not None and
                         self.imageTexture.ready())
        return imageTexReady and self.auxmgr.texturesReady()


    @property
    def clipTexture(self):
        """Returns the :class:`.ImageTexture` associated with the
        :attr:`.VolumeOpts.clipImage`.
        """
        return self.auxmgr.texture('clip')


    @property
    def modulateTexture(self):
        """Returns the :class:`.ImageTexture` associated with the
        :attr:`.VolumeOpts.modulateImage`.
        """
        return self.auxmgr.texture('modulate')


    def addDisplayListeners(self):
        """Called by :meth:`__init__`.

        Adds a bunch of listeners to the :class:`.Display` object, and the
        associated :class:`.VolumeOpts` instance, which define how the image
        should be displayed.

        This is done so we can update the colour, vertex, and image data when
        display properties are changed.
        """

        display = self.display
        opts    = self.opts
        name    = self.name

        crPVs   = opts.getPropVal('clippingRange').getPropertyValueList()

        display .addListener('alpha',            name, self._alphaChanged)
        opts    .addListener('displayRange',     name,
                             self._displayRangeChanged)
        opts    .addListener('modulateRange',    name,
                             self._modulateRangeChanged)

        crPVs[0].addListener(name, self._lowClippingRangeChanged)
        crPVs[1].addListener(name, self._highClippingRangeChanged)

        opts    .addListener('clipImage',        name, self._clipImageChanged)
        opts    .addListener('modulateImage',    name,
                             self._modulateImageChanged)
        opts    .addListener('invertClipping',   name,
                             self._invertClippingChanged)
        opts    .addListener('cmap',             name, self._cmapChanged)
        opts    .addListener('gamma',            name, self._cmapChanged)
        opts    .addListener('logScale',         name, self._cmapChanged)
        opts    .addListener('interpolateCmaps', name, self._cmapChanged)
        opts    .addListener('negativeCmap',     name, self._cmapChanged)
        opts    .addListener('cmapResolution',   name, self._cmapChanged)
        opts    .addListener('useNegativeCmap',  name,
                             self._useNegativeCmapChanged)
        opts    .addListener('invert',           name, self._invertChanged)
        opts    .addListener('modulateAlpha',    name,
                             self._modulateAlphaChanged)
        opts    .addListener('volume',           name, self._volumeChanged)
        opts    .addListener('channel',          name, self._channelChanged)
        opts    .addListener('interpolation',    name,
                             self._interpolationChanged)
        opts    .addListener('transform',        name, self._transformChanged)
        opts    .addListener('displayXform',     name,
                             self._displayXformChanged)
        opts    .addListener('enableOverrideDataRange',  name,
                             self._enableOverrideDataRangeChanged)
        opts    .addListener('overrideDataRange', name,
                             self._overrideDataRangeChanged)

        # 3D-only options
        if self.threedee:

            opts.addListener('numSteps',        name, self._numStepsChanged)
            opts.addListener('numInnerSteps',   name,
                             self._numInnerStepsChanged)
            opts.addListener('resolution',      name,  self._resolutionChanged)
            opts.addListener('blendFactor',     name,
                             self._blendPropertiesChanged)
            opts.addListener('blendByIntensity', name,
                             self._blendPropertiesChanged)
            opts.addListener('smoothing',       name, self._smoothingChanged)
            opts.addListener('showClipPlanes',  name,
                             self._showClipPlanesChanged)
            opts.addListener('numClipPlanes',
                             name,
                             self._numClipPlanesChanged)
            opts.addListener('clipMode',        name, self._clipModeChanged)
            opts.addListener('clipPosition',    name, self._clipping3DChanged)
            opts.addListener('clipAzimuth',     name, self._clipping3DChanged)
            opts.addListener('clipInclination', name, self._clipping3DChanged)

        # GLVolume instances need to keep track of whether
        # the volume/channel properties of their corresponding
        # VolumeOpts instance is synced to other VolumeOpts
        # instances - if it is, there an ImageTexture for
        # the image may already exist (i.e. have been
        # created by another GLVolume), and we can just
        # re-use it. Otherwise we will need to create our
        # own ImageTexture.
        #
        # Save a flag so the removeDisplayListeners
        # method knows whether it needs to de-register
        # sync change listeners - using opts.getParent()
        # as the test in that method is dangerous, as
        # the DisplayOpts instance might have already
        # had its destroy method called on it, and might
        # have been detached from its parent.
        self.__syncListenersRegistered = opts.getParent() is not None

        if self.__syncListenersRegistered:
            opts.addSyncChangeListener('volume',
                                       name,
                                       self._imageSyncChanged)
            opts.addSyncChangeListener('channel',
                                       name,
                                       self._imageSyncChanged)


    def removeDisplayListeners(self):
        """Called by :meth:`destroy`. Removes all the property listeners that
        were added by :meth:`addDisplayListeners`.
        """

        display = self.display
        opts    = self.opts
        name    = self.name
        crPVs   = opts.getPropVal('clippingRange').getPropertyValueList()

        display .removeListener('alpha',                   name)
        opts    .removeListener('displayRange',            name)
        opts    .removeListener('modulateRange',           name)
        crPVs[0].removeListener(name)
        crPVs[1].removeListener(name)
        opts    .removeListener('clipImage',               name)
        opts    .removeListener('modulateImage',           name)
        opts    .removeListener('invertClipping',          name)
        opts    .removeListener('cmap',                    name)
        opts    .removeListener('gamma',                   name)
        opts    .removeListener('logScale',                name)
        opts    .removeListener('interpolateCmaps',        name)
        opts    .removeListener('negativeCmap',            name)
        opts    .removeListener('useNegativeCmap',         name)
        opts    .removeListener('cmapResolution',          name)
        opts    .removeListener('invert',                  name)
        opts    .removeListener('modulateAlpha',           name)
        opts    .removeListener('volume',                  name)
        opts    .removeListener('channel',                 name)
        opts    .removeListener('interpolation',           name)
        opts    .removeListener('transform',               name)
        opts    .removeListener('displayXform',            name)
        opts    .removeListener('enableOverrideDataRange', name)
        opts    .removeListener('overrideDataRange',       name)

        if self.threedee:
            opts.removeListener('numSteps',         name)
            opts.removeListener('numInnerSteps',    name)
            opts.removeListener('resolution',       name)
            opts.removeListener('blendFactor',      name)
            opts.removeListener('blendByIntensity', name)
            opts.removeListener('smoothing',        name)
            opts.removeListener('showClipPlanes',   name)
            opts.removeListener('numClipPlanes',    name)
            opts.removeListener('clipMode',         name)
            opts.removeListener('clipPosition',     name)
            opts.removeListener('clipAzimuth',      name)
            opts.removeListener('clipInclination',  name)

        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('volume',  name)
            opts.removeSyncChangeListener('channel', name)


    def testUnsynced(self):
        """Used by the :meth:`refreshImageTexture` method.

        Returns ``True`` if certain critical :class:`VolumeOpts` properties
        have been unsynced from the parent instance, meaning that this
        ``GLVolume`` instance needs to create its own image texture;
        returns ``False`` otherwise.
        """
        is4D  = len(self.image.shape) >= 4 and self.image.shape[3] > 1
        isRGB = self.image.nvals > 1

        return ((self.opts.getParent() is None)                      or
                (is4D  and not self.opts.isSyncedToParent('volume')) or
                (isRGB and not self.opts.isSyncedToParent('channel')))


    def updateShaderState(self, *args, **kwargs):
        """Calls :func:`.gl14.glvolume_funcs.updateShaderState` or
        :func:`.gl21.glvolume_funcs.updateShaderStatea`, then
        :meth:`.Notifier.notify`. Uses the :func:`.idle.idleWhen` function to
        make sure that it is not called until :meth:`ready` returns ``True``.

        :arg alwaysNotify: Must be passed as a keyword argument. If
                           ``False`` (the default), ``notify`` is only called
                           if ``glvolume_funcs.updateShaderState`` returns
                           ``True``. Otherwise, ``notify`` is always called.
        """

        alwaysNotify = kwargs.pop('alwaysNotify', None)

        # When alwaysNotify is True, we
        # set a flag on this GLVolume
        # instance to make sure that the
        # func() function below (which is
        # called asynchronously) gets
        # its value.
        #
        # We have to do this because this
        # updateShaderState method may be
        # called multiple times for a single
        # event, with different values of
        # alwaysNotify, and some of these
        # calls may be silently dropped
        # (see below).
        #
        # But if one of those calls needs
        # to force a notification, we want
        # that notification to happen.
        if alwaysNotify:
            self.__alwaysNotify = True

        def func():
            if fslgl.glvolume_funcs.updateShaderState(self) or \
               self.__alwaysNotify:
                self.notify()
                self.__alwaysNotify = False

        # Don't re-queue the update if it is
        # already queued on the idle loop.
        # As mentioned above, updateShaderState
        # may get called several times for a
        # single event, but in this situation
        # we only want to actually do the
        # update once.
        idle.idleWhen(func,
                      self.ready,
                      name=self.name,
                      skipIfQueued=True)


    def refreshImageTexture(self, **kwargs):
        """Refreshes the :class:`.ImageTexture` used to store the
        :class:`.Image` data. This is performed through the :mod:`.resources`
        module, so the image texture can be shared between multiple
        ``GLVolume`` instances.

        All keyword arguments are passed through to the :class:`.ImageTexture`
        constructor.
        """

        opts     = self.opts
        texName  = self.texName
        unsynced = self.testUnsynced()

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))

        if self.imageTexture is not None:

            if self.imageTexture.name == texName:
                return None

            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.name)

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        if opts.enableOverrideDataRange: normRange = opts.overrideDataRange
        else:                            normRange = None

        self.imageTexture = glresources.get(
            texName,
            textures.createImageTexture,
            texName,
            self.image,
            interp=interp,
            channel=opts.channel,
            volume=opts.index()[3:],
            normaliseRange=normRange,
            notify=False,
            **kwargs)

        self.imageTexture.register(self.name, self.__texturesChanged)


    def registerAuxImage(self, which, image, onReady=None):
        """Calls :meth:`.AuxImageTextureManager.registerAuxImage`, making
        sure that the texture interpolation is set appropriately.
        """

        if self.opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                                 interp = gl.GL_LINEAR

        self.auxmgr.texture(which).deregister(self.name)
        self.auxmgr.registerAuxImage(which, image, interp=interp)
        self.auxmgr.texture(which).register(self.name, self.__texturesChanged)
        if onReady is not None:
            idle.idleWhen(onReady, self.auxmgr.texturesReady)


    def refreshColourTextures(self):
        """Refreshes the :class:`.ColourMapTexture` instances used to colour
        image voxels.
        """

        display  = self.display
        opts     = self.opts
        alpha    = display.alpha / 100.0
        cmap     = opts.cmap
        interp   = opts.interpolateCmaps
        res      = opts.cmapResolution
        logScale = opts.logScale
        gamma    = opts.realGamma(opts.gamma)
        negCmap  = opts.negativeCmap
        invert   = opts.invert
        dmin     = opts.displayRange[0]
        dmax     = opts.displayRange[1]

        if interp: interp = gl.GL_LINEAR
        else:      interp = gl.GL_NEAREST

        self.colourTexture.set(cmap=cmap,
                               invert=invert,
                               alpha=alpha,
                               resolution=res,
                               gamma=gamma,
                               logScale=logScale,
                               interp=interp,
                               displayRange=(dmin, dmax))

        self.negColourTexture.set(cmap=negCmap,
                                  invert=invert,
                                  alpha=alpha,
                                  resolution=res,
                                  gamma=gamma,
                                  interp=interp,
                                  displayRange=(dmin, dmax))


    def preDraw(self, *args, **kwargs):
        """Binds the :class:`.ImageTexture` to ``GL_TEXTURE0`` and the
        :class:`.ColourMapTexture` to ``GL_TEXTURE1, and calls the
        version-dependent ``preDraw`` function.
        """

        # Set up the image and colour textures
        self.imageTexture    .bindTexture(gl.GL_TEXTURE0)
        self.colourTexture   .bindTexture(gl.GL_TEXTURE1)
        self.negColourTexture.bindTexture(gl.GL_TEXTURE2)
        self.clipTexture     .bindTexture(gl.GL_TEXTURE3)
        self.modulateTexture .bindTexture(gl.GL_TEXTURE4)

        fslgl.glvolume_funcs.preDraw(self, *args, **kwargs)


    def draw2D(self, *args, **kwargs):
        """Calls the version dependent ``draw2D`` function. """

        with glroutines.enabled((gl.GL_CULL_FACE)):
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glCullFace(gl.GL_BACK)
            gl.glFrontFace(self.frontFace())
            fslgl.glvolume_funcs.draw2D(self, *args, **kwargs)


    def draw3D(self, *args, **kwargs):
        """Calls the version dependent ``draw3D`` function. """

        opts = self.opts
        w, h = self.canvas.GetScaledSize()
        res  = self.opts.resolution / 100.0
        sw   = int(np.ceil(w * res))
        sh   = int(np.ceil(h * res))

        # Initialise and resize
        # the offscreen textures
        for rt in [self.renderTexture1, self.renderTexture2]:
            if rt.shape != (sw, sh):
                rt.shape = sw, sh

            with rt.target():
                gl.glClearColor(0, 0, 0, 0)
                gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        if opts.resolution != 100:
            gl.glViewport(0, 0, sw, sh)

        # Do the render. Even though we're
        # drawing off-screen,  we need to
        # enable depth-testing, otherwise
        # depth values will not get written
        # to the depth buffer!
        #
        # The glvolume_funcs.draw3D function
        # will put the final render into
        # renderTexture1
        with glroutines.enabled((gl.GL_DEPTH_TEST, gl.GL_CULL_FACE)):
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
            gl.glFrontFace(gl.GL_CCW)
            gl.glCullFace(gl.GL_BACK)
            fslgl.glvolume_funcs.draw3D(self, *args, **kwargs)

        # Apply smoothing if needed. If smoothing
        # is enabled, the final final render will
        # be in renderTexture2
        if opts.smoothing > 0:
            self.smoothFilter.set(offsets=[1.0 / sw, 1.0 / sh])
            self.smoothFilter.osApply(self.renderTexture1,
                                      self.renderTexture2)

        # We now have the final result
        # - draw it to the screen.
        verts = np.array([[-1, -1, 0],
                          [-1,  1, 0],
                          [ 1, -1, 0],
                          [ 1, -1, 0],
                          [-1,  1, 0],
                          [ 1,  1, 0]], dtype=np.float32)

        invproj = affine.invert(self.canvas.projectionMatrix)
        verts   = affine.transform(verts, invproj)

        if opts.resolution != 100:
            gl.glViewport(0, 0, w, h)

        with glroutines.enabled(gl.GL_DEPTH_TEST):

            # If smoothing was not applied, rt1
            # contains the final render. Otherwise,
            # rt2 contains the final render, but rt1
            # contains the depth information. So we
            # need to # temporarily replace rt2.depth
            # with rt1.depth.
            if opts.smoothing > 0:
                src    = self.renderTexture2
                olddep = self.renderTexture2.depthTexture
                dep    = self.renderTexture1.depthTexture
            else:
                src    = self.renderTexture1
                olddep = self.renderTexture1.depthTexture
                dep    = olddep

            src.depthTexture = dep
            src.draw(verts, useDepth=True)
            src.depthTexture = olddep


    def drawAll(self, *args, **kwargs):
        """Calls the version dependent ``drawAll`` function. """

        fslgl.glvolume_funcs.drawAll(self, *args, **kwargs)


    def postDraw(self, *args, **kwargs):
        """Unbinds the ``ImageTexture`` and ``ColourMapTexture``, and calls the
        version-dependent ``postDraw`` function.
        """

        self.imageTexture    .unbindTexture()
        self.colourTexture   .unbindTexture()
        self.negColourTexture.unbindTexture()
        self.clipTexture     .unbindTexture()
        self.modulateTexture .unbindTexture()

        fslgl.glvolume_funcs.postDraw(self, *args, **kwargs)


    def getAuxTextureXform(self, which):
        """Calculates a transformation matrix which will transform from the
        image coordinate system into the :attr:`.VolumeOpts.clipImage` or
        :attr:`.VolumeOpts.modulateImage` coordinate system. If the property
        is ``None``, it will be an identity transform.

        This transform is used by shader programs to find the auxillary image
        coordinates that correspond with specific image coordinates.
        """
        return affine.concat(
            self.auxmgr.textureXform(which),
            # to support 2D image textures
            self.imageTexture.invTexCoordXform(self.overlay.shape))


    def getModulateValueXform(self):
        """Returns an affine transform to normalise alpha modulation values.

        The GL volume shaders need to normalise the modulate value by the
        modulation range to generate an opacity value. We calculate a suitable
        scale and offset by buildin an affine transform which transforms voxel
        values from the image/modulate image texture range to 0/1, where 0
        corresponds to the low modulate range bound, and 1 to the high
        modulate range bound. The resulting scale/offset can be used by the
        shader to convert a modulate value directly into an opacity value.
        """

        opts = self.opts
        if opts.modulateImage is None:
            modXform = self.imageTexture.voxValXform
        else:
            modXform = self.modulateTexture.voxValXform

        modlo, modhi = opts.modulateRange
        modrange     = modhi - modlo
        if modrange == 0:
            modXform = np.eye(4)
        else:
            modXform = affine.concat(
                affine.scaleOffsetXform(1 / modrange, -modlo / modrange),
                modXform)

        return modXform


    def generateVertices2D(self, zpos, axes, bbox=None):
        """Overrides :meth:`.GLImageObject.generateVertices2D`.

        Appliies the :meth:`.ImageTextureBase.texCoordXform` to the texture
        coordinates - this is performed to support 2D images/textures.
        """

        vertices, voxCoords, texCoords = \
            glimageobject.GLImageObject.generateVertices2D(
                self, zpos, axes, bbox)

        texCoords = affine.transform(
            texCoords, self.imageTexture.texCoordXform(self.overlay.shape))

        return vertices, voxCoords, texCoords


    def generateVertices3D(self, bbox=None):
        """Overrides :meth:`.GLImageObject.generateVertices3D`.

        Appliies the :meth:`.ImageTextureBase.texCoordXform` to the texture
        coordinates - this is performed to support 2D images/textures.
        """

        vertices, voxCoords, texCoords = \
            glimageobject.GLImageObject.generateVertices3D(self, bbox)

        texCoords = affine.transform(
            texCoords, self.imageTexture.texCoordXform(self.overlay.shape))

        return vertices, voxCoords, texCoords


    def _alphaChanged(self, *a):
        """Called when the :attr:`.Display.alpha` property changes. """

        self.refreshColourTextures()
        if self.threedee:
            self.updateShaderState(alwaysNotify=True)
        else:
            self.notify()


    def _displayRangeChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.displayRange` property changes.
        """
        self.refreshColourTextures()
        self.updateShaderState()


    def _lowClippingRangeChanged(self, *a):
        """Called when the low :attr:`.VolumeOpts.clippingRange` property
        changes. Separate listeners are used for the low and high clipping
        values to avoid unnecessary duplicate refreshes in the event that the
        :attr:`.VolumeOpts.linkLowRanges` or
        :attr:`.VolumeOpts.linkHighRanges` flags are set.
        """
        if self.opts.linkLowRanges:
            return

        self.updateShaderState()


    def _highClippingRangeChanged(self, *a):
        """Called when the high :attr:`.VolumeOpts.clippingRange` property
        changes (see :meth:`_lowClippingRangeChanged`).
        """
        if self.opts.linkHighRanges:
            return

        self.updateShaderState(self)


    def _modulateRangeChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.modulateRange` property changes.
        """
        self.updateShaderState()


    def _clipImageChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.clipImage` property changes.
        """
        self.registerAuxImage('clip', self.opts.clipImage)


    def _modulateImageChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.modulateImage` property changes.
        """
        self.registerAuxImage('modulate', self.opts.modulateImage)


    def _invertClippingChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.invertClipping` property changes.
        """
        self.updateShaderState()


    def _cmapChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.cmap` or
        :attr:`.VolumeOpts.negativeCmap` properties change.
        """
        self.refreshColourTextures()
        self.notify()


    def _useNegativeCmapChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.useNegativeCmap` property
        changes.
        """
        self.updateShaderState()


    def _invertChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.invert` property changes. """
        self.refreshColourTextures()
        self.notify()


    def _modulateAlphaChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.modulateAlpha` property changes.
        Calls :meth:`updateShaderState`.
        """
        self.updateShaderState()


    def _enableOverrideDataRangeChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.enableOverrideDataRange` property
        changes. Calls :meth:`_volumeChanged`.
        """
        self._volumeChanged(volRefresh=True)


    def _overrideDataRangeChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.overrideDataRange` property
        changes. Calls :meth:`_volumeChanged`, but only if
        :attr:`.VolumeOpts.enableOverrideDataRange` is ``True``.
        """
        if self.opts.enableOverrideDataRange:
            self._volumeChanged(volRefresh=True)


    def _volumeChanged(self, *a, **kwa):
        """Called when the :attr:`.NiftiOpts.volume` property changes Also
        called when other properties, which require a texture refresh, change.
        """
        opts       = self.opts
        volRefresh = kwa.pop('volRefresh', False)

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        if opts.enableOverrideDataRange: normRange = opts.overrideDataRange
        else:                            normRange = None

        self.imageTexture.set(volume=opts.index()[3:],
                              channel=opts.channel,
                              interp=interp,
                              volRefresh=volRefresh,
                              normaliseRange=normRange)

        self.clipTexture    .set(interp=interp)
        self.modulateTexture.set(interp=interp)


    def _channelChanged(self, *a, **kwa):
        """Called when the :attr:`.NiftiOpts.channel` changes.
        Refreshes the texture.
        """
        self._volumeChanged()


    def _interpolationChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.interpolation` property changes.
        """
        self._volumeChanged(volRefresh=True)


    def _transformChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.transform` property changes.
        """
        self.notify()


    def _displayXformChanged(self, *a):
        """Called when the :attr:`.NiftiOpts.displayXform` property changes.
        """
        self.notify()


    def _numStepsChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.numSteps` property changes.
        """
        self.notify()


    def _numInnerStepsChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.numInnerSteps` property
        changes.
        """
        fslgl.glvolume_funcs.compileShaders(self)
        self.updateShaderState(alwaysNotify=True)


    def _resolutionChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.resolution` property
        changes.
        """
        self.notify()


    def _numClipPlanesChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.numClipPlanes` property
        changes.
        """
        if float(fslgl.GL_COMPATIBILITY) == 1.4:
            fslgl.glvolume_funcs.compileShaders(self)
        self.updateShaderState(alwaysNotify=True)


    def _clipModeChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.clipMode` property
        changes.
        """
        if float(fslgl.GL_COMPATIBILITY) == 1.4:
            fslgl.glvolume_funcs.compileShaders(self)
        self.updateShaderState(alwaysNotify=True)


    def _clipping3DChanged(self, *a):
        """Called when any of the :attr:`.Volume3DOpts.clipPosition`,
        :attr:`.Volume3DOpts.clipAzimuth`, or
        :attr:`.Volume3DOpts.clipInclination` properties change.
        """

        self.updateShaderState(alwaysNotify=True)


    def _showClipPlanesChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.showClipPlanes` property
        changes.
        """
        self.updateShaderState(alwaysNotify=True)


    def _blendPropertiesChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.showClipPlanes` property
        changes.
        """
        self.updateShaderState(alwaysNotify=True)


    def _smoothingChanged(self, *a):
        """Called when the :attr:`.Volume3DOpts.smoothing` property
        changes.
        """
        self.smoothFilter.set(kernSize=self.opts.smoothing * 2)
        self.notify()


    def _imageSyncChanged(self, *a):
        """Called when the synchronisation state of the
        :attr:`.NiftiOpts.volume` or :attr:`.VolumeOpts.interpolation`
        properties change.
        """

        self.refreshImageTexture()
        self.updateShaderState(alwaysNotify=True)


    def __texturesChanged(self, *a):
        """Called when either the ``imageTexture`` or the ``clipTexture``
        changes. Calls :meth:`updateShaderState`.
        """
        self.updateShaderState(alwaysNotify=True)
