#!/usr/bin/env python
#
# globject.py - The GLObject class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLObject` class, which is a superclass
for all FSLeyes OpenGL overlay types. The following classes are
defined in this module:

.. autosummary::
   :nosignatures:

   GLObject
   GLSimpleObject


See also the :class:`.GLImageObject`, which is the base class for all
``GLObject`` sub-types that display :class:`.Nifti` overlays.


This module also provides a few functions, most importantly
:func:`createGLObject`:

.. autosummary::
   :nosignatures:

   getGLObjectType
   createGLObject
"""

import logging

import fsl.utils.notifier as notifier


log = logging.getLogger(__name__)


def getGLObjectType(overlayType):
    """This function returns an appropriate :class:`GLObject` type for the
    given :attr:`.Display.overlayType` value.
    """

    from . import glvolume
    from . import glrgbvolume
    from . import glcomplex
    from . import glmask
    from . import glrgbvector
    from . import gllinevector
    from . import glmesh
    from . import gllabel
    from . import gltensor
    from . import glsh
    from . import glmip

    typeMap = {
        'volume'     : glvolume    .GLVolume,
        'mask'       : glmask      .GLMask,
        'rgbvector'  : glrgbvector .GLRGBVector,
        'linevector' : gllinevector.GLLineVector,
        'mesh'       : glmesh      .GLMesh,
        'label'      : gllabel     .GLLabel,
        'tensor'     : gltensor    .GLTensor,
        'sh'         : glsh        .GLSH,
        'mip'        : glmip       .GLMIP,
        'rgb'        : glrgbvolume .GLRGBVolume,
        'complex'    : glcomplex   .GLComplex
    }

    return typeMap.get(overlayType, None)


def createGLObject(overlay, overlayList, displayCtx, canvas, threedee=False):
    """Create :class:`GLObject` instance for the given overlay, as specified
    by the :attr:`.Display.overlayType` property.

    :arg overlay:     An overlay object (e.g. a :class:`.Image` instance).

    :arg overlayList: The :class:`.OverlayList`

    :arg displayCtx:  The :class:`.DisplayContext` managing the scene.

    :arg canvas:      The canvas which will be displaying this ``GLObject``.

    :arg threedee:    If ``True``, the ``GLObject`` will be configured for
                      3D rendering. Otherwise it will be configured for 2D
                      slice-based rendering.
    """

    display = displayCtx.getDisplay(overlay)
    ctr     = getGLObjectType(display.overlayType)

    if ctr is not None:
        return ctr(overlay, overlayList, displayCtx, canvas, threedee)
    else:
        return None


class GLObject(notifier.Notifier):
    """The :class:`GLObject` class is a base class for all OpenGL objects
    displayed in *FSLeyes*.


    **Instance attributes**


    The following attributes will always be available on ``GLObject``
    instances:

      - ``name``:       A unique name for this ``GLObject`` instance.

      - ``overlay``:    The overlay to be displayed.

      - ``display``:    The :class:`.Display` instance describing the
                        overlay display properties.

      - ``opts``:       The :class:`.DisplayOpts` instance describing the
                        overlay-type specific display properties.

      - ``displayCtx``: The :class:`.DisplayContext` managing the scene
                        that this ``GLObject`` is a part of.

      - ``canvas``:     The canvas which is displaying this ``GLObject``.
                        Could be a :class:`.SliceCanvas`, a
                        :class:`.LightBoxCanvas`, a :class:`.Scene3DCanvas`,
                        or some future not-yet-created canvas.

      - ``threedee``:   A boolean flag indicating whether this ``GLObject``
                        is configured for 2D or 3D rendering.


    **Usage**


    Once you have created a ``GLObject``:

     1. Do not use the ``GLObject`` until its :meth:`ready` method returns
        ``True``.

     2. In order to render the ``GLObject`` to a canvas, call (in order) the
        :meth:`preDraw`, :meth:`draw2D` (or :meth:`draw3D`), and
        :meth:`postDraw`, methods. Multple calls to
        :meth:`draw2D`/:meth:`draw3D` may occur between calls to
        :meth:`preDraw` and :meth:`postDraw`.

     3. Once you are finished with the ``GLObject``, call its :meth:`destroy`
        method.


    Note that a ``GLObject`` which has been created for 2D rendering
    is not expected be able to render in 3D, nor vice-versa.


    **Update listeners**


    A ``GLObject`` instance will notify registered listeners when its state
    changes and it needs to be re-drawn.  Entities which are interested in
    changes to a ``GLObject`` instance may register as *update listeners*, via
    the :meth:`.Notifier.register` method. It is the resposibility of
    sub-classes of ``GLObject`` to call the :meth:`.Notifier.notify` method to
    facilitate this notification process.


    **Sub-class resposibilities***


    Sub-class implementations must do the following:

     - Call :meth:`__init__`. A ``GLObject.__init__`` sub-class method must
       have the following signature, and must pass all arguments through to
       ``GLObject.__init__``::

           def __init__(self, overlay, displayCtx, canvas, threedee)

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
       .GLImageObject
    """


    def __init__(self, overlay, overlayList, displayCtx, canvas, threedee):
        """Create a :class:`GLObject`.  The constructor adds one attribute
        to this instance, ``name``, which is simply a unique name for this
        instance.

        Subclass implementations must call this method, and should also
        perform any necessary OpenGL initialisation, such as creating
        textures.

        :arg overlay:     The overlay

        :arg overlayList: The :class:`.OverlayList`

        :arg displayCtx:  The ``DisplayContext`` managing the scene

        :arg canvas:      The canvas that is displaying this ``GLObject``.

        :arg threedee:    Whether this ``GLObject`` is to be used for 2D or 3D
                          rendering.
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__threedee    = threedee
        self.__overlay     = overlay
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__canvas      = canvas
        self.__display     = None
        self.__opts        = None

        # GLSimpleObject passes in None for
        # both the overlay and the displayCtx.
        if overlay is not None and displayCtx is not None:
            self.__display = displayCtx.getDisplay(overlay)
            self.__opts    = self.__display.opts

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
    def overlay(self):
        """The overlay being drawn by this ``GLObject``."""
        return self.__overlay


    @property
    def canvas(self):
        """The canvas which is drawing this ``GLObject``."""
        return self.__canvas


    @property
    def display(self):
        """The :class:`.Display` instance containing overlay display
        properties.
        """
        return self.__display


    @property
    def opts(self):
        """The :class:`.DisplayOpts` instance containing overlay
        (type-specific) display properties.
        """
        return self.__opts


    @property
    def overlayList(self):
        """The :class:`.OverlayList`."""
        return self.__overlayList


    @property
    def displayCtx(self):
        """The :class:`.DisplayContext` dsecribing thef scene that this
        ``GLObject`` is a part of.
        """
        return self.__displayCtx


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


    def getBoundsLengths(self):
        """Convenience method which returns a tuple containing the
        ``(x, y, z)``  lengths of the bounding box which contains the
        ``GLObject``.
        """
        los, his = self.getDisplayBounds()
        return tuple([hi - lo for lo, hi in zip(los, his)])


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


    def destroy(self):
        """This method must be called when this :class:`GLObject` is no longer
        needed.

        It should perform any necessary cleaning up, such as deleting texture
        objects.

        .. note:: Sub-classes which override this method must call this
                  implementation.
        """
        self.__overlay    = None
        self.__display    = None
        self.__opts       = None
        self.__displayCtx = None


    @property
    def destroyed(self):
        """This method may be called to test whether a call has been made to
        :meth:`destroy`.

        It should return ``True`` if this ``GLObject`` has been destroyed,
        ``False`` otherwise.
        """
        raise NotImplementedError()


    def preDraw(self, xform=None, bbox=None):
        """This method is called at the start of a draw routine.

        It should perform any initialisation which is required before one or
        more calls to the :meth:`draw2D`/:meth:`draw3D` methods are made, such
        as binding and configuring textures.

        See :meth:`draw2D` for details on the ``xform`` and ``bbox``
        arguments.  They are only guaranteed to be passed to the ``preDraw``
        method in scenarios where only a single call to ``draw2D``
        or``draw3D`` is made between calls to ``preDraw`` and ``postDraw``.
        """
        raise NotImplementedError()


    def draw2D(self, zpos, axes, xform=None, bbox=None):
        """This method is called on ``GLObject`` instances which are
        configured for 2D rendering. It should draw a view of this
        ``GLObject`` - a 2D slice at the given Z location, which specifies
        the position along the screen depth axis.

        :arg zpos:  Position along Z axis to draw.

        :arg axes:  Tuple containing the ``(x, y, z)`` axes in the
                    display coordinate system The ``x`` and ``y`` axes
                    correspond to the horizontal and vertical display axes
                    respectively, and the ``z`` to the depth.

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


    def drawAll(self, axes, zposes, xforms):
        """This is a convenience method for 2D lightboxD canvases, where
        multple 2D slices at different depths are drawn alongside each other.

        This method should do the same as multiple calls to the :meth:`draw2D`
        method, one for each of the Z positions and transformation matrices
        contained in the ``zposes`` and ``xforms`` arrays (``axes`` is fixed).

        In some circumstances (hint: the :class:`.LightBoxCanvas`), better
        performance may be achieved in combining multiple renders, rather
        than doing it with separate calls to :meth:`draw`.

        The default implementation does exactly this, so this method need only
        be overridden for subclasses which are able to get better performance
        by combining the draws.
        """
        for (zpos, xform) in zip(zposes, xforms):
            self.draw2D(zpos, axes, xform)


    def postDraw(self, xform=None, bbox=None):
        """This method is called after the :meth:`draw2D`/:meth:`draw3D`
        methods have been called one or more times.

        It should perform any necessary cleaning up, such as unbinding
        textures.

        See the :meth:`draw2D` method for details on the ``xform`` and
        ``bbox`` arguments.
        """
        raise NotImplementedError()


class GLSimpleObject(GLObject):
    """The ``GLSimpleObject`` class is a convenience superclass for simple
    rendering tasks (probably fixed-function) which are not associated with a
    specific overlay, and require no setup or initialisation/management of GL
    memory or state. It is used by the :mod:`.annotations` module.

    All subclasses need to do is implement the :meth:`GLObject.draw2D` and
    :meth:`GLObject.draw3D` methods. The :mod:`.annotations` module uses the
    ``GLSimpleObject`` class.

    Subclasses should not assume that any of the other methods will ever
    be called.

    .. note:: The :attr:`GLObject.overlay`, :attr:`GLObject.display`,
              :attr:`GLObject.opts`, :attr:`GLObject.canvas`,
              :attr:`GLObject.overlayList` and :attr:`GLObject.displayCtx`
              properties of a ``GLSimpleObject`` are all set to ``None``.
    """


    def __init__(self, threedee):
        """Create a ``GLSimpleObject``. """
        GLObject.__init__(self, None, None, None, None, threedee)
        self.__destroyed = False


    def ready(self):
        """Overrides :meth:`GLObject.ready`. Returns ``True``. """
        return True


    def destroy( self):
        """Overrides :meth:`GLObject.destroy`. Does nothing. """
        GLObject.destroy(self)
        self.__destroyed = True


    @property
    def destroyed(self):
        """Overrides :meth:`GLObject.destroy`. Returns ``True`` if
        :meth:`destroy` hs been called, ``False`` otherwise.
        """
        return self.__destroyed


    def preDraw(self, *args, **kwargs):
        """Overrides :meth:`GLObject.preDraw`. Does nothing. """
        pass


    def postDraw(self, *args, **kwargs):
        """Overrides :meth:`GLObject.postDraw`. Does nothing. """
        pass
