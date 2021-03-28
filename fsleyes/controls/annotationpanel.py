#!/usr/bin/env python
#
# annotationpanel.py - The AnnotationPanel
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains the :class:`AnnotationPanel` class, a FSLeyes control
panel which allows the user to annotate the canvases of an
:class:`.OrthoPanel`.
"""


import wx

import fsleyes_widgets.elistbox      as elb
import fsleyes_widgets.bitmapradio   as bmpradio
import fsleyes.icons                 as fslicons
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.gl.annotations        as annotations


class AnnotationPanel(ctrlpanel.ControlPanel):
    """The ``AnnotationPanel`` contains controls allowing the user to add
    annotations to the canvases in an :class:`.OrthoPanel`. The user is able
    to add points, lines, rectangles, circles, and text to any canvas, and
    can adjust the properties (e.g. colour, thickness) of each annotation.

    When a user selects an annotation to add, the
    :class:`.OrthoAnnotateProfile` is enabled on the ``OrthoPanel``, which
    provides user interaction.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, ortho):
        """Create an ``AnnotationPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, frame)
        self.__ortho = ortho

        self.__buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__mainSizer   = wx.BoxSizer(wx.VERTICAL)

        self.__annotList   = elb.EditableListBox(
            self, style=(elb.ELB_NO_ADD |
                         elb.ELB_NO_MOVE))

        self.__annotOptions = bmpradio.BitmapRadioBox(
            self, style=bmpradio.BMPRADIO_ALLOW_DESELECTED)

        icons = {
            'text'   : [fslicons.loadBitmap('textAnnotationHighlight24'),
                        fslicons.loadBitmap('textAnnotation24')],
            'rect'   : [fslicons.loadBitmap('rectAnnotationHighlight24'),
                        fslicons.loadBitmap('rectAnnotation24')],
            'line'   : [fslicons.loadBitmap('lineAnnotationHighlight24'),
                        fslicons.loadBitmap('lineAnnotation24')],
            'arrow'  : [fslicons.loadBitmap('arrowAnnotationHighlight24'),
                        fslicons.loadBitmap('arrowAnnotation24')],
            'point'  : [fslicons.loadBitmap('pointAnnotationHighlight24'),
                        fslicons.loadBitmap('pointAnnotation24')],
            'circle' : [fslicons.loadBitmap('circleAnnotationHighlight24'),
                        fslicons.loadBitmap('circleAnnotation24')],
        }

        for option, icons in icons.items():
            self.__annotOptions.AddChoice(*icons, clientData=option)

        self.__mainSizer.Add(self.__annotList,    flag=wx.EXPAND, proportion=1)
        self.__mainSizer.Add(self.__annotOptions, flag=wx.EXPAND)

        self.SetSizer(self.__mainSizer)

        self.__annotOptions.Bind(bmpradio.EVT_BITMAP_RADIO_EVENT,
                                 self.__onAnnotOption)


    def __onAnnotOption(self, ev):
        if ev.value:
            self.__ortho.profile = 'annotate'
            self.__ortho.getCurrentProfile().mode = ev.clientData
        else:
            self.__ortho.profile = 'view'
