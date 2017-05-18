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
from . import                volumeopts


class LabelOpts(volumeopts.NiftiOpts):
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

        if aux_file == '':
            aux_file = 'random'

        if aux_file.startswith('mgh'):
            aux_file = 'mgh-cma-freesurfer'

        if colourmaps.isLookupTableRegistered(aux_file):
            self.lut = aux_file

        volumeopts.NiftiOpts.__init__(self, overlay, *args, **kwargs)
