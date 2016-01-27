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


import fsl.fsleyes.gl.shaders as shaders
import fsl.utils.transform    as transform


def compileShaders(self, vertShader, indexed=False):
    """Compiles the vertex/fragment shader programs (by creating a
    :class:`.GLSLShader` instance).

    If the :attr:`.VectorOpts.colourImage` property is set, the ``glvolume``
    fragment shader is used. Otherwise, the ``glvector`` fragment shader
    is used.
    """
    
    if self.shader is not None:
        self.shader.destroy()

    opts                = self.displayOpts
    useVolumeFragShader = opts.colourImage is not None

    if useVolumeFragShader: fragShader = 'glvolume'
    else:                   fragShader = 'glvector'

    vertSrc = shaders.getVertexShader(  vertShader)
    fragSrc = shaders.getFragmentShader(fragShader)
    
    return shaders.GLSLShader(vertSrc, fragSrc, indexed)

    
def updateFragmentShaderState(self, useSpline=False):
    """Updates the state of the fragment shader - it may be either the
    ``glvolume`` or the ``glvector`` shader.
    """

    changed             = False
    opts                = self.displayOpts
    shader              = self.shader
    useVolumeFragShader = opts.colourImage is not None

    invClipValXform = self.clipTexture.invVoxValXform
    clippingRange   = opts.clippingRange
    imageShape      = self.vectorImage.shape[:3]

    # Transform the clip threshold into
    # the texture value range, so the
    # fragment shader can compare texture
    # values directly to it.    
    if opts.clipImage is not None:
        clipLow  = clippingRange[0] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
        clipHigh = clippingRange[1] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
    else:
        clipLow  = 0
        clipHigh = 1

    if useVolumeFragShader:

        voxValXform     = self.colourTexture.voxValXform
        invVoxValXform  = self.colourTexture.invVoxValXform
        texZero         = 0.0 * invVoxValXform[0, 0] + invVoxValXform[3, 0]
        img2CmapXform   = transform.concat(
            voxValXform,
            self.cmapTexture.getCoordinateTransform())

        changed |= shader.set('clipTexture',      2)
        changed |= shader.set('imageTexture',     3)
        changed |= shader.set('colourTexture',    7)
        changed |= shader.set('negColourTexture', 7)
        changed |= shader.set('img2CmapXform',    img2CmapXform)
        changed |= shader.set('imageShape',       imageShape)
        changed |= shader.set('imageIsClip',      False)
        changed |= shader.set('useNegCmap',       False)
        changed |= shader.set('useSpline',        useSpline)
        changed |= shader.set('clipLow',          clipLow)
        changed |= shader.set('clipHigh',         clipHigh)
        changed |= shader.set('texZero',          texZero)
        changed |= shader.set('invertClip',       False)
    
    else:

        voxValXform = self.imageTexture.voxValXform
        cmapXform   = self.xColourTexture.getCoordinateTransform()

        changed |= shader.set('vectorTexture',   0)
        changed |= shader.set('modulateTexture', 1)
        changed |= shader.set('clipTexture',     2)
        changed |= shader.set('xColourTexture',  4)
        changed |= shader.set('yColourTexture',  5)
        changed |= shader.set('zColourTexture',  6)
        changed |= shader.set('voxValXform',     voxValXform)
        changed |= shader.set('cmapXform',       cmapXform)
        changed |= shader.set('imageShape',      imageShape)
        changed |= shader.set('clipLow',         clipLow)
        changed |= shader.set('clipHigh',        clipHigh) 
        changed |= shader.set('useSpline',       useSpline)

    return changed
