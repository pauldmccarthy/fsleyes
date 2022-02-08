#!/usr/bin/env python
#
# __init__.py - Functions for OpenGL 3.3 rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains modules for rendering various :class:`.GLObject`
types in an OpenGL 3.3 compatible manner.
"""

from .      import gltractogram_funcs  # noqa
from ..gl21 import (gllabel_funcs,
                    gllinevector_funcs,
                    glmask_funcs,
                    glmesh_funcs,
                    glmip_funcs,
                    glrgbvector_funcs,
                    glrgbvolume_funcs,
                    glsh_funcs,
                    gltensor_funcs,
                    glvector_funcs,
                    glvolume_funcs)  # noqa
