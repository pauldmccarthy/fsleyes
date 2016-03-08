#!/usr/bin/env python
#
# globject.py - The GLObject class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLObject` class, which is a superclass for
all 2D representations of objects in OpenGL.

This module also provides the :func:`getGLObjectType` and
:func:`createGLObject` functions, which provide mappings between overlay
types and their corresponding OpenGL representations.
"""

import logging

import numpy as np

import routines            as glroutines
import fsl.utils.transform as transform
import fsl.utils.notifier  as notifier


log = logging.getLogger(__name__)


def getGLObjectType(overlayType):
    """This function returns an appropriate :class:`GLObject` type for the
    given :attr:`.Display.overlayType` value.
    """

    import glvolume
    import glmask
    import glrgbvector
    import gllinevector
    import glmodel
    import gllabel
    import gltensor

    typeMap = {
        'volume'     : glvolume    .GLVolume,
        'mask'       : glmask      .GLMask,
        'rgbvector'  : glrgbvector .GLRGBVector,
        'linevector' : gllinevector.GLLineVector,
        'model'      : glmodel     .GLModel,
        'label'      : gllabel     .GLLabel,
        'tensor'     : gltensor    .GLTensor
    }

    return typeMap.get(overlayType, None)


def createGLObject(overlay, display, xax, yax):
    """Create :class:`GLObject` instance for the given overlay, as specified
    by the :attr:`.Display.overlayType` property.

    :arg overlay: An overlay object (e.g. a :class:`.Image` instance).
    
    :arg display: A :class:`.Display` instance describing how the overlay
                  should be displayed.

    :arg xax:     Initial display X axis

    :arg yax:     Initial display Y axis    
    """
    ctr = getGLObjectType(display.overlayType)

    if ctr is not None: return ctr(overlay, display, xax, yax)
    else:               return None


class GLObject(notifier.Notifier):
    """The :class:`GLObject` class is a base class for all 2D OpenGL
    objects displayed in *FSLeyes*.

    
    **Instance attributes**

    
    The following attributes will always be available on ``GLObject``
    instances:

      - ``name``: A unique name for this ``GLObject`` instance.

      - ``xax``:  Index of the display coordinate system axis that
                  corresponds to the horizontal screen axis.
    
      - ``yax``:  Index of the display coordinate system axis that 
                  corresponds to the vertical screen axis.
    
      - ``zax``:  Index of the display coordinate system axis that 
                  corresponds to the depth screen axis.


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
    
           def __init__(self, overlay, display, xax, yax)
    

     - Call :meth:`notify` whenever its OpenGL representation changes.

     - Override the following methods:
    
       .. autosummary::
          :nosignatures:

          getDisplayBounds
          getDataResolution
          ready
          destroy
          preDraw
          draw
          postDraw

    Alternately, a sub-class could derive from one of the following classes,
    instead of deriving directly from the ``GLObject`` class:

    .. autosummary::
       :nosignatures:

       GLSimpleObject
       GLImageObject
    """

    
    def __init__(self, xax, yax):
        """Create a :class:`GLObject`.  The constructor adds one attribute 
        to this instance, ``name``, which is simply a unique name for this
        instance, and gives values to the ``xax``, ``yax``, and ``zax``
        attributes.

        Subclass implementations must call this method, and should also
        perform any necessary OpenGL initialisation, such as creating
        textures.

        :arg xax: Initial display X axis
        :arg yax: Initial display Y axis
        """

        # Give this instance a name, and set 
        # initial values for the display axes
        self.name = '{}_{}'.format(type(self).__name__, id(self))
        self.xax  = xax
        self.yax  = yax
        self.zax  = 3 - xax - yax

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.memory('{}.del ({})'.format(type(self).__name__, id(self)))


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
        system ``(x, y, z)`` axes, for rendering this ``GLObject`` to screen.

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
        """This method is called when the display orientation for this
        :class:`GLObject` changes. It sets :attr:`xax`, :attr:`yax`,
        and :attr:`zax` attributes on this ``GLObject`` instance.

        Sub-classes may override this method, but should still call this
        implementation, or should set the ``xax``, ``yax``, and ``zax``
        attributes themselves.
        """
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

    
    def destroy(self):
        """This method is called when this :class:`GLObject` is no longer
        needed.
        
        It should perform any necessary cleaning up, such as deleting texture
        objects.
        """
        raise NotImplementedError()

    
    def preDraw(self):
        """This method is called at the start of a draw routine.

        It should perform any initialisation which is required before one or
        more calls to the :meth:`draw` method are made, such as binding and
        configuring textures.
        """
        raise NotImplementedError()

    
    def draw(self, zpos, xform=None):
        """This method should draw a view of this ``GLObject`` - a 2D slice
        at the given Z location, which specifies the position along the screen
        depth axis.

        If the ``xform`` parameter is provided, it should be applied to the
        model view transformation before drawing.
        """
        raise NotImplementedError()


    def drawAll(self, zposes, xforms):
        """This method should do the same as multiple calls to the
        :meth:`draw` method, one for each of the Z positions and
        transformation matrices contained in the ``zposes`` and
        ``xforms`` arrays.

        In some circumstances (hint: the :class:`.LightBoxCanvas`), better
        performance may be achieved in combining multiple renders, rather
        than doing it with separate calls to :meth:`draw`.

        The default implementation does exactly this, so this method need only
        be overridden for subclasses which are able to get better performance
        by combining the draws.
        """
        for (zpos, xform) in zip(zposes, xforms):
            self.draw(zpos, xform)


    def postDraw(self):
        """This method is called after the :meth:`draw` method has been called
        one or more times.

        It should perform any necessary cleaning up, such as unbinding
        textures.
        """
        raise NotImplementedError()


class GLSimpleObject(GLObject):
    """The ``GLSimpleObject`` class is a convenience superclass for simple
    rendering tasks (probably fixed-function) which require no setup or
    initialisation/management of GL memory or state. All subclasses need to
    do is implement the :meth:`GLObject.draw` method. The :mod:`.annotations`
    module uses the ``GLSimpleObject`` class.

    Subclasses should not assume that any of the other methods will ever
    be called.
    """

    def __init__(self, xax, yax):
        """Create a ``GLSimpleObject``. """
        GLObject.__init__(self, xax, yax)


    def ready(self):
        """Overrides :meth:`GLObject.ready`. Returns ``True``. """
        return True

        
    def destroy( self):
        """Overrides :meth:`GLObject.destroy`. Does nothing. """
        pass

    
    def preDraw(self):
        """Overrides :meth:`GLObject.preDraw`. Does nothing. """
        pass

    
    def postDraw(self):
        """Overrides :meth:`GLObject.postDraw`. Does nothing. """
        pass


class GLImageObject(GLObject):
    """The ``GLImageObject`` class is the base class for all GL representations
    of :class:`.Nifti1` instances. 
    """
    
    def __init__(self, image, display, xax, yax):
        """Create a ``GLImageObject``.

        This constructor adds the following attributes to this instance:

        =============== =======================================================
        ``image``       A reference to the :class:`.Nifti1` overlay being
                        displayed.
        ``display``     A reference to the :class:`.Display` instance
                        associated with the ``image``.
        ``displayOpts`` A reference to the :class:`.DisplayOpts` instance,
                        containing overlay type-specific display options. This
                        is assumed to be a sub-class of :class:`.Nifti1Opts`.
        =============== =======================================================

        :arg image:   The :class:`.Nifti1` instance
        
        :arg display: An associated :class:`.Display` instance.

        :arg xax:     Initial display X axis

        :arg yax:     Initial display Y axis
        """
        
        GLObject.__init__(self, xax, yax)
        self.image       = image
        self.display     = display
        self.displayOpts = display.getDisplayOpts()


    def destroy(self):
        """If this method is overridden, it should be called by the subclass
        implementation. It clears references to the :class:`.Image`,
        :class:`.Display`, and :class:`.DisplayOpts` instances.
        """
        self.image       = None
        self.display     = None
        self.displayOpts = None


    def getDisplayBounds(self):
        """Returns the bounds of the :class:`.Image` (see the
        :meth:`.DisplayOpts.bounds` property).
        """
        return (self.displayOpts.bounds.getLo(),
                self.displayOpts.bounds.getHi())


    def getDataResolution(self, xax, yax):
        """Returns a suitable screen resolution for rendering this
        ``GLImageObject``.
        """

        import nibabel as nib

        image = self.image
        opts  = self.displayOpts
        res   = opts.resolution

        # Figure out a good display resolution
        # along each voxel dimension
        pixdim = np.array(image.pixdim[:3])
        steps  = [res, res, res] / pixdim
        steps  = np.maximum(steps, [1, 1, 1])
        res    = image.shape[:3] / steps

        # Make sure the pixel
        # resolutions are integers
        res = np.array(res.round(), dtype=np.uint32)

        # Figure out an approximate 
        # correspondence between the
        # voxel axes and the display
        # coordinate system axes. 
        xform = opts.getTransform('id', 'display')
        axes  = nib.orientations.aff2axcodes(
            xform, ((0, 0), (1, 1), (2, 2)))

        # Re-order the voxel resolutions
        # in the display space
        res = [res[axes[0]], res[axes[1]], res[axes[2]]]

        return res

        
    def generateVertices(self, zpos, xform):
        """Generates vertex coordinates for a 2D slice of the :class:`.Image`,
        through the given ``zpos``, with the optional ``xform`` applied to the
        coordinates.
        
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
        """

        vertices, voxCoords, texCoords = glroutines.slice2D(
            self.image.shape[:3],
            self.xax,
            self.yax,
            zpos, 
            self.displayOpts.getTransform('voxel',   'display'),
            self.displayOpts.getTransform('display', 'voxel'))

        if xform is not None: 
            vertices = transform.transform(vertices, xform)

        return vertices, voxCoords, texCoords 
