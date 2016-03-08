#!/usr/bin/env python
#
# annotations.py - 2D annotations on a SliceCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com> 
#
"""This module provides the :class:`Annotations` class, which implements
functionality to draw 2D OpenGL annotations on a canvas


The :class:`Annotations` class is used by the :class:`.SliceCanvas` and
:class:`.LightBoxCanvas` classes, and users of those class, to annotate the
canvas.


All annotations derive from the :class:`AnnotationObject` base class. The
following annotation types are defined:

.. autosummary::
   :nosignatures:

   Line
   Rect
   VoxelGrid
   VoxelSelection
"""


import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.fsleyes.gl.globject  as globject
import fsl.fsleyes.gl.routines  as glroutines
import fsl.fsleyes.gl.resources as glresources
import fsl.fsleyes.gl.textures  as textures
import fsl.utils.transform      as transform


log = logging.getLogger(__name__)


class Annotations(object):
    """An :class:`Annotations` object provides functionality to draw 2D
    annotations on a :class:`.SliceCanvas`. Annotations may be enqueued via
    any of the :meth:`line`, :meth:`rect`, :meth:`grid`, :meth:`selection` or
    :meth:`obj`, methods.

    
    A call to :meth:`draw` will then draw each of the queued annotations on
    the canvas, and clear the queue.

    
    If an annotation is to be persisted, it can be enqueued, as above, but
    passing ``hold=True`` to the queueing method.  The annotation will then
    remain in the queue until it is removed via :meth:`dequeue`, or the
    entire annotations queue is cleared via :meth:`clear`.

    
    Annotations can be queued by one of the helper methods on the
    :class:`Annotations` object (e.g. :meth:`line` or :meth:`rect`), or by
    manually creating an :class:`AnnotationObject` and passing it to the
    :meth:`obj` method.
    """

    
    def __init__(self, xax, yax):
        """Creates an :class:`Annotations` object.

        :arg xax: Index of the display coordinate system axis that corresponds
                  to the horizontal screen axis.
        
        :arg yax: Index of the display coordinate system axis that corresponds
                  to the horizontal screen axis.
        """
        
        self.__q     = []
        self.__holdq = []
        self.__xax   = xax
        self.__yax   = yax

        
    def setAxes(self, xax, yax):
        """This method must be called if the display orientation changes.  See
        :meth:`__init__`.
        """
        
        self.__xax = xax
        self.__yax = yax
        
        for obj in self.__q:     obj.setAxes(xax, yax)
        for obj in self.__holdq: obj.setAxes(xax, yax)

        
    def line(self, *args, **kwargs):
        """Queues a line for drawing - see the :class:`Line` class. """
        hold = kwargs.pop('hold', False)
        obj  = Line(self.__xax, self.__yax, *args, **kwargs)
        
        return self.obj(obj, hold)

        
    def rect(self, *args, **kwargs):
        """Queues a rectangle for drawing - see the :class:`Rectangle` class.
        """
        hold = kwargs.pop('hold', False)
        obj  = Rect(self.__xax, self.__yax, *args, **kwargs)
        
        return self.obj(obj, hold)


    def grid(self, *args, **kwargs):
        """Queues a voxel grid for drawing - see the :class:`VoxelGrid` class.
        """ 
        hold = kwargs.pop('hold', False)
        obj  = VoxelGrid(self.__xax, self.__yax, *args, **kwargs)
        
        return self.obj(obj, hold)

    
    def selection(self, *args, **kwargs):
        """Queues a selection for drawing - see the :class:`VoxelSelection`
        class.
        """ 
        hold = kwargs.pop('hold', False)
        obj  = VoxelSelection(self.__xax, self.__yax, *args, **kwargs)
        
        return self.obj(obj, hold) 
    
        
    def obj(self, obj, hold=False):
        """Queues the given :class:`AnnotationObject` for drawing.

        :arg hold: If ``True``, the given ``AnnotationObject`` will be kept in
                   the queue until it is explicitly removed. Otherwise (the
                   default), the object will be removed from the queue after
                   it has been drawn.
        """
        
        if hold: self.__holdq.append(obj)
        else:    self.__q    .append(obj)

        obj.setAxes(self.__xax, self.__yax)

        return obj


    def dequeue(self, obj, hold=False):
        """Removes the given :class:`AnnotationObject` from the queue, but
        does not call its :meth:`.GLObject.destroy` method - this is the
        responsibility of the caller.
        """

        if hold:
            try:    self.__holdq.remove(obj)
            except: pass
        else:
            try:    self.__q.remove(obj)
            except: pass


    def clear(self):
        """Clears both the normal queue and the persistent (a.k.a. ``hold``)
        queue, and calls the :meth:`.GLObject.destroy` method on every object
        in the queue.
        """

        for obj in self.__q:     obj.destroy()
        for obj in self.__holdq: obj.destroy()
        
        self.__q     = []
        self.__holdq = []
        

    def draw(self, zpos, xform=None, skipHold=False):
        """Draws all enqueued annotations.

        :arg zpos:     Position along the Z axis, above which all annotations
                       should be drawn.

        :arg xform:    Transformation matrix which should be applied to all
                       objects.

        :arg skipHold: Do not draw items on the hold queue - only draw one-off
                       items.
        """

        if not skipHold: objs = self.__holdq + self.__q
        else:            objs = self.__q

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glMultMatrixf(xform.ravel('C')) 

        for obj in objs:
            
            obj.setAxes(self.__xax, self.__yax)

            if obj.xform is not None:
                gl.glMatrixMode(gl.GL_MODELVIEW)
                gl.glPushMatrix()
                gl.glMultMatrixf(obj.xform.ravel('C'))

            if obj.colour is not None:
                
                if len(obj.colour) == 3: colour = list(obj.colour) + [1.0]
                else:                    colour = list(obj.colour)
                gl.glColor4f(*colour)

            if obj.width is not None:
                gl.glLineWidth(obj.width) 

            try:
                obj.preDraw()
                obj.draw(zpos)
                obj.postDraw()
            except Exception as e:
                log.warn('{}'.format(e), exc_info=True)

            if obj.xform is not None:
                gl.glPopMatrix() 

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPopMatrix()

        # Clear the regular queue after each draw
        self.__q = []


class AnnotationObject(globject.GLSimpleObject):
    """Base class for all annotation objects. An ``AnnotationObject`` is drawn
    by an :class:`Annotations` instance. The ``AnnotationObject`` contains some
    attributes which are common to all annotation types:

    ========== =============================================================
    ``colour`` Annotation colour
    ``width``  Annotation line width (if the annotation is made up of lines)
    ``xform``  Custom transformation matrix to apply to annotation vertices.
    ========== =============================================================

    Subclasses must, at the very least, override the
    :meth:`globject.GLObject.draw` method.
    """
    
    def __init__(self, xax, yax, xform=None, colour=None, width=None):
        """Create an ``AnnotationObject``.

        :arg xax:    Initial display X axis

        :arg yax:    Initial display Y axis        

        :arg xform:  Transformation matrix which will be applied to all
                     vertex coordinates.
        
        :arg colour: RGB/RGBA tuple specifying the annotation colour.
        
        :arg width:  Line width to use for the annotation.
        """
        globject.GLSimpleObject.__init__(self, xax, yax)
        
        self.colour = colour
        self.width  = width
        self.xform  = xform

        if self.xform is not None:
            self.xform = np.array(self.xform, dtype=np.float32)

            
    def preDraw(self):
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        
    def postDraw(self):
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY) 

        
class Line(AnnotationObject):
    """The ``Line`` class is an :class:`AnnotationObject` which represents a
    2D line.
    """

    def __init__(self, xax, yax, xy1, xy2, *args, **kwargs):
        """Create a ``Line`` annotation.

        The ``xy1`` and ``xy2`` coordinate tuples should be in relation to the
        axes which map to the horizontal/vertical screen axes on the target
        canvas.

        :arg xax: Initial display X axis

        :arg yax: Initial display Y axis        

        :arg xy1: Tuple containing the (x, y) coordinates of one endpoint.
        
        :arg xy2: Tuple containing the (x, y) coordinates of the second
                  endpoint.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.
        """
        AnnotationObject.__init__(self, xax, yax, *args, **kwargs)
        self.xy1 = xy1
        self.xy2 = xy2


    def draw(self, zpos):
        """Draws this ``Line`` annotation. """
        xax = self.xax
        yax = self.yax
        zax = self.zax

        idxs                 = np.arange(2,     dtype=np.uint32) 
        verts                = np.zeros((2, 3), dtype=np.float32)
        verts[0, [xax, yax]] = self.xy1
        verts[1, [xax, yax]] = self.xy2
        verts[:, zax]        = zpos

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts.ravel('C')) 
        gl.glDrawElements(gl.GL_LINES, len(idxs), gl.GL_UNSIGNED_INT, idxs) 

        
class Rect(AnnotationObject):
    """The ``Rect`` class is an :class:`AnnotationObject` which represents a
    2D rectangle.
    """

    def __init__(self, xax, yax, xy, w, h, *args, **kwargs):
        """Create a :class:`Rect` annotation.

        :arg xax: Initial display X axis

        :arg yax: Initial display Y axis        

        :arg xy:  Tuple specifying bottom left of the rectangle, in the display
                  coordinate system.
        :arg w:   Rectangle width.
        :arg h:   Rectangle height.

        All other arguments are passed through to
        :meth:`AnnotationObject.__init__`.        
        """
        AnnotationObject.__init__(self, xax, yax, *args, **kwargs)
        self.xy = xy
        self.w  = w
        self.h  = h

        
    def draw(self, zpos):
        """Draws this ``Rectangle`` annotation. """
        
        if self.w == 0 or self.h == 0:
            return

        xax = self.xax
        yax = self.yax
        zax = self.zax
        xy  = self.xy
        w   = self.w
        h   = self.h

        bl = [xy[0],     xy[1]]
        br = [xy[0] + w, xy[1]]
        tl = [xy[0],     xy[1] + h]
        tr = [xy[0] + w, xy[1] + h]

        idxs                 = np.arange(8,     dtype=np.uint32)
        verts                = np.zeros((8, 3), dtype=np.float32)
        verts[0, [xax, yax]] = bl
        verts[1, [xax, yax]] = br
        verts[2, [xax, yax]] = tl
        verts[3, [xax, yax]] = tr
        verts[4, [xax, yax]] = bl
        verts[5, [xax, yax]] = tl
        verts[6, [xax, yax]] = br
        verts[7, [xax, yax]] = tr
        verts[:,  zax]       = zpos

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts.ravel('C')) 
        gl.glDrawElements(gl.GL_LINES, len(idxs), gl.GL_UNSIGNED_INT, idxs) 


class VoxelGrid(AnnotationObject):
    """The ``VoxelGrid`` is an :class:`AnnotationObject` which represents a
    collection of selected voxels. See also the :class:`VoxelSelection`
    annotation.

    Each selected voxel is highlighted with a rectangle around its border.
    """

    
    def __init__(self,
                 xax,
                 yax,
                 selectMask,
                 displayToVoxMat,
                 voxToDisplayMat,
                 offsets=None,
                 *args,
                 **kwargs):
        """Create a ``VoxelGrid`` annotation.

        :arg xax:             Initial display X axis

        :arg yax:             Initial display Y axis        

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
        AnnotationObject.__init__(self, xax, yax, *args, **kwargs)
        
        if offsets is None:
            offsets = [0, 0, 0]

        self.displayToVoxMat = displayToVoxMat
        self.selectMask      = selectMask
        self.offsets         = offsets


    def draw(self, zpos):
        """Draws this ``VoxelGrid`` annotation. """

        xax = self.xax
        yax = self.yax
        zax = self.zax

        dispLoc = [0] * 3
        dispLoc[zax] = zpos
        voxLoc = transform.transform([dispLoc], self.displayToVoxMat)[0]

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

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts.ravel('C')) 
        gl.glDrawElements(gl.GL_LINES, len(idxs), gl.GL_UNSIGNED_INT, idxs)


class VoxelSelection(AnnotationObject):
    """A ``VoxelSelection`` is an :class:`AnnotationObject` which draws
    selected voxels from a :class:`.Selection` instance.  A
    :class:`.SelectionTexture` is used to draw the selected voxels.
    """

    
    def __init__(self,
                 xax,
                 yax,
                 selection,
                 displayToVoxMat,
                 voxToDisplayMat,
                 offsets=None,
                 *args,
                 **kwargs):
        """Create a ``VoxelSelection`` annotation.

        :arg xax:             Initial display X axis

        :arg yax:             Initial display Y axis        

        :arg selection:       A :class:`.Selection` instance which defines
                              the voxels to be highlighted.
        
        :arg displayToVoxMat: A transformation matrix which transforms from
                              display space coordinates into voxel space
                              coordinates.

        :arg voxToDisplayMat: A transformation matrix which transforms from
                              voxel coordinates into display space
                              coordinates.

        :arg offsets:         If ``None`` (the default), the ``selection``
                              must have the same shape as the image data
                              being annotated. Alternately, you may set
                              ``offsets`` to a sequence of three values,
                              which are used as offsets for the xyz voxel
                              values. This is to allow for a sub-space of
                              the full image space to be annotated.

        All other arguments are passed through to the
        :meth:`AnnotationObject.__init__` method.
        """
        
        AnnotationObject.__init__(self, xax, yax, *args, **kwargs)

        if offsets is None:
            offsets = [0, 0, 0]

        self.selection       = selection
        self.displayToVoxMat = displayToVoxMat
        self.voxToDisplayMat = voxToDisplayMat
        self.offsets         = offsets

        texName = '{}_{}'.format(type(self).__name__, id(selection))
        
        self.texture = glresources.get(
            texName,
            textures.SelectionTexture,
            texName,
            selection)

        
    def destroy(self):
        """Must be called when this ``VoxelSelection`` is no longer needed.
        Destroys the :class:`.SelectionTexture`.
        """
        glresources.delete(self.texture.getTextureName())
        self.texture = None


    def draw(self, zpos):
        """Draws this ``VoxelSelection``."""

        xax   = self.xax
        yax   = self.yax
        shape = self.selection.selection.shape

        verts, _, texs = glroutines.slice2D(shape,
                                            xax,
                                            yax,
                                            zpos,
                                            self.voxToDisplayMat,
                                            self.displayToVoxMat)

        verts = np.array(verts, dtype=np.float32).ravel('C')
        texs  = np.array(texs,  dtype=np.float32).ravel('C')

        self.texture.bindTexture(gl.GL_TEXTURE0)
        
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE)
        
        gl.glEnable(gl.GL_TEXTURE_3D)        
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

        gl.glVertexPointer(  3, gl.GL_FLOAT, 0, verts)
        gl.glTexCoordPointer(3, gl.GL_FLOAT, 0, texs)
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)

        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glDisable(gl.GL_TEXTURE_3D)

        self.texture.unbindTexture()
