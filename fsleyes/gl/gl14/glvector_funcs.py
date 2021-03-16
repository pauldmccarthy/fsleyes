#!/usr/bin/env python
#
# glvector_funcs.py - Functions used by glrgbvector_funcs and
#                     gllinevector_funcs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains logic for managing vertex and fragment shader programs
used for rendering :class:`.GLRGBVector` and :class:`.GLLineVector` instances.
These functions are used by the :mod:`.gl14.glrgbvector_funcs` and
:mod:`.gl14.gllinevector_funcs` modules.
"""


import numpy as np

import fsl.data.constants   as constants
import fsl.transform.affine as affine
import fsleyes.gl.shaders   as shaders


def destroy(self):
    """Destroys the vertex/fragment shader programs created in :func:`init`.
    """
    self.shader.destroy()
    self.shader = None


def compileShaders(self, vertShader):
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

    if useVolumeFragShader: fragShader = 'glvolume'
    else:                   fragShader = 'glvector'

    vertSrc  = shaders.getVertexShader(  vertShader)
    fragSrc  = shaders.getFragmentShader(fragShader)

    if useVolumeFragShader:
        textures = {
            'clipTexture'      : 1,
            'imageTexture'     : 2,
            'colourTexture'    : 3,
            'negColourTexture' : 3,

            # glvolume frag shader expects a modulate
            # alpha texture, but it is not used
            'modulateTexture'  : 1,
        }

    else:
        textures = {
            'modulateTexture' : 0,
            'clipTexture'     : 1,
            'vectorTexture'   : 4,
        }

    self.shader = shaders.ARBPShader(vertSrc,
                                     fragSrc,
                                     shaders.getShaderDir(),
                                     textures)


def updateShaderState(self):
    """Updates the state of the vector vertex and fragment shaders - the
    fragment shader may may be either the ``glvolume`` or the ``glvector``
    shader.
    """

    opts                = self.opts
    useVolumeFragShader = opts.colourImage is not None
    modLow,  modHigh    = self.getModulateRange()
    clipLow, clipHigh   = self.getClippingRange()
    modMode             = {'brightness' : -0.5,
                           'alpha'      :  0.5}[opts.modulateMode]

    clipping = [clipLow, clipHigh, -1, -1]

    if np.isclose(modHigh, modLow):
        mod = [0,  0,  0, 0]
    else:
        mod = [modLow,  modHigh, 1.0 / (modHigh - modLow), modMode]

    # Inputs which are required by both the
    # glvolume and glvetor fragment shaders
    self.shader.setFragParam('clipping', clipping)

    clipCoordXform   = self.getAuxTextureXform('clip')
    colourCoordXform = self.getAuxTextureXform('colour')
    modCoordXform    = self.getAuxTextureXform('modulate')

    self.shader.setVertParam('clipCoordXform',   clipCoordXform)
    self.shader.setVertParam('colourCoordXform', colourCoordXform)
    self.shader.setVertParam('modCoordXform',    modCoordXform)

    if useVolumeFragShader:

        voxValXform = self.colourTexture.voxValXform
        cmapXform   = self.cmapTexture.getCoordinateTransform()
        voxValXform = affine.concat(cmapXform, voxValXform)
        voxValXform = [voxValXform[0, 0], voxValXform[0, 3], 0, 0]

        self.shader.setFragParam('voxValXform', voxValXform)

        # settings expected by glvolume
        # frag shader, but not used
        self.shader.setFragParam('negCmap',  [-1, 0, 0, 0])
        self.shader.setFragParam('modulate', [0, 0, -1, 1])

    else:

        colours, colourXform = self.getVectorColours()

        # See comments in gl21/glvector_funcs.py
        if self.vectorImage.niftiDataType == constants.NIFTI_DT_RGB24:
            voxValXform = affine.scaleOffsetXform(2, -1)
        else:
            voxValXform = self.imageTexture.voxValXform

        voxValXform = [voxValXform[0, 0], voxValXform[0, 3], 0, 0]

        self.shader.setFragParam('voxValXform', voxValXform)
        self.shader.setFragParam('mod',         mod)
        self.shader.setFragParam('xColour',     colours[0])
        self.shader.setFragParam('yColour',     colours[1])
        self.shader.setFragParam('zColour',     colours[2])
        self.shader.setFragParam('colourXform', [colourXform[0, 0],
                                                 colourXform[0, 3], 0, 0])
    return True
