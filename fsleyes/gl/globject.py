#!/usr/bin/env python
#
# globject.py - The GLObject class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLObject` class, which is a superclass
for all FSLeyes OpenGL overlay types. The following classes are
also defined in this module:

.. autosummary::
   :nosignatures:

   GLObject
   GLSimpleObject
   GLImageObject

This module also provides a few functions, most importantly
:func:`createGLObject`:

.. autosummary::
   :nosignatures:

   getGLObjectType
   createGLObject
"""

import logging

import numpy as np

import fsl.utils.transform as transform
import fsl.utils.notifier  as notifier
from . import routines     as glroutines


log = logging.getLogger(__name__)


def getGLObjectType(overlayType):
    """This function returns an appropriate :class:`GLObject` type for the
    given :attr:`.Display.overlayType` value.
    """

    from . import glvolume
    from . import glmask
    from . import glrgbvector
    from . import gllinevector
    from . import glmesh
    from . import glgiftimesh
    from . import gllabel
    from . import gltensor
    from . import glsh

    typeMap = {
        'volume'     : glvolume    .GLVolume,
        'mask'       : glmask      .GLMask,
        'rgbvector'  : glrgbvector .GLRGBVector,
        'linevector' : gllinevector.GLLineVector,
        'mesh'       : glmesh      .GLMesh,
        'giftimesh'  : glgiftimesh .GLGiftiMesh,
        'label'      : gllabel     .GLLabel,
        'tensor'     : gltensor    .GLTensor,
        'sh'         : glsh        .GLSH
    }

    return typeMap.get(overlayType, None)


def createGLObject(overlay, display, threedee=False):
    """Create :class:`GLObject` instance for the given overlay, as specified
    by the :attr:`.Display.overlayType` property.

    :arg overlay:  An overlay object (e.g. a :class:`.Image` instance).

    :arg display:  A :class:`.Display` instance describing how the overlay
                    should be displayed.

    :arg threedee: If ``True``, the ``GLObject`` will be configured for
                   3D rendering. Otherwise it will be configured for 2D
                   slice-based rendering.
    """
    ctr = getGLObjectType(display.overlayType)

    if ctr is not None: return ctr(overlay, display, threedee)
    else:               return None


class GLObject(notifier.Notifier):
    """The :class:`GLObject` class is a base class for all OpenGL objects
    displayed in *FSLeyes*.


    **Instance attributes**


    The following attributes will always be available on ``GLObject``
    instances:

      - ``name``:     A unique name for this ``GLObject`` instance.

      - ``threedee``: A boolean flag indicating whether this ``GLObject``
                      is configured for 2D or 3D rendering.

    If the ``GLObject`` is created for 2D slice-based rendering, the following
    attributes will also be present:

      - ``xax``:  Index of the display coordinate system axis that
                  corresponds to the horizontal screen axis.

      - ``yax``:  Index of the display coordinate system axis that
                  corresponds to the vertical screen axis.

      - ``zax``:  Index of the display coordinate system axis that
                  corresponds to the depth screen axis.


    **Usage**


    Once you have created a ``GLObject``:


     1. If the ``GLObject`` was created for 2D rendering, you must call the
        :meth:`setAxes` method after creation, and before doing anything else.

     2. Do not use the ``GLObject`` until its :meth:`ready` method returns
        ``True``.

     3. In order to render the ``GLObject`` to a canvas, call (in order) the
        :meth:`preDraw`, :meth:`draw2D` (or :meth:`draw3D`), and
        :meth:`postDraw`, methods. Multple calls to
        :meth:`draw2D`/:meth:`draw3D` may occur between calls to
        :meth:`preDraw` and :meth:`postDraw`.

     4. Once you are finished with the ``GLObject``, call its :meth:`destroy`
        method.

    **Update listeners**


    Entities which are interested in changes to a ``GLObject`` representation
    may register as *update listeners*, via the :meth:`.Notifier.register`
    method. Whenever the state of a ``GLObject`` changes, all update listeners
    will be called. It is the resposibility of sub-class implementations to
    call the :meth:`.Notifier.notify` method to facilitate this notification
    process.


    **Sub-class resposibilities***


    Sub-class implementations must do the following:

     - Call :meth:`__init__`. A ``GLObject.__init__`` sub-class method must
       have the following signature::

           def __init__(self, overlay, display, threedee)


     - Call :meth:`notify` whenever its OpenGL representation changes.

     - Override the following methods:

       .. autosummary::
          :nosignatures:

          getDisplayBounds
          getDataResolution
          ready
          destroy
          destroyed
          preDraw
          draw2D
          draw3D
          postDraw

    Alternately, a sub-class could derive from one of the following classes,
    instead of deriving directly from the ``GLObject`` class:

    .. autosummary::
       :nosignatures:

       GLSimpleObject
       GLImageObject
    """


    def __init__(self, threedee):
        """Create a :class:`GLObject`.  The constructor adds one attribute
        to this instance, ``name``, which is simply a unique name for this
        instance.

        If ``threedee is True``, ``xax``, ``yax``, and ``zax`` attributes are
        also added. You must call the :meth:`setAxes` method after creation
        to configure these attributes

        Subclass implementations must call this method, and should also
        perform any necessary OpenGL initialisation, such as creating
        textures.

        :arg threedee: Whether this ``GLObject`` is to be used for 2D or 3D
                       rendering.
        """

        self.__name     = '{}_{}'.format(type(self).__name__, id(self))
        self.__threedee = threedee

        if not threedee:
            self.__xax  = 0
            self.__yax  = 1
            self.__zax  = 2

        log.debug('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.debug('{}.del ({})'.format(type(self).__name__, id(self)))


    @property
    def name(self):
        """A unique name for this ``GLObject``. """
        return self.__name


    @property
    def xax(self):
        """Property which specifies the Y (horizontal) axis, if this
        ``GLObject`` is configured for 2D rendering.
        """
        return self.__xax

    @property
    def yax(self):
        """Property which specifies the Y (vertical) axis, if this ``GLObject``
        is configured for 2D rendering.
        """
        return self.__yax


    @property
    def zax(self):
        """Property which specifies the Z (depth) axis, if this ``GLObject``
        is configured for 2D rendering.
        """
        return self.__zax


    @property
    def threedee(self):
        """Property which is ``True`` if this ``GLObject`` was configured
        for 3D rendering, or ``False`` if it was configured for 2D slice
        rendering.
        """
        return self.__threedee


    def ready(self):
        """This method must return ``True`` or ``False`` to indicate
        whether this ``GLObject`` is ready to be drawn. The method should,
        for example, make sure that all :class:`.ImageTexture` objects
        are ready to be used.
        """
        raise NotImplementedError('The ready method must be '
                                  'implemented by GLObject subclasses')


    def getDisplayBounds(self):
        """This method must calculate and return a bounding box, in the
        display coordinate system, which contains the entire ``GLObject``.
        The bounds must be returned as a tuple with the following structure::

            ((xlo, ylo, zlo), (xhi, yhi, zhi))

        This method must be implemented by sub-classes.
        """

        raise NotImplementedError('The getDisplayBounds method must be '
                                  'implemented by GLObject subclasses')


    def getDataResolution(self, xax, yax):
        """This method must calculate and return a sequence of three values,
        which defines a suitable pixel resolution, along the display coordinate
        system ``(x, y, z)`` axes, for rendering a 2D slice of this
        ``GLObject`` to screen.


        This method should be implemented by sub-classes. If not implemented,
        a default resolution is used. The returned resolution *might* be used
        to render this ``GLObject``, but typically only in a low performance
        environment where off-screen rendering to a
        :class:`.GLObjectRenderTexture` is used - see the
        :class:`.SliceCanvas` documentation for more details.


        :arg xax: Axis to be used as the horizontal screen axis.
        :arg yax: Axis to be used as the vertical screen axis.
        """
        return None


    def setAxes(self, xax, yax):
        """This method must be called after creation of ``GLObject`` instances
        which have been configured for 2D rendering. It may also be called at
        later times when the display orientation for this :class:`GLObject`
        changes. It updates :attr:`xax`, :attr:`yax`, and :attr:`zax`
        properties on this ``GLObject`` instance.


        Sub-classes may override this method, but must still call this
        implementation.


        An :exc:`AttributeError` will be raised if this method is called on
        a ``GLObject`` that has been configured for 3D rendering.
        """
        if self.__threedee:
            raise AttributeError('setAxes called on a 3D '
                                 '{}'.format(type(self).__name__))
        self.__xax = xax
        self.__yax = yax
        self.__zax = 3 - xax - yax


    def destroy(self):
        """This method must be called when this :class:`GLObject` is no longer
        needed.

        It should perform any necessary cleaning up, such as deleting texture
        objects.
        """
        raise NotImplementedError()


    def destroyed(self):
        """This method may be called to test whether a call has been made to
        :meth:`destroy`.

        It should return ``True`` if this ``GLObject`` has been destroyed,
        ``False`` otherwise.
        """
        raise NotImplementedError()


    def preDraw(self):
        """This method is called at the start of a draw routine.

        It should perform any initialisation which is required before one or
        more calls to the :meth:`draw2D`/:meth:`draw3D` methods are made, such
        as binding and configuring textures.
        """
        raise NotImplementedError()


    def draw2D(self, zpos, xform=None, bbox=None):
        """This method is called on ``GLObject`` instances which are
        configured for 2D rendering. It should draw a view of this
        ``GLObject`` - a 2D slice at the given Z location, which specifies
        the position along the screen depth axis.

        :arg xform: If provided, it must be applied to the model view
                    transformation before drawing.

        :arg bbox:  If provided, defines the bounding box, in the display
                    coordinate system, which is to be displayed. Can be used
                    as a performance hint (i.e. to limit the number of things
                    that are rendered).
        """
        raise NotImplementedError()


    def draw3D(self, xform=None, bbox=None):
        """This method is called on ``GLObject`` instances which are
        configured for 3D rendering. It should draw a 3D view of this
        ``GLObject``.

        :arg xform: If provided, it must be applied to the model view
                    transformation before drawing.

        :arg bbox:  If provided, defines the bounding box, in the display
                    coordinate system, which is to be displayed. Can be used
                    as a performance hint (i.e. to limit the number of things
                    that are rendered).
        """
        raise NotImplementedError()


    def drawAll(self, zposes, xforms):
        """This is a convenience method for 2D lightboxD canvases, where
        multple 2D slices at different depths are drawn alongside each other.

        This method should do the same as multiple calls to the :meth:`draw2D`
        method, one for each of the Z positions and transformation matrices
        contained in the ``zposes`` and ``xforms`` arrays.

        In some circumstances (hint: the :class:`.LightBoxCanvas`), better
        performance may be achieved in combining multiple renders, rather
        than doing it with separate calls to :meth:`draw`.

        The default implementation does exactly this, so this method need only
        be overridden for subclasses which are able to get better performance
        by combining the draws.
        """
        for (zpos, xform) in zip(zposes, xforms):
            self.draw2D(zpos, xform)


    def postDraw(self):
        """This method is called after the :meth:`draw2D`/:meth:`draw3D`
        methods have been called one or more times.

        It should perform any necessary cleaning up, such as unbinding
        textures.
        """
        raise NotImplementedError()


class GLSimpleObject(GLObject):
    """The ``GLSimpleObject`` class is a convenience superclass for simple
    rendering tasks (probably fixed-function) which require no setup or
    initialisation/management of GL memory or state. All subclasses need to do
    is implement the :meth:`GLObject.draw2D` and :meth:`GLObject.draw3D`
    methods. The :mod:`.annotations` module uses the ``GLSimpleObject`` class.

    Subclasses should not assume that any of the other methods will ever
    be called.
    """

    def __init__(self, threedee):
        """Create a ``GLSimpleObject``. """
        GLObject.__init__(self, threedee)
        self.__destroyed = False


    def ready(self):
        """Overrides :meth:`GLObject.ready`. Returns ``True``. """
        return True


    def destroy( self):
        """Overrides :meth:`GLObject.destroy`. Does nothing. """
        self.__destroyed = True


    def destroyed(self):
        """Overrides :meth:`GLObject.destroy`. Returns ``True`` if
        :meth:`destroy` hs been called, ``False`` otherwise.
        """
        return self.__destroyed


    def preDraw(self):
        """Overrides :meth:`GLObject.preDraw`. Does nothing. """
        pass


    def postDraw(self):
        """Overrides :meth:`GLObject.postDraw`. Does nothing. """
        pass


class GLImageObject(GLObject):
    """The ``GLImageObject`` class is the base class for all GL representations
    of :class:`.Nifti` instances. It contains some convenience methods for
    drawing volumetric image data.
    """

    def __init__(self, image, display, threedee):
        """Create a ``GLImageObject``.

        This constructor adds the following attributes to this instance:

        =========== =======================================================
        ``image``   A reference to the :class:`.Nifti` overlay being
                    displayed.
        ``display`` A reference to the :class:`.Display` instance
                    associated with the ``image``.
        ``opts``    A reference to the :class:`.DisplayOpts` instance,
                    containing overlay type-specific display options. This
                    is assumed to be a sub-class of :class:`.NiftiOpts`.
        =========== =======================================================

        :arg image:    The :class:`.Nifti` instance

        :arg display:  An associated :class:`.Display` instance.

        :arg threedee: 2D or 3D rendering
        """

        GLObject.__init__(self, threedee)
        self.__image   = image
        self.__display = display
        self.__opts    = display.getDisplayOpts()


    @property
    def image(self):
        """The :class:`.Nifti` being rendered by this ``GLImageObject``. """
        return self.__image


    @property
    def display(self):
        """The :class:`.Display` instance associated with the image. """
        return self.__display

    @property
    def opts(self):
        """The :class:`.DisplayOpts` instance associated with the image. """
        return self.__opts


    def destroy(self):
        """If this method is overridden, it should be called by the subclass
        implementation. It clears references to the :class:`.Image`,
        :class:`.Display`, and :class:`.DisplayOpts` instances.
        """
        self.__image   = None
        self.__display = None
        self.__opts    = None


    def destroyed(self):
        """Returns ``True`` if :meth:`destroy` has been called, ``False``
        otherwise.
        """
        return self.image is None


    def getDisplayBounds(self):
        """Returns the bounds of the :class:`.Image` (see the
        :meth:`.DisplayOpts.bounds` property).
        """
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi())


    def getDataResolution(self, xax, yax):
        """Returns a suitable screen resolution for rendering this
        ``GLImageObject`` in 2D.
        """

        import nibabel as nib

        image = self.image
        opts  = self.opts

        # Figure out a good display resolution
        # along each voxel dimension
        shape = np.array(image.shape[:3])

        # Figure out an approximate
        # correspondence between the
        # voxel axes and the display
        # coordinate system axes.
        xform = opts.getTransform('id', 'display')
        axes  = nib.orientations.aff2axcodes(
            xform, ((0, 0), (1, 1), (2, 2)))

        # Re-order the voxel resolutions
        # in the display space
        res = [shape[axes[0]], shape[axes[1]], shape[axes[2]]]

        return res


    def generateVertices2D(self, zpos, xform=None, bbox=None):
        """Generates vertex coordinates for a 2D slice of the :class:`.Image`,
        through the given ``zpos``, with the optional ``xform`` and ``bbox``
        applied to the coordinates.

        This is a convenience method for generating vertices which can be used
        to render a slice through a 3D texture. It is used by the
        :mod:`.gl14.glvolume_funcs` and :mod:`.gl21.glvolume_funcs` (and other)
        modules.


        A tuple of three values is returned, containing:

          - A ``6*3 numpy.float32`` array containing the vertex coordinates

          - A ``6*3 numpy.float32`` array containing the voxel coordinates
            corresponding to each vertex

          - A ``6*3 numpy.float32`` array containing the texture coordinates
            corresponding to each vertex


        This method will raise an :exc:`AttributeError` if called on a
        ``GLImageObject`` configured for 3D rendering.
        """

        opts   = self.opts
        v2dMat = opts.getTransform('voxel',   'display')
        d2vMat = opts.getTransform('display', 'voxel')
        v2tMat = opts.getTransform('voxel',   'texture')

        vertices, voxCoords = glroutines.slice2D(
            self.image.shape[:3],
            self.xax,
            self.yax,
            zpos,
            v2dMat,
            d2vMat,
            bbox=bbox)

        if xform is not None:
            vertices = transform.transform(vertices, xform)

        # If not interpolating, centre the
        # voxel coordinates on the Z/depth
        # axis. We do this to avoid rounding
        # bias when the display Z position is
        # on a voxel boundary.
        if not hasattr(opts, 'interpolation') or opts.interpolation == 'none':
            voxCoords = opts.roundVoxels(voxCoords, daxes=[self.zax])

        texCoords = transform.transform(voxCoords, v2tMat)

        return vertices, voxCoords, texCoords


    def generateVertices3D(self, xform=None, bbox=None):
        """Generates vertex coordinates defining the 3D bounding box of the
        :class:`.Image`, with the optional ``xform`` and ``bbox`` applied to
        the coordinates. See the :func:`.routines.boundingBox` function.

        A tuple of three values is returned, containing:

          - A ``36*3 numpy.float32`` array containing the vertex coordinates

          - A ``36*3 numpy.float32`` array containing the voxel coordinates
            corresponding to each vertex

          - A ``36*3 numpy.float32`` array containing the texture coordinates
            corresponding to each vertex
        """
        opts   = self.opts
        v2dMat = opts.getTransform('voxel',   'display')
        d2vMat = opts.getTransform('display', 'voxel')
        v2tMat = opts.getTransform('voxel',   'texture')

        vertices, voxCoords = glroutines.boundingBox(
            self.image.shape[:3],
            v2dMat,
            d2vMat,
            bbox=bbox)

        if xform is not None:
            vertices = transform.transform(vertices, xform)

        texCoords = transform.transform(voxCoords, v2tMat)

        return vertices, voxCoords, texCoords


    def generateVoxelCoordinates2D(self, zpos, bbox=None, space='voxel'):
        """Generates a 2D grid of voxel coordinates along the
        XY display coordinate system plane, at the given ``zpos``.

        :arg zpos:  Position along the display coordinate system Z axis.

        :arg bbox:  Limiting bounding box.

        :arg space: Either ``'voxel'`` (the default) or ``'display'``.
                    If the latter, the returned coordinates are in terms
                    of the display coordinate system. Otherwise, the
                    returned coordinates are integer voxel coordinates.

        :returns: A ``numpy.float32`` array of shape ``(N, 3)``, containing
                  the coordinates for ``N`` voxels.

        This method will raise an :exc:`AttributeError` if called on a
        ``GLImageObject`` configured for 3D rendering.

        See the :func:`.pointGrid` function.
        """

        if space not in ('voxel', 'display'):
            raise ValueError('Unknown value for space ("{}")'.format(space))

        image      = self.image
        opts       = self.opts
        v2dMat     = opts.getTransform('voxel',   'display')
        d2vMat     = opts.getTransform('display', 'voxel')

        if opts.transform == 'id':
            resolution = [1, 1, 1]
        elif opts.transform in ('pixdim', 'pixdim-flip'):
            resolution = image.pixdim[:3]
        else:
            resolution = [min(image.pixdim[:3])] * 3

        voxels = glroutines.pointGrid(
            image.shape,
            resolution,
            v2dMat,
            self.xax,
            self.yax,
            bbox=bbox)[0]

        voxels[:, self.zax] = zpos

        if space == 'voxel':
            voxels = transform.transform(voxels, d2vMat)
            voxels = opts.roundVoxels(voxels,
                                      daxes=[self.zax],
                                      roundOther=False)

        return voxels


    def generateVoxelCoordinates3D(self, bbox, space='voxel'):
        """


        See the :func:`.pointGrid3D` function.

        note: Not implemented properly yet.
        """

        if space not in ('voxel', 'display'):
            raise ValueError('Unknown value for space ("{}")'.format(space))


        image      = self.image
        opts       = self.opts
        v2dMat     = opts.getTransform('voxel',   'display')
        d2vMat     = opts.getTransform('display', 'voxel')

        voxels = glroutines.pointGrid3D(image.shape[:3])

        if space == 'voxel':
            pass
            # voxels = transform.transform(voxels, d2vMat)
            # voxels = opts.roundVoxels(voxels)

        return voxels
