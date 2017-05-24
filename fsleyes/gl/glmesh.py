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


class GLMesh(globject.GLObject):
    """The ``GLMesh`` class is a :class:`.GLObject` which encapsulates the
    logic required to render 2D slices of a :class:`.TriangleMesh` overlay.
    The ``GLMesh`` class assumes that the :class:`.Display` instance
    associated with the ``TriangleMesh`` overlay holds a reference to a
    :class:`.MeshOpts` instance, which contains ``GLMesh`` specific
    display settings.


    A ``GLMesh`` is rendered in one of two different ways, depending upon
    the  value of the :attr:`.MeshOpts.outline`  property.


    If ``MeshOpts.outline is False``, a filled cross-section of the mesh is
    drawn. This is accomplished using a three-pass technique, roughly
    following that described at
    http://glbook.gamedev.net/GLBOOK/glbook.gamedev.net/moglgp/advclip.html:

     1. The front face of the mesh is rendered to the stencil buffer.

     2. The back face is rendered to the stencil buffer, and subtracted
        from the front face.

     3. This intersection (of the mesh with a plane at the slice Z location)
        is then rendered to the canvas.


    This cross-section is filled with the :attr:`.MeshOpts.colour` property.


    If ``MeshOpts.outline is True``, the :func:`.trimesh.mesh_plane` function
    is used to calculate the intersection of the mesh triangles with the
    viewing plane. Theese lines are then rendered as ``GL_LINES`` primitives.


    These lines will be coloured in one of the following ways:

       - With the ``MeshOpts.colour``.

       - According to the :attr:`.MeshOpts.vertexData` if it is set, in which
         case the properties of the :class:`.ColourMapOpts` class (from which
         the :class:`.MeshOpts` class derives) come into effect.

       - Or, if :attr:`vertexData` is set, and the :attr:`.MeshOpts.useLut`
         property is ``True``, the :attr:`.MeshOpts.lut` is used.


    When ``MeshOpts.outline is True``, and ``MeshOpts.vertexData is not
    None``, the ``GLMesh`` class makes use of the ``glmesh`` vertex and
    fragment shaders. These shaders are managed by two OpenGL version-specific
    modules - :mod:`.gl14.glmesh_funcs`, and :mod:`.gl21.glmesh_funcs`. These
    version specific modules must provide the following functions:

    ======================= =================================
    ``compileShaders``      Compiles vertex/fragment shaders.
    ``destroy``             Performs any necessary clean up.
    ``updateShaderState``   Updates vertex/fragment shaders.
    ``drawColouredOutline`` Draws mesh outline using shaders.
    ======================= =================================
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

        # We use a render texture when
        # rendering model cross sections.
        # This texture is kept at display/
        # screen resolution
        self.renderTexture = textures.RenderTexture(self.name, gl.GL_NEAREST)

        # Mesh overlays are coloured:
        #
        #  - with a costant colour (opts.outline == False), or
        #
        #  - with a +/- colour map, (opts.outline == True and opts.vertexData
        #    is not None), or
        #
        #  - with a lookup table (opts.outline == True and opts.useLut == True
        #    and opts.vertexData is not None)
        self.cmapTexture    = textures.ColourMapTexture(  self.name)
        self.negCmapTexture = textures.ColourMapTexture(  self.name)
        self.lutTexture     = textures.LookupTableTexture(self.name)

        self.lut = None

        self.registerLut()
        self.addListeners()
        self.updateVertices()
        self.refreshCmapTextures(notify=False)

        fslgl.glmesh_funcs.compileShaders(self)
        fslgl.glmesh_funcs.updateShaderState(self)


    def destroy(self):
        """Must be called when this ``GLMesh`` is no longer needed. Removes
        some property listeners and destroys the colour map texturtes and
        off-screen :class:`.RenderTexture`.
        """

        self.renderTexture .destroy()
        self.cmapTexture   .destroy()
        self.negCmapTexture.destroy()
        self.lutTexture    .destroy()

        fslgl.glmesh_funcs.destroy(self)
        self.removeListeners()
        self.deregisterLut()

        self.lut            = None
        self.renderTexture  = None
        self.cmapTexture    = None
        self.negCmapTexture = None
        self.lutTexture     = None
        self.overlay        = None
        self.display        = None
        self.opts           = None


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

        def shader(*a):
            fslgl.glmesh_funcs.updateShaderState(self)
            self.notify()

        def refreshCmap(*a):
            self.refreshCmapTextures(notify=False)
            fslgl.glmesh_funcs.updateShaderState(self)
            self.notify()

        def registerLut(*a):
            self.deregisterLut()
            self.registerLut()
            self.refreshCmapTextures()

        def refresh(*a):
            self.notify()

        opts   .addListener('bounds',           name, self.updateVertices)
        opts   .addListener('colour',           name, refresh,     weak=False)
        opts   .addListener('outline',          name, refresh,     weak=False)
        opts   .addListener('outlineWidth',     name, refresh,     weak=False)
        opts   .addListener('vertexData',       name, refresh,     weak=False)
        opts   .addListener('vertexDataIndex',  name, refresh,     weak=False)
        opts   .addListener('clippingRange',    name, shader,      weak=False)
        opts   .addListener('invertClipping',   name, shader,      weak=False)
        opts   .addListener('cmap',             name, refreshCmap, weak=False)
        opts   .addListener('useNegativeCmap',  name, refreshCmap, weak=False)
        opts   .addListener('negativeCmap',     name, refreshCmap, weak=False)
        opts   .addListener('cmapResolution',   name, refreshCmap, weak=False)
        opts   .addListener('interpolateCmaps', name, refreshCmap, weak=False)
        opts   .addListener('invert',           name, refreshCmap, weak=False)
        opts   .addListener('displayRange',     name, refreshCmap, weak=False)
        opts   .addListener('useLut',           name, shader,      weak=False)
        opts   .addListener('lut',              name, registerLut, weak=False)
        display.addListener('alpha',            name, refreshCmap, weak=False)
        # We don't need to listen for
        # brightness or contrast, because
        # they are linked to displayRange.


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all of the listeners added by
        the :meth:`addListeners` method.
        """
        self.opts   .removeListener('bounds',           self.name)
        self.opts   .removeListener('colour',           self.name)
        self.opts   .removeListener('outline',          self.name)
        self.opts   .removeListener('outlineWidth',     self.name)
        self.opts   .removeListener('vertexData',       self.name)
        self.opts   .removeListener('vertexDataIndex',  self.name)
        self.opts   .removeListener('clippingRange',    self.name)
        self.opts   .removeListener('invertClipping',   self.name)
        self.opts   .removeListener('cmap',             self.name)
        self.opts   .removeListener('useNegativeCmap',  self.name)
        self.opts   .removeListener('negativeCmap',     self.name)
        self.opts   .removeListener('cmapResolution',   self.name)
        self.opts   .removeListener('interpolateCmaps', self.name)
        self.opts   .removeListener('invert',           self.name)
        self.opts   .removeListener('displayRange',     self.name)
        self.opts   .removeListener('useLut',           self.name)
        self.opts   .removeListener('lut',              self.name)
        self.display.removeListener('alpha',            self.name)


    def registerLut(self):
        """Registers property listeners with the currently registered
        :class:`.LookupTable` (the :attr:`.MeshOpts.lut` property).
        """

        self.lut = self.opts.lut

        if self.lut is not None:
            for topic in ['label', 'added', 'removed']:
                self.lut.register(self.name, self.refreshCmapTextures, topic)


    def deregisterLut(self):
        """De-registers property listeners from the currently registered
        :class:`.LookupTable`.
        """

        if self.lut is not None:
            for topic in ['label', 'added', 'removed']:
                self.lut.deregister(self.name, topic)

        self.lut = None


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


    def preDraw(self):
        """Overrides :meth:`.GLObject.preDraw`. Sets the size of the backing
        :class:`.RenderTexture` instance based on the current viewport size.
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

        # Mesh is 2D, and is
        # perpendicular to
        # the viewing plane
        if np.any(np.isclose([lo[xax], lo[yax]], [hi[xax], hi[yax]])):
            return

        is2D = np.isclose(lo[zax], hi[zax])

        # 2D meshes are always drawn,
        # regardless of the zpos
        if not is2D and (zpos < lo[zax] or zpos > hi[zax]):
            return

        if is2D:
            self.draw2D(xform, bbox)

        elif opts.outline:
            self.drawOutline(zpos, xform, bbox)

        else:
            lo, hi = self.calculateViewport(lo, hi, bbox)
            xmin   = lo[xax]
            xmax   = hi[xax]
            ymin   = lo[yax]
            ymax   = hi[yax]
            tex    = self.renderTexture

            if is2D: self.renderCrossSection2D(    lo, hi, tex)
            else:    self.renderCrossSection(zpos, lo, hi, tex)

            tex.drawOnBounds(zpos, xmin, xmax, ymin, ymax, xax, yax, xform)


    def drawOutline(self, zpos, xform=None, bbox=None):
        """Called by :meth:`draw` when :attr:`.MeshOpts.outline` is ``True``.
        Calculates the intersection of the mesh with the viewing plane,
        and renders it as a set of ``GL_LINES``. If
        :attr:`.MeshOpts.vertexData` is ``None``, the draw is performed
        using immediate mode OpenGL.

        Otherwise, the :func:`.gl14.glmesh_funcs.drawColouredOutline` or
        :func:`.gl21.glmesh_funcs.drawColouredOutline` function is used, which
        performs shader-based rendering.
        """

        opts = self.opts

        # Makes code below a bit nicer
        if xform is None:
            xform = np.eye(4)

        vertices, faces, dists, vertXform = self.calculateIntersection(
            zpos, bbox)

        if vertXform is not None:
            xform = transform.concat(xform, vertXform)

        vdata     = self.getVertexData(faces, dists)
        useShader = vdata is not None
        vertices  = vertices.reshape(-1, 3)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('F'))

        gl.glLineWidth(opts.outlineWidth)

        # Constant colour
        if not useShader:
            gl.glColor(*opts.getConstantColour())
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices.ravel('C'))
            gl.glDrawArrays(gl.GL_LINES, 0, vertices.shape[0])
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        # Coloured from vertex data
        else:
            fslgl.glmesh_funcs.drawColouredOutline(self, vertices, vdata)

        gl.glPopMatrix()


    def draw2D(self, xform=None, bbox=None):
        """Called by :meth:`draw` for :class:`.TriangleMesh` overlays
        which are actually 2D (with a flat third dimension).
        """

        opts      = self.opts
        vdata     = opts.getVertexData()
        useShader = vdata is not None
        vertices  = self.vertices
        faces     = self.indices

        if opts.outline:
            gl.glLineWidth(opts.outlineWidth)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        # Constant colour
        if not useShader:

            gl.glColor(*opts.getConstantColour())
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

            gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices.ravel('C'))
            gl.glDrawElements(gl.GL_TRIANGLES,
                              faces.shape[0],
                              gl.GL_UNSIGNED_INT,
                              faces.ravel('C'))

            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        # Coloured from vertex data
        else:
            vdata = vdata[:, opts.vertexDataIndex]
            fslgl.glmesh_funcs.drawColouredOutline(
                self, vertices, vdata, faces, gl.GL_TRIANGLES)

        # Reset the polygon mode back to fill
        if opts.outline:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)


    def renderCrossSection(self, zpos, lo, hi, dest):
        """Renders a filled cross-section of the mesh to an off-screen
        :class:`.RenderTexture`.

        :arg zpos: Position along the z axis
        :arg lo:   Tuple containing the low bounds on each axis.
        :arg hi:   Tuple containing the high bounds on each axis.
        :arg dest: The :class:`.RenderTexture` to render to.
        """

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

        gl.glColor(*opts.getConstantColour())

        # Disable alpha blending - we
        # just want the colour copied
        # into the texture as-is.
        with glroutines.disabled(gl.GL_BLEND):
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


    def calculateViewport(self, lo, hi, bbox=None):
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


    def calculateIntersection(self, zpos, bbox=None):
        """Uses the :func:`.trimesh.mesh_plane` and
        :func:`.trimesh.points_to_barycentric` functions to calculate the
        intersection of the mesh with the viewing plane at the given ``zpos``.

        :arg zpos:  Z axis coordinate at which the intersection is to be
                    calculated

        :arg bbox:  A tuple containing a ``([xlo, ylo, zlo], [xhi, yhi, zhi])``
                    bounding box to which the calculation can be restricted.

        :returns: A tuple containing:

                   - A ``(n, 2, 3)`` array which contains the two vertices of
                     a line for every intersected face (triangle) in the mesh.

                   - A ``(n, 3)`` array containing the intersected faces
                     (indices into the :attr:`.TriangleMesh.vertices` array).

                   - A ``(n, 2, 3)`` array containing the barycentric
                     coordinates of the intersection line vertices.

                   - A ``(4, 4)`` array containing a transformation matrix
                     for transforming the line vertices into the display
                     coordinate system. May be ``None``, indicating that
                     no transformation is necessary.
        """

        overlay     = self.overlay
        zax         = self.zax
        opts        = self.opts
        origin      = [0] * 3
        normal      = [0] * 3
        origin[zax] = zpos
        normal[zax] = 1

        if opts.refImage is not None:

            ropts  = opts.displayCtx.getOpts(opts.refImage)
            origin = ropts.transformCoords(origin,
                                           ropts.transform,
                                           opts.coordSpace)

            vertXform = ropts.getTransform(opts.coordSpace, ropts.transform)

        else:
            vertXform = None

        # TODO use bbox to constrain?
        lines, faces = trimesh.mesh_plane(
            overlay.vertices,
            overlay.indices,
            plane_normal=normal,
            plane_origin=origin,
            return_faces=True)

        faces = overlay.indices[faces]

        # Calculate the barycentric coordinates
        # (distance from triangle vertices) for
        # each intersection line - this is used
        # for interpolating vertex colours.

        triangles = overlay.vertices[faces].repeat(2, axis=0)
        points    = lines.reshape((-1, 3))

        if triangles.size > 0:
            dists = trimesh.points_to_barycentric(triangles, points)
            dists = dists.reshape((-1, 2, 3))
        else:
            dists = np.zeros((0, 2, 3))

        return lines, faces, dists, vertXform


    def getVertexData(self, faces, dists):
        """If :attr:`.MeshOpts.vertexData` is not ``None``, this method
        returns the vertex data to use for the line segments calculated
        in the :meth:`calculateIntersection` method.

        The ``dists`` array contains barycentric coordinates for each line
        vertex, and is used to linearly interpolate between the values of the
        vertices of the intersected triangles (defined in ``faces``).

        If ``MeshOpts.vertexData is None``, this method returns ``None``.
        """

        opts  = self.opts
        vdata = opts.getVertexData()

        if vdata is None:
            return None

        vdata = vdata[:, opts.vertexDataIndex]

        vdata = vdata[faces].repeat(2, axis=0).reshape(-1, 2, 3)
        vdata = (vdata * dists).reshape(-1, 3).sum(axis=1)

        return vdata


    def refreshCmapTextures(self, *a, **kwa):
        """Called when various :class:`.Display` or :class:`.MeshOpts``
        properties change. Refreshes the :class:`.ColourMapTexture` instances
        corresponding to the :attr:`.MeshOpts.cmap` and
        :attr:`.MeshOpts.negativeCmap` properties, and the
        :class:`.LookupTableTexture` corresponding to the :attr:`.MeshOpts.lut`
        property.

        :arg notify: Must be passed as a keyword argument. If ``True`` (the
                     default) :meth:`.GLObject.notify` is called after the
                     textures have been updated.
        """

        notify = kwa.pop('notify', True)

        display = self.display
        opts    = self.opts
        alpha   = display.alpha / 100.0
        cmap    = opts.cmap
        interp  = opts.interpolateCmaps
        res     = opts.cmapResolution
        negCmap = opts.negativeCmap
        invert  = opts.invert
        dmin    = opts.displayRange[0]
        dmax    = opts.displayRange[1]

        if interp: interp = gl.GL_LINEAR
        else:      interp = gl.GL_NEAREST

        self.cmapTexture.set(cmap=cmap,
                             invert=invert,
                             alpha=alpha,
                             resolution=res,
                             interp=interp,
                             displayRange=(dmin, dmax))

        self.negCmapTexture.set(cmap=negCmap,
                                invert=invert,
                                alpha=alpha,
                                resolution=res,
                                interp=interp,
                                displayRange=(dmin, dmax))

        self.lutTexture.set(alpha=display.alpha           / 100.0,
                            brightness=display.brightness / 100.0,
                            contrast=display.contrast     / 100.0,
                            lut=opts.lut)

        if notify:
            self.notify()
