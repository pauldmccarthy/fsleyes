#!/usr/bin/env python
#
# gltractogram.py - Logic for rendering GLTractogram instances.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains logic for rendering :class:`.GLTractogram` instances.
"""


import numpy     as np
import OpenGL.GL as gl

import fsleyes.gl          as fslgl
import fsleyes.gl.shaders  as shaders
import fsleyes.gl.globject as globject


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

        self.shader = None

        fslgl.gltractogram_funcs.compileShaders(self)
        self.prepareData()
        self.addListeners()

        with self.shader.loaded():
            self.updateShaderState()
            self.shader.setAtt('vertex', self.vertices)
            self.shader.setAtt('orient', self.orients)


    def destroy(self):
        """
        """

        if not self.threedee:
            pass

        self.removeListeners()
        globject.GLObject.destroy(self)


    def destroyed(self):
        """
        """
        pass


    def prepareData(self, *a):

        ovl  = self.overlay
        opts = self.opts

        self.vertices = np.asarray(ovl.vertices, dtype=np.float32)
        self.offsets  = np.asarray(ovl.offsets,  dtype=np.int32)
        self.counts   = np.asarray(ovl.lengths,  dtype=np.int32)
        self.orients  = opts.orientation


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

        opts   .addListener('xColour',      name, shader,  weak=False)
        opts   .addListener('yColour',      name, shader,  weak=False)
        opts   .addListener('zColour',      name, shader,  weak=False)
        opts   .addListener('suppressX',    name, shader,  weak=False)
        opts   .addListener('suppressY',    name, shader,  weak=False)
        opts   .addListener('suppressZ',    name, shader,  weak=False)
        opts   .addListener('suppressMode', name, shader,  weak=False)
        opts   .addListener('resolution',   name, shader,  weak=False)
        opts   .addListener('lineWidth',    name, refresh, weak=False)
        display.addListener('brightness',   name, shader,  weak=False)
        display.addListener('contrast',     name, shader,  weak=False)
        display.addListener('alpha',        name, shader,  weak=False)


    def removeListeners(self):
        """
        """
        opts    = self.opts
        display = self.display
        name    = self.name

        opts   .removeListener('xColour',      name)
        opts   .removeListener('yColour',      name)
        opts   .removeListener('zColour',      name)
        opts   .removeListener('suppressX',    name)
        opts   .removeListener('suppressY',    name)
        opts   .removeListener('suppressZ',    name)
        opts   .removeListener('suppressMode', name)
        opts   .removeListener('resolution',   name)
        opts   .removeListener('lineWidth',    name)
        display.removeListener('brightness',   name)
        display.removeListener('contrast',     name)
        display.removeListener('alpha',        name)


    def ready(self):
        """Overrides :meth:`.GLObject.ready`. Always returns ``True``. """
        return True


    def getDisplayBounds(self):
        """Overrides :meth:`.GLObject.getDisplayBounds`. Returns a bounding
        box which contains the mesh vertices.
        """
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi())


    def updateShaderState(self, *_):

        opts           = self.opts
        shader         = self.shader
        colours, xform = opts.getVectorColours()
        scale          = xform[0, 0]
        offset         = xform[0, 3]

        with shader.loaded():

            shader.set('xColour',      colours[0])
            shader.set('yColour',      colours[1])
            shader.set('zColour',      colours[2])
            shader.set('colourScale',  scale)
            shader.set('colourOffset', offset)

            # GL33 only
            shader.set('resolution',   opts.resolution)


    def preDraw(self):
        pass


    def draw2D(self, zpos, axes, xform=None):
        pass


    def draw3D(self, xform=None):
        fslgl.gltractogram_funcs.draw3D(self, xform)


    def postDraw(self):
        pass
