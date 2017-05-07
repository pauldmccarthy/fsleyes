#!/usr/bin/env python
#
# giftiopts.py - The GiftiOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GiftiOpts` class, which contains settings
for displaying a :class:`.GiftiSurface` overlay.
"""


import fsl.data.gifti as fslgifti
from . import            meshopts


class GiftiOpts(meshopts.MeshOpts):
    """The :class:`GiftiOpts` class, which contains settings for displaying
    a :class:`.GiftiSurface` overlay.

    Currently (as of FSLeyes |version|), the ``GiftiOpts`` class is identical
    to the :class:`.MeshOpts` class (from which it derives), with the exception
    that the initial value of the :attr:`.MeshOpts.coordSpace` property is
    set to ``'affine'``, and the :attr:`.MeshOpts.vertexData` property is
    populated with any GIFTI data files that are related to the surface file.
    """


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``GiftiOpts`` instance.

        All arguments are passed to the :class:`.MeshOpts` constructor.
        """

        self.getProp('coordSpace').setConstraint(self, 'default', 'affine')
        self.coordSpace = 'affine'

        vdataFiles = [None] + fslgifti.relatedFiles(overlay.dataSource)
        self.getProp('vertexData').setChoices(vdataFiles, instance=self)

        meshopts.MeshOpts.__init__(self, overlay, *args, **kwargs)
