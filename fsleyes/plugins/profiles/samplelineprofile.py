#!/usr/bin/env python
#
# samplelineprofile.py - The SampleLineProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SampleLineProfile` class, an interaction
:class:`.Profile` for :class:`.OrthoPanel` views, which is used by the
:class:`.SampleLinePanel`.
"""


import wx

import fsleyes.profiles.orthoviewprofile as orthoviewprofile


class SampleLineProfile(orthoviewprofile.OrthoViewProfile):
    """The ``SampleLineProfile`` class is a :class:`.Profile` for the
    :class:`.OrthoPanel` class, which allows the user to draw a line on
    a canvas. The :class:`.SampleLinePanel` will then sample values along
    that line from the currently selected overlay, and display them on a
    plot.
    """


    @staticmethod
    def tempModes():
        """Returns the temporary mode map for the ``SampleLineProfile``,
        which controls the use of modifier keys to temporarily enter other
        interaction modes.
        """
        return {
            ('sample',  wx.WXK_SHIFT)                  : 'nav',
            ('sample',  wx.WXK_CONTROL)                : 'zoom',
            ('sample',  wx.WXK_ALT)                    : 'pan',
            ('sample', (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice'}


    @staticmethod
    def altHandlers():
        """Returns the alternate handlers map, which allows event handlers
        defined in one mode to be re-used whilst in another mode.
        """
        return {('sample', 'MiddleMouseDrag') : ('pan', 'LeftMouseDrag')}


    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create a ``SampleLineProfile``.

        :arg viewPanel:    An :class:`.OrthoPanel` instance.
        :arg overlayList:  The :class:`.OverlayList` instance.
        :arg displayCtx:   The :class:`.DisplayContext` instance.
        """

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            viewPanel,
            overlayList,
            displayCtx,
            ['sample'])
        self.mode = 'sample'

        self.__sampleLine  = None
        self.__sampleStart = None
        self.__sampleEnd   = None


    def destroy(self):
        """Called when this ``SampleLineProfile`` is no longer used.
        Clears the current line annotation, if there is one, then calls
        the base class ``destroy`` method.
        """
        if self.__sampleLine is not None:
            line = self.__sampleLine
            line.annot.dequeue(line, hold=True, fixed=False)
            self.__sampleLine = None
            line.annot.canvas.Refresh()

        super().destroy()

    @property
    def sampleLine(self):
        """Returns a reference to the :class:`.Line` annotation that has most
        recently been drawn, or ``None`` if no line has been drawn.
        """
        return self.__sampleLine


    @property
    def sampleStart(self):
        """Return the ``(x, y, z)`` display coordinates of the start of the
        most recently drawn line, or ``None`` if no line has been drawn.
        """
        return self.__sampleStart


    @property
    def sampleEnd(self):
        """Return the ``(x, y, z)`` display coordinates of the end of the
        most recently drawn line, or ``None`` if no line has been drawn.
        """
        return self.__sampleEnd


    def _sampleModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Adds a new line annotation."""

        if self.__sampleLine is not None:
            line = self.__sampleLine
            line.annot.dequeue(line, hold=True, fixed=False)
            line.annot.canvas.Refresh()
            self.__sampleLine  = None
            self.__sampleStart = None
            self.__sampleEnd   = None

        opts  = canvas.opts
        annot = canvas.getAnnotations()
        x, y  = (canvasPos[opts.xax], canvasPos[opts.yax])

        self.__sampleStart = canvasPos
        self.__sampleLine  = annot.line(x, y, x, y,
                                        lineWidth=3, colour='#ff5050',
                                        hold=True, fixed=False)


    def _sampleModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Adjust the line end point so it tracks the mouse location."""
        opts             = canvas.opts
        line             = self.__sampleLine
        line.x2          = canvasPos[opts.xax]
        line.y2          = canvasPos[opts.yax]
        self.__sampleEnd = canvasPos
        canvas.Refresh()
