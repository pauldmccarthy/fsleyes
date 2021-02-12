#!/usr/bin/env python
#
# glmesh.py - The GLMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`GLMesh` class, a :class:`.GLObject` used
to render :class:`.Mesh` overlays.
"""


import numpy        as np
import numpy.linalg as npla
import OpenGL.GL    as gl

from . import                  globject
import fsl.data.utils       as dutils
import fsl.transform.affine as affine
import fsleyes.gl           as fslgl
import fsleyes.gl.routines  as glroutines
import fsleyes.gl.textures  as textures


class GLMesh(globject.GLObject):
    """The ``GLMesh`` class is a :class:`.GLObject` which encapsulates the
    logic required to draw 2D slices, and 3D renderings, of a
    :class:`.Mesh` overlay.  The ``GLMesh`` class assumes that the
    :class:`.Display` instance associated with the ``Mesh`` overlay
    holds a reference to a :class:`.MeshOpts` instance, which contains
    ``GLMesh`` specific display settings.


    **2D rendering**


    A ``GLMesh`` is rendered in one of two different ways, depending upon the
    value of the :attr:`.MeshOpts.outline` and :attr:`.MeshOpts.vertexData`
    properties.


    *Cross-sections*

    If ``outline is False and vertexData is None``, a filled cross-section of
    the mesh is drawn. This is accomplished using a three-pass technique,
    roughly following that described at
    http://glbook.gamedev.net/GLBOOK/glbook.gamedev.net/moglgp/advclip.html:

     1. The front face of the mesh is rendered to the stencil buffer.

     2. The back face is rendered to the stencil buffer, and subtracted
        from the front face.

     3. This intersection (of the mesh with a plane at the slice Z location)
        is then rendered to the canvas.


    This cross-section is filled with the :attr:`.MeshOpts.colour` property.


    *Outlines*


    If ``outline is True or vertexData is not None``, the intersection of the
    mesh triangles with the viewing plane is calculated. These lines are then
    rendered as ``GL_LINES`` primitives.


    When a mesh outline is drawn on a canvas, the calculated line vertices,
    and corresponding mesh faces (triangles) are cached via the
    :meth:`.OverlayList.setData` method. This is so that other parts of
    FSLeyes can access this information if necessary (e.g. the
    :class:`.OrthoViewProfile` provides mesh-specific interaction). For a
    canvas which is showing a plane orthogonal to display axis X, Y or Z, this
    data will be given a key of ``'crosssection_0'``, ``'crosssection_1'``, or
    ``'crosssection_2'`` respectively.


    *Colouring*


    These lines will be coloured in one of the following ways:

       - With the ``MeshOpts.colour``.

       - According to the :attr:`.MeshOpts.vertexData` if it is set, in which
         case the properties of the :class:`.ColourMapOpts` class (from which
         the :class:`.MeshOpts` class derives) come into effect.

       - Or, if :attr:`vertexData` is set, and the :attr:`.MeshOpts.useLut`
         property is ``True``, the :attr:`.MeshOpts.lut` is used.


    When ``MeshOpts.vertexData is not None``, the ``GLMesh`` class makes use
    of the ``glmesh`` vertex and fragment shaders. These shaders are managed
    by two OpenGL version-specific modules - :mod:`.gl14.glmesh_funcs`, and
    :mod:`.gl21.glmesh_funcs`. These version specific modules must provide the
    following functions:


     - ``compileShaders(GLMesh)``: Compiles vertex/fragment shaders.

     - ``updateShaderState(GLMesh, **kwargs)``: Updates vertex/fragment
       shaders. Should expect the following keyword arguments:

        - ``useNegCmap``: Boolean which is ``True`` if a negative colour map
           should be used

        - ``cmapXform``:   Transformation matrix which transforms from vertex
                           data into colour map texture coordinates.

        - ``flatColour``:  Colour to use for fragments which are outside
                           of the clipping range.

     - ``preDraw(GLMesh)``: Prepare for drawing (e.g. load shaders)

     - ``draw(GLMesh, glType, vertices, indices=None, normals=None, vdata=None)``:  # noqa
        Draws mesh using shaders.

     - ``postDraw(GLMesh)``: Clean up after drawing


    **3D rendering**


    3D mesh rendering is much simpler than 2D rendering. The mesh is simply
    rendered to the canvas, and coloured in the same way as described above.
    Whether the 3D mesh is coloured with a flat colour, or according to vertex
    data, shader programs are used which colour the mesh, and also apply a
    simple lighting effect.


    **Flat shading**

    When the :attr:`.MeshOpts.flatShading` property is active (only possible
    when 3D rendering), the mesh vertices and indices need to be modified.
    In order to achive flat shading, each vertex of a triangle must be given
    the same vertex data value. This means that vertices cannot be shared by
    different triangles. So when the ``flatShading`` property changes, the
    :meth:`updateVertices` method will re-generate the vertices and indices
    accordingly. The :meth:`getVertexData` method will modify the vertex
    data that gets passed to the shader accordingly too.
    """


    def __init__(self, overlay, overlayList, displayCtx, canvas, threedee):
        """Create a ``GLMesh``.

        :arg overlay:     A :class:`.Mesh` overlay.
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg canvas:      The canvas drawing this ``GLMesh``.
        :arg threedee:    2D or 3D rendering.
        """

        globject.GLObject.__init__(
            self, overlay, overlayList, displayCtx, canvas, threedee)

        self.flatShader   = None
        self.dataShader   = None
        self.activeShader = None

        # We use a render texture when
        # rendering model cross sections.
        # This texture is kept at display/
        # screen resolution
        self.renderTexture = textures.RenderTexture(
            self.name, interp=gl.GL_NEAREST)

        # Mesh overlays are coloured:
        #
        #  - with a constant colour (opts.outline == False), or
        #
        #  - with a +/- colour map, (opts.vertexData not None), or
        #
        #  - with a lookup table (opts.useLut == True and
        #    opts.vertexData is not None)
        self.cmapTexture    = textures.ColourMapTexture(  self.name)
        self.negCmapTexture = textures.ColourMapTexture(  self.name)
        self.lutTexture     = textures.LookupTableTexture(self.name)

        self.lut = None

        self.registerLut()
        self.addListeners()
        self.updateVertices()
        self.refreshCmapTextures(notify=False)

        self.compileShaders()
        self.updateShaderState()


    def destroy(self):
        """Must be called when this ``GLMesh`` is no longer needed. Removes
        some property listeners and destroys the colour map textures and
        off-screen :class:`.RenderTexture`.
        """

        self.renderTexture .destroy()
        self.cmapTexture   .destroy()
        self.negCmapTexture.destroy()
        self.lutTexture    .destroy()

        self.removeListeners()
        self.deregisterLut()

        globject.GLObject.destroy(self)

        if self.flatShader is not None: self.flatShader.destroy()
        if self.dataShader is not None: self.dataShader.destroy()

        self.dataShader   = None
        self.flatShader   = None
        self.activeShader = None

        self.lut            = None
        self.renderTexture  = None
        self.cmapTexture    = None
        self.negCmapTexture = None
        self.lutTexture     = None


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
        canvas  = self.canvas
        opts    = self.opts

        def shader(*a):
            self.updateShaderState()
            self.notify()

        def vertices(*a):
            self.updateVertices()
            self.updateShaderState()
            self.notify()

        def refreshCmap(*a):
            self.refreshCmapTextures(notify=False)
            self.updateShaderState()
            self.notify()

        def registerLut(*a):
            self.deregisterLut()
            self.registerLut()
            self.refreshCmapTextures()

        def refresh(*a):
            self.notify()

        self.overlay.register(name, vertices, 'vertices')
        opts   .addListener('bounds',           name, vertices,    weak=False)
        opts   .addListener('colour',           name, shader,      weak=False)
        opts   .addListener('outline',          name, refresh,     weak=False)
        opts   .addListener('outlineWidth',     name, refresh,     weak=False)
        opts   .addListener('wireframe',        name, refresh,     weak=False)
        opts   .addListener('vertexData',       name, shader,      weak=False)
        opts   .addListener('modulateData',     name, shader,      weak=False)
        opts   .addListener('vertexDataIndex',  name, shader,      weak=False)
        opts   .addListener('clippingRange',    name, shader,      weak=False)
        opts   .addListener('modulateRange',    name, shader,      weak=False)
        opts   .addListener('invertClipping',   name, shader,      weak=False)
        opts   .addListener('discardClipped',   name, shader,      weak=False)
        opts   .addListener('cmap',             name, refreshCmap, weak=False)
        opts   .addListener('useNegativeCmap',  name, refreshCmap, weak=False)
        opts   .addListener('negativeCmap',     name, refreshCmap, weak=False)
        opts   .addListener('cmapResolution',   name, refreshCmap, weak=False)
        opts   .addListener('interpolateCmaps', name, refreshCmap, weak=False)
        opts   .addListener('invert',           name, refreshCmap, weak=False)
        opts   .addListener('gamma',            name, refreshCmap, weak=False)
        opts   .addListener('displayRange',     name, refreshCmap, weak=False)
        opts   .addListener('useLut',           name, shader,      weak=False)
        opts   .addListener('lut',              name, registerLut, weak=False)
        opts   .addListener('modulateAlpha',    name, shader,      weak=False)
        opts   .addListener('flatShading',      name, vertices,    weak=False)
        display.addListener('alpha',            name, refreshCmap, weak=False)

        # We don't need to listen for
        # brightness or contrast, because
        # they are linked to displayRange.


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all of the listeners added by
        the :meth:`addListeners` method.
        """
        self.overlay.deregister(self.name, 'vertices')
        self.opts   .removeListener('bounds',           self.name)
        self.opts   .removeListener('colour',           self.name)
        self.opts   .removeListener('outline',          self.name)
        self.opts   .removeListener('outlineWidth',     self.name)
        self.opts   .removeListener('wireframe',        self.name)
        self.opts   .removeListener('vertexData',       self.name)
        self.opts   .removeListener('modulateData',     self.name)
        self.opts   .removeListener('vertexDataIndex',  self.name)
        self.opts   .removeListener('clippingRange',    self.name)
        self.opts   .removeListener('modulateRange',    self.name)
        self.opts   .removeListener('invertClipping',   self.name)
        self.opts   .removeListener('discardClipped',   self.name)
        self.opts   .removeListener('cmap',             self.name)
        self.opts   .removeListener('useNegativeCmap',  self.name)
        self.opts   .removeListener('negativeCmap',     self.name)
        self.opts   .removeListener('cmapResolution',   self.name)
        self.opts   .removeListener('interpolateCmaps', self.name)
        self.opts   .removeListener('invert',           self.name)
        self.opts   .removeListener('gamma',            self.name)
        self.opts   .removeListener('displayRange',     self.name)
        self.opts   .removeListener('useLut',           self.name)
        self.opts   .removeListener('lut',              self.name)
        self.opts   .removeListener('modulateAlpha',    self.name)
        self.opts   .removeListener('flatShading',      self.name)
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
        change. (Re-)generates the mesh vertices, indices and normals (if
        being displayed in 3D). They are stored as attributes called
        ``vertices``, ``indices``, and ``normals`` respectively.
        """

        overlay  = self.overlay
        opts     = self.opts
        threedee = self.threedee
        vertices = overlay.vertices
        indices  = overlay.indices
        normals  = self.overlay.vnormals
        vdata    = opts.getVertexData('vertex')
        xform    = opts.getTransform('mesh', 'display')

        if not np.all(np.isclose(xform, np.eye(4))):
            vertices = affine.transform(vertices, xform)

            if self.threedee:
                nmat    = affine.invert(xform).T
                normals = affine.transform(normals, nmat, vector=True)

        self.origIndices = indices
        indices          = np.asarray(indices.flatten(), dtype=np.uint32)

        # If flatShading is active, we cannot share
        # vertices between triangles, so we generate
        # a set of unique vertices for each triangle,
        # and then re-generate the triangle indices.
        # The original indices are saved above, as
        # they will be used by the getVertexData
        # method to duplicate the vertex data.
        if threedee and (vdata is not None) and opts.flatShading:
            self.vertices = vertices[indices].astype(np.float32)
            self.indices  = np.arange(0, len(self.vertices), dtype=np.uint32)
            normals       = normals[indices, :]
        else:
            self.vertices = np.asarray(vertices, dtype=np.float32)
            self.indices  = indices

        self.vertices = dutils.makeWriteable(self.vertices)
        self.indices  = dutils.makeWriteable(self.indices)

        if self.threedee:
            self.normals = np.array(normals, dtype=np.float32)


    def frontFace(self):
        """Returns the face of the mesh triangles which which will be facing
        outwards, either ``GL_CCW`` or ``GL_CW``. This will differ depending
        on the mesh-to-display transformation matrix.

        This method is only used in 3D rendering.
        """

        if not self.threedee:
            return gl.GL_CCW

        # Only looking at the mesh -> display
        # transform, thus we are assuming that
        # the MVP matrix does not have any
        # negative scales.
        xform = self.opts.getTransform('mesh', 'display')

        if npla.det(xform) > 0: return gl.GL_CCW
        else:                   return gl.GL_CW


    def getDisplayBounds(self):
        """Overrides :meth:`.GLObject.getDisplayBounds`. Returns a bounding
        box which contains the mesh vertices.
        """
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi())


    def draw2DOutlineEnabled(self):
        """Only relevent for 2D rendering. Returns ``True`` if outline mode
        should be used, ``False`` otherwise.
        """

        opts    = self.opts
        overlay = self.overlay

        return ((overlay.trimesh is not None) and
                (opts.outline or opts.vertexData is not None))


    def needShader(self):
        """Returns ``True`` if a shader should be loaded, ``False`` otherwise.
        Relevant for both 2D and 3D rendering.
        """
        return (self.threedee or
                (self.draw2DOutlineEnabled() and
                 self.opts.vertexData is not None))


    def preDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLObject.preDraw`. Performs some pre-drawing
        configuration, which might involve loading shaders, and/or setting the
        size of the backing :class:`.RenderTexture` instance based on the
        current viewport size.
        """

        useShader  = self.needShader()
        outline    = self.draw2DOutlineEnabled()
        useTexture = not (self.threedee or outline)

        # A shader program is used either in 3D, or
        # in 2D when some vertex data is being shown
        if useShader:
            fslgl.glmesh_funcs.preDraw(self)

            if self.opts.vertexData is not None:
                if self.opts.useLut:
                    self.lutTexture.bindTexture(gl.GL_TEXTURE0)
                else:
                    self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
                    self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)

        # An off-screen texture is used when
        # drawing off-screen textures in 2D
        if useTexture:
            size   = gl.glGetIntegerv(gl.GL_VIEWPORT)
            width  = size[2]
            height = size[3]

            # We only need to resize the texture when
            # the viewport size/quality changes.
            if self.renderTexture.shape != (width, height):
                self.renderTexture.shape = width, height


    def draw2D(self, zpos, axes, xform=None, bbox=None):
        """Overrids :meth:`.GLObject.draw2D`. Draws a 2D slice of the
        :class:`.Mesh`, at the specified Z location.
        """

        overlay       = self.overlay
        lo,  hi       = self.getDisplayBounds()
        xax, yax, zax = axes
        outline       = self.draw2DOutlineEnabled()

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

        # the calculateIntersection method caches
        # cross section vertices - make sure they're
        # cleared in case we are not doing an outline
        # draw.
        self.overlayList.setData(overlay, 'crosssection_{}'.format(zax), None)

        if is2D:
            self.draw2DMesh(xform, bbox)

        elif outline:
            self.drawOutline(zpos, axes, xform, bbox)

        else:
            lo, hi = self.calculateViewport(lo, hi, axes, bbox)
            xmin   = lo[xax]
            xmax   = hi[xax]
            ymin   = lo[yax]
            ymax   = hi[yax]
            tex    = self.renderTexture

            self.drawCrossSection(zpos, axes, lo, hi, tex)

            tex.drawOnBounds(zpos, xmin, xmax, ymin, ymax, xax, yax, xform)


    def draw3D(self, xform=None, bbox=None):
        """Overrides :meth:`.GLObject.draw3D`. Draws a 3D rendering of the
        mesh.
        """
        opts      = self.opts
        verts     = self.vertices
        idxs      = self.indices
        normals   = self.normals
        blo, bhi  = self.getDisplayBounds()
        vdata     = self.getVertexData('vertex')
        mdata     = self.getVertexData('modulate')

        if mdata is None:
            mdata = vdata

        is2D = np.isclose(bhi[2], blo[2])

        if opts.wireframe:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            gl.glLineWidth(2)
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('F'))

        if is2D or opts.wireframe:
            enable = (gl.GL_DEPTH_TEST)
        else:
            enable = (gl.GL_DEPTH_TEST, gl.GL_CULL_FACE)

        gl.glDisable(gl.GL_CULL_FACE)
        with glroutines.enabled(enable):
            gl.glFrontFace(self.frontFace())
            if not is2D:
                gl.glCullFace(gl.GL_BACK)
            fslgl.glmesh_funcs.draw(
                self,
                gl.GL_TRIANGLES,
                verts,
                normals=normals,
                indices=idxs,
                vdata=vdata,
                mdata=mdata)

        if xform is not None:
            gl.glPopMatrix()


    def postDraw(self, xform=None, bbox=None):
        """Overrides :meth:`.GLObject.postDraw`. May call the
        :func:`.gl14.glmesh_funcs.postDraw` or
        :func:`.gl21.glmesh_funcs.postDraw` function.
        """

        if self.needShader():
            fslgl.glmesh_funcs.postDraw(self)

            if self.opts.vertexData is not None:
                if self.opts.useLut:
                    self.lutTexture.unbindTexture()
                else:
                    self.cmapTexture   .unbindTexture()
                    self.negCmapTexture.unbindTexture()


    def drawOutline(self, zpos, axes, xform=None, bbox=None):
        """Called by :meth:`draw2D` when ``MeshOpts.outline is True or
        MeshOpts.vertexData is not None``.  Calculates the intersection of the
        mesh with the viewing plane, and renders it as a set of
        ``GL_LINES``. If ``MeshOpts.vertexData is None``, the draw is
        performed using immediate mode OpenGL.

        Otherwise, the :func:`.gl14.glmesh_funcs.draw` or
        :func:`.gl21.glmesh_funcs.draw` function is used, which performs
        shader-based rendering.
        """

        opts = self.opts

        # Makes code below a bit nicer
        if xform is None:
            xform = np.eye(4)

        vertices, faces, dists, vertXform = self.calculateIntersection(
            zpos, axes, bbox)

        if vertXform is not None:
            xform = affine.concat(xform, vertXform)

        vdata     = self.getVertexData('vertex',   faces, dists)
        mdata     = self.getVertexData('modulate', faces, dists)
        useShader = vdata is not None
        vertices  = vertices.reshape(-1, 3)
        nvertices = vertices.shape[0]

        if mdata is None:
            mdata = vdata

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('F'))

        gl.glLineWidth(opts.outlineWidth)

        # Constant colour
        if not useShader:
            vertices = vertices.ravel('C')
            gl.glColor(*opts.getConstantColour())
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
            gl.glDrawArrays(gl.GL_LINES, 0, nvertices)
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        # Coloured from vertex data
        else:
            fslgl.glmesh_funcs.draw(
                self,
                gl.GL_LINES,
                vertices,
                vdata=vdata,
                mdata=mdata)

        gl.glPopMatrix()


    def draw2DMesh(self, xform=None, bbox=None):
        """Not to be confused with :meth:`draw2D`.  Called by :meth:`draw2D`
        for :class:`.Mesh` overlays which are actually 2D (with a flat
        third dimension).
        """

        opts      = self.opts
        vdata     = opts.getVertexData('vertex')
        mdata     = opts.getVertexData('modulate')
        useShader = self.needShader()
        vertices  = self.vertices
        faces     = self.indices

        if mdata is None:
            mdata = vdata

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
            # TODO separate modulateDataIndex?
            vdata = vdata[:, opts.vertexDataIndex]
            mdata = mdata[:, 0]
            fslgl.glmesh_funcs.draw(
                self,
                gl.GL_TRIANGLES,
                vertices,
                indices=faces,
                vdata=vdata,
                mdata=mdata)


    def drawCrossSection(self, zpos, axes, lo, hi, dest):
        """Renders a filled cross-section of the mesh to an off-screen
        :class:`.RenderTexture`. See:

        http://glbook.gamedev.net/GLBOOK/glbook.gamedev.net/moglgp/advclip.html

        :arg zpos: Position along the z axis
        :arg axes: Tuple containing ``(x, y, z)`` axis indices.
        :arg lo:   Tuple containing the low bounds on each axis.
        :arg hi:   Tuple containing the high bounds on each axis.
        :arg dest: The :class:`.RenderTexture` to render to.
        """

        opts     = self.opts
        xax      = axes[0]
        yax      = axes[1]
        zax      = axes[2]
        xmin     = lo[xax]
        ymin     = lo[yax]
        xmax     = hi[xax]
        ymax     = hi[yax]
        vertices = self.vertices.ravel('C')
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
        gl.glFrontFace(gl.GL_CCW)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

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
        direction = [gl.GL_INCR, gl.GL_DECR]

        # If the mesh coordinate transformation
        # has a negative determinant, it means
        # the back faces will be facing the camera,
        # so we need to render the back faces first.
        if npla.det(opts.getTransform('mesh', 'display')) > 0:
            faceOrder = [gl.GL_FRONT, gl.GL_BACK]
        else:
            faceOrder = [gl.GL_BACK,  gl.GL_FRONT]

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


    def calculateViewport(self, lo, hi, axes, bbox=None):
        """Called by :meth:`draw2D`. Calculates an appropriate viewport (the
        horizontal/vertical minimums/maximums in display coordinates) given
        the ``lo`` and ``hi`` ``GLMesh`` display bounds, and a display
        ``bbox``.
        """

        xax = axes[0]
        yax = axes[1]

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


    def calculateIntersection(self, zpos, axes, bbox=None):
        """Uses the :func:`.Mesh.planeIntersection` method to
        calculate the intersection of the mesh with the viewing plane at
        the given ``zpos``.

        :arg zpos:  Z axis coordinate at which the intersection is to be
                    calculated

        :arg axes:  Tuple containing the ``(x, y, z)`` axis indices.

        :arg bbox:  A tuple containing a ``([xlo, ylo, zlo], [xhi, yhi, zhi])``
                    bounding box to which the calculation can be restricted.

        :returns: A tuple containing:

                   - A ``(n, 2, 3)`` array which contains the two vertices of
                     a line for every intersected face (triangle) in the mesh.

                   - A ``(n, 3)`` array containing the intersected faces
                     (indices into the :attr:`.Mesh.vertices` array).

                   - A ``(n, 2, 3)`` array containing the barycentric
                     coordinates of the intersection line vertices.

                   - A ``(4, 4)`` array containing a transformation matrix
                     for transforming the line vertices into the display
                     coordinate system. May be ``None``, indicating that
                     no transformation is necessary.

        .. note:: The line vertices, and corresponding mesh triangle face
                  indices, which make up the cross section are saved
                  via the :meth:`.OverlayList.setData` method, with a key
                  ``'crosssection_[zax]'``, where ``[zax]`` is set to the
                  index of the display Z axis.
        """

        overlay     = self.overlay
        zax         = axes[2]
        opts        = self.opts
        origin      = [0] * 3
        normal      = [0] * 3
        origin[zax] = zpos
        normal[zax] = 1

        vertXform = opts.getTransform(           'mesh',    'display')
        origin    = opts.transformCoords(origin, 'display', 'mesh')
        normal    = opts.transformCoords(normal, 'display', 'mesh',
                                         vector=True)

        # TODO use bbox to constrain? This
        #      would be nice, but is not
        #      supported by trimesh.
        lines, faces, dists = overlay.planeIntersection(
            normal, origin, distances=True)

        lines = np.asarray(lines, dtype=np.float32)
        faces = np.asarray(faces, dtype=np.uint32)

        # cache the line vertices for other
        # things which might be interested.
        # See, for example, OrthoViewProfile
        # pick mode methods.
        self.overlayList.setData(overlay,
                                 'crosssection_{}'.format(zax),
                                 (lines, faces))

        faces = overlay.indices[faces]

        return lines, faces, dists, vertXform


    def getVertexData(self, vdtype, faces=None, dists=None):
        """If :attr:`.MeshOpts.vertexData` (or :attr:`.MeshOpts.modulateData`)
        is not ``None``, this method returns the vertex data to use for the
        current vertex data index.

        ``faces`` and ``dists`` are used by the :meth:`drawOutline` method,
        which draws a cross-section of the mesh. The ``dists`` array contains
        barycentric coordinates for each line vertex, and is used to linearly
        interpolate between the values of the vertices of the intersected
        triangles (defined in ``faces``).

        If ``MeshOpts.vertexData is None``, this method returns ``None``.

        :arg vdtype: Use ``'vertex'`` for :attr:`.MeshOpts.vertexData`, or
                     ``'modulate'`` for :attr:`.MeshOpts.modulateData`.
        """

        opts  = self.opts
        vdata = opts.getVertexData(vdtype)

        if vdata is None:
            return None

        # TODO separate modulateDataIndex for modulateData?
        if vdtype == 'vertex': vdata = vdata[:, opts.vertexDataIndex]
        else:                  vdata = vdata[:, 0]

        # when flat-shading, we colour each
        # triangle according to the data
        # value for its first vertex. This
        # should really be pre-generated
        # whenever the vertex data or flat-
        # shading option is changed, but it
        # is quick for typical surfaces, so
        # I'm not bothering for now.
        if self.threedee and (vdata is not None) and opts.flatShading:
            vdata = vdata[self.origIndices[:, 0]].repeat(3)

        if faces is not None and dists is not None:
            vdata = vdata[faces].repeat(2, axis=0).reshape(-1, 2, 3)
            vdata = (vdata * dists).reshape(-1, 3).sum(axis=1)

        return np.asarray(vdata, np.float32)


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
        gamma   = opts.realGamma(opts.gamma)
        invert  = opts.invert
        dmin    = opts.displayRange[0]
        dmax    = opts.displayRange[1]

        if interp: interp = gl.GL_LINEAR
        else:      interp = gl.GL_NEAREST

        self.cmapTexture.set(cmap=cmap,
                             invert=invert,
                             alpha=alpha,
                             resolution=res,
                             gamma=gamma,
                             interp=interp,
                             displayRange=(dmin, dmax))

        self.negCmapTexture.set(cmap=negCmap,
                                invert=invert,
                                alpha=alpha,
                                resolution=res,
                                gamma=gamma,
                                interp=interp,
                                displayRange=(dmin, dmax))

        self.lutTexture.set(alpha=display.alpha           / 100.0,
                            brightness=display.brightness / 100.0,
                            contrast=display.contrast     / 100.0,
                            lut=opts.lut)

        if notify:
            self.notify()


    def compileShaders(self):
        """(Re)Compiles the vertex/fragment shader program(s), via a call
        to the GL-version specific ``compileShaders`` function.
        """
        if self.flatShader is not None: self.flatShader.destroy()
        if self.dataShader is not None: self.dataShader.destroy()

        self.activeShader = None

        fslgl.glmesh_funcs.compileShaders(self)


    def updateShaderState(self):
        """Updates the vertex/fragment shader program(s) state, via a call to
        the GL-version specific ``updateShaderState`` function.
        """

        dopts      = self.opts
        canvas     = self.canvas
        flatColour = dopts.getConstantColour()
        useNegCmap = (not dopts.useLut) and dopts.useNegativeCmap

        if dopts.useLut:
            delta     = 1.0 / (dopts.lut.max() + 1)
            cmapXform = affine.scaleOffsetXform(delta, 0.5 * delta)
        else:
            cmapXform = self.cmapTexture.getCoordinateTransform()

        # calculate a scale+offset which transforms
        # modulate alpha value from the data range
        # into an alpha value, according to the
        # modulateRange
        modlo, modhi = dopts.modulateRange
        modRange     = modhi - modlo
        if modRange == 0:
            modScale  = 1
            modOffset = 0
        else:
            modScale  = 1 / modRange
            modOffset = -modlo / modRange

        fslgl.glmesh_funcs.updateShaderState(
            self,
            useNegCmap=useNegCmap,
            cmapXform=cmapXform,
            modScale=modScale,
            modOffset=modOffset,
            flatColour=flatColour)
