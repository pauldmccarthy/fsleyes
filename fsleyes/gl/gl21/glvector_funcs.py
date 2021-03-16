#!/usr/bin/env python
#
# glvector_funcs.py - Functions used by glrgbvector_funcs and
#                     gllinevector_funcs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains logic for managing vertex and fragment shader programs
used for rendering :class:`.GLRGBVector` and :class:`.GLLineVector` instances.
These functions are used by the :mod:`.gl21.glrgbvector_funcs` and
:mod:`.gl21.gllinevector_funcs` modules.
"""


import numpy as np

import fsl.data.constants   as constants
import fsl.transform.affine as affine
import fsleyes.gl.shaders   as shaders


def compileShaders(self, vertShader, indexed=False):
    """Compiles the vertex/fragment shader programs (by creating a
    :class:`.GLSLShader` instance).

    If the :attr:`.VectorOpts.colourImage` property is set, the ``glvolume``
    fragment shader is used. Otherwise, the ``glvector`` fragment shader
    is used.
    """

    if self.shader is not None:
        self.shader.destroy()

    opts                = self.opts
    useVolumeFragShader = opts.colourImage is not None

    self.useVolumeFragShader = useVolumeFragShader

    if useVolumeFragShader: fragShader = 'glvolume'
    else:                   fragShader = 'glvector'

    vertSrc = shaders.getVertexShader(  vertShader)
    fragSrc = shaders.getFragmentShader(fragShader)

    return shaders.GLSLShader(vertSrc, fragSrc, indexed)


def updateShaderState(self, useSpline=False):
    """Updates the state of the vector vertex fragment shader. The fragment
    shader may be either the ``glvolume`` or the ``glvector`` shader.
    """

    changed           = False
    opts              = self.opts
    shader            = self.shader
    imageShape        = self.vectorImage.shape[:3]
    modLow,  modHigh  = self.getModulateRange()
    clipLow, clipHigh = self.getClippingRange()

    if opts.modulateImage is None: modShape  = [1, 1, 1]
    else:                          modShape  = opts.modulateImage.shape[:3]
    if opts.clipImage     is None: clipShape = [1, 1, 1]
    else:                          clipShape = opts.clipImage.shape[:3]

    modMode     = {'brightness' : 0,
                   'alpha'      : 1}[opts.modulateMode]

    clipXform   = self.getAuxTextureXform('clip')
    colourXform = self.getAuxTextureXform('colour')
    modXform    = self.getAuxTextureXform('modulate')

    changed |= self.shader.set('clipCoordXform',   clipXform)
    changed |= self.shader.set('colourCoordXform', colourXform)
    changed |= self.shader.set('modCoordXform',    modXform)

    if self.useVolumeFragShader:

        voxValXform   = self.colourTexture.voxValXform
        img2CmapXform = affine.concat(
            self.cmapTexture.getCoordinateTransform(),
            voxValXform)

        changed |= shader.set('clipTexture',      1)
        changed |= shader.set('imageTexture',     2)
        changed |= shader.set('colourTexture',    3)
        changed |= shader.set('negColourTexture', 3)
        changed |= shader.set('img2CmapXform',    img2CmapXform)
        changed |= shader.set('imageShape',       imageShape)
        changed |= shader.set('imageIsClip',      False)
        changed |= shader.set('useNegCmap',       False)
        changed |= shader.set('useSpline',        useSpline)
        changed |= shader.set('clipLow',          clipLow)
        changed |= shader.set('clipHigh',         clipHigh)
        changed |= shader.set('invertClip',       False)

    else:
        # If we are displaying an RGB24 image
        # as a vector, we map uint8 [0, 255] to
        # [-1, 1]. The integer values will be
        # automatically normalised to [0, 1],
        # so we transform from that range.
        if self.vectorImage.niftiDataType == constants.NIFTI_DT_RGB24:
            voxValXform = affine.scaleOffsetXform(2, -1)

        # Otherwise, if it's floating point,
        # it will not be normalised.
        else:
            voxValXform = self.imageTexture.voxValXform

        colours, colourXform = self.getVectorColours()

        changed |= shader.set('modulateTexture', 0)
        changed |= shader.set('clipTexture',     1)
        changed |= shader.set('vectorTexture',   4)
        changed |= shader.set('xColour',         colours[0])
        changed |= shader.set('yColour',         colours[1])
        changed |= shader.set('zColour',         colours[2])
        changed |= shader.set('colourXform',     colourXform)
        changed |= shader.set('voxValXform',     voxValXform)
        changed |= shader.set('imageShape',      imageShape)
        changed |= shader.set('modImageShape',   modShape)
        changed |= shader.set('clipImageShape',  clipShape)
        changed |= shader.set('clipLow',         clipLow)
        changed |= shader.set('clipHigh',        clipHigh)
        changed |= shader.set('modLow',          modLow)
        changed |= shader.set('modHigh',         modHigh)
        changed |= shader.set('useSpline',       useSpline)
        changed |= shader.set('modulateMode',    modMode)

    return changed
