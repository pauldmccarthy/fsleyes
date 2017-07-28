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
import fsleyes.gl.trimesh                  as trimesh


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
         calculateRayCastSettings
         get3DClipPlane
         clipPlaneVertices
         drawClipPlanes
    """


    def __init__(self, overlay, displayCtx, canvas, threedee):
        """Create a ``GLImageObject``.

        :arg image:       A :class:`.Nifti` object.

        :arg displayCtx:  The :class:`.DisplayContext` object managing the
                          scene.

        :arg canvas:      The canvas doing the drawing.

        :arg threedee:    Set up for 2D or 3D rendering.
        """

        globject.GLObject.__init__(self, overlay, displayCtx, canvas, threedee)

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
            opts.addListener('customXform',  name, **kwargs)
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
        opts.removeListener('customXform',     name)
        opts.removeListener('displayXform',    name)
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
        if self.canvas.invertX: numInverts += 1
        if self.canvas.invertY: numInverts += 1

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


    def calculateRayCastSettings(self):
        """Calculates various parameters required for 3D ray-cast rendering
        (see the :class:`.GLVolume` class). Returns a tuple containing:

          - A vector defining the amount by which to move along a ray in a
            single iteration of the ray-casting algorithm. This can be added
            directly to the volume texture coordinates.

          - A vector defining the maximum distance by which to randomly adjust
            the start location of each ray, to induce a dithering effect in
            the rendered scene.

          - A transformation matrix which transforms from image texture
            coordinates into the display coordinate system.

        .. note:: This method will raise an error if called on a
                  ``GLImageObject`` which is managing an overlay that is not
                  associated with a :class:`.Volume3DOpts` instance. It will
                  also raise an error if called on a ``GLImageObject`` that is
                  not being drawn by a :class:`.Scene3DCanvas`.
        """

        # In GL, the camera position
        # is initially pointing in
        # the -z direction.
        opts   = self.opts
        eye    = [0, 0, -1]
        target = [0, 0,  1]

        # We take this initial camera
        # configuration, and transform
        # it by the inverse modelview
        # matrix
        mvmat  = self.canvas.getViewMatrix()
        t2dmat = opts.getTransform('texture', 'display')
        xform  = transform.concat(mvmat, t2dmat)
        ixform = transform.invert(xform)

        eye    = transform.transform(eye,    ixform, vector=True)
        target = transform.transform(target, ixform, vector=True)

        # Direction that the 'camera' is
        # pointing, normalied to unit length
        cdir = transform.normalise(eye - target)

        # Calculate the length of one step
        # along the camera direction in a
        # single iteration of the ray-cast
        # loop.
        rayStep = cdir / opts.numSteps

        # Maximum amount by which to dither
        # the scene. This is done by applying
        # a random offset to the starting
        # point of each ray - we pass the
        # shader a vector in the camera direction,
        # so all it needs to do is scale the
        # vector by a random amount, and add the
        # vector to the starting point.
        ditherDir = cdir * opts.dithering

        # A transformation matrix which can
        # transform image texture coordinates
        # into the corresponding screen
        # (normalised device) coordinates.
        # This allows the fragment shader to
        # convert an image texture coordinate
        # into a relative depth value.
        proj  = gl.glGetFloat(gl.GL_PROJECTION_MATRIX).T

        # Adjust the projection so that the final depth
        # value will map the display bounds to -1, +1
        zscale  = 20000.0 / self.displayCtx.bounds.zlen
        zscale  = transform.scaleOffsetXform([1, 1, zscale], 0)
        xform   = transform.concat(zscale, proj, xform)

        return rayStep, ditherDir, xform


    @memoize.Instanceify(memoize.memoize)
    def get3DClipPlane(self, planeIdx):
        """A convenience method for use with overlays being displayed
        in terms of a :class:`.Volume3DOpts` instance.

        This method calculates a point-vector description of the specified
        clipping plane. ``planeIdx`` is an index into the
        :attr:`.Volume3DOpts.clipPosition`, :attr:`.Volume3DOpts.clipAzimuth`,
        and :attr:`.Volume3DOpts.clipInclination`, properties.

        Returns the clip plane at the given ``planeIdx`` as an origin and
        normal vector, in the display coordinate system..
        """

        opts    = self.opts
        pos     = opts.clipPosition[   planeIdx]
        azimuth = opts.clipAzimuth[    planeIdx]
        incline = opts.clipInclination[planeIdx]

        b       = opts.bounds
        pos     = pos             / 100.0
        azimuth = azimuth * np.pi / 180.0
        incline = incline * np.pi / 180.0

        xmid = b.xlo + 0.5 * b.xlen
        ymid = b.ylo + 0.5 * b.ylen
        zmid = b.zlo + 0.5 * b.zlen

        centre = [xmid, ymid, zmid]
        normal = [0, 0, -1]

        rot1     = transform.axisAnglesToRotMat(incline, 0, 0)
        rot2     = transform.axisAnglesToRotMat(0, 0, azimuth)
        rotation = transform.concat(rot2, rot1)

        normal = transform.transformNormal(normal, rotation)
        normal = transform.normalise(normal)

        offset = (pos - 0.5) * max((b.xlen, b.ylen, b.zlen))
        origin = centre + normal * offset

        return origin, normal


    @memoize.Instanceify(memoize.memoize)
    def clipPlaneVertices(self, planeIdx, bbox=None):
        """A convenience method for use with overlays being displayed
        in terms of a :class:`.Volume3DOpts` instance.

        Generates vertices for the clipping plane specified by ``planeIdx``
        (an index into the ``Volume3DOpts.clip*`` lists).

        Returns a ``(N, 3)`` ``numpy`` array containing thevertices, and
        a 1D ``numpy`` array containing vertex indices.

        See the :meth:`get3DClipPlane` and :meth:`drawClipPlanes` methods.
        """

        origin, normal = self.get3DClipPlane(planeIdx)
        vertices       = self.generateVertices3D(bbox=bbox)[0]
        indices        = np.arange(vertices.shape[0]).reshape(-1, 3)

        # Calculate the intersection of the clip
        # plane with the image bounding box
        lines = trimesh.mesh_plane(
            vertices,
            indices,
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

            if xform is not None:
                verts = transform.transform(verts, xform)

            if len(idxs) == 0:
                continue

            # A consistent colour for
            # each clipping plane
            rgb = self.__clipPlaneColours.get(i, None)
            if rgb is None:
                rgb = fslcmaps.randomBrightColour()[:3]
                self.__clipPlaneColours[i] = rgb

            r, g, b = rgb

            with glroutines.enabled(gl.GL_VERTEX_ARRAY):

                gl.glColor4f(r, g, b, 0.3)
                gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts.ravel('C'))
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
