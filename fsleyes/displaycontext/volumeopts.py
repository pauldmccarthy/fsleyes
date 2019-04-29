#!/usr/bin/env python
#
# volumeopts.py - Defines the VolumeOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`NiftiOpts` and :class:`VolumeOpts` classes.


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
                                stored in the NIFTI header.


 **radioloigcal scaled voxels** (a.k.a. ``pixdim-flip``) The image data voxel
                                coordinates are scaled by the ``pixdim`` values
                                stored in the NIFTI header and, if the image
                                appears to be stored in neurological order,
                                the X (left-right) axis is inverted.


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


Pixdim flip
^^^^^^^^^^^


The ``pixdim-flip`` transform is the coordinate system used internally by many
of the FSL tools.  For instance, this is the coordinate system used by
FSLView, by ``flirt``, and in the VTK sub-cortical segmentation model files
output by ``first``.


Furthermore, the vectors in eigenvector images images output by ``dtifit`` are
oriented according to this space, so if the input data is in neurological
orientation, these vectors need to be inverted along the x axis.


http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/FAQ#What_is_the_format_of_the_matrix_used_by_FLIRT.2C_and_how_does_it_relate_to_the_transformation_parameters.3F


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

import fsl.data.image                     as fslimage
import fsl.utils.transform                as transform
from   fsl.utils.platform import platform as fslplatform
import fsleyes_props                      as props

import fsleyes.colourmaps   as fslcm
from . import display       as fsldisplay
from . import colourmapopts as cmapopts
from . import volume3dopts  as vol3dopts


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
            self.__xforms    = {}
            self.__dsOverlay = None
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

        lo, hi = transform.axisBounds(
            self.overlay.shape[:3],
            self.getTransform('voxel', 'display'))

        self.bounds[:] = [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]]


    def __displaySpaceChanged(self, *a):
        """Called when the :attr:`.DisplayContext.displaySpace` property
        changes.  Re-generates transformation matrices, and re-calculates
        the display :attr:`bounds` (via calls to :meth:`__setupTransforms` and
        :meth:`__transformChanged`).
        """

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

        image = self.overlay
        shape = np.array(image.shape[:3])

        voxToIdMat      = np.eye(4)
        voxToPixdimMat  = np.diag(list(image.pixdim[:3]) + [1.0])
        voxToPixFlipMat = image.voxToScaledVoxMat
        voxToWorldMat   = image.voxToWorldMat
        voxToWorldMat   = transform.concat(self.displayXform, voxToWorldMat)
        ds              = self.displayCtx.displaySpace

        # The reference transforms depend on the value of
        # displaySpace
        if ds == 'world':
            voxToRefMat = voxToWorldMat
        elif ds is self.overlay:
            voxToRefMat = voxToPixFlipMat
        else:
            voxToRefMat = transform.concat(ds.voxToScaledVoxMat,
                                           ds.worldToVoxMat,
                                           voxToWorldMat)

        # When going from voxels to textures,
        # we add 0.5 to centre the voxel (see
        # the note on coordinate systems at
        # the top of this file).
        voxToTexMat        = transform.scaleOffsetXform(tuple(1.0 / shape),
                                                        tuple(0.5 / shape))

        idToVoxMat         = transform.invert(voxToIdMat)
        idToPixdimMat      = transform.concat(voxToPixdimMat,  idToVoxMat)
        idToPixFlipMat     = transform.concat(voxToPixFlipMat, idToVoxMat)
        idToWorldMat       = transform.concat(voxToWorldMat,   idToVoxMat)
        idToRefMat         = transform.concat(voxToRefMat,     idToVoxMat)
        idToTexMat         = transform.concat(voxToTexMat,     idToVoxMat)

        pixdimToVoxMat     = transform.invert(voxToPixdimMat)
        pixdimToIdMat      = transform.concat(voxToIdMat,      pixdimToVoxMat)
        pixdimToPixFlipMat = transform.concat(voxToPixFlipMat, pixdimToVoxMat)
        pixdimToWorldMat   = transform.concat(voxToWorldMat,   pixdimToVoxMat)
        pixdimToRefMat     = transform.concat(voxToRefMat,     pixdimToVoxMat)
        pixdimToTexMat     = transform.concat(voxToTexMat,     pixdimToVoxMat)

        pixFlipToVoxMat    = transform.invert(voxToPixFlipMat)
        pixFlipToIdMat     = transform.concat(voxToIdMat,      pixFlipToVoxMat)
        pixFlipToPixdimMat = transform.concat(voxToPixdimMat,  pixFlipToVoxMat)
        pixFlipToWorldMat  = transform.concat(voxToWorldMat,   pixFlipToVoxMat)
        pixFlipToRefMat    = transform.concat(voxToRefMat,     pixFlipToVoxMat)
        pixFlipToTexMat    = transform.concat(voxToTexMat,     pixFlipToVoxMat)

        worldToVoxMat      = transform.invert(voxToWorldMat)
        worldToIdMat       = transform.concat(voxToIdMat,      worldToVoxMat)
        worldToPixdimMat   = transform.concat(voxToPixdimMat,  worldToVoxMat)
        worldToPixFlipMat  = transform.concat(voxToPixFlipMat, worldToVoxMat)
        worldToRefMat      = transform.concat(voxToRefMat,     worldToVoxMat)
        worldToTexMat      = transform.concat(voxToTexMat,     worldToVoxMat)

        refToVoxMat        = transform.invert(voxToRefMat)
        refToIdMat         = transform.concat(voxToIdMat,      refToVoxMat)
        refToPixdimMat     = transform.concat(voxToPixdimMat,  refToVoxMat)
        refToPixFlipMat    = transform.concat(voxToPixFlipMat, refToVoxMat)
        refToWorldMat      = transform.concat(voxToWorldMat,   refToVoxMat)
        refToTexMat        = transform.concat(voxToTexMat,     refToVoxMat)

        texToVoxMat        = transform.invert(voxToTexMat)
        texToIdMat         = transform.concat(voxToIdMat,      texToVoxMat)
        texToPixdimMat     = transform.concat(voxToPixdimMat,  texToVoxMat)
        texToPixFlipMat    = transform.concat(voxToPixFlipMat, texToVoxMat)
        texToWorldMat      = transform.concat(voxToWorldMat,   texToVoxMat)
        texToRefMat        = transform.concat(voxToRefMat,     texToVoxMat)

        self.__xforms['id',  'id']          = np.eye(4)
        self.__xforms['id',  'pixdim']      = idToPixdimMat
        self.__xforms['id',  'pixdim-flip'] = idToPixFlipMat
        self.__xforms['id',  'affine']      = idToWorldMat
        self.__xforms['id',  'reference']   = idToRefMat
        self.__xforms['id',  'texture']     = idToTexMat

        self.__xforms['pixdim', 'pixdim']      = np.eye(4)
        self.__xforms['pixdim', 'id']          = pixdimToIdMat
        self.__xforms['pixdim', 'pixdim-flip'] = pixdimToPixFlipMat
        self.__xforms['pixdim', 'affine']      = pixdimToWorldMat
        self.__xforms['pixdim', 'reference']   = pixdimToRefMat
        self.__xforms['pixdim', 'texture']     = pixdimToTexMat

        self.__xforms['pixdim-flip', 'pixdim-flip'] = np.eye(4)
        self.__xforms['pixdim-flip', 'id']          = pixFlipToIdMat
        self.__xforms['pixdim-flip', 'pixdim']      = pixFlipToPixdimMat
        self.__xforms['pixdim-flip', 'affine']      = pixFlipToWorldMat
        self.__xforms['pixdim-flip', 'reference']   = pixFlipToRefMat
        self.__xforms['pixdim-flip', 'texture']     = pixFlipToTexMat

        self.__xforms['affine', 'affine']      = np.eye(4)
        self.__xforms['affine', 'id']          = worldToIdMat
        self.__xforms['affine', 'pixdim']      = worldToPixdimMat
        self.__xforms['affine', 'pixdim-flip'] = worldToPixFlipMat
        self.__xforms['affine', 'reference']   = worldToRefMat
        self.__xforms['affine', 'texture']     = worldToTexMat

        self.__xforms['reference', 'reference']   = np.eye(4)
        self.__xforms['reference', 'id']          = refToIdMat
        self.__xforms['reference', 'pixdim']      = refToPixdimMat
        self.__xforms['reference', 'pixdim-flip'] = refToPixFlipMat
        self.__xforms['reference', 'affine']      = refToWorldMat
        self.__xforms['reference', 'texture']     = refToTexMat

        self.__xforms['texture', 'texture']     = np.eye(4)
        self.__xforms['texture', 'id']          = texToIdMat
        self.__xforms['texture', 'pixdim']      = texToPixdimMat
        self.__xforms['texture', 'pixdim-flip'] = texToPixFlipMat
        self.__xforms['texture', 'affine']      = texToWorldMat
        self.__xforms['texture', 'reference']   = texToRefMat


    @classmethod
    def getVolumeProps(cls):
        """Overrides :meth:`DisplayOpts.getVolumeProps`. Returns a list
        of property names which control the displayed volume/timepoint.
        """
        return ['volume', 'volumeDim']


    def getTransform(self, from_, to, xform=None):
        """Return a matrix which may be used to transform coordinates
        from ``from_`` to ``to``. Valid values for ``from_`` and ``to``
        are:


        =============== ======================================================
        ``id``          Voxel coordinates

        ``voxel``       Equivalent to ``id``.

        ``pixdim``      Voxel coordinates, scaled by voxel dimensions

        ``pixdim-flip`` Voxel coordinates, scaled by voxel dimensions, and
                        with the X axis flipped if the affine matrix has
                        a positivie determinant. If the affine matrix does
                        not have a positive determinant, this is equivalent to
                        ``pixdim``.

        ``pixflip``     Equivalent to ``pixdim-flip``.

        ``affine``      World coordinates, as defined by the NIFTI
                        ``qform``/``sform``. See :attr:`.Image.voxToWorldMat`.

        ``world``       Equivalent to ``affine``.

        ``reference``   ``pixdim-flip`` coordinates of the reference image
                        specified by the :attr:`.DisplayContext.displaySpace`
                        attribute. If the ``displaySpace`` is set to
                        ``'world'``, this is equivalent to ``affine``.

        ``ref``         Equivalent to ``reference``.

        ``display``     Equivalent to the current value of :attr:`transform`.

        ``texture``     Voxel coordinates scaled to lie between 0.0 and 1.0,
                        suitable for looking up voxel values when stored as
                        an OpenGL texture.
        =============== ======================================================


        If the ``xform`` parameter is provided, and one of ``from_`` or ``to``
        is ``display``, the value of ``xform`` is used instead of the current
        value of :attr:`transform`.
        """

        if xform is None:
            xform = self.transform

        if   from_ == 'display': from_ = xform
        elif from_ == 'world':   from_ = 'affine'
        elif from_ == 'voxel':   from_ = 'id'
        elif from_ == 'pixflip': from_ = 'pixdim-flip'
        elif from_ == 'ref':     from_ = 'reference'

        if   to    == 'display': to    = xform
        elif to    == 'world':   to    = 'affine'
        elif to    == 'voxel':   to    = 'id'
        elif to    == 'pixflip': to    = 'pixdim-flip'
        elif to    == 'ref':     to    = 'reference'

        return self.__xforms[from_, to]


    def roundVoxels(self, voxels, daxes=None, roundOther=False):
        """Round the given voxel coordinates to integers. This is a
        surprisingly complicated operation.

        FSLeyes and the NIFTI standard map integer voxel coordinates to the
        voxel centre. For example, a voxel [3, 4, 5] fills the space::

            [2.5-3.5, 3.5-4.5, 4.5-5.5].


        So all we need to do is round to the nearest integer. But there are a
        few problems with breaking ties when rounding...


        The numpy.round function breaks ties (e.g. 7.5) by rounding to the
        nearest *even* integer, which can cause funky behaviour.  So instead
        of using numpy.round, we take floor(x+0.5), to force consistent
        behaviour (i.e. always rounding central values up).


        The next problem is that we have to round the voxel coordaintes
        carefully, depending on the orientation of the voxel axis w.r.t. the
        display axis. We want to round in the same direction in the display
        coordinate system, regardless of the voxel orientation. So we need to
        check the orientation of the voxel axis, and round down or up
        accordingly.


        This is to handle scenarios where we have two anatomically aligned
        images, but with opposing storage orders (e.g. one stored
        neurologically, and one stored radiologically). If we have such
        images, and the display location is on a voxel boundary, we want the
        voxel coordinates for one image to be rounded in the same anatomical
        direction (i.e. the same direction in the display coordinate
        system). Otherwise the same display location will map to mis-aligned
        voxels in the two images, because the voxel coordinate rounding will
        move in anatomically opposing directions.


        This method also prevents coordinates that are close to 0 from being
        set to -1, and coordinates that are close to the axis size from being
        set to (size + 1). In other words, voxel coordinates which are on the
        low or high boundaries will be rounded so as to be valid voxel
        coordinates.

        :arg voxels:     A ``(N, 3)`` ``numpy`` array containing the voxel
                         coordinates to be rounded.

        :arg daxes:      Display coordinate system axes along which to round
                         the coordinates (defaults to all axes).

        :arg roundOther: If ``True``, any voxel axes which are not in
                         ``daxes`` will still be rounded, but not with an
                         orientation-specific rounding convention.

        :returns:    The ``voxels``, rounded appropriately.
        """

        if daxes is None:
            daxes = list(range(3))

        shape = self.overlay.shape[:3]
        ornts = self.overlay.axisMapping(self.getTransform('display', 'voxel'))

        # We start by truncating the precision
        # of the coordinates, so that values
        # which are very close to voxel midpoints
        # (e.g. 0.49999), get rounded to 0.5.
        voxels = np.round(voxels, decimals=3)

        # Keep track of the voxel axes that
        # have had the rounding treatment
        roundedAxes = []

        for dax in daxes:

            ornt = ornts[dax]
            vax  = abs(ornt) - 1
            vals = voxels[:, vax]

            roundedAxes.append(vax)

            # Identify values which are close
            # to the low or high bounds - we
            # will clamp them after rounding.
            #
            # This is a third rounding problem
            # which is not documented above -
            # we clamp low/high values to avoid
            # them under/overflowing in the
            # floor/ceil operations below
            closeLow  = np.isclose(vals, -0.5)
            closeHigh = np.isclose(vals, shape[vax] - 0.5)

            # Round in a direction which is
            # dictated by the image orientation
            if ornt < 0: vals = np.floor(vals + 0.5)
            else:        vals = np.ceil( vals - 0.5)

            # Clamp low/high voxel coordinates
            vals[closeLow]  = 0
            vals[closeHigh] = shape[vax] - 1

            voxels[:, vax]  = vals

        # If the roundOther flag is true,
        # we round all other voxel axes
        # in a more conventional manner
        # (but still using floor(v + 0.5)
        # rather than round to avoid
        # annoying numpy even/odd behaviour).
        if roundOther:
            for vax in range(3):
                if vax not in roundedAxes:
                    voxels[:, vax] = np.floor(voxels[:, vax] + 0.5)

        return voxels


    def transformCoords(self,
                        coords,
                        from_,
                        to_,
                        vround=False,
                        vector=False,
                        pre=None,
                        post=None):
        """Transforms the given coordinates from ``from_`` to ``to_``.

        The ``from_`` and ``to_`` parameters must be those accepted by the
        :meth:`getTransform` method.

        :arg coords: Coordinates to transform
        :arg from_:  Space to transform from
        :arg to_:    Space to transform to
        :arg vround: If ``True``, and ``to_ in ('voxel', 'id)``, the
                     transformed coordinates are rounded to the nearest
                     integer.
        :arg vector: Defaults to ``False``. If ``True``, the coordinates
                     are treated as vectors.
        :arg pre:    Transformation to apply before the ``from_``-to-``to``
                     transformation.
        :arg post:   Transformation to apply after the ``from_``-to-``to``
                     transformation.
        """

        xform = self.getTransform(from_, to_)

        if pre  is not None: xform = transform.concat(xform, pre)
        if post is not None: xform = transform.concat(post, xform)

        coords = np.array(coords)
        coords = transform.transform(coords, xform, vector=vector)

        # Round to integer voxel coordinates?
        if to_ in ('voxel', 'id') and vround:
            coords = self.roundVoxels(coords)

        return coords


    def getVoxel(self, xyz=None, clip=True, vround=True):
        """Calculates and returns the voxel coordinates corresponding to the
        given location (assumed to be in the display coordinate system) for
        the :class:`.Nifti` associated with this ``NiftiOpts`` instance..

        :arg xyz:    Display space location to convert to voxels. If not
                     provided, the current :attr:`.DisplayContext.location`
                     is used.

        :arg clip:   If ``False``, and the transformed coordinates are out of
                     the voxel coordinate bounds, the coordinates returned
                     anyway. Defaults to ``True``.


        :arg vround: If ``True``, the returned voxel coordinates are rounded
                     to the nearest integer. Otherwise they may be fractional.


        :returns:    ``None`` if the location is outside of the image bounds,
                     unless ``clip=False``.
        """

        if xyz is not None: x, y, z = xyz
        else:               x, y, z = self.displayCtx.location.xyz

        overlay = self.overlay
        vox     = self.transformCoords([[x, y, z]],
                                       'display',
                                       'voxel',
                                       vround=vround)[0]

        if vround:
            vox = [int(v) for v in vox]

        if not clip:
            return vox

        for ax in (0, 1, 2):
            if vox[ax] < 0 or vox[ax] >= overlay.shape[ax]:
                return None

        return vox


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


class VolumeOpts(cmapopts.ColourMapOpts, vol3dopts.Volume3DOpts, NiftiOpts):
    """The ``VolumeOpts`` class defines options for displaying :class:`.Image`
    instances as regular 3D volumes.
    """


    clipImage = props.Choice()
    """Clip voxels according to the values in another image. By default, voxels
    are clipped by the values in the image itself - this property allows the
    user to choose another image by which voxels are to be clipped. Any image
    which is in the :class:`.OverlayList`, and which has the same voxel
    dimensions as the primary image can be selected for clipping. The
    :attr:`.ColourMapOpts.clippingRange` property dictates the values outside
    of which voxels are clipped.
    """


    interpolation = props.Choice(('none', 'linear', 'spline'))
    """How the value shown at a real world location is derived from the
    corresponding data value(s). ``none`` is equivalent to nearest neighbour
    interpolation.
    """


    @classmethod
    def getInitialDisplayRange(cls):
        """This class method returns a tuple containing ``(low, high)``
        percentile values which are used to set the initial values for the
        :attr:`.ColourMapOpts.displayRange` and
        :attr:`.ColourMapOpts.clippingRange` properties. If the initial
        display range has not yet been set (via the
        :meth:`setInitialDisplayRange` method), ``None`` is returned.
        """
        try:
            return cls.__initialDisplayRange
        except AttributeError:
            return None


    @classmethod
    def setInitialDisplayRange(cls, drange):
        """Sets the initial values for the :attr:`.ColourMapOpts.displayRange`
        and :attr:`.ColourMapOpts.clippingRange` to be used for new
        :class:`VolumeOpts` instances.

        :arg drange: A tuple containing ``(low, high)`` display range values
                     as percentiles of the image data range. May be ``None``,
                     in which case the initial display range will be set to the
                     image data range.
        """

        if drange is not None:
            low, high = drange
            if not all((low < high,
                        low >= 0,
                        low <= 100,
                        high >= 0,
                        high <= 100)):
                raise ValueError('Invalid initial display '
                                 'range: {}'.format(drange))

        cls.__initialDisplayRange = drange


    def __init__(self,
                 overlay,
                 display,
                 overlayList,
                 displayCtx,
                 **kwargs):
        """Create a :class:`VolumeOpts` instance for the specified ``overlay``,
        assumed to be an :class:`.Image` instance.

        All arguments are passed through to the :class:`.DisplayOpts`
        constructor.
        """

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslplatform.glVersion) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        # Interpolation cannot be unbound
        # between VolumeOpts instances. This is
        # primarily to reduce memory requirement
        # - if interpolation were different
        # across different views, we would have
        # to create multiple 3D image textures
        # for the same image.
        nounbind = kwargs.get('nounbind', [])
        nounbind.append('interpolation')
        nounbind.append('clipImage')
        kwargs['nounbind'] = nounbind

        # Some FSL tools will set the nifti aux_file
        # field to the name of a colour map - Check
        # to see if this is the case (do this before
        # calling __init__, so we don't clobber any
        # existing values).
        cmap = str(overlay.header.get('aux_file', 'none')).lower()

        if cmap == 'mgh-subcortical': cmap = 'subcortical'
        if cmap == 'mgh-cortical':    cmap = 'cortical'

        if cmap in fslcm.getColourMaps():
            self.cmap = cmap

        NiftiOpts.__init__(self,
                           overlay,
                           display,
                           overlayList,
                           displayCtx,
                           **kwargs)

        # Some things only happen
        # on the parent instance
        self.__registered = self.getParent() is None

        # Check whether the data range for this
        # image is silly. If it is, and we are
        # on a platform that cannot use floating
        # point textures, we turn on the override
        # data range option.
        if self.__registered and np.issubdtype(overlay.dtype, np.floating):
            import fsleyes.gl.textures.texture3d as t3d
            if not t3d.Texture3D.canUseFloatTextures()[0]:

                dmin, dmax = overlay.dataRange

                # a range of greater than 10e7
                # is defined as being "silly"
                if abs(dmax - dmin) > 10e7:

                    if   overlay.ndim == 3: sample = overlay[:]
                    elif overlay.ndim == 4: sample = overlay[..., 0]

                    drange = np.percentile(sample[sample != 0], [1, 99])

                    self.overrideDataRange       = drange
                    self.enableOverrideDataRange = True

        # Configure the initial display
        # range for new images, from the
        # initialDisplayRange percentiles.
        # We do this before ColourMapOpts.init
        drange = VolumeOpts.getInitialDisplayRange()

        if self.__registered and drange is not None:

            if   overlay.ndim == 3: sample = overlay[:]
            elif overlay.ndim == 4: sample = overlay[..., 0]

            drange = np.percentile(sample[sample != 0], drange)
            crange = [drange[0], overlay.dataRange[1]]

            self.displayRange  = drange
            self.clippingRange = crange

        cmapopts .ColourMapOpts.__init__(self)
        vol3dopts.Volume3DOpts .__init__(self)

        # Both parent and child VolumeOpts instances
        # listen for Image dataRange changes. The data
        # range for large images may be calculated
        # asynchronously on a separate thread, meaning
        # that data range updates may occur at random
        # times.
        #
        # If parent instances did not listen for data
        # range updates and, at startup, the following
        # sequence of events occurs:
        #
        #   1. Parent VolumeOpts instance created
        #
        #   2. Image.dataRange updated
        #
        #   3. Child VolumeOpts instance created
        #
        # The known parent data range will be 0-0,
        # the child will not receive any notification
        # about the data range change, and the child's
        # data range will be clobbered by the parent's.
        # This ugly situation is avoided simply by
        # having the parent track changes to the data
        # range in addition to all children.
        overlay.register(self.name,
                         self.__dataRangeChanged,
                         'dataRange',
                         runOnIdle=True)

        # We need to listen for changes to clipImage
        # and to [enable]overrideDataRange, as they
        # will change the display data range. These
        # cannot be unbound between parent/children,
        # so only the parent needs to listen.
        if self.__registered:
            overlayList.addListener('overlays',
                                    self.name,
                                    self.__overlayListChanged)
            self       .addListener('clipImage',
                                    self.name,
                                    self.__clipImageChanged)
            self       .addListener('enableOverrideDataRange',
                                    self.name,
                                    self.__enableOverrideDataRangeChanged)
            self       .addListener('overrideDataRange',
                                    self.name,
                                    self.__overrideDataRangeChanged)

            self.__overlayListChanged()
            self.__clipImageChanged(updateDataRange=False)


    def destroy(self):
        """Removes property listeners, and calls the :meth:`NiftiOpts.destroy`
        method.
        """

        overlay     = self.overlay
        overlayList = self.overlayList

        overlay.deregister(self.name, 'dataRange')

        if self.__registered:

            overlayList.removeListener('overlays',                self.name)
            self       .removeListener('clipImage',               self.name)
            self       .removeListener('enableOverrideDataRange', self.name)
            self       .removeListener('overrideDataRange',       self.name)

        cmapopts .ColourMapOpts.destroy(self)
        vol3dopts.Volume3DOpts .destroy(self)
        NiftiOpts              .destroy(self)


    def getDataRange(self):
        """Overrides :meth:`.ColourMapOpts.getDataRange`. Returns the
        :attr:`.Image.dataRange` of the image, or the
        :attr:`overrideDataRange` if it is active.
        """
        if self.enableOverrideDataRange: return self.overrideDataRange
        else:                            return self.overlay.dataRange


    def getClippingRange(self):
        """Overrides :meth:`.ColourMapOpts.getClippingRange`.
        If a :attr:`.clipImage` is set, returns its data range. Otherwise
        returns ``None``.
        """

        if self.clipImage is None:
            return cmapopts.ColourMapOpts.getClippingRange(self)
        else:
            return self.clipImage.dataRange


    def __dataRangeChanged(self, *a):
        """Called when the :attr:`.Image.dataRange` property changes.
        Calls :meth:`.ColourMapOpts.updateDataRange`.
        """
        self.updateDataRange(resetDR=False, resetCR=False)


    def __enableOverrideDataRangeChanged(self, *a):
        """Called when the :attr:`enableOverrideDataRange` property changes.
        Calls :meth:`.ColourMapOpts.updateDataRange`.
        """
        self.updateDataRange()


    def __overrideDataRangeChanged(self, *a):
        """Called when the :attr:`overrideDataRange` property changes.
        Calls :meth:`.ColourMapOpts.updateDataRange`.
        """
        self.updateDataRange()


    def __overlayListChanged(self, *a):
        """Called when the :`class:`.OverlayList` changes. Updates the
        options of the :attr:`clipImage` property.
        """

        clipProp = self.getProp('clipImage')
        clipVal  = self.clipImage
        overlays = self.displayCtx.getOrderedOverlays()

        options  = [None]

        for overlay in overlays:

            if overlay is self.overlay:                 continue
            if not isinstance(overlay, fslimage.Image): continue

            options.append(overlay)

        clipProp.setChoices(options, instance=self)

        if clipVal in options: self.clipImage = clipVal
        else:                  self.clipImage = None


    def __clipImageChanged(self, *a, **kwa):
        """Called when the :attr:`clipImage` property is changed. Updates
         the range of the :attr:`clippingRange` property.

        :arg updateDataRange: Defaults to ``True``. If ``False``, the
                              :meth:`.ColourMapOpts.updateDataRange` method
                              is not called.
        """

        updateDR = kwa.get('updateDataRange', True)

        haveClipImage = self.clipImage is not None

        if not haveClipImage:
            self.enableProperty('linkLowRanges')
            self.enableProperty('linkHighRanges')

        # If the clipping range is based on another
        # image, it makes no sense to link the low/
        # high display/clipping ranges, as they are
        # probably different. So if a clip image is
        # selected, we disable the link range
        # properties.
        elif self.propertyIsEnabled('linkLowRanges'):

            self.linkLowRanges  = False
            self.linkHighRanges = False

            self.disableProperty('linkLowRanges')
            self.disableProperty('linkHighRanges')

        log.debug('Clip image changed for {}: {}'.format(
            self.overlay,
            self.clipImage))

        if updateDR:
            self.updateDataRange(resetDR=False)
