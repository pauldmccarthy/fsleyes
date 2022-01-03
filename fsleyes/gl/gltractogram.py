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
        return (self.overlay.bounds.getLo(),
                self.overlay.bounds.getHi())


    def preDraw(self, xform=None, bbox=None):
        if not self.threedee:
            pass
        fslgl.gltractogram_funcs.preDraw(self, xform=None, bbox=None)

    def draw2D(self, zpos, axes, xform=None, bbox=None):
        pass

    def draw3D(self, xform=None, bbox=None):

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glMultMatrixf(np.array(xform, dtype=np.float32).ravel('F'))
        fslgl.gltractogram_funcs.draw3D(self, xform, bbox)
        if xform is not None:
            gl.glPopMatrix()


    def postDraw(self, xform=None, bbox=None):
        if not self.threedee:
            pass
