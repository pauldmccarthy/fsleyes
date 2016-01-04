#!/usr/bin/env python
#
# glvector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.fsleyes.gl.shaders as shaders
import fsl.utils.transform    as transform


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

    opts                = self.displayOpts
    useVolumeFragShader = opts.colourImage is not None

    if useVolumeFragShader: fragShader = 'glvolume'
    else:                   fragShader = 'glvector'
    
    vertSrc  = shaders.getVertexShader(  vertShader)
    fragSrc  = shaders.getFragmentShader(fragShader)

    if useVolumeFragShader:
        textures = {
            'imageTexture'     : 3,
            'clipTexture'      : 2,
            'colourTexture'    : 7,
            'negColourTexture' : 7
        }

    else:
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

    opts                = self.displayOpts
    useVolumeFragShader = opts.colourImage is not None 

    invClipValXform = self.clipTexture.invVoxValXform
    shape           = list(self.vectorImage.shape[:3])
    clippingRange   = opts.clippingRange
    
    if opts.clipImage is not None:
        clipLo = clippingRange[0] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
        clipHi = clippingRange[1] * \
            invClipValXform[0, 0] + invClipValXform[3, 0]
    else:
        clipLo = 0
        clipHi = 1

    clipping = [clipLo, clipHi, -1, -1]

    self.shader.load()

    # Inputs which are required by both the
    # glvolume and glvetor fragment shaders
    self.shader.setFragParam('imageShape', shape + [0])
    self.shader.setFragParam('clipping',   clipping)
    
    if useVolumeFragShader:
        
        voxValXform    = self.colourTexture.voxValXform
        invVoxValXform = self.colourTexture.voxValXform
        cmapXform      = self.cmapTexture.getCoordinateTransform()
        voxValXform    = transform.concat(voxValXform, cmapXform)
        texZero        = 0.0 * invVoxValXform[0, 0] + invVoxValXform[3, 0]
        
        self.shader.setFragParam('voxValXform', voxValXform)
        self.shader.setFragParam('negCmap',     [0, texZero, 0, 0])

    else:

        voxValXform = self.imageTexture.voxValXform 
        cmapXform   = self.xColourTexture.getCoordinateTransform()
        
        self.shader.setFragParam('voxValXform', voxValXform)
        self.shader.setFragParam('cmapXform',   cmapXform)

    self.shader.unload()
