#!/usr/bin/env python
#
# rendertexture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL                        as gl
import OpenGL.raw.GL._types             as gltypes
import OpenGL.GL.EXT.framebuffer_object as glfbo

import                            texture
import fsl.fsleyes.gl.routines as glroutines


log = logging.getLogger(__name__)


class RenderTexture(texture.Texture2D):
    """A 2D texture and frame buffer, intended to be used as a target for
    off-screen rendering of a scene.
    """
    
    def __init__(self, name, interp=gl.GL_NEAREST):
        """

        Note that a current target must have been set for the GL context
        before a frameBuffer can be created ... in other words, call
        ``context.SetCurrent`` before creating a ``RenderTexture``).
        """

        texture.Texture2D.__init__(self, name, interp)

        self.__frameBuffer  = glfbo.glGenFramebuffersEXT(1)
        self.__renderBuffer = glfbo.glGenRenderbuffersEXT(1)
        
        log.debug('Created fbo {} and render buffer {}'.format(
            self.__frameBuffer, self.__renderBuffer))

        self.__oldSize         = None
        self.__oldProjMat      = None
        self.__oldMVMat        = None
        self.__oldFrameBuffer  = None
        self.__oldRenderBuffer = None

        
    def destroy(self):
        texture.Texture.destroy(self)

        log.debug('Deleting RB{}/FBO{}'.format(
            self.__renderBuffer,
            self.__frameBuffer))
        glfbo.glDeleteFramebuffersEXT(    gltypes.GLuint(self.__frameBuffer))
        glfbo.glDeleteRenderbuffersEXT(1, gltypes.GLuint(self.__renderBuffer))


    def setData(self, data):
        raise NotImplementedError('Texture data cannot be set for {} '
                                  'instances'.format(type(self).__name__))


    def setRenderViewport(self, xax, yax, lo, hi):

        if self.__oldSize    is not None or \
           self.__oldProjMat is not None or \
           self.__oldMVMat   is not None:
            raise RuntimeError('RenderTexture RB{}/FBO{} has already '
                               'configured the viewport'.format(
                                   self.__renderBuffer,
                                   self.__frameBuffer))

        log.debug('Configuring viewport for RB{}/FBO{}'.format(
            self.__renderBuffer,
            self.__frameBuffer))

        width, height = self.getSize()
        
        self.__oldSize    = gl.glGetIntegerv(gl.GL_VIEWPORT)
        self.__oldProjMat = gl.glGetFloatv(  gl.GL_PROJECTION_MATRIX)
        self.__oldMVMat   = gl.glGetFloatv(  gl.GL_MODELVIEW_MATRIX)

        glroutines.show2D(xax, yax, width, height, lo, hi)
            

    def restoreViewport(self):

        if self.__oldSize    is None or \
           self.__oldProjMat is None or \
           self.__oldMVMat   is None:
            raise RuntimeError('RenderTexture RB{}/FBO{} has not '
                               'configured the viewport'.format(
                                   self.__renderBuffer,
                                   self.__frameBuffer)) 

        log.debug('Clearing viewport (from RB{}/FBO{})'.format(
            self.__renderBuffer,
            self.__frameBuffer)) 

        gl.glViewport(*self.__oldSize)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(self.__oldProjMat)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(self.__oldMVMat)

        self.__oldSize    = None
        self.__oldProjMat = None
        self.__oldMVMat   = None

        
    def bindAsRenderTarget(self):

        if self.__oldFrameBuffer  is not None or \
           self.__oldRenderBuffer is not None:
            raise RuntimeError('RenderTexture RB{}/FBO{} is not bound'.format(
                self.__renderBuffer,
                self.__frameBuffer)) 
        
        self.__oldFrameBuffer  = gl.glGetIntegerv(
            glfbo.GL_FRAMEBUFFER_BINDING_EXT)
        self.__oldRenderBuffer = gl.glGetIntegerv(
            glfbo.GL_RENDERBUFFER_BINDING_EXT)

        log.debug('Setting RB{}/FBO{} as render target'.format(
            self.__renderBuffer,
            self.__frameBuffer))

        glfbo.glBindFramebufferEXT( glfbo.GL_FRAMEBUFFER_EXT,
                                    self.__frameBuffer) 
        glfbo.glBindRenderbufferEXT(glfbo.GL_RENDERBUFFER_EXT,
                                    self.__renderBuffer)


    def unbindAsRenderTarget(self):
        
        if self.__oldFrameBuffer  is None or \
           self.__oldRenderBuffer is None:
            raise RuntimeError('RenderTexture RB{}/FBO{} '
                               'has not been bound'.format(
                                   self.__renderBuffer,
                                   self.__frameBuffer)) 

        log.debug('Restoring render target to RB{}/FBO{} '
                  '(from RB{}/FBO{})'.format(
                      self.__oldRenderBuffer,
                      self.__oldFrameBuffer,
                      self.__renderBuffer,
                      self.__frameBuffer)) 

        glfbo.glBindFramebufferEXT( glfbo.GL_FRAMEBUFFER_EXT,
                                    self.__oldFrameBuffer)
        glfbo.glBindRenderbufferEXT(glfbo.GL_RENDERBUFFER_EXT, 
                                    self.__oldRenderBuffer)

        self.__oldFrameBuffer  = None
        self.__oldRenderBuffer = None

        
    def refresh(self):
        texture.Texture2D.refresh(self)

        width, height = self.getSize()

        # Configure the frame buffer
        self.bindTexture()
        self.bindAsRenderTarget()
        glfbo.glFramebufferTexture2DEXT(
            glfbo.GL_FRAMEBUFFER_EXT,
            glfbo.GL_COLOR_ATTACHMENT0_EXT,
            gl   .GL_TEXTURE_2D,
            self.getTextureHandle(),
            0)

        # and the render buffer
        glfbo.glRenderbufferStorageEXT(
            glfbo.GL_RENDERBUFFER_EXT,
            gl.GL_DEPTH24_STENCIL8,
            width,
            height)

        glfbo.glFramebufferRenderbufferEXT(
            glfbo.GL_FRAMEBUFFER_EXT,
            gl.GL_DEPTH_STENCIL_ATTACHMENT,
            glfbo.GL_RENDERBUFFER_EXT,
            self.__renderBuffer)
            
        if glfbo.glCheckFramebufferStatusEXT(glfbo.GL_FRAMEBUFFER_EXT) != \
           glfbo.GL_FRAMEBUFFER_COMPLETE_EXT:
            self.unbindAsRenderTarget()
            self.unbindTexture()            
            raise RuntimeError('An error has occurred while '
                               'configuring the frame buffer')

        self.unbindAsRenderTarget()
        self.unbindTexture()

        
class GLObjectRenderTexture(RenderTexture):
    
    def __init__(self, name, globj, xax, yax, maxResolution=1024):
        """
        """
        
        self.__globj         = globj
        self.__xax           = xax
        self.__yax           = yax
        self.__maxResolution = maxResolution

        RenderTexture.__init__(self, name)

        name = '{}_{}'.format(self.getTextureName(), id(self))
        globj.addUpdateListener(name, self.__updateSize)

        self.__updateSize()        

    
    def setAxes(self, xax, yax):
        self.__xax = xax
        self.__yax = yax
        self.__updateSize()

        
    def destroy(self):

        name = '{}_{}'.format(self.getTextureName(), id(self))
        self.__globj.removeUpdateListener(name) 
        RenderTexture.destroy(self)

    
    def setSize(self, width, height):
        raise NotImplementedError(
            'Texture size cannot be set for {} instances'.format(
                type(self).__name__))
        
        
    def __updateSize(self, *a):
        globj  = self.__globj
        maxRes = self.__maxResolution

        resolution = globj.getDataResolution(self.__xax, self.__yax)

        if resolution is None:
            resolution = [256, 256, 256]
            log.debug('Using default resolution '
                      'for GLObject {}'.format(type(globj).__name__))

        width  = resolution[self.__xax]
        height = resolution[self.__yax]

        if any((width <= 0, height <= 0)):
            raise ValueError('Invalid GLObject resolution: {}'.format(
                (width, height)))

        if width > maxRes or height > maxRes:
            oldWidth, oldHeight = width, height
            ratio = min(width, height) / float(max(width, height))

            if width > height:
                width  = maxRes
                height = width * ratio
            else:
                height = maxRes
                width  = height * ratio

            width  = int(round(width))
            height = int(round(height))

            log.debug('Limiting texture resolution to {}x{} '
                      '(for {} resolution {}x{})'.format(
                          width,
                          height,
                          type(globj).__name__,
                          oldWidth,
                          oldHeight))

        RenderTexture.setSize(self, width, height) 
