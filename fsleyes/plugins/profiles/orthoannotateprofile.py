#!/usr/bin/env python
#
# orthoannotateprofile.py - The OrthoAnnotateProfile
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoAnnotateProfile` class, an
interaction :class:`.Profile` for :class:`.OrthoPanel` views.
"""

import copy

import numpy as np
import          wx

import fsleyes_widgets.utils.status      as status
import fsleyes_widgets.dialog            as fsldlg
import fsleyes.strings                   as strings
import fsleyes.gl.annotations            as annotations
import fsleyes.profiles.orthoviewprofile as orthoviewprofile


class OrthoAnnotateProfile(orthoviewprofile.OrthoViewProfile):
    """The ``OrthoAnnotateProfile`` class is a :class:`.Profile` for the
    :class:`.OrthoPanel` class, which allows the user to annotate the
    canvases of an ``OrthoPanel`` with simple shapes and text.
    """


    colour = copy.copy(annotations.AnnotationObject.colour)
    """Initial colour to give all annotations. """


    lineWidth =  copy.copy(annotations.AnnotationObject.lineWidth)
    """Initial width to give line-based annotations. """


    fontSize = copy.copy(annotations.TextAnnotation.fontSize)
    """Initial font size to give text annotations. """


    filled = copy.copy(annotations.Rect.filled)
    """Whether ellipses/rectangles are filled in or not."""


    border = copy.copy(annotations.Rect.border)
    """Whether ellipses/rectangles are drawn with a border or not."""


    honourZLimits = copy.copy(annotations.AnnotationObject.honourZLimits)
    """Whether annotations are drawn when outside their Z limits."""


    alpha = copy.copy(annotations.AnnotationObject.alpha)
    """Opacity."""


    @staticmethod
    def tempModes():
        """Returns the temporary mode map for the ``OrthoAnnotateProfile``,
        which controls the use of modifier keys to temporarily enter other
        interaction modes.
        """
        return {
            ('line',     wx.WXK_SHIFT)                  : 'nav',
            ('line',     wx.WXK_CONTROL)                : 'move',
            ('line',     wx.WXK_ALT)                    : 'pan',
            ('line',    (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice',
            ('point',    wx.WXK_SHIFT)                  : 'nav',
            ('point',    wx.WXK_CONTROL)                : 'move',
            ('point',    wx.WXK_ALT)                    : 'pan',
            ('point',   (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice',
            ('rect',     wx.WXK_SHIFT)                  : 'nav',
            ('rect',     wx.WXK_CONTROL)                : 'move',
            ('rect',     wx.WXK_ALT)                    : 'pan',
            ('rect',    (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice',
            ('text',     wx.WXK_SHIFT)                  : 'nav',
            ('text',     wx.WXK_CONTROL)                : 'move',
            ('text',     wx.WXK_ALT)                    : 'pan',
            ('text',    (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice',
            ('ellipse',  wx.WXK_SHIFT)                  : 'nav',
            ('ellipse',  wx.WXK_CONTROL)                : 'move',
            ('ellipse',  wx.WXK_ALT)                    : 'pan',
            ('ellipse', (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice',
            ('arrow',    wx.WXK_SHIFT)                  : 'nav',
            ('arrow',    wx.WXK_CONTROL)                : 'move',
            ('arrow',    wx.WXK_ALT)                    : 'pan',
            ('arrow',   (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice'}


    @staticmethod
    def altHandlers():
        """Returns the alternate handlers map, which allows event handlers
        defined in one mode to be re-used whilst in another mode.
        """
        return {
            ('line',    'MiddleMouseDrag') : ('pan', 'LeftMouseDrag'),
            ('point',   'MiddleMouseDrag') : ('pan', 'LeftMouseDrag'),
            ('rect',    'MiddleMouseDrag') : ('pan', 'LeftMouseDrag'),
            ('text',    'MiddleMouseDrag') : ('pan', 'LeftMouseDrag'),
            ('arrow',   'MiddleMouseDrag') : ('pan', 'LeftMouseDrag'),
            ('ellipse', 'MiddleMouseDrag') : ('pan', 'LeftMouseDrag'),

            ('move',    'MouseWheel') : ('zoom', 'MouseWheel'),

            # Right mouse click/drag allows
            # annotations to be moved
            ('nav',     'RightMouseDown') : ('move', 'LeftMouseDown'),
            ('line',    'RightMouseDown') : ('move', 'LeftMouseDown'),
            ('point',   'RightMouseDown') : ('move', 'LeftMouseDown'),
            ('rect',    'RightMouseDown') : ('move', 'LeftMouseDown'),
            ('text',    'RightMouseDown') : ('move', 'LeftMouseDown'),
            ('arrow',   'RightMouseDown') : ('move', 'LeftMouseDown'),
            ('ellipse', 'RightMouseDown') : ('move', 'LeftMouseDown'),

            ('nav',     'RightMouseDrag') : ('move', 'LeftMouseDrag'),
            ('line',    'RightMouseDrag') : ('move', 'LeftMouseDrag'),
            ('point',   'RightMouseDrag') : ('move', 'LeftMouseDrag'),
            ('rect',    'RightMouseDrag') : ('move', 'LeftMouseDrag'),
            ('text',    'RightMouseDrag') : ('move', 'LeftMouseDrag'),
            ('arrow',   'RightMouseDrag') : ('move', 'LeftMouseDrag'),
            ('ellipse', 'RightMouseDrag') : ('move', 'LeftMouseDrag'),

            ('nav',     'RightMouseUp') : ('move', 'LeftMouseUp'),
            ('line',    'RightMouseUp') : ('move', 'LeftMouseUp'),
            ('point',   'RightMouseUp') : ('move', 'LeftMouseUp'),
            ('rect',    'RightMouseUp') : ('move', 'LeftMouseUp'),
            ('text',    'RightMouseUp') : ('move', 'LeftMouseUp'),
            ('arrow',   'RightMouseUp') : ('move', 'LeftMouseUp'),
            ('ellipse', 'RightMouseUp') : ('move', 'LeftMouseUp')}


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
            ['line', 'arrow', 'point', 'rect', 'text', 'ellipse', 'move'])
        self.mode = 'nav'

        # Used to store a reference to an annotation
        # and previous mouse location during mouse
        # drags.
        self.__dragging = None
        self.__lastPos  = None


    def __initialSettings(self, canvas, canvasPos):
        """Returns a dictionary containing some initial settings with which all
        new annotations are created.
        """
        opts = canvas.opts
        zpos = canvasPos[opts.zax]
        return {
            'colour'        : self.colour,
            'lineWidth'     : self.lineWidth,
            'fontSize'      : self.fontSize,
            'filled'        : self.filled,
            'border'        : self.border,
            'alpha'         : self.alpha,
            'honourZLimits' : self.honourZLimits,
            'zmin'          : np.floor(zpos),
            'zmax'          : np.ceil( zpos),
            'hold'          : True,
            'fixed'         : False
        }


    def __displaySize(self, size, squared):
        """Display the given size (length or area) in the
        :class:`.FSLeyesFrame` status bar.

        :arg size:    Size to display
        :arg squared: If ``True``, ^2 is shown after the size value (use if
                      the size is an area).
        """
        displayCtx = self.displayCtx
        opts       = displayCtx.getOpts(displayCtx.getSelectedOverlay())
        refimage   = opts.referenceImage

        if refimage is not None:
            units  = refimage.xyzUnits
            units  = strings.nifti.get(('xyz_unit', units), '(unknown units)')

            if squared:
                units = f'{units}\u00B2'
            size = f'{size:.2f} {units}'
        else:
            size = f'{size:.2f}'

        status.update(size)


    def _moveModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """If the mouse lands on an annotation, save a reference to it
        so it can be moved on mouse drag.
        """
        opts  = canvas.opts
        annot = canvas.getAnnotations()
        pos   = canvasPos[opts.xax], canvasPos[opts.yax]

        for obj in annot.annotations:
            try:
                if obj.hit(*pos):
                    self.__dragging = obj
                    self.__lastPos  = pos
                    break
            except NotImplementedError:
                pass


    def _moveModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Move the annotation that was clicked on. """

        obj     = self.__dragging
        lastPos = self.__lastPos

        if obj is None:
            return

        opts   = canvas.opts
        pos    = (canvasPos[opts.xax], canvasPos[opts.yax])
        offset = (pos[0] - lastPos[0], pos[1] - lastPos[1])

        try:
            obj.move(*offset)
            self.__lastPos = pos
        except NotImplementedError:
            pass

        canvas.Refresh()


    def _moveModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clears the reference to the annotation that was being moved. """
        self.__dragging = None
        self.__lastPos  = None


    def _lineModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Adds a new line annotation."""
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        x, y            = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.line(x, y, x, y, **settings)


    def _lineModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the line end point so it tracks the mouse location."""
        opts    = canvas.opts
        line    = self.__dragging
        line.x2 = canvasPos[opts.xax]
        line.y2 = canvasPos[opts.yax]

        # display line length in the
        # FSLeyesFrame status bar
        xy1    = np.array([line.x1, line.y1])
        xy2    = np.array([line.x2, line.y2])
        length = np.sqrt(np.sum((xy1 - xy2) ** 2))
        self.__displaySize(length, False)
        canvas.Refresh()


    def _lineModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clear a reference to the newly created line. If the mouse hasn't
        moved since mouse down, the line is deleted.
        """
        line            = self.__dragging
        annot           = canvas.getAnnotations()
        self.__dragging = None

        if (line.x1 == line.x2 and line.y1 == line.y2):
            annot.dequeue(line, hold=True)

        canvas.Refresh()


    def _arrowModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Adds a new arrow annotation."""
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        x, y            = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.arrow(x, y, x, y, **settings)


    def _arrowModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the arrow end point so it tracks the mouse location."""
        opts     = canvas.opts
        arrow    = self.__dragging
        arrow.x2 = canvasPos[opts.xax]
        arrow.y2 = canvasPos[opts.yax]

        # display arrow length in the
        # FSLeyesFrame status bar
        xy1    = np.array([arrow.x1, arrow.y1])
        xy2    = np.array([arrow.x2, arrow.y2])
        length = np.sqrt(np.sum((xy1 - xy2) ** 2))
        self.__displaySize(length, False)
        canvas.Refresh()


    def _arrowModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clear a reference to the newly created arrow. If the mouse hasn't
        moved since mouse down, the arrow is deleted.
        """
        arrow            = self.__dragging
        annot           = canvas.getAnnotations()
        self.__dragging = None

        if (arrow.x1 == arrow.x2 and arrow.y1 == arrow.y2):
            annot.dequeue(arrow, hold=True)

        canvas.Refresh()


    def _pointModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Creates a new point annotation. """
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        x, y            = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.point(x, y, **settings)
        canvas.Refresh()


    def _pointModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Changes the location of the point annotation to track the mouse drag
        location.
        """
        opts              = canvas.opts
        self.__dragging.x = canvasPos[opts.xax]
        self.__dragging.y = canvasPos[opts.yax]
        canvas.Refresh()


    def _pointModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clear a reference to the newly created point annotation. """
        self.__dragging = None


    def _textModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Show a dialog prompting the user for some text, then creates a new
        text annotation.
        """
        opts     = canvas.opts
        annot    = canvas.getAnnotations()
        settings = self.__initialSettings(canvas, canvasPos)
        x, y     = (canvasPos[opts.xax], canvasPos[opts.yax])
        msg      = strings.messages[self, 'TextAnnotation']
        dlg      = fsldlg.TextEditDialog(self.viewPanel,
                                         message=msg,
                                         style=fsldlg.TED_OK_CANCEL)

        if dlg.ShowModal() == wx.ID_OK:
            annot.text(dlg.GetText(), x, y, coordinates='display', **settings)
            canvas.Refresh()


    def _rectModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Create a new rectangle annotation.
        """
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        x, y            = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.rect(x, y, 0, 0, **settings)


    def _rectModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the size of the rectangle with the mouse drag. """
        opts   = canvas.opts
        rect   = self.__dragging
        rect.w = canvasPos[opts.xax] - rect.x
        rect.h = canvasPos[opts.yax] - rect.y

        # display rect area in status bar
        self.__displaySize(np.abs(rect.w * rect.h), True)

        canvas.Refresh()


    def _rectModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clear the reference to the new rectangle annotation. If the
        rectangle has no area (the user clicked without dragging), the
        rectangle is deleted.
        """
        rect            = self.__dragging
        annot           = canvas.getAnnotations()
        self.__dragging = None

        if rect.w == 0 or rect.h == 0:
            annot.dequeue(rect, hold=True)

        canvas.Refresh()


    def _ellipseModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Create a new ellipse annotation. """
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        x, y            = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.ellipse(x, y, 0, 0, **settings)


    def _ellipseModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the ellipse radius with the mouse drag. """
        opts      = canvas.opts
        ellipse   = self.__dragging
        p1        = np.array((ellipse.x, ellipse.y))
        p2        = np.array((canvasPos[opts.xax], canvasPos[opts.yax]))
        ellipse.w = np.abs(p1[0] - p2[0])
        ellipse.h = np.abs(p1[1] - p2[1])

        # display ellipse area in status bar
        self.__displaySize(np.pi * ellipse.w * ellipse.h, True)
        canvas.Refresh()


    def _ellipseModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clear the reference to the new ellipse annotation. If the ellipse
        has no area (the user clicked without dragging), the ellipse is deleted.
        """
        ellipse         = self.__dragging
        annot           = canvas.getAnnotations()
        self.__dragging = None

        if (ellipse.w == 0) or (ellipse.h == 0):
            annot.dequeue(ellipse, hold=True)

        canvas.Refresh()
