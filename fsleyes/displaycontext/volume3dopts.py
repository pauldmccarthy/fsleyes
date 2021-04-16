#!/usr/bin/env python
#
# volume3dopts.py - The Volume3DOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.Volume3DOpts` class, a mix-in for
use with :class:`.DisplayOpts` classes.
"""

import numpy as np

import fsl.transform.affine as affine
import fsleyes_props        as props
import fsleyes_widgets      as fwidgets
import fsleyes.gl           as fslgl


class Volume3DOpts(object):
    """The ``Volume3DOpts`` class is a mix-in for use with :class:`.DisplayOpts`
    classes. It defines display properties used for ray-cast based rendering
    of :class:`.Image` overlays.


    The properties in this class are tightly coupled to the ray-casting
    implementation used by the :class:`.GLVolume` class - see its documentation
    for details.
    """


    blendFactor = props.Real(minval=0.001, maxval=1, default=0.1)
    """Controls how much each sampled point on each ray contributes to the
    final colour.
    """


    blendByIntensity  = props.Boolean(default=True)
    """If ``True``, the colours from samples are weighted by voxel intensity
    as well as the blendFactor.
    """


    numSteps = props.Int(minval=25, maxval=500, default=100, clamped=False)
    """Specifies the maximum number of samples to acquire in the rendering of
    each pixel of the 3D scene. This corresponds to the number of iterations
    of the ray-casting loop.

    .. note:: In a low performance environment, the actual number of steps
              may differ from this value - use the :meth:`getNumSteps` method
              to get the number of steps that are actually executed.
    """


    numInnerSteps = props.Int(minval=1, maxval=100, default=10, clamped=True)
    """Only used in low performance environments. Specifies the number of
    ray-casting steps to execute in a single iteration on the GPU, as part
    of an outer loop which is running on the CPU. See the :class:`.GLVolume`
    class documentation for more details on the rendering process.

    .. warning:: The maximum number of iterations that can be performed within
                 an ARB fragment program is implementation-dependent. Too high
                 a value may result in errors or a corrupted view. See the
                 :class:`.GLVolume` class for details.
    """


    resolution = props.Int(minval=10, maxval=100, default=100, clamped=True)
    """Only used in low performance environments. Specifies the resolution
    of the off-screen buffer to which the volume is rendered, as a percentage
    of the screen resolution.

    See the :class:`.GLVolume` class documentation for more details.
    """


    smoothing = props.Int(minval=0, maxval=10, default=0, clamped=True)
    """Amount of smoothing to apply to the rendered volume - this setting
    controls the smoothing filter radius, in pixels.
    """


    numClipPlanes = props.Int(minval=0, maxval=5, default=0, clamped=True)
    """Number of active clip planes. """


    showClipPlanes = props.Boolean(default=False)
    """If ``True``, wirframes depicting the active clipping planes will
    be drawn.
    """

    clipMode = props.Choice(('intersection', 'union', 'complement'))
    """This setting controls how the active clip planes are combined.

      -  ``intersection`` clips the intersection of all planes
      -  ``union`` clips the union of all planes
      -  ``complement`` clips the complement of all planes
    """


    clipPosition = props.List(
        props.Percentage(minval=0, maxval=100, clamped=True),
        minlen=10,
        maxlen=10)
    """Centre of clip-plane rotation, as a distance from the volume centre -
    0.5 is centre.
    """


    clipAzimuth = props.List(
        props.Real(minval=-180, maxval=180, clamped=True),
        minlen=10,
        maxlen=10)
    """Rotation (degrees) of the clip plane about the Z axis, in the display
    coordinate system.
    """


    clipInclination = props.List(
        props.Real(minval=-180, maxval=180, clamped=True),
        minlen=10,
        maxlen=10)
    """Rotation (degrees) of the clip plane about the Y axis in the display
    coordinate system.
    """


    def __init__(self):
        """Create a :class:`Volume3DOpts` instance.
        """

        # If we're in an X11/SSh session,
        # step down the quality so it's
        # a bit faster.
        if fwidgets.inSSHSession():
            self.numSteps    = 60
            self.resolution  = 70
            self.blendFactor = 0.3

        # If we're in GL14, restrict the
        # maximum possible amount of
        # smoothing, as GL14 fragment
        # programs cannot be too large.
        if float(fslgl.GL_COMPATIBILITY) < 2.1:
            smooth = self.getProp('smoothing')
            smooth.setAttribute(self, 'maxval', 6)

        self.clipPosition[:]    = 10 * [50]
        self.clipAzimuth[:]     = 10 * [0]
        self.clipInclination[:] = 10 * [0]

        # Give convenient initial values for
        # the first three clipping planes
        self.clipInclination[1] = 90
        self.clipAzimuth[    1] = 0
        self.clipInclination[2] = 90
        self.clipAzimuth[    2] = 90


    def destroy(self):
        """Does nothing. """
        pass


    def getNumSteps(self):
        """Return the value of the :attr:`numSteps` property, possibly
        adjusted according to the the :attr:`numInnerSteps` property. The
        result of this method should be used instead of the value of
        the :attr:`numSteps` property.

        See the :class:`.GLVolume` class for more details.
        """

        if float(fslgl.GL_COMPATIBILITY) >= 2.1:
            return self.numSteps

        outer = self.getNumOuterSteps()

        return int(outer * self.numInnerSteps)


    def getNumOuterSteps(self):
        """Returns the number of iterations for the outer ray-casting loop.

        See the :class:`.GLVolume` class for more details.
        """

        total = self.numSteps
        inner = self.numInnerSteps
        outer = np.ceil(total / float(inner))

        return int(outer)


    def calculateRayCastSettings(self, view=None, proj=None):
        """Calculates various parameters required for 3D ray-cast rendering
        (see the :class:`.GLVolume` class).


        :arg view: Transformation matrix which transforms from model
                   coordinates to view coordinates (i.e. the GL view matrix).


        :arg proj: Transformation matrix which transforms from view coordinates
                   to normalised device coordinates (i.e. the GL projection
                   matrix).

        Returns a tuple containing:

          - A vector defining the amount by which to move along a ray in a
            single iteration of the ray-casting algorithm. This can be added
            directly to the volume texture coordinates.

          - A transformation matrix which transforms from image texture
            coordinates into the display coordinate system.

        .. note:: This method will raise an error if called on a
                  ``GLImageObject`` which is managing an overlay that is not
                  associated with a :class:`.Volume3DOpts` instance.
        """

        if view is None: view = np.eye(4)
        if proj is None: proj = np.eye(4)

        # In GL, the camera position
        # is initially pointing in
        # the -z direction.
        eye    = [0, 0, -1]
        target = [0, 0,  1]

        # We take this initial camera
        # configuration, and transform
        # it by the inverse modelview
        # matrix
        t2dmat = self.getTransform('texture', 'display')
        xform  = affine.concat(view, t2dmat)
        ixform = affine.invert(xform)

        eye    = affine.transform(eye,    ixform, vector=True)
        target = affine.transform(target, ixform, vector=True)

        # Direction that the 'camera' is
        # pointing, normalied to unit length
        cdir = affine.normalise(eye - target)

        # Calculate the length of one step
        # along the camera direction in a
        # single iteration of the ray-cast
        # loop. Multiply by sqrt(3) so that
        # the maximum number of steps will
        # be reached across the longest axis
        # of the image texture cube.
        rayStep = np.sqrt(3) * cdir / self.getNumSteps()

        # A transformation matrix which can
        # transform image texture coordinates
        # into the corresponding screen
        # (normalised device) coordinates.
        # This allows the fragment shader to
        # convert an image texture coordinate
        # into a relative depth value.
        #
        # The projection matrix puts depth into
        # [-1, 1], but we want it in [0, 1]
        zscale = affine.scaleOffsetXform([1, 1, 0.5], [0, 0, 0.5])
        xform  = affine.concat(zscale, proj, xform)

        return rayStep, xform


    def get3DClipPlane(self, planeIdx):
        """A convenience method which calculates a point-vector description
        of the specified clipping plane. ``planeIdx`` is an index into the
        :attr:`clipPosition`, :attr:`clipAzimuth`, and
        :attr:`clipInclination`, properties.

        Returns the clip plane at the given ``planeIdx`` as an origin and
        normal vector, in the display coordinate system..
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

        rot1     = affine.axisAnglesToRotMat(incline, 0, 0)
        rot2     = affine.axisAnglesToRotMat(0, 0, azimuth)
        rotation = affine.concat(rot2, rot1)

        normal = affine.transformNormal(normal, rotation)
        normal = affine.normalise(normal)

        offset = (pos - 0.5) * max((b.xlen, b.ylen, b.zlen))
        origin = centre + normal * offset

        return origin, normal
