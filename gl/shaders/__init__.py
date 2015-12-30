#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import glsl.parse   as glslparse
import glsl.program as glslprogram
import arbp.parse   as arbpparse
import arbp.program as arbpprogram


GLSLShader = glslprogram.GLSLShader
ARBShaer   = arbpprogram.ARBShader
parseGLSL  = glslparse  .parseGLSL
parseARBP  = arbpparse  .parseARBP
