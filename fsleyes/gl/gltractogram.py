#!/usr/bin/env python
#
# gltractogram.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


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

        fslgl.gltractogram_funcs.compileShaders(self)

        self.__refreshData()


    def destroy(self):
        """
        """
        globject.GLObject.destroy(self)
        if not self.threedee:
            pass


    def destroyed(self):
        """
        """
        pass


    def ready(self):
        """Overrides :meth:`.GLObject.ready`. Always returns ``True``. """
        return True


    def getDisplayBounds(self):
        """Overrides :meth:`.GLObject.getDisplayBounds`. Returns a bounding
        box which contains the mesh vertices.
        """
        return (self.opts.bounds.getLo(),
                self.opts.bounds.getHi())


    def __refreshData(self, *a):

        ovl  = self.overlay
        opts = self.opts

        self.vertices = np.asarray(ovl.vertices, dtype=np.float32)
        self.offsets  = np.asarray(ovl.offsets,  dtype=np.int32)
        self.counts   = np.asarray(ovl.lengths,  dtype=np.int32)
        self.orients  = opts.orientation
        fslgl.gltractogram_funcs.updateShaderState(self)


    def preDraw(self, xform=None, bbox=None):
        pass


    def draw2D(self, zpos, axes, xform=None, bbox=None):
        pass


    def draw3D(self, xform=None, bbox=None):
        fslgl.gltractogram_funcs.draw3D(self, xform, bbox)


    def postDraw(self, xform=None, bbox=None):
        pass
