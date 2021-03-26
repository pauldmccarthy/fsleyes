#!/usr/bin/env python
#
# annotationpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsleyes_widgets.elistbox      as elb
import fsleyes.controls.controlpanel as ctrlpanel


class AnnotationPanel(ctrlpanel.ControlPanel):

    def __init__(self, parent, overlayList, displayCtx, frame, ortho):
        """
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, frame)
        self.__ortho = ortho

        self.__buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__mainSizer   = wx.BoxSizer(wx.VERTICAL)

        self.__annotList   = elb.EditableListBox(
            self, style=(elb.ELB_NO_ADD |
                         elb.ELB_NO_MOVE))

        self.__text   = wx.Button(self, label='text')
        self.__rect   = wx.Button(self, label='rect')
        self.__line   = wx.Button(self, label='line')
        self.__point  = wx.Button(self, label='point')
        self.__circle = wx.Button(self, label='circle')

        self.__buttonSizer.Add(self.__text,   flag=wx.EXPAND, proportion=1)
        self.__buttonSizer.Add(self.__rect,   flag=wx.EXPAND, proportion=1)
        self.__buttonSizer.Add(self.__line,   flag=wx.EXPAND, proportion=1)
        self.__buttonSizer.Add(self.__point,  flag=wx.EXPAND, proportion=1)
        self.__buttonSizer.Add(self.__circle, flag=wx.EXPAND, proportion=1)

        self.__mainSizer.Add(self.__annotList,   flag=wx.EXPAND, proportion=1)
        self.__mainSizer.Add(self.__buttonSizer, flag=wx.EXPAND)

        self.SetSizer(self.__mainSizer)
