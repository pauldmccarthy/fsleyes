#!/usr/bin/env python
#
# gllabel.py - OpenGL representation for label/atlas images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import OpenGL.GL      as gl

import fsl.fsleyes.gl as fslgl
import resources      as glresources
import                   globject
import                   textures


class GLLabel(globject.GLImageObject):

    
    def __init__(self, image, display):

        globject.GLImageObject.__init__(self, image, display)

        lutTexName   = '{}_lut'.format(self.name)

        self.lutTexture   = textures.LookupTableTexture(lutTexName)
        self.imageTexture = None

        self.refreshImageTexture()
        self.refreshLutTexture()
 
        fslgl.gllabel_funcs.init(self)
        self.addListeners()

        
    def destroy(self):

        glresources.delete(self.imageTexture.getTextureName())
        self.lutTexture.destroy()

        self.removeListeners()
        fslgl.gllabel_funcs.destroy(self)
        globject.GLImageObject.destroy(self)


    def addListeners(self):

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        def shaderUpdate(*a):
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate()
            
        def shaderCompile(*a):
            fslgl.gllabel_funcs.compileShaders(self)
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate() 

        def lutUpdate(*a):
            self.refreshLutTexture()
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate()

        def lutChanged(*a):
            if self.__lut is not None:
                self.__lut.removeListener('labels', self.name)
                
            self.__lut = opts.lut

            if self.__lut is not None:
                self.__lut.addListener('labels', self.name, lutUpdate)
 
            lutUpdate()

        def imageRefresh(*a):
            self.refreshImageTexture()
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate()
            
        def imageUpdate(*a):
            self.imageTexture.set(volume=opts.volume,
                                  resolution=opts.resolution)
            
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate() 

        self.__lut = opts.lut

        # TODO If you add a software shader, you will
        #      need to call gllabel_funcs.compileShaders
        #      when display.softwareMode changes

        display .addListener('alpha',        name, lutUpdate,     weak=False)
        display .addListener('brightness',   name, lutUpdate,     weak=False)
        display .addListener('contrast',     name, lutUpdate,     weak=False)
        display .addListener('softwareMode', name, shaderCompile, weak=False)
        opts    .addListener('outline',      name, shaderUpdate,  weak=False)
        opts    .addListener('outlineWidth', name, shaderUpdate,  weak=False)
        opts    .addListener('lut',          name, lutChanged,    weak=False)
        opts    .addListener('volume',       name, imageUpdate,   weak=False)
        opts    .addListener('resolution',   name, imageUpdate,   weak=False)
        opts.lut.addListener('labels',       name, lutUpdate,     weak=False)

        if opts.getParent() is not None:
            opts.addSyncChangeListener(
                'volume',     name, imageRefresh, weak=False)
            opts.addSyncChangeListener(
                'resolution', name, imageRefresh, weak=False)


    def removeListeners(self):
        display = self.display
        opts    = self.displayOpts
        name    = self.name

        display .removeListener(          'alpha',        name)
        display .removeListener(          'brightness',   name)
        display .removeListener(          'contrast',     name)
        display .removeListener(          'softwareMode', name)
        opts    .removeListener(          'outline',      name)
        opts    .removeListener(          'outlineWidth', name)
        opts    .removeListener(          'lut',          name)
        opts    .removeListener(          'volume',       name)
        opts    .removeListener(          'resolution',   name)
        opts.lut.removeListener(          'labels',       name)

        if opts.getParent() is not None:
            opts.removeSyncChangeListener('volume',     name)
            opts.removeSyncChangeListener('resolution', name)


        
    def setAxes(self, xax, yax):
        """Overrides :meth:`.GLImageObject.setAxes`.
        """
        globject.GLImageObject.setAxes(self, xax, yax)
        fslgl.gllabel_funcs.updateShaderState(self)


    def refreshImageTexture(self):
        
        opts     = self.displayOpts
        texName  = '{}_{}' .format(type(self).__name__, id(self.image))

        unsynced = (opts.getParent() is None            or
                    not opts.isSyncedToParent('volume') or
                    not opts.isSyncedToParent('resolution'))

        if unsynced:
            texName = '{}_unsync_{}'.format(texName, id(opts))

        if self.imageTexture is not None:
            glresources.delete(self.imageTexture.getTextureName())
            
        self.imageTexture = glresources.get(
            texName, 
            textures.ImageTexture,
            texName,
            self.image) 


    def refreshLutTexture(self, *a):

        display = self.display
        opts    = self.displayOpts

        self.lutTexture.set(alpha=display.alpha           / 100.0,
                            brightness=display.brightness / 100.0,
                            contrast=display.contrast     / 100.0,
                            lut=opts.lut)
        
    def preDraw(self):

        self.imageTexture.bindTexture(gl.GL_TEXTURE0)
        self.lutTexture  .bindTexture(gl.GL_TEXTURE1)
        fslgl.gllabel_funcs.preDraw(self)

    
    def draw(self, zpos, xform=None):
        fslgl.gllabel_funcs.draw(self, zpos, xform)


    def postDraw(self):
        self.imageTexture.unbindTexture()
        self.lutTexture  .unbindTexture()
        fslgl.gllabel_funcs.postDraw(self)
