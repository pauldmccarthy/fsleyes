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


import fsleyes_props      as props
import fsleyes.colourmaps as colourmaps
from . import                niftiopts


class LabelOpts(niftiopts.NiftiOpts):
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


    outlineWidth = props.Int(minval=0, maxval=10, default=1, clamped=True)
    """Width of labelled region outlines, if :attr:``outline` is ``True``.
    This value is in terms of pixels.
    """


    showNames = props.Boolean(default=False)
    """If ``True``, region names (as defined by the current
    :class:`.LookupTable`) will be shown alongside each labelled region.

    .. note:: Not implemented yet.
    """


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``LabelOpts`` instance for the specified ``overlay``.
        All arguments are passed through to the :class:`.NiftiOpts`
        constructor.
        """

        # Some FSL tools will set the nifti aux_file
        # field to the name of a colour map - Check
        # to see if this is the case (again, before
        # calling __init__, so we don't clobber any
        # existing values).
        aux_file = overlay.strval('aux_file').lower()

        if aux_file.startswith('mgh'):
            aux_file = 'freesurfercolorlut'

        # Check to see if any registered lookup table
        # has an ID that starts with the aux_file value.
        # Default to random lut if aux_file is empty,
        # or does not correspond to a registered lut.
        lut = 'random'

        if aux_file != '':
            luts = colourmaps.getLookupTables()
            luts = [l.key for l in luts if l.key.startswith(aux_file)]

            if len(luts) == 1:
                lut = luts[0]

        self.lut = lut

        niftiopts.NiftiOpts.__init__(self, overlay, *args, **kwargs)
