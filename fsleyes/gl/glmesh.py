#!/usr/bin/env python
#
# glmesh.py - The GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLMesh` class, a :class:`.GLObject` used
to render :class:`.TriangleMesh` overlays.
"""


import numpy        as np
import numpy.linalg as npla
import OpenGL.GL    as gl

from . import                 globject
import fsl.utils.transform as transform
import fsleyes.gl          as fslgl
import fsleyes.gl.routines as glroutines
import fsleyes.gl.textures as textures
import fsleyes.colourmaps  as fslcmaps


class GLMesh(globject.GLObject):
    """The ``GLMesh`` class is a :class:`.GLObject` which encapsulates the
    logic required to render 2D slices of a :class:`.TriangleMesh` overlay.
    The ``GLMesh`` class assumes that the :class:`.Display` instance
    associated with the ``TriangleMesh`` overlay holds a reference to a
    :class:`.MeshOpts` instance, which contains ``GLMesh`` specific
    display settings.

    
    The ``GLMesh`` renders cross-sections of a ``TriangleMesh`` overlay using
    a three-pass technique, roughly following that described at 
    http://glbook.gamedev.net/GLBOOK/glbook.gamedev.net/moglgp/advclip.html:

    
    1. The front face of the mesh is rendered to the stencil buffer.

    2. The back face is rendered to the stencil buffer,  and subtracted
       from the front face.

    3. This intersection (of the mesh with a plane at the slice Z location)
       is then rendered to the canvas.


    The ``GLMesh`` class has the ability to draw the mesh with a fill
    colour, or to draw only the mesh outline. To accomplish this, in step 3
    above, the intersection mask is actually drawn to an off-screen
    :class:`.RenderTexture`. If outline mode (controlled by the
    :attr:`.MeshOpts.outline` property) is enabled, an edge-detection shader
    program is run on this off-screen texture. Then, the texture is rendered
    to the canvas. If outline mode is disabled, the shader programs are not
    executed.


    The ``GLMesh`` class makes use of two OpenGL version-specific modules,
    :mod:`.gl14.glmesh_funcs`, and :mod:`.gl21.glmesh_funcs`. These version
    specific modules must provide the following functions:

    ========================== ======================================
    ``destroy(GLMesh)``        Performs any necessary clean up.
    ``compileShaders(GLMesh)`` Compiles vertex/fragment shaders.
    ``updateShaders(GLMesh)``  Updates vertex/fragment shader states.
    ``loadShaders(GLMesh)``    Loads vertex/fragment shaders.
    ``unloadShaders(GLMesh)``  Unloads vertex/fragment shaders.
    ========================== ======================================
    """

    
    def __init__(self, overlay, display, xax, yax):
        """Create a ``GLMesh``.

        :arg overlay: A :class:`.TriangleMesh` overlay.

        :arg display: A :class:`.Display` instance defining how the
                      ``overlay`` is to be displayed.
        
        :arg xax:     Initial display X axis

        :arg yax:     Initial display Y axis        
        """

        globject.GLObject.__init__(self, xax, yax)

        self.shader  = None
        self.overlay = overlay
        self.display = display
        self.opts    = display.getDisplayOpts()

        self.addListeners()
        self._updateVertices()

        self._renderTexture = textures.RenderTexture(self.name, gl.GL_NEAREST)

        fslgl.glmesh_funcs.compileShaders(self)

        
    def destroy(self):
        """Must be called when this ``GLMesh`` is no longer needed. Removes
        some property listeners and destroys the off-screen
        :class:`.RenderTexture`.
        """
        self._renderTexture.destroy()
        fslgl.glmesh_funcs.destroy(self)
        self.removeListeners()
        
        self.overlay = None
        self.display = None
        self.opts    = None

        
    def ready(self):
        """Overrides :meth:`.GLObject.ready`. Always returns ``True``. """
        return True

        
    def addListeners(self):
        """Called by :meth:`__init__`. Adds some property listeners to the
        :class:`.Display` and :class:`.MeshOpts` instances so the OpenGL
        representation can be updated when the display properties are changed..
        """

        name    = self.name
        display = self.display
        opts    = self.opts

        def refresh(*a):
            self.notify()

        opts   .addListener('bounds',       name, self._updateVertices)
        opts   .addListener('colour',       name, refresh, weak=False)
        opts   .addListener('outline',      name, refresh, weak=False)
        opts   .addListener('showName',     name, refresh, weak=False)
        opts   .addListener('outlineWidth', name, refresh, weak=False)
        opts   .addListener('quality',      name, refresh, weak=False) 
        display.addListener('brightness',   name, refresh, weak=False)
        display.addListener('contrast',     name, refresh, weak=False)
        display.addListener('alpha',        name, refresh, weak=False)

        
    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all of the listeners added by
        the :meth:`addListeners` method.
        """
        self.opts   .removeListener('bounds',       self.name)
        self.opts   .removeListener('colour',       self.name)
        self.opts   .removeListener('outline',      self.name)
        self.opts   .removeListener('outlineWidth', self.name)
        self.opts   .removeListener('quality',      self.name)
        self.display.removeListener('brightness',   self.name)
        self.display.removeListener('contrast',     self.name)
        self.display.removeListener('alpha',        self.name)

 
    def setAxes(self, xax, yax):
        """Overrides :meth:`.GLObject.setAxes`. Calls the base class
        implementation, and calls :meth:`.GLObjectRenderTexture.setAxes`
        on the off-screen texture.
        """
        globject.GLObject.setAxes(self, xax, yax)


    def _updateVertices(self, *a):
        """Called by :meth:`__init__`, and when certain display properties
        change. (Re-)generates the mesh vertices and indices. They are stored
        as attributes called ``vertices`` and ``indices`` respectively.
        """

        vertices = self.overlay.vertices
        indices  = self.overlay.indices
        xform    = self.opts.getCoordSpaceTransform()

        if not np.all(xform == np.eye(4)):
            vertices = transform.transform(vertices, xform)

        self.vertices = np.array(vertices,          dtype=np.float32)
        self.indices  = np.array(indices.flatten(), dtype=np.uint32)
        self.notify()

        
    def getDisplayBounds(self):
        """Overrides :meth:`.GLObject.getDisplayBounds`. Returns a bounding
        box which contains the mesh vertices. 
        """
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi()) 

    
    def getDataResolution(self, xax, yax):
        """Overrides :meth:`.GLObject.getDataResolution`. Returns a 
        resolution (in pixels), along each display coordinate system axis,
        suitable for drawing this ``GLMesh``.
        """

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

        xMeshLen = abs(hi[xax] - lo[xax])
        yMeshLen = abs(hi[yax] - lo[yax])
        zMeshLen = abs(hi[zax] - lo[zax])

        resolution      = [1, 1, 1]
        resolution[xax] = int(round(2048.0 * xMeshLen / xDisplayLen))
        resolution[yax] = int(round(2048.0 * yMeshLen / yDisplayLen))
        resolution[zax] = int(round(2048.0 * zMeshLen / zDisplayLen))
        
        return resolution
        
        
    def getOutlineOffsets(self):
        """Returns an array containing two values, which are to be used as the
        outline widths along the horizontal/vertical screen axes (if outline
        mode is being used). The values are in display coordinate system units.

        .. note:: This method is used by the :mod:`.gl14.glmesh_funcs` and
                  :mod:`.gl21.glmesh_funcs` modules.
        """
        opts          = self.opts
        width, height = self._renderTexture.getSize()
        outlineWidth  = opts.outlineWidth * (opts.quality / 100.0)

        if width in (None, 0) or height in (None, 0):
            return [0, 0]

        # outlineWidth is a value between 0.0 and 1.0 - 
        # we use this value so that it effectly sets the
        # outline to between 0% and 10% of the mesh
        # width/height (whichever is smaller)
        offsets = [outlineWidth / width, outlineWidth / height]
        offsets = np.array(offsets, dtype=np.float32)

        return offsets
 

    def preDraw(self):
        """Overrides :meth:`.GLObject.preDraw`. Sets the size of the backing
        :class:`.RenderTexture` based on the current viewport size.
        """

        quality = self.opts.quality / 100.0
        size    = gl.glGetIntegerv(gl.GL_VIEWPORT)
        width   = int(round(size[2] * quality))
        height  = int(round(size[3] * quality))

        self._renderTexture.setSize(width, height)
        fslgl.glmesh_funcs.updateShaders(self)

    
    def draw(self, zpos, xform=None, bbox=None):
        """Overrids :meth:`.GLObject.draw`. Draws a 2D slice of the
        :class:`.TriangleMesh`, at the specified Z location.
        """

        display  = self.display 
        opts     = self.opts

        xax      = self.xax
        yax      = self.yax
        zax      = self.zax

        vertices = self.vertices
        indices  = self.indices
        lo,  hi  = self.getDisplayBounds()

        if zpos < lo[zax] or zpos > hi[zax]:
            return

        self._renderTexture.bindAsRenderTarget()
        lo, hi = self.__setRenderTextureViewport(lo, hi, bbox)
        xmin   = lo[xax]
        ymin   = lo[yax]
        xmax   = hi[xax]
        ymax   = hi[yax]

        # Figure out the equation of a plane
        # perpendicular to the Z axis, and
        # located at the z position. This is
        # used as a clipping plane to draw 
        # the mesh intersection.
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
        # intersection of the mesh with the clipping
        # plane.
        gl.glStencilFunc(gl.GL_ALWAYS, 0, 0)

        # If the mesh coordinate transformation
        # has a positive determinant, we need to
        # render the back faces first, otherwise
        # the cross-section mask will not be
        # created correctly. Something to do with
        # the vertex unwinding order, I guess.
        direction = [gl.GL_INCR, gl.GL_DECR]
        
        if npla.det(opts.getCoordSpaceTransform()) > 0:
            faceOrder = [gl.GL_BACK,  gl.GL_FRONT]
        else:
            faceOrder = [gl.GL_FRONT, gl.GL_BACK]

        for face, direction in zip(faceOrder, direction):
            
            gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, direction)
            gl.glCullFace(face)

            gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
            gl.glDrawElements(gl.GL_TRIANGLES,
                              len(indices),
                              gl.GL_UNSIGNED_INT,
                              indices)

        # Third pass - render the intersection
        # of the front and back faces from the
        # stencil buffer to the render texture.
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

        # If drawing the mesh outline, run the
        # render texture through the shader
        # programs. Otherwise, the render texture
        # is just drawn directly to the canvas.
        if opts.outline:
            fslgl.glmesh_funcs.loadShaders(self)

        self._renderTexture.drawOnBounds(
            zpos, xmin, xmax, ymin, ymax, xax, yax, xform)
        
        if opts.outline:
            fslgl.glmesh_funcs.unloadShaders(self)

    
    def postDraw(self):
        """Overrides :meth:`.GLObject.postDraw`. This method does nothing. """
        pass


    def __setRenderTextureViewport(self, lo, hi, bbox=None):
        """Called by :meth:`draw`. Calculates an appropriate viewport (the
        horizontal/vertical minimums/maximums in display coordinates) given
        the ``lo`` and ``hi`` ``GLMesh`` display bounds, and a display
        ``bbox``.

        Sets the viewport on the :class:`.RenderTexture`, and returns the
        bounds.
        """

        xax = self.xax
        yax = self.yax

        if bbox is not None and (lo[xax] < bbox[xax][0] or
                                 hi[xax] < bbox[xax][1] or
                                 lo[yax] > bbox[yax][0] or
                                 hi[yax] > bbox[yax][1]):

            xlen  = float(hi[xax] - lo[xax])
            ylen  = float(hi[yax] - lo[yax])
            ratio = xlen / ylen
            
            bblo = [ax[0] for ax in bbox]
            bbhi = [ax[1] for ax in bbox]

            lo   = [max(l, bbl) for l, bbl in zip(lo, bblo)]
            hi   = [min(h, bbh) for h, bbh in zip(hi, bbhi)]

            dxlen  = float(hi[xax] - lo[xax])
            dylen  = float(hi[yax] - lo[yax])
            
            dratio = dxlen / dylen

            if dratio > ratio:

                ndxlen   = xlen * (dylen / ylen)
                lo[xax] += 0.5 * (ndxlen - dxlen)
                hi[xax] -= 0.5 * (ndxlen - dxlen)

            elif dratio < ratio:

                ndylen   = ylen * (dxlen / xlen)
                lo[yax] += 0.5 * (ndylen - dylen)
                hi[yax] -= 0.5 * (ndylen - dylen)

        self._renderTexture.setRenderViewport(xax, yax, lo, hi)
        
        return lo, hi
