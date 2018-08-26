#!/usr/bin/env python
#
# glmip.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from . import glimageobject


class GLMIP(glimageobject.GLImageObject):

    def __init__(self, image, overlayList, displayCtx, canvas, threedee):
        print('Yargh')


    def destroy(self):
        pass


    def ready(self):
        return True

    def preDraw(self, xform=None, bbox=None):
        pass

    def draw2D(self, zpos, axes, xform=None, bbox=None):
        pass

    def draw3D(self, xform=None, bbox=None):
        pass

    def postDraw(self, xform=None, bbox=None):
        pass
