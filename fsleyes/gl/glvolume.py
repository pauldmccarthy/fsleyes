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

import OpenGL.GL        as gl

import fsl.utils.async  as async
import fsleyes.gl       as fslgl
from . import              textures
from . import              globject
from . import resources as glresources


log = logging.getLogger(__name__)


class GLVolume(globject.GLImageObject):
    """The ``GLVolume`` class is a :class:`.GLImageObject` which encapsulates
    the data and logic required to render 2D slices of an :class:`.Image`
    overlay.


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

    ``preDraw(GLVolume)``                 Initialise the GL state, ready for
                                          drawing.

    ``draw(GLVolume, zpos, xform=None)``  Draw a slice of the image at the
                                          given ``zpos``. If ``xform`` is not
                                          ``None``, it must be applied as a
                                          transformation on the vertex
                                          coordinates.

    ``drawAll(Glvolume, zposes, xforms)`` Draws slices at each of the
                                          specified ``zposes``, applying the
                                          corresponding ``xforms`` to each.

    ``postDraw(GLVolume)``                Clear the GL state after drawing.
    ===================================== =====================================


    **Rendering**


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


    **Textures**


    The ``GLVolume`` class uses three textures:

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


    **Attributes**


    The following attributes are available on a ``GLVolume`` instance:

    ==================== ==================================================
    ``imageTexture``     The :class:`.ImageTexture` which stores the image
                         data.
    ``clipTexture``      The :class:`.ImageTexture` which stores the clip
                         image data.   If :attr:`.VolumeOpts.clipImage`
                         is ``None``, this attribute will also be ``None``.
    ``colourTexture``    The :class:`.ColourMapTexture` used to store the
                         colour map.
    ``negColourTexture`` The :class:`.ColourMapTexture` used to store the
                         negative colour map.
    ``texName``          A name used for the ``imageTexture``,
                         ``colourTexture``, and ``negColourTexture`. The
                         name for the latter is suffixed with ``'_neg'``.
    ==================== ==================================================
    """


    def __init__(self, image, display, xax, yax):
        """Create a ``GLVolume`` object.

        :arg image:   An :class:`.Image` object.

        :arg display: A :class:`.Display` object which describes how the image
                      is to be displayed.

        :arg xax:     Initial display X axis

        :arg yax:     Initial display Y axis
        """

        globject.GLImageObject.__init__(self, image, display, xax, yax)

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
        self.shader   = None

        # References to the clip image and
        # associated DisplayOpts instance,
        # if it is set.
        self.clipImage        = None
        self.clipOpts         = None

        # Refs to all of the texture objects.
        self.imageTexture     = None
        self.clipTexture      = None
        self.colourTexture    = textures.ColourMapTexture(self.texName)
        self.negColourTexture = textures.ColourMapTexture(
            '{}_neg'.format(self.texName))

        # This attribute is used by the
        # updateShaderState method to
        # make sure that the Notifier.notify()
        # method gets called when needed.
        # See that method for details.
        self.__alwaysNotify = False

        # If the VolumeOpts instance has
        # inherited a clipImage value,
        # make sure we're registered with it.
        if self.displayOpts.clipImage is not None:
            self.registerClipImage()

        self.refreshColourTextures()
        self.refreshImageTexture()
        self.refreshClipTexture()

        # Call glvolume_funcs.init when the image
        # and clip textures are ready to be used.
        def init():
            fslgl.glvolume_funcs.init(self)
            self.notify()

        async.idleWhen(init, self.texturesReady)


    def destroy(self):
        """This must be called when this :class:`GLVolume` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles), calls :meth:`removeDisplayListeners`,
        and calls :meth:`.GLImageObject.destroy`.
        """

        self.deregisterClipImage()
        self.removeDisplayListeners()

        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.getTextureName())

        if self.clipTexture is not None:
            self.clipTexture.deregister(self.name)
            glresources.delete(self.clipTexture.getTextureName())

        self.colourTexture   .destroy()
        self.negColourTexture.destroy()

        self.imageTexture     = None
        self.clipTexture      = None
        self.colourTexture    = None
        self.negColourTexture = None

        fslgl.glvolume_funcs  .destroy(self)
        globject.GLImageObject.destroy(self)


    def ready(self):
        """Returns ``True`` if this ``GLVolume`` is ready to be drawn,
        ``False`` otherwise.
        """
        return (not self.destroyed()    and
                self.shader is not None and
                self.texturesReady())


    def texturesReady(self):
        """Returns ``True`` if the ``imageTexture`` and ``clipTexture`` (if
        applicable) are both ready to be used, ``False`` otherwise.
        """
        imageTexReady = (self.imageTexture is not None and
                         self.imageTexture.ready())

        clipTexReady  = (self.clipImage is None or
                         (self.clipTexture is not None and
                          self.clipTexture.ready()))

        return imageTexReady and clipTexReady


    def addDisplayListeners(self):
        """Called by :meth:`__init__`.

        Adds a bunch of listeners to the :class:`.Display` object, and the
        associated :class:`.VolumeOpts` instance, which define how the image
        should be displayed.

        This is done so we can update the colour, vertex, and image data when
        display properties are changed.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        crPVs   = opts.getPropVal('clippingRange').getPropertyValueList()

        display .addListener('alpha',            name, self._alphaChanged)
        opts    .addListener('displayRange',     name,
                             self._displayRangeChanged)

        crPVs[0].addListener(name, self._lowClippingRangeChanged)
        crPVs[1].addListener(name, self._highClippingRangeChanged)

        opts    .addListener('clipImage',        name, self._clipImageChanged)
        opts    .addListener('invertClipping',   name,
                             self._invertClippingChanged)
        opts    .addListener('cmap',             name, self._cmapChanged)
        opts    .addListener('interpolateCmaps', name, self._cmapChanged)
        opts    .addListener('negativeCmap',     name, self._cmapChanged)
        opts    .addListener('cmapResolution',   name, self._cmapChanged)
        opts    .addListener('useNegativeCmap',  name,
                             self._useNegativeCmapChanged)
        opts    .addListener('invert',           name, self._invertChanged)
        opts    .addListener('volume',           name, self._volumeChanged)
        opts    .addListener('interpolation',    name,
                             self._interpolationChanged)
        opts    .addListener('transform',        name, self._transformChanged)
        opts    .addListener('displayXform',     name,
                             self._displayXformChanged)
        opts    .addListener('enableOverrideDataRange',  name,
                             self._enableOverrideDataRangeChanged)
        opts    .addListener('overrideDataRange', name,
                             self._overrideDataRangeChanged)

        # GLVolume instances need to keep track of whether
        # the volume property of their corresponding
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


    def removeDisplayListeners(self):
        """Called by :meth:`destroy`. Removes all the property listeners that
        were added by :meth:`addDisplayListeners`.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name
        crPVs   = opts.getPropVal('clippingRange').getPropertyValueList()

        display .removeListener(          'alpha',                   name)
        opts    .removeListener(          'displayRange',            name)
        crPVs[0].removeListener(name)
        crPVs[1].removeListener(name)
        opts    .removeListener(          'clipImage',               name)
        opts    .removeListener(          'invertClipping',          name)
        opts    .removeListener(          'cmap',                    name)
        opts    .removeListener(          'interpolateCmaps',        name)
        opts    .removeListener(          'negativeCmap',            name)
        opts    .removeListener(          'useNegativeCmap',         name)
        opts    .removeListener(          'cmapResolution',          name)
        opts    .removeListener(          'invert',                  name)
        opts    .removeListener(          'volume',                  name)
        opts    .removeListener(          'interpolation',           name)
        opts    .removeListener(          'transform',               name)
        opts    .removeListener(          'displayXform',            name)
        opts    .removeListener(          'enableOverrideDataRange', name)
        opts    .removeListener(          'overrideDataRange',       name)

        if self.__syncListenersRegistered:
            opts.removeSyncChangeListener('volume', name)


    def testUnsynced(self):
        """Used by the :meth:`refreshImageTexture` method.

        Returns ``True`` if certain critical :class:`VolumeOpts` properties
        have been unsynced from the parent instance, meaning that this
        ``GLVolume`` instance needs to create its own image texture;
        returns ``False`` otherwise.
        """
        is4D = len(self.image.shape) >= 4 and self.image.shape[3] > 1

        return (self.displayOpts.getParent() is None or
                (is4D and not self.displayOpts.isSyncedToParent('volume')))


    def updateShaderState(self, *args, **kwargs):
        """Calls :func:`.gl14.glvolume_funcs.updateShaderState` or
        :func:`.gl21.glvolume_funcs.updateShaderStatea`, then
        :meth:`.Notifier.notify`. Uses the :func:`.async.idleWhen` function to
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
        async.idleWhen(func,
                       self.ready,
                       name=self.name,
                       skipIfQueued=True)


    def refreshImageTexture(self):
        """Refreshes the :class:`.ImageTexture` used to store the
        :class:`.Image` data. This is performed through the :mod:`.resources`
        module, so the image texture can be shared between multiple
        ``GLVolume`` instances.
        """

        opts     = self.displayOpts
        texName  = self.texName
        unsynced = self.testUnsynced()

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))

        if self.imageTexture is not None:

            if self.imageTexture.getTextureName() == texName:
                return None

            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.getTextureName())

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            self.image,
            interp=interp,
            volume=opts.volume,
            notify=False)

        self.imageTexture.register(self.name, self.__texturesChanged)


    def registerClipImage(self):
        """Called whenever the :attr:`.VolumeOpts.clipImage` property changes.
        Adds property listeners to the :class:`.NiftiOpts` instance
        associated with the new clip image, if necessary.
        """

        clipImage = self.displayOpts.clipImage

        if clipImage is None:
            return

        clipOpts = self.displayOpts.displayCtx.getOpts(clipImage)

        self.clipImage = clipImage
        self.clipOpts  = clipOpts

        def updateClipTexture(*a):
            self.clipTexture.set(volume=clipOpts.volume)

        clipOpts.addListener('volume',
                             self.name,
                             updateClipTexture,
                             weak=False)


    def deregisterClipImage(self):
        """Called whenever the :attr:`.VolumeOpts.clipImage` property changes.
        Removes property listeners from the :class:`.NiftiOpts` instance
        associated with the old clip image, if necessary.
        """

        if self.clipImage is None:
            return

        self.clipOpts.removeListener('volume', self.name)

        self.clipImage = None
        self.clipOpts  = None


    def refreshClipTexture(self):
        """Re-creates the :class:`.ImageTexture` used to store the
        :attr:`.VolumeOpts.clipImage`.
        """
        clipImage = self.clipImage
        opts      = self.displayOpts
        clipOpts  = self.clipOpts

        texName   = '{}_clip_{}'.format(type(self).__name__, id(clipImage))

        if self.clipTexture is not None:
            self.clipTexture.deregister(self.name)
            glresources.delete(self.clipTexture.getTextureName())
            self.clipTexture = None

        if clipImage is None:
            return None

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        self.clipTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            clipImage,
            interp=interp,
            volume=clipOpts.volume,
            notify=False)

        self.clipTexture.register(self.name, self.__texturesChanged)


    def refreshColourTextures(self):
        """Refreshes the :class:`.ColourMapTexture` instances used to colour
        image voxels.
        """

        display = self.display
        opts    = self.displayOpts
        alpha   = display.alpha / 100.0
        cmap    = opts.cmap
        interp  = opts.interpolateCmaps
        res     = opts.cmapResolution
        negCmap = opts.negativeCmap
        invert  = opts.invert
        dmin    = opts.displayRange[0]
        dmax    = opts.displayRange[1]

        if interp: interp = gl.GL_LINEAR
        else:      interp = gl.GL_NEAREST

        self.colourTexture.set(cmap=cmap,
                               invert=invert,
                               alpha=alpha,
                               resolution=res,
                               interp=interp,
                               displayRange=(dmin, dmax))

        self.negColourTexture.set(cmap=negCmap,
                                  invert=invert,
                                  alpha=alpha,
                                  resolution=res,
                                  interp=interp,
                                  displayRange=(dmin, dmax))


    def preDraw(self):
        """Binds the :class:`.ImageTexture` to ``GL_TEXTURE0`` and the
        :class:`.ColourMapTexture` to ``GL_TEXTURE1, and calls the
        version-dependent ``preDraw`` function.
        """

        # Set up the image and colour textures
        self.imageTexture    .bindTexture(gl.GL_TEXTURE0)
        self.colourTexture   .bindTexture(gl.GL_TEXTURE1)
        self.negColourTexture.bindTexture(gl.GL_TEXTURE2)

        if self.clipTexture is not None:
            self.clipTexture .bindTexture(gl.GL_TEXTURE3)

        fslgl.glvolume_funcs.preDraw(self)


    def draw(self, zpos, xform=None, bbox=None):
        """Draws a 2D slice of the image at the given Z location in the
        display coordinate system.

     .  This is performed via a call to the OpenGL version-dependent ``draw``
        function, contained in one of the :mod:`.gl14.glvolume_funcs` or
        :mod:`.gl21.glvolume_funcs` modules.

        If ``xform`` is not ``None``, it is applied as an affine
        transformation to the vertex coordinates of the rendered image data.

        .. note:: Calls to this method must be preceded by a call to
                  :meth:`preDraw`, and followed by a call to :meth:`postDraw`.
        """

        fslgl.glvolume_funcs.draw(self, zpos, xform, bbox)


    def drawAll(self, zposes, xforms):
        """Calls the version dependent ``drawAll`` function. """

        fslgl.glvolume_funcs.drawAll(self, zposes, xforms)


    def postDraw(self):
        """Unbinds the ``ImageTexture`` and ``ColourMapTexture``, and calls the
        version-dependent ``postDraw`` function.
        """

        self.imageTexture    .unbindTexture()
        self.colourTexture   .unbindTexture()
        self.negColourTexture.unbindTexture()

        if self.clipTexture is not None:
            self.clipTexture.unbindTexture()

        fslgl.glvolume_funcs.postDraw(self)


    def _alphaChanged(self, *a):
        """Called when the :attr:`.Display.alpha` property changes. """
        self.refreshColourTextures()
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
        if self.displayOpts.linkLowRanges:
            return

        self.updateShaderState()


    def _highClippingRangeChanged(self, *a):
        """Called when the high :attr:`.VolumeOpts.clippingRange` property
        changes (see :meth:`_lowClippingRangeChanged`).
        """
        if self.displayOpts.linkHighRanges:
            return

        self.updateShaderState(self)


    def _clipImageChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.clipImage` property changes.
        """
        self.deregisterClipImage()
        self.registerClipImage()
        self.refreshClipTexture()


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


    def _enableOverrideDataRangeChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.enableOverrideDataRange` property
        changes. Calls :meth:`_volumeChanged`.
        """
        self._volumeChanged()


    def _overrideDataRangeChanged(self, *a):
        """Called when the :attr:`.VolumeOpts.overrideDataRange` property
        changes. Calls :meth:`_volumeChanged`, but only if
        :attr:`.VolumeOpts.enableOverrideDataRange` is ``True``.
        """
        if self.displayOpts.enableOverrideDataRange:
            self._volumeChanged()


    def _volumeChanged(self, *a, **kwa):
        """Called when the :attr:`.NiftiOpts.volume` property changes Also
        called when other properties, which require a texture refresh, change.
        """
        opts       = self.displayOpts
        volume     = opts.volume
        volRefresh = kwa.pop('volRefresh', False)

        if opts.interpolation == 'none': interp = gl.GL_NEAREST
        else:                            interp = gl.GL_LINEAR

        if opts.enableOverrideDataRange: normRange = opts.overrideDataRange
        else:                            normRange = None

        self.imageTexture.set(volume=volume,
                              interp=interp,
                              volRefresh=volRefresh,
                              normaliseRange=normRange)

        if self.clipTexture is not None:
            self.clipTexture.set(interp=interp)


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
