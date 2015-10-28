#!/usr/bin/env python
#
# __init__.py - Functions for OpenGL 1.4 rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains modules for rendering various :class:`.GLObject`
types in an OpenGL 1.4 compatible manner. The following modules currently
exist:

.. autosummary::

   ~fsl.fsleyes.gl.gl14.glvolume_funcs
   ~fsl.fsleyes.gl.gl14.glrgbvector_funcs
   ~fsl.fsleyes.gl.gl14.gllinevector_funcs
   ~fsl.fsleyes.gl.gl14.glmodel_funcs
   ~fsl.fsleyes.gl.gl14.gllabel_funcs
"""

import glvolume_funcs
import glrgbvector_funcs
import gllinevector_funcs
import glmodel_funcs
import gllabel_funcs
