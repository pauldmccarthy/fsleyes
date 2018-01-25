#!/usr/bin/env python
#
# glimageobject.py - The GLImageObject class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLImageObject` class, a sub-class of
:class:`.GLObject`, and the base class for all OpenGL objects which display
data from :class:`.Nifti` overlays.
"""


import numpy     as np
import OpenGL.GL as gl

import fsl.utils.transform                 as transform
import fsl.utils.memoize                   as memoize

import fsleyes.displaycontext.volume3dopts as volume3dopts
import fsleyes.colourmaps                  as fslcmaps
import fsleyes.gl.globject                 as globject
import fsleyes.gl.routines                 as glroutines


class GLImageObject(globject.GLObject):
    """The ``GLImageObject`` class is the base class for all GL representations
    of :class:`.Nifti` instances. It contains some convenience methods for
    drawing volumetric image data.

    Some useful methods for 2D rendering::

      .. autsummary::
         :nosignatures:

         frontFace
         generateVertices2D
         generateVoxelCoordinates2D

    Some useful methods for 3D rendering::

      .. autsummary::
         :nosignatures:

         generateVertices3D
         generateVoxelCoordinates3D
         get3DClipPlane
         clipPlaneVertices
         drawClipPlanes
    """


    def __init__(self, overlay, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLImageObject``.

        :arg image:       A :class:`.Nifti` object.

        :arg overlayList: The :class`.OverlayList`.

        :arg displayCtx:  The :class:`.DisplayContext` object managing the
                          scene.

        :arg canvas:      The canvas doing the drawing.

        :arg threedee:    Set up for 2D or 3D rendering.
        """

        globject.GLObject.__init__(
            self, overlay, overlayList, displayCtx, canvas, threedee)

        self.__name = 'GLImageObject_{}'.format(self.name)

        name = self.__name
        opts = self.opts

        # In 3D mode, when Volume3DOpts.showClipPlanes
        # is on, we create a unique random colour for
        # each displayed clipping plane.
        self.__clipPlaneColours = {}

        # If this is being shown in 3D,
        # we add some listeners. Some
        # geometry methods are memoized,
        # and we need to invalidate the
        # memoize cache when certain
        # display properties change.
        if self.threedee and isinstance(opts, volume3dopts.Volume3DOpts):

            kwargs = {'callback' : self.__boundsChanged, 'immediate' : True}

            # Invalidate vertices on bounds change
            opts.addListener('bounds',       name, **kwargs)
            opts.addListener('transform',    name, **kwargs)
            opts.addListener('displayXform', name, **kwargs)

            # Invalidate 3Dclipping on any clip chagnes
            kwargs['callback'] = self.__clip3DChanged
            opts.addListener('clipPosition',    name, **kwargs)
            opts.addListener('clipAzimuth',     name, **kwargs)
            opts.addListener('clipInclination', name, **kwargs)


    @property
    def image(self):
        """The :class:`.Nifti` being rendered by this ``GLImageObject``. This
        is equivalent to :meth:`.GLObject.overlay`.
        """
        return self.overlay


    def destroy(self):
        """Must be called when this ``GLImageObject`` is no longer needed.
        Removes some property listeners.
        """

        name = self.__name
        opts = self.opts

        opts.removeListener('bounds',          name)
        opts.removeListener('transform',       name)
        opts.removeListener('displayXform',    name)

        if self.threedee and isinstance(opts, volume3dopts.Volume3DOpts):
            opts.removeListener('clipPosition',    name)
            opts.removeListener('clipAzimuth',     name)
            opts.removeListener('clipInclination', name)

        globject.GLObject.destroy(self)


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


    def frontFace(self):
        """Convenience method for 2D rendering.

        Image slices are generally drawn onto a 2D plane which is parallel to
        the viewing plane (see the :class:`.GLVolume` class). If the canvas
        that is drawing this ``GLImageObject`` has adjusted the projection
        matrix (e.g. via the :attr:`.SliceCanvas.invertX` or
        :attr:`.SliceCanvas.invertY` properties), the front or back face of
        this plane may be facing the viewing plane.

        So if face-culling is desired, this method returns the face that
        is facing away from the viewing plane, i.e. the face that can safely
        be culled.

        .. note:: This will raise an error if called on a ``GLImageObject``
                  which is being drawn by anything other than a
                  :class:`.SliceCanvas` or :class:`.LightBoxCanvas`.
        """

        front = gl.GL_CCW
        back  = gl.GL_CW

        numInverts = 0

        copts = self.canvas.opts

        # No flips if rendering
        # to an offscreen texture
        if copts.renderMode != 'onscreen':
            return front

        if copts.invertX: numInverts += 1
        if copts.invertY: numInverts += 1

        if numInverts == 1:
            front, back = back, front

        return front


    def generateVertices2D(self, zpos, axes, bbox=None):
        """Generates vertex coordinates for a 2D slice of the :class:`.Image`,
        through the given ``zpos``, with the optional ``bbox`` applied to the
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

        opts          = self.opts
        v2dMat        = opts.getTransform('voxel',   'display')
        d2vMat        = opts.getTransform('display', 'voxel')
        v2tMat        = opts.getTransform('voxel',   'texture')
        xax, yax, zax = axes

        vertices, voxCoords = glroutines.slice2D(
            self.image.shape[:3],
            xax,
            yax,
            zpos,
            v2dMat,
            d2vMat,
            bbox=bbox)

        # If not interpolating, centre the
        # voxel coordinates on the Z/depth
        # axis. We do this to avoid rounding
        # bias when the display Z position is
        # on a voxel boundary.
        if not hasattr(opts, 'interpolation') or opts.interpolation == 'none':
            voxCoords = opts.roundVoxels(voxCoords, daxes=[zax])

        texCoords = transform.transform(voxCoords, v2tMat)

        return vertices, voxCoords, texCoords


    @memoize.Instanceify(memoize.memoize)
    def generateVertices3D(self, bbox=None):
        """Generates vertex coordinates defining the 3D bounding box of the
        :class:`.Image`, with the optional ``bbox`` applied to the
        coordinates. See the :func:`.routines.boundingBox` function.

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

        texCoords = transform.transform(voxCoords, v2tMat)

        return vertices, voxCoords, texCoords


    def generateVoxelCoordinates2D(
            self,
            zpos,
            axes,
            bbox=None,
            space='voxel'):
        """Generates a 2D grid of voxel coordinates along the
        XY display coordinate system plane, at the given ``zpos``.

        :arg zpos:  Position along the display coordinate system Z axis.

        :arg axes:  Axis indices.

        :arg bbox:  Limiting bounding box.

        :arg space: Either ``'voxel'`` (the default) or ``'display'``.
                    If the latter, the returned coordinates are in terms
                    of the display coordinate system. Otherwise, the
                    returned coordinates are integer voxel coordinates.

        :returns: A ``numpy.float32`` array of shape ``(N, 3)``, containing
                  the coordinates for ``N`` voxels.

        See the :func:`.pointGrid` function.
        """

        if space not in ('voxel', 'display'):
            raise ValueError('Unknown value for space ("{}")'.format(space))

        image         = self.image
        opts          = self.opts
        v2dMat        = opts.getTransform('voxel',   'display')
        d2vMat        = opts.getTransform('display', 'voxel')
        xax, yax, zax = axes

        # TODO If space == voxel, you should call
        #      pointGrid to generate voxels, and
        #      avoid the subsequent transform back
        #      from display to voxel space.

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
            xax,
            yax,
            bbox=bbox)[0]

        voxels[:, zax] = zpos

        if space == 'voxel':
            voxels = transform.transform(voxels, d2vMat)
            voxels = opts.roundVoxels(voxels,
                                      daxes=[zax],
                                      roundOther=False)

        return voxels


    def generateVoxelCoordinates3D(self, bbox, space='voxel'):
        """


        See the :func:`.pointGrid3D` function.

        note: Not implemented properly yet.
        """

        if space not in ('voxel', 'display'):
            raise ValueError('Unknown value for space ("{}")'.format(space))

        # TODO

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


    @memoize.Instanceify(memoize.memoize)
    def get3DClipPlane(self, *args, **kwargs):
        """Memoized wrapper around the :meth:`.Volume3DOpts.get3DClipPlane`
        method.
        """
        return self.opts.get3DClipPlane(*args, **kwargs)


    @memoize.Instanceify(memoize.memoize)
    def clipPlaneVertices(self, planeIdx, bbox=None):
        """A convenience method for use with overlays being displayed
        in terms of a :class:`.Volume3DOpts` instance.

        Generates vertices for the clipping plane specified by ``planeIdx``
        (an index into the ``Volume3DOpts.clip*`` lists).

        Returns a ``(N, 3)`` ``numpy`` array containing the vertices, and
        a 1D ``numpy`` array containing vertex indices.

        See the :meth:`get3DClipPlane` and :meth:`drawClipPlanes` methods.

        .. note:: This method depends on the ``trimesh`` library - if it is
                  not present, two empty arrays are returned.
        """

        origin, normal = self.get3DClipPlane(planeIdx)
        vertices       = self.generateVertices3D(bbox=bbox)[0]
        indices        = np.arange(vertices.shape[0]).reshape(-1, 3)

        try:
            import trimesh
            import trimesh.intersections as tmint
        except ImportError:
            return np.zeros((0, 3)), np.zeros((0,))

        # Calculate the intersection of the clip
        # plane with the image bounding box
        lines = tmint.mesh_plane(
            trimesh.Trimesh(vertices, indices),
            plane_normal=normal,
            plane_origin=origin)

        # I'm assuming that the
        # returned lines are sorted
        vertices = np.array(lines.reshape(-1, 3), dtype=np.float32)

        if vertices.shape[0] < 3:
            return np.zeros((0, 3)), np.zeros((0,))

        indices = glroutines.polygonIndices(vertices.shape[0])

        return vertices, indices


    def drawClipPlanes(self, xform=None, bbox=None):
        """A convenience method for use with overlays being displayed
        in terms of a :class:`.Volume3DOpts` instance.

        Draws the active clipping planes, as specified by the
        :class:`.Volume3DOpts` clipping properties.

        :arg xform: A transformation matrix to apply to the clip plane
                    vertices before drawing them.

        :arg bbox:  A bounding box by which the clip planes can be limited
                    (not currently honoured).
        """

        if not self.opts.showClipPlanes:
            return

        for i in range(self.opts.numClipPlanes):

            verts, idxs = self.clipPlaneVertices(i, bbox)

            if len(idxs) == 0:
                continue

            if xform is not None:
                verts = transform.transform(verts, xform)

            verts = np.array(verts.ravel('C'), dtype=np.float32, copy=False)

            # A consistent colour for
            # each clipping plane
            rgb = self.__clipPlaneColours.get(i, None)
            if rgb is None:
                rgb = fslcmaps.randomBrightColour()[:3]
                self.__clipPlaneColours[i] = rgb

            r, g, b = rgb

            with glroutines.enabled(gl.GL_VERTEX_ARRAY):

                gl.glColor4f(r, g, b, 0.3)
                gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)
                gl.glDrawElements(gl.GL_TRIANGLES,
                                  len(idxs),
                                  gl.GL_UNSIGNED_INT,
                                  idxs)


    def __boundsChanged(self, *a):
        """Called when any change to the overlay bounds change.

        Some of the methods on this class use the
        :func:`fsl.utils.memoize.memoize` decorator to cache previously
        calculated values. When certain :class:`.DisplayOpts` properties
        change, these cached values need to be invalidated. This method
        does that.
        """

        self.generateVertices3D.invalidate()
        self.__clip3DChanged()


    def __clip3DChanged(self, *a):
        """Called when any change to the 3D clipping properties change.

        See the :meth:`__boundsChanged` method.
        """
        self.get3DClipPlane   .invalidate()
        self.clipPlaneVertices.invalidate()
