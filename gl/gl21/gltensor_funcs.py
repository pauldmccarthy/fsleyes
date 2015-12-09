#!/usr/bin/env python
#
# gltensor_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL                as gl

import fsl.fsleyes.gl           as fslgl
import fsl.fsleyes.gl.resources as glresources
import fsl.fsleyes.gl.textures  as textures
import fsl.fsleyes.gl.shaders   as shaders


log = logging.getLogger(__name__)


def init(self):


    image = self.image

    v1 = image.V1()
    v2 = image.V2()
    v3 = image.V3()
    l1 = image.L1()
    l2 = image.L2()
    l3 = image.L3()


    def vPrefilter(d):
        return d.transpose((3, 0, 1, 2))

    names = ['v1', 'v2', 'v3', 'l1', 'l2', 'l3']
    imgs  = [ v1,   v2,   v3,   l1,   l2,   l3]

    for  name, img in zip(names, imgs):
        texName = '{}_{}'.format(type(self).__name__, id(img))

        if name[0] == 'v':
            prefilter = vPrefilter
            nvals     = 3
        else:
            prefilter = None
            nvals     = 1
        
        tex = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            img,
            nvals=nvals,
            normalise=True,
            prefilter=prefilter)

        setattr(self, '{}Texture'.format(name), tex)


    self.shaders = None

    compileShaders(self)


def destroy(self):
    pass


def compileShaders(self):
    if self.shaders is not None:
        gl.glDeleteProgram(self.shaders)

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)


def updateShaderState(self):
    pass


def preDraw(self):
    pass


def draw(self, zpos, xform=None):
    pass


def postDraw(self):
    pass
