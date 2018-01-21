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

        vdataFiles = [None] + fslfs.relatedFiles(overlay.dataSource)
        self.getProp('vertexData').setChoices(vdataFiles, instance=self)

        meshopts.MeshOpts.__init__(self, overlay, *args, **kwargs)
