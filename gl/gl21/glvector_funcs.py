#!/usr/bin/env python
#
# glvector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.fsleyes.gl.shaders      as shaders
import fsl.fsleyes.gl.glsl.program as glslprogram
import fsl.utils.transform         as transform


def compileShaders(self):

    if self.shader is not None:
        self.shader.delete()

    opts                = self.displayOpts
    useVolumeFragShader = opts.colourImage is not None

    if useVolumeFragShader: fragShader = 'GLVolume'
    else:                   fragShader = self

    vertSrc = shaders.getVertexShader(  self)
    fragSrc = shaders.getFragmentShader(fragShader)
    
    return glslprogram.ShaderProgram(vertSrc, fragSrc)

    
def updateFragmentShaderState(self, useSpline=False):
    """
    """
    opts                = self.displayOpts
    shader              = self.shader
    useVolumeFragShader = opts.colourImage is not None

    invClipValXform = self.clipTexture  .invVoxValXform
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

        shader.set('imageTexture',     3)
        shader.set('clipTexture',      2)
        shader.set('colourTexture',    7)
        shader.set('negColourTexture', 7)
        shader.set('img2CmapXform',    img2CmapXform)
        shader.set('imageShape',       imageShape)
        shader.set('imageIsClip',      False)
        shader.set('useNegCmap',       False)
        shader.set('useSpline',        useSpline)
        shader.set('clipLow',          clipLow)
        shader.set('clipHigh',         clipHigh)
        shader.set('texZero',          texZero)
        shader.set('invertClip',       False)
    
    else:

        voxValXform = self.imageTexture.voxValXform
        cmapXform   = self.xColourTexture.getCoordinateTransform()

        shader.set('imageTexture',    0)
        shader.set('modulateTexture', 1)
        shader.set('clipTexture',     2)
        shader.set('xColourTexture',  4)
        shader.set('yColourTexture',  5)
        shader.set('zColourTexture',  6)
        shader.set('voxValXform',     voxValXform)
        shader.set('cmapXform',       cmapXform)
        shader.set('imageShape',      imageShape)
        shader.set('clipLow',         clipLow)
        shader.set('clipHigh',        clipHigh) 
        shader.set('useSpline',       useSpline)
