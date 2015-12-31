#!/usr/bin/env python
#
# glvector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.fsleyes.gl.shaders as shaders


def destroy(self):
    """Destroys the vertex/fragment shader programs created in :func:`init`.
    """
    self.shader.delete()
    self.shader = None

    
def compileShaders(self, vertShader):
    """Compiles the vertex/fragment shader programs used for drawing
    :class:`.GLRGBVector` instances. Stores references to the shader
    programs on the ``GLRGBVector`` instance. 
    """
    if self.shader is not None:
        self.shader.delete()

    vertSrc  = shaders.getVertexShader(  vertShader)
    fragSrc  = shaders.getFragmentShader('glvector')
    textures = {
        'vectorTexture'   : 0,
        'modulateTexture' : 1,
        'clipTexture'     : 2,
        'xColourTexture'  : 4,
        'yColourTexture'  : 5,
        'zColourTexture'  : 6
    }
        
    self.shader = shaders.ARBPShader(vertSrc, fragSrc, textures)


def updateFragmentShaderState(self):

    opts = self.displayOpts

    self.shader.load()
    
    voxValXform     = self.imageTexture.voxValXform
    invClipValXform = self.clipTexture.invVoxValXform

    cmapXform       = self.xColourTexture.getCoordinateTransform()
    shape           = list(self.vectorImage.shape[:3])
    clippingRange   = opts.clippingRange
    
    if opts.clipImage is not None:
        clipLow  = clippingRange[0] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
        clipHigh = clippingRange[1] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
    else:
        clipLow  = 0
        clipHigh = 1

    self.shader.setFragParam('voxValXform', voxValXform)
    self.shader.setFragParam('cmapXform',   cmapXform)
    self.shader.setFragParam('imageShape',  shape + [0])
    self.shader.setFragParam('clipping',    [clipLow, clipHigh, 0, 0])

    self.shader.unload()
