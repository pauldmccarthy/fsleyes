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
import fsleyes.gl.trimesh  as trimesh
import fsleyes.gl.routines as glroutines
import fsleyes.gl.textures as textures
import fsleyes.colourmaps  as fslcmaps

import OpenGL.GL.ARB.draw_instanced as arbdi


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
        self.updateVertices()

        # We use a render texture when
        # rendering model cross sections.
        # This texture is kept at display/
        # screen resolution
        self.renderTexture = textures.RenderTexture(self.name, gl.GL_NEAREST)

        fslgl.glmesh_funcs.compileShaders(self)

        
    def destroy(self):
        """Must be called when this ``GLMesh`` is no longer needed. Removes
        some property listeners and destroys the off-screen
        :class:`.RenderTexture`.
        """

        self.renderTexture.destroy()
        fslgl.glmesh_funcs.destroy(self)
        self.removeListeners()

        self.renderTexture = None
        self.overlay       = None
        self.display       = None
        self.opts          = None

        
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

        opts   .addListener('bounds',       name, self.updateVertices)
        opts   .addListener('colour',       name, refresh, weak=False)
        opts   .addListener('outline',      name, refresh, weak=False)
        opts   .addListener('showName',     name, refresh, weak=False)
        opts   .addListener('outlineWidth', name, refresh, weak=False)
        opts   .addListener('vertexData',   name, refresh, weak=False)
        opts   .addListener('cmap',         name, refresh, weak=False)
        opts   .addListener('displayRange', name, refresh, weak=False)
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
        self.opts   .removeListener('vertexData',   self.name)
        self.opts   .removeListener('cmap',         self.name)
        self.opts   .removeListener('displayRange', self.name)
        self.display.removeListener('brightness',   self.name)
        self.display.removeListener('contrast',     self.name)
        self.display.removeListener('alpha',        self.name)

 
    def setAxes(self, xax, yax):
        """Overrides :meth:`.GLObject.setAxes`. Calls the base class
        implementation, and calls :meth:`.GLObjectRenderTexture.setAxes`
        on the off-screen texture.
        """
        globject.GLObject.setAxes(self, xax, yax)


    def updateVertices(self, *a):
        """Called by :meth:`__init__`, and when certain display properties
        change. (Re-)generates the mesh vertices and indices. They are stored
        as attributes called ``vertices`` and ``indices`` respectively.
        """

        overlay  = self.overlay
        vertices = overlay.vertices
        indices  = overlay.indices
        xform    = self.opts.getCoordSpaceTransform()

        if not np.all(np.isclose(xform, np.eye(4))):
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

        # TODO Base this on the current render texture size?

        raise NotImplementedError()
 

    def preDraw(self):
        """Overrides :meth:`.GLObject.preDraw`. Sets the size of the backing
        :class:`.RenderTexture`instances based on the current viewport size.
        """

        size   = gl.glGetIntegerv(gl.GL_VIEWPORT)
        width  = size[2]
        height = size[3]

        # We only need to resize the texture when
        # the viewport size/quality changes.
        if self.renderTexture.getSize() != (width, height):
            self.renderTexture.setSize(width, height)

    
    def draw(self, zpos, xform=None, bbox=None):
        """Overrids :meth:`.GLObject.draw`. Draws a 2D slice of the
        :class:`.TriangleMesh`, at the specified Z location.
        """

        opts    = self.opts
        xax     = self.xax
        yax     = self.yax
        zax     = self.zax
        lo,  hi = self.getDisplayBounds()

        if zpos < lo[zax] or zpos > hi[zax]:
            return
        
        if opts.outline:
            self.drawOutline(zpos)
            
        else:
            lo, hi = self.__calculateViewport(lo, hi, bbox)
            xmin   = lo[xax]
            xmax   = hi[xax]
            ymin   = lo[yax]
            ymax   = hi[yax]
            tex    = self.renderTexture
            self.renderCrossSection(zpos, lo, hi, tex)
            tex.drawOnBounds(zpos, xmin, xmax, ymin, ymax, xax, yax, xform)


    def drawOutline(self, zpos):
        """
        """

        overlay = self.overlay
        opts    = self.opts
        zax     = self.zax

        origin      = [0] * 3
        normal      = [0] * 3
        origin[zax] = zpos
        normal[zax] = 1

        ropts = opts.displayCtx.getOpts(opts.refImage)
        origin = ropts.transformCoords(origin,
                                       ropts.transform,
                                       opts.coordSpace)

        lines, faces = trimesh.mesh_plane(
            overlay.vertices,
            overlay.indices,
            plane_normal=normal,
            plane_origin=origin)

        # TODO Data for each vertex

        lines = np.array(lines.reshape((-1, 3)), dtype=np.float32)

        xform = ropts.getTransform(opts.coordSpace, ropts.transform)
        xform = np.array(xform, dtype=np.float32)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(xform.ravel('F'))
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        
        gl.glColor(*opts.colour)
        gl.glLineWidth(opts.outlineWidth)

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, lines.ravel('C'))
        gl.glDrawArrays(gl.GL_LINES, 0, lines.shape[0])

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glPopMatrix()


    def renderCrossSection(self, zpos, lo, hi, dest):
        """
        """
        
        display  = self.display 
        opts     = self.opts
        xax      = self.xax
        yax      = self.yax
        zax      = self.zax
        xmin     = lo[xax]
        ymin     = lo[yax]
        xmax     = hi[xax]
        ymax     = hi[yax]
        vertices = self.vertices
        indices  = self.indices

        dest.bindAsRenderTarget()
        dest.setRenderViewport(xax, yax, lo, hi)
        
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

        planeEq  = glroutines.planeEquation(clipPlaneVerts[0, :],
                                            clipPlaneVerts[1, :],
                                            clipPlaneVerts[2, :])

        gl.glClearColor(0, 0, 0, 0)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT |
                   gl.GL_DEPTH_BUFFER_BIT |
                   gl.GL_STENCIL_BUFFER_BIT)

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

            gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices.ravel('C'))
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

        dest.unbindAsRenderTarget()
        dest.restoreViewport()
            
    
    def postDraw(self):
        """Overrides :meth:`.GLObject.postDraw`. This method does nothing. """
        pass


    def __calculateViewport(self, lo, hi, bbox=None):
        """Called by :meth:`draw`. Calculates an appropriate viewport (the
        horizontal/vertical minimums/maximums in display coordinates) given
        the ``lo`` and ``hi`` ``GLMesh`` display bounds, and a display
        ``bbox``.
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
        
        return lo, hi
