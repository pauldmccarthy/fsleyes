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
    properties - either a filled cross-secetion is drawn, or an outline of the
    cross-section is drawn.

    *Cross-sections*

    If ``outline is False and vertexData is None``, a filled cross-section of
    the mesh is drawn - see the :meth:`drawCrossSection` method.


    *Outlines*

    If ``outline is True or vertexData is not None``, an outline of the
    intersection of the mesh triangles with the viewing plane is calculated
    and drawn - see the :meth:`drawOutline` method.


    *Colouring*


    These lines will be coloured in one of the following ways:

       - With the ``MeshOpts.colour``.

       - According to the :attr:`.MeshOpts.vertexData` if it is set, in which
         case the properties of the :class:`.ColourMapOpts` class (from which
         the :class:`.MeshOpts` class derives) come into effect.

       - Or, if :attr:`vertexData` is set, and the :attr:`.MeshOpts.useLut`
         property is ``True``, the :attr:`.MeshOpts.lut` is used.


    Te ``GLMesh`` class makes use of the ``glmesh`` vertex and fragment
    shaders. These shaders are managed by two OpenGL version-specific modules -
    :mod:`.gl14.glmesh_funcs`, and :mod:`.gl21.glmesh_funcs`. These version
    specific modules must provide the following functions:

     - ``compileShaders(GLMesh)``: Compiles vertex/fragment shaders.
     - ``updateShaderState(GLMesh, **kwargs)``: Updates vertex/fragment
       shader settings.


    **3D rendering**


    3D mesh rendering is much simpler than 2D rendering. The mesh is simply
    rendered to the canvas, and coloured in the same way as described above.
    Whether the 3D mesh is coloured with a flat colour, or according to vertex
    data, shader programs are used which colour the mesh, and also apply a
    simple lighting effect.


    **Interpolation**

    When the :attr:`.MeshOpts.interpolation` property is set to ``'nearest'``,
    the mesh vertices and indices need to be modified.  In order to achieve
    nearest neighbour interpolation (a.k.a. flat shading) , each vertex of a
    triangle must be given the same vertex data value. This means that
    vertices cannot be shared by different triangles. So when the
    ``interpolation`` property changes, the :meth:`updateVertices` method will
    re-generate the vertices and indices accordingly. The
    :meth:`getVertexData` method will modify the vertex data that gets passed
    to the shader accordingly too.
    """


    def __init__(self, overlay, overlayList, displayCtx, threedee):
        """Create a ``GLMesh``.

        :arg overlay:     A :class:`.Mesh` overlay.
        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext` managing the scene.
        :arg canvas:      The canvas drawing this ``GLMesh``.
        :arg threedee:    2D or 3D rendering.
        """

        globject.GLObject.__init__(
            self, overlay, overlayList, displayCtx, threedee)

        # Separate shaders are use for flat
        # colouring vs data colouring.
        self.flatShader    = None
        self.dataShader    = None
        # Two shaders are used for 2D cross
        # section drawing.
        self.xsectcpShader = None
        self.xsectblShader = None

        # We also use a render texture when
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

        if self.flatShader    is not None: self.flatShader   .destroy()
        if self.dataShader    is not None: self.dataShader   .destroy()
        if self.xsectcpShader is not None: self.xsectcpShader.destroy()
        if self.xsectblShader is not None: self.xsectblShader.destroy()

        self.dataShader    = None
        self.flatShader    = None
        self.xsectcpShader = None
        self.xsectblShader = None

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
        opts    = self.opts

        def shader(*a):
            self.updateShaderState()
            self.notify()

        def vertices(*a):
            self.updateVertices()
            self.updateShaderState()
            self.notify()

        def cmap(*a):
            self.refreshCmapTextures(notify=False)
            self.updateShaderState()
            self.notify()

        def lut(*a):
            self.deregisterLut()
            self.registerLut()
            self.refreshCmapTextures()

        def refresh(*a):
            self.notify()

        self.overlay.register(name, vertices, 'vertices')
        opts   .addListener('bounds',              name, vertices, weak=False)
        opts   .addListener('colour',              name, shader,   weak=False)
        opts   .addListener('outline',             name, refresh,  weak=False)
        opts   .addListener('outlineWidth',        name, refresh,  weak=False)
        opts   .addListener('wireframe',           name, refresh,  weak=False)
        opts   .addListener('vertexData',          name, shader,   weak=False)
        opts   .addListener('modulateData',        name, shader,   weak=False)
        opts   .addListener('vertexDataIndex',     name, shader,   weak=False)
        opts   .addListener('clippingRange',       name, shader,   weak=False)
        opts   .addListener('modulateRange',       name, shader,   weak=False)
        opts   .addListener('invertClipping',      name, shader,   weak=False)
        opts   .addListener('discardClipped',      name, shader,   weak=False)
        opts   .addListener('cmap',                name, cmap,     weak=False)
        opts   .addListener('useNegativeCmap',     name, cmap,     weak=False)
        opts   .addListener('negativeCmap',        name, cmap,     weak=False)
        opts   .addListener('cmapResolution',      name, cmap,     weak=False)
        opts   .addListener('interpolateCmaps',    name, cmap,     weak=False)
        opts   .addListener('invert',              name, cmap,     weak=False)
        opts   .addListener('gamma',               name, cmap,     weak=False)
        opts   .addListener('displayRange',        name, cmap,     weak=False)
        opts   .addListener('useLut',              name, shader,   weak=False)
        opts   .addListener('lut',                 name, lut,      weak=False)
        opts   .addListener('modulateAlpha',       name, shader,   weak=False)
        opts   .addListener('invertModulateAlpha', name, shader,   weak=False)
        opts   .addListener('interpolation',       name, vertices, weak=False)
        display.addListener('alpha',               name, cmap,     weak=False)

        # We don't need to listen for
        # brightness or contrast, because
        # they are linked to displayRange.


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all of the listeners added by
        the :meth:`addListeners` method.
        """
        overlay = self.overlay
        opts    = self.opts
        display = self.display
        name    = self.name

        overlay.deregister(name, 'vertices')
        opts   .removeListener('bounds',              name)
        opts   .removeListener('colour',              name)
        opts   .removeListener('outline',             name)
        opts   .removeListener('outlineWidth',        name)
        opts   .removeListener('wireframe',           name)
        opts   .removeListener('vertexData',          name)
        opts   .removeListener('modulateData',        name)
        opts   .removeListener('vertexDataIndex',     name)
        opts   .removeListener('clippingRange',       name)
        opts   .removeListener('modulateRange',       name)
        opts   .removeListener('invertClipping',      name)
        opts   .removeListener('discardClipped',      name)
        opts   .removeListener('cmap',                name)
        opts   .removeListener('useNegativeCmap',     name)
        opts   .removeListener('negativeCmap',        name)
        opts   .removeListener('cmapResolution',      name)
        opts   .removeListener('interpolateCmaps',    name)
        opts   .removeListener('invert',              name)
        opts   .removeListener('gamma',               name)
        opts   .removeListener('displayRange',        name)
        opts   .removeListener('useLut',              name)
        opts   .removeListener('lut',                 name)
        opts   .removeListener('modulateAlpha',       name)
        opts   .removeListener('invertModulateAlpha', name)
        opts   .removeListener('interpolation',       name)
        display.removeListener('alpha',               name)


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
        interp   = opts.interpolation
        normals  = overlay.vnormals
        vdata    = opts.getVertexData('vertex')
        xform    = opts.getTransform('mesh', 'display')

        if not np.all(np.isclose(xform, np.eye(4))):
            vertices = affine.transform(vertices, xform)

            if self.threedee:
                nmat    = affine.invert(xform).T
                normals = affine.transform(normals, nmat, vector=True)

        self.origIndices = indices
        indices          = np.asarray(indices.flatten(), dtype=np.uint32)

        # If interp == nn, we cannot share
        # vertices between triangles, so we generate
        # a set of unique vertices for each triangle,
        # and then re-generate the triangle indices.
        # The original indices are saved above, as
        # they will be used by the getVertexData
        # method to duplicate the vertex data (as
        # we need to provide a data value for each
        # vertex).
        if threedee and (vdata is not None) and interp == 'nearest':
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
        """

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


    def preDraw(self):
        """Overrides :meth:`.GLObject.preDraw`. Binds colour map
        textures, if the mesh is being coloured with data.
        """

        if self.opts.vertexData is not None:
            if self.opts.useLut:
                self.lutTexture.bindTexture(gl.GL_TEXTURE0)
            else:
                self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
                self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)


    def draw2D(self, canvas, zpos, axes, xform=None):
        """Overrids :meth:`.GLObject.draw2D`. Draws a 2D slice of the
        :class:`.Mesh`, at the specified Z location.
        """

        overlay       = self.overlay
        lo,  hi       = self.getDisplayBounds()
        xax, yax, zax = axes
        outline       = self.draw2DOutlineEnabled()

        # Mesh is 2D, and is perpendicular to
        # the viewing plane - don't draw it.
        if np.any(np.isclose([lo[xax], lo[yax]], [hi[xax], hi[yax]])):
            return

        # Mesh is 2D, and is parallel
        # to the viewing plane.
        is2D = np.isclose(lo[zax], hi[zax])

        # Don't draw this mesh if it does not
        # intersect the plane at zpos. 2D
        # meshes are always drawn, regardless
        # of the zpos.
        if not is2D and (zpos < lo[zax] or zpos > hi[zax]):
            return

        # The calculateIntersection method
        # caches cross section vertices -
        # make sure they're cleared in case
        # we are not doing an outline draw.
        self.overlayList.setData(overlay, 'crosssection_{}'.format(zax), None)

        # Delegate to the appropriate sub-method
        if   is2D:    self.draw2DMesh(canvas, xform)
        elif outline: self.drawOutline(canvas, zpos, axes, xform)
        else:         self.drawCrossSection(canvas, zpos, axes, xform)


    def draw3D(self, canvas, xform=None):
        """Overrides :meth:`.GLObject.draw3D`. Draws a 3D rendering of the
        mesh.
        """
        opts      = self.opts
        flat      = opts.vertexData is None
        mvmat     = canvas.viewMatrix
        mvpmat    = canvas.mvpMatrix
        blo, bhi  = self.getDisplayBounds()

        if flat: shader = self.flatShader
        else:    shader = self.dataShader

        if xform is not None:
            mvmat  = affine.concat(mvmat,  xform)
            mvpmat = affine.concat(mvpmat, xform)

        normmat  = affine.invert(mvmat[:3, :3]).T
        lightPos = affine.transform(canvas.lightPos, mvmat)

        is2D = np.any(np.isclose(bhi, blo))

        if opts.wireframe: polymode = gl.GL_LINE
        else:              polymode = gl.GL_FILL

        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, polymode)
        gl.glLineWidth(1)

        if is2D or opts.wireframe: enable = (gl.GL_DEPTH_TEST)
        else:                      enable = (gl.GL_DEPTH_TEST, gl.GL_CULL_FACE)

        with glroutines.enabled(enable), shader.loaded():
            shader.set('MVP',       mvpmat)
            shader.set('MV',        mvmat)
            shader.set('normalmat', normmat)
            shader.set('lighting',  canvas.opts.light)
            shader.set('lightPos',  lightPos)
            gl.glFrontFace(self.frontFace())
            gl.glCullFace(gl.GL_BACK)
            shader.draw(gl.GL_TRIANGLES)

        # restore polygon mode to default (in
        # case we were drawing a wireframe)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)


    def postDraw(self):
        """Overrides :meth:`.GLObject.postDraw`. """
        if self.opts.vertexData is not None:
            if self.opts.useLut:
                self.lutTexture.unbindTexture()
            else:
                self.cmapTexture   .unbindTexture()
                self.negCmapTexture.unbindTexture()


    def drawOutline(self, canvas, zpos, axes, xform=None):
        """Called by :meth:`draw2D` when ``MeshOpts.outline is True or
        MeshOpts.vertexData is not None``.  Calculates the intersection of the
        mesh with the viewing plane as a set of line segments.

        If the :attr:`.MeshOpts.outlineWidth` property is equal to ``1``, the
        segments are drawn as ``GL_LINES`` primitives. Otherwise the lines are
        converted into polygons and drawn as ``GL_TRIANGLES`` (see
        :func:`.routines.lineAsPolygon`).

        The :func:`.gl14.glmesh_funcs.draw` or
        :func:`.gl21.glmesh_funcs.draw` function called to do the draw.

        When a mesh outline is drawn on a canvas, the calculated line vertices,
        and corresponding mesh faces (triangles) are cached via the
        :meth:`.OverlayList.setData` method. This is so that other parts of
        FSLeyes can access this information if necessary (e.g. the
        :class:`.OrthoViewProfile` provides mesh-specific interaction). For a
        canvas which is showing a plane orthogonal to display axis X, Y or Z,
        this data will be given a key of ``'crosssection_0'``,
        ``'crosssection_1'``, or ``'crosssection_2'`` respectively. This cache
        is written by the :meth:`calculateIntersection` method.
        """

        opts   = self.opts
        bbox   = canvas.viewport
        flat   = opts.vertexData is None

        if flat: shader = self.flatShader
        else:    shader = self.dataShader

        # Calculate cross-section of mesh with z
        # position as a set of line segments
        vertices, faces, dists, vertXform = self.calculateIntersection(
            zpos, axes, bbox)

        if xform     is     None: xform = np.eye(4)
        if vertXform is not None: xform = affine.concat(xform, vertXform)

        xform = affine.concat(canvas.mvpMatrix, xform)

        # Retrieve vertex data associated with cros-
        # section (will return None if no vertex
        # data is selected)
        vdata    = self.getVertexData('vertex',   faces, dists)
        mdata    = self.getVertexData('modulate', faces, dists)
        vertices = vertices.reshape(-1, 3)

        # Convert line segments to triangles
        # if drawing thick lines. If default
        # line width, we can use GL_LINES
        if opts.outlineWidth == 1:
            glprim  = gl.GL_LINES
            indices = None
        else:
            zax               = axes[2]
            lineWidth         = opts.outlineWidth * canvas.pixelSize()[0]
            glprim            = gl.GL_TRIANGLES
            vertices, indices = glroutines.lineAsPolygon(
                vertices, lineWidth, zax, indices=True)

            # Each line (two vertices) is replaced with
            # two triangles (defined by four vertices).
            # So we have to duplicate each vertex data
            # value. The lineAsPolyuon function keeps
            # the vertex order the same as the original
            # line-based vertices, so we can np.repeat
            # the data.
            if vdata is not None: vdata = np.repeat(vdata, 2)
            if mdata is not None: mdata = np.repeat(mdata, 2)

        if mdata is None:
            mdata = vdata

        # Draw the outline
        with shader.loaded():
            shader.set(   'MVP',    xform)
            shader.setAtt('vertex', vertices)
            shader.setIndices(indices)
            if not flat:
                shader.setAtt('vertexData',   vdata)
                shader.setAtt('modulateData', mdata)
            shader.draw(glprim, 0, vertices.shape[0])


    def draw2DMesh(self, canvas, xform=None):
        """Not to be confused with :meth:`draw2D`.  Called by :meth:`draw2D`
        for :class:`.Mesh` overlays which are actually 2D (with a flat
        third dimension).
        """

        opts      = self.opts
        vdata     = opts.getVertexData('vertex')
        mdata     = opts.getVertexData('modulate')
        flat      = opts.vertexData is None
        vertices  = self.vertices
        indices   = self.indices

        if flat: shader = self.flatShader
        else:    shader = self.dataShader

        if xform is None: xform = canvas.mvpMatrix
        else:             xform = affine.concat(canvas.mvpMatrix, xform)

        if mdata is None:
            mdata = vdata

        # Outline mode for 2D meshes is
        # not supported at the moment.
        if opts.outline:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        with shader.loaded():
            shader.set(       'MVP',    xform)
            shader.setAtt(    'vertex', vertices)
            shader.setIndices(indices)
            if not flat:
                shader.setAtt('vertexData',   vdata)
                shader.setAtt('modulateData', mdata)
            shader.draw(gl.GL_TRIANGLES)


    def drawCrossSection(self, canvas, zpos, axes, xform=None):
        """Called by :meth:`draw2D` when ``outline is False and vertexData is None``

        Draws a filled cross-section of the mesh at the specified Z location.

        This is accomplished using a four-pass technique, roughly following
        that described at

        http://glbook.gamedev.net/GLBOOK/glbook.gamedev.net/moglgp/advclip.html

        1. The mesh back face stencil is drawn to an off-screen stencil buffer.

        2. The mesh front face stencil is subtracted from the back face
           stencil. The stencil buffer now contains a binary mask of the cross-
           section.

        3. An off-screen texture is filled with the :attr:`.MeshOpts.colour`,
           masked by the stencil buffer.

        4. The off-screen texture is drawn to the canvas.

        :arg zpos:  Position along the z axis
        :arg axes:  Tuple containing ``(x, y, z)`` axis indices.
        :arg xform: Transformation matrix to apply to the vertices.
        """

        xax, yax, zax = axes
        bbox          = canvas.viewport
        cpshader      = self.xsectcpShader
        blshader      = self.xsectblShader
        lo, hi        = self.getDisplayBounds()
        lo, hi        = self.calculateViewport(lo, hi, axes, bbox)
        xmin          = lo[xax]
        xmax          = hi[xax]
        ymin          = lo[yax]
        ymax          = hi[yax]
        tex           = self.renderTexture

        # Make sure the off-screen texture
        # matches the display size
        width, height = canvas.GetSize()
        if tex.shape != (width, height):
            tex.shape = width, height

        if xform is None: xform = canvas.mvpMatrix
        else:             xform = affine.concat(canvas.mvpMatrix, xform)

        # Figure out the equation of a plane
        # perpendicular to the Z axis, and located
        # at the z position. This is used as a
        # clipping plane to draw the mesh
        # intersection. The clip plane is defined in
        # the display coordinate system, before MVP
        # transformation.
        clipPlane                = np.zeros((4, 3), dtype=np.float32)
        clipPlane[0, [xax, yax]] = [xmin, ymin]
        clipPlane[1, [xax, yax]] = [xmin, ymax]
        clipPlane[2, [xax, yax]] = [xmax, ymax]
        clipPlane[3, [xax, yax]] = [xmax, ymin]
        clipPlane[:,  zax]       =  zpos
        clipPlane = glroutines.planeEquation(clipPlane[0, :],
                                             clipPlane[1, :],
                                             clipPlane[2, :])

        # http://glbook.gamedev.net/GLBOOK/glbook.gamedev.net/moglgp/\
        #     advclip.html
        #
        # We can calculate a cross-section of the mesh
        # by subtracting a front-face stencil from a
        # back-face stencil, clipped by the above
        # clipping plane. We use the stencil buffer of
        # the off-screen render texture, and perform
        # these steps:
        #
        # 1. Draw back faces to the stencil buffer
        # 2. Subtract front faces from the stencil buffer
        # 3. Fill the off-screen texture with the fill colour,
        #    masking it with the stencil buffer
        # 4. Draw the off-screen texture to the display
        gl.glFrontFace(self.frontFace())
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        with glroutines.enabled((gl.GL_CULL_FACE, gl.GL_STENCIL_TEST)), \
             tex.target(xax, yax, lo, hi):

            glroutines.clear((0, 0, 0, 0))
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_STENCIL_BUFFER_BIT)

            # Use a clip-plane shader for steps 1 and 2
            with cpshader.loaded():

                cpshader.set('MVP',       tex.mvpMatrix)
                cpshader.set('clipPlane', clipPlane)

                # We just want to populate the stencil
                # buffer, so set the stencil test to
                # always pass, and suppress draws to
                # the rgba buffer.
                gl.glColorMask(gl.GL_FALSE, gl.GL_FALSE,
                               gl.GL_FALSE, gl.GL_FALSE)
                gl.glStencilFunc(gl.GL_ALWAYS, 0, 0)

                # first pass - draw back faces onto
                # stencil buffer. Second pass -
                # subtract front faces from back
                # faces in the stencil buffer
                faces = [gl.GL_FRONT, gl.GL_BACK]
                dirs  = [gl.GL_INCR,  gl.GL_DECR]
                for face, direction in zip(faces, dirs):
                    gl.glCullFace(face)
                    gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, direction)
                    cpshader.draw(gl.GL_TRIANGLES)

            # Now we have a mask of the cross-section
            # in the stencil buffer - use a "blitting"
            # shader to fill the off screen texture with
            # the flat colour, but mask with the stencil
            # buffer.
            gl.glDisable(gl.GL_CULL_FACE)
            gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE)
            gl.glStencilFunc(gl.GL_NOTEQUAL, 0, 255)

            # disable blending, otherwise we will end up blending
            # with the output of the clip plane shader
            with blshader.loaded(), glroutines.disabled((gl.GL_BLEND, )):
                verts = tex.generateVertices(zpos, xmin, xmax,
                                             ymin, ymax, xax, yax)
                blshader.setAtt('vertex', verts)
                blshader.set(   'MVP',    tex.mvpMatrix)
                blshader.draw(gl.GL_TRIANGLES, 0, 6)

        # Finally, draw the off-screen texture to the display
        tex.drawOnBounds(zpos, xmin, xmax, ymin, ymax, xax, yax, xform)


    def calculateViewport(self, lo, hi, axes, bbox=None):
        """Called by :meth:`drawCrossSection`. Calculates an appropriate
        viewport (the horizontal/vertical minimums/maximums in display
        coordinates) given the ``lo`` and ``hi`` ``GLMesh`` display bounds,
        and a display ``bbox``.

        This is needed to preserve the aspect ratio of the mesh cross-section.
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

        opts   = self.opts
        interp = opts.interpolation
        vdata  = opts.getVertexData(vdtype)

        if vdata is None:
            return None

        # TODO separate modulateDataIndex for modulateData?
        if vdtype == 'vertex': vdata = vdata[:, opts.vertexDataIndex]
        else:                  vdata = vdata[:, 0]

        # when using nn interp, we colour each
        # triangle according to the data value
        # for its first vertex. This should
        # really be pre-generated whenever the
        # vertex data or flat- shading option
        # is changed, but it is quick for
        # typical surfaces, so I'm not
        # bothering for now.
        if self.threedee and (vdata is not None) and interp == 'nearest':
            vdata = vdata[self.origIndices[:, 0]].repeat(3)

        # Used by drawOutline - retrieve the
        # vertex data associated with the faces
        # of the mesh that are intersected by
        # the cross section, and linearly
        # interpolate across the face if needed.
        # Otherwise colour according to the
        # first vertex in each face.
        elif faces is not None and dists is not None:
            if interp == 'linear':
                vdata = vdata[faces].repeat(2, axis=0).reshape(-1, 2, 3)
                vdata = (vdata * dists).reshape(-1, 3).sum(axis=1)
            else:
                vdata = vdata[faces[:, 0]].repeat(2)

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
        if self.flatShader    is not None: self.flatShader   .destroy()
        if self.dataShader    is not None: self.dataShader   .destroy()
        if self.xsectcpShader is not None: self.xsectcpShader.destroy()
        if self.xsectblShader is not None: self.xsectblShader.destroy()

        fslgl.glmesh_funcs.compileShaders(self)


    def updateShaderState(self):
        """Updates the vertex/fragment shader program(s) state, via a call to
        the GL-version specific ``updateShaderState`` function.
        """

        dopts      = self.opts
        flatColour = dopts.getConstantColour()
        useNegCmap = (not dopts.useLut) and dopts.useNegativeCmap

        if dopts.useLut:
            delta     = 1.0 / (dopts.lut.max() + 1)
            cmapXform = affine.scaleOffsetXform(delta, 0.5 * delta)
        else:
            cmapXform = self.cmapTexture.getCoordinateTransform()

        modScale, modOffset = dopts.modulateScaleOffset()

        fslgl.glmesh_funcs.updateShaderState(
            self,
            useNegCmap=useNegCmap,
            cmapXform=cmapXform,
            modScale=modScale,
            modOffset=modOffset,
            flatColour=flatColour)
