#!/usr/bin/env python
#
# __init__.py - Functions for OpenGL 1.4 rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains modules for rendering various :class:`.GLObject`
types in an OpenGL 1.4 compatible manner.
"""

from . import glvolume_funcs      # noqa
from . import glrgbvector_funcs   # noqa
from . import gllinevector_funcs  # noqa
from . import glmesh_funcs        # noqa
from . import glmask_funcs        # noqa
from . import gllabel_funcs       # noqa

gltensor_funcs = None
glsh_funcs     = None
glmip_funcs    = None
