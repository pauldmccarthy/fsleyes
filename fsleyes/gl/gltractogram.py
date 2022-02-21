#!/usr/bin/env python
#
# gltractogram.py - Logic for rendering GLTractogram instances.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

"""This module contains logic for rendering :class:`.Tractogram` overlays.
``Tractogram`` rendering is only suppported in 3D, i.e. in the
:class:`.Scene3DCanvas`.
"""


import itertools as it

import numpy     as np
import OpenGL.GL as gl

import fsleyes.gl           as fslgl
import fsleyes.gl.textures  as textures
import fsleyes.gl.globject  as globject
import fsleyes.gl.resources as glresources


class GLTractogram(globject.GLObject):
    """The GLTractogram contains logic for drawing :class:`.Tractogram`
    overlays.
    """

    def __init__(self, overlay, overlayList, displayCtx, canvas, threedee):
        """Create a :meth:`GLTractogram`. """
        globject.GLObject.__init__(
            self, overlay, overlayList, displayCtx, canvas, threedee)

        if not threedee:
            pass

        # Shaders are created in compileShaders.
        # imageTexture created in refreshImageTexture
        # Three separate shader types are used:
        #  - 'orient' - coloured by streamline orientation
        #  - 'vdata'  - coloured by per-vertex/streamline data
        #  - 'idata'  - coloured by data from an Image
        self.shaders        = {'orient' : [], 'vdata' : [], 'idata' : []}
        self.cmapTexture    = textures.ColourMapTexture(self.name)
        self.negCmapTexture = textures.ColourMapTexture(self.name)
        self.imageTexture   = None

        # Orientation is used for RGB colouring.
        # We have to apply abs so that GL doesn't
        # interpolate across -ve/+ve boundaries.
        # when passing from vertex shader through
        # to fragment shader.
        self.vertices = np.asarray(overlay.vertices, dtype=np.float32)
        self.offsets  = np.asarray(overlay.offsets,  dtype=np.int32)
        self.counts   = np.asarray(overlay.lengths,  dtype=np.int32)
        self.orients  = np.abs(overlay.orientation,  dtype=np.float32)

        self.refreshImageTexture()
        self.addListeners()
        self.compileShaders()


    def addListeners(self):
        """Called by :meth:`__init__`. Adds a bunch of property listeners
        to the :class:`.Display` and :class:`.TractogramOpts` instances.
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

        def vdata(*_):
            self.updateVertexData()
            self.notify()

        def idata(*_):
            self.refreshImageTexture()
            self.notifyWhen(self.ready)

        opts   .addListener('resolution',       name, shader,  weak=False)
        opts   .addListener('colourMode',       name, vdata,   weak=False)
        opts   .addListener('lineWidth',        name, refresh, weak=False)
        opts   .addListener('vertexData',       name, vdata,   weak=False)
        opts   .addListener('streamlineData',   name, vdata,   weak=False)
        opts   .addListener('colourImage',      name, idata,   weak=False)
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
        """Called by :meth:`destroy`. Removes all property listeners. """
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
        """Removes listeners and destroys textures and shader programs. """

        if not self.threedee:
            pass

        if self.cmapTexture is not None:
            self.cmapTexture.destroy()

        if self.negCmapTexture is not None:
            self.negCmapTexture.destroy()

        if self.imageTexture is not None:
            self.imageTexture.destroy()

        if self.shaders is not None:
            for shader in it.chain(*self.shaders.values()):
                shader.destroy()

        self.cmapTexture    = None
        self.negCmapTexture = None
        self.imageTexture   = None
        self.shaders        = None

        self.removeListeners()
        globject.GLObject.destroy(self)


    @property
    def destroyed(self):
        """Returns ``True`` if :meth:`destroy` has been called. """
        return self.shaders is None


    def compileShaders(self):
        """Called by :meth:`__init__`. Calls
        :func:`.gl21.gltractogram_funcs.compileShaders` or
        :func:`.gl33.gltractogram_funcs.compileShaders`, passes vertex data to
        the shader programs, and calls :meth:`updateShaderState`
        """
        fslgl.gltractogram_funcs.compileShaders(self)

        for shader in self.shaders['orient']:
            with shader.loaded():
                shader.setAtt('vertex', self.vertices)
                shader.setAtt('data',   self.orients)
        for shader in self.shaders['vdata'] + self.shaders['idata']:
            with shader.loaded():
                shader.setAtt('vertex', self.vertices)

        self.updateShaderState()


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

        for shader in self.shaders['orient']:
            with shader.loaded():
                shader.set('xColour',      colours[0])
                shader.set('yColour',      colours[1])
                shader.set('zColour',      colours[2])
                shader.set('colourScale',  colourScale)
                shader.set('colourOffset', colourOffset)
                shader.set('resolution',   opts.resolution)
                shader.set('lighting',     False)

        for shader in self.shaders['vdata'] + self.shaders['idata']:
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
                shader.set('lighting',      False)

        if opts.colourImage is not None:
            copts     = self.displayCtx.getOpts(opts.colourImage)
            w2tXform  = copts.getTransform('world', 'texture')
            voxXform  = self.imageTexture.voxValXform
            voxScale  = voxXform[0, 0]
            voxOffset = voxXform[0, 3]
            for shader in self.shaders['idata']:
                with shader.loaded():
                    shader.set('imageTexture',  2)
                    shader.set('texCoordXform', w2tXform)
                    shader.set('voxScale',      voxScale)
                    shader.set('voxOffset',     voxOffset)


    def updateVertexData(self):
        """Called when :class:`.TractogramOpts.vertexData` or
        :class:`.TractogramOpts.streamlineData` changes. Passes data to the
        shader programs.
        """

        opts  = self.opts
        ovl   = self.overlay
        cmode = opts.colourMode

        if cmode == 'vertexData' and opts.vertexData is not None:
            data = ovl.getVertexData(opts.vertexData)
        elif cmode == 'streamlineData' and opts.streamlineData is not None:
            data = ovl.getStreamlineDataPerVertex(opts.streamlineData)
        else:
            return

        for shader in self.shaders['vdata']:
            with shader.loaded():
                shader.setAtt('data', data)


    def ready(self):
        """Overrides :meth:`.GLObject.ready`. Returns ``True`` if the
        :attr:`.TractogramOpts.colourImage` is ready (or unset).
        """
        return (self.imageTexture is None) or self.imageTexture.ready()


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


    def refreshImageTexture(self):
        """Called on changes to :attr:`.TractogramOpts.colourImage`.
        Refreshes the :class:`.ImageTexture` object as needed.
        """

        opts   = self.opts
        cimage = opts.colourImage

        if self.imageTexture is not None:
            self.imageTexture.deregister(self.name)
            glresources.delete(self.imageTexture.name)

        if cimage is None:
            return

        texName = '{}_{}'.format(type(self).__name__, id(cimage))
        self.imageTexture = glresources.get(
            texName,
            textures.createImageTexture,
            texName,
            cimage,
            interp=gl.GL_LINEAR,
            notify=False)
        self.imageTexture.register(self.name, self.updateShaderState)


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


    def draw3D(self, xform=None):
        """Binds textures if necessary, then calls
        :func:`.gl21.gltractogram_funcs.draw3D` or
        :func:`.gl33.gltractogram_funcs.draw3D`.
        """

        cmode = self.opts.effectiveColourMode
        cmaps = cmode in ('idata', 'vdata')
        image = cmode ==  'idata'

        if cmaps:
            self.cmapTexture   .bindTexture(gl.GL_TEXTURE0)
            self.negCmapTexture.bindTexture(gl.GL_TEXTURE1)
        if image:
            self.imageTexture.bindTexture(gl.GL_TEXTURE2)

        fslgl.gltractogram_funcs.draw3D(self, xform)

        if cmaps:
            self.cmapTexture   .unbindTexture()
            self.negCmapTexture.unbindTexture()
        if image:
            self.imageTexture.unbindTexture()
