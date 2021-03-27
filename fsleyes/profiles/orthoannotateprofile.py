#!/usr/bin/env python
#
# orthoannotateprofile.py - The OrthoAnnotateProfile
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoAnnotateProfile` class, an
interaction :class:`.Profile` for :class:`.OrthoPanel` views.
"""

import numpy as np
import          wx

import fsleyes_widgets.dialog            as fsldlg
import fsleyes.gl.annotations            as annotations
import fsleyes.profiles.orthoviewprofile as orthoviewprofile


class OrthoAnnotateProfile(orthoviewprofile.OrthoViewProfile):
    """The ``OrthoAnnotateProfile`` class is a :class:`.Profile` for the
    :class:`.OrthoPanel` class, which allows the user to annotate the
    canvases of an ``OrthoPanel`` with simple shapes and text.
    """


    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create an ``OrthoAnnotateProfile``.

        :arg viewPanel:    An :class:`.OrthoPanel` instance.
        :arg overlayList:  The :class:`.OverlayList` instance.
        :arg displayCtx:   The :class:`.DisplayContext` instance.
        """

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            viewPanel,
            overlayList,
            displayCtx,
            ['line', 'point', 'rect', 'text', 'circle'])
        self.mode = 'nav'

        self.__draggingAnnotation = None


    def _lineModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        opts  = canvas.opts
        annot = canvas.getAnnotations()
        pos   = (canvasPos[opts.xax], canvasPos[opts.yax])
        line  = annot.line(pos, pos, hold=True)
        self.__draggingAnnotation = line


    def _lineModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        opts = canvas.opts
        pos  = (canvasPos[opts.xax], canvasPos[opts.yax])
        self.__draggingAnnotation.xy2 = pos
        canvas.Refresh()


    def _lineModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        line  = self.__draggingAnnotation
        annot = canvas.getAnnotations()
        if line.xy1 == line.xy2:
            annot.dequeue(line, hold=True)
        self.__draggingAnnotation = None
        canvas.Refresh()


    def _pointModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        opts  = canvas.opts
        annot = canvas.getAnnotations()
        pos   = (canvasPos[opts.xax], canvasPos[opts.yax])
        point = annot.point(pos, hold=True)
        self.__draggingAnnotation = point
        canvas.Refresh()


    def _pointModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        opts = canvas.opts
        pos  = (canvasPos[opts.xax], canvasPos[opts.yax])
        self.__draggingAnnotation.xy = pos
        canvas.Refresh()


    def _textModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        annot = canvas.getAnnotations()
        dlg   = fsldlg.TextEditDialog(self.viewPanel,
                                      style=fsldlg.TED_OK_CANCEL)

        if dlg.ShowModal() == wx.ID_OK:
            annot.text(dlg.GetText(),
                       canvasPos,
                       coordinates='display',
                       hold=True)
            canvas.Refresh()


    def _rectModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        opts  = canvas.opts
        annot = canvas.getAnnotations()
        pos   = (canvasPos[opts.xax], canvasPos[opts.yax])
        rect  = annot.rect(pos, 0, 0, hold=True)
        self.__draggingAnnotation = rect


    def _rectModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        opts   = canvas.opts
        rect   = self.__draggingAnnotation
        rect.w = canvasPos[opts.xax] - rect.xy[0]
        rect.h = canvasPos[opts.yax] - rect.xy[1]
        canvas.Refresh()


    def _rectModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        rect  = self.__draggingAnnotation
        annot = canvas.getAnnotations()
        if rect.w == 0 or rect.h == 0:
            annot.dequeue(rect, hold=True)
        self.__draggingAnnotation = None
        canvas.Refresh()


    def _circleModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        opts   = canvas.opts
        annot  = canvas.getAnnotations()
        pos    = (canvasPos[opts.xax], canvasPos[opts.yax])
        circle = annot.circle(pos, 0, filled=True, hold=True)
        self.__draggingAnnotation = circle


    def _circleModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        opts          = canvas.opts
        circle        = self.__draggingAnnotation
        p1            = np.array(circle.xy)
        p2            = np.array((canvasPos[opts.xax], canvasPos[opts.yax]))
        circle.radius = np.sqrt(np.sum((p1 - p2) ** 2))
        canvas.Refresh()


    def _circleModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        circle = self.__draggingAnnotation
        annot  = canvas.getAnnotations()
        if circle.radius == 0:
            annot.dequeue(circle, hold=True)
        self.__draggingAnnotation = None
        canvas.Refresh()
