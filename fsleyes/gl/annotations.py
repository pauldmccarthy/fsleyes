#!/usr/bin/env python
#
# annotations.py - 2D annotations on a SliceCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Annotations` class, which implements
functionality to draw annotations (lines, text, etc)


The :class:`Annotations` class is used by the :class:`.SliceCanvas`,
:class:`.LightBoxCanvas`, and :class:`.Scene3DCanvas` classes, and users of
those classes, to annotate the canvas.

Not all annotation types currently support being drawn on a
:class:`.Scene3DCanvas`.


All annotations derive from the :class:`AnnotationObject` base class. The
following annotation types are defined:

.. autosummary::
   :nosignatures:

   Point
   Line
   Arrow
   Rect
   Ellipse
   VoxelSelection
   TextAnnotation
"""


import time
import logging

import numpy       as np
import OpenGL.GL   as gl

import fsl.transform.affine     as affine
import fsleyes_props            as props
import fsleyes.gl               as fslgl
import fsleyes.gl.globject      as globject
import fsleyes.gl.shaders       as shaders
import fsleyes.gl.routines      as glroutines
import fsleyes.gl.resources     as glresources
import fsleyes.gl.textures      as textures
import fsleyes.gl.text          as gltext
import fsleyes.gl.textures.data as texdata


log = logging.getLogger(__name__)


class Annotations(props.HasProperties):
    """An :class:`Annotations` object provides functionality to draw
    annotations on an OpenGL canvas. Annotations may be enqueued via
    any of the :meth:`line`, :meth:`rect`, :meth:`ellpse`, :meth:`point`,
    :meth:`selection` or :meth:`obj`, methods, and de-queued via the
    :meth:`dequeue` method.


    Annotations can be enqueued in one of three ways, using the `hold` and
    `fixed` parameters:


      - **Transient**: When calling ``line``, ``rect``, etc, passing
        ``hold=False` enqueues the annotation for the next call to
        :meth:`draw`. After the annotation is drawn, it is removed from the
        queue, and would need to be re-queued to draw it again. The ``fixed``
        parameter has no effect for transient annotations.

      - **Fixed**: When calling ``line``, ``rect``, etc, passing
        ``hold=True`` and ```fixed=True`` enqueues the annotation for all
        subsequent calls to :meth:`draw`. Fixed annotations are stored in
        an internal, inaccessible queue, so if you need to manipulate a
        fixed annotation, you need to maintain your own reference to it.

      - `**Persistent`**: When calling ``line``, ``rect``, etc, passing
        ``hold=True`` and ``fixed=False`` adds the annotation to the
        accessible :attr:`annotations` list.


    Transient annotations are intended for one-off annotations, e.g. a
    cursor mark at the current mouse location.


    Fixed annotations are intended for persistent annotations which are
    intended to be immutable, i.e. that cannot be directly manipulated by the
    user, e.g. anatomical orientation labels on the canvases of an
    :class:`.OrthoPanel`.


    Persistent annotations are intended for persistent annotations which are
    intended to be manipulated by the user - these annotations are used by the
    :class:`.AnnotationPanel` in conjunction with the
    :class:`.OrthoAnnotateProfile`.


    After annotations have been enqueued in one of the above manners, a call
    to :meth:`draw2D` or :meth:`draw3D` will draw each annotation on the
    canvas, and clear the transient queue. The default value for ``hold`` is
    ``False``, and ``fixed`` is ``True``,


    Annotations can be queued by one of the helper methods on the
    :class:`Annotations` object (e.g. :meth:`line` or :meth:`rect`), or by
    manually creating an :class:`AnnotationObject` and passing it to the
    :meth:`obj` method.
    """


    annotations = props.List()
    """Contains all persistent :class:`AnnotationObject` instances, which have
    been added to the queue with ``hold=True`` and ``fixed=False``.
    """


    def __init__(self, canvas):
        """Creates an :class:`Annotations` object.

        :arg canvas: The :class:`.SliceCanvas` that owns this
                     ``Annotations`` object.
        """

        self.__transient = []
        self.__fixed     = []
        self.__canvas    = canvas
        self.__shader    = None


    @property
    def canvas(self):
        """Returns a ref to the canvas that owns this ``Annotations`` instance.
        """
        return self.__canvas


    def destroy(self):
        """Must be called when this :class:`.Annotations` object is no longer
        needed.
        """
        self.clear()
        if self.__shader is not None:
            self.__shader.destroy()
            self.__shader = None


    @property
    def defaultShader(self):
        """Returns a shader program used by most :class:`AnnotationObject`
        types.
        """

        if self.__shader is not None:
            return self.__shader

        vertSrc = shaders.getVertexShader(  'annotations')
        fragSrc = shaders.getFragmentShader('annotations')
        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            shader = shaders.ARBPShader(vertSrc, fragSrc)
        else:
            shader = shaders.GLSLShader(vertSrc, fragSrc)

        self.__shader = shader
        return shader


    def line(self, *args, **kwargs):
        """Queues a line for drawing - see the :class:`Line` class. """
        hold  = kwargs.pop('hold',  False)
        fixed = kwargs.pop('fixed', True)
        obj   = Line(self, *args, **kwargs)
        return self.obj(obj, hold, fixed)


    def arrow(self, *args, **kwargs):
        """Queues an arrow for drawing - see the :class:`Arrow` class. """
        hold  = kwargs.pop('hold',  False)
        fixed = kwargs.pop('fixed', True)
        obj   = Arrow(self, *args, **kwargs)
        return self.obj(obj, hold, fixed)


    def point(self, *args, **kwargs):
        """Queues a point for drawing - see the :class:`Point` class. """
        hold  = kwargs.pop('hold',  False)
        fixed = kwargs.pop('fixed', True)
        obj   = Point(self, *args, **kwargs)
        return self.obj(obj, hold, fixed)


    def rect(self, *args, **kwargs):
        """Queues a rectangle for drawing - see the :class:`Rectangle` class.
        """
        hold  = kwargs.pop('hold',  False)
        fixed = kwargs.pop('fixed', True)
        obj   = Rect(self, *args, **kwargs)
        return self.obj(obj, hold, fixed)


    def ellipse(self, *args, **kwargs):
        """Queues a circle for drawing - see the :class:`Ellipse` class.
        """
        hold  = kwargs.pop('hold',  False)
        fixed = kwargs.pop('fixed', True)
        obj   = Ellipse(self, *args, **kwargs)
        return self.obj(obj, hold, fixed)


    def selection(self, *args, **kwargs):
        """Queues a selection for drawing - see the :class:`VoxelSelection`
        class.
        """
        hold  = kwargs.pop('hold',  False)
        fixed = kwargs.pop('fixed', True)
        obj   = VoxelSelection(self, *args, **kwargs)
        return self.obj(obj, hold, fixed)


    def text(self, *args, **kwargs):
        """Queues a text annotation for drawing - see the
        :class:`TextAnnotation` class.
        """
        hold  = kwargs.pop('hold',  False)
        fixed = kwargs.pop('fixed', True)
        obj   = TextAnnotation(self, *args, **kwargs)
        return self.obj(obj, hold, fixed)


    def obj(self, obj, hold=False, fixed=True):
        """Queues the given :class:`AnnotationObject` for drawing.

        :arg hold:  If ``True``, the given ``AnnotationObject`` will be added
                    to the fixed or persistent queues, and will remain there
                    until it is explicitly removed. Otherwise (the default),
                    the object will be added to the transient queue, and
                    removed from the queue after it has been drawn.

        :arg fixed: If ``True`` (the default), and ``hold=True``, the given
                    ``AnnotationObject`` will be added to the fixed queue, and
                    will remain there until it is explicitly
                    removed. Otherwise, the object will be added to the
                    persistent queue and, again, will remain there until it is
                    explicitly removed. Has no effect when ``hold=False``.
        """
        if   hold and fixed: self.__fixed    .append(obj)
        elif hold:           self.annotations.append(obj)
        else:                self.__transient.append(obj)
        return obj


    def dequeue(self, obj, hold=False, fixed=True):
        """Removes the given :class:`AnnotationObject` from the appropriate
        queue, but does not call its :meth:`.GLObject.destroy` method - this
        is the responsibility of the caller.
        """

        if hold and fixed:
            try:               self.__fixed.remove(obj)
            except ValueError: pass
        elif hold:
            try:               self.annotations.remove(obj)
            except ValueError: pass
        else:
            try:               self.__transient.remove(obj)
            except ValueError: pass


    def clear(self):
        """Clears all queues, and calls the :meth:`.GLObject.destroy` method
        on every object in the queue.
        """

        for obj in self.__fixed:     obj.destroy()
        for obj in self.__transient: obj.destroy()
        for obj in self.annotations: obj.destroy()

        self.__fixed        = []
        self.__transient    = []
        self.annotations[:] = []


    def draw2D(self, zpos, axes):
        """Draws all enqueued annotations. Fixed annotations are drawn first,
        then persistent, then transient - i.e. transient annotations will
        be drawn on top of persistent, which will be drawn on to of fixed.

        :arg zpos: Position along the Z axis, above which all annotations
                   should be drawn.

        :arg axes: Display coordinate system axis mapping to the screen
                   coordinate system.
        """

        objs = (list(self.__fixed)     +
                list(self.annotations) +
                list(self.__transient))

        drawTime = time.time()

        for obj in objs:

            if obj.expired(drawTime): continue
            if not obj.enabled:       continue
            if obj.honourZLimits:
                if obj.zmin is not None and zpos < obj.zmin: continue
                if obj.zmax is not None and zpos > obj.zmax: continue

            try:
                obj.draw2D(self.canvas, zpos, axes)
            except Exception as e:
                log.warning(e, exc_info=True)

        # Clear the transient queue after each draw
        self.__transient = []


    def draw3D(self, xform=None):
        """Draws all enqueued annotations. Fixed annotations are drawn first,
        then persistent, then transient - i.e. transient annotations will
        be drawn on top of persistent, which will be drawn on to of fixed.

        :arg xform:
        """

        objs = (list(self.__fixed)     +
                list(self.annotations) +
                list(self.__transient))

        drawTime = time.time()

        for obj in objs:

            if obj.expired(drawTime): continue
            if not obj.enabled:       continue

            if obj.occlusion:
                features = [gl.GL_DEPTH_TEST]
            else:
                features = []

            try:
                with glroutines.enabled(features):
                    obj.draw3D(self.canvas, xform)
            except Exception as e:
                log.warning(e, exc_info=True)

        # Clear the transient queue after each draw
        self.__transient = []


class AnnotationObject(globject.GLSimpleObject, props.HasProperties):
    """Base class for all annotation objects. An ``AnnotationObject`` is drawn
    by an :class:`Annotations` instance. The ``AnnotationObject`` contains some
    attributes which are common to all annotation types:

    ============= ============================================================
    ``colour``    Annotation colour
    ``alpha``     Transparency
    ``enabled``   Whether the annotation should be drawn or not.
    ``lineWidth`` Annotation line width (if the annotation is made up of
                  lines)
    ``expiry``    Time (in seconds) after which the annotation will expire and
                  not be drawn.
    ``zmin``      Minimum z value below which this annotation will not be
                  drawn.
    ``zmax``      Maximum z value above which this annotation will not be
                  drawn.
    ``creation``  Time of creation.
    ============= ============================================================

    All of these attributes can be modified directly, after which you should
    trigger a draw on the owning ``SliceCanvas`` to refresh the annotation.
    You shouldn't touch the ``expiry`` or ``creation`` attributes though.

    Subclasses must, at the very least, override the
    :meth:`globject.GLObject.vertices2D` method.
    """


    enabled = props.Boolean(default=True)
    """Whether to draw this annotation or not. """


    lineWidth = props.Int(default=1, minval=0.1, clamped=True)
    """Line width in pixels (approx), for annotations which are drawn with
    lines. See also the :meth:`normalisedLineWidth` method.
    """


    colour = props.Colour(default='#a00000')
    """Annotation colour."""


    alpha = props.Percentage(default=100)
    """Opacity."""


    honourZLimits = props.Boolean(default=False)
    """If True, the :attr:`zmin`/:attr:`zmax` properties are enforced.
    Otherwise (the default) they are ignored, and the annotation is
    always drawn.

    Only relevant when being drawn via :meth:`draw2D`.
    """


    zmin = props.Real()
    """Minimum z value below which this annotation will not be drawn.
    Only relevant when being drawn via :meth:`draw2D`.
    """


    zmax = props.Real()
    """Maximum z value below which this annotation will not be drawn.
    Only relevant when being drawn via :meth:`draw2D`.
    """


    occlusion = props.Boolean(default=False)
    """Only relevant when drawing via :meth:`draw3D`. If ``True``,
    depth testing is enabled.
    """


    applyMvp =  props.Boolean(default=True)
    """If ``True`` (the default), it is assumed that the annotation coordinates
    are specified in the display coordinate system, and therefore that they
    should be transformed by the :meth:`.SliceCanvas.mvpMatrix` (or
    :meth:`.Scene3DCanvas.mvpMatrix`). If ``False``, it is assumed that the
    annotation coordinates are in normalised device coordinates.
    Not honoured by all annotation types.
    """


    def __init__(self,
                 annot,
                 colour=None,
                 alpha=None,
                 lineWidth=None,
                 enabled=None,
                 expiry=None,
                 honourZLimits=None,
                 zmin=None,
                 zmax=None,
                 occlusion=None,
                 applyMvp=None,
                 **kwargs):
        """Create an ``AnnotationObject``.

        :arg annot:         The :class:`Annotations` object that created this
                            ``AnnotationObject``.

        :arg colour:        RGB/RGBA tuple specifying the annotation colour.

        :arg alpha:         Opacity.

        :arg lineWidth:     Line width to use for the annotation.

        :arg enabled:       Initially enabled or disabled.

        :arg expiry:        Time (in seconds) after which this annotation
                            should be expired and not drawn.

        :arg honourZLimits: Whether to enforce ``zmin``/``zmax``.

        :arg zmin:          Minimum z value below which this annotation should
                            not be drawn.

        :arg zmax:          Maximum z value above which this annotation should
                            not be drawn.

        :arg occlusion:     Whether to draw with depth testing.

        :arg applyMvp:      Whether to apply the canvas MVP matrix.

        Any other arguments are ignored.
        """
        globject.GLSimpleObject.__init__(self, False)

        self.annot    = annot
        self.creation = time.time()
        self.expiry   = expiry

        if colour        is not None: self.colour        = colour
        if alpha         is not None: self.alpha         = alpha
        if lineWidth     is not None: self.lineWidth     = lineWidth
        if enabled       is not None: self.enabled       = enabled
        if honourZLimits is not None: self.honourZLimits = honourZLimits
        if zmin          is not None: self.zmin          = zmin
        if zmax          is not None: self.zmax          = zmax
        if occlusion     is not None: self.occlusion     = occlusion
        if applyMvp      is not None: self.applyMvp      = applyMvp


    def destroy(self):
        """Must be called when  this ``AnnotationObject`` is no longer needed.
        The default implementation does nothing, but may be overridden by
        sub-classes.
        """


    def resetExpiry(self):
        """Resets the expiry for this ``AnnotationObject`` so that it is
        valid from the current time.
        """
        self.creation = time.time()


    def hit(self, x, y):
        """Return ``True`` if the given X/Y point is within the bounds of this
        annotation, ``False`` otherwise.  Must be implemented by sub-classes,
        but only those annotations which are drawn by the
        :class:`.OrthoAnnotateProfile`.

        Only relevant for annotations drawn on a :meth:`.SliceCanvas` of an
        :class:`.OrthoPanel`.

        :arg x: X coordinate (in display coordinates).
        :arg y: Y coordinate (in display coordinates).
        """
        raise NotImplementedError()


    def move(self, x, y):
        """Move this annotation acording to ``(x, y)``, which is specified as
        an offset relative to the current location. Must be implemented by
        sub-classes, but only those annotations which are drawn by the
        :class:`.OrthoAnnotateProfile`.

        Only relevant for annotations drawn on a :meth:`.SliceCanvas` of an
        :class:`.OrthoPanel`.

        :arg x: X coordinate (in display coordinates).
        :arg y: Y coordinate (in display coordinates).
        """
        raise NotImplementedError()


    def expired(self, now):
        """Returns ``True`` if this ``Annotation`` has expired, ``False``
        otherwise.

        :arg now: The current time
        """
        if self.expiry is None:
            return False

        return (self.creation + self.expiry) < now


    @property
    def normalisedLineWidth(self):
        """Returns the :attr:`lineWidth`, converted into units proportional to
        either display coordinates (if :attr:`applyMvp` is ``True``), or
        normalised device coordinates (if :attr:`applyMvp` is ``False``).
        """

        pw, ph = self.annot.canvas.pixelSize()
        cw, ch = self.annot.canvas.GetSize()

        if self.applyMvp:
            return self.lineWidth * min((pw, ph))
        else:
            return self.lineWidth * max((1 / cw, 1 / ch))


    def vertices2D(self, zpos, axes):
        """Must be implemented by sub-classes which rely on the default
        :meth:`draw2D` implementation. Generates and returns verticws to
        display this annotation. The exact return type may differ depending
        on the annotation type.
        """
        raise NotImplementedError()


    def vertices3D(self):
        """Must be implemented by sub-classes which rely on the default
        :meth:`draw3D` implementation. Generates and returns verticws to
        display this annotation. The exact return type may differ depending
        on the annotation type.
        """
        raise NotImplementedError()


    def __draw(self, canvas, vertices, xform=None):
        """Used by the default :meth:`draw2D` and :meth:`draw3D`
        implementations.
        """
        shader = self.annot.defaultShader
        mvpmat = canvas.mvpMatrix
        colour = list(self.colour[:3]) + [self.alpha / 100.0]

        if vertices is None or len(vertices) == 0:
            return

        if not self.applyMvp:
            mvpmat = np.eye(4, dtype=np.float32)

        if xform is not None:
            mvpmat = affine.concat(mvpmat, xform)

        # load all vertex types, and use offsets
        # to draw each vertex group separately
        primitives              = [v[0] for v in vertices]
        vertices                = [v[1] for v in vertices]
        vertices, lens, offsets = glroutines.stackVertices(vertices)

        with shader.loaded():
            shader.set(   'MVP',    mvpmat)
            shader.set(   'colour', colour)
            shader.setAtt('vertex', vertices)
            with shader.loadedAtts():
                for prim, length, off in zip(primitives, lens, offsets):
                    shader.draw(prim, off, length)


    def draw2D(self, canvas, zpos, axes, xform=None):
        """Draw this annotation on a 2D plane. This method implements a
        default routine used by most annotation types - the annotation is
        drawn using vertices returned by the overridden :meth:`vertices2D`
        method.

        This method may be overridden by sub-classes which require a different
        routine.
        """
        vertices = self.vertices2D(zpos, axes)
        self.__draw(canvas, vertices, xform)


    def draw3D(self, canvas, xform=None):
        """Draw this annotation in 3D. This method implements a
        default routine used by most annotation types - the annotation is
        drawn using vertices returned by the overridden :meth:`vertices3D`
        method.

        This method may be overridden by sub-classes which require a different
        routine.
        """
        vertices = self.vertices3D()
        self.__draw(canvas, vertices, xform)


class Point(AnnotationObject):
    """The ``Point`` class is an :class:`AnnotationObject` which represents a
    point, drawn as a small crosshair. The size of the point is proportional
    to the :attr:`AnnotationObject.lineWidth`.
    """


    def __init__(self, annot, x, y, z=None, **kwargs):
        """Create a ``Point`` annotation.

        The ``xy`` coordinate tuple should be in relation to the axes which
        map to the horizontal/vertical screen axes on the target canvas.

        :arg annot: The :class:`Annotations` object that owns this ``Point``.
        :arg x:     X coordinates of the point
        :arg y:     Y coordinates of the point
        :arg z:     Z coordinates, if this ``Point`` is being drawn via
                    :meth:`draw3D`.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """
        AnnotationObject.__init__(self, annot, **kwargs)
        self.x = x
        self.y = y
        self.z = z


    def vertices2D(self, zpos, axes):
        """Returns vertices to draw this ``Point`` annotation. """

        xax, yax, zax        = axes
        lineWidth            = self.normalisedLineWidth
        offset               = lineWidth * 2
        x, y                 = self.x, self.y
        verts                = np.zeros((4, 3), dtype=np.float32)
        verts[0, [xax, yax]] = [x - offset, y]
        verts[1, [xax, yax]] = [x + offset, y]
        verts[2, [xax, yax]] = [x, y - offset]
        verts[3, [xax, yax]] = [x, y + offset]
        verts[:, zax]        = zpos

        verts = glroutines.lineAsPolygon(verts, lineWidth, zax)

        return [(gl.GL_TRIANGLES, verts)]


    def vertices3D(self):
        """Returns vertices to draw this ``Point`` annotation. """

        lineWidth   = self.normalisedLineWidth
        offset      = lineWidth * 2
        x, y, z     = self.x, self.y, self.z
        verts       = np.zeros((6, 3), dtype=np.float32)
        verts[0, :] = [x - offset, y,          z]
        verts[1, :] = [x + offset, y,          z]
        verts[2, :] = [x,          y - offset, z]
        verts[3, :] = [x,          y + offset, z]
        verts[4, :] = [x,          y,          z - offset]
        verts[5, :] = [x,          y,          z + offset]

        # See note in Line.vertices3D
        if self.applyMvp:
            camera = affine.transform(
                [0, -1, 0],
                affine.invert(self.annot.canvas.viewRotation),
                vector=True)
        else:
            camera = [0, 0, 1]

        verts = glroutines.lineAsPolygon(verts, lineWidth, camera=camera)

        return [(gl.GL_TRIANGLES, verts)]


    def hit(self, x, y):
        """Returns ``True`` if ``(x, y)`` is within the bounds of this
        ``Point``, ``False`` otherwise.
        """
        lineWidth = self.normalisedLineWidth
        px, py    = self.x, self.y
        dist      = np.sqrt((x - px) ** 2 + (y - py) ** 2)
        return dist <= (lineWidth * 2)


    def move(self, x, y):
        """Move this ``Point`` according to ``x`` and ``y``. """
        self.x = self.x + x
        self.y = self.y + y


class Line(AnnotationObject):
    """The ``Line`` class is an :class:`AnnotationObject` which represents a
    2D line.
    """


    def __init__(self, annot, x1, y1, x2, y2, z1=None, z2=None, **kwargs):
        """Create a ``Line`` annotation.

        The ``xy1`` and ``xy2`` coordinate tuples should be in relation to the
        axes which map to the horizontal/vertical screen axes on the target
        canvas.

        :arg annot: The :class:`Annotations` object that owns this ``Line``.
        :arg x1:    X coordinate of one endpoint.
        :arg y1:    Y coordinate of one endpoint.
        :arg x2:    X coordinate of the other endpoint.
        :arg y2:    Y coordinate of the second endpoint.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """
        AnnotationObject.__init__(self, annot, **kwargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.z1 = z1
        self.z2 = z2


    def vertices2D(self, zpos, axes):
        """Returns a set of vertices for drawing this line on a 2D plane,
        with the ``GL_TRIANGLES`` primitive.
        """
        xax, yax, zax  = axes
        lineWidth      = self.normalisedLineWidth
        points         = np.zeros((2, 3))
        points[:, xax] = [self.x1, self.x2]
        points[:, yax] = [self.y1, self.y2]
        points[:, zax] = zpos

        verts = glroutines.lineAsPolygon(points, lineWidth, axis=zax)

        return [(gl.GL_TRIANGLES, verts)]


    def vertices3D(self):
        """Returns a set of vertices for drawing this line in a 3D space,
        with the ``GL_TRIANGLES`` primitive.
        """
        verts       = np.zeros((2, 3), dtype=np.float32)
        verts[0, :] = self.x1, self.y1, self.z1
        verts[1, :] = self.x2, self.y2, self.z2

        lineWidth = self.normalisedLineWidth

        # To draw the line at the requested width,
        # we have to specify the camera direction
        # in the display coordinate system. The
        # Scene3DCanvas initially points towards
        # -y, so we can localise it by applying
        # the inverse model-view matrix to that
        # vector.
        if self.applyMvp:
            camera = affine.transform(
                [0, -1, 0],
                affine.invert(self.annot.canvas.viewRotation),
                vector=True)
        else:
            camera = [0, 0, 1]

        verts = glroutines.lineAsPolygon(verts, lineWidth, camera=camera)

        return [(gl.GL_TRIANGLES, verts)]


    def hit(self, x, y):
        """Returns ``True`` if ``(x, y)`` is within the bounds of this
        ``Line``, ``False`` otherwise.

        http://paulbourke.net/geometry/pointlineplane/
        """

        x1, y1 = self.x1, self.y1
        x2, y2 = self.x2, self.y2
        x3, y3 = x, y

        num = np.abs((x3 - x1) * (x2 - x1) + (y3 - y1) * (y2 - y1))
        dnm = (x2 - x1) ** 2 + (y2 - y1) ** 2
        u   = num / dnm

        ix   = x1 + u * (x2 - x1)
        iy   = y1 + u * (y2 - y1)
        dist = np.sqrt((x3 - ix) ** 2 + (y3 - iy) ** 2)

        return dist <= self.normalisedLineWidth


    def move(self, x, y):
        """Move this ``Line`` according to ``(x, y)``."""
        self.x1 = self.x1 + x
        self.y1 = self.y1 + y
        self.x2 = self.x2 + x
        self.y2 = self.y2 + y


class Arrow(Line):
    """The ``Arrow`` class is an :class:`AnnotationObject` which represents a
    2D line with an arrow head at one end. The size of the is proportional
    to the current :attr:`AnnotationObject.lineWidth`.
    """


    def vertices2D(self, zpos, axes):
        """Draw the arrow. """

        lineverts = Line.vertices2D(self, zpos, axes)

        xax, yax, zax = axes

        # We draw the arrow head as a triangle at the
        # second line vertex (xy2). We generate the
        # two other vertices of the triangle by
        # rotating +/- 30 degrees around xy2.
        xy1   = np.array([self.x1, self.y1])
        xy2   = np.array([self.x2, self.y2])
        vec   = xy2 - xy1
        vec   = vec / np.sqrt(vec[0] ** 2 + vec[1] ** 2)
        angle = np.arccos(np.dot(vec, [1, 0])) * np.sign(vec[1])
        delta = np.pi / 6

        p1 = np.array((np.cos(angle + delta), np.sin(angle + delta)))
        p2 = np.array((np.cos(angle - delta), np.sin(angle - delta)))

        # We also add a little padding to xy2 because
        # otherwise the main line may appear beyond
        # the triangle if a large line width is set.
        xy2 = xy2 + self.lineWidth * vec * 0.5
        p1  = xy2 - self.lineWidth * p1
        p2  = xy2 - self.lineWidth * p2

        verts = np.zeros((3, 3), dtype=np.float32)
        verts[0, [xax, yax]] = xy2
        verts[1, [xax, yax]] = p1
        verts[2, [xax, yax]] = p2
        verts[:, zax]        = zpos

        verts = [(gl.GL_TRIANGLES, verts)]

        return lineverts + verts


class BorderMixin:
    """Mixin for ``AnnotationObject`` classes which display a shape which
    can be filled or unfilled, and can have a border or no border.
    """


    filled = props.Boolean(default=True)
    """Whether to fill the rectangle. """


    border = props.Boolean(default=True)
    """Whether to draw a border around the rectangle. """


    def draw2D(self, canvas, zpos, axes):
        shader   = self.annot.defaultShader
        mvpmat   = canvas.mvpMatrix
        vertices = self.vertices2D(zpos, axes)

        if vertices is None or len(vertices) == 0:
            return

        primitives              = [v[0] for v in vertices]
        vertices                = [v[1] for v in vertices]
        vertices, lens, offsets = glroutines.stackVertices(vertices)

        colour = list(self.colour[:3])
        alpha  = self.alpha / 100.0

        with shader.loaded():
            shader.set(   'MVP',    mvpmat)
            shader.setAtt('vertex', vertices)

            with shader.loadedAtts():
                if self.border:
                    prim   = primitives.pop(0)
                    off    = offsets   .pop(0)
                    length = lens      .pop(0)
                    if self.filled: shader.set('colour', colour + [1.0])
                    else:           shader.set('colour', colour + [alpha])
                    shader.draw(prim, off, length)
                if self.filled:
                    prim   = primitives.pop(0)
                    off    = offsets   .pop(0)
                    length = lens      .pop(0)
                    shader.set('colour', colour + [alpha])
                    shader.draw(prim, off, length)


class Rect(BorderMixin, AnnotationObject):
    """The ``Rect`` class is an :class:`AnnotationObject` which represents a
    2D rectangle.
    """


    def __init__(self,
                 annot,
                 x,
                 y,
                 w,
                 h,
                 filled=True,
                 border=True,
                 **kwargs):
        """Create a :class:`Rect` annotation.

        :arg annot:  The :class:`Annotations` object that owns this
                     ``Rect``.

        :arg x:      X coordinate of one  corner of the rectangle, in
                     the display coordinate system.

        :arg y:      Y coordinate of one  corner of the rectangle, in
                     the display coordinate system.

        :arg w:      Rectangle width (actually an offset relative to ``x``)

        :arg h:      Rectangle height (actually an offset relative to ``y``)

        :arg filled: If ``True``, the rectangle is filled

        :arg border: If ``True``, a border is drawn around the rectangle.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.

        Note that if ``filled=False`` and ``border=False``, nothing will be
        drawn. The ``.AnnotationObject.alpha`` value is ignored when drawing
        the border.
        """
        AnnotationObject.__init__(self, annot, **kwargs)

        self.x      = x
        self.y      = y
        self.w      = w
        self.h      = h
        self.filled = filled
        self.border = border


    def hit(self, x, y):
        """Returns ``True`` if ``(x, y)`` is within the bounds of this
        ``Rect``, ``False`` otherwise.
        """

        xlo, ylo = self.x, self.y
        xhi, yhi = (xlo + self.w, ylo + self.h)

        xlo, xhi = sorted((xlo, xhi))
        ylo, yhi = sorted((ylo, yhi))

        return (x >= xlo and
                x <= xhi and
                y >= ylo and
                y <= yhi)


    def move(self, x, y):
        """Move this ``Rect`` according to ``(x, y)``."""
        self.x = self.x + x
        self.y = self.y + y


    def vertices2D(self, zpos, axes):
        """Generates vertices to draw this ``Rectangle`` annotation. """

        if self.w == 0 or self.h == 0:
            return

        xax, yax, zax = axes
        x, y          = self.x, self.y
        w             = self.w
        h             = self.h

        bl = [x,     y]
        br = [x + w, y]
        tl = [x,     y + h]
        tr = [x + w, y + h]

        verts = []

        if self.border:
            verts.append(self.__border(zpos, xax, yax, zax, bl, br, tl, tr))

        if self.filled:
            verts.append(self.__fill(zpos, xax, yax, zax, bl, br, tl, tr))

        return verts


    def __fill(self, zpos, xax, yax, zax, bl, br, tl, tr):
        """Generate the rectangle fill. """
        verts = np.zeros((6, 3), dtype=np.float32)
        verts[0, [xax, yax]] = bl
        verts[1, [xax, yax]] = br
        verts[2, [xax, yax]] = tl
        verts[3, [xax, yax]] = tl
        verts[4, [xax, yax]] = br
        verts[5, [xax, yax]] = tr
        verts[:,       zax]  = zpos
        return gl.GL_TRIANGLES, verts


    def __border(self, zpos, xax, yax, zax, bl, br, tl, tr):
        """Generate the rectangle outline. """
        lineWidth            = self.normalisedLineWidth
        verts                = np.zeros((8, 3), dtype=np.float32)
        verts[0, [xax, yax]] = bl
        verts[1, [xax, yax]] = br
        verts[2, [xax, yax]] = tl
        verts[3, [xax, yax]] = tr
        verts[4, [xax, yax]] = bl
        verts[5, [xax, yax]] = tl
        verts[6, [xax, yax]] = br
        verts[7, [xax, yax]] = tr
        verts[:,       zax]  = zpos

        verts = glroutines.lineAsPolygon(verts, lineWidth, axis=zax)

        return gl.GL_TRIANGLES, verts


class Ellipse(BorderMixin, AnnotationObject):
    """The ``Ellipse`` class is an :class:`AnnotationObject` which represents a
    ellipse.
    """


    def __init__(self,
                 annot,
                 x,
                 y,
                 w,
                 h,
                 npoints=60,
                 filled=True,
                 border=True,
                 **kwargs):
        """Create an ``Ellipse`` annotation.

        :arg annot:   The :class:`Annotations` object that owns this
                      ``Ellipse``.

        :arg x:       X coordinate of ellipse centre, in the display
                      coordinate system.

        :arg y:       Y coordinate of ellipse centre, in the display
                      coordinate system.

        :arg w:       Horizontal radius.

        :arg h:       Vertical radius.

        :arg npoints: Number of vertices used to draw the ellipse outline.

        :arg filled:  If ``True``, the ellipse is filled

        :arg border: If ``True``, a border is drawn around the ellipse

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """

        AnnotationObject.__init__(self, annot, **kwargs)

        self.x       = x
        self.y       = y
        self.w       = w
        self.h       = h
        self.npoints = npoints
        self.filled  = filled
        self.border  = border


    def hit(self, x, y):
        """Returns ``True`` if ``(x, y)`` is within the bounds of this
        ``Ellipse``, ``False`` otherwise.
        """

        # https://math.stackexchange.com/a/76463
        h,  k  = self.x, self.y
        rx, ry = self.w, self.h
        return ((x - h) ** 2) / (rx ** 2) + ((y - k) ** 2) / (ry ** 2) <= 1


    def move(self, x, y):
        """Move this ``Rect`` according to ``(x, y)``."""
        self.x = self.x + x
        self.y = self.y + y


    def vertices2D(self, zpos, axes):
        """Generate vertices for this ``Ellipse`` annotation. """

        if (self.w == 0) or (self.h == 0):
            return

        xax, yax, zax = axes
        x, y          = self.x, self.y
        w, h          = self.w, self.h

        verts   = np.zeros((self.npoints + 1, 3), dtype=np.float32)
        samples = np.linspace(0, 2 * np.pi, self.npoints)

        verts[0, [xax, yax]] = x, y
        verts[1:, xax]       = w * np.sin(samples) + x
        verts[1:, yax]       = h * np.cos(samples) + y
        verts[:,  zax]       = zpos

        allVertices = []

        # border
        if self.border:
            borderVerts = glroutines.lineAsPolygon(
                verts[1:], self.normalisedLineWidth, axis=zax, mode='strip')
            allVertices.append((gl.GL_TRIANGLES, borderVerts))
        if self.filled:
            allVertices.append((gl.GL_TRIANGLE_FAN, verts))

        return allVertices


class VoxelSelection(AnnotationObject):
    """A ``VoxelSelection`` is an :class:`AnnotationObject` which draws
    selected voxels from a :class:`.selection.Selection` instance.  A
    :class:`.SelectionTexture` is used to draw the selected voxels.
    """


    def __init__(self,
                 annot,
                 selection,
                 overlay,
                 offsets=None,
                 **kwargs):
        """Create a ``VoxelSelection`` annotation.

        :arg annot:     The :class:`Annotations` object that owns this
                        ``VoxelSelection``.

        :arg selection: A :class:`.selection.Selection` instance which defines
                        the voxels to be highlighted.

        :arg overlay:   A :class:`.Nifti` instance which is used for its
                        voxel-to-display transformation matrices.

        :arg offsets:   If ``None`` (the default), the ``selection`` must have
                        the same shape as the image data being
                        annotated. Alternately, you may set ``offsets`` to a
                        sequence of three values, which are used as offsets
                        for the xyz voxel values. This is to allow for a
                        sub-space of the full image space to be annotated.

        All other arguments are passed through to the
        :meth:`AnnotationObject.__init__` method.
        """

        if offsets is None:
            offsets = [0, 0, 0]

        self.__selection = selection
        self.__overlay   = overlay
        self.__offsets   = offsets

        texName = f'{type(self).__name__}_{id(selection)}'

        ndims = texdata.numTextureDims(selection.shape)

        if ndims == 2: ttype = textures.SelectionTexture2D
        else:          ttype = textures.SelectionTexture3D

        self.__texture = glresources.get(
            texName,
            ttype,
            texName,
            selection)

        self.__shader = self.__createShader()

        # Call base class init afterwards,
        # as the init function may need to
        # access the texture created above.
        AnnotationObject.__init__(self, annot, **kwargs)


    def __createShader(self):
        """Called by :meth:`__init__`. Creates a shader program.
        """
        constants = {'textureIs2D' : self.texture.ndim == 2}
        vertSrc   = shaders.getVertexShader(  'annotations_voxelselection')
        fragSrc   = shaders.getFragmentShader('annotations_voxelselection')

        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            return shaders.ARBPShader(vertSrc, fragSrc, constants=constants)
        else:
            return shaders.GLSLShader(vertSrc, fragSrc, constants=constants)


    def destroy(self):
        """Must be called when this ``VoxelSelection`` is no longer needed.
        Destroys the :class:`.SelectionTexture`.
        """
        super().destroy()

        if self.__texture is not None:
            glresources.delete(self.__texture.name)

        if self.__shader is not None:

            self.__shader.destroy()

        self.__overlay = None
        self.__shader  = None
        self.__texture = None


    @property
    def texture(self):
        """Return the :class:`.SelectionTexture` used by this
        ``VoxelSelection``.
        """
        return self.__texture


    def vertices2D(self, zpos, axes):
        """Returns vertices and texture coordinates to draw this
        ``VoxelSelection``.
        """

        xax, yax, zax = axes
        opts          = self.annot.canvas.displayCtx.getOpts(self.__overlay)
        texture       = self.__texture
        shape         = self.__selection.getSelection().shape
        displayToVox  = opts.getTransform('display', 'voxel')
        voxToDisplay  = opts.getTransform('voxel',   'display')
        voxToTex      = opts.getTransform('voxel',   'texture')
        voxToTex      = affine.concat(texture.texCoordXform(shape), voxToTex)
        verts, voxs   = glroutines.slice2D(shape,
                                           xax,
                                           yax,
                                           zpos,
                                           voxToDisplay,
                                           displayToVox)

        # See note in GLImageObject.generateVoxelCoordinates2D
        voxs  = opts.roundVoxels(voxs, daxes=[zax])
        texs  = affine.transform(voxs, voxToTex)
        verts = np.array(verts, dtype=np.float32)
        texs  = np.array(texs,  dtype=np.float32)

        return verts, texs


    def draw2D(self, canvas, zpos, axes):
        """Draw a :class:`.VoxelSelection` annotation. """

        shader              = self.__shader
        texture             = self.texture
        mvpmat              = canvas.mvpMatrix
        colour              = list(self.colour[:3]) + [self.alpha / 100.0]
        vertices, texCoords = self.vertices2D(zpos, axes)

        with texture.bound(gl.GL_TEXTURE0), shader.loaded():
            shader.set(   'tex',      0)
            shader.set(   'MVP',      mvpmat)
            shader.set(   'colour',   colour)
            shader.setAtt('vertex',   vertices)
            shader.setAtt('texCoord', texCoords)
            shader.draw(gl.GL_TRIANGLES, 0, len(vertices))


class TextAnnotation(AnnotationObject):
    """A ``TextAnnotation`` is an ``AnnotationObject`` which draws a
    :class:`fsleyes.gl.text.Text` object.

    The ``Text`` class allows the text position to be specified as either
    x/y proportions, or as absolute pixels. The ``TextAnnotation`` class
    adds an additional option to specify the location in terms of a
    3D position in the display coordinate system.

    This can be achieved by setting ``coordinates`` to ``'display'``, and
    setting ``pos`` to the 3D position in the display coordinate system.
    """


    text  = props.String()
    """Text to draw. """


    fontSize = props.Int(minval=6, maxval=48)
    """Text font size in points. The size of the text annotation is kept
    proportional to the canvas zoom level.
    """


    def __init__(self,
                 annot,
                 text=None,
                 x=None,
                 y=None,
                 off=None,
                 coordinates='proportions',
                 fontSize=10,
                 halign=None,
                 valign=None,
                 colour=None,
                 **kwargs):
        """Create a ``TextAnnotation``.

        :arg annot:      The :class:`Annotations` object that owns this
                         ``TextAnnotation``.

        See the :class:`.Text` class for details on the other arguments.
        """
        AnnotationObject.__init__(self, annot, **kwargs)

        self.text        = text
        self.x           = x
        self.y           = y
        self.off         = off
        self.coordinates = coordinates
        self.fontSize    = fontSize
        self.halign      = halign
        self.valign      = valign
        self.colour      = colour
        self.__initscale = None
        self.__text      = gltext.Text()


    @property
    def gltext(self):
        return self.__text


    def destroy(self):
        """Must be called when this ``TextAnnotation`` is no longer needed.
        """
        super().destroy()
        if self.__text is not None:
            self.__text.destroy()
            self.__text = None


    def draw2D(self, canvas, zpos, axes):
        """Draw this ``TextAnnotation``. """

        if self.colour is not None: colour = self.colour[:3]
        else:                       colour = [1, 1, 1]

        text             = self.__text
        opts             = canvas.opts
        text.text        = self.text
        text.off         = self.off
        text.coordinates = self.coordinates
        text.fontSize    = self.fontSize
        text.halign      = self.halign
        text.valign      = self.valign
        text.colour      = colour
        text.alpha       = self.alpha / 100

        if self.coordinates == 'display':

            # Make sure the text is sized proportional
            # to the display coordinate system, so
            # invariant to zoom factor/canvas size
            if self.__initscale is None:
                w, h             = canvas.pixelSize()
                self.__initscale = np.sqrt(w * h)

            w, h  = canvas.pixelSize()
            scale = np.sqrt(w * h)

            pos           = [0] * 3
            pos[opts.xax] = self.x
            pos[opts.yax] = self.y
            pos[opts.zax] = opts.pos[2]

            text.pos         = canvas.worldToCanvas(pos)
            text.scale       = self.__initscale / scale
            text.coordinates = 'pixels'
        else:
            text.pos         = self.x, self.y
            text.coordinates = self.coordinates

        text.draw(*canvas.GetSize())


    def hit(self, x, y):
        """Returns ``True`` if ``(x, y)`` is within the bounds of this
        ``TextAnnotation``, ``False`` otherwise. Only supported for text
        drawn relative to the display coordinate system
        (``coordinates='display'``) - raises a ``NotImplementedError``
        otherwise.
        """

        if self.coordinates != 'display':
            raise NotImplementedError()

        canvas     = self.annot.canvas
        opts       = canvas.opts
        xlo,  ylo  = self.__text.pos
        xlen, ylen = self.__text.size

        # the Text object works in pixels, but
        # here we're working in display coords
        xy1 = canvas.canvasToWorld(xlo,        ylo)
        xy2 = canvas.canvasToWorld(xlo + xlen, ylo + ylen)

        xlo, xhi = sorted((xy1[opts.xax], xy2[opts.xax]))
        ylo, yhi = sorted((xy1[opts.yax], xy2[opts.yax]))

        return (x >= xlo and
                x <= xhi and
                y >= ylo and
                y <= yhi)


    def move(self, x, y):
        """Move this ``TextAnnotation`` according to ``(x, y)``.

        Only supported for text drawn relative to the display coordinate
        system (``coordinates='display'``) - raises a ``NotImplementedError``
        otherwise.
        """
        if self.coordinates != 'display':
            raise NotImplementedError()

        self.x = self.x + x
        self.y = self.y + y
