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
