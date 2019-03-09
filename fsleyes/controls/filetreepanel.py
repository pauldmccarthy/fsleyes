#!/usr/bin/env python
#
# filetreepanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path   as op
import itertools as it
import functools as ft
import              logging
import              collections

import wx

import numpy as np

import fsl.utils.path                as fslpath
import fsl.utils.filetree            as filetree
import fsl.utils.settings            as fslsettings
import fsleyes_widgets.widgetlist    as wlist
import fsleyes_widgets.widgetgrid    as wgrid
import fsleyes_widgets.elistbox      as elb

import fsleyes.actions.loadoverlay   as loadoverlay
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

        self.__tree     = None
        self.__query    = None
        self.__overlays = None

        self.__loadDir      = wx.Button(self)
        self.__customTree   = wx.Button(self)
        self.__treeChoice   = wx.Choice(self)
        self.__dirName      = wx.StaticText(self, style=wx.ST_ELLIPSIZE_MIDDLE)
        self.__mainSplitter = wx.SplitterWindow(
            self,
            style=wx.SP_LIVE_UPDATE)
        self.__leftPanel    = wx.Panel(self.__mainSplitter)
        self.__leftSizer    = wx.BoxSizer(wx.VERTICAL)

        self.__varPanel     = VariablePanel(self.__leftPanel,    self)
        self.__fileTypes    = FileTypePanel(self.__leftPanel,    self)
        self.__fileList     = FileListPanel(self.__mainSplitter, self)

        self.__leftSizer.Add(self.__fileTypes, flag=wx.EXPAND, proportion=1)
        self.__leftSizer.Add(self.__varPanel,  flag=wx.EXPAND)
        self.__leftPanel.SetSizer(self.__leftSizer)

        self.__mainSplitter.SetMinimumPaneSize(50)
        self.__mainSplitter.SplitVertically(  self.__leftPanel,
                                              self.__fileList)
        self.__mainSplitter.SetSashGravity(0.3)

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
        query    = self.__query
        ftypes   = self.__fileTypes.GetFileTypes()
        allvars  = query.variables()
        varyings = self.__varPanel.GetVaryings()
        fixed    = self.__varPanel.GetFixed()
        ftfixed  = {}

        for ft in ftypes:
            print('axes for', ft)
            for v in query.variables(ft):
                print('  ', v)

        for ftype in ftypes:
            ftvars = self.__query.variables(ftype)
            ftfixed[ftype] = {}
            for var in fixed:
                if var in ftvars:
                    ftfixed[ftype][var] = allvars[var]

        fixed = ftfixed

        for var, val in list(varyings.items()):

            if not any([var in query.variables(ft) for ft in ftypes]):
                varyings.pop(var)
                continue

            elif val == '*':
                varyings[var] = allvars[var]
            else:
                varyings[var] = [val]

        flist.ResetGrid(ftypes, varyings, fixed)


    def GetFile(self, ftype, **vars):
        return self.__query.query(ftype, **vars)


    def ShowFiles(self, vars, ftypes, ftvars, files):

        overlayList = self.overlayList
        overlays    = self.__overlays

        keys = [(ftype, ) + tuple(sorted(v.items()))
                for ftype, v in zip(ftypes, ftvars)]

        if overlays is not None:
            idxs = {k : overlayList.index(v) for k, v in overlays.items()}
        else:
            idxs = {}

        def onLoad(ovlidxs, ovls):
            for key, ovl in zip(keys, ovls):
                idx = idxs.get(key, None)
                if idx is None: overlayList.append(ovl)
                else:           overlayList[idx] = ovl

                print('overlay', ovl, 'key', key)

            self.__overlays = {k : o for k, o in zip(keys, ovls)}

        loadoverlay.loadOverlays(files, onLoad=onLoad)


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
            allvars    = [(var, vals) for var, vals in allvars.items()]
            allvars    = collections.OrderedDict(list(sorted(allvars)))
            shortnames = list(sorted(query.short_names))

        self.__tree  = tree
        self.__query = query

        self.__dirName  .SetLabel(dirname or '')
        self.__varPanel .SetVariables(allvars)
        self.__fileTypes.SetFileTypes(shortnames)

        self.__leftPanel.Layout()

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
            if tog.GetValue():
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
            style=(wx   .HSCROLL            |
                   wx   .VSCROLL            |
                   wgrid.WG_KEY_NAVIGATION  |
                   wgrid.WG_SELECTABLE_ROWS |
                   wgrid.WG_DRAGGABLE_COLUMNS))

        self.__varcols  = []
        self.__ftcols   = []
        self.__rows     = []
        self.__rowfiles = []

        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)
        self.SetSizer(self.__sizer)

        self.__grid.Bind(wgrid.EVT_WG_SELECT,  self.__onSelect)
        self.__grid.Bind(wgrid.EVT_WG_REORDER, self.__onReorder)


    def __onSelect(self, ev):

        vars  = self.__rows[    ev.row]
        files = self.__rowfiles[ev.row]

        ftypes, ftvars, files = zip(*files)

        self.__ftpanel.ShowFiles(vars, ftypes, ftvars, files)


    def __onReorder(self, ev):
        """
        """
        varcols = self.__grid.GetColLabels()[:len(self.__varcols)]

        def cmp(r1, r2):
            r1 = self.__rows[r1]
            r2 = self.__rows[r2]
            for col in varcols:
                v1 = r1[col]
                v2 = r2[col]
                if   v1 == v2:   continue
                elif v1 is None: return  1
                elif v2 is None: return -1
                elif v1 > v2:    return  1
                elif v1 < v2:    return -1
            return 0

        grid     = self.__grid
        rowidxs  = list(range(len(self.__rows)))
        rowidxs  = sorted(rowidxs, key=ft.cmp_to_key(cmp))
        rows     = [self.__rows[    i] for i in rowidxs]
        rowfiles = [self.__rowfiles[i] for i in rowidxs]

        self.__varcols  = varcols
        self.__rows     = rows
        self.__rowfiles = rowfiles

        for ri in range(len(rows)):
            vals  = rows[    ri]
            files = rowfiles[ri]

            for ci in range(len(varcols)):
                val = vals[varcols[ci]]
                if val is None:
                    val = NONELBL
                grid.SetText(ri, ci, val)

            for ci, (ftype, ftvars, ftfile) in enumerate(files, len(varcols)):
                if ftfile is not None: grid.SetText(ri, ci, '\u2022')
                else:                  grid.SetText(ri, ci, '')


    def ResetGrid(self, ftypes, varyings, fixed):
        """
        """

        # Force a constsient ordering
        # of the varying variables
        _varyings = collections.OrderedDict()
        for var in sorted(varyings.keys()):
            _varyings[var] = varyings[var]
        varyings = _varyings

        # example template for one row
        # sub=X, ses=Y, T1
        #               T2
        #               surface[surf=mid]
        #               surface[surf=pial]
        #               surface[surf=white]

        # Build a list of all columns:
        #
        #  - one column for each varying variable
        #  - one column for each file type that doesn't have any fixed
        #    variables
        #  - one column for each file type and set of fixed variable values,
        #    for file types which do have fixed variables
        #
        # varcols: list of varying variable names that map to grid columns
        # ftcols:  list of (ftype, {var : val}) tuples for all file types/fixed
        #          variables, each of which maps to one column
        #
        grid      = self.__grid
        varcols   = [var for var, vals in varyings.items() if len(vals) > 1]
        ftcols    = []
        collabels = list(varcols)

        for ftype in ftypes:

            ftvars    = fixed[ftype]
            ftvarprod = list(it.product(*[vals for vals in ftvars.values()]))

            for ftvals in ftvarprod:

                ftvals = {var : val for var, val in zip(ftvars, ftvals)}

                ftcols.append((ftype, ftvals))

                if len(ftvals) == 0:
                    lbl = ftype
                else:
                    lbl = ftype + '[' + ','.join(
                        ['{}={}'.format(var, val)
                         for var, val in ftvals.items()]) + ']'
                collabels.append(lbl)

        # Build a list of all rows:
        #  - rows:     a {var : val} dict for each row, containing all
        #              varyings
        #
        #  - rowfiles: a [(ftype, {var : val}, file)] list for each row,
        #              containing all fixed variables for each file type
        #              The file will be None if there is no fike of this
        #              type for these variable values
        rows     = []
        rowfiles = []

        # loop through all possible combinations of varying values
        valprod = list(it.product(*varyings.values()))
        for rowi, vals in enumerate(valprod):

            rowivals  = {var : val for var, val in zip(varyings.keys(), vals)}
            rowifiles = []
            nfiles    = 0

            for ftype, ftvars in ftcols:

                ftvars = dict(ftvars)

                # Should you only be storing
                # the fixed vars here?
                ftvars.update(rowivals)
                ftfile = self.__ftpanel.GetFile(ftype, **ftvars).reshape((-1,))

                try:
                    ftfile  = ftfile[0].filename
                    nfiles += 1
                except Exception:
                    ftfile = None

                rowifiles.append((ftype, ftvars, ftfile))

            # Drop rows which have no files
            if nfiles > 0:
                rows    .append(rowivals)
                rowfiles.append(rowifiles)

        nrows = len(rows)
        ncols = len(varcols) + len(ftcols)

        self.__varcols  = varcols
        self.__ftcols   = ftcols
        self.__rows     = rows
        self.__rowfiles = rowfiles

        grid.ClearGrid()
        grid.SetGridSize(nrows, ncols)
        grid.SetDragLimit(len(varcols) - 1)
        grid.SetColLabels(collabels)
        grid.ShowColLabels()

        for rowi, (vals, files) in enumerate(zip(rows, rowfiles)):

            for coli, col in enumerate(varcols):
                val = vals[col]
                if val is None:
                    val = NONELBL
                grid.SetText(rowi, coli, val)

            for coli, (ftype, ftvars, ftfile) in enumerate(files,
                                                           len(varcols)):
                if ftfile is not None: grid.SetText(rowi, coli, '\u2022')
                else:                  grid.SetText(rowi, coli, '')

        grid.Refresh()
