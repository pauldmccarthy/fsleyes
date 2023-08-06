#!/usr/bin/env python
#
# manager.py - Utility classes for managing textures.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourMapTextureManager` and
:class:`AuxImageTextureManager` classes, which are utilities used used by
various :class:`.GLObject` classes for managing texture resources.
"""


import numpy     as np
import OpenGL.GL as gl

import fsl.data.image                   as fslimage
import fsl.transform.affine             as affine

import fsleyes.displaycontext.niftiopts as niftiopts
import fsleyes.gl.textures              as textures
import fsleyes.gl.resources             as glresources


class ColourMapTextureManager:
    """Class which manages :class:`.ColourMapTexture` instances associated with
    a :class:`.ColourMapOpts` instance.

    This class manages creation and configuration of two
    :class:`.ColourMapTexture` instances which are associated with the
    :attr:`.ColourMapOpts.cmap` and :attr:`.ColourMapOpts.negativeCmap`
    properties.
    """

    def __init__(self, globj, expalpha=False):
        """Create a ``ColourMapTextureManager``.

        :arg globj:    The :class:`.GLObject` that is using this manager.
        :arg expalpha: Defaults to ``False``. If ``True``, the
                       :attr:`.Display.alpha` value is scaled exponentially,
                       i.e. ``alpha = (Display.alpha / 100) ** 2)``.
        """
        self.__globj          = globj
        self.__expalpha       = expalpha
        self.__name           = '_'.join((type(self).__name__,
                                          type(globj).__name__,
                                          str(id(self))))
        self.__cmapTexture    = textures.ColourMapTexture(self.name)
        self.__negCmapTexture = textures.ColourMapTexture(f'{self.name}_neg')

        self.__addListeners()
        self.__refreshCmapTextures()


    def destroy(self):
        """Must be called when this ``ColourMapTextureManager`` is no longer
        needed. Destroyes the :class:`.ColourMapTexture` instances, removes
        property listeners, and clears references.
        """
        self.__removeListeners()
        self.__cmapTexture   .destroy()
        self.__negCmapTexture.destroy()
        self.__cmapTexture    = None
        self.__negCmapTexture = None

    @property
    def name(self):
        """Return a unique name for this ``ColourMapTextureManager``. """
        return self.__name

    @property
    def cmapTexture(self):
        """Return the :class:`.ColourMapTexture`. """
        return self.__cmapTexture

    @property
    def negCmapTexture(self):
        """Return the negative :class:`.ColourMapTexture`. """
        return self.__negCmapTexture


    def __addListeners(self):
        """Called by :meth:`__init__`. Adds property listeners to the
        :class:`.Display` / :class:`.DisplayOpts` instances.
        """
        name    = self.__name
        opts    = self.__globj.opts
        display = self.__globj.display
        refresh = self.__refreshCmapTextures
        display .addListener('alpha',            name, refresh)
        opts    .addListener('displayRange',     name, refresh)
        opts    .addListener('cmap',             name, refresh)
        opts    .addListener('negativeCmap',     name, refresh)
        opts    .addListener('gamma',            name, refresh)
        opts    .addListener('logScale',         name, refresh)
        opts    .addListener('cmapResolution',   name, refresh)
        opts    .addListener('interpolateCmaps', name, refresh)
        opts    .addListener('invert',           name, refresh)


    def __removeListeners(self):
        """Called by :meth:`destroy`. Removes property listeners from the
        :class:`.Display` / :class:`.DisplayOpts` instances.
        """
        name    = self.__name
        opts    = self.__globj.opts
        display = self.__globj.display
        display .removeListener('alpha',            name)
        opts    .removeListener('displayRange',     name)
        opts    .removeListener('cmap',             name)
        opts    .removeListener('negativeCmap',     name)
        opts    .removeListener('gamma',            name)
        opts    .removeListener('logScale',         name)
        opts    .removeListener('cmapResolution',   name)
        opts    .removeListener('interpolateCmaps', name)
        opts    .removeListener('invert',           name)


    def __refreshCmapTextures(self):
        """Refreshes the :class:`.ColourMapTexture` instances used to colour
        data.
        """

        display  = self.__globj.display
        opts     = self.__globj.opts
        alpha    = display.alpha / 100.0
        cmap     = opts.cmap
        res      = opts.cmapResolution
        logScale = opts.logScale
        gamma    = opts.realGamma(opts.gamma)
        negCmap  = opts.negativeCmap
        invert   = opts.invert
        interp   = opts.interpolateCmaps
        dmin     = opts.displayRange[0]
        dmax     = opts.displayRange[1]

        if self.__expalpha and alpha < 1:
            alpha = alpha ** 2

        self.__cmapTexture.set(cmap=cmap,
                               invert=invert,
                               alpha=alpha,
                               resolution=res,
                               gamma=gamma,
                               logScale=logScale,
                               interp=interp,
                               displayRange=(dmin, dmax))

        self.__negCmapTexture.set(cmap=negCmap,
                                  invert=invert,
                                  alpha=alpha,
                                  resolution=res,
                                  gamma=gamma,
                                  interp=interp,
                                  displayRange=(dmin, dmax))


class AuxImageTextureManager:
    """Utility class used by some :class:`GLImageObject` instances.

    The ``AuxImageTextureManager`` is used to manage "auxillary"
    :class:`.ImageTexture` instances which are used when rendering a
    ``GLObject``. For example, :class:`.GLVolume` instances may need to
    use an ``ImageTexture`` to store the data for the
    :attr:`.VolumeOpts.clipImage` setting.
    """


    def __init__(self, globj, **auximages):
        """Create an ``AuxImageTextureManager``.

        Note that an initial value *must* be given for each auxillary texture
        type.

        :arg globj:     The :class:`GLObject` which requires the
                        auxillary image textures.

        :arg auximages: ``auxtype=initial_value`` for each auxillary image
                        texture type. The initial value must be one of:

                         - an :class:`.Image`
                         - ``None``
                         - A tuple containing an ``Image``, and a dict
                           containing settings to initialise the
                           ``ImageTexture`` (passed as ``kwargs`` to
                           ``ImageTexture.__init__``).
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__globj       = globj
        self.__opts        = globj.opts
        self.__displayCtx  = globj.displayCtx
        self.__auxtypes    = tuple(auximages.keys())
        self.__auxopts     = {t : None for t in self.__auxtypes}
        self.__auximages   = {t : None for t in self.__auxtypes}
        self.__auxtextures = {t : None for t in self.__auxtypes}

        for which, image in auximages.items():
            if isinstance(image, tuple):
                image, settings = image
            else:
                settings = {}
            self.registerAuxImage(which, image, **settings)


    def destroy(self):
        """Must be calld when this ``AuxImageTextureManager`` is no longer
        needed. Clears references and destroys texture objects.
        """
        self.__globj      = None
        self.__displayCtx = None
        self.__opts       = None

        for t in self.__auxtypes:
            self.deregisterAuxImage(t, False)
            self.__destroyAuxTexture(t)


    @property
    def name(self):
        return self.__name


    @property
    def globj(self):
        return self.__globj


    @property
    def overlay(self):
        return self.globj.overlay


    @property
    def opts(self):
        return self.__opts


    @property
    def displayCtx(self):
        return self.__displayCtx


    def texture(self, which):
        return self.__auxtextures[which]


    def image(self, which):
        return self.__auximages[which]


    def textureXform(self, which):
        """Generates and returns a transformation matrix which can be used to
        transform texture coordinates from the main overlay to the specified
        auxillary image. If the main overlay is not an :class:`.Image`, the
        transformation matrix will transform from display coordinates to
        auxillary image texture coordinates.
        """
        opts     = self.opts
        auximage = self.__auximages[which]
        auxopts  = self.__auxopts[  which]

        if auximage is None:
            return np.eye(4)
        elif isinstance(opts, niftiopts.NiftiOpts):
            return affine.concat(
                auxopts.getTransform('display', 'texture'),
                opts   .getTransform('texture', 'display'))
        else:
            return auxopts.getTransform('display', 'texture')


    def texturesReady(self):
        """Returns ``True`` if all auxillary textures are in a usable
        state, ``False`` otherwise.
        """
        for tex in self.__auxtextures.values():
            if (tex is None) or (not tex.ready()):
                return False
        return True


    def registerAuxImage(self, which, image, **kwargs):
        """Register an auxillary image.

        Creates an :class:`.ImageTexture` to store the image data.
        Registers a listener with the :attr:`.NiftiOpts.volume` property of
        the image, so the texture can be updated when the image volume
        changes.

        :arg which: Name of the auxillary image
        :arg image: :class:`.Image` object

        All other arguments are passed through to the :meth:`refreshAuxTexture`
        method.
        """

        old = self.__auximages[which]

        if not isinstance(image, fslimage.Image):
            image = None

        # Image already registered
        if (image is not None) and (image is old):
            return

        if old is not None:
            self.deregisterAuxImage(which, False)

        if image is None:
            opts = None
        else:
            opts = self.displayCtx.getOpts(image)

            def volumeChange(*a):
                tex = self.texture(which)
                tex.set(volume=opts.index()[3:])

            opts.addListener('volume',
                             '{}_{}'.format(self.name, which),
                             volumeChange,
                             weak=False)

        self.__auximages[which] = image
        self.__auxopts[  which] = opts
        self.refreshAuxTexture(which, **kwargs)


    def deregisterAuxImage(self, which, refreshTexture=True):
        """De-register an auxillary image.  Deregisters the
        :attr:`.NiftiOpts.volume` listener that was registered in
        :meth:`registerAuxImage`, and destroys the associated
        :class:`.ImageTexture`.

        :arg which:          Name of the auxillary image

        :arg refreshTexture: Defaults to ``True``. Call
                             :meth:`refreshAuxTexture` to destroy the
                             associated ``ImageTexture``.
        """

        image = self.__auximages[which]
        opts  = self.__auxopts[  which]

        if image is None:
            return

        opts.removeListener('volume', '{}_{}'.format(self.name, which))

        self.__auximages[which] = None
        self.__auxopts[  which] = None

        if refreshTexture:
            self.refreshAuxTexture(which)


    def __destroyAuxTexture(self, which):
        """Destroys the :class:`.ImageTexture` for type ``which``. """
        tex = self.__auxtextures[which]
        if tex is not None:
            glresources.delete(tex.name)
        self.__auxtextures[which] = None


    def refreshAuxTexture(self, which, **kwargs):
        """Create/re-create an auxillary :class:`.ImageTexture`.

        The previous ``ImageTexture`` (if one exists) is destroyed.  If no
        :class:`.Image` of type ``which`` is currently registered, a small
        dummy ``Image`` and ``ImageTexture`` is created.

        :arg which: Name of the auxillary image

        All other arguments are passed through to the
        :class:`.ImageTexture.__init__` method.
        """

        self.__destroyAuxTexture(which)

        image = self.__auximages[  which]
        opts  = self.__auxopts[    which]
        tex   = self.__auxtextures[which]

        if image is None:
            textureData    = np.zeros((3, 3, 3), dtype=np.uint8)
            textureData[:] = 255
            image          = fslimage.Image(textureData)
            norm           = None
        else:
            norm = image.dataRange

        # by default we use a name which
        # is not coupled to the aux opts
        # instance, as the texture may be
        # sharable.
        texName = '{}_{}_{}_{}'.format(
            type(self).__name__, id(self.overlay), id(image), which)

        # check to see whether the aux
        # opts object is unsynced from
        # its parent - if so, we have to
        # create a dedicated texture
        if opts is not None:
            unsynced = (opts.getParent() is None or
                        not opts.isSyncedToParent('volume'))
            if unsynced:
                texName = '{}_unsync_{}'.format(texName, id(opts))

        if opts is not None: volume = opts.index()[3:]
        else:                volume = 0

        kwargs['notify'] = kwargs.get('notify', False)

        tex = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            image,
            initialise=False)

        # obtain a ref to the texture before it
        # initialises itself, in case a callback
        # function needs access to the texture
        self.__auxtextures[which] = tex
        tex.set(normaliseRange=norm, volume=volume, **kwargs)
