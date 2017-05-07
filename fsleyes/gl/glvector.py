#!/usr/bin/env python
#
# glvector.py - The GLVectorBase and GLVector classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLVectorBase` and :class:`GLVector`
classes. The ``GLVectorBase`` class encapsulate the logic for rendering
overlays which contain directional data, and the ``GLVector`` class
specifically conatins logic for displaying ``X*Y*Z*3`` :class:`.Image`
overlays.
"""


import numpy               as np
import OpenGL.GL           as gl

import fsl.data.image      as fslimage
import fsl.utils.async     as async
import fsl.utils.transform as transform
import fsleyes.colourmaps  as fslcm
from . import resources    as glresources
from . import                 textures
from . import                 globject


class GLVectorBase(globject.GLImageObject):
    """The :class:`GLVectorBase` class encapsulates the logic for rendering
    :class:`.Nifti` overlay types which represent directional data (and which
    are described by a :class:`.VectorOpts` instance).  The ``GLVectorBase``
    class is a sub-class of :class:`.GLImageObject`.


    The ``GLVectorBase`` class is a base class which is not intended to be
    instantiated directly. The :class:`.GLRGBVector`, :class:`.GLLineVector`,
    :class:`.GLTensor`, and :class:`.GLSH` subclasses should be used instead.
    These subclasses share the functionality provided by this class. See also
    the :class:`GLVector` class, which is also a base class.


    *Colouring*

    A ``GLVectorBase`` can be coloured in one of two ways:

     - Each voxel is coloured according to the orientation of the vector.
       A custom fragment shader program looks up the ``xyz`` vector values,
       and combines three colours (corresponding to the ``xyz`` directions)
       to form the final fragment colour. The colours for each component
       are specified by the :attr:`.VectorOpts.xColour`,
       :attr:`.VectorOpts.yColour`, and :attr:`.VectorOpts.zColour`
       properties. If the image being displayed contains directional data
       (i.e. is a ``X*Y*Z*3`` vector image), you should use the
       :class:`GLVector` class.

     - Each voxel is coloured according to the values contained in another
       image, which are used to look up a colour in a colour map. The image
       and colour map are respectively specified by the
       :attr:`.VectorOpts.colourImage` and :attr:`.VectorOpts.cmap` properties.


    In either case, the brightness of each vector colour may be modulated by
    another image, specified by the :attr:`.VectorOpts.modulateImage`
    property.  This modulation image is stored as a 3D single-channel
    :class:`.ImageTexture`.


    Finally, vector voxels may be clipped according to the values of another
    image, specified by the :attr:`.VectorOpts.clipImage` property.  This
    clipping image is stored as a 3D single-channel :class:`.ImageTexture`, and
    the clipping thresholds specified by the :attr:`.VectorOpts.clippingRange`
    property.


    *Textures*

    The ``GLVectorBase`` class configures its textures in the following manner:

    =================== ==================
    ``modulateTexture`` ``gl.GL_TEXTURE0``
    ``clipTexture``     ``gl.GL_TEXTURE1``
    ``colourTexture``   ``gl.GL_TEXTURE2``
    ``cmapTexture``     ``gl.GL_TEXTURE3``
    =================== ==================
    """


    def __init__(self, overlay, display, xax, yax, init=None, preinit=None):
        """Create a ``GLVectorBase`` object bound to the given overlay and
        display.

        Initialises the OpenGL data required to render the given vector
        overlay. This method does the following:

          - Creates the modulate, clipping and colour image textures.

          - Adds listeners to the :class:`.Display` and :class:`.VectorOpts`
            instances, so the textures and geometry can be updated when
            necessary.

        :arg overlay:        A :class:`.Nifti` object.

        :arg display:        A :class:`.Display` object which describes how the
                             overlay is to be displayed.

        :arg xax:            Initial display X axis

        :arg yax:            Initial display Y axis

        :arg init:           An optional function to be called when all of the
                             :class:`.ImageTexture` instances associated with
                             this ``GLVectorBase`` have been initialised.

        :arg preinit:        An optional functiono be called after this
                             ``GLVectorBase`` has configured itself, but
                             *before* ``init`` is called. Used by
                             :class:`GLVector`.
        """

        globject.GLImageObject.__init__(self, overlay, display, xax, yax)

        name = self.name

        self.cmapTexture     = textures.ColourMapTexture('{}_cm'.format(name))

        self.shader          = None
        self.modulateImage   = None
        self.clipImage       = None
        self.colourImage     = None
        self.modulateOpts    = None
        self.clipOpts        = None
        self.colourOpts      = None
        self.modulateTexture = None
        self.clipTexture     = None
        self.colourTexture   = None

        # Make sure we are registered with the
        # auxillary images if any of them are set.
        opts = self.displayOpts

        if opts.colourImage   is not None: self.registerAuxImage('colour')
        if opts.modulateImage is not None: self.registerAuxImage('modulate')
        if opts.clipImage     is not None: self.registerAuxImage('clip')

        self.addListeners()

        def initWrapper():
            if init is not None:
                init()
            self.notify()

        self.refreshColourMapTexture()
        self.refreshAuxTexture('modulate')
        self.refreshAuxTexture('clip')
        self.refreshAuxTexture('colour')

        if preinit is not None:
            preinit()

        async.idleWhen(initWrapper, self.texturesReady)


    def destroy(self):
        """Must be called when this ``GLVectorBase`` is no longer needed.
        Deletes the GL textures, and deregisters the listeners configured in
        :meth:`__init__`.
        """

        self.cmapTexture.destroy()

        for tex in (self.modulateTexture,
                    self.clipTexture,
                    self.colourTexture):
            tex.deregister(self.name)
            glresources.delete(tex.getTextureName())

        self.removeListeners()
        self.deregisterAuxImage('modulate')
        self.deregisterAuxImage('clip')
        self.deregisterAuxImage('colour')

        self.modulateTexture = None
        self.clipTexture     = None
        self.colourTexture   = None
        self.modulateImage   = None
        self.clipImage       = None
        self.colourImage     = None
        self.modulateOpts    = None
        self.clipOpts        = None
        self.colourOpts      = None

        globject.GLImageObject.destroy(self)


    def ready(self):
        """Returns ``True`` if this ``GLVectorBase`` is ready to be drawn,
        ``False`` otherwise.
        """
        return self.shader is not None and self.texturesReady()


    def texturesReady(self):
        """Returns ``True`` if all of the textures are ready, ``False``
        otherwise.
        """
        return (self.modulateTexture is not None and
                self.clipTexture     is not None and
                self.colourTexture   is not None and
                self.modulateTexture.ready()     and
                self.clipTexture    .ready()     and
                self.colourTexture  .ready())


    def addListeners(self):
        """Called by :meth:`__init__`. Adds listeners to properties of the
        :class:`.Display` and :class:`.VectorOpts` instances, so that the GL
        representation can be updated when the display properties change.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        display.addListener('alpha',         name, self.__cmapPropChanged)
        display.addListener('brightness',    name, self.__cmapPropChanged)
        display.addListener('contrast',      name, self.__cmapPropChanged)
        opts   .addListener('xColour',       name, self.asyncUpdateShaderState)
        opts   .addListener('yColour',       name, self.asyncUpdateShaderState)
        opts   .addListener('zColour',       name, self.asyncUpdateShaderState)
        opts   .addListener('suppressX',     name, self.asyncUpdateShaderState)
        opts   .addListener('suppressY',     name, self.asyncUpdateShaderState)
        opts   .addListener('suppressZ',     name, self.asyncUpdateShaderState)
        opts   .addListener('suppressMode',  name, self.asyncUpdateShaderState)
        opts   .addListener('cmap',          name, self.__cmapPropChanged)
        opts   .addListener('modulateImage', name, self.__modImageChanged)
        opts   .addListener('clipImage',     name, self.__clipImageChanged)
        opts   .addListener('colourImage',   name, self.__colourImageChanged)
        opts   .addListener('clippingRange', name, self.asyncUpdateShaderState)
        opts   .addListener('modulateRange', name, self.asyncUpdateShaderState)
        opts   .addListener('transform',     name, self.notify)


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all property listeners added
        by  the :meth:`addListeners` method.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        display.removeListener('alpha',         name)
        display.removeListener('brightness',    name)
        display.removeListener('contrast',      name)
        opts   .removeListener('xColour',       name)
        opts   .removeListener('yColour',       name)
        opts   .removeListener('zColour',       name)
        opts   .removeListener('cmap',          name)
        opts   .removeListener('suppressX',     name)
        opts   .removeListener('suppressY',     name)
        opts   .removeListener('suppressZ',     name)
        opts   .removeListener('suppressMode',  name)
        opts   .removeListener('modulateImage', name)
        opts   .removeListener('clipImage',     name)
        opts   .removeListener('colourImage',   name)
        opts   .removeListener('clippingRange', name)
        opts   .removeListener('modulateRange', name)
        opts   .removeListener('transform' ,    name)


    def compileShaders(self):
        """This method must be provided by subclasses (e.g.g the
        :class:`.GLRGBVector` and :class:`.GLLineVector` classes), and must
        compile the vertex/fragment shaders used to render this
        ``GLVectorBase``.
        ."""
        raise NotImplementedError('compileShaders must be implemented by '
                                  '{} subclasses'.format(type(self).__name__))


    def updateShaderState(self):
        """This method must be provided by subclasses (e.g. the
        :class:`.GLRGBVector` and :class:`.GLLineVector` classes), and must
        update the state of the vertex/fragment shader programs. It must return
        ``True`` if the shader state was updated, ``False`` otherwise.
        """
        raise NotImplementedError('updateShaderState must be implemented by '
                                  '{} subclasses'.format(type(self).__name__))


    def asyncUpdateShaderState(self, *args, **kwargs):
        """Calls :meth:`updateShaderState` and then :meth:`.Notifier.notify`, using
        :func:`.async.idleWhen` function to make sure that it is only called
        when :meth:`ready` returns ``True``.
        """

        alwaysNotify = kwargs.pop('alwaysNotify', None)

        def func():
            if self.updateShaderState() or alwaysNotify:
                self.notify()

        async.idleWhen(func,
                       self.ready,
                       name=self.name,
                       skipIfQueued=True)


    def registerAuxImage(self, which):
        """Called when the :attr:`.VectorOpts.modulateImage`,
        :attr:`.VectorOpts.clipImage`, or :attr:`.VectorOpts.colourImage`
        properties change. Registers a listener with the
        :attr:`.NiftiOpts.volume` property of the modulate/clip/colour image,
        so the modulate/clip/colour textures can be updated when the image
        volume changes.
        """

        imageAttr = '{}Image'  .format(which)
        optsAttr  = '{}Opts'   .format(which)
        texAttr   = '{}Texture'.format(which)

        image = getattr(self.displayOpts, imageAttr)
        tex   = getattr(self,             texAttr)

        if image is None or image == 'none':
            image = None

        setattr(self, optsAttr,  None)
        setattr(self, imageAttr, image)

        if image is None:
            return

        opts = self.displayOpts.displayCtx.getOpts(image)

        setattr(self, optsAttr, opts)

        def volumeChange(*a):
            tex.set(volume=opts.volume)
            self.asyncUpdateShaderState(alwaysNotify=True)

        # We set overwrite=True, because
        # the modulate/clip/colour images
        # may be the same.
        opts.addListener('volume',
                         self.name,
                         volumeChange,
                         overwrite=True,
                         weak=False)


    def deregisterAuxImage(self, which):
        """Called when the :attr:`.VectorOpts.modulateImage`,
        :attr:`.VectorOpts.clipImage` or :attr:`.VectorOpts.colourImage`
        properties change.  Deregisters the :attr:`.NiftiOpts.volume`
        listener that was registered in :meth:`registerAuxImage`.
        """

        imageAttr = '{}Image'.format(which)
        optsAttr  = '{}Opts' .format(which)

        opts = getattr(self, optsAttr)

        if opts is not None:
            opts.removeListener('volume', self.name)

        setattr(self, imageAttr, None)
        setattr(self, optsAttr,  None)


    def refreshAuxTexture(self, which, interp=gl.GL_NEAREST):
        """Called when the :attr`.VectorOpts.modulateImage`,
        :attr`.VectorOpts.clipImage`, or :attr`.VectorOpts.colourImage`
        properties changes.  Reconfigures the modulation/clip/colour
        :class:`.ImageTexture`. If no image is selected, a 'dummy' texture is
        creatad, which contains all white values (and which result in the
        auxillary textures having no effect).

        The ``interp`` argument can be used to set the initial interpolation
        type (``GL_NEAREST`` or ``GL_LINEAR``).
        """

        imageAttr = '{}Image'  .format(which)
        optsAttr  = '{}Opts'   .format(which)
        texAttr   = '{}Texture'.format(which)

        image = getattr(self, imageAttr)
        opts  = getattr(self, optsAttr)
        tex   = getattr(self, texAttr)

        if tex is not None:
            tex.deregister(self.name)
            glresources.delete(tex.getTextureName())

        if image is None:

            textureData    = np.zeros((5, 5, 5), dtype=np.uint8)
            textureData[:] = 255
            image          = fslimage.Image(textureData)
            norm           = None

        else:
            norm = image.dataRange

        texName = '{}_{}_{}_{}'.format(
            type(self).__name__, id(self.image), id(image), which)

        if opts is not None:
            unsynced = (opts.getParent() is None or
                        not opts.isSyncedToParent('volume'))

            # TODO If unsynced, this GLVectorBase needs to
            # update the mod/clip/colour textures whenever
            # their volume property changes.
            # Right?
            if unsynced:
                texName = '{}_unsync_{}'.format(texName, id(opts))

        if opts is not None: volume = opts.volume
        else:                volume = 0

        tex = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            image,
            normaliseRange=norm,
            volume=volume,
            notify=False,
            interp=interp)

        tex.register(self.name, self.__textureChanged)

        setattr(self, texAttr, tex)


    def refreshColourMapTexture(self, colourRes=256):
        """Called when the component colour maps need to be updated, when one
        of the :attr:`.VectorOpts.xColour`, ``yColour``, ``zColour``, ``cmap``,
        ``suppressX``, ``suppressY``, or ``suppressZ`` properties change.

        Regenerates the colour map texture.
        """

        display = self.display
        opts    = self.displayOpts

        if self.colourImage is not None:
            dmin, dmax = self.colourImage.dataRange

        else:
            dmin, dmax = 0.0, 1.0

        dmin, dmax = fslcm.briconToDisplayRange(
            (dmin, dmax),
            display.brightness / 100.0,
            display.contrast   / 100.0)

        self.cmapTexture.set(cmap=opts.cmap,
                             alpha=display.alpha / 100.0,
                             displayRange=(dmin, dmax))


    def getVectorColours(self):
        """Prepares the colours that represent each direction.


        Returns:
          - a ``numpy`` array of size ``(3, 4)`` containing the
            RGBA colours that correspond to the ``x``, ``y``, and ``z``
            vector directions.

          - A ``numpy`` array of shape ``(4, 4)`` which encodes a scale
            and offset to be applied to the vector value before it
            is combined with the colours, encoding the current
            brightness and contrast settings.
        """
        display = self.display
        opts    = self.displayOpts
        bri     = display.brightness / 100.0
        con     = display.contrast   / 100.0
        alpha   = display.alpha      / 100.0

        colours       = np.array([opts.xColour, opts.yColour, opts.zColour])
        colours[:, 3] = alpha

        if   opts.suppressMode == 'white':       suppress = [1, 1, 1, alpha]
        elif opts.suppressMode == 'black':       suppress = [0, 0, 0, alpha]
        elif opts.suppressMode == 'transparent': suppress = [0, 0, 0, 0]

        # Transparent suppression
        if opts.suppressX: colours[0, :] = suppress
        if opts.suppressY: colours[1, :] = suppress
        if opts.suppressZ: colours[2, :] = suppress

        # Scale/offset for brightness/contrast.
        # Note: This code is a duplicate of
        # that found in ColourMapTexture.
        lo, hi = fslcm.briconToDisplayRange((0, 1), bri, con)

        if hi == lo: scale = 0.0000000000001
        else:        scale = hi - lo

        xform = np.identity(4, dtype=np.float32)
        xform[0, 0] = 1.0 / scale
        xform[0, 3] = -lo * xform[0, 0]

        return colours, xform


    def getClippingRange(self):
        """Returns the :attr:`clippingRange`, suitable for use in the fragment
        shader. The returned values are transformed into the clip image
        texture value range, so the fragment shader can compare texture
        values directly to it.
        """

        opts = self.displayOpts

        clipLow, clipHigh = opts.clippingRange
        xform             = self.clipTexture.invVoxValXform

        if opts.clipImage is not None:
            clipLow  = clipLow  * xform[0, 0] + xform[0, 3]
            clipHigh = clipHigh * xform[0, 0] + xform[0, 3]
        else:
            clipLow  = -0.1
            clipHigh =  1.1

        return clipLow, clipHigh


    def getModulateRange(self):
        """Returns the :attr:`modulateRange`, suitable for use in the fragment
        shader. The returned values are transformed into the modulate image
        texture value range, so the fragment shader can compare texture values
        directly to it.
        """

        opts = self.displayOpts

        modLow, modHigh = opts.modulateRange
        xform           = self.modulateTexture.invVoxValXform

        if opts.modulateImage is not None:
            modLow  = modLow  * xform[0, 0] + xform[0, 3]
            modHigh = modHigh * xform[0, 0] + xform[0, 3]
        else:
            modLow  = 0
            modHigh = 1

        return modLow, modHigh


    def getAuxTextureXform(self, which):
        """Generates and returns a transformation matrix which can be used
        to transform texture coordinates from the vector image to the specified
        auxillary image (``'clip'``, ``'modulate'`` or ``'colour'``).
        """
        opts     = self.displayOpts
        auxImage = getattr(self, '{}Image'.format(which), None)
        auxOpts  = getattr(self, '{}Opts' .format(which), None)

        if auxImage is None:
            return np.eye(4)
        else:
            return transform.concat(
                auxOpts.getTransform('display', 'texture'),
                opts   .getTransform('texture', 'display'))


    def preDraw(self):
        """Must be called by subclass implementations.

        Ensures that all of the textures managed by this ``GLVectorBase`` are
        bound to their corresponding texture units.
        """

        self.modulateTexture.bindTexture(gl.GL_TEXTURE0)
        self.clipTexture    .bindTexture(gl.GL_TEXTURE1)
        self.colourTexture  .bindTexture(gl.GL_TEXTURE2)
        self.cmapTexture    .bindTexture(gl.GL_TEXTURE3)


    def postDraw(self):
        """Must be called by subclass implementations.

        Unbinds all of the textures managed by this ``GLVectorBase``.
        """

        self.modulateTexture.unbindTexture()
        self.clipTexture    .unbindTexture()
        self.colourTexture  .unbindTexture()
        self.cmapTexture    .unbindTexture()


    def __cmapPropChanged(self, *a):
        """Called when a :class:`.Display` or :class:`.VectorOpts` property
        affecting the vector colour map settings changes. Calls
        :meth:`refreshColourMapTexture` and :meth:`asyncUpdateShaderState`.
        """
        self.refreshColourMapTexture()
        self.asyncUpdateShaderState(alwaysNotify=True)


    def __colourImageChanged(self, *a):
        """Called when the :attr:`.VectorOpts.colourImage` changes. Registers
        with the new image, and refreshes textures as needed.
        """
        self.deregisterAuxImage('colour')
        self.registerAuxImage(  'colour')

        def onRefresh():
            self.compileShaders()
            self.refreshColourMapTexture()
            self.asyncUpdateShaderState(alwaysNotify=True)

        self.refreshAuxTexture('colour')
        async.idleWhen(onRefresh, self.texturesReady)


    def __modImageChanged(self, *a):
        """Called when the :attr:`.VectorOpts.modulateImage` changes.
        Registers with the new image, and refreshes textures as needed.
        """
        self.deregisterAuxImage('modulate')
        self.registerAuxImage(  'modulate')
        self.refreshAuxTexture( 'modulate')
        self.asyncUpdateShaderState(alwaysNotify=True)


    def __clipImageChanged(self, *a):
        """Called when the :attr:`.VectorOpts.clipImage` changes.
        Registers with the new image, and refreshes textures as needed.
        """
        self.deregisterAuxImage('clip')
        self.registerAuxImage(  'clip')
        self.refreshAuxTexture( 'clip')
        self.asyncUpdateShaderState(alwaysNotify=True)


    def __textureChanged(self, *a):
        """Called when any of the :class:`.ImageTexture` instances containing
        clipping, modulation or colour data, are refreshed. Notifies
        listeners of this ``GLVectorBase`` (via the :class:`.Notifier` base
        class).
        """
        self.asyncUpdateShaderState(alwaysNotify=True)


class GLVector(GLVectorBase):
    """The ``GLVector`` class is a sub-class of :class:`GLVectorBase`, which
    contains some additional logic for rendering :class:`.Image` overlays
    with a shape ``X*Y*Z*3``, and which contain directional data.


    By default , the ``image`` overlay passed to :meth:`__init__` is assumed
    to be an :class:`.Image` instance which contains vector data. If this is
    not the case, the ``vectorImage`` parameter may be used to pass in the
    :class:`.Image` that contains the vector data.


    This vector image is stored on the GPU as a 3D RGB :class:`.ImageTexture`,
    where the ``R`` channel contains the ``x`` vector values, the ``G``
    channel the ``y`` values, and the ``B`` channel the ``z`` values.

    This texture is bound to texture unit  ``gl.GL_TEXTURE4`` in the
    :meth:`preDraw` method.
    """

    def __init__(self, image, *args, **kwargs):
        """Create a ``GLVector``. All of the arguments documented here are
        optional, but if provided, must be passed as keyword arguments. All
        other arguments are passed through to :meth:`GLVectorBase.__init__`.


        :arg vectorImage:    If ``None``, the ``image`` is assumed to be a 4D
                             :class:`.Image` instance which contains the
                             vector data. If this is not the case, the
                             ``vectorImage`` parameter can be used to specify
                             an ``Image`` instance which does contain the
                             vector data.

        :arg prefilter:      An optional function which filters the data before
                             it is stored as a 3D texture. See
                             :class:`.Texture3D`. Regardless of whether this
                             function is provided, the data is always
                             transposed so that the fourth dimension is the
                             fastest changing, before being transferred to the
                             GPU.

        :arg prefilterRange: If the provided ``prefilter`` function will cause
                             the range of the data to change, this function
                             must be provided, and must, given the original
                             data range, return a suitably adjusted adjust data
                             range.
        """


        def defaultPrefilter(d):
            return d

        vectorImage    = kwargs.pop('vectorImage',    image)
        prefilter      = kwargs.pop('prefilter',      defaultPrefilter)
        prefilterRange = kwargs.pop('prefilterRange', None)

        if len(vectorImage.shape) != 4 or vectorImage.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ vector angles')

        self.vectorImage     = vectorImage
        self.imageTexture    = None
        self.prefilter       = prefilter
        self.prefilterRange  = prefilterRange

        # Using the preinit hook to overcome a slight
        # chicken-and-egg problem. We need to create
        # the image texture before shaders are created
        # (which are done via the init hook, as defined
        # in sub-classes, e.g. GLRGBVector). But we
        # need access to the display/displayopts objects
        # in order to configure the image texture.
        # So pre-init ensures that the GLObject refs
        # (display/displayOpts) are set up, then the
        # image texture is refreshed, then the init hook
        # is called.
        preinit = kwargs.pop('preinit', None)

        def preinitWrapper():
            self.refreshImageTexture()
            if preinit is not None:
                preinit()

        GLVectorBase.__init__(self,
                              image,
                              *args,
                              preinit=preinitWrapper,
                              **kwargs)


    def destroy(self):
        """Overrides :meth:`GLVectorBase.destroy`. Must be called when this
        ``GLVector`` is no longer needed. Calls :meth:`GLVectorBase.destroy`,
        and destroys the vector image texture.
        """

        GLVectorBase.destroy(self)
        self.imageTexture.deregister(self.name)
        glresources.delete(self.imageTexture.getTextureName())

        self.imageTexture = None


    def texturesReady(self):
        """Overrides :meth:`GLVectorBase.texturesReady`.  Returns ``True`` if
        all of the textures managed by this ``GLVector`` are ready to be used,
        ``False`` otherwise.
        """
        return (self.imageTexture is not None and
                self.imageTexture.ready()     and
                GLVectorBase.texturesReady(self))


    def refreshImageTexture(self, interp=gl.GL_NEAREST):
        """Called by :meth:`__init__`, and when the :class:`.ImageTexture`
        needs to be updated. (Re-)creates the ``ImageTexture``, using the
        :mod:`.resources` module so that the texture can be shared by other
        users.

        :arg interp: Interpolation method (``GL_NEAREST`` or ``GL_LINEAR``).
                     Used by sub-class implementations (see
                     :class:`.GLRGBVector`).
        """

        prefilter      = self.prefilter
        prefilterRange = self.prefilterRange
        vecImage       = self.vectorImage
        texName        = '{}_{}'.format(type(self).__name__, id(vecImage))

        if self.imageTexture is not None:
            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.getTextureName())

        # the fourth dimension (the vector directions)
        # must be the fastest changing in the texture data
        def realPrefilter(d):
            return prefilter(d.transpose((3, 0, 1, 2)))

        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            vecImage,
            nvals=3,
            interp=interp,
            normaliseRange=vecImage.dataRange,
            prefilter=realPrefilter,
            prefilterRange=prefilterRange,
            notify=False)

        self.imageTexture.register(self.name, self.__textureChanged)


    def preDraw(self):
        """Overrides :meth:`GLVectorBase`. Binds the vector image texture.
        """
        GLVectorBase.preDraw(self)
        self.imageTexture.bindTexture(gl.GL_TEXTURE4)


    def postDraw(self):
        """Overrides :meth:`GLVectorBase`. Unbinds the vector image texture.
        """
        GLVectorBase.postDraw(self)
        self.imageTexture.unbindTexture()


    def __textureChanged(self, *a):
        """Called when the :class:`.ImageTexture` instance containing the vector
        data is are refreshed. Notifies listeners of this ``GLVector`` (via the
        :class:`.Notifier` base class).
        """
        self.asyncUpdateShaderState(alwaysNotify=True)
