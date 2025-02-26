#!/usr/bin/env python
#
# gltractogram.py - Logic for rendering GLTractogram instances.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

"""This module contains logic for rendering :class:`.Tractogram` overlays.
"""


import itertools as it

import numpy     as np
import OpenGL.GL as gl

import fsl.utils.idle       as idle
import fsl.transform.affine as affine
import fsl.data.image       as fslimage

import fsleyes.gl           as fslgl
import fsleyes.gl.textures  as textures
import fsleyes.gl.globject  as globject


class GLTractogram(globject.GLObject):
    """The GLTractogram contains logic for drawing :class:`.Tractogram`
    overlays.
    """

    def __init__(self, overlay, overlayList, displayCtx, threedee):
        """Create a :meth:`GLTractogram`. """
        globject.GLObject.__init__(
            self, overlay, overlayList, displayCtx, threedee)

        # Shaders are created in compileShaders.
        # imageTexture created in refreshImageTexture
        #
        # Three separate shader types are used:
        #  - 'orientation' - coloured by streamline orientation
        #  - 'vertexData'  - coloured by per-vertex/streamline data
        #  - 'imageData'   - coloured by data from an Image
        #
        # Separate shader programs are used depending
        # on the TractogramOpts.clipMode -
        #  - 'none'       - no clipping, or clipping by the same
        #                   data used for colouring
        #  - 'vertexData' - clipping by a separate vertex data set
        #  - 'imageData'  - clipping by a separate image data set
        #
        # Each leaf node is a dict of {<geometry> : GLSLShader}
        # mappings for different geometry shaders. The GL21
        # implementation does not use geometry, and hence will
        # only contains one entry, whereas the GL33 implementation
        # uses geometry shaders for different rendering applications.
        self.shaders = {
            '2D' : {
                'orientation' : {'none' : {}, 'vertexData' : {}, 'imageData' : {}},
                'vertexData'  : {'none' : {}, 'vertexData' : {}, 'imageData' : {}},
                'imageData'   : {'none' : {}, 'vertexData' : {}, 'imageData' : {}}},
            '3D' : {
                'orientation' : {'none' : {}, 'vertexData' : {}, 'imageData' : {}},
                'vertexData'  : {'none' : {}, 'vertexData' : {}, 'imageData' : {}},
                'imageData'   : {'none' : {}, 'vertexData' : {}, 'imageData' : {}}}
        }

        # Scale alpha exponentially in the
        # colour maps (see inline comments in
        # updateShaderState)
        self.cmapmgr        = textures.ColourMapTextureManager(
            self, expalpha=True)
        self.imageTextures  = textures.AuxImageTextureManager(
            self, colour=None, clip=None)

        self.compileShaders()
        self.updateStreamlineData()
        self.refreshImageTexture('clip')
        self.refreshImageTexture('colour')
        self.updateColourData(refresh=False)
        self.updateClipData(refresh=False)
        self.addListeners()

        # Call updateShaderState asynchronously,
        # as it may depend on the image textures
        # being ready, which might be prepared
        # off the main thread.
        if 'imageData' not in (self.opts.colourMode, self.opts.clipMode):
            self.updateShaderState()
        else:
            idle.idleWhen(self.updateShaderState, self.ready)


    def addListeners(self):
        """Called by :meth:`__init__`. Adds a bunch of property listeners
        to the :class:`.Display` and :class:`.TractogramOpts` instances.
        """
        opts    = self.opts
        display = self.display
        name    = self.name

        def refresh(*_):
            self.notify()

        def data(*_):
            self.updateStreamlineData()
            self.notify()

        def shader(*_):
            self.updateShaderState()
            self.notify()

        def cmaps(*_):
            self.updateShaderState()
            self.notify()

        def colour(*_):
            self.updateColourData()
            self.notifyWhen(self.ready)

        def clip(*_):
            self.updateClipData()
            self.updateShaderState()
            self.notifyWhen(self.ready)

        opts   .wlisten('bounds',              name, refresh)
        opts   .wlisten('resolution',          name, shader)
        opts   .wlisten('subsample',           name, data)
        opts   .wlisten('colourMode',          name, colour)
        opts   .wlisten('clipMode',            name, clip)
        opts   .wlisten('lineWidth',           name, refresh)
        opts   .wlisten('sliceWidth',          name, refresh)
        opts   .wlisten('xColour',             name, shader)
        opts   .wlisten('yColour',             name, shader)
        opts   .wlisten('zColour',             name, shader)
        opts   .wlisten('suppressX',           name, shader)
        opts   .wlisten('suppressY',           name, shader)
        opts   .wlisten('suppressZ',           name, shader)
        opts   .wlisten('suppressMode',        name, shader)
        opts   .wlisten('displayRange',        name, cmaps)
        opts   .wlisten('clippingRange',       name, shader)
        opts   .wlisten('invertClipping',      name, shader)
        opts   .wlisten('cmap',                name, cmaps)
        opts   .wlisten('negativeCmap',        name, cmaps)
        opts   .wlisten('useNegativeCmap',     name, shader)
        opts   .wlisten('gamma',               name, cmaps)
        opts   .wlisten('logScale',            name, cmaps)
        opts   .wlisten('cmapResolution',      name, cmaps)
        opts   .wlisten('interpolateCmaps',    name, cmaps)
        opts   .wlisten('invert',              name, cmaps)
        opts   .wlisten('modulateAlpha',       name, shader)
        opts   .wlisten('invertModulateAlpha', name, shader)
        opts   .wlisten('modulateRange',       name, shader)
        opts   .wlisten('pseudo3D',            name, data)
        opts   .wlisten('xclipdir',            name, refresh)
        opts   .wlisten('yclipdir',            name, refresh)
        opts   .wlisten('zclipdir',            name, refresh)
        display.wlisten('alpha',               name, cmaps)


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all property listeners. """
        opts    = self.opts
        display = self.display
        name    = self.name

        opts   .remove('bounds',              name)
        opts   .remove('resolution',          name)
        opts   .remove('subsample',           name)
        opts   .remove('lineWidth',           name)
        opts   .remove('sliceWidth',          name)
        opts   .remove('colourMode',          name)
        opts   .remove('clipMode',            name)
        opts   .remove('xColour',             name)
        opts   .remove('yColour',             name)
        opts   .remove('zColour',             name)
        opts   .remove('suppressX',           name)
        opts   .remove('suppressY',           name)
        opts   .remove('suppressZ',           name)
        opts   .remove('suppressMode',        name)
        opts   .remove('displayRange',        name)
        opts   .remove('clippingRange',       name)
        opts   .remove('invertClipping',      name)
        opts   .remove('cmap',                name)
        opts   .remove('negativeCmap',        name)
        opts   .remove('useNegativeCmap',     name)
        opts   .remove('gamma',               name)
        opts   .remove('logScale',            name)
        opts   .remove('cmapResolution',      name)
        opts   .remove('interpolateCmaps',    name)
        opts   .remove('invert',              name)
        opts   .remove('modulateAlpha',       name)
        opts   .remove('invertModulateAlpha', name)
        opts   .remove('modulateRange',       name)
        opts   .remove('pseudo3D',            name)
        opts   .remove('xclipdir',            name)
        opts   .remove('yclipdir',            name)
        opts   .remove('zclipdir',            name)
        display.remove('alpha',               name)


    def destroy(self):
        """Removes listeners and destroys textures and shader programs. """

        if self.cmapmgr is not None:
            self.cmapmgr.destroy()

        if self.imageTextures is not None:
            self.imageTextures.destroy()

        if self.shaders is not None:
            for shader in self.iterShaders():
                shader.destroy()

        self.cmapmgr        = None
        self.imageTextures  = None
        self.shaders        = None

        self.removeListeners()
        globject.GLObject.destroy(self)


    def iterShaders(self, colourModes=None, clipModes=None, dims=None):
        """Returns all shader programs for the specified colour/clipping
        modes.
        """
        if isinstance(colourModes, str):
            colourModes = [colourModes]
        if isinstance(clipModes, str):
            clipModes = [clipModes]
        if isinstance(dims, str):
            dims = [dims]
        if colourModes is None or len(colourModes) == 0:
            colourModes = ['orientation', 'vertexData', 'imageData']
        if clipModes is None or len(clipModes) == 0:
            clipModes = ['none', 'vertexData', 'imageData']
        if dims is None or len(dims) == 0:
            dims = ['2D', '3D']
        shaders = [self.shaders[d] for d in dims]
        shaders = it.chain(*[[s[m] for m in colourModes] for s in shaders])
        shaders = it.chain(*[[s[m] for m in clipModes]   for s in shaders])
        return it.chain(*[s.values() for s in shaders])


    @property
    def destroyed(self):
        """Returns ``True`` if :meth:`destroy` has been called. """
        return self.shaders is None


    def ready(self):
        """Overrides :meth:`.GLObject.ready`. Returns ``True`` if the
        :attr:`.TractogramOpts.colourImage` is ready (or unset).
        """
        return self.imageTextures.texturesReady()


    def getDisplayBounds(self):
        """Overrides :meth:`.GLObject.getDisplayBounds`. Returns a bounding
        box which contains the mesh vertices.
        """
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi())


    def normalisedLineWidth(self, canvas, mvp, threedee):
        """Returns :attr:`lineWidth`, scaled so that it is with respect to
        normalised device coordinates. Streamline lines/tubes (in 3D) and
        vertices (in 2D) are drawn such that the width/radius is fixed w.r.t.
        the world coordinate system - i.e. for a given ``lineWidth``,
        lines/tubes/circles will be small when zoomed out, and big when
        zoomed in.

        :arg canvas: Canvas being drawn on
        :arg mvp:    Current MVP matrix
        """
        # Line width is fixed at 0.1 in world
        # units. Below we convert it so it is
        # in terms of NDCs.
        lineWidth =  self.opts.lineWidth / 10

        if threedee:
            # We don't apply the scene3d rotation, because
            # the projection matrix adds an uneven scaling
            # to the depth axis (see routines.ortho3D),
            # which will affect scaling when rotated to be
            # in line with that axis.  I may revisit this in
            # the future, as the ortho3D function is a bit
            # nuts in how it handles depth (caused by my
            # lack of understanding of near/far clipping).
            scaling   = affine.concat(canvas.projectionMatrix,
                                      canvas.viewScale)
            lineWidth = [lineWidth * scaling[0, 0],
                         lineWidth * scaling[1, 1]]

        else:
            # return separate scales for each axis
            lineWidth = affine.transform([lineWidth] * 3, mvp, vector=True)
            lineWidth = np.abs(lineWidth[:2])

        return lineWidth


    @property
    def cmapTexture(self):
        """Return the :class:`.ColourMapTexture` associated with
        :attr:`.TractogramOpts.cmap`.
        """
        return self.cmapmgr.cmapTexture


    @property
    def negCmapTexture(self):
        """Return the :class:`.ColourMapTexture` associated with
        :attr:`.TractogramOpts.negativeCmap`.
        """
        return self.cmapmgr.negCmapTexture


    @property
    def clipImageTexture(self):
        """Return a reference to an :class:`.ImageTexture` which contains
        data for clipping, when :attr:`.TractogramOpts.clipMode` is set
        to an :class:`.Image`.
        """
        return self.imageTextures.texture('clip')


    @property
    def colourImageTexture(self):
        """Return a reference to an :class:`.ImageTexture` which contains
        data for colouring, when :attr:`.TractogramOpts.colourMode` is set
        to an :class:`.Image`.
        """
        return self.imageTextures.texture('colour')


    def shaderAttributeArgs(self):
        """Returns keyword arguments to pass to :meth:`.GLSLShader.setAtt`
        for all per-vertex attributes. The GL21 2D rendering logic uses
        instanced rendering, so a divisor must be set for all vertex
        attributes.
        """
        if fslgl.GL_COMPATIBILITY != '2.1':     return {}
        if self.threedee or self.opts.pseudo3D: return {}
        else:                                   return {'divisor' : 1}


    def compileShaders(self):
        """Called by :meth:`__init__`. Calls
        :func:`.gl21.gltractogram_funcs.compileShaders` or
        :func:`.gl33.gltractogram_funcs.compileShaders`, passes vertex data to
        the shader programs, and calls :meth:`updateShaderState`
        """
        fslgl.gltractogram_funcs.compileShaders(self)


    def updateStreamlineData(self):
        """Prepares streamline data and passes it to GL. This method is called
        on creation, and whenever the :attr:`.TractogramOpts.subsample` setting
        changes.

        For 2D views (ortho/lightbox), the tractogram is drawn as ``GL_POINT``
        points using glDrawArrays (or equivalent). For 3D views, streamlines
        are drawn as ``GL_LINE_STRIP`` lines using offsets/counts into the
        vertex array.
        """

        ovl         = self.overlay
        opts        = self.opts
        subsamp     = opts.subsample
        nverts      = ovl.nvertices
        nstrms      = ovl.nstreamlines
        kwargs      = self.shaderAttributeArgs()
        threedee    = self.threedee or opts.pseudo3D
        indices     = None

        # randomly select a subset of streamlines
        # (3D) or vertices (2D).
        if subsamp < 100:
            if threedee: lim = nstrms
            else:        lim = nverts
            n       = int(lim * subsamp / 100)
            indices = np.random.choice(lim, n)
            indices = np.sort(indices)

            if threedee:
                vertices, offsets, counts, indices = ovl.subset(indices)
                orients = ovl.vertexOrientations[indices]
            else:
                offsets, counts = [0], [0]
                vertices        = ovl.vertices[          indices]
                orients         = ovl.vertexOrientations[indices]
        else:
            vertices = ovl.vertices
            orients  = ovl.vertexOrientations
            offsets  = ovl.offsets
            counts   = ovl.lengths

        # Orientation is used for RGB colouring.
        # We have to apply abs so that GL doesn't
        # interpolate across -ve/+ve boundaries.
        # when passing from vertex shader through
        # to fragment shader.
        self.vertices =        np.asarray(vertices, dtype=np.float32)
        self.orients  = np.abs(np.asarray(orients,  dtype=np.float32))
        self.offsets  =        np.asarray(offsets,  dtype=np.int32)
        self.counts   =        np.asarray(counts,   dtype=np.int32)
        self.indices  = indices

        # upload vertices/orients/indices to GL.
        # For 3D, offsets/counts are passed on
        # each draw
        for shader in self.iterShaders('orientation'):
            with shader.loaded():
                shader.setAtt('vertex', self.vertices, **kwargs)
                shader.setAtt('orient', self.orients,  **kwargs)
        for shader in self.iterShaders(('vertexData', 'imageData')):
            with shader.loaded():
                shader.setAtt('vertex', self.vertices, **kwargs)
        if opts.effectiveColourMode == 'vertexData':
            self.updateColourData()
        if opts.effectiveClipMode == 'vertexData':
            self.updateClipData()


    def updateShaderState(self):
        """Passes display properties as uniform values to the shader programs.
        """
        opts                = self.opts
        display             = self.display
        colours, xform      = opts.getVectorColours()
        colourScale         = xform[0, 0]
        colourOffset        = xform[0, 3]
        cmapXform           = self.cmapTexture.getCoordinateTransform()
        cmapScale           = cmapXform[0, 0]
        cmapOffset          = cmapXform[0, 3]
        modScale, modOffset = opts.modulateScaleOffset()
        sameData            = opts.clipMode in (None, opts.colourMode)

        # We scale alpha exponentially as, for a
        # typical tractogram with many streamlines,
        # transparency only starts to take effect
        # when display.alpha ~= 20. Also, when
        # alpha < 100, we draw the tractogram twice
        # - see the gltractogram_funcs.draw3D
        # function for more details.
        if display.alpha < 100:
            alpha         = (display.alpha / 100) ** 2
            colours[0][3] = alpha
            colours[0][3] = alpha
            colours[1][3] = alpha
            colours[2][3] = alpha

        for shader in self.iterShaders('orientation'):
            with shader.loaded():
                shader.set('xColour',      colours[0])
                shader.set('yColour',      colours[1])
                shader.set('zColour',      colours[2])
                shader.set('colourScale',  colourScale)
                shader.set('colourOffset', colourOffset)
                shader.set('resolution',   opts.resolution)

        for shader in self.iterShaders('orientation',
                                       ['vertexData', 'imageData']):
            with shader.loaded():
                shader.set('invertClip',   opts.invertClipping)
                shader.set('applyClip',    opts.clipMode is not None)
                shader.set('clipLow',      opts.clippingRange.xlo)
                shader.set('clipHigh',     opts.clippingRange.xhi)

        for shader in self.iterShaders(['vertexData', 'imageData']):
            with shader.loaded():
                shader.set('resolution',    opts.resolution)
                shader.set('cmap',          0)
                shader.set('negCmap',       1)
                shader.set('useNegCmap',    opts.useNegativeCmap)
                shader.set('cmapScale',     cmapScale)
                shader.set('cmapOffset',    cmapOffset)
                shader.set('sameData',      sameData)
                shader.set('applyClip',     opts.clipMode is not None)
                shader.set('invertClip',    opts.invertClipping)
                shader.set('clipLow',       opts.clippingRange.xlo)
                shader.set('clipHigh',      opts.clippingRange.xhi)
                shader.set('modulateAlpha', opts.modulateAlpha)
                shader.set('modScale',      modScale)
                shader.set('modOffset',     modOffset)


    def updateColourData(self, refresh=True):
        """Called when :class:`.TractogramOpts.colourMode` changes. Passes
        data to the shader programs.
        """

        opts    = self.opts
        ovl     = self.overlay
        indices = self.indices
        cmode   = opts.effectiveColourMode
        kwargs  = self.shaderAttributeArgs()

        if cmode == 'orientation':
            return

        if cmode == 'vertexData':
            data = ovl.getVertexData(opts.colourMode)
            if indices is not None:
                data = data[indices]
            for shader in self.iterShaders('vertexData'):
                with shader.loaded():
                    shader.setAtt('vertexData', data, **kwargs)

        if refresh and cmode == 'imageData':
            self.refreshImageTexture('colour')


    def updateClipData(self, refresh=True):
        """Called when :class:`.TractogramOpts.clipMode` changes. Passes
        data to the shader programs.
        """

        opts    = self.opts
        ovl     = self.overlay
        indices = self.indices
        cmode   = opts.effectiveClipMode
        kwargs  = self.shaderAttributeArgs()

        if cmode == 'none':
            return

        if cmode == 'vertexData':
            data = ovl.getVertexData(opts.clipMode)
            if indices is not None:
                data = data[indices]
            for shader in self.iterShaders(None, 'vertexData'):
                with shader.loaded():
                    shader.setAtt('clipVertexData', data, **kwargs)

        elif refresh and cmode == 'imageData':
            self.refreshImageTexture('clip')


    def refreshImageTexture(self, which):
        """Called on changes to :attr:`.TractogramOpts.colourMode` and
        :attr:`.TractogramOpts.clipMode`. Refreshes the :class:`.ImageTexture`
        objects as needed.
        """

        opts = self.opts

        if which == 'colour': image = opts.colourMode
        else:                 image = opts.clipMode

        # Not currently colouring/clipping by image.
        if not isinstance(image, fslimage.Image):
            return

        # image already registered
        if image is self.imageTextures.image(which):
            return

        # When the texture has been prepared,
        # we need to tell the shader programs
        # how to use it.
        if which == 'colour': callback = self.colourImageTextureChanged
        else:                 callback = self.clipImageTextureChanged

        self.imageTextures.registerAuxImage(
            which, image, callback=callback, notify=True)
        self.imageTextures.texture(which).register(self.name, callback)


    def colourImageTextureChanged(self, *_):
        """Calls :meth:`imageTextureChanged`. """
        self.imageTextureChanged('colour')


    def clipImageTextureChanged(self, *_):
        """Calls :meth:`imageTextureChanged`. """
        self.imageTextureChanged('clip')


    def imageTextureChanged(self, which):
        """Called when :attr:`.TractogramOpts.colourMode` or
        :attr:`.TractogramOpts.clipMode` is set to an image, and the
        underlying :class:`.ImageTexture` changes. Sets some shader uniforms
        accordingly.
        """

        if which == 'colour': image = self.opts.colourMode
        else:                 image = self.opts.clipMode

        texture   = self.imageTextures.texture(which)
        opts      = self.displayCtx.getOpts(image)
        w2tXform  = opts.getTransform('world', 'texture')
        voxXform  = texture.voxValXform
        voxScale  = voxXform[0, 0]
        voxOffset = voxXform[0, 3]

        if which == 'colour':
            for shader in self.iterShaders('imageData'):
                with shader.loaded():
                    shader.set('imageTexture',  2)
                    shader.set('texCoordXform', w2tXform)
                    shader.set('voxScale',      voxScale)
                    shader.set('voxOffset',     voxOffset)
        elif which == 'clip':
            for shader in self.iterShaders([], ['imageData']):
                with shader.loaded():
                    shader.set('clipTexture',       3)
                    shader.set('clipTexCoordXform', w2tXform)
                    shader.set('clipValScale',      voxScale)
                    shader.set('clipValOffset',     voxOffset)


    def preDraw(self):
        """Called before :meth:`draw2D`/:meth:`draw3D`. Binds textures as
        needed.
        """

        colourMode = self.opts.effectiveColourMode
        clipMode   = self.opts.effectiveClipMode

        cmaps     = colourMode in ('imageData', 'vertexData')
        colourTex = colourMode == 'imageData'
        clipTex   = clipMode   == 'imageData'

        if cmaps:
            self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
            self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)
        if colourTex:
            self.colourImageTexture.bindTexture(gl.GL_TEXTURE2)
        if clipTex:
            self.clipImageTexture.bindTexture(gl.GL_TEXTURE3)


    def draw2D(self, canvas, zpos, axes, xform=None):
        """Draws a 2D slice through the tractogram. Calls
        :func:`.gl21.gltractogram_funcs.draw2D` or
        :func:`.gl33.gltractogram_funcs.draw2D`.
        """

        # Draw 3D tractogram on 2D canvas
        if self.opts.pseudo3D:
            self.drawPseudo3D(canvas, zpos, axes, xform)
            return

        if xform is None:
            xform = np.eye(4)

        opts = self.opts
        zax  = axes[2]

        # We draw a 2D slice through the tractogram by
        # manipulating the projection matrix so that z
        # coordinates within the slice are mapped to
        # the range (-1, +1). Vertices with z outside
        # of that range will be clipped by GL.
        step    = opts.calculateSliceWidth(zax)
        zmin    = zpos - step
        zmax    = zpos + step
        viewmat = canvas.viewMatrix
        projmat = canvas.calculateViewport(
            zmin=zmin, zmax=zmax, expandz=False)[1]

        # Make sure that the scales have the same
        # sign as the rotations in the view matrix
        # produced by gl.routines.show2D
        if np.sign(projmat[2, 2]) != np.sign(viewmat[2, :2].sum()):
            projmat[2, 2] *= -1

        strm2disp = opts.getTransform(to='display')
        mvp       = affine.concat(projmat, viewmat, xform, strm2disp)

        fslgl.gltractogram_funcs.draw2D(self, canvas, mvp)


    def drawPseudo3D(self, canvas, zpos, axes, xform=None):
        """Draws a 3D rendering of the tractogram onto a 2D canvas.

        Calls :func:`.gl21.gltractogram_funcs.drawPseudo3D` or
        :func:`.gl33.gltractogram_funcs.drawPseudo3D`.
        """
        if xform is None:
            xform = np.eye(4)

        opts = self.opts
        zax  = axes[2]

        if   zax == 0: clipdir = opts.xclipdir
        elif zax == 1: clipdir = opts.yclipdir
        elif zax == 2: clipdir = opts.zclipdir

        if clipdir != 'none':

            step       = opts.calculateSliceWidth(zax)
            zmin, zmax = canvas.viewport[zax]

            if   clipdir == 'low':  zmin       = zpos
            elif clipdir == 'high': zmax       = zpos
            else:                   zmin, zmax = zpos - step, zpos + step

            # manipulate projection matrix to
            # clip vertices - see notes in draw2D
            viewmat = canvas.viewMatrix
            projmat = canvas.calculateViewport(
                zmin=zmin, zmax=zmax, expandz=False)[1]

            if np.sign(projmat[2, 2]) != np.sign(viewmat[2, :2].sum()):
                projmat[2, 2] *= -1

        else:
            projmat = np.array(canvas.projectionMatrix)

        viewmat   = canvas.viewMatrix
        strm2disp = opts.getTransform(to='display')
        mvp       = affine.concat(projmat, viewmat, xform, strm2disp)

        fslgl.gltractogram_funcs.drawPseudo3D(self, canvas, mvp)


    def draw3D(self, canvas, xform=None):
        """Calls :func:`.gl21.gltractogram_funcs.draw3D` or
        :func:`.gl33.gltractogram_funcs.draw3D`.
        """
        mvp       = canvas.mvpMatrix
        lighting  = canvas.opts.light
        lightPos  = affine.transform(canvas.lightPos, mvp)
        strm2disp = self.opts.getTransform(to='display')
        mvp       = affine.concat(mvp, strm2disp)

        fslgl.gltractogram_funcs.draw3D(
            self, canvas, mvp, lighting, lightPos, xform=xform)


    def postDraw(self):
        """Called after :meth:`draw2D`/:meth:`draw3D`. Unbinds textures as
        needed.
        """

        colourMode = self.opts.effectiveColourMode
        clipMode   = self.opts.effectiveClipMode

        cmaps     = colourMode in ('imageData', 'vertexData')
        colourTex = colourMode == 'imageData'
        clipTex   = clipMode   == 'imageData'

        if cmaps:
            self.cmapTexture   .unbindTexture()
            self.negCmapTexture.unbindTexture()
        if colourTex:
            self.colourImageTexture.unbindTexture()
        if clipTex:
            self.clipImageTexture.unbindTexture()
