#!/usr/bin/env python
#
# refimageopts.py - The RefImageOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`RefImageOpts` class, a mixin for use with
:class:`.DisplayOpts` sub-classes.
"""

import itertools            as it

import numpy                as np

import fsl.transform.affine as affine
import fsl.data.image       as fslimage
import fsl.data.mghimage    as fslmgh
import fsleyes_props        as props


class RefImageOpts:
    """The ``RefImageOpts`` class is a mixin to be used with
    :class:`.DisplayOpts` sub-classes. It is intended to be used for
    ``DisplayOpts`` class which store settings for overlays that are
    associated with a :class:`.Nifti` image, but are not ``Nifti`` overlays
    themselves.

    The ``RefImageOpts`` mixin provides a :attr:`refImage` property which
    identifies the reference ``Nifti`` image for the overlay. The ``refImage``
    property can be set to any loaded ``Nifti`` instance.

    See the :class:`.MeshOpts` and :class:`.TractogramOpts` classes for
    examples of ``DisplayOpts`` classes which use the ``RefImageOpts`` mixin.

    To use the ``RefImageOpts`` class, you must:

      1. Define your class to inherit from both :class:`.DisplayOpts` and
         ``RefImageOpts``::

             class MyOpts(DisplayOpts, RefImageOpts):
                 ...

      2. Call the ``RefImageOpts.__init__`` method *after*
         :meth:`.DisplayOpts.__init__`::

             def __init__(self, *args, **kwargs):
                 DisplayOpts.__init__(self, *args, **kwargs)
                 RefImageOpts.__init__(self)

      3. Implement the :meth:`getBounds` method to return the overlay bounds
         in its native coordinate system (the value of :attr:`coordSpace`).

      4. Call :meth:`updateBounds` whenever your overlay's native bounds
         change.

      5. Call :meth:`destroy` when your instance is being destroyed.
    """


    refImage = props.Choice()
    """A reference :class:`.Image` instance which the overlay is defined
    in terms of.

    For example, if a :class:`.Mesh` overlay represents the segmentation of
    a sub-cortical region from a T1 image, you would set the ``refImage`` to
    that T1 image.

    Any :class:`.Image` instance in the :class:`.OverlayList` may be chosen
    as the reference image.
    """


    coordSpace = props.Choice(
        ('affine', 'pixdim', 'pixdim-flip', 'id', 'torig'),
        default='pixdim-flip')
    """If :attr:`refImage` is not ``None``, this property defines the
    reference image coordinate space in which the coordinates of this
    overlay are defined (e.g. voxels, scaled voxels, world coordinates).

    =============== =========================================================
    ``affine``      The coordinates of this overlay are defined in the
                    reference image world coordinate system.

    ``id``          The coordinates of this overlay are defined in the
                    reference image voxel coordinate system.

    ``pixdim``      The coordinates of this overlay are defined in the
                    reference image voxel coordinate system, scaled by the
                    voxel pixdims.

    ``pixdim-flip`` The coordinates of this overlay are defined in the
                    reference image voxel coordinate system, scaled by the
                    voxel pixdims. If the reference image transformation
                    matrix has a positive determinant, the X axis is flipped.

    ``torig``       The coordinates of this overlay are defined in the
                    Freesurfer "Torig" / "vox2ras-tkr" coordinate system.
    =============== =========================================================

    The default value is ``pixdim-flip``, as this is the coordinate system
    used in the VTK sub-cortical segmentation model files output by FIRST.
    This can be overridden by sub-classes - see the :class:`.GiftiOpts` class
    for an example.

    See also the :ref:`note on coordinate systems
    <volumeopts-coordinate-systems>`, and the :meth:`.NiftiOpts.getTransform`
    method.
    """


    def __init__(self):
        """Initialise a ``RefImageOpts`` instance. This must be called
        *after* the :meth:`.DisplayOpts.__init__` method.
        """

        # A copy of the refImage property
        # value is kept here so, when it
        # changes, we can de-register from
        # the previous one.
        self.__oldRefImage = None

        self.__child = self.getParent() is not None

        if self.__child:
            olist = self.overlayList
            lname = self.listenerName

            olist.ilisten('overlays',   lname, self.__overlayListChanged)
            self .ilisten('refImage',   lname, self.__refImageChanged)
            self .ilisten('coordSpace', lname, self.updateBounds)

            self.__overlayListChanged()
            self.__refImageChanged()


    @property
    def referenceImage(self):
        """Overrides :meth:`.DisplayOpts.referenceImage`.

        If a :attr:`refImage` is selected, it is returned. Otherwise,``None``
        is returned.
        """
        return self.refImage


    @property
    def listenerName(self):
        """Returns a unique name for this ``RefImageOpts`` instance, which
        is distinct from its :meth:`.DisplayOpts.name`.
        """
        return f'RefImageOpts_{self.name}'


    def destroy(self):
        """Must be called when this ``RefImageOpts`` is being destroyed.
        De-registers property listeners.
        """
        if self.__child:
            olist = self.overlayList
            lname = self.listenerName
            ref   = self.refImage

            self.__oldRefImage = None

            olist.removeListener('overlays',   lname)
            self .removeListener('refImage',   lname)
            self .removeListener('coordSpace', lname)

            if ref is not None:
                # An exception may occur if the
                # DC has been/is being destroyed
                try:
                    ropts = self.displayCtx.getOpts(ref)
                    ropts.removeListener('bounds', lname)
                except Exception:
                    pass

            for overlay in self.overlayList:
                if not isinstance(overlay, fslimage.Nifti):
                    continue
                # An exception may occur if the
                # DC has been/is being destroyed
                try:
                    display = self.displayCtx.getDisplay(overlay)
                    display.remove('name', lname)
                except Exception:
                    pass


    def transformCoords(self, coords, from_=None, to=None, **kwargs):
        """Transforms the given ``coords`` from ``from_`` to ``to``.

        :arg coords: Coordinates to transform.
        :arg from_:  Space that the coordinates are in
        :arg to:     Space to transform the coordinates to

        All other parameters are passed through to the
        :meth:`.NiftiOpts.transformCoords` method of the reference image
        ``DisplayOpts``.

        The ``from_`` and ``to`` parameters may be set to any value accepted
        by :meth:`.NiftiOpts.getTransform`, in addition to ``'torig'``, which
        refers to the Freesurfer coordinate system.

        If ``from_`` or ``to`` are not provided, they are set to the current
        value of :attr:`coordSpace`.
        """

        ref = self.refImage

        if ref is None:
            return coords

        if from_ is None: from_ = self.coordSpace
        if to    is None: to    = self.coordSpace

        pre  = None
        post = None

        if from_ == 'torig':
            from_ = 'world'
            pre   = affine.concat(
                ref.getAffine('voxel', 'world'),
                affine.invert(fslmgh.voxToSurfMat(ref)))

        if to == 'torig':
            to   = 'world'
            post = affine.concat(
                fslmgh.voxToSurfMat(ref),
                ref.getAffine('world', 'voxel'))

        opts = self.displayCtx.getOpts(ref)
        return opts.transformCoords(
            coords, from_, to, pre=pre, post=post, **kwargs)


    def getTransform(self, from_=None, to=None):
        """Return a matrix which may be used to transform coordinates from
        ``from_`` to ``to``.

        If the :attr:`refImage` property is not set, an identity matrix is
        returned.

        The ``from_`` and ``to`` parameters may be set to any value accepted
        by :meth:`.NiftiOpts.getTransform`, in addition to ``'torig'``, which
        refers to the Freesurfer coordinate system.

        If ``from_`` or ``to`` are not provided, they are set to the current
        value of :attr:`coordSpace`.
        """
        ref = self.refImage

        if ref is None:
            return np.eye(4)

        if from_ is None: from_ = self.coordSpace
        if to    is None: to    = self.coordSpace

        pre  = np.eye(4)
        post = np.eye(4)

        if from_ == 'torig':
            from_ = 'world'
            pre   = affine.concat(
                ref.getAffine('voxel', 'world'),
                affine.invert(fslmgh.voxToSurfMat(ref)))

        if to == 'torig':
            to   = 'world'
            post = affine.concat(
                fslmgh.voxToSurfMat(ref),
                ref.getAffine('world', 'voxel'))

        ropts = self.displayCtx.getOpts(ref)
        xform = ropts.getTransform(from_, to)
        return affine.concat(post, xform, pre)


    def getBounds(self):
        """Must be implemented by sub-classes. Must return the
        overlay bounds in its native coordinate system (i.e. the coordinate
        system corresponding to :attr:`coordSpace`).
        """
        raise NotImplementedError()


    def updateBounds(self):
        """Called whenever any of the :attr:`refImage`, :attr:`coordSpace`,
        or :attr:`transform` properties change. May also be invoked by
        sub-classes to trigger a bounds update.

        Updates the :attr:`.DisplayOpts.bounds` property accordingly.
        """

        # create a bounding box for the
        # overlay vertices in their
        # native coordinate system
        lo, hi        = self.getBounds()
        xlo, ylo, zlo = lo
        xhi, yhi, zhi = hi

        # Transform the bounding box
        # into display coordinates
        xform         = self.getTransform(to='display')
        bbox          = list(it.product(*zip(lo, hi)))
        bbox          = affine.transform(bbox, xform)

        # re-calculate the min/max bounds
        x        = np.sort(bbox[:, 0])
        y        = np.sort(bbox[:, 1])
        z        = np.sort(bbox[:, 2])
        xlo, xhi = x.min(), x.max()
        ylo, yhi = y.min(), y.max()
        zlo, zhi = z.min(), z.max()

        oldBounds   = self.bounds
        self.bounds = [xlo, xhi, ylo, yhi, zlo, zhi]

        # make sure listeners are notified
        # even if bounds haven't changed
        if np.all(np.isclose(oldBounds, self.bounds)):
            self.propNotify('bounds')


    def __overlayListChanged(self):
        """Called when the overlay list changes. Updates the :attr:`refImage`
        property so that it contains a list of overlays which can be
        associated with the mesh.
        """

        imgProp  = self.getProp('refImage')
        imgVal   = self.refImage
        overlays = self.displayCtx.getOrderedOverlays()

        # the overlay for this MeshOpts
        # instance has been removed
        if self.overlay not in overlays:
            self.overlayList.removeListener('overlays', self.listenerName)
            return

        imgOptions = [None]

        for overlay in overlays:

            # The overlay must be a Nifti instance.
            if not isinstance(overlay, fslimage.Nifti):
                continue

            imgOptions.append(overlay)

            # Register a listener on the display names so
            # that any bound widgets get updated immediately
            display = self.displayCtx.getDisplay(overlay)
            display.addListener('name',
                                self.listenerName,
                                self.__overlayListChanged,
                                overwrite=True)

        # The previous refImage may have
        # been removed from the overlay list
        if imgVal in imgOptions: self.refImage = imgVal
        else:                    self.refImage = None

        imgProp.setChoices(imgOptions, instance=self)


    def __refImageChanged(self):
        """Called when the :attr:`refImage` property changes.

        If a new reference image has been specified, removes listeners from
        the old one (if necessary), and adds listeners to the
        :attr:`.NiftiOpts.bounds` property associated with the new reference
        image. Calls the :meth:`updateBounds` method.
        """

        # TODO You are not tracking changes to the
        # refImage overlay type -  if this changes,
        # you will need to re-bind to the transform
        # property of the new DisplayOpts instance
        lname = self.listenerName

        if self.__oldRefImage is not None and \
           self.__oldRefImage in self.overlayList:
            opts = self.displayCtx.getOpts(self.__oldRefImage)
            opts.removeListener('bounds', lname)

        self.__oldRefImage = self.refImage

        if self.refImage is not None:
            opts = self.displayCtx.getOpts(self.refImage)
            opts.ilisten('bounds', lname, self.updateBounds)

        self.updateBounds()
