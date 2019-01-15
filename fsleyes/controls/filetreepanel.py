#!/usr/bin/env python
#
# filetreepanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            logging

import wx

import fsl.utils.filetree            as filetree

import fsleyes.strings               as strings
import fsleyes.controls.controlpanel as ctrlpanel


log = logging.getLogger(__name__)


class FileTreePanel(ctrlpanel.ControlPanel):

    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``FileTreePanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__loadDir    = wx.Button(self)
        self.__customTree = wx.Button(self)
        self.__treeChoice = wx.Choice(self)

        self.__splitter   = wx.SplitterWindow(self,
                                              style=wx.SP_LIVE_UPDATE)
        self.__fileList   = wx.ListBox(self.__splitter)
        self.__varPanel   = None

        self.__splitter.SetMinimumPaneSize(50)
        self.__splitter.SplitVertically(self.__fileList,
                                        wx.Panel(self.__splitter))
        self.__splitter.SetSashGravity(0.4)

        treefiles  = filetree.list_all_trees()
        treelabels = [op.basename(tf) for tf in treefiles]
        for f, l in zip(treefiles, treelabels):
            self.__treeChoice.Append(l, clientData=f)

        self.__loadDir   .SetLabel(strings.labels[self, 'loadDir'])
        self.__customTree.SetLabel(strings.labels[self, 'customTree'])

        self.__topSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__topSizer.Add(self.__loadDir,    flag=wx.EXPAND, proportion=1)
        self.__topSizer.Add(self.__treeChoice, flag=wx.EXPAND, proportion=1)
        self.__topSizer.Add(self.__customTree, flag=wx.EXPAND, proportion=1)

        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.__mainSizer.Add(self.__topSizer, flag=wx.EXPAND)
        self.__mainSizer.Add(self.__splitter, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__mainSizer)

        self.__loadDir   .Bind(wx.EVT_BUTTON, self.__onLoadDir)
        self.__customTree.Bind(wx.EVT_BUTTON, self.__onCustomTree)
        self.__treeChoice.Bind(wx.EVT_CHOICE, self.__onTreeChoice)


    def __onLoadDir(self, ev):
        """
        """
        pass


    def __onTreeChoice(self, ev):
        """
        """
        pass



    def __onCustomTree(self, ev):
        """
        """
        pass


class FileTreeVariablePanel(wx.Panel):

    def __init__(self, tree, query):
        pass
