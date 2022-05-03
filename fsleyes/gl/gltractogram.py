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
        self.shaders        = {
            'orientation' : {'none' : [], 'vertexData' : [], 'imageData' : []},
            'vertexData'  : {'none' : [], 'vertexData' : [], 'imageData' : []},
            'imageData'   : {'none' : [], 'vertexData' : [], 'imageData' : []}}
        self.cmapTexture    = textures.ColourMapTexture(self.name)
        self.negCmapTexture = textures.ColourMapTexture(self.name)
        self.imageTextures  = textures.AuxImageTextureManager(
            self, colour=None, clip=None)

        self.compileShaders()
        self.updateStreamlineData()
        self.refreshImageTexture('clip')
        self.refreshImageTexture('colour')
        self.refreshCmapTextures()
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
            self.refreshCmapTextures()
            self.updateShaderState()
            self.notify()

        def colour(*_):
            self.updateColourData()
            self.notifyWhen(self.ready)

        def clip(*_):
            self.updateClipData()
            self.notifyWhen(self.ready)

        opts   .addListener('resolution',          name, shader,  weak=False)
        opts   .addListener('subsample',           name, data,    weak=False)
        opts   .addListener('colourMode',          name, colour,  weak=False)
        opts   .addListener('clipMode',            name, clip,    weak=False)
        opts   .addListener('lineWidth',           name, refresh, weak=False)
        opts   .addListener('xColour',             name, shader,  weak=False)
        opts   .addListener('yColour',             name, shader,  weak=False)
        opts   .addListener('zColour',             name, shader,  weak=False)
        opts   .addListener('suppressX',           name, shader,  weak=False)
        opts   .addListener('suppressY',           name, shader,  weak=False)
        opts   .addListener('suppressZ',           name, shader,  weak=False)
        opts   .addListener('suppressMode',        name, shader,  weak=False)
        opts   .addListener('displayRange',        name, cmaps,   weak=False)
        opts   .addListener('clippingRange',       name, shader,  weak=False)
        opts   .addListener('invertClipping',      name, shader,  weak=False)
        opts   .addListener('cmap',                name, cmaps,   weak=False)
        opts   .addListener('negativeCmap',        name, cmaps,   weak=False)
        opts   .addListener('useNegativeCmap',     name, shader,  weak=False)
        opts   .addListener('gamma',               name, cmaps,   weak=False)
        opts   .addListener('logScale',            name, cmaps,   weak=False)
        opts   .addListener('cmapResolution',      name, cmaps,   weak=False)
        opts   .addListener('interpolateCmaps',    name, cmaps,   weak=False)
        opts   .addListener('invert',              name, cmaps,   weak=False)
        opts   .addListener('modulateAlpha',       name, shader,  weak=False)
        opts   .addListener('invertModulateAlpha', name, shader,  weak=False)
        opts   .addListener('modulateRange',       name, shader,  weak=False)
        display.addListener('alpha',               name, cmaps,   weak=False)


    def removeListeners(self):
        """Called by :meth:`destroy`. Removes all property listeners. """
        opts    = self.opts
        display = self.display
        name    = self.name

        opts   .removeListener('resolution',          name)
        opts   .removeListener('subsample',           name)
        opts   .removeListener('lineWidth',           name)
        opts   .removeListener('colourMode',          name)
        opts   .removeListener('clipMode',            name)
        opts   .removeListener('xColour',             name)
        opts   .removeListener('yColour',             name)
        opts   .removeListener('zColour',             name)
        opts   .removeListener('suppressX',           name)
        opts   .removeListener('suppressY',           name)
        opts   .removeListener('suppressZ',           name)
        opts   .removeListener('suppressMode',        name)
        opts   .removeListener('displayRange',        name)
        opts   .removeListener('clippingRange',       name)
        opts   .removeListener('invertClipping',      name)
        opts   .removeListener('cmap',                name)
        opts   .removeListener('negativeCmap',        name)
        opts   .removeListener('useNegativeCmap',     name)
        opts   .removeListener('gamma',               name)
        opts   .removeListener('logScale',            name)
        opts   .removeListener('cmapResolution',      name)
        opts   .removeListener('interpolateCmaps',    name)
        opts   .removeListener('invert',              name)
        opts   .removeListener('modulateAlpha',       name)
        opts   .removeListener('invertModulateAlpha', name)
        opts   .removeListener('modulateRange',       name)
        display.removeListener('alpha',               name)


    def destroy(self):
        """Removes listeners and destroys textures and shader programs. """

        if self.cmapTexture is not None:
            self.cmapTexture.destroy()

        if self.negCmapTexture is not None:
            self.negCmapTexture.destroy()

        if self.imageTextures is not None:
            self.imageTextures.destroy()

        if self.shaders is not None:
            for shader in self.iterShaders():
                shader.destroy()

        self.cmapTexture    = None
        self.negCmapTexture = None
        self.imageTextures  = None
        self.shaders        = None

        self.removeListeners()
        globject.GLObject.destroy(self)


    def iterShaders(self, colourModes=None, clipModes=None):
        """Returns all shader programs for the specified colour/clipping
        modes.
        """
        if isinstance(colourModes, str):
            colourModes = [colourModes]
        if isinstance(clipModes, str):
            clipModes = [clipModes]
        if colourModes is None or len(colourModes) == 0:
            colourModes = ['orientation', 'vertexData', 'imageData']
        if clipModes is None or len(clipModes) == 0:
            clipModes = ['none', 'vertexData', 'imageData']
        shaders = [self.shaders[m] for m in colourModes]
        shaders = it.chain(*[[s[m] for m in clipModes] for s in shaders])
        return it.chain(*shaders)


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


    def normalisedLineWidth(self, canvas, mvp):
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

        if self.threedee:
            # We don't apply the scene3d rotation, because
            # the projection matrix adds an uneven scaling
            # to the depth axis (see routines.ortho3D),
            # which will affect scaling when rotated to be
            # in line with that axis.  I may revisit this in
            # the future, as the ortho3D function is a bit
            # nuts in how it handles depth (caused my my
            # lack of understanding of near/far clipping).
            scaling   = affine.concat(canvas.projectionMatrix,
                                      canvas.viewScale)
            lineWidth = [lineWidth * scaling[0, 0],
                         lineWidth * scaling[1, 1]]

        else:
            # return separate scales for each axis
            lineWidth = affine.transform([lineWidth] * 3, mvp, vector=True)

        return lineWidth


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
        if fslgl.GL_COMPATIBILITY != '2.1': return {}
        if self.threedee:                   return {}
        else:                               return {'divisor' : 1}


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
        threedee    = self.threedee
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


    def refreshCmapTextures(self):
        """Called when various :class:`.Display` or :class:`.TractogramOpts``
        properties change. Refreshes the :class:`.ColourMapTexture` instances
        corresponding to the :attr:`.TractogramOpts.cmap` and
        :attr:`.TractogramOpts.negativeCmap` properties.
        """

        display  = self.display
        opts     = self.opts
        alpha    = display.alpha / 100.0
        cmap     = opts.cmap
        interp   = opts.interpolateCmaps
        res      = opts.cmapResolution
        negCmap  = opts.negativeCmap
        gamma    = opts.realGamma(opts.gamma)
        logScale = opts.logScale
        invert   = opts.invert
        dmin     = opts.displayRange[0]
        dmax     = opts.displayRange[1]

        if interp: interp = gl.GL_LINEAR
        else:      interp = gl.GL_NEAREST

        # Scale alpha exponentially (see inline
        # comments in updateShaderState)
        if alpha < 1:
            alpha = alpha ** 2

        self.cmapTexture.set(cmap=cmap,
                             invert=invert,
                             alpha=alpha,
                             resolution=res,
                             gamma=gamma,
                             logScale=logScale,
                             interp=interp,
                             displayRange=(dmin, dmax))

        self.negCmapTexture.set(cmap=negCmap,
                                invert=invert,
                                alpha=alpha,
                                resolution=res,
                                gamma=gamma,
                                logScale=logScale,
                                interp=interp,
                                displayRange=(dmin, dmax))


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

        if xform is None:
            xform = np.eye(4)

        opts = self.opts
        zax  = axes[2]

        # We draw a 2D slice through the tractogram by
        # manipulating the projection matrix so that z
        # coordinates within the slice are mapped to
        # the range (-1, +1). Vertices with z outside
        # of that range will be clipped by GL.
        projmat       = np.array(canvas.projectionMatrix)
        step          = opts.sliceWidth(zax)
        zlo           = zpos - step
        zhi           = zpos + step
        projmat[2, 2] = 2 / (zhi - zlo)
        projmat[2, 3] = -(zhi + zlo) / (zhi - zlo)

        # The routines.show2D function encodes a
        # -ve scale on the yaxis in the view
        # matrix.  We need to accommodate it
        # here.
        if zax == 1:
            projmat[2, 2] *= -1

        viewmat   = canvas.viewMatrix
        strm2disp = opts.displayTransform
        mvp       = affine.concat(projmat, viewmat, xform, strm2disp)

        fslgl.gltractogram_funcs.draw2D(self, canvas, mvp)


    def draw3D(self, *args, **kwargs):
        """Calls :func:`.gl21.gltractogram_funcs.draw3D` or
        :func:`.gl33.gltractogram_funcs.draw3D`.
        """
        fslgl.gltractogram_funcs.draw3D(self, *args, **kwargs)


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
