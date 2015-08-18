#!/usr/bin/env python
#
# rendertexturelist.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.fsleyes.gl.routines as glroutines
import fsl.utils.transform     as transform
import                            rendertexture


log = logging.getLogger(__name__)


class RenderTextureStack(object):

    def __init__(self, globj):


        self.name = '{}_{}_{}'.format(
            type(self).__name__,
            type(globj).__name__, id(self))

        self.__globj              = globj
        self.__maxNumTextures     = 256
        self.__maxWidth           = 1024
        self.__maxHeight          = 1024
        self.__defaultNumTextures = 64
        self.__defaultWidth       = 256
        self.__defaultHeight      = 256

        self.__textureDirty       = []
        self.__textures           = []

        self.__lastDrawnTexture   = None
        self.__updateQueue        = []

        self.__globj.addUpdateListener(
            '{}_{}'.format(type(self).__name__, id(self)),
            self.__refreshAllTextures)

        import wx
        wx.GetApp().Bind(wx.EVT_IDLE, self.__textureUpdateLoop)

            
    def __refreshAllTextures(self, *a):

        if self.__lastDrawnTexture is not None:
            lastIdx = self.__lastDrawnTexture
        else:
            lastIdx = len(self.__textures) / 2
            
        aboveIdxs = range(lastIdx, len(self.__textures))
        belowIdxs = range(lastIdx, 0, -1)

        idxs = [0] * len(self.__textures)

        for i in range(len(self.__textures)):
            
            if len(aboveIdxs) > 0 and len(belowIdxs) > 0:
                if i % 2: idxs[i] = aboveIdxs.pop(0)
                else:     idxs[i] = belowIdxs.pop(0)
                
            elif len(aboveIdxs) > 0: idxs[i] = aboveIdxs.pop(0)
            else:                    idxs[i] = belowIdxs.pop(0) 

        self.__textureDirty = [True] * len(self.__textures)
        self.__updateQueue  = idxs


    def __zposToIndex(self, zpos):
        zmin  = self.__zmin
        zmax  = self.__zmax
        ntexs = len(self.__textures)
        index = ntexs * (zpos - zmin) / (zmax - zmin)

        limit = len(self.__textures) - 1

        if index > limit and index <= limit + 1:
            index = limit

        return int(index)

    
    def __indexToZpos(self, index):
        zmin  = self.__zmin
        zmax  = self.__zmax
        ntexs = len(self.__textures)
        return index * (zmax - zmin) / ntexs + zmin


    def __textureUpdateLoop(self, ev):
        ev.Skip()

        if len(self.__updateQueue) == 0 or len(self.__textures) == 0:
            return

        idx = self.__updateQueue.pop(0)

        if not self.__textureDirty[idx]:
            return

        tex = self.__textures[idx]
        
        log.debug('Refreshing texture slice {} (zax {})'.format(
            idx, self.__zax))
        
        self.__refreshTexture(tex, idx)

        if len(self.__updateQueue) > 0:
            ev.RequestMore()

            
    def getGLObject(self):
        return self.__globj

    
    def setAxes(self, xax, yax):

        zax        = 3 - xax - yax
        self.__xax = xax
        self.__yax = yax
        self.__zax = zax

        lo, hi = self.__globj.getDisplayBounds()
        res    = self.__globj.getDataResolution(xax, yax)

        if res is not None: numTextures = res[zax]
        else:               numTextures = self.__defaultNumTextures

        if numTextures > self.__maxNumTextures:
            numTextures = self.__maxNumTextures

        self.__zmin = lo[zax]
        self.__zmax = hi[zax]

        self.__destroyTextures()
        
        for i in range(numTextures):
            self.__textures.append(
                rendertexture.RenderTexture('{}_{}'.format(self.name, i)))

        self.__textureDirty = [True] * numTextures
        self.__refreshAllTextures()

        
    def __destroyTextures(self):

        import wx
        texes = self.__textures
        self.__textures = []
        for tex in texes:
            wx.CallLater(50, tex.destroy)
        
    
    def destroy(self):
        self.__destroyTextures()


    def __refreshTexture(self, tex, idx):

        zpos = self.__indexToZpos(idx)
        xax  = self.__xax
        yax  = self.__yax

        lo, hi = self.__globj.getDisplayBounds()
        res    = self.__globj.getDataResolution(xax, yax)

        if res is not None:
            width  = res[xax]
            height = res[yax]
        else:
            width  = self.__defaultWidth
            height = self.__defaultHeight

        if width  > self.__maxWidth:  width  = self.__maxWidth
        if height > self.__maxHeight: height = self.__maxHeight

        log.debug('Refreshing render texture for slice {} (zpos {}, '
                  'zax {}): {} x {}'.format(idx, zpos, self.__zax,
                                            width, height))

        tex.setSize(width, height)

        oldSize       = gl.glGetIntegerv(gl.GL_VIEWPORT)
        oldProjMat    = gl.glGetFloatv(  gl.GL_PROJECTION_MATRIX)
        oldMVMat      = gl.glGetFloatv(  gl.GL_MODELVIEW_MATRIX)

        glroutines.show2D(xax, yax, width, height, lo, hi)

        tex.bindAsRenderTarget()
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.__globj.preDraw()
        self.__globj.draw(zpos)
        self.__globj.postDraw()
        tex.unbindAsRenderTarget()
        
        gl.glViewport(*oldSize)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(oldProjMat)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(oldMVMat)

        self.__textureDirty[idx] = False

    
    def draw(self, zpos, xform=None):

        xax     = self.__xax
        yax     = self.__yax
        zax     = self.__zax

        texIdx                  = self.__zposToIndex(zpos)
        self.__lastDrawnTexture = texIdx

        if texIdx < 0 or texIdx >= len(self.__textures):
            return

        lo, hi  = self.__globj.getDisplayBounds()
        texture = self.__textures[texIdx]

        if self.__textureDirty[texIdx]:
            self.__refreshTexture(texture, texIdx)

        vertices = np.zeros((6, 3), dtype=np.float32)
        vertices[:, zax] = zpos
        vertices[0, [xax, yax]] = lo[xax], lo[yax]
        vertices[1, [xax, yax]] = lo[xax], hi[yax]
        vertices[2, [xax, yax]] = hi[xax], lo[yax]
        vertices[3, [xax, yax]] = hi[xax], lo[yax]
        vertices[4, [xax, yax]] = lo[xax], hi[yax]
        vertices[5, [xax, yax]] = hi[xax], hi[yax]

        if xform is not None:
            vertices = transform.transform(vertices, xform=xform)

        texture.draw(vertices)
