#!/usr/bin/env python
#
# volume3dopts.py - The Volume3DOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.Volume3DOpts` class, a mix-in for
use with :class:`.DisplayOpts` classes. It defines display properties used
for ray-cast based rendering of :class:`.Image` overlays.
"""


import fsleyes_props as props


class Volume3DOpts(object):
    """
    """


    dithering = props.Real(minval=0,
                           maxval=0.1,
                           default=0.01,
                           clamped=True)
    """Only used in 3D rendering. Specifies the amount of randomness to
    introduce in the rendering procedure to achieve a dithering (addition of
    random noise) effect. This is necessary to remove some aliasing effects
    inherent in the rendering process.
    """


    numSteps = props.Int(minval=50,
                         maxval=1000,
                         default=50,
                         clamped=True)
    """Only used in 3D rendering. Specifies the maximum number of samples to
    acquire in the rendering of each pixel of the 3D scene. This corresponds
    to the number of iterations of the ray-casting loop.
    """


    numClipPlanes = props.Int(minval=0, maxval=10, default=0, clamped=True)
    """Number of active clip planes. """


    showClipPlanes = props.Boolean(default=False)
    """If ``True``, wirframes depicting the active clipping planes will
    be drawn.
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
        """
        """

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
        """
        """
        pass
