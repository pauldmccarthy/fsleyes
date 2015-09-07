#!/usr/bin/env python
#
# labelopts.py - The LabelOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LabelOpts` class, which defines settings
for displaying :class:`.Image` overlays as label images., such as anatomical
atlas images, tissue segmentation images, and so on.
"""

import props

import volumeopts

import fsl.fsleyes.colourmaps as fslcm


class LabelOpts(volumeopts.ImageOpts):
    """The ``LabelOpts`` class defines settings for displaying
    :class:`.Image` overlays as label images., such as anatomical atlas
    images, tissue segmentation images, and so on.
    """

    lut = props.Choice()
    """The :class:`.LookupTable` used to colour each label.
    """
    
    outline = props.Boolean(default=False)
    """If ``True`` only the outline of contiguous regions with the same label
    value will be shown. If ``False``, contiguous regions will be filled.
    """

    
    outlineWidth = props.Real(minval=0, maxval=1, default=0.25, clamped=True)
    """Width of labelled region outlines, if :attr:``outline` is ``True``.
    This value is in terms of the image voxels - a value of 1 will result in
    an outline that is one voxel wide.
    """

    
    showNames = props.Boolean(default=False)
    """If ``True``, region names (as defined by the current
    :class:`.LookupTable`) will be shown alongside each labelled region.
    """


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``LabelOpts`` instance for the specified ``overlay``.
        All arguments are passed through to the :class:`.ImageOpts`
        constructor.
        """
        volumeopts.ImageOpts.__init__(self, overlay, *args, **kwargs)

        luts  = fslcm.getLookupTables()
        alts  = [[l.name, l.key] for l in luts]

        lutChoice = self.getProp('lut')
        lutChoice.setChoices(luts, alternates=alts)
