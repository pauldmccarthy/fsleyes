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

import fsl.data.image                    as fslimage
import fsleyes_props                     as props
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


    honourZLimits = copy.copy(annotations.AnnotationObject.honourZLimits)
    """Whether annotations are drawn when outside their Z limits."""


    alpha = copy.copy(annotations.AnnotationObject.alpha)
    """Opacity."""


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
            'alpha'         : self.alpha,
            'honourZLimits' : self.honourZLimits,
            'zmin'          : np.floor(zpos),
            'zmax'          : np.ceil( zpos),
            'hold'          : True
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
        refimage   = opts.getReferenceImage()

        if refimage is not None:
            units  = refimage.xyzUnits
            units  = strings.nifti.get(('xyz_unit', units), '(unknown units)')

            if squared:
                units = f'{units}\u00B2'
            size = f'{size:.2f} {units}'
        else:
            size = f'{size:.2f}'

        status.update(size)


    def _moveModeRightMouseDown(self, ev, canvas, mousePos, canvasPos):
        """If the mouse lands on an annotation, save a reference to it
        so it can be moved on mouse drag.
        """
        opts  = canvas.opts
        annot = canvas.getAnnotations()
        pos   = canvasPos[opts.xax], canvasPos[opts.yax]

        for obj in annot.annotations:
            try:
                if obj.hit(pos):
                    self.__dragging = obj
                    self.__lastPos  = pos
                    break
            except NotImplementedError:
                pass


    def _moveModeRightMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Move the annotation that was clicked on. """

        obj     = self.__dragging
        lastPos = self.__lastPos

        if obj is None:
            return

        opts   = canvas.opts
        pos    = (canvasPos[opts.xax], canvasPos[opts.yax])
        offset = (pos[0] - lastPos[0], pos[1] - lastPos[1])

        try:
            obj.move(offset)
            self.__lastPos = pos
        except NotImplementedError:
            pass

        canvas.Refresh()


    def _moveModeRightMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clears the reference to the annotation that was being moved. """
        self.__dragging = None
        self.__lastPos  = None


    def _lineModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Adds a new line annotation."""
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        pos             = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.line(pos, pos, **settings)


    def _lineModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the line end point so it tracks the mouse location."""
        opts     = canvas.opts
        line     = self.__dragging
        line.xy2 = (canvasPos[opts.xax], canvasPos[opts.yax])

        # display line length in the
        # FSLeyesFrame status bar
        xy1    = np.array(line.xy1)
        xy2    = np.array(line.xy2)
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

        if line.xy1 == line.xy2:
            annot.dequeue(line, hold=True)

        canvas.Refresh()


    def _arrowModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Adds a new arrow annotation."""
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        pos             = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.arrow(pos, pos, **settings)


    def _arrowModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the arrow end point so it tracks the mouse location."""
        opts      = canvas.opts
        arrow     = self.__dragging
        arrow.xy2 = (canvasPos[opts.xax], canvasPos[opts.yax])

        # display arrow length in the
        # FSLeyesFrame status bar
        xy1    = np.array(arrow.xy1)
        xy2    = np.array(arrow.xy2)
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

        if arrow.xy1 == arrow.xy2:
            annot.dequeue(arrow, hold=True)

        canvas.Refresh()


    def _pointModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Creates a new point annotation. """
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        pos             = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.point(pos, **settings)
        canvas.Refresh()


    def _pointModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Changes the location of the point annotation to track the mouse drag
        location.
        """
        opts               = canvas.opts
        self.__dragging.xy = (canvasPos[opts.xax], canvasPos[opts.yax])
        canvas.Refresh()


    def _pointModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clear a reference to the newly created point annotation. """
        self.__dragging = None


    def _textModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Show a dialog prompting the user for some text, then creates a new
        text annotation.
        """
        annot    = canvas.getAnnotations()
        settings = self.__initialSettings(canvas, canvasPos)
        dlg      = fsldlg.TextEditDialog(self.viewPanel,
                                         style=fsldlg.TED_OK_CANCEL)

        if dlg.ShowModal() == wx.ID_OK:
            annot.text(dlg.GetText(),
                       canvasPos,
                       coordinates='display',
                       **settings)
            canvas.Refresh()


    def _rectModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Create a new rectangle annotation.
        """
        opts            = canvas.opts
        annot           = canvas.getAnnotations()
        pos             = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.rect(pos, 0, 0, **settings)


    def _rectModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the size of the rectangle with the mouse drag. """
        opts   = canvas.opts
        rect   = self.__dragging
        rect.w = canvasPos[opts.xax] - rect.xy[0]
        rect.h = canvasPos[opts.yax] - rect.xy[1]

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
        pos             = (canvasPos[opts.xax], canvasPos[opts.yax])
        settings        = self.__initialSettings(canvas, canvasPos)
        self.__dragging = annot.ellipse(pos, 0, 0, **settings)


    def _ellipseModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the ellipse radius with the mouse drag. """
        opts           = canvas.opts
        ellipse        = self.__dragging
        p1             = np.array(ellipse.xy)
        p2             = np.array((canvasPos[opts.xax], canvasPos[opts.yax]))
        ellipse.width  = np.abs(p1[0] - p2[0])
        ellipse.height = np.abs(p1[1] - p2[1])

        # display ellipse area in status bar
        self.__displaySize(np.pi * ellipse.width * ellipse.height, True)
        canvas.Refresh()


    def _ellipseModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Clear the reference to the new ellipse annotation. If the ellipse
        has no area (the user clicked without dragging), the ellipse is deleted.
        """
        ellipse         = self.__dragging
        annot           = canvas.getAnnotations()
        self.__dragging = None

        if (ellipse.width == 0) or (ellipse.height == 0):
            annot.dequeue(ellipse, hold=True)

        canvas.Refresh()
