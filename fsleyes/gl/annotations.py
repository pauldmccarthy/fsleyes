#!/usr/bin/env python
#
# annotations.py - 2D annotations on a SliceCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Annotations` class, which implements
functionality to draw 2D OpenGL annotations on a :class:`.SliceCanvas`.


The :class:`Annotations` class is used by the :class:`.SliceCanvas` and
:class:`.LightBoxCanvas` classes, and users of those class, to annotate the
canvas.


.. note:: The ``Annotations`` class only works with the :class:`.SliceCanvas`
          and :class:`.LightBoxCanvas` - there is no support for the
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
   VoxelGrid
   VoxelSelection
   TextAnnotation
"""


import logging
import time

import numpy       as np
import OpenGL.GL   as gl

import fsl.transform.affine     as affine
import fsleyes_props            as props
import fsleyes.gl.globject      as globject
import fsleyes.gl.routines      as glroutines
import fsleyes.gl.resources     as glresources
import fsleyes.gl.textures      as textures
import fsleyes.gl.text          as gltext
import fsleyes.gl.textures.data as texdata


log = logging.getLogger(__name__)


class Annotations(props.HasProperties):
    """An :class:`Annotations` object provides functionality to draw 2D
    annotations on a :class:`.SliceCanvas`. Annotations may be enqueued via
    any of the :meth:`line`, :meth:`rect`, :meth:`circle`, :meth:`point`,
    :meth:`grid`, :meth:`selection` or :meth:`obj`, methods.


    A call to :meth:`draw` will then draw each of the queued annotations on
    the canvas, and clear the queue.


    If an annotation is to be persisted, it can be enqueued, as above, but
    passing ``hold=True`` to the queueing method.  The annotation will then
    remain in the queue until it is removed via :meth:`dequeue`, or the
    entire annotations queue is cleared via :meth:`clear`. Held, or persistent,
    annotations are stored in the :attr:`annotations` attribute.


    Annotations can be queued by one of the helper methods on the
    :class:`Annotations` object (e.g. :meth:`line` or :meth:`rect`), or by
    manually creating an :class:`AnnotationObject` and passing it to the
    :meth:`obj` method.
    """


    annotations = props.List()
    """Contains all persistent :class:`AnnotationObject` instances, which have
    been added to the queue with ``hold=True``.
    """


    def __init__(self, canvas, xax, yax):
        """Creates an :class:`Annotations` object.

        :arg canvas: The :class:`.SliceCanvas` that owns this
                     ``Annotations`` object.

        :arg xax:    Index of the display coordinate system axis that
                     corresponds to the horizontal screen axis.

        :arg yax:    Index of the display coordinate system axis that
                     corresponds to the vertical screen axis.
        """

        self.__q      = []
        self.__xax    = xax
        self.__yax    = yax
        self.__zax    = 3 - xax - yax
        self.__canvas = canvas


    @property
    def canvas(self):
        """Returns a ref to the canvas that owns this ``Annotations`` instance.
        """
        return self.__canvas


    def setAxes(self, xax, yax):
        """This method must be called if the display orientation changes.  See
        :meth:`__init__`.
        """

        self.__xax = xax
        self.__yax = yax
        self.__zax = 3 - xax - yax


    def getDisplayBounds(self):
        """Returns a tuple containing the ``(xmin, xmax, ymin, ymax)`` display
        bounds of the ``SliceCanvas`` that owns this ``Annotations`` object.
        """
        return self.__canvas.opts.displayBounds


    def line(self, *args, **kwargs):
        """Queues a line for drawing - see the :class:`Line` class. """
        hold = kwargs.pop('hold', False)
        obj  = Line(self, *args, **kwargs)

        return self.obj(obj, hold)


    def arrow(self, *args, **kwargs):
        """Queues an arrow for drawing - see the :class:`Arrow` class. """
        hold = kwargs.pop('hold', False)
        obj  = Arrow(self, *args, **kwargs)

        return self.obj(obj, hold)


    def point(self, *args, **kwargs):
        """Queues a point for drawing - see the :class:`Point` class. """
        hold = kwargs.pop('hold', False)
        obj  = Point(self, *args, **kwargs)

        return self.obj(obj, hold)


    def rect(self, *args, **kwargs):
        """Queues a rectangle for drawing - see the :class:`Rectangle` class.
        """
        hold = kwargs.pop('hold', False)
        obj  = Rect(self, *args, **kwargs)

        return self.obj(obj, hold)


    def ellipse(self, *args, **kwargs):
        """Queues a circle for drawing - see the :class:`Ellipse` class.
        """
        hold = kwargs.pop('hold', False)
        obj  = Ellipse(self, *args, **kwargs)

        return self.obj(obj, hold)


    def grid(self, *args, **kwargs):
        """Queues a voxel grid for drawing - see the :class:`VoxelGrid` class.
        """
        hold = kwargs.pop('hold', False)
        obj  = VoxelGrid(self, *args, **kwargs)

        return self.obj(obj, hold)


    def selection(self, *args, **kwargs):
        """Queues a selection for drawing - see the :class:`VoxelSelection`
        class.
        """
        hold = kwargs.pop('hold', False)
        obj  = VoxelSelection(self, *args, **kwargs)

        return self.obj(obj, hold)


    def text(self, *args, **kwargs):
        """Queues a text annotation for drawing - see the :class:`Text`
        class.
        """
        hold = kwargs.pop('hold', False)
        obj  = TextAnnotation(self, *args, **kwargs)

        return self.obj(obj, hold)


    def obj(self, obj, hold=False):
        """Queues the given :class:`AnnotationObject` for drawing.

        :arg hold: If ``True``, the given ``AnnotationObject`` will be kept in
                   the queue until it is explicitly removed. Otherwise (the
                   default), the object will be removed from the queue after
                   it has been drawn.
        """

        if hold: self.annotations.append(obj)
        else:    self.__q        .append(obj)

        return obj


    def dequeue(self, obj, hold=False):
        """Removes the given :class:`AnnotationObject` from the queue, but
        does not call its :meth:`.GLObject.destroy` method - this is the
        responsibility of the caller.
        """

        if hold:
            try:               self.annotations.remove(obj)
            except ValueError: pass
        else:
            try:               self.__q.remove(obj)
            except ValueError: pass


    def clear(self):
        """Clears both the normal queue and the persistent (a.k.a. ``hold``)
        queue, and calls the :meth:`.GLObject.destroy` method on every object
        in the queue.
        """

        for obj in self.__q:         obj.destroy()
        for obj in self.annotations: obj.destroy()

        self.__q            = []
        self.annotations[:] = []


    def draw(self, zpos, xform=None, skipHold=False):
        """Draws all enqueued annotations.

        :arg zpos:     Position along the Z axis, above which all annotations
                       should be drawn.

        :arg xform:    Transformation matrix which should be applied to all
                       objects.

        :arg skipHold: Do not draw items on the hold queue - only draw one-off
                       items.
        """

        if not skipHold: objs = list(self.annotations) + self.__q
        else:            objs = self.__q

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glMultMatrixf(xform.ravel('F'))

        drawTime = time.time()
        axes     = (self.__xax, self.__yax, self.__zax)

        for obj in objs:

            if obj.expired(drawTime): continue
            if not obj.enabled:       continue
            if obj.honourZLimits:
                if obj.zmin is not None and zpos < obj.zmin: continue
                if obj.zmax is not None and zpos > obj.zmax: continue

            if obj.xform is not None:
                gl.glMatrixMode(gl.GL_MODELVIEW)
                gl.glPushMatrix()
                gl.glMultMatrixf(obj.xform.ravel('F'))

            if obj.colour is not None:

                if len(obj.colour) == 3: colour = list(obj.colour) + [1.0]
                else:                    colour = list(obj.colour)

                colour[3] = obj.alpha / 100.0

                gl.glColor4f(*colour)

            if obj.lineWidth is not None:
                gl.glLineWidth(obj.lineWidth)

            try:
                obj.preDraw()
                obj.draw2D(zpos, axes)
                obj.postDraw()
            except Exception as e:
                log.warning('{}'.format(e), exc_info=True)

            if obj.xform is not None:
                gl.glPopMatrix()

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPopMatrix()

        # Clear the regular queue after each draw
        self.__q = []


class AnnotationObject(globject.GLSimpleObject, props.HasProperties):
    """Base class for all annotation objects. An ``AnnotationObject`` is drawn
    by an :class:`Annotations` instance. The ``AnnotationObject`` contains some
    attributes which are common to all annotation types:

    ============  =============================================================
    ``colour``    Annotation colour
    ``enabled``   Whether the annotation should be drawn or not.
    ``lineWidth`` Annotation line width (if the annotation is made up of lines)
    ``xform``     Custom transformation matrix to apply to annotation vertices.
    ``expiry``    Time (in seconds) after which the annotation will expire and
                  not be drawn.
    ``zmin``      Minimum z value below which this annotation will not be
                  drawn.
    ``zmax``      Maximum z value above which this annotation will not be
                  drawn.
    ``fixed``     Flag indicating that this annotation cannot be modified.
                  This is not enforced in any way, but is used by the
                  :class:`.OrthoAnnotateProfile` to determine which annotations
                  can be manipulated by the user.
    ``creation``  Time of creation.
    ============  =============================================================

    All of these attributes can be modified directly, after which you should
    trigger a draw on the owning ``SliceCanvas`` to refresh the annotation.
    You shouldn't touch the ``expiry`` or ``creation`` attributes though.

    Subclasses must, at the very least, override the
    :meth:`globject.GLObject.draw2D` method.
    """


    enabled = props.Boolean(default=True)
    """Whether to draw this annotation or not. """


    lineWidth = props.Int(default=1)
    """Line width, for annotations which are drawn with lines. """


    colour = props.Colour(default='#a00000')
    """Annotation colour."""


    alpha = props.Percentage(default=100)
    """Opacity."""


    honourZLimits = props.Boolean(default=False)
    """If True, the :attr:`zmin`/:attr:`zmax` properties are enforced.
    Otherwise (the default) they are ignored, and the annotation is
    always drawn.
    """


    zmin = props.Real()
    """Minimum z value below which this annotation will not be drawn. """


    zmax = props.Real()
    """Maximum z value below which this annotation will not be drawn. """


    def __init__(self,
                 annot,
                 xform=None,
                 colour=None,
                 alpha=None,
                 lineWidth=None,
                 enabled=True,
                 expiry=None,
                 honourZLimits=False,
                 zmin=None,
                 zmax=None,
                 fixed=True,
                 **kwargs):
        """Create an ``AnnotationObject``.

        :arg annot:         The :class:`Annotations` object that created this
                            ``AnnotationObject``.

        :arg xform:         Transformation matrix which will be applied to all
                            vertex coordinates.

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

        :arg fixed:         Flag indicating whether this ``AnnotationObject``
                            can be modified.

        Any other arguments are ignored.
        """
        globject.GLSimpleObject.__init__(self, False)

        self.annot    = annot
        self.xform    = xform
        self.creation = time.time()
        self.fixed    = fixed
        self.expiry   = expiry

        if colour        is not None: self.colour        = colour
        if alpha         is not None: self.alpha         = alpha
        if enabled       is not None: self.enabled       = enabled
        if lineWidth     is not None: self.lineWidth     = lineWidth
        if honourZLimits is not None: self.honourZLimits = honourZLimits
        if zmin          is not None: self.zmin          = zmin
        if zmax          is not None: self.zmax          = zmax

        if self.xform is not None:
            self.xform = np.array(self.xform, dtype=np.float32)


    def resetExpiry(self):
        """Resets the expiry for this ``AnnotationObject`` so that it is
        valid from the current time.
        """
        self.creation = time.time()


    def hit(self, xy):
        """Return ``True`` if the given X/Y point is within the bounds of this
        annotation, ``False`` otherwise.  Must be implemented by sub-classes,
        but only those annotations which are drawn by the
        :class:`.OrthoAnnotateProfile`.

        :arg xy: ``(x, y)`` tuple in display coordinates.
        """
        raise NotImplementedError()


    def move(self, xy):
        """Move this annotation acording to xy, which is specified as an offset
        relative to the current location. Must be implemented by sub-classes,
        but only those annotations which are drawn by the
        :class:`.OrthoAnnotateProfile`.

        :arg xy: ``(x, y)`` tuple in display coordinates.
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


    def preDraw(self, *args, **kwargs):
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)


    def postDraw(self, *args, **kwargs):
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)


class Point(AnnotationObject):
    """The ``Point`` class is an :class:`AnnotationObject` which represents a
    point, drawn as a small crosshair. The size of the point is proportional
    to the :attr:`AnnotationObject.lineWidth`.
    """


    def __init__(self, annot, xy, *args, **kwargs):
        """Create a ``Point`` annotation.

        The ``xy`` coordinate tuple should be in relation to the axes which
        map to the horizontal/vertical screen axes on the target canvas.

        :arg annot: The :class:`Annotations` object that owns this ``Point``.

        :arg xy:    Tuple containing the (x, y) coordinates of the point

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """
        AnnotationObject.__init__(self, annot, *args, **kwargs)
        self.xy = xy


    def draw2D(self, zpos, axes):
        """Draws this ``Point`` annotation. """

        xax, yax, zax        = axes
        offset               = self.lineWidth * 0.5
        x, y                 = self.xy
        idxs                 = np.arange(4,     dtype=np.uint32)
        verts                = np.zeros((4, 3), dtype=np.float32)
        verts[0, [xax, yax]] = [x - offset, y]
        verts[1, [xax, yax]] = [x + offset, y]
        verts[2, [xax, yax]] = [x, y - offset]
        verts[3, [xax, yax]] = [x, y + offset]
        verts[:, zax]        = zpos
        verts                = verts.ravel('C')

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
        gl.glDrawElements(gl.GL_LINES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


    def hit(self, xy):
        """Returns ``True`` if ``xy`` is within the bounds of this ``Point``,
        ``False`` otherwise.
        """
        x, y   = xy
        px, py = self.xy
        dist   = np.sqrt((x - px) ** 2 + (y - py) ** 2)
        return dist <= self.lineWidth


    def move(self, xy):
        """Move this ``Point`` according to ``xy``. """
        self.xy = (self.xy[0] + xy[0], self.xy[1] + xy[1])


class Line(AnnotationObject):
    """The ``Line`` class is an :class:`AnnotationObject` which represents a
    2D line.
    """


    def __init__(self, annot, xy1, xy2, *args, **kwargs):
        """Create a ``Line`` annotation.

        The ``xy1`` and ``xy2`` coordinate tuples should be in relation to the
        axes which map to the horizontal/vertical screen axes on the target
        canvas.

        :arg annot: The :class:`Annotations` object that owns this ``Line``.

        :arg xy1:   Tuple containing the (x, y) coordinates of one endpoint.

        :arg xy2:   Tuple containing the (x, y) coordinates of the second
                    endpoint.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """
        AnnotationObject.__init__(self, annot, *args, **kwargs)
        self.xy1 = xy1
        self.xy2 = xy2


    def draw2D(self, zpos, axes):
        """Draws this ``Line`` annotation. """

        xax, yax, zax = axes

        idxs                 = np.arange(2,     dtype=np.uint32)
        verts                = np.zeros((2, 3), dtype=np.float32)
        verts[0, [xax, yax]] = self.xy1
        verts[1, [xax, yax]] = self.xy2
        verts[:, zax]        = zpos
        verts                = verts.ravel('C')

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
        gl.glDrawElements(gl.GL_LINES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


    def hit(self, xy):
        """Returns ``True`` if ``xy`` is within the bounds of this ``Line``,
        ``False`` otherwise.

        https://en.wikipedia.org/wiki/\
            Distance_from_a_point_to_a_line#Line_defined_by_two_points
        """

        x0, y0 = xy
        x1, y1 = self.xy1
        x2, y2 = self.xy2

        area = np.abs((x2 - x1) * (y1 - y0) - (x1 - x0) * (y2 - y1))
        dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        return (area / dist) <= (self.lineWidth * 2)


    def move(self, xy):
        """Move this ``Line`` according to ``xy``."""
        self.xy1 = (self.xy1[0] + xy[0], self.xy1[1] + xy[1])
        self.xy2 = (self.xy2[0] + xy[0], self.xy2[1] + xy[1])


class Arrow(Line):
    """The ``Arrow`` class is an :class:`AnnotationObject` which represents a
    2D line with an arrow head at one end. The size of the is proportional
    to the current :attr:`AnnotationObject.lineWidth`.
    """


    def draw2D(self, zpos, axes):
        """Draw the arrow. """

        Line.draw2D(self, zpos, axes)

        xax, yax, zax = axes

        # We draw the arrow head as a triangle at the
        # second line vertex (xy2). We generate the
        # two other vertices of the triangle by
        # rotating +/- 30 degrees around xy2.
        xy1   = np.array(self.xy1)
        xy2   = np.array(self.xy2)
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

        idxs  = np.arange(3, dtype=np.uint32)
        verts = np.zeros((3, 3), dtype=np.float32)
        verts[0, [xax, yax]] = xy2
        verts[1, [xax, yax]] = p1
        verts[2, [xax, yax]] = p2
        verts[:, zax]        = zpos

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
        gl.glDrawElements(gl.GL_TRIANGLES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


class Rect(AnnotationObject):
    """The ``Rect`` class is an :class:`AnnotationObject` which represents a
    2D rectangle.
    """


    filled = props.Boolean(default=True)
    """Whether to fill the rectangle. """


    def __init__(self,
                 annot,
                 xy,
                 w,
                 h,
                 filled=True,
                 *args,
                 **kwargs):
        """Create a :class:`Rect` annotation.

        :arg annot:  The :class:`Annotations` object that owns this
                     ``Rect``.

        :arg xy:     Tuple specifying bottom left of the rectangle, in
                     the display coordinate system.

        :arg w:      Rectangle width.

        :arg h:      Rectangle height.

        :arg filled: If ``True``, the rectangle is filled with a transparent
                     shade of :attr:`AnnotationObject.colour`.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """
        AnnotationObject.__init__(self, annot, *args, **kwargs)

        self.xy     = xy
        self.w      = w
        self.h      = h
        self.filled = filled


    def hit(self, xy):
        """Returns ``True`` if ``xy`` is within the bounds of this ``Rect``,
        ``False`` otherwise.
        """

        x,  y    = xy
        xlo, ylo = self.xy
        xhi, yhi = (xlo + self.w, ylo + self.h)

        xlo, xhi = sorted((xlo, xhi))
        ylo, yhi = sorted((ylo, yhi))

        return (x >= xlo and
                x <= xhi and
                y >= ylo and
                y <= yhi)


    def move(self, xy):
        """Move this ``Rect`` according to ``xy``."""
        self.xy = (self.xy[0] + xy[0], self.xy[1] + xy[1])


    def draw2D(self, zpos, axes):
        """Draws this ``Rectangle`` annotation. """

        if self.w == 0 or self.h == 0:
            return

        xax, yax, zax = axes
        xy            = self.xy
        w             = self.w
        h             = self.h

        bl = [xy[0],     xy[1]]
        br = [xy[0] + w, xy[1]]
        tl = [xy[0],     xy[1] + h]
        tr = [xy[0] + w, xy[1] + h]

        self.__drawRect(zpos, xax, yax, zax, bl, br, tl, tr)

        if self.filled:
            self.__drawFill(zpos, xax, yax, zax, bl, br, tl, tr)


    def __drawFill(self, zpos, xax, yax, zax, bl, br, tl, tr):
        """Draw a filled version of the rectangle. """

        if self.colour is not None: colour = list(self.colour[:3])
        else:                       colour = [1, 1, 1]

        colour = colour + [0.25 * self.alpha / 100]

        idxs  = np.array([0, 1, 2, 2, 1, 3], dtype=np.uint32)
        verts = np.zeros((4, 3),             dtype=np.float32)

        verts[0, [xax, yax]] = bl
        verts[1, [xax, yax]] = br
        verts[2, [xax, yax]] = tl
        verts[3, [xax, yax]] = tr
        verts[:,  zax]       = zpos
        verts                = verts.ravel('C')

        # I'm assuming that glPolygonMode
        # is already set to GL_FILL
        gl.glColor4f(*colour)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
        gl.glDrawElements(gl.GL_TRIANGLES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


    def __drawRect(self, zpos, xax, yax, zax, bl, br, tl, tr):
        """Draw the rectangle outline. """

        idxs  = np.array([0, 1, 2, 3, 0, 2, 1, 3], dtype=np.uint32)
        verts = np.zeros((4, 3),                   dtype=np.float32)

        verts[0, [xax, yax]] = bl
        verts[1, [xax, yax]] = br
        verts[2, [xax, yax]] = tl
        verts[3, [xax, yax]] = tr
        verts[:,  zax]       = zpos
        verts                = verts.ravel('C')

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
        gl.glDrawElements(gl.GL_LINES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


class Ellipse(AnnotationObject):
    """The ``Ellipse`` class is an :class:`AnnotationObject` which represents a
    ellipse.
    """


    filled = props.Boolean(default=True)
    """Whether to fill the ellipse. """


    def __init__(self,
                 annot,
                 xy,
                 width,
                 height,
                 npoints=60,
                 filled=True,
                 *args, **kwargs):
        """Create an ``Ellipse`` annotation.

        :arg annot:   The :class:`Annotations` object that owns this
                      ``Ellipse``.

        :arg xy:      Tuple specifying the ellipse centre, in the display
                      coordinate system.

        :arg width:   Horizontal radius.

        :arg height:  Vertical radius.

        :arg npoints: Number of vertices used to draw the ellipse outline.

        :arg filled:  If ``True``, the ellipse is filled with a
                      transparent shade of ``colour``.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """

        AnnotationObject.__init__(self, annot, *args, **kwargs)

        self.xy      = xy
        self.width   = width
        self.height  = height
        self.npoints = npoints
        self.filled  = filled


    def hit(self, xy):
        """Returns ``True`` if ``xy`` is within the bounds of this ``Ellipse``,
        ``False`` otherwise.
        """

        # https://math.stackexchange.com/a/76463
        x,  y  = xy
        h,  k  = self.xy
        rx, ry = self.width, self.height
        return ((x - h) ** 2) / (rx ** 2) + ((y - k) ** 2) / (ry ** 2) <= 1


    def move(self, xy):
        """Move this ``Rect`` according to ``xy``."""
        self.xy = (self.xy[0] + xy[0], self.xy[1] + xy[1])


    def draw2D(self, zpos, axes):
        """Draws this ``Ellipse`` annotation. """

        if (self.width == 0) or (self.height == 0):
            return

        if self.colour is not None: colour = list(self.colour[:3])
        else:                       colour = [1, 1, 1]

        colour = colour + [0.25 * self.alpha / 100]

        xax, yax, zax = axes
        x, y          = self.xy
        w             = self.width
        h             = self.height

        idxs    = np.arange(self.npoints + 1, dtype=np.uint32)
        verts   = np.zeros((self.npoints + 1, 3), dtype=np.float32)
        samples = np.linspace(0, 2 * np.pi, self.npoints)

        verts[0, [xax, yax]] = x, y
        verts[1:, xax]       = w * np.sin(samples) + x
        verts[1:, yax]       = h * np.cos(samples) + y
        verts[:,  zax]       = zpos

        # outline
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts[1:-1])
        gl.glDrawElements(
            gl.GL_LINE_LOOP, len(idxs) - 2, gl.GL_UNSIGNED_INT, idxs[:-2])

        if self.filled:
            gl.glColor4f(*colour)
            gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
            gl.glDrawElements(
                gl.GL_TRIANGLE_FAN, len(idxs), gl.GL_UNSIGNED_INT, idxs)


class VoxelGrid(AnnotationObject):
    """The ``VoxelGrid`` is an :class:`AnnotationObject` which represents a
    collection of selected voxels. See also the :class:`VoxelSelection`
    annotation.

    Each selected voxel is highlighted with a rectangle around its border.
    """


    def __init__(self,
                 annot,
                 selectMask,
                 displayToVoxMat,
                 voxToDisplayMat,
                 offsets=None,
                 *args,
                 **kwargs):
        """Create a ``VoxelGrid`` annotation.

        :arg annot:           The :class:`Annotations` object that owns this
                              ``VoxelGrid``.

        :arg selectMask:      A 3D numpy array, the same shape as the image
                              being annotated (or a sub-space of the image -
                              see the ``offsets`` argument),  which is
                              interpreted as a mask array - values which are
                              ``True`` denote selected voxels.

        :arg displayToVoxMat: A transformation matrix which transforms from
                              display space coordinates into voxel space
                              coordinates.

        :arg voxToDisplayMat: A transformation matrix which transforms from
                              voxel coordinates into display space
                              coordinates.

        :arg offsets:         If ``None`` (the default), the ``selectMask``
                              must have the same shape as the image data
                              being annotated. Alternately, you may set
                              ``offsets`` to a sequence of three values,
                              which are used as offsets for the xyz voxel
                              values. This is to allow for a sub-space of
                              the full image space to be annotated.
        """

        kwargs['xform'] = voxToDisplayMat
        AnnotationObject.__init__(self, annot, *args, **kwargs)

        if offsets is None:
            offsets = [0, 0, 0]

        self.displayToVoxMat = displayToVoxMat
        self.selectMask      = selectMask
        self.offsets         = offsets


    def draw2D(self, zpos, axes):
        """Draws this ``VoxelGrid`` annotation. """

        xax, yax, zax = axes
        dispLoc       = [0] * 3
        dispLoc[zax]  = zpos
        voxLoc        = affine.transform([dispLoc], self.displayToVoxMat)[0]

        vox = int(round(voxLoc[zax]))

        restrictions = [slice(None)] * 3
        restrictions[zax] = slice(vox - self.offsets[zax],
                                  vox - self.offsets[zax] + 1)

        xs, ys, zs = np.where(self.selectMask[restrictions])
        voxels     = np.vstack((xs, ys, zs)).T

        for ax in range(3):
            off = restrictions[ax].start
            if off is None:
                off = 0
            voxels[:, ax] += off + self.offsets[ax]

        verts, idxs = glroutines.voxelGrid(voxels, xax, yax, 1, 1)
        verts = verts.ravel('C')

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
        gl.glDrawElements(gl.GL_LINES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


class VoxelSelection(AnnotationObject):
    """A ``VoxelSelection`` is an :class:`AnnotationObject` which draws
    selected voxels from a :class:`.selection.Selection` instance.  A
    :class:`.SelectionTexture` is used to draw the selected voxels.
    """


    def __init__(self,
                 annot,
                 selection,
                 opts,
                 offsets=None,
                 *args,
                 **kwargs):
        """Create a ``VoxelSelection`` annotation.

        :arg annot:     The :class:`Annotations` object that owns this
                        ``VoxelSelection``.

        :arg selection: A :class:`.selection.Selection` instance which defines
                        the voxels to be highlighted.

        :arg opts:      A :class:`.NiftiOpts` instance which is used
                        for its voxel-to-display transformation matrices.

        :arg offsets:   If ``None`` (the default), the ``selection`` must have
                        the same shape as the image data being
                        annotated. Alternately, you may set ``offsets`` to a
                        sequence of three values, which are used as offsets
                        for the xyz voxel values. This is to allow for a
                        sub-space of the full image space to be annotated.

        All other arguments are passed through to the
        :meth:`AnnotationObject.__init__` method.
        """

        AnnotationObject.__init__(self, annot, *args, **kwargs)

        if offsets is None:
            offsets = [0, 0, 0]

        self.__selection = selection
        self.__opts      = opts
        self.__offsets   = offsets

        texName = '{}_{}'.format(type(self).__name__, id(selection))

        ndims = texdata.numTextureDims(selection.shape)

        if ndims == 2: ttype = textures.SelectionTexture2D
        else:          ttype = textures.SelectionTexture3D

        self.__texture = glresources.get(
            texName,
            ttype,
            texName,
            selection)


    def destroy(self):
        """Must be called when this ``VoxelSelection`` is no longer needed.
        Destroys the :class:`.SelectionTexture`.
        """
        glresources.delete(self.__texture.name)
        self.__texture = None
        self.__opts    = None


    @property
    def texture(self):
        """Return the :class:`.SelectionTexture` used by this
        ``VoxelSelection``.
        """
        return self.__texture


    def draw2D(self, zpos, axes):
        """Draws this ``VoxelSelection``."""

        xax, yax     = axes[:2]
        opts         = self.__opts
        texture      = self.__texture
        shape        = self.__selection.getSelection().shape
        displayToVox = opts.getTransform('display', 'voxel')
        voxToDisplay = opts.getTransform('voxel',   'display')
        voxToTex     = opts.getTransform('voxel',   'texture')
        voxToTex     = affine.concat(texture.texCoordXform(shape), voxToTex)
        verts, voxs  = glroutines.slice2D(shape,
                                          xax,
                                          yax,
                                          zpos,
                                          voxToDisplay,
                                          displayToVox)

        texs  = affine.transform(voxs, voxToTex)[:, :texture.ndim]
        verts = np.array(verts, dtype=np.float32).ravel('C')
        texs  = np.array(texs,  dtype=np.float32).ravel('C')

        texture.bindTexture(gl.GL_TEXTURE0)
        gl.glClientActiveTexture(gl.GL_TEXTURE0)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE)

        with glroutines.enabled((texture.target,
                                 gl.GL_TEXTURE_COORD_ARRAY,
                                 gl.GL_VERTEX_ARRAY)):
            gl.glVertexPointer(  3,            gl.GL_FLOAT, 0, verts)
            gl.glTexCoordPointer(texture.ndim, gl.GL_FLOAT, 0, texs)
            gl.glDrawArrays(     gl.GL_TRIANGLES, 0, 6)

        texture.unbindTexture()


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
    """Text font size."""


    def __init__(self,
                 annot,
                 text=None,
                 pos=None,
                 off=None,
                 coordinates='proportions',
                 fontSize=10,
                 halign=None,
                 valign=None,
                 colour=None,
                 bgColour=None,
                 angle=None,
                 **kwargs):
        """Create a ``TextAnnotation``.

        :arg annot:      The :class:`Annotations` object that owns this
                         ``TextAnnotation``.

        See the :class:`.Text` class for details on the other arguments.
        """
        AnnotationObject.__init__(self, annot, **kwargs)

        self.text        = text
        self.pos         = pos
        self.off         = off
        self.coordinates = coordinates
        self.fontSize    = fontSize
        self.halign      = halign
        self.valign      = valign
        self.colour      = colour
        self.bgColour    = bgColour
        self.angle       = angle
        self.__initscale = None
        self.__text      = gltext.Text()


    @property
    def gltext(self):
        return self.__text


    def destroy(self):
        """Must be called when this ``TextAnnotation`` is no longer needed.
        """
        AnnotationObject.destroy(self)
        self.__text.destroy()
        self.__text = None


    def draw2D(self, zpos, axes):
        """Draw this ``TextAnnotation``. """

        text             = self.__text
        canvas           = self.annot.canvas
        opts             = canvas.opts
        text.text        = self.text
        text.pos         = self.pos
        text.off         = self.off
        text.coordinates = self.coordinates
        text.fontSize    = self.fontSize
        text.halign      = self.halign
        text.valign      = self.valign
        text.colour      = self.colour
        text.bgColour    = self.bgColour
        text.angle       = self.angle

        if self.coordinates == 'display':
            if self.__initscale is None:
                self.__initscale = canvas.zoomToScale(opts.zoom)
            scale = canvas.zoomToScale(opts.zoom)

            pos           = [0] * 3
            pos[opts.xax] = self.pos[0]
            pos[opts.yax] = self.pos[1]
            pos[opts.zax] = opts.pos[2]

            text.pos         = canvas.worldToCanvas(pos)
            text.scale       = self.__initscale / scale
            text.coordinates = 'pixels'
        else:
            text.pos         = self.pos
            text.coordinates = self.coordinates

        text.draw(*canvas.GetSize())


    def hit(self, xy):
        """Returns ``True`` if ``xy`` is within the bounds of this
        ``TextAnnotation``, ``False`` otherwise. Only supported for text
        drawn relative to the display coordinate system
        (``coordinates='display'``) - raises a ``NotImplementedError``
        otherwise.
        """

        if self.coordinates != 'display':
            raise NotImplementedError()

        canvas     = self.annot.canvas
        opts       = canvas.opts
        x,    y    = xy
        xlo,  ylo  = self.__text.pos
        xlen, ylen = self.__text.size

        # the Text object works in pixels,
        # but here we're working in display
        # coords
        xy1 = canvas.canvasToWorld(xlo,        ylo)
        xy2 = canvas.canvasToWorld(xlo + xlen, ylo + ylen)

        xlo, xhi = sorted((xy1[opts.xax], xy2[opts.xax]))
        ylo, yhi = sorted((xy1[opts.yax], xy2[opts.yax]))

        return (x >= xlo and
                x <= xhi and
                y >= ylo and
                y <= yhi)


    def move(self, xy):
        """Move this ``TextAnnotation`` according to ``xy``.

        Only supported for text drawn relative to the display coordinate
        system (``coordinates='display'``) - raises a ``NotImplementedError``
        otherwise.
        """
        if self.coordinates != 'display':
            raise NotImplementedError()

        self.pos = (self.pos[0] + xy[0], self.pos[1] + xy[1])
