#!/usr/bin/env python
#
# glgiftimesh.py - The GLGiftiMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLGiftiMesh` class, a :class:`.GLObject`
used to render :class:`.GiftiSurface` overlays.
"""


import numpy as np

import fsl.utils.transform as transform
from . import                 glmesh


class GLGiftiMesh(glmesh.GLMesh):
    """The :class:`GLGiftiMesh` class is a :class:`.GLObject` used to render
    :class:`.GiftiSurface` overlays.

    Currently (as of FSLeyes |version|), the ``GLGiftiMesh`` class is nearly
    identical to the :class:`.GLMesh` class, from which it derives.
    """

    def __init__(self, *a, **k):
        """Create a ``GLGiftiMesh`` instance.

        All arguments are passed to the :class:`.GLMesh` constructor.
        """
        glmesh.GLMesh.__init__(self, *a, **k)


    def updateVertices(self, *a):
        """Overrides the :meth:`.GLMesh.updateVertices` method. The
        vertex order of the ``GiftiSurface`` indices needs to be adjusted
        to make them displayable in OpenGL.
        """

        import fsl.data.gifti as fslgifti

        overlay  = self.overlay
        vertices = overlay.vertices
        indices  = overlay.indices
        xform    = self.opts.getCoordSpaceTransform()

        if not np.all(np.isclose(xform, np.eye(4))):
            vertices = transform.transform(vertices, xform)

        # We need to fix the
        # triangle unwinding
        # order for Gifti surfaces
        if isinstance(overlay, fslgifti.GiftiSurface):
            indices = indices[:, [1, 0, 2]]

        self.vertices = np.array(vertices,          dtype=np.float32)
        self.indices  = np.array(indices.flatten(), dtype=np.uint32)
        self.notify()
