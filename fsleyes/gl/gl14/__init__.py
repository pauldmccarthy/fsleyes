#!/usr/bin/env python
#
# __init__.py - Functions for OpenGL 1.4 rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains modules for rendering various :class:`.GLObject`
types in an OpenGL 1.4 compatible manner.
"""

from . import glvolume_funcs
from . import glrgbvector_funcs
from . import gllinevector_funcs
from . import glmesh_funcs
from . import gllabel_funcs

gltensor_funcs = None
glsh_funcs     = None
