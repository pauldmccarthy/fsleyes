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
import fsl.data.mghimage   as fslmgh
import fsl.utils.transform as transform
from . import                 meshopts


class FreesurferOpts(meshopts.MeshOpts):
    """The :class:`FreesurferOpts` class, which contains settings for
    displaying a :class:`.FreesurferMesh` overlay.

    Freesurfer surface vertices are defined in a coordinate system which
    differs from the world coordinate system of the source image. This
    class customises some behaviour of the :class:`.MeshOpts` class so
    that this difference is taken into account.
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


    def getTransform(self, from_, to):
        """Overrides :meth:`.MeshOpts.getTransform`. If the
        :attr:`.MeshOpts.coordSpace` property is ``'torig'``, and one of
        ``from_`` or ``to`` is ``'mesh'``, the transform is adjusted to
        account for the difference between Freesurfer's RAS and RAStkr spaces.
        """

        ref   = self.refImage
        xform = meshopts.MeshOpts.getTransform(self, from_, to)

        if isinstance(ref, fslmgh.MGHImage) and self.coordSpace == 'torig':

            surf2world = ref.surfToWorldMat
            world2surf = ref.worldToSurfMat

            if   from_ == 'mesh': xform = transform.concat(xform, surf2world)
            elif to    == 'mesh': xform = transform.concat(world2surf, xform)

        return xform


    def transformCoords(self, coords, from_, to, **kwargs):
        """Overrides :meth:`.MeshOpts.transformCoords`. If the
        :attr:`.MeshOpts.coordSpace` property is ``'torig'``, and one of
        ``from_`` or ``to`` is ``'mesh'``, the coordinate transform is
        adjusted to take into account the difference between Freesurfer's RAS
        and RAStkr spaces.
        """

        ref  = self.refImage
        pre  = None
        post = None

        if isinstance(ref, fslmgh.MGHImage) and self.coordSpace == 'torig':
            if from_ == 'mesh': pre  = ref.surfToWorldMat
            if to    == 'mesh': post = ref.worldToSurfMat

        coords = meshopts.MeshOpts.transformCoords(
            self, coords, from_, to, pre=pre, post=post, **kwargs)

        return coords
