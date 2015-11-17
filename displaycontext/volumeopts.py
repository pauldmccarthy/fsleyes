#!/usr/bin/env python
#
# volumeopts.py - Defines the VolumeOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`ImageOpts` and :class:`VolumeOpts` classes.


.. _volumeopts-coordinate-systems:

---------------------------------------
An important note on coordinate systems
---------------------------------------


*FSLeyes* displays all overlays in a single coordinate system, referred
throughout as the *display coordinate system*. However, :class:`.Image`
overlays can potentially be displayed in one of three coordinate systems:


 ====================== ====================================================
 **voxel** space        (a.k.a. ``id``) The image data voxel coordinates
                        map to the display coordinates.

 **scaled voxel** space (a.k.a. ``pixdim``) The image data voxel coordinates
                        are scaled by the ``pixdim`` values stored in the
                        NIFTI1 header.

 **world** space        (a.k.a. ``affine``) The image data voxel coordinates
                        are transformed by the ``qform``/``sform``
                        transformation matrix stored in the NIFTI1 header.
 ====================== ====================================================


The :attr:`ImageOpts.transform` property controls how the image data is
transformed into the display coordinate system. It allows any of the above
spaces to be specified (as ``id``, ``pixdim`` or ``affine``` respectively),
and also allows a ``custom`` transformation to be specified (see the
:attr:`customXform` property).


Regardless of the space in which the ``Image`` is displayed , the
voxel-to-display space transformation assumes that integer voxel coordinates
correspond to the centre of the voxel in the display coordinate system. In
other words, a voxel at location::

    [x, y, z]


will be transformed such that, in the display coordinate system, it occupies
the space::

    [x-0.5 - x+0.5, y-0.5 - y+0.5, z-0.5 - z+0.5]


For example, if the :attr:`ImageOpts.transform` property is set to ``id``, the
voxel::

    [2, 3, 4]

is drawn such that it occupies the space::

    [1.5 - 2.5, 2.5 - 3.5, 3.5 - 4.5]


This convention is in line with the convention defined by the ``NIFTI1``
specification: it assumes that the voxel coordinates ``[x, y, z]`` correspond
to the centre of a voxel.
"""


import logging

import numpy as np

import props

import fsl.utils.transform    as transform
import fsl.fsleyes.colourmaps as fslcm
import fsl.fsleyes.actions    as actions
import display                as fsldisplay


log = logging.getLogger(__name__)


class ImageOpts(fsldisplay.DisplayOpts):
    """The ``ImageOpts`` class describes how an :class:`.Image` overlay
    should be displayed.

    
    ``ImageOpts`` is the base class for a number of :class:`.DisplayOpts`
    sub-classes - it contains display options which are common to all overlay
    types that represent a NIFTI1 image.
    """

    
    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """If the ``Image`` is 4D, the current volume to display.""" 

    
    resolution = props.Real(maxval=10, default=1, clamped=True)
    """Data resolution in the image world coordinate system. The minimum
    value is configured in :meth:`__init__`.
    """ 


    transform = props.Choice(
        ('affine', 'pixdim', 'id', 'custom'),
        default='pixdim')
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

 
    def __init__(self, *args, **kwargs):
        """Create an ``ImageOpts`` instance.

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

        kwargs['nounbind'] = nounbind

        fsldisplay.DisplayOpts.__init__(self, *args, **kwargs)

        overlay = self.overlay

        self.addListener('transform',
                         self.name,
                         self.__transformChanged,
                         immediate=True)
        self.addListener('customXform',
                         self.name,
                         self.__customXformChanged,
                         immediate=True)

        # The display<->* transformation matrices
        # are created in the _setupTransforms method
        self.__xforms = {}
        self.__setupTransforms()
        self.__transformChanged()
 
        # is this a 4D volume?
        if self.overlay.is4DImage():
            self.setConstraint('volume', 'maxval', overlay.shape[3] - 1)

        # limit resolution to the image dimensions
        self.resolution = min(overlay.pixdim[:3])
        self.setConstraint('resolution', 'minval', self.resolution)


    def destroy(self):
        """Calls the :meth:`.DisplayOpts.destroy` method. """
        self.removeListener('transform',   self.name)
        self.removeListener('customXform', self.name)
        fsldisplay.DisplayOpts.destroy(self)

        
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
 
        
    def __setupTransforms(self):
        """Calculates transformation matrices between all of the possible
        spaces in which the overlay may be displayed.

        These matrices are accessible via the :meth:`getTransform` method.
        """

        image = self.overlay

        voxToIdMat        = np.eye(4)
        voxToPixdimMat    = np.diag(list(image.pixdim[:3]) + [1.0])
        voxToAffineMat    = image.voxToWorldMat.T
        voxToCustomMat    = self.customXform
        
        idToVoxMat        = transform.invert(voxToIdMat)
        idToPixdimMat     = transform.concat(idToVoxMat, voxToPixdimMat)
        idToAffineMat     = transform.concat(idToVoxMat, voxToAffineMat)
        idToCustomMat     = transform.concat(idToVoxMat, voxToCustomMat)

        pixdimToVoxMat    = transform.invert(voxToPixdimMat)
        pixdimToIdMat     = transform.concat(pixdimToVoxMat, voxToIdMat)
        pixdimToAffineMat = transform.concat(pixdimToVoxMat, voxToAffineMat)
        pixdimToCustomMat = transform.concat(pixdimToVoxMat, voxToCustomMat)

        affineToVoxMat    = image.worldToVoxMat.T
        affineToIdMat     = transform.concat(affineToVoxMat, voxToIdMat)
        affineToPixdimMat = transform.concat(affineToVoxMat, voxToPixdimMat)
        affineToCustomMat = transform.concat(affineToVoxMat, voxToCustomMat)

        customToVoxMat    = transform.invert(voxToCustomMat)
        customToIdMat     = transform.concat(customToVoxMat, voxToIdMat)
        customToPixdimMat = transform.concat(customToVoxMat, voxToPixdimMat)
        customToAffineMat = transform.concat(customToVoxMat, voxToAffineMat)

        self.__xforms['id',  'id']     = np.eye(4)
        self.__xforms['id',  'pixdim'] = idToPixdimMat 
        self.__xforms['id',  'affine'] = idToAffineMat
        self.__xforms['id',  'custom'] = idToCustomMat

        self.__xforms['pixdim', 'pixdim'] = np.eye(4)
        self.__xforms['pixdim', 'id']     = pixdimToIdMat
        self.__xforms['pixdim', 'affine'] = pixdimToAffineMat
        self.__xforms['pixdim', 'custom'] = pixdimToCustomMat
 
        self.__xforms['affine', 'affine'] = np.eye(4)
        self.__xforms['affine', 'id']     = affineToIdMat
        self.__xforms['affine', 'pixdim'] = affineToPixdimMat
        self.__xforms['affine', 'custom'] = affineToCustomMat

        self.__xforms['custom', 'custom'] = np.eye(4)
        self.__xforms['custom', 'id']     = customToIdMat
        self.__xforms['custom', 'pixdim'] = customToPixdimMat
        self.__xforms['custom', 'affine'] = customToAffineMat


    def getTransform(self, from_, to, xform=None):
        """Return a matrix which may be used to transform coordinates
        from ``from_`` to ``to``. Valid values for ``from_`` and ``to``
        are:

        
        =========== ======================================================
        ``id``      Voxel coordinates
        
        ``voxel``   Equivalent to ``id``.
        
        ``pixdim``  Voxel coordinates, scaled by voxel dimensions
        
        ``affine``  World coordinates, as defined by the NIFTI1
                    ``qform``/``sform``. See :attr:`.Image.voxToWorldMat`.

        ``world``   Equivalent to ``affine``.

        ``custom``  Coordinates in the space defined by the custom
                    transformation matrix, as specified via the
                    :attr:`customXform` property.
        
        ``display`` Equivalent to the current value of :attr:`transform`.
        =========== ======================================================

        
        If the ``xform`` parameter is provided, and one of ``from_`` or ``to``
        is ``display``, the value of ``xform`` is used instead of the current
        value of :attr:`transform`.
        """

        if xform is None:
            xform = self.transform

        if   from_ == 'display': from_ = xform
        elif from_ == 'world':   from_ = 'affine'
        elif from_ == 'voxel':   from_ = 'id'
        
        if   to    == 'display': to    = xform
        elif to    == 'world':   to    = 'affine'
        elif to    == 'voxel':   to    = 'id'

        return self.__xforms[from_, to]


    def getTransformOffsets(self, from_, to_):
        """Returns a set of offsets which should be applied to coordinates
        before/after applying a transfromation.  
        
        When an image is displayed in ``id``, ``pixdim`` and ``affine`` space,
        voxel coordinates map to the voxel centre, so our voxel from above will
        occupy the space ``(-0.5 - 0.5, 0.5 - 1.5, 1.5 - 2.5)``. This is
        dictated by the NIFTI specification. See the
        :ref:`note on coordinate systems <volumeopts-coordinate-systems>`.

        
        This function returns some offsets to ensure that the coordinate
        transformation from the source space to the target space is valid,
        given the above requirements.


        A tuple containing two sets of offsets (each of which is a tuple of
        three values). The first set is to be applied to the source
        coordinates (in the ``from_`` space) before transformation, and the
        second set to the target coordinates (in the ``to_`` space) after the
        transformation.

        
        See also the :meth:`transformCoords` method, which will perform the
        transformation correctly for you, without you having to worry about
        these silly offsets.

        
        .. note:: This method was written during a crazy time when, in ``id``
                  or ``pixdim`` space, voxels ``(0, 0, 0)`` of images overlaid
                  on each other were aligned at the voxel corner, whereas in
                  ``affine`` space, they were aligned at the voxel
                  centre. This is no longer the case, so this method is not
                  actually necessary, and just returns all zeros. But it is
                  still here, and still being used, just in case we need to
                  change these conventions again in the future.
        """
        return (0, 0, 0), (0, 0, 0)


    def transformCoords(self, coords, from_, to_):
        """Transforms the given coordinates from ``from_`` to ``to_``.

        The ``from_`` and ``to_`` parameters must both be one of:
        
           - ``display``: The display coordinate system
           - ``voxel``:   The image voxel coordinate system
           - ``world``:   The image world coordinate system
           - ``custom``:  The coordinate system defined by the custom
                          transformation matrix (see :attr:`customXform`)
        """

        xform     = self.getTransform(       from_, to_)
        pre, post = self.getTransformOffsets(from_, to_)
        
        coords    = np.array(coords) + pre
        coords    = transform.transform(coords, xform)

        return coords + post

    
    def getVoxel(self):
        """Calculates and returns the voxel coordinates corresponding to the
        current :attr:`.DisplayContext.location` for the :class:`.Image`
        associated with this ``ImageOpts`` instance.

        Returns ``None`` if the current location is outside of the image
        bounds.
        """

        overlay = self.overlay
        x, y, z = self.displayCtx.location.xyz

        vox     = self.transformCoords([[x, y, z]], 'display', 'voxel')[0]
        vox     = map(int, np.round(vox))

        if vox[0] < 0                 or \
           vox[1] < 0                 or \
           vox[2] < 0                 or \
           vox[0] >= overlay.shape[0] or \
           vox[1] >= overlay.shape[1] or \
           vox[2] >= overlay.shape[2]:
            return None

        return vox 


    def displayToStandardCoordinates(self, coords):
        """Overrides :meth:`.DisplayOpts.displayToStandardCoordinates`.
        Transforms the given display system coordinates into the world
        coordinates of the :class:`.Image` associated with this
        ``ImageOpts`` instance.
        """
        return self.transformCoords(coords, 'display', 'world')

    
    def standardToDisplayCoordinates(self, coords):
        """Overrides :meth:`.DisplayOpts.standardToDisplayCoordinates`.
        Transforms the given coordinates (assumed to be in the world
        coordinate system of the ``Image`` associated with this ``ImageOpts``
        instance) into the display coordinate system.
        """ 
        return self.transformCoords(coords, 'world', 'display')


class VolumeOpts(ImageOpts):
    """The ``VolumeOpts`` class defines options for displaying :class:`.Image`
    instances as regular 3D volumes.

    The ``VolumeOpts`` class links the :attr:`.Display.brightness` and
    :attr:`.Display.contrast` properties to its own :attr:`displayRange`
    property, so changes in either of the former will result in a change to
    the latter, and vice versa. This relationship is defined by the
    :func:`~.colourmaps.displayRangeToBricon` and
    :func:`~.colourmaps.briconToDisplayRange` functions, in the
    :mod:`.colourmaps` module.

    In addition to all of the display properties, ``VolumeOpts`` instances
    have the following attributes:

    =========== ===============================
    ``dataMin`` The minimum value in the image.
    ``dataMax`` The maximum value in the image.
    =========== ===============================

    For large images (where *large* is arbitrarily defined in
    :meth:`__init__`), the ``dataMin`` and ``dataMax`` attributes will contain
    range of a sample of the image data, rather their actual values. This is
    purely to eliminate the need to calculate minimum/maximum values over very
    large (and potentially memory-mapped) images, which can be a time
    consuming operation.


    ``VolumeOpts`` instances provide the following  :mod:`.actions`:

    .. autosummary::
       :nosignatures:

       resetDisplayRange
    """

    
    displayRange = props.Bounds(ndims=1)
    """Image values which map to the minimum and maximum colour map colours."""

    
    clippingRange = props.Bounds(ndims=1)
    """Values outside of this range are not shown."""

    
    invertClipping = props.Boolean(default=False)
    """If ``True``, the behaviour of :attr:`clippingRange` is inverted, i.e.
    values inside the clipping range are clipped, instead of those outside
    the clipping range.
    """

    
    cmap = props.ColourMap()
    """The colour map, a :class:`matplotlib.colors.Colourmap` instance."""

    
    interpolation = props.Choice(('none', 'linear', 'spline'))
    """How the value shown at a real world location is derived from the
    corresponding data value(s). ``none`` is equivalent to nearest neighbour
    interpolation.
    """


    invert = props.Boolean(default=False)
    """Use an inverted version of the current colour map (see the :attr:`cmap`
    property).
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

        # Attributes controlling image display. Only
        # determine the real min/max for small images -
        # if it's memory mapped, we have no idea how big
        # it may be! So we calculate the min/max of a
        # sample (either a slice or an image, depending
        # on whether the image is 3D or 4D)
        if np.prod(overlay.shape) > 2 ** 30:
            sample = overlay.data[..., overlay.shape[-1] / 2]
            self.dataMin = float(np.nanmin(sample))
            self.dataMax = float(np.nanmax(sample))
        else:
            self.dataMin = float(np.nanmin(overlay.data))
            self.dataMax = float(np.nanmax(overlay.data))

        if np.any(np.isnan((self.dataMin, self.dataMax))):
            self.dataMin = 0
            self.dataMax = 0

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 10000.0

        self.clippingRange.xmin = self.dataMin - dMinDistance
        self.clippingRange.xmax = self.dataMax + dMinDistance
        
        # By default, the lowest values
        # in the image are clipped
        self.clippingRange.xlo  = self.dataMin + dMinDistance
        self.clippingRange.xhi  = self.dataMax + dMinDistance

        self.displayRange.xlo  = self.dataMin
        self.displayRange.xhi  = self.dataMax

        # The Display.contrast property expands/contracts
        # the display range, by a scaling factor up to
        # approximately 10.
        self.displayRange.xmin = self.dataMin - 10 * dRangeLen
        self.displayRange.xmax = self.dataMax + 10 * dRangeLen
        
        self.setConstraint('displayRange', 'minDistance', dMinDistance)

        ImageOpts.__init__(self,
                           overlay,
                           display,
                           overlayList,
                           displayCtx,
                           **kwargs)

        # The displayRange property of every child VolumeOpts
        # instance is linked to the corresponding 
        # Display.brightness/contrast properties, so changes
        # in one are reflected in the other.
        if kwargs.get('parent', None) is not None:
            display.addListener('brightness', self.name, self.__briconChanged)
            display.addListener('contrast',   self.name, self.__briconChanged)
            self   .addListener('displayRange',
                                self.name,
                                self.__displayRangeChanged)

            # Because displayRange and bri/con are intrinsically
            # linked, it makes no sense to let the user sync/unsync
            # them independently. So here we are binding the boolean
            # sync properties which control whether the dRange/bricon
            # properties are synced with their parent. So when one
            # property is synced/unsynced, the other ones are too.
            self.bindProps(self   .getSyncPropertyName('displayRange'),
                           display,
                           display.getSyncPropertyName('brightness'))
            self.bindProps(self   .getSyncPropertyName('displayRange'), 
                           display,
                           display.getSyncPropertyName('contrast'))


    @actions.action
    def resetDisplayRange(self):
        """Resets the display range to the data range."""
        self.displayRange.x = [self.dataMin, self.dataMax]


    def destroy(self):
        """Removes property listeners, and calls the :meth:`ImageOpts.destroy`
        method.
        """

        if self.getParent() is not None:
            display = self.display
            display.removeListener('brightness',   self.name)
            display.removeListener('contrast',     self.name)
            self   .removeListener('displayRange', self.name)
            self.unbindProps(self   .getSyncPropertyName('displayRange'),
                             display,
                             display.getSyncPropertyName('brightness'))
            self.unbindProps(self   .getSyncPropertyName('displayRange'), 
                             display,
                             display.getSyncPropertyName('contrast'))

        ImageOpts.destroy(self)


    def __toggleListeners(self, enable=True):
        """This method enables/disables the property listeners which
        are registered on the :attr:`displayRange` and
        :attr:`.Display.brightness`/:attr:`.Display.contrast`/properties.
        
        Because these properties are linked via the
        :meth:`__displayRangeChanged` and :meth:`__briconChanged` methods,
        we need to be careful about avoiding recursive callbacks.

        Furthermore, because the properties of both :class:`VolumeOpts` and
        :class:`.Display` instances are possibly synchronised to a parent
        instance (which in turn is synchronised to other children), we need to
        make sure that the property listeners on these other sibling instances
        are not called when our own property values change. So this method
        disables/enables the property listeners on all sibling ``VolumeOpts``
        and ``Display`` instances.
        """

        parent = self.getParent()

        # this is the parent instance
        if parent is None:
            return

        # The parent.getChildren() method will
        # contain this VolumeOpts instance,
        # so the below loop toggles listeners
        # for this instance and all of the other
        # children of the parent
        peers  = parent.getChildren()

        for peer in peers:

            if enable:
                peer.display.enableListener('brightness',   peer.name)
                peer.display.enableListener('contrast',     peer.name)
                peer        .enableListener('displayRange', peer.name)
            else:
                peer.display.disableListener('brightness',   peer.name)
                peer.display.disableListener('contrast',     peer.name)
                peer        .disableListener('displayRange', peer.name) 
                

    def __briconChanged(self, *a):
        """Called when the ``brightness``/``contrast`` properties of the
        :class:`.Display` instance change.
        
        Updates the :attr:`displayRange` property accordingly.

        See :func:`.colourmaps.briconToDisplayRange`.
        """

        dlo, dhi = fslcm.briconToDisplayRange(
            (self.dataMin, self.dataMax),
            self.display.brightness / 100.0,
            self.display.contrast   / 100.0)

        self.__toggleListeners(False)
        self.displayRange.x = [dlo, dhi]
        self.__toggleListeners(True)

        
    def __displayRangeChanged(self, *a):
        """Called when the `attr:`displayRange` property changes.

        Updates the :attr:`.Display.brightness` and :attr:`.Display.contrast`
        properties accordingly.

        See :func:`.colourmaps.displayRangeToBricon`.
        """

        brightness, contrast = fslcm.displayRangeToBricon(
            (self.dataMin, self.dataMax),
            self.displayRange.x)
        
        self.__toggleListeners(False)

        # update bricon
        self.display.brightness = brightness * 100
        self.display.contrast   = contrast   * 100

        self.__toggleListeners(True)
