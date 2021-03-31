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


import copy

import wx

import fsleyes_widgets.elistbox              as elb
import fsleyes_props                         as props
import fsleyes_widgets.widgetlist            as widgetlist
import fsleyes_widgets.bitmapradio           as bmpradio
import fsleyes.strings                       as strings
import fsleyes.icons                         as fslicons
import fsleyes.controls.controlpanel         as ctrlpanel
import fsleyes.profiles.orthoannotateprofile as annotprofile
import fsleyes.gl.annotations                as annotations


class AnnotationPanel(ctrlpanel.ControlPanel):
    """The ``AnnotationPanel`` contains controls allowing the user to add
    annotations to the canvases in an :class:`.OrthoPanel`. The user is able
    to add points, lines, rectangles, ellipses, and text to any canvas, and
    can adjust the properties (e.g. colour, thickness) of each annotation.

    When a user selects an annotation to add, the
    :class:`.OrthoAnnotateProfile` is enabled on the ``OrthoPanel``, which
    provides user interaction.
    """


    colour        = copy.copy(annotprofile.OrthoAnnotateProfile.colour)
    fontSize      = copy.copy(annotprofile.OrthoAnnotateProfile.fontSize)
    lineWidth     = copy.copy(annotprofile.OrthoAnnotateProfile.lineWidth)
    filled        = copy.copy(annotprofile.OrthoAnnotateProfile.filled)
    honourZLimits = copy.copy(annotprofile.OrthoAnnotateProfile.honourZLimits)
    alpha         = copy.copy(annotprofile.OrthoAnnotateProfile.alpha)


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

        self.__widgets       = widgetlist.WidgetList(self, minHeight=24)
        self.__colour        = props.makeWidget(self.__widgets, self, 'colour')
        self.__filled        = props.makeWidget(self.__widgets, self, 'filled')
        self.__honourZLimits = props.makeWidget(self.__widgets, self,
                                                'honourZLimits')
        self.__fontSize      = props.makeWidget(self.__widgets, self,
                                                'fontSize', slider=False)
        self.__lineWidth     = props.makeWidget(self.__widgets, self,
                                                'lineWidth', slider=False)
        self.__alpha         = props.makeWidget(self.__widgets, self,
                                                'alpha', spin=False)

        self.__widgets.AddWidget(self.__colour,
                                 strings.labels[self, 'colour'])
        self.__widgets.AddWidget(self.__alpha,
                                 strings.labels[self, 'alpha'])
        self.__widgets.AddWidget(self.__fontSize,
                                 strings.labels[self, 'fontSize'])
        self.__widgets.AddWidget(self.__lineWidth,
                                 strings.labels[self, 'lineWidth'])
        self.__widgets.AddWidget(self.__filled,
                                 strings.labels[self, 'filled'])
        self.__widgets.AddWidget(self.__honourZLimits,
                                 strings.labels[self, 'honourZLimits'])

        self.__annotOptions = bmpradio.BitmapRadioBox(
            self, style=bmpradio.BMPRADIO_ALLOW_DESELECTED)

        icons = {
            'text'    : [fslicons.loadBitmap('textAnnotationHighlight24'),
                         fslicons.loadBitmap('textAnnotation24')],
            'rect'    : [fslicons.loadBitmap('rectAnnotationHighlight24'),
                         fslicons.loadBitmap('rectAnnotation24')],
            'line'    : [fslicons.loadBitmap('lineAnnotationHighlight24'),
                         fslicons.loadBitmap('lineAnnotation24')],
            'arrow'   : [fslicons.loadBitmap('arrowAnnotationHighlight24'),
                         fslicons.loadBitmap('arrowAnnotation24')],
            'point'   : [fslicons.loadBitmap('pointAnnotationHighlight24'),
                         fslicons.loadBitmap('pointAnnotation24')],
            'ellipse' : [fslicons.loadBitmap('ellipseAnnotationHighlight24'),
                         fslicons.loadBitmap('ellipseAnnotation24')],
        }

        for option, icons in icons.items():
            self.__annotOptions.AddChoice(*icons, clientData=option)

        self.__mainSizer.Add(self.__annotList,    flag=wx.EXPAND, proportion=1)
        self.__mainSizer.Add(self.__widgets,      flag=wx.EXPAND)
        self.__mainSizer.Add(self.__annotOptions, flag=wx.EXPAND)

        self.SetSizer(self.__mainSizer)

        self.__annotOptions.Bind(bmpradio.EVT_BITMAP_RADIO_EVENT,
                                 self.__onAnnotOption)


    def __onAnnotOption(self, ev):
        if ev.value:
            self.__ortho.profile = 'annotate'

            profile      = self.__ortho.getCurrentProfile()
            profile.mode = ev.clientData

            profile.bindProps('colour',        self)
            profile.bindProps('fontSize',      self)
            profile.bindProps('lineWidth',     self)
            profile.bindProps('filled',        self)
            profile.bindProps('alpha',         self)
            profile.bindProps('honourZLimits', self)
        else:
            self.__ortho.profile = 'view'
