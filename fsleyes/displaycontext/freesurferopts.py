#!/usr/bin/env python
#
# freesurferopts.py - The FreesurferOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FreesurferOpts` class, which contains
settings for displaying a :class:`.FreesurferMesh` overlay.
"""


import fsl.data.freesurfer  as fslfs
import fsl.data.mghimage    as fslmgh
import fsl.transform.affine as affine
from . import                  meshopts


class FreesurferOpts(meshopts.MeshOpts):
    """The :class:`FreesurferOpts` class, which contains settings for
    displaying a :class:`.FreesurferMesh` overlay.

    This class differs from the :class:`.MeshOpts` class only in that
    it tries to identify auxillary vertex and data files for the
    :attr:`.MeshOpts.vertexSet` and :attr:`.MeshOpts.vertexData`
    properties based on <freesurfer file naming conventions.
    """


    def __init__(self, overlay, *args, **kwargs):
        """Create a ``FreesurferOpts`` instance.

        All arguments are passed to the :class:`.MeshOpts` constructor.
        """

        self.getProp('coordSpace').setDefault('torig', self)
        self.coordSpace = 'torig'

        # Find surface files that
        # contain other vertex sets
        vertFiles  = [overlay.dataSource] + \
                     fslfs.relatedGeometryFiles(overlay.dataSource)

        vdataFiles = [None] + fslfs.relatedVertexDataFiles(overlay.dataSource)

        self.getProp('vertexSet') .setChoices(vertFiles,  instance=self)
        self.getProp('vertexData').setChoices(vdataFiles, instance=self)

        meshopts.MeshOpts.__init__(self, overlay, *args, **kwargs)
