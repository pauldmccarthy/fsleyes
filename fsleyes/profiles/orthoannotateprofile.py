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


    colour = props.Colour(default='#a00000')
    """Initial colour to give all annotations. """


    width = props.Int(minval=1, maxval=10, default=1, clamped=True)
    """Initial width to give line-based annotations. """


    fontSize = props.Int(minval=6, maxval=48, default=10, clamped=False)
    """Initial font size to give text annotations. """


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
            ['line', 'arrow', 'point', 'rect', 'text', 'ellipse'])
        self.mode = 'nav'

        # Used to store a reference to annotations during mouse drags.
        self.__dragging = None


    def __initialSettings(self, canvas, canvasPos):
        """Returns a dictionary containing some initial settings with which all
        new annotations are created.
        """
        opts = canvas.opts
        zpos = canvasPos[opts.zax]
        return {
            'colour'   : self.colour,
            'width'    : self.width,
            'fontSize' : self.fontSize,
            'zmin'     : np.floor(zpos),
            'zmax'     : np.ceil( zpos),
            'filled'   : True,
            'hold'     : True
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
