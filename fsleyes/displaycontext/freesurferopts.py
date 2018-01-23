#!/usr/bin/env python
#
# freesurferopts.py - The FreesurferOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FreesurferOpts` class, which contains
settings for displaying a :class:`.FreesurferMesh` overlay.
"""


import fsl.data.freesurfer as fslfs
from . import                 meshopts


class FreesurferOpts(meshopts.MeshOpts):
    """The :class:`FreesurferOpts` class, which contains settings for
    displaying a :class:`.FreesurferMesh` overlay.
    """


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``FreesurferOpts`` instance.

        All arguments are passed to the :class:`.MeshOpts` constructor.
        """

        self.getProp('coordSpace').setAttribute(self, 'default', 'affine')
        self.coordSpace = 'affine'

        # Find surface files that
        # contain other vertex sets
        vertFiles  = [overlay.dataSource] + \
                     fslfs.relatedGeometryFiles(overlay.dataSource)

        vdataFiles = [None] + fslfs.relatedVertexDataFiles(overlay.dataSource)

        self.getProp('vertexSet') .setChoices(vertFiles,  instance=self)
        self.getProp('vertexData').setChoices(vdataFiles, instance=self)

        meshopts.MeshOpts.__init__(self, overlay, *args, **kwargs)
