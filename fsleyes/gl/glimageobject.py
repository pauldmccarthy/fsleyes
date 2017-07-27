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

import fsl.utils.transform as transform

import fsleyes.gl.globject as globject
import fsleyes.gl.routines as glroutines


class GLImageObject(globject.GLObject):
    """The ``GLImageObject`` class is the base class for all GL representations
    of :class:`.Nifti` instances. It contains some convenience methods for
    drawing volumetric image data.
    """


    def __init__(self, overlay, displayCtx, canvas, threedee):
        """Create a ``GLImageObject`` """

        globject.GLObject.__init__(self, overlay, displayCtx, canvas, threedee)


    @property
    def image(self):
        """The :class:`.Nifti` being rendered by this ``GLImageObject``. This
        is equivalent to :meth:`.GLObject.overlay`.
        """
        return self.overlay


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
        """Convenience method for 2D rendering. Images are drawn onto a 2D
        plane which is parallel to the viewing plane. If the canvas that is
        drawing this ``GLImageObject`` has adjusted the projection matrix
        (e.g. via the :attr:`.SliceCanvas.invertX` or
        :attr:`.SliceCanvas.invertY` properties), the front or back face of
        this plane may be facing the iewing plane.

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

        opts           = self.opts
        v2dMat         = opts.getTransform('voxel',   'display')
        d2vMat         = opts.getTransform('display', 'voxel')
        v2tMat         = opts.getTransform('voxel',   'texture')
        xax,  yax, zax = axes

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


    @memoize.memoize
    def get3DClipPlane(self, planeIdx):
        """Returns the clip plane at the given ``planeIdx`` as an origin and
        normal vector.
        """

        pos     = self.clipPosition[   planeIdx]
        azimuth = self.clipAzimuth[    planeIdx]
        incline = self.clipInclination[planeIdx]

        b       = self.bounds
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


    def clipPlaneVertices(self,
                          planeIdx,
                          clippedVertices,
                          clippedIndices,
                          xform):
        """Generates vertices for the clipping plane specified by ``planeIdx``
        (an index into the ``Volume3DOpts.clip*`` lists).

        See the :meth:`drawClipPlanes` method.
        """

        origin, normal = self.opts.get3DClipPlane(planeIdx)

        origin = transform.transform(      origin, xform)
        normal = transform.transformNormal(normal, xform)

        lines = trimesh.mesh_plane(
            clippedVertices,
            clippedIndices.reshape(-1, 3),
            plane_normal=normal,
            plane_origin=origin)

        # Assuming that the returned
        # lines are sorted
        vertices = np.array(lines.reshape(-1, 3), dtype=np.float32)

        if vertices.shape[0] < 3:
            return np.zeros((0, 3)), np.zeros((0,))

        indices = glroutines.polygonIndices(vertices.shape[0])

        return vertices, indices
