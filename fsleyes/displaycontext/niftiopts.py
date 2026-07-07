#!/usr/bin/env python
#
# niftiopts.py - The NiftiOpts class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`NiftiOpts` class.


.. _volumeopts-coordinate-systems:


---------------------------------------
An important note on coordinate systems
---------------------------------------


*FSLeyes* displays all overlays in a single coordinate system, referred
throughout as the *display coordinate system*. However, :class:`.Nifti`
overlays can potentially be transformed into the display coordinate system
in one of several ways:


 ============================== ===============================================
 **voxels**                     (a.k.a. ``id``) The image data voxel
                                coordinates map to the display coordinates.

 **scaled voxels**              (a.k.a. ``pixdim``) The image data voxel
                                coordinates are scaled by the ``pixdim`` values
                                stored in the NIFTI header. The origin is
                                fixed at the centre of voxel ``(0, 0, 0)``.

 **radioloigcal scaled voxels** (a.k.a. ``pixdim-flip``) The image data voxel
                                coordinates are scaled by the ``pixdim``
                                values stored in the NIFTI header and, if the
                                image appears to be stored in neurological
                                order, the X (left-right) axis is
                                inverted. The origin is fixed at the centre of
                                voxel ``(0, 0, 0)`` (or ``(X-1, 0, 0)`` for
                                inverted images).

 **world**                      (a.k.a. ``affine``) The image data voxel
                                coordinates are transformed by the
                                transformation matrix stored in the NIFTI
                                header - see the :class:`.Nifti` class for more
                                details.

 **reference**                  (a.k.a. ``reference``) The image data voxel
                                coordinates are transformed into the
                                ``pixdim-flip`` coordinate system of another,
                                *reference*, NIFTI image. The reference overlay
                                is specified by the
                                :attr:`.DisplayContext.displaySpace` attribute.
 ============================== ===============================================


The :attr:`NiftiOpts.transform` property controls how the image data is
transformed into the display coordinate system. It allows any of the above
spaces to be specified (as ``id``, ``pixdim``, ``pixdim-flip``, ``affine```,
or ``reference`` respectively).

All of the logic for managing these coordinate systems is defined in the
:class:`.Transformer` class - :class:`.NiftiOpts` instances will create and
use a new :class:`.Transformer` instance as needed.


Pixdim flip
^^^^^^^^^^^


The ``pixdim-flip`` transform is the coordinate system used internally by many
of the FSL tools.  For instance, this is the coordinate system used by
FSLView, by ``flirt``, and in the VTK sub-cortical segmentation model files
output by ``first``.


Furthermore, the vectors in eigenvector images images output by ``dtifit`` are
oriented according to this space, so if the input data is in neurological
orientation, these vectors need to be inverted along the x axis.


https://fsl.fmrib.ox.ac.uk/fsl/docs/#/registration/flirt/faq?id=what-is-the-format-of-the-matrix-used-by-flirt-and-how-does-it-relate-to-the-transformation-parameters


What is a voxel?
^^^^^^^^^^^^^^^^


Regardless of the space in which the ``Nifti`` is displayed , the
voxel-to-display space transformation (and in general, all of FSLeyes) assumes
that integer voxel coordinates correspond to the centre of the voxel in the
display coordinate system. In other words, a voxel at location::

    [x, y, z]


is assumed to occupy the space that corresponds to::

    [x-0.5 - x+0.5, y-0.5 - y+0.5, z-0.5 - z+0.5]


For example, if the :attr:`NiftiOpts.transform` property is set to ``id``, the
voxel::

    [2, 3, 4]

is drawn such that it occupies the space::

    [1.5 - 2.5, 2.5 - 3.5, 3.5 - 4.5]


This convention is in line with the convention defined by the ``NIFTI``
specification: it assumes that the voxel coordinates ``[x, y, z]`` correspond
to the centre of a voxel.
"""


import logging

import numpy as np

import fsl.data.image       as fslimage
import fsl.transform.affine as affine
import fsleyes_props        as props

import fsleyes.displaycontext.display     as fsldisplay
import fsleyes.displaycontext.transformer as transformer


log = logging.getLogger(__name__)



class NiftiOpts(fsldisplay.DisplayOpts):
    """The ``NiftiOpts`` class describes how a :class:`.Nifti` overlay
    should be displayed.


    ``NiftiOpts`` is the base class for a number of :class:`.DisplayOpts`
    sub-classes - it contains display options which are common to all overlay
    types that represent a NIFTI image.
    """


    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """If the ``Image`` has more than 3 dimensions, the current volume to
    display. The volume dimension is controlled by the :attr:`volumeDim`
    property.
    """


    volumeDim = props.Int(minval=0, maxval=5, default=0, clamped=True)
    """For images with more than three dimensions, this property controls
    the dimension that the :attr:`volume` property indexes into. When the
    ``volumeDim`` changes, the ``volume`` for the previous ``volumeDim``
    is fixed at its last value, and used for subsequent lookups.
    """


    transform = props.Choice(
        ('affine', 'pixdim', 'pixdim-flip', 'id', 'reference'),
        default='pixdim-flip')
    """This property defines how the overlay should be transformd into
    the display coordinate system. See the
    :ref:`note on coordinate systems <volumeopts-coordinate-systems>`
    for important information regarding this property.
    """


    displayXform = props.Array(
        dtype=np.float64,
        shape=(4, 4),
        resizable=False,
        default=[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    """A custom transformation matrix which is concatenated on to the voxel ->
    world transformation of the :class:`.Nifti` overlay.

    This transform is intended for temporary changes to the overlay display
    (when :attr:`.DisplayContext.displaySpace` ``== 'world'``) - changes to it
    will *not* result in the ::attr:`.DisplayContext.bounds` being updated.

    If you change the ``displayXform``, make sure to change it back to an
    identity matrix when you are done.
    """


    enableOverrideDataRange = props.Boolean(default=False)
    """By default, the :attr:`.Image.dataRange` property is used to set
    display and clipping ranges. However, if this property is ``True``,
    the :attr:`overrideDataRange` is used instead.

    ..note:: The point of this property is to make it easier to display images
             with a very large data range driven by outliers. On platforms
             which do not support floating point textures, these images are
             impossible to display unless they are normalised according to
             a smaller data range. See the
             :meth:`.Texture3D.__determineTextureType` method for some more
             details.
    """


    overrideDataRange = props.Bounds(ndims=1, clamped=False)
    """Data range used in place of the :attr:`.Image.dataRange` if the
    :attr:`enableOverrideDataRange` property is ``True``.
    """


    def __init__(self, *args, **kwargs):
        """Create a ``NiftiOpts`` instance.

        All arguments are passed through to the :class:`.DisplayOpts`
        constructor.
        """

        nounbind = kwargs.get('nounbind', [])
        nobind   = kwargs.get('nobind',   [])

        nounbind.append('overrideDataRange')
        nounbind.append('enableOverrideDataRange')
        nobind  .append('displayXform')

        kwargs['nounbind'] = nounbind
        kwargs['nobind']   = nobind

        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)

        self.__child = self.getParent() is not None

        if self.__child:

            # is this a >3D volume?
            ndims = self.overlay.ndim

            # We store indices for every dimension
            # past the XYZ dims. Whenever the volumeDim
            # changes, we cache the index for the old
            # dimensions, and restore the index for the
            # new dimension.
            self.setAttribute('volumeDim', 'maxval', max(0, ndims - 4))
            self.setAttribute('volume',    'cache',  [0] * (ndims - 3))

            if ndims <= 3:
                self.setAttribute('volume', 'maxval', 0)

            self.overlay   .register(   self.name,
                                        self.__overlayTransformChanged,
                                        topic='transform')
            self           .addListener('volumeDim',
                                        self.name,
                                        self.__volumeDimChanged,
                                        immediate=True)
            self           .addListener('transform',
                                        self.name,
                                        self.__transformChanged,
                                        immediate=True)
            self           .addListener('displayXform',
                                        self.name,
                                        self.__displayXformChanged,
                                        immediate=True)
            self.displayCtx.addListener('displaySpace',
                                        self.name,
                                        self.__displaySpaceChanged,
                                        immediate=True)

            # The display<->* transformation matrices
            # are created in the _setupTransforms method.
            # The __displaySpaceChanged method registers
            # a listener with the current display space
            # (if it is an overlay)
            self.__xforms    = None
            self.__dsOverlay = None
            self.__displaySpaceChanged(refresh=False)
            self.__setupTransforms()
            self.__transformChanged()
            self.__volumeDimChanged()


    def destroy(self):
        """Calls the :meth:`.DisplayOpts.destroy` method. """

        if self.__child:
            self.overlay   .deregister(    self.name, topic='transform')
            self.displayCtx.removeListener('displaySpace', self.name)
            self           .removeListener('volumeDim',    self.name)
            self           .removeListener('transform',    self.name)
            self           .removeListener('displayXform', self.name)

            if self.__dsOverlay is not None:
                self.__dsOverlay.deregister(self.name, topic='transform')
                self.__dsOverlay = None

        fsldisplay.DisplayOpts.destroy(self)


    def __toggleSiblingListeners(self, enable=True):
        """Enables/disables the ``volumeDim`` listeners of sibling
        ``NiftiOpts`` instances. This is used by the :meth:`__volumeDimChanged`
        method to avoid nastiness.
        """
        for s in self.getParent().getChildren():
            if s is not self:
                if enable: s.enableListener( 'volumeDim', s.name)
                else:      s.disableListener('volumeDim', s.name)


    def __volumeDimChanged(self, *a):
        """Called when the :attr:`volumeDim` changes. Saves the value of
        ``volume`` for the last ``volumeDim``, and restores the previous
        value of ``volume`` for the new ``volumeDim``.
        """

        if self.overlay.ndim <= 3:
            return

        # Here we disable volumeDim listeners on all
        # sibling instances, then save/restore the
        # volume value and properties asynchronously,
        # then re-enable the slblings.  This is a
        # horrible means of ensuring that only the
        # first VolumeOpts instance (out of a set of
        # synchronised instances) updates the volume
        # value and properties. The other instances
        # will be updated through synchronisation.
        # This is necessary because subsequent
        # instances would corrupt the update made by
        # the first instance.
        #
        # A nicer way to do things like this would be
        # nice.
        def update():

            oldVolume    = self.volume
            oldVolumeDim = self.getLastValue('volumeDim')

            if oldVolumeDim is None:
                oldVolumeDim = 0

            cache               = list(self.getAttribute('volume', 'cache'))
            cache[oldVolumeDim] = oldVolume
            newVolume           = cache[self.volumeDim]
            newVolumeLim        = self.overlay.shape[self.volumeDim + 3] - 1

            self.setAttribute('volume', 'maxval', newVolumeLim)
            self.setAttribute('volume', 'cache',  cache)
            self.volume = newVolume

        self.__toggleSiblingListeners(False)
        props.safeCall(update)
        props.safeCall(self.__toggleSiblingListeners, True)


    def __overlayTransformChanged(self, *a):
        """Called when the :class:`.Nifti` overlay sends a notification
        on the ``'transform'`` topic, indicating that its voxel->world
        transformation matrix has been updated.
        """
        self.__setupTransforms()
        self.__transformChanged()


    def __displaySpaceTransformChanged(self, *a):
        """Called when the :attr:`.DisplayContext.displaySpace` is a
        :class:`.Nifti`  overlay, and its :attr:`.Nifti.voxToWorldMat`
        changes. Updates the transformation matrices for this image.
        """
        self.__setupTransforms()
        self.__transformChanged()


    def __transformChanged(self, *a):
        """Called when the :attr:`transform` property changes.

        Calculates the min/max values of a 3D bounding box, in the display
        coordinate system, which is big enough to contain the image. Sets the
        :attr:`.DisplayOpts.bounds` property accordingly.
        """

        lo, hi = affine.axisBounds(
            self.overlay.shape[:3],
            self.getTransform('voxel', 'display'))

        self.bounds[:] = [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]]


    def __displaySpaceChanged(self, *a, **kwa):
        """Called when the :attr:`.DisplayContext.displaySpace` property
        changes.  Re-generates transformation matrices, and re-calculates
        the display :attr:`bounds` (via calls to :meth:`__setupTransforms` and
        :meth:`__transformChanged`).
        """

        refresh      = kwa.pop('refresh', True)
        displaySpace = self.displayCtx.displaySpace

        if self.__dsOverlay is not None:
            self.__dsOverlay.deregister(self.name, topic='transform')
            self.__dsOverlay = None

        # Register a listener on the display space reference
        # image, because when its voxToWorldMat changes, we
        # need to update our *toref and refto* transforms.
        if isinstance(displaySpace, fslimage.Nifti) and \
           displaySpace is not self.overlay:
            self.__dsOverlay = displaySpace
            self.__dsOverlay.register(self.name,
                                      self.__displaySpaceTransformChanged,
                                      topic='transform')

        if refresh:
            self.__setupTransforms()
            if self.transform == 'reference':
                self.__transformChanged()


    def __displayXformChanged(self, *a):
        """Called when the :attr:`displayXform` property changes. Updates
        the transformation matrices and :attr:`bounds` accordingly.

        Critically, when the :attr:`displayXform` property changes, the
        :class:`.DisplayContext` is *not* notified. This is because
        the ``displayXform`` is intended for temporary changes.
        """

        # The displayXform is intended as a temporary
        # transformation for display purposes - the
        # DisplayOpts.bounds property gets updated when
        # it changes, but we don't want the
        # DisplayContext.bounds property to be updated.
        # So we suppress all notification while
        # updating the transformation matrices.
        with self.displayCtx.freeze(self.overlay):
            self.__setupTransforms()
            self.__transformChanged()


    def __setupTransforms(self):
        """Calculates transformation matrices between all of the possible
        spaces in which the overlay may be displayed.

        These matrices are accessible via the :meth:`getTransform` method.
        """

        self.__xforms = transformer.Transformer(self.overlay,
                                                self.displayCtx,
                                                self,
                                                self.displayXform)


    @classmethod
    def getVolumeProps(cls):
        """Overrides :meth:`DisplayOpts.getVolumeProps`. Returns a list
        of property names which control the displayed volume/timepoint.
        """
        return ['volume', 'volumeDim']


    @property
    def transformer(self):
        """Overrides :meth:`.DisplayOpts.transformer`. Returns the
        :class:`.Transformer` instance  used by this :class:`.NiftiOpts`
        instance to transform coordinates.
        """
        return self.__xforms


    def getTransform(self, from_, to):
        """Return a matrix which may be used to transform coordinates
        from ``from_`` to ``to``.

        See the :meth:`.Transformer.getTransform` for more details.
        """

        if not self.__child:
            raise RuntimeError('getTransform cannot be called on '
                               'a parent NiftiOpts instance')

        return self.__xforms.getTransform(from_, to)


    def roundVoxels(self, voxels, **kwargs):
        """Round the given voxel coordinates to integers.

        See the :meth:`.Transformer.roundVoxels` method for details on the
        arguments and return value.
        """

        if not self.__child:
            raise RuntimeError('roundVoxels cannot be called on '
                               'a parent NiftiOpts instance')

        return self.__xforms.roundVoxels(voxels, **kwargs)


    def transformCoords(self,
                        coords,
                        from_,
                        to,
                        **kwargs):
        """Transforms the given coordinates from ``from_`` to ``to``.

        See the :meth:`.Transformer.transformCoords` method for details on the
        arguments and return value.
        """

        if not self.__child:
            raise RuntimeError('transformCoords cannot be called on '
                               'a parent NiftiOpts instance')

        return self.__xforms.transformCoords(coords, from_, to, **kwargs)


    def getVoxel(self, xyz=None, **kwargs):
        """Calculates and returns the voxel coordinates corresponding to the
        given location (assumed to be in the display coordinate system) for
        the :class:`.Nifti` associated with this ``NiftiOpts`` instance.

        See the :meth:`.Transformer.getVoxel` method for details on the
        arguments and return value.
        """

        if not self.__child:
            raise RuntimeError('getVoxel cannot be called on '
                               'a parent NiftiOpts instance')

        return self.__xforms.getVoxel(xyz, **kwargs)


    def setIndex(self, indices):
        """Sets the indexes of all non-spatial dimensions. The :attr:`volume`
        property is also updated.
        """
        if len(indices) != self.overlay.ndim - 3:
            raise ValueError(
                f'Wrong number of indices - {self.display.name} '
                f'has {self.overlay.ndim-3} non-spatial dimensions')
        self.setAttribute('volume', 'cache', indices)
        self.volume = indices[self.volumeDim]


    def index(self, slc=None, atVolume=True):
        """Given a slice object ``slc``, which indexes into the X, Y, and Z
        dimensions, fills it to slice every dimension of the image, using
        the current :attr:`volume` and :attr:`volumeDim`, and saved values
        for the other volume dimensions.

        :arg slc:      Something which can slice the first three dimensions
                       of the image. If ``None``, defaults to ``[:, :, :]``.

        :arg atVolume: If ``True``, the returned slice will index the current
                       :attr:`volume` of the current :attr:`volumeDim`.
                       Otherwise the returned slice will index across the whole
                       :attr:`volumeDim`.
        """

        if slc is None:
            slc = [slice(None), slice(None), slice(None)]

        if self.overlay.ndim <= 3:
            return tuple(slc)

        newSlc      = [None] * self.overlay.ndim
        newSlc[:3]  = slc
        newSlc[ 3:] = self.getAttribute('volume', 'cache')

        vdim = self.volumeDim + 3

        if atVolume: newSlc[vdim] = self.volume
        else:        newSlc[vdim] = slice(None)

        return tuple(newSlc)
