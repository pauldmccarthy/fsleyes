#!/usr/bin/env python
#
# transformer.py - The Transformer class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Transformer` class, which contains core
logic for managing affine transformations, and transforming coordinates
between all of the different coordinate systems that FSLeyes has to deal with.

The ``Transformer`` class is used by the :class:`.NiftiOpts` class to manage
transformations for :class:`.Nifti` / :class:`.Image` overlays.
"""


import numpy as np

from   fsl.transform     import affine
import fsl.data.mghimage as     fslmgh


class Transformer:
    """The ``Transformer`` class creates affine transformation matrices
    for one :class:`.Nifti` instance between FSLeyes coordinate systems.
    """

    def __init__(self, overlay, displayCtx, displaySpace, postmat=None):
        """Create a ``Transformer`` instance.

        :arg overlay:      A :class:`.Nifti` instance.

        :arg displayCtx:   The :class:`.DisplayContext` responsible for
                           displaying ``overlay``


        :arg displaySpace: Coordinate system into which the :class:`.Nifti`
                           instance is transformed for display. This is
                           *not* the :attr:`.DisplayContext.displaySpace`
                           setting. See the :attr:`.NiftiOpts.transform`
                           setting for more details.

        :arg postmat:      Optional world->world affine concatenated onto the
                           overlay voxel->world affine. This is used by the
                           :class:`.NiftiOpts` class for its
                           :attr:`.NiftiOpts.displayXform` setting.
        """
        self.displaySpace = displaySpace
        self.__overlay    = overlay
        self.__displayCtx = displayCtx
        self.__xforms     = createTransforms(overlay, displayCtx, postmat)


    @property
    def displaySpace(self):
        """Return the coordinate system that the :class:`.Nifti` instance
        associated with this Transformer is being displayed in.
        """
        return self.__displaySpace


    @displaySpace.setter
    def displaySpace(self, displaySpace):
        """Change the coordinate system that the :class:`.Nifti` instance
        associated with this Transformer is being displayed in.
        """
        if displaySpace not in ('affine', 'pixdim', 'pixdim-flip',
                                'id', 'reference', 'torig'):
            raise ValueError(f'Invalid displaySpace value: {displaySpace}')
        self.__displaySpace = displaySpace


    @property
    def overlay(self):
        """Returns a reference to the :class:`.Nifti` instance for this
        ``Transformer``.
        """
        return self.__overlay


    @property
    def displayCtx(self):
        """Returns a reference to the :class:`.DisplayContext` instance for
        this ``Transformer``.
        """
        return self.__displayCtx


    def getTransform(self, from_, to):
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

        ``torig``       Refers to the Freesurfer coordinate system.

        ``reference``   ``pixdim-flip`` coordinates of the reference image
                        specified by the :attr:`.DisplayContext.displaySpace`
                        attribute. If the ``displaySpace`` is set to
                        ``'world'``, this is equivalent to ``affine``.

        ``ref``         Equivalent to ``reference``.

        ``display``     Equivalent to the current value of
                        :attr:`displaySpace`.

        ``texture``     Voxel coordinates scaled to lie between 0.0 and 1.0,
                        suitable for looking up voxel values when stored as
                        an OpenGL texture.
        =============== ======================================================
        """


        if   from_ == 'display': from_ = self.displaySpace
        if   from_ == 'world':   from_ = 'affine'
        elif from_ == 'voxel':   from_ = 'id'
        elif from_ == 'pixflip': from_ = 'pixdim-flip'
        elif from_ == 'ref':     from_ = 'reference'

        if   to    == 'display': to    = self.displaySpace
        if   to    == 'world':   to    = 'affine'
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

        :returns:        The ``voxels``, rounded appropriately.
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
                        to,
                        vround=False,
                        vector=False,
                        pre=None,
                        post=None):
        """Transforms the given coordinates from ``from_`` to ``to``.

        The ``from_`` and ``to`` parameters must be those accepted by the
        :meth:`getTransform` method.

        :arg coords: Coordinates to transform
        :arg from_:  Space to transform from
        :arg to:     Space to transform to
        :arg vround: If ``True``, and ``to in ('voxel', 'id)``, the
                     transformed coordinates are rounded to the nearest
                     integer.
        :arg vector: Defaults to ``False``. If ``True``, the coordinates
                     are treated as vectors.
        :arg pre:    Transformation to apply before the ``from_``-to-``to``
                     transformation.
        :arg post:   Transformation to apply after the ``from_``-to-``to``
                     transformation.
        """

        xform = self.getTransform(from_, to)

        if pre  is not None: xform = affine.concat(xform, pre)
        if post is not None: xform = affine.concat(post, xform)

        coords = np.array(coords)
        coords = affine.transform(coords, xform, vector=vector)

        # Round to integer voxel coordinates?
        if to in ('voxel', 'id') and vround:
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


def createTransforms(image, displayCtx, postmat=None):
    """Creates affine matrices to transform between all coordinate systems.

    This function is used by the :class:`Transformer` class to set up affine
    matrices which can be used to transform coordinates from the given image's
    voxel and world coordinate systems into the FSLeyes display coordinate
    system. Refer to the :meth:`Transformer.getTransform` method for more
    details.

    :arg image:      :class:`.Nifti` instance to create transformations for.

    :arg displayCtx: The :class:`.DisplayContext` responsible for displaying
                     ``image``.

    :arg postmat:    Optional world->world transformation concatenated onto
                     the voxel->world affine - the :class:`NiftiOpts` class
                     uses this option for its ``displayXform`` property.
    """

    if postmat is None:
        postmat = np.eye(4)

    xforms          = {}
    shape           = np.array(image.shape[:3])
    voxToIdMat      = np.eye(4)
    voxToPixdimMat  = image.getAffine('voxel', 'scaled')
    voxToPixFlipMat = image.getAffine('voxel', 'fsl')
    voxToWorldMat   = image.getAffine('voxel', 'world')
    voxToWorldMat   = affine.concat(postmat, voxToWorldMat)
    voxToTorigMat   = fslmgh.voxToSurfMat(image)
    ds              = displayCtx.displaySpace

    # The reference transforms depend
    # on the value of displaySpace
    if ds == 'world':
        voxToRefMat = voxToWorldMat
    elif ds == 'scaledVoxel':
        voxToRefMat = voxToPixdimMat
    elif ds == 'fslview':
        voxToRefMat = voxToPixFlipMat
    elif ds is image:
        voxToRefMat = voxToPixFlipMat
    else:
        voxToRefMat = affine.concat(ds.getAffine('voxel', 'fsl'),
                                    ds.getAffine('world', 'voxel'),
                                    voxToWorldMat)

    # When going from voxels to textures,
    # we add 0.5 to centre the voxel (see
    # the note on coordinate systems at
    # the top of this file).
    voxToTexMat        = affine.scaleOffsetXform(tuple(1.0 / shape),
                                                 tuple(0.5 / shape))

    idToVoxMat         = affine.invert(voxToIdMat)
    idToPixdimMat      = affine.concat(voxToPixdimMat,  idToVoxMat)
    idToPixFlipMat     = affine.concat(voxToPixFlipMat, idToVoxMat)
    idToWorldMat       = affine.concat(voxToWorldMat,   idToVoxMat)
    idToRefMat         = affine.concat(voxToRefMat,     idToVoxMat)
    idToTexMat         = affine.concat(voxToTexMat,     idToVoxMat)
    idToTorigMat       = affine.concat(voxToTorigMat,   idToVoxMat)

    pixdimToVoxMat     = affine.invert(voxToPixdimMat)
    pixdimToIdMat      = affine.concat(voxToIdMat,      pixdimToVoxMat)
    pixdimToPixFlipMat = affine.concat(voxToPixFlipMat, pixdimToVoxMat)
    pixdimToWorldMat   = affine.concat(voxToWorldMat,   pixdimToVoxMat)
    pixdimToRefMat     = affine.concat(voxToRefMat,     pixdimToVoxMat)
    pixdimToTexMat     = affine.concat(voxToTexMat,     pixdimToVoxMat)
    pixdimToTorigMat   = affine.concat(voxToTorigMat,   pixdimToVoxMat)

    pixFlipToVoxMat    = affine.invert(voxToPixFlipMat)
    pixFlipToIdMat     = affine.concat(voxToIdMat,      pixFlipToVoxMat)
    pixFlipToPixdimMat = affine.concat(voxToPixdimMat,  pixFlipToVoxMat)
    pixFlipToWorldMat  = affine.concat(voxToWorldMat,   pixFlipToVoxMat)
    pixFlipToRefMat    = affine.concat(voxToRefMat,     pixFlipToVoxMat)
    pixFlipToTexMat    = affine.concat(voxToTexMat,     pixFlipToVoxMat)
    pixFlipToTorigMat  = affine.concat(voxToTorigMat,   pixFlipToVoxMat)

    worldToVoxMat      = affine.invert(voxToWorldMat)
    worldToIdMat       = affine.concat(voxToIdMat,      worldToVoxMat)
    worldToPixdimMat   = affine.concat(voxToPixdimMat,  worldToVoxMat)
    worldToPixFlipMat  = affine.concat(voxToPixFlipMat, worldToVoxMat)
    worldToRefMat      = affine.concat(voxToRefMat,     worldToVoxMat)
    worldToTexMat      = affine.concat(voxToTexMat,     worldToVoxMat)
    worldToTorigMat    = affine.concat(voxToTorigMat,   worldToVoxMat)

    refToVoxMat        = affine.invert(voxToRefMat)
    refToIdMat         = affine.concat(voxToIdMat,      refToVoxMat)
    refToPixdimMat     = affine.concat(voxToPixdimMat,  refToVoxMat)
    refToPixFlipMat    = affine.concat(voxToPixFlipMat, refToVoxMat)
    refToWorldMat      = affine.concat(voxToWorldMat,   refToVoxMat)
    refToTexMat        = affine.concat(voxToTexMat,     refToVoxMat)
    refToTorigMat      = affine.concat(voxToTorigMat,   refToVoxMat)

    texToVoxMat        = affine.invert(voxToTexMat)
    texToIdMat         = affine.concat(voxToIdMat,      texToVoxMat)
    texToPixdimMat     = affine.concat(voxToPixdimMat,  texToVoxMat)
    texToPixFlipMat    = affine.concat(voxToPixFlipMat, texToVoxMat)
    texToWorldMat      = affine.concat(voxToWorldMat,   texToVoxMat)
    texToRefMat        = affine.concat(voxToRefMat,     texToVoxMat)
    texToTorigMat      = affine.concat(voxToTorigMat,   texToVoxMat)

    torigToVoxMat        = affine.invert(voxToTorigMat)
    torigToIdMat         = affine.concat(voxToIdMat,      torigToVoxMat)
    torigToPixdimMat     = affine.concat(voxToPixdimMat,  torigToVoxMat)
    torigToPixFlipMat    = affine.concat(voxToPixFlipMat, torigToVoxMat)
    torigToWorldMat      = affine.concat(voxToWorldMat,   torigToVoxMat)
    torigToTexMat        = affine.concat(voxToTexMat,     torigToVoxMat)
    torigToRefMat        = affine.concat(voxToRefMat,     torigToVoxMat)

    xforms['id',  'id']          = np.eye(4)
    xforms['id',  'pixdim']      = idToPixdimMat
    xforms['id',  'pixdim-flip'] = idToPixFlipMat
    xforms['id',  'affine']      = idToWorldMat
    xforms['id',  'reference']   = idToRefMat
    xforms['id',  'texture']     = idToTexMat
    xforms['id',  'torig']       = idToTorigMat

    xforms['pixdim', 'pixdim']      = np.eye(4)
    xforms['pixdim', 'id']          = pixdimToIdMat
    xforms['pixdim', 'pixdim-flip'] = pixdimToPixFlipMat
    xforms['pixdim', 'affine']      = pixdimToWorldMat
    xforms['pixdim', 'reference']   = pixdimToRefMat
    xforms['pixdim', 'texture']     = pixdimToTexMat
    xforms['pixdim', 'torig']       = pixdimToTorigMat

    xforms['pixdim-flip', 'pixdim-flip'] = np.eye(4)
    xforms['pixdim-flip', 'id']          = pixFlipToIdMat
    xforms['pixdim-flip', 'pixdim']      = pixFlipToPixdimMat
    xforms['pixdim-flip', 'affine']      = pixFlipToWorldMat
    xforms['pixdim-flip', 'reference']   = pixFlipToRefMat
    xforms['pixdim-flip', 'texture']     = pixFlipToTexMat
    xforms['pixdim-flip', 'torig']       = pixFlipToTorigMat

    xforms['affine', 'affine']      = np.eye(4)
    xforms['affine', 'id']          = worldToIdMat
    xforms['affine', 'pixdim']      = worldToPixdimMat
    xforms['affine', 'pixdim-flip'] = worldToPixFlipMat
    xforms['affine', 'reference']   = worldToRefMat
    xforms['affine', 'texture']     = worldToTexMat
    xforms['affine', 'torig']       = worldToTorigMat

    xforms['reference', 'reference']   = np.eye(4)
    xforms['reference', 'id']          = refToIdMat
    xforms['reference', 'pixdim']      = refToPixdimMat
    xforms['reference', 'pixdim-flip'] = refToPixFlipMat
    xforms['reference', 'affine']      = refToWorldMat
    xforms['reference', 'texture']     = refToTexMat
    xforms['reference', 'torig']       = refToTorigMat

    xforms['texture', 'texture']     = np.eye(4)
    xforms['texture', 'id']          = texToIdMat
    xforms['texture', 'pixdim']      = texToPixdimMat
    xforms['texture', 'pixdim-flip'] = texToPixFlipMat
    xforms['texture', 'affine']      = texToWorldMat
    xforms['texture', 'reference']   = texToRefMat
    xforms['texture', 'torig']       = texToTorigMat

    xforms['torig', 'torig']       = np.eye(4)
    xforms['torig', 'id']          = torigToIdMat
    xforms['torig', 'pixdim']      = torigToPixdimMat
    xforms['torig', 'pixdim-flip'] = torigToPixFlipMat
    xforms['torig', 'affine']      = torigToWorldMat
    xforms['torig', 'texture']     = torigToTexMat
    xforms['torig', 'reference']   = torigToRefMat

    return xforms
