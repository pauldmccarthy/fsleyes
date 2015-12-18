#!/usr/bin/env python
#
# glvector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import OpenGL.GL as gl
import numpy     as np

import fsl.fsleyes.gl.shaders as shaders
import fsl.utils.transform    as transform


def compileShaders(self, vertAtts, vertUniforms):

    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders) 

    opts                = self.displayOpts
    useVolumeFragShader = opts.colourImage is not None

    if useVolumeFragShader:
        fragShader   = 'GLVolume'
        fragUniforms = ['imageTexture',     'clipTexture', 'colourTexture',
                        'negColourTexture', 'imageIsClip', 'useNegCmap',
                        'imageShape',       'useSpline',   'img2CmapXform',
                        'clipLow',          'clipHigh',    'texZero',
                        'invertClip'] 
    else:
        fragShader   = self
        fragUniforms = ['imageTexture',   'modulateTexture', 'clipTexture',
                        'clipLow',        'clipHigh',        'xColourTexture',
                        'yColourTexture', 'zColourTexture',  'voxValXform',
                        'cmapXform',      'imageShape',      'useSpline'] 

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(fragShader)
    
    self.shaders    = shaders.compileShaders(vertShaderSrc, fragShaderSrc)
    self.shaderVars = shaders.getShaderVars(self.shaders,
                                            vertAtts,
                                            vertUniforms,
                                            fragUniforms) 

    
def updateFragmentShaderState(
        self,
        useSpline=False):
    """
    """
    opts                = self.displayOpts
    svars               = self.shaderVars
    useVolumeFragShader = opts.colourImage is not None

    if useVolumeFragShader:

        voxValXform     = self.colourTexture.voxValXform
        invVoxValXform  = self.colourTexture.invVoxValXform
        invClipValXform = self.clipTexture  .invVoxValXform
        clippingRange   = opts.clippingRange
        imageShape      = self.vectorImage.shape[:3]
        imageShape      = np.array(imageShape, dtype=np.float32)
        texZero         = 0.0 * invVoxValXform[0, 0] + invVoxValXform[3, 0]

        img2CmapXform = transform.concat(
            voxValXform,
            self.cmapTexture.getCoordinateTransform())
        img2CmapXform = np.array(img2CmapXform, dtype=np.float32).ravel('C') 
        
        if opts.clipImage is not None:
            clipLow  = clippingRange[0] * \
                invClipValXform[0, 0] + invClipValXform[3, 0]
            clipHigh = clippingRange[1] * \
                invClipValXform[0, 0] + invClipValXform[3, 0]
        else:
            clipLow  = 0
            clipHigh = 1
 
        gl.glUniform1i(svars['imageTexture'],      3)
        gl.glUniform1i(svars['clipTexture'],       2)
        gl.glUniform1i(svars['colourTexture'],     7)
        gl.glUniform1i(svars['negColourTexture'],  7)
        
        gl.glUniformMatrix4fv(svars['img2CmapXform'], 1, False, img2CmapXform)
        gl.glUniform3fv(      svars['imageShape'],  1,          imageShape)
        
        gl.glUniform1i(svars['imageIsClip'], False)
        gl.glUniform1i(svars['useNegCmap'],  False)
        gl.glUniform1i(svars['useSpline'],   useSpline)
        gl.glUniform1f(svars['clipLow'],     clipLow)
        gl.glUniform1f(svars['clipHigh'],    clipHigh)
        gl.glUniform1f(svars['texZero'],     texZero)
        gl.glUniform1i(svars['invertClip'],  False)
    
    else:

        # The coordinate transformation matrices for 
        # each of the three colour textures are identical
        voxValXform     = self.imageTexture.voxValXform
        invClipValXform = self.clipTexture .invVoxValXform
        cmapXform       = self.xColourTexture.getCoordinateTransform()
        imageShape      = np.array(self.vectorImage.shape, dtype=np.float32)
        clippingRange   = opts.clippingRange

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

        gl.glUniform1i(svars['imageTexture'],    0)
        gl.glUniform1i(svars['modulateTexture'], 1)
        gl.glUniform1i(svars['clipTexture'],     2)
        gl.glUniform1i(svars['xColourTexture'],  4)
        gl.glUniform1i(svars['yColourTexture'],  5)
        gl.glUniform1i(svars['zColourTexture'],  6)
        
        gl.glUniformMatrix4fv(svars['voxValXform'], 1, False, voxValXform)
        gl.glUniformMatrix4fv(svars['cmapXform'],   1, False, cmapXform)
        
        gl.glUniform3fv(svars['imageShape'], 1, imageShape)
        gl.glUniform1f( svars['clipLow'],       clipLow)
        gl.glUniform1f( svars['clipHigh'],      clipHigh) 
        gl.glUniform1f( svars['useSpline'],     useSpline)
