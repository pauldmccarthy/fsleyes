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
overlays can potentially be displayed in one of four coordinate systems:


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
 ============================== ===============================================


Pixdim flip
^^^^^^^^^^^


The :attr:`NiftiOpts.transform` property controls how the image data is
transformed into the display coordinate system. It allows any of the above
spaces to be specified (as ``id``, ``pixdim``, ``pixdim-flip``, or ``affine```
respectively), and also allows a ``custom`` transformation to be specified
(see the :attr:`customXform` property). This ``custom`` transformation is used
to transform one image into the space of another, by concatentating multiple
transformation matrices - see the :attr:`.DisplayContext.displaySpace`
property.


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

import fsl.data.image       as fslimage
import fsl.utils.transform  as transform
import fsleyes_props        as props

import fsleyes.colourmaps   as fslcm
from . import display       as fsldisplay
from . import colourmapopts as cmapopts


log = logging.getLogger(__name__)


class NiftiOpts(fsldisplay.DisplayOpts):
    """The ``NiftiOpts`` class describes how a :class:`.Nifti` overlay
    should be displayed.


    ``NiftiOpts`` is the base class for a number of :class:`.DisplayOpts`
    sub-classes - it contains display options which are common to all overlay
    types that represent a NIFTI image.
    """


    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """If the ``Image`` is 4D, the current volume to display."""


    transform = props.Choice(
        ('affine', 'pixdim', 'pixdim-flip', 'id', 'custom'),
        default='pixdim-flip')
    """This property defines how the overlay should be transformd into
    the display coordinate system. See the
    :ref:`note on coordinate systems <volumeopts-coordinate-systems>`
    for important information regarding this property.
    """


    customXform = props.Array(
        dtype=np.float64,
        shape=(4, 4),
        resizable=False,
        default=[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    """A custom transformation matrix which is used when the :attr:`transform`
    property is set to ``custom``.
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


    If the :attr:`.DisplayContext.displaySpace` is not equal to ``'world'``,
    changing the displayXform will not have any immediate effect.

    If you change the ``displayXform`` to temporarily change the , make sure
    to change it back to an identity matrix when you are done.
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

        # The transform property cannot be unsynced
        # across different displays, as it affects
        # the display context bounds, which also
        # cannot be unsynced
        nounbind = kwargs.get('nounbind', [])
        nounbind.append('transform')
        nounbind.append('customXform')
        nounbind.append('displayXform')
        nounbind.append('overrideDataRange')
        nounbind.append('enableOverrideDataRange')

        kwargs['nounbind'] = nounbind

        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)

        overlay = self.overlay

        # is this a 4D volume?
        if len(self.overlay.shape) == 4:
            self.setConstraint('volume', 'maxval', overlay.shape[3] - 1)

        # Because the transform properties cannot
        # be unbound between parents/children, all
        # NiftiOpts instances for a single overlay
        # will have the same values. Therefore
        # only the parent instance needs to
        # register for when they change.
        self.__registered = self.getParent() is None

        if self.__registered:
            overlay.register(self.name,
                             self.__overlayTransformChanged,
                             topic='transform')

            self.addListener('transform',
                             self.name,
                             self.__transformChanged,
                             immediate=True)
            self.addListener('customXform',
                             self.name,
                             self.__customXformChanged,
                             immediate=True)
            self.addListener('displayXform',
                             self.name,
                             self.__displayXformChanged,
                             immediate=True)

            # The display<->* transformation matrices
            # are created in the _setupTransforms method
            self.__xforms = {}
            self.__setupTransforms()
            self.__transformChanged()


    def destroy(self):
        """Calls the :meth:`.DisplayOpts.destroy` method. """

        if self.__registered:
            self.overlay.deregister(self.name, topic='transform')
            self.removeListener('transform',    self.name)
            self.removeListener('customXform',  self.name)
            self.removeListener('displayXform', self.name)

        fsldisplay.DisplayOpts.destroy(self)


    def __overlayTransformChanged(self, *a):
        """Called when the :class:`.Nifti` overlay sends a notification
        on the ``'transform'`` topic, indicating that its voxel->world
        transformation matrix has been updated.
        """
        stdLoc = self.displayToStandardCoordinates(
            self.displayCtx.location.xyz)

        self.__setupTransforms()
        self.__transformChanged()
        self.displayCtx.cacheStandardCoordinates(self.overlay, stdLoc)


    def __transformChanged(self, *a):
        """Called when the :attr:`transform` property changes.

        Calculates the min/max values of a 3D bounding box, in the display
        coordinate system, which is big enough to contain the image. Sets the
        :attr:`.DisplayOpts.bounds` property accordingly.
        """

        oldValue = self.getLastValue('transform')

        if oldValue is None:
            oldValue = self.transform

        self.displayCtx.cacheStandardCoordinates(
            self.overlay,
            self.transformCoords(self.displayCtx.location.xyz,
                                 oldValue,
                                 'world'))

        lo, hi = transform.axisBounds(
            self.overlay.shape[:3],
            self.getTransform('voxel', 'display'))

        self.bounds[:] = [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]]


    def __customXformChanged(self, *a):
        """Called when the :attr:`customXform` property changes.  Re-generates
        transformation matrices, and re-calculates the display :attr:`bounds`
        (via calls to :meth:`__setupTransforms` and
        :meth:`__transformChanged`).
        """

        stdLoc = self.displayToStandardCoordinates(
            self.displayCtx.location.xyz)

        self.__setupTransforms()
        if self.transform == 'custom':
            self.__transformChanged()

            # if transform == custom, the cached value
            # calculated in __transformChanged will be
            # wrong, so we have to overwrite it here.
            # The stdLoc value calculated above is valid,
            # because it was calculated before the
            # transformation matrices were recalculated
            # in __setupTransforms
            self.displayCtx.cacheStandardCoordinates(self.overlay, stdLoc)


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
        voxToPixFlipMat = np.array(voxToPixdimMat)
        voxToAffineMat  = image.voxToWorldMat
        voxToAffineMat  = transform.concat(self.displayXform, voxToAffineMat)
        voxToCustomMat  = self.customXform

        # When going from voxels to textures,
        # we add 0.5 to centre the voxel (see
        # the note on coordinate systems at
        # the top of this file).
        voxToTexMat     = transform.scaleOffsetXform(tuple(1.0 / shape),
                                                     tuple(0.5 / shape))

        # pixdim-flip space differs from
        # pixdim space only if the image
        # is in neurological orientation
        if image.isNeurological():
            x               = (image.shape[0] - 1) * image.pixdim[0]
            flip            = transform.scaleOffsetXform([-1, 1, 1], [x, 0, 0])
            voxToPixFlipMat = transform.concat(voxToPixFlipMat, flip)

        idToVoxMat         = transform.invert(voxToIdMat)
        idToPixdimMat      = transform.concat(voxToPixdimMat,  idToVoxMat)
        idToPixFlipMat     = transform.concat(voxToPixFlipMat, idToVoxMat)
        idToAffineMat      = transform.concat(voxToAffineMat,  idToVoxMat)
        idToCustomMat      = transform.concat(voxToCustomMat,  idToVoxMat)
        idToTexMat         = transform.concat(voxToTexMat,     idToVoxMat)

        pixdimToVoxMat     = transform.invert(voxToPixdimMat)
        pixdimToIdMat      = transform.concat(voxToIdMat,      pixdimToVoxMat)
        pixdimToPixFlipMat = transform.concat(voxToPixFlipMat, pixdimToVoxMat)
        pixdimToAffineMat  = transform.concat(voxToAffineMat,  pixdimToVoxMat)
        pixdimToCustomMat  = transform.concat(voxToCustomMat,  pixdimToVoxMat)
        pixdimToTexMat     = transform.concat(voxToTexMat,     pixdimToVoxMat)

        pixFlipToVoxMat    = transform.invert(voxToPixFlipMat)
        pixFlipToIdMat     = transform.concat(voxToIdMat,     pixFlipToVoxMat)
        pixFlipToPixdimMat = transform.concat(voxToPixdimMat, pixFlipToVoxMat)
        pixFlipToAffineMat = transform.concat(voxToAffineMat, pixFlipToVoxMat)
        pixFlipToCustomMat = transform.concat(voxToCustomMat, pixFlipToVoxMat)
        pixFlipToTexMat    = transform.concat(voxToTexMat,    pixFlipToVoxMat)

        affineToVoxMat     = transform.invert(voxToAffineMat)
        affineToIdMat      = transform.concat(voxToIdMat,      affineToVoxMat)
        affineToPixdimMat  = transform.concat(voxToPixdimMat,  affineToVoxMat)
        affineToPixFlipMat = transform.concat(voxToPixFlipMat, affineToVoxMat)
        affineToCustomMat  = transform.concat(voxToCustomMat,  affineToVoxMat)
        affineToTexMat     = transform.concat(voxToTexMat,     affineToVoxMat)

        customToVoxMat     = transform.invert(voxToCustomMat)
        customToIdMat      = transform.concat(voxToIdMat,      customToVoxMat)
        customToPixdimMat  = transform.concat(voxToPixdimMat,  customToVoxMat)
        customToPixFlipMat = transform.concat(voxToPixFlipMat, customToVoxMat)
        customToAffineMat  = transform.concat(voxToAffineMat,  customToVoxMat)
        customToTexMat     = transform.concat(voxToTexMat,     customToVoxMat)

        texToVoxMat        = transform.invert(voxToTexMat)
        texToIdMat         = transform.concat(voxToIdMat,      texToVoxMat)
        texToPixdimMat     = transform.concat(voxToPixdimMat,  texToVoxMat)
        texToPixFlipMat    = transform.concat(voxToPixFlipMat, texToVoxMat)
        texToAffineMat     = transform.concat(voxToAffineMat,  texToVoxMat)
        texToCustomMat     = transform.concat(voxToCustomMat , texToVoxMat)

        self.__xforms['id',  'id']          = np.eye(4)
        self.__xforms['id',  'pixdim']      = idToPixdimMat
        self.__xforms['id',  'pixdim-flip'] = idToPixFlipMat
        self.__xforms['id',  'affine']      = idToAffineMat
        self.__xforms['id',  'custom']      = idToCustomMat
        self.__xforms['id',  'texture']     = idToTexMat

        self.__xforms['pixdim', 'pixdim']      = np.eye(4)
        self.__xforms['pixdim', 'id']          = pixdimToIdMat
        self.__xforms['pixdim', 'pixdim-flip'] = pixdimToPixFlipMat
        self.__xforms['pixdim', 'affine']      = pixdimToAffineMat
        self.__xforms['pixdim', 'custom']      = pixdimToCustomMat
        self.__xforms['pixdim', 'texture']     = pixdimToTexMat

        self.__xforms['pixdim-flip', 'pixdim-flip'] = np.eye(4)
        self.__xforms['pixdim-flip', 'id']          = pixFlipToIdMat
        self.__xforms['pixdim-flip', 'pixdim']      = pixFlipToPixdimMat
        self.__xforms['pixdim-flip', 'affine']      = pixFlipToAffineMat
        self.__xforms['pixdim-flip', 'custom']      = pixFlipToCustomMat
        self.__xforms['pixdim-flip', 'texture']     = pixFlipToTexMat

        self.__xforms['affine', 'affine']      = np.eye(4)
        self.__xforms['affine', 'id']          = affineToIdMat
        self.__xforms['affine', 'pixdim']      = affineToPixdimMat
        self.__xforms['affine', 'pixdim-flip'] = affineToPixFlipMat
        self.__xforms['affine', 'custom']      = affineToCustomMat
        self.__xforms['affine', 'texture']     = affineToTexMat

        self.__xforms['custom', 'custom']      = np.eye(4)
        self.__xforms['custom', 'id']          = customToIdMat
        self.__xforms['custom', 'pixdim']      = customToPixdimMat
        self.__xforms['custom', 'pixdim-flip'] = customToPixFlipMat
        self.__xforms['custom', 'affine']      = customToAffineMat
        self.__xforms['custom', 'texture']     = customToTexMat

        self.__xforms['texture', 'texture']     = np.eye(4)
        self.__xforms['texture', 'id']          = texToIdMat
        self.__xforms['texture', 'pixdim']      = texToPixdimMat
        self.__xforms['texture', 'pixdim-flip'] = texToPixFlipMat
        self.__xforms['texture', 'affine']      = texToAffineMat
        self.__xforms['texture', 'custom']      = texToCustomMat


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

        ``custom``      Coordinates in the space defined by the custom
                        transformation matrix, as specified via the
                        :attr:`customXform` property.

        ``display``     Equivalent to the current value of :attr:`transform`.

        ``texture``     Voxel coordinates scaled to lie between 0.0 and 1.0,
                        suitable for looking up voxel values when stored as
                        an OpenGL texture.
        =============== ======================================================


        If the ``xform`` parameter is provided, and one of ``from_`` or ``to``
        is ``display``, the value of ``xform`` is used instead of the current
        value of :attr:`transform`.
        """

        # The parent NitfiOpts instance
        # manages transforms
        parent = self.getParent()
        if parent is not None:
            return parent.getTransform(from_, to, xform)

        if xform is None:
            xform = self.transform

        if   from_ == 'display': from_ = xform
        elif from_ == 'world':   from_ = 'affine'
        elif from_ == 'voxel':   from_ = 'id'
        elif from_ == 'pixflip': from_ = 'pixdim-flip'

        if   to    == 'display': to    = xform
        elif to    == 'world':   to    = 'affine'
        elif to    == 'voxel':   to    = 'id'
        elif to    == 'pixflip': to    = 'pixdim-flip'

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
        ornts = self.overlay.axisMapping(self.getTransform('voxel', 'display'))

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


    def transformCoords(self, coords, from_, to_, vround=False):
        """Transforms the given coordinates from ``from_`` to ``to_``.

        The ``from_`` and ``to_`` parameters must both be one of:

           - ``display``: The display coordinate system
           - ``voxel``:   The image voxel coordinate system
           - ``world``:   The image world coordinate system
           - ``custom``:  The coordinate system defined by the custom
                          transformation matrix (see :attr:`customXform`)

        :arg coords: Coordinates to transform
        :arg from_:  Space to transform from
        :arg to_:    Space to transform to
        :arg vround: If ``True``, and ``to_ == 'voxel'``, the transformed
                     coordinates are rounded to the nearest integer.
        """

        xform  = self.getTransform(from_, to_)
        coords = np.array(coords)
        coords = transform.transform(coords, xform)

        # Round to integer voxel coordinates?
        if to_ == 'voxel' and vround:
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


    def displayToStandardCoordinates(self, coords):
        """Overrides :meth:`.DisplayOpts.displayToStandardCoordinates`.
        Transforms the given display system coordinates into the world
        coordinates of the :class:`.Nifti` associated with this
        ``NiftiOpts`` instance.
        """
        return self.transformCoords(coords, 'display', 'world')


    def standardToDisplayCoordinates(self, coords):
        """Overrides :meth:`.DisplayOpts.standardToDisplayCoordinates`.
        Transforms the given coordinates (assumed to be in the world
        coordinate system of the ``Nifti`` associated with this ``NiftiOpts``
        instance) into the display coordinate system.
        """
        return self.transformCoords(coords, 'world', 'display')


class VolumeOpts(cmapopts.ColourMapOpts, NiftiOpts):
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
        cmapopts.ColourMapOpts.__init__(self)

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
        self.__registered = self.getParent() is None
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
            self.__clipImageChanged()


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

        cmapopts.ColourMapOpts.destroy(self)
        NiftiOpts             .destroy(self)


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


    def __clipImageChanged(self, *a):
        """Called when the :attr:`clipImage` property is changed. Updates
         the range of the :attr:`clippingRange` property.
        """

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

        self.updateDataRange(resetDR=False)
