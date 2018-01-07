#!/usr/bin/env python
#
# maskopts.py - The MaskOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MaskOpts` class, which defines settings
for displaying an :class:`.Image` overlay as a binary mask.
"""


import copy
import logging

import fsleyes_props                      as props
from   fsl.utils.platform import platform as fslplatform
from . import                                volumeopts


log = logging.getLogger(__name__)


class MaskOpts(volumeopts.NiftiOpts):
    """The ``MaskOpts`` class defines settings for displaying an
    :class:`.Image` overlay as a binary mask.
    """


    threshold = props.Bounds(ndims=1)
    """The mask threshold range - values outside of this range are not
    displayed.
    """


    invert = props.Boolean(default=False)
    """If ``True``, the :attr:`threshold` range is inverted - values
    inside the range are not shown, and values outside of the range are shown.
    """


    colour = props.Colour()
    """The mask colour."""


    outline = props.Boolean(default=False)
    """If ``True`` only the outline of the mask will be shown.  If ``False``,
    the filled mask will be displayed.
    """


    outlineWidth = props.Int(minval=0, maxval=10, default=1, clamped=True)
    """Width of mask outline, if :attr:``outline` is ``True``.  This value is
    in terms of pixels.
    """


    interpolation = copy.copy(volumeopts.VolumeOpts.interpolation)


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``MaskOpts`` instance for the given overlay. All arguments
        are passed through to the :class:`.NiftiOpts` constructor.
        """

        # We need GL >= 2.1 for
        # spline interpolation
        if float(fslplatform.glVersion) < 2.1:
            interp = self.getProp('interpolation')
            interp.removeChoice('spline', instance=self)
            interp.updateChoice('linear', instance=self, newAlt=['spline'])

        kwargs['nounbind'] = ['interpolation']

        # Initialise threshold from data reange. Do
        # this before __init__, in case we need to
        # inherit settings from the parent instance
        dmin, dmax = overlay.dataRange
        dlen       = dmax - dmin
        doff       = dlen / 100.0

        self.threshold.xmin = dmin - doff
        self.threshold.xmax = dmax + doff
        self.threshold.xlo  = dmin + doff
        self.threshold.xhi  = dmax + doff

        volumeopts.NiftiOpts.__init__(self, overlay, *args, **kwargs)

        overlay.register(self.name,
                         self.__dataRangeChanged,
                         topic='dataRange',
                         runOnIdle=True)

        # The master MaskOpts instance makes
        # sure that colour[3] and Display.alpha
        # are consistent w.r.t. each other.
        self.__registered = self.getParent() is None
        if self.__registered:
            self.display.addListener('alpha',
                                     self.name,
                                     self.__alphaChanged,
                                     immediate=True)
            self        .addListener('colour',
                                     self.name,
                                     self.__colourChanged,
                                     immediate=True)


    def destroy(self):
        """Removes some property listeners and calls
        :meth:`.NitfiOpts.destroy`.
        """

        self.overlay.deregister(self.name, topic='dataRange')

        if self.__registered:
            self.display.removeListener('alpha',  self.name)
            self        .removeListener('colour', self.name)

        volumeopts.NiftiOpts.destroy(self)


    def __dataRangeChanged(self, *a):
        """Called when the :attr:`~fsl.data.image.Image.dataRange` changes.
        Updates the :attr:`threshold` limits.
        """
        dmin, dmax   = self.overlay.dataRange
        dRangeLen    = abs(dmax - dmin)
        dminDistance = dRangeLen / 100.0

        self.threshold.xmin = dmin - dminDistance
        self.threshold.xmax = dmax + dminDistance

        # If the threshold was
        # previously unset, grow it
        if self.threshold.x == (0, 0):
            self.threshold.x = (0, dmax + dminDistance)


    def __colourChanged(self, *a):
        """Called when :attr:`.colour` changes. Updates :attr:`.Display.alpha`
        from the alpha component.
        """

        alpha = self.colour[3] * 100

        log.debug('Propagating MaskOpts.colour[3] to '
                  'Display.alpha [{}]'.format(alpha))

        with props.skip(self.display, 'alpha', self.name):
            self.display.alpha = alpha


    def __alphaChanged(self, *a):
        """Called when :attr:`.Display.alpha` changes. Updates the alpha
        component of :attr:`.colour`.
        """

        alpha       = self.display.alpha / 100.0
        r, g, b, _  = self.colour

        log.debug('Propagating Display.alpha to MaskOpts.'
                  'colour[3] [{}]'.format(alpha))

        with props.skip(self, 'colour', self.name):
            self.colour = r, g, b, alpha
