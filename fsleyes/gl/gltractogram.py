#!/usr/bin/env python
#
# gltractogram.py - Logic for rendering GLTractogram instances.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains logic for rendering :class:`.GLTractogram` instances.
"""

import itertools as it

import numpy     as np
import OpenGL.GL as gl

import fsleyes.gl           as fslgl
import fsleyes.gl.textures  as textures
import fsleyes.gl.globject  as globject


class GLTractogram(globject.GLObject):
    """
    """

    def __init__(self, overlay, overlayList, displayCtx, canvas, threedee):
        """
        """
        globject.GLObject.__init__(
            self, overlay, overlayList, displayCtx, canvas, threedee)

        if not threedee:
            pass

        self.cmapTexture    = textures.ColourMapTexture(self.name)
        self.negCmapTexture = textures.ColourMapTexture(self.name)
        self.shaders        = {'data' : [], 'orient' : []}

        self.vertices = np.asarray(overlay.vertices, dtype=np.float32)
        self.offsets  = np.asarray(overlay.offsets,  dtype=np.int32)
        self.counts   = np.asarray(overlay.lengths,  dtype=np.int32)

        # Orientation is used for RGB colouring.
        # We have to apply abs so that GL doesn't
        # interpolate across -ve/+ve boundaries.
        # when passing from vertex shader through
        # to fragment shader.
        self.orients = np.abs(self.opts.orientation)

        self.addListeners()
        self.compileShaders()


    def addListeners(self):
        """
        """
        opts    = self.opts
        display = self.display
        name    = self.name

        def refresh(*_):
            self.notify()

        def shader(*_):
            self.updateShaderState()
            self.notify()

        def cmaps(*_):
            self.refreshCmapTextures()
            self.updateShaderState()
            self.notify()

        def data(*_):
            self.updateVertexData()
            self.notify()

        opts   .addListener('resolution',       name, shader,  weak=False)
        opts   .addListener('colourMode',       name, data,    weak=False)
        opts   .addListener('lineWidth',        name, refresh, weak=False)
        opts   .addListener('vertexData',       name, data,    weak=False)
        opts   .addListener('streamlineData',   name, data,    weak=False)
        opts   .addListener('xColour',          name, shader,  weak=False)
        opts   .addListener('yColour',          name, shader,  weak=False)
        opts   .addListener('zColour',          name, shader,  weak=False)
        opts   .addListener('suppressX',        name, shader,  weak=False)
        opts   .addListener('suppressY',        name, shader,  weak=False)
        opts   .addListener('suppressZ',        name, shader,  weak=False)
        opts   .addListener('suppressMode',     name, shader,  weak=False)
        opts   .addListener('displayRange',     name, cmaps,   weak=False)
        opts   .addListener('clippingRange',    name, shader,  weak=False)
        opts   .addListener('invertClipping',   name, shader,  weak=False)
        opts   .addListener('cmap',             name, cmaps,   weak=False)
        opts   .addListener('negativeCmap',     name, cmaps,   weak=False)
        opts   .addListener('useNegativeCmap',  name, shader,  weak=False)
        opts   .addListener('gamma',            name, cmaps,   weak=False)
        opts   .addListener('logScale',         name, cmaps,   weak=False)
        opts   .addListener('cmapResolution',   name, cmaps,   weak=False)
        opts   .addListener('interpolateCmaps', name, cmaps,   weak=False)
        opts   .addListener('invert',           name, cmaps,   weak=False)
        opts   .addListener('modulateAlpha',    name, shader,  weak=False)
        opts   .addListener('modulateRange',    name, shader,  weak=False)
        display.addListener('alpha',            name, cmaps,   weak=False)


    def removeListeners(self):
        """
        """
        opts    = self.opts
        display = self.display
        name    = self.name

        opts   .removeListener('resolution',       name)
        opts   .removeListener('lineWidth',        name)
        opts   .removeListener('colourMode',       name)
        opts   .removeListener('vertexData',       name)
        opts   .removeListener('streamlineData',   name)
        opts   .removeListener('xColour',          name)
        opts   .removeListener('yColour',          name)
        opts   .removeListener('zColour',          name)
        opts   .removeListener('suppressX',        name)
        opts   .removeListener('suppressY',        name)
        opts   .removeListener('suppressZ',        name)
        opts   .removeListener('suppressMode',     name)
        opts   .removeListener('displayRange',     name)
        opts   .removeListener('clippingRange',    name)
        opts   .removeListener('invertClipping',   name)
        opts   .removeListener('cmap',             name)
        opts   .removeListener('negativeCmap',     name)
        opts   .removeListener('useNegativeCmap',  name)
        opts   .removeListener('gamma',            name)
        opts   .removeListener('logScale',         name)
        opts   .removeListener('cmapResolution',   name)
        opts   .removeListener('interpolateCmaps', name)
        opts   .removeListener('invert',           name)
        opts   .removeListener('modulateAlpha',    name)
        opts   .removeListener('modulateRange',    name)
        display.removeListener('alpha',            name)


    def destroy(self):
        """
        """

        if not self.threedee:
            pass

        if self.cmapTexture is not None:
            self.cmapTexture.destroy()
        if self.negCmapTexture is not None:
            self.negCmapTexture.destroy()

        if self.shaders is not None:
            for shader in it.chain(*self.shaders.values()):
                shader.destroy()

        self.cmapTexture    = None
        self.negCmapTexture = None
        self.shaders        = None

        self.removeListeners()
        fslgl.gltractogram_funcs.destroy(self)
        globject.GLObject.destroy(self)


    def destroyed(self):
        """
        """
        return self.shaders is None


    def compileShaders(self):
        """
        """
        fslgl.gltractogram_funcs.compileShaders(self)

        for shader in self.shaders['orient']:
            with shader.loaded():
                shader.setAtt('vertex', self.vertices)
                shader.setAtt('data',   self.orients)
        for shader in self.shaders['data']:
            with shader.loaded():
                shader.setAtt('vertex', self.vertices)

        self.updateShaderState()


    def updateShaderState(self):
        """
        """
        opts                = self.opts
        colours, xform      = opts.getVectorColours()
        colourScale         = xform[0, 0]
        colourOffset        = xform[0, 3]
        cmapXform           = self.cmapTexture.getCoordinateTransform()
        cmapScale           = cmapXform[0, 0]
        cmapOffset          = cmapXform[0, 3]
        modScale, modOffset = opts.modulateScaleOffset()

        for shader in self.shaders['orient']:
            with shader.loaded():
                shader.set('xColour',      colours[0])
                shader.set('yColour',      colours[1])
                shader.set('zColour',      colours[2])
                shader.set('colourScale',  colourScale)
                shader.set('colourOffset', colourOffset)
                shader.set('resolution',   opts.resolution)

        for shader in self.shaders['data']:
            with shader.loaded():
                shader.set('resolution',    opts.resolution)
                shader.set('cmap',          0)
                shader.set('negCmap',       1)
                shader.set('useNegCmap',    opts.useNegativeCmap)
                shader.set('cmapScale',     cmapScale)
                shader.set('cmapOffset',    cmapOffset)
                shader.set('invertClip',    opts.invertClipping)
                shader.set('clipLow',       opts.clippingRange.xlo)
                shader.set('clipHigh',      opts.clippingRange.xhi)
                shader.set('modulateAlpha', opts.modulateAlpha)
                shader.set('modScale',      modScale)
                shader.set('modOffset',     modOffset)


    def updateVertexData(self):
        """
        """

        opts  = self.opts
        ovl   = self.overlay
        cmode = opts.colourMode

        if cmode == 'orientation':
            return

        if cmode == 'vertexData':
            data = ovl.getVertexData(opts.vertexData)
        elif cmode == 'streamlineData':
            data = ovl.getStreamlineDataPerVertex(opts.streamlineData)

        if data is None:
            return

        for shader in self.shaders['data']:
            with shader.loaded():
                shader.setAtt('data', data)


    def ready(self):
        """Overrides :meth:`.GLObject.ready`. Always returns ``True``. """
        return True


    def getDisplayBounds(self):
        """Overrides :meth:`.GLObject.getDisplayBounds`. Returns a bounding
        box which contains the mesh vertices.
        """
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi())


    @property
    def normalisedLineWidth(self):
        """Returns :attr:`lineWidth`, scaled to normalised device coordinates.
        """
        cw, ch    = self.canvas.GetSize()
        lineWidth = self.opts.lineWidth * max((1 / cw, 1 / ch))
        return lineWidth


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
        logScale = opts.realGamma(opts.gamma)
        invert   = opts.invert
        dmin     = opts.displayRange[0]
        dmax     = opts.displayRange[1]

        if interp: interp = gl.GL_LINEAR
        else:      interp = gl.GL_NEAREST

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


    def draw3D(self, xform=None):

        needTextures = self.opts.effectiveColourMode == 'data'

        if needTextures:
            self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
            self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)
        fslgl.gltractogram_funcs.draw3D(self, xform)
        if needTextures:
            self.cmapTexture   .unbindTexture()
            self.negCmapTexture.unbindTexture()
