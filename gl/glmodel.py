#!/usr/bin/env python
#
# glmodel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy     as np
import OpenGL.GL as gl

import                            globject
import fsl.utils.transform     as transform
import fsl.fsleyes.gl          as fslgl
import fsl.fsleyes.gl.routines as glroutines
import fsl.fsleyes.gl.textures as textures
import fsl.fsleyes.colourmaps  as fslcmaps


class GLModel(globject.GLObject):

    def __init__(self, overlay, display):

        globject.GLObject.__init__(self)

        self.overlay = overlay
        self.display = display
        self.opts    = display.getDisplayOpts()

        self.addListeners()
        self._updateVertices()

        self._renderTexture = textures.GLObjectRenderTexture(
            self.name, self, 0, 1)
        self._renderTexture.setInterpolation(gl.GL_LINEAR)

        fslgl.glmodel_funcs.compileShaders(self)
        fslgl.glmodel_funcs.updateShaders( self)

        
    def destroy(self):
        self._renderTexture.destroy()
        fslgl.glmodel_funcs.destroy(self)
        self.removeListeners()
        
        self.overlay = None
        self.display = None
        self.opts    = None

        
    def addListeners(self):

        name    = self.name
        display = self.display
        opts    = self.opts

        def refresh(*a):
            self.onUpdate()

        def shaderUpdate(*a):
            fslgl.glmodel_funcs.updateShaders(self)
            self.onUpdate()
        
        opts   .addListener('refImage',     name, self._updateVertices)
        opts   .addListener('coordSpace',   name, self._updateVertices)
        opts   .addListener('transform',    name, self._updateVertices)
        opts   .addListener('colour',       name, refresh,      weak=False)
        opts   .addListener('outline',      name, refresh,      weak=False)
        opts   .addListener('showName',     name, refresh,      weak=False)
        display.addListener('brightness',   name, refresh,      weak=False)
        display.addListener('contrast',     name, refresh,      weak=False)
        display.addListener('alpha',        name, refresh,      weak=False)
        opts   .addListener('outlineWidth', name, shaderUpdate, weak=False)

        
    def removeListeners(self):
        self.opts   .removeListener('refImage',     self.name)
        self.opts   .removeListener('coordSpace',   self.name)
        self.opts   .removeListener('transform',    self.name)
        self.opts   .removeListener('colour',       self.name)
        self.opts   .removeListener('outline',      self.name)
        self.opts   .removeListener('outlineWidth', self.name)
        self.display.removeListener('brightness',   self.name)
        self.display.removeListener('contrast',     self.name)
        self.display.removeListener('alpha',        self.name)


    def _updateVertices(self, *a):

        vertices = self.overlay.vertices
        indices  = self.overlay.indices

        xform = self.opts.getCoordSpaceTransform()

        if xform is not None:
            vertices = transform.transform(vertices, xform)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices  = np.array(indices,  dtype=np.uint32)
        self.onUpdate()

        
    def getDisplayBounds(self):
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi()) 

    
    def getDataResolution(self, xax, yax):

        # TODO How can I have this resolution tied
        # to the rendering target resolution (i.e.
        # the screen), instead of being fixed?
        # 
        # Perhaps the DisplayContext class should 
        # have a method which returns the current
        # rendering resolution for a given display
        # space axis/length ..
        #
        # Also, isn't it a bit dodgy to be accessing
        # the DisplayContext instance through the
        # DisplayOpts instance? Why not just pass
        # the displayCtx instance to the GLObject
        # constructor, and have it directly accessible
        # by all GLobjects?

        zax = 3 - xax - yax

        xDisplayLen = self.opts.displayCtx.bounds.getLen(xax)
        yDisplayLen = self.opts.displayCtx.bounds.getLen(yax)
        zDisplayLen = self.opts.displayCtx.bounds.getLen(zax)

        lo, hi = self.getDisplayBounds()

        xModelLen = abs(hi[xax] - lo[xax])
        yModelLen = abs(hi[yax] - lo[yax])
        zModelLen = abs(hi[zax] - lo[zax])

        resolution      = [1, 1, 1]
        resolution[xax] = int(round(2048.0 * xModelLen / xDisplayLen))
        resolution[yax] = int(round(2048.0 * yModelLen / yDisplayLen))
        resolution[zax] = int(round(2048.0 * zModelLen / zDisplayLen))
        
        return resolution
        
    
    def setAxes(self, xax, yax):
        globject.GLObject.setAxes(self, xax, yax)
        self._renderTexture.setAxes(xax, yax)

        
    def getOutlineOffsets(self):
        """Used by the :mod:`glmodel_funcs` modules.
        """
        width, height = self._renderTexture.getSize()
        outlineWidth  = self.opts.outlineWidth

        # outlineWidth is a value between 0.0 and 1.0 - 
        # we use this value so that it effectly sets the
        # outline to between 0% and 10% of the model
        # width/height (whichever is smaller)
        outlineWidth *= 10
        offsets = 2 * [min(outlineWidth / width, outlineWidth / height)]
        offsets = np.array(offsets, dtype=np.float32) 
        return offsets
 

    def preDraw(self):
        pass

    
    def draw(self, zpos, xform=None):

        display = self.display 
        opts    = self.opts

        xax = self.xax
        yax = self.yax
        zax = self.zax

        vertices = self.vertices
        indices  = self.indices

        lo, hi = self.getDisplayBounds()

        xmin = lo[xax]
        ymin = lo[yax]
        zmin = lo[zax]
        xmax = hi[xax]
        ymax = hi[yax]
        zmax = hi[zax]

        if zpos < zmin or zpos > zmax:
            return

        clipPlaneVerts                = np.zeros((4, 3), dtype=np.float32)
        clipPlaneVerts[0, [xax, yax]] = [xmin, ymin]
        clipPlaneVerts[1, [xax, yax]] = [xmin, ymax]
        clipPlaneVerts[2, [xax, yax]] = [xmax, ymax]
        clipPlaneVerts[3, [xax, yax]] = [xmax, ymin]
        clipPlaneVerts[:,  zax]       =  zpos

        vertices = vertices.ravel('C')
        planeEq  = glroutines.planeEquation(clipPlaneVerts[0, :],
                                            clipPlaneVerts[1, :],
                                            clipPlaneVerts[2, :])

        self._renderTexture.bindAsRenderTarget()
        self._renderTexture.setRenderViewport(xax, yax, lo, hi)

        gl.glClearColor(0, 0, 0, 0)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
        gl.glClear(gl.GL_STENCIL_BUFFER_BIT)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnable(gl.GL_CLIP_PLANE0)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_STENCIL_TEST)

        gl.glClipPlane(gl.GL_CLIP_PLANE0, planeEq)
        gl.glColorMask(gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE)

        # First and second passes - render front and
        # back faces separately. In the stencil buffer,
        # subtract the mask created by the second
        # render from the mask created by the first -
        # this gives us a mask which shows the
        # intersection of the model with the clipping
        # plane.
        gl.glStencilFunc(gl.GL_ALWAYS, 0, 0)

        # I don't understand why, but if any of the
        # display system axes are inverted, we need
        # to render the back faces first, otherwise
        # the cross-section mask will not be created
        # correctly.
        direction = [gl.GL_INCR, gl.GL_DECR]

        if np.any(np.array(hi) < 0.0): faceOrder = [gl.GL_FRONT, gl.GL_BACK]
        else:                          faceOrder = [gl.GL_BACK,  gl.GL_FRONT]
        
        for face, direction in zip(faceOrder, direction):
            
            gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, direction)
            gl.glCullFace(face)

            gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
            gl.glDrawElements(gl.GL_TRIANGLES,
                              len(indices),
                              gl.GL_UNSIGNED_INT,
                              indices)

        # third pass - render the intersection
        # of the front and back faces from the
        # stencil buffer to the render texture
        gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE)

        gl.glDisable(gl.GL_CLIP_PLANE0)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        gl.glStencilFunc(gl.GL_NOTEQUAL, 0, 255)

        colour = list(fslcmaps.applyBricon(
            opts.colour[:3],
            display.brightness / 100.0,
            display.contrast   / 100.0))
        
        colour.append(display.alpha / 100.0)

        gl.glColor(*colour)
        gl.glBegin(gl.GL_QUADS)

        gl.glVertex3f(*clipPlaneVerts[0, :])
        gl.glVertex3f(*clipPlaneVerts[1, :])
        gl.glVertex3f(*clipPlaneVerts[2, :])
        gl.glVertex3f(*clipPlaneVerts[3, :])
        gl.glEnd()

        gl.glDisable(gl.GL_STENCIL_TEST)

        self._renderTexture.unbindAsRenderTarget()
        self._renderTexture.restoreViewport()

        if opts.outline:
            fslgl.glmodel_funcs.loadShaders(self)

        self._renderTexture.drawOnBounds(
            zpos, xmin, xmax, ymin, ymax, xax, yax, xform)
        
        if opts.outline:
            fslgl.glmodel_funcs.unloadShaders(self)

    
    def postDraw(self):
        pass
