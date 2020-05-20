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

import fsl.data.image                      as fslimage
import fsl.transform.affine                as affine
import fsl.utils.memoize                   as memoize

import fsleyes.displaycontext.volume3dopts as volume3dopts
import fsleyes.colourmaps                  as fslcmaps
import fsleyes.gl.globject                 as globject
import fsleyes.gl.textures                 as textures
import fsleyes.gl.resources                as glresources
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


    @property
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

        texCoords = affine.transform(voxCoords, v2tMat)

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

        texCoords = affine.transform(voxCoords, v2tMat)

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
            voxels = affine.transform(voxels, d2vMat)
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
            # voxels = affine.transform(voxels, d2vMat)
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
                verts = affine.transform(verts, xform)

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


class AuxImageTextureManager:
    """Utility class used by some :class:`GLImageObject` instances.

    The ``AuxImageTextureManager`` is used to manage "auxillary"
    :class:`.ImageTexture` instances which are used when rendering the
    ``GLImageObject``. For example, :class:`.GLVolume` instances may need to
    use an ``ImageTexture`` to store the data for the
    :attr:`.VolumeOpts.clipImage` setting.
    """


    def __init__(self, globj, **auximages):
        """Create an ``AuxImageTextureManager``.

        Note that an initial value *must* be given for each auxillary texture
        type.

        :arg globj:     The :class:`GLImageObject` which requires the
                        auxillary image textures.

        :arg auximages: ``auxtype=initial_value`` for each auxillary image
                        texture type. The initial value must be one of:

                         - an :class:`.Image`
                         - ``None``
                         - A tuple containing an ``Image``, and a dict
                           containing settings to initialise the
                           ``ImageTexture`` (passed as ``kwargs`` to
                           ``ImageTexture.__init__``).
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__globj       = globj
        self.__image       = globj.image
        self.__opts        = globj.opts
        self.__displayCtx  = globj.displayCtx
        self.__auxtypes    = tuple(auximages.keys())
        self.__auxopts     = {t : None for t in self.__auxtypes}
        self.__auximages   = {t : None for t in self.__auxtypes}
        self.__auxtextures = {t : None for t in self.__auxtypes}

        for which, image in auximages.items():
            if isinstance(image, tuple):
                image, settings = image
            else:
                settings = {}
            self.registerAuxImage(which, image, **settings)


    def destroy(self):
        """Must be calld when this ``AuxImageTextureManager`` is no longer
        needed. Clears references and destroys texture objects.
        """
        self.__globj      = None
        self.__displayCtx = None
        self.__opts       = None

        for t in self.__auxtypes:
            self.deregisterAuxImage(t, False)
            self.__destroyAuxTexture(t)


    @property
    def name(self):
        return self.__name


    @property
    def globj(self):
        return self.__globj


    @property
    def image(self):
        return self.__image


    @property
    def opts(self):
        return self.__opts


    @property
    def displayCtx(self):
        return self.__displayCtx


    def texture(self, which):
        return self.__auxtextures[which]


    def textureXform(self, which):
        """Generates and returns a transformation matrix which can be used to
        transform texture coordinates from the main image to the specified
        auxillary image.
        """
        opts     = self.opts
        auximage = self.__auximages[which]
        auxopts  = self.__auxopts[  which]

        if auximage is None:
            return np.eye(4)
        else:
            return affine.concat(
                auxopts.getTransform('display', 'texture'),
                opts   .getTransform('texture', 'display'))


    def texturesReady(self):
        """Returns ``True`` if all auxillary textures are in a usable
        state, ``False`` otherwise.
        """
        for tex in self.__auxtextures.values():
            if (tex is None) or (not tex.ready()):
                return False
        return True


    def registerAuxImage(self, which, image, **kwargs):
        """Register an auxillary image.

        Creates an :class:`.ImageTexture` to store the image data.
        Registers a listener with the :attr:`.NiftiOpts.volume` property of
        the image, so the texture can be updated when the image volume
        changes.

        :arg which: Name of the auxillary image
        :arg image: :class:`.Image` object

        All other arguments are passed through to the :meth:`refreshAuxTexture`
        method.
        """

        if self.__auximages[which] is not None:
            self.deregisterAuxImage(which, False)

        if image is None:
            opts = None

        else:
            opts = self.displayCtx.getOpts(image)
            def volumeChange(*a):
                tex = self.texture(which)
                tex.set(volume=opts.index()[3:])

            opts.addListener('volume',
                             '{}_{}'.format(self.name, which),
                             volumeChange,
                             weak=False)

        self.__auximages[which] = image
        self.__auxopts[  which] = opts
        self.refreshAuxTexture(which, **kwargs)


    def deregisterAuxImage(self, which, refreshTexture=True):
        """De-register an auxillary image.  Deregisters the
        :attr:`.NiftiOpts.volume` listener that was registered in
        :meth:`registerAuxImage`, and destroys the associated
        :class:`.ImageTexture`.

        :arg which:          Name of the auxillary image

        :arg refreshTexture: Defaults to ``True``. Call
                             :meth:`refreshAuxTexture` to destroy the
                             associated ``ImageTexture``.
        """

        image = self.__auximages[which]
        opts  = self.__auxopts[  which]

        if image is None:
            return

        opts.removeListener('volume', '{}_{}'.format(self.name, which))

        self.__auximages[which] = None
        self.__auxopts[  which] = None

        if refreshTexture:
            self.refreshAuxTexture(which)


    def __destroyAuxTexture(self, which):
        """Destroys the :class:`.ImageTexture` for type ``which``. """
        tex = self.__auxtextures[which]
        if tex is not None:
            glresources.delete(tex.name)
        self.__auxtextures[which] = None


    def refreshAuxTexture(self, which, **kwargs):
        """Create/re-create an auxillary :class:`.ImageTexture`.

        The previous ``ImageTexture`` (if one exists) is destroyed.  If no
        :class:`.Image` of type ``which`` is currently registered, a small
        dummy ``Image`` and ``ImageTexture`` is created.

        :arg which: Name of the auxillary image

        All other arguments are passed through to the
        :class:`.ImageTexture.__init__` method.
        """

        self.__destroyAuxTexture(which)

        image = self.__auximages[  which]
        opts  = self.__auxopts[    which]
        tex   = self.__auxtextures[which]

        if image is None:
            textureData    = np.zeros((3, 3, 3), dtype=np.uint8)
            textureData[:] = 255
            image          = fslimage.Image(textureData)
            norm           = None
        else:
            norm = image.dataRange

        # by default we use a name which
        # is not coupled to the aux opts
        # instance, as the texture may be
        # sharable.
        texName = '{}_{}_{}_{}'.format(
            type(self).__name__, id(self.image), id(image), which)

        # check to see whether the aux
        # opts object is unsynced from
        # its parent - if so, we have to
        # create a dedicated texture
        if opts is not None:
            unsynced = (opts.getParent() is None or
                        not opts.isSyncedToParent('volume'))
            if unsynced:
                texName = '{}_unsync_{}'.format(texName, id(opts))

        if opts is not None: volume = opts.index()[3:]
        else:                volume = 0

        tex = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            image,
            normaliseRange=norm,
            volume=volume,
            notify=False,
            **kwargs)

        self.__auxtextures[which] = tex
