#!/usr/bin/env python
#
# filetreepanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path   as op
import itertools as it
import              logging

import wx

import numpy as np

import fsl.utils.path                as fslpath
import fsl.utils.filetree            as filetree
import fsl.utils.settings            as fslsettings
import fsleyes_widgets.widgetlist    as wlist
import fsleyes_widgets.widgetgrid    as wgrid
import fsleyes_widgets.elistbox      as elb

import fsleyes.strings               as strings
import fsleyes.controls.controlpanel as ctrlpanel


log = logging.getLogger(__name__)

NONELBL = strings.labels['VariablePanel.value.none']
ANYLBL  = strings.labels['VariablePanel.value.any']
ALLLBL  = strings.labels['VariablePanel.value.all']


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

        self.__tree  = None
        self.__query = None

        self.__loadDir      = wx.Button(self)
        self.__customTree   = wx.Button(self)
        self.__treeChoice   = wx.Choice(self)
        self.__dirName      = wx.StaticText(self, style=wx.ST_ELLIPSIZE_MIDDLE)
        self.__mainSplitter = wx.SplitterWindow(
            self,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        self.__leftSplitter = wx.SplitterWindow(
            self.__mainSplitter,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        self.__varPanel     = VariablePanel(self.__leftSplitter, self)
        self.__fileTypes    = FileTypePanel(self.__leftSplitter, self)
        self.__fileList     = FileListPanel(self.__mainSplitter, self)

        self.__leftSplitter.SetMinimumPaneSize(50)
        self.__mainSplitter.SetMinimumPaneSize(50)
        self.__leftSplitter.SplitHorizontally(self.__fileTypes,
                                              self.__varPanel)
        self.__mainSplitter.SplitVertically(  self.__leftSplitter,
                                              self.__fileList)
        self.__mainSplitter.SetSashGravity(0.4)
        self.__leftSplitter.SetSashGravity(0.4)

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
        self.__mainSizer.Add(self.__topSizer,     flag=wx.EXPAND)
        self.__mainSizer.Add(self.__dirName,      flag=wx.EXPAND)
        self.__mainSizer.Add(self.__mainSplitter, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__mainSizer)

        self.__loadDir   .Bind(wx.EVT_BUTTON, self.__onLoadDir)
        self.__customTree.Bind(wx.EVT_BUTTON, self.__onCustomTree)
        self.__treeChoice.Bind(wx.EVT_CHOICE, self.__onTreeChoice)


    def UpdateMatches(self):
        """
        """

        if self.__tree is None or self.__query is None:
            return

        flist    = self.__fileList
        ftypes   = self.__fileTypes.GetFileTypes()
        allvars  = self.__query.variables()
        varyings = self.__varPanel.GetVaryings()

        fixed    = self.__varPanel.GetFixed()
        ftfixed  = {}
        for ftype in ftypes:
            ftvars = self.__query.variables(ftype)
            ftfixed[ftype] = {}
            for var in fixed:
                if var in ftvars:
                    ftfixed[ftype][var] = allvars[var]
        fixed    = ftfixed

        hits     = {ft : self.__query.query(ft, **varyings) for ft in ftypes}

        for var, val in list(varyings.items()):
            if val == '*': varyings[var] = allvars[var]
            else:          varyings.pop(var)

        flist.ResetGrid(ftypes, varyings, fixed)



    def __loadTree(self, treename, dirname):
        """
        """

        if treename is None or dirname is None:
            dirname    = None
            tree       = None
            query      = None
            allvars    = None
            shortnames = None
        else:
            tree       = filetree.FileTree.read(treename, directory=dirname)
            query      = filetree.FileTreeQuery(tree)
            allvars    = query.variables()
            shortnames = query.short_names

        self.__tree  = tree
        self.__query = query

        self.__dirName  .SetLabel(dirname or '')
        self.__varPanel .SetVariables(allvars)
        self.__fileTypes.SetFileTypes(shortnames)

        self.UpdateMatches()


    def __getTreeChoice(self):
        """
        """
        idx = self.__treeChoice.GetSelection()

        if idx == wx.NOT_FOUND:
            return None

        return self.__treeChoice.GetClientData(idx)


    def __onLoadDir(self, ev):
        """
        """

        msg     = strings.messages[self, 'loadDir']
        fromDir = fslsettings.read('loadSaveOverlayDir')

        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                           message=msg,
                           defaultPath=fromDir,
                           style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() != wx.ID_OK:
            return

        dirname  = dlg.GetPath()
        treename = self.__getTreeChoice()

        self.__loadTree(treename, dirname)


    def __onTreeChoice(self, ev):
        """
        """
        dirname  = self.__dirName.GetLabel() or None
        treename = self.__getTreeChoice()
        self.__loadTree(treename, dirname)


    def __onCustomTree(self, ev):
        """
        """
        pass


class FileTypePanel(elb.EditableListBox):


    def __init__(self, parent, ftpanel):
        """
        """
        elb.EditableListBox.__init__(
            self,
            parent,
            style=(elb.ELB_NO_ADD    |
                   elb.ELB_NO_REMOVE |
                   elb.ELB_NO_MOVE))

        self.__ftpanel = ftpanel


    def SetFileTypes(self, filetypes):
        """
        """
        self.Clear()

        if filetypes is None:
            return

        for ft in filetypes:
            toggle = wx.CheckBox(self)
            self.Append(ft, extraWidget=toggle)
            toggle.Bind(wx.EVT_CHECKBOX, self.__onToggle)


    def GetFileTypes(self):
        """
        """
        filetypes = self.GetLabels()
        toggles   = self.GetWidgets()
        active    = []

        for ft, tog in zip(filetypes, toggles):
            if tog:
                active.append(ft)

        return active


    def __onToggle(self, ev):
        """
        """
        self.__ftpanel.UpdateMatches()


class VariablePanel(wx.Panel):


    def __init__(self, parent, ftpanel):

        wx.Panel.__init__(self, parent)

        self.__ftpanel  = ftpanel
        self.__varList  = wlist.WidgetList(self)
        self.__vars     = None

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__varList, flag=wx.EXPAND, proportion=1)


    def SetVariables(self, vars):

        self.__vars = {}

        self.__varList.Clear()

        if vars is None or len(vars) == 0:
            self.__ftpanel.UpdateMatches()
            return


        for var, vals in vars.items():

            if None in vals:
                vals.remove(None)
                vals = [ANYLBL, ALLLBL, NONELBL] + sorted(vals)
            else:
                vals = [ANYLBL, ALLLBL] + sorted(vals)
            choice = wx.Choice(self.__varList, choices=vals, name=var)

            choice.SetSelection(0)
            choice.Bind(wx.EVT_CHOICE, self.__onVariable)

            self.__varList.AddWidget(choice, var)
            self.__vars[var] = vals


    def GetVaryings(self):

        queryvars = {}

        for choice in self.__varList.GetWidgets():
            var    = choice.GetName()
            validx = choice.GetSelection()
            val    = self.__vars[var][validx]

            if   val == ALLLBL:  continue
            elif val == ANYLBL:  queryvars[var] = '*'
            elif val == NONELBL: queryvars[var] = None
            else:                queryvars[var] = val

        return queryvars


    def GetFixed(self):

        flatvars = []

        for choice in self.__varList.GetWidgets():
            var    = choice.GetName()
            validx = choice.GetSelection()
            val    = self.__vars[var][validx]

            if val == ALLLBL:
                flatvars.append(var)

        return flatvars


    def __onVariable(self, ev):
        """
        """
        self.__ftpanel.UpdateMatches()


class FileListPanel(wx.Panel):

    def __init__(self, parent, ftpanel):
        wx.Panel.__init__(self, parent)
        self.__ftpanel = ftpanel

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.__grid = wgrid.WidgetGrid(
            self,
            style=(wgrid.WG_KEY_NAVIGATION  |
                   wgrid.WG_SELECTABLE_ROWS |
                   wgrid.WG_DRAGGABLE_COLUMNS))

        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)
        self.SetSizer(self.__sizer)


    def ResetGrid(self, ftypes, varyings, fixed):
        """
        """

        print('ftypes', ftypes)
        print('Varyings')
        print(varyings)
        print('fixed')
        print(fixed)

        nrows = np.prod([len(vals) for vals in varyings.values()])
        ncols = len(varyings)

        collabels = [var for var in varyings.keys()]

        #
        for ft in ftypes:
            ftvars = fixed[ft]
            ftcols = list(it.product(*[vals for vals in ftvars.values()]))
            ncols += len(ftcols)

            for ftvals in ftcols:
                collabels += [ft + '[' + ','.join(
                    ['{}={}'.format(var, val)
                     for var, val in zip(ftvars, ftvals)]) + ']']

        print('Num rows', nrows)
        print('Num cols', ncols)
        print('col labels')
        print('\n'.join(collabels))

        self.__grid.ClearGrid()
        self.__grid.SetGridSize(nrows, ncols)
        self.__grid.SetColLabels(collabels)
        self.__grid.ShowColLabels()
        self.__grid.Refresh()
