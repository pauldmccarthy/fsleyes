#!/usr/bin/env python
#
# filetreepanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""

See also the :mod:`.filetreemanager` module, which contains the logic for
generating the file list.
"""


import os.path as op
import            logging
import            collections

import            wx

import fsl.utils.filetree               as filetree
import fsl.utils.settings               as fslsettings
import fsleyes_widgets.widgetlist       as wlist
import fsleyes_widgets.widgetgrid       as wgrid
import fsleyes_widgets.elistbox         as elb

import fsleyes.strings                  as strings
import fsleyes.controls.controlpanel    as ctrlpanel
import fsleyes.controls.filetreemanager as ftmanager


log = logging.getLogger(__name__)

NONELBL = strings.labels['VariablePanel.value.none']
ANYLBL  = strings.labels['VariablePanel.value.any']
ALLLBL  = strings.labels['VariablePanel.value.all']


class FileTreePanel(ctrlpanel.ControlPanel):
    """

    The user needs to select a data directory, and a file tree. The file
    tree can be selected either from the drop down list of built-in trees, or a
    custom tree file can be selected.

    Once the user has selected a file tree and a data directory, the
    :class:`FileTypePanel` and :class:`VariablePanel` will be populated,
    allowing the user to choose which file types to display, and how to
    arrange them.


    """

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
        self.__mgr   = None

        self.__loadDir      = wx.Button(self)
        self.__customTree   = wx.Button(self)
        self.__treeChoice   = wx.Choice(self)
        self.__dirName      = wx.StaticText(self, style=wx.ST_ELLIPSIZE_MIDDLE)
        self.__mainSplitter = wx.SplitterWindow(
            self, style=wx.SP_LIVE_UPDATE)
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


    def Update(self):
        """Called by the sub-panels when the user changes any settings.
        Re-generates the file grid.
        """

        if self.__tree is None or self.__query is None:
            return

        mgr      = self.__mgr
        flist    = self.__fileList
        ftypes   = self.__fileTypes.GetFileTypes()
        varyings = self.__varPanel.GetVaryings()
        fixed    = self.__varPanel.GetFixed()

        mgr.update(ftypes, varyings, fixed)
        flist.ResetGrid(mgr)


    def __loadTree(self, treename, dirname):
        """Called when a new tree or data directory is selected. Clears
        any previous file tree, and loads the new one. If either the tree
        or directory are ``None``, any existing file tree is cleared.

        :arg treename: File tree name or file
        :arg dirname:  Data directory
        """

        if treename is None or dirname is None:
            dirname    = None
            tree       = None
            query      = None
            mgr        = None
            allvars    = None
            shortnames = None
        else:
            tree       = filetree.FileTree.read(treename, directory=dirname)
            query      = filetree.FileTreeQuery(tree)
            mgr        = ftmanager.FileTreeManager(self.overlayList,
                                                   self.displayCtx,
                                                   query)
            allvars    = query.variables()
            allvars    = [(var, vals) for var, vals in allvars.items()]
            allvars    = collections.OrderedDict(list(sorted(allvars)))
            shortnames = list(sorted(query.short_names))

        self.__tree  = tree
        self.__query = query
        self.__mgr   = mgr

        self.__dirName  .SetLabel(dirname or '')
        self.__varPanel .SetVariables(allvars)
        self.__fileTypes.SetFileTypes(shortnames)
        self.__leftPanel.Layout()

        self.Update()


    def __getTreeChoice(self):
        """Returns the current selection of the built-in filetree drop down
        box.
        """
        idx = self.__treeChoice.GetSelection()

        if idx == wx.NOT_FOUND:
            return None

        return self.__treeChoice.GetClientData(idx)


    def __onLoadDir(self, ev):
        """Called when the user pushes the *load data directory* button.

        Prompts the user to select a directory, then calls the
        :meth:`__loadTree` method.
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
        """Called when the user changes the built-in file tree selection.
        Calls the :meth:`__loadTree` method.
        """
        dirname  = self.__dirName.GetLabel() or None
        treename = self.__getTreeChoice()
        self.__loadTree(treename, dirname)


    def __onCustomTree(self, ev):
        """Called when the user pushes the *load custom tree* button.
        """
        raise NotImplementedError()


class FileTypePanel(elb.EditableListBox):
    """The ``FileTypePanel`` displays a list of available file types.
    It allows the user to choose which file types should be displayed.

    Whenever the user changes the selected file types, the
    :meth:`FileTreePanel.Update` method is called.
    """

    def __init__(self, parent, ftpanel):
        """Create a ``FileTypePanel``.

        :arg parent:  ``wx`` parent object
        :arg ftpanel: The :class:`.FileTreePanel`
        """
        elb.EditableListBox.__init__(
            self, parent, style=(elb.ELB_NO_ADD    |
                                 elb.ELB_NO_REMOVE |
                                 elb.ELB_NO_MOVE))

        self.__ftpanel = ftpanel


    def SetFileTypes(self, filetypes):
        """Display the given list of file types.

        A check box is displayed alongside each file type allowing the
        user to toggle it on and off.

        :arg filetypes: List of file types Pass in ``None`` to clear the
                        list.
        """
        self.Clear()

        if filetypes is None:
            return

        for ftype in filetypes:
            toggle = wx.CheckBox(self)
            self.Append(ftype, extraWidget=toggle)
            toggle.Bind(wx.EVT_CHECKBOX, self.__onToggle)


    def GetFileTypes(self):
        """Returns a list of the file types that are currently selected. """

        filetypes = self.GetLabels()
        toggles   = self.GetWidgets()
        active    = []

        for ftype, tog in zip(filetypes, toggles):
            if tog.GetValue():
                active.append(ftype)

        return active


    def __onToggle(self, ev):
        """Called when a file type is toggled. Calls the
        :meth:`FileTreePanel.Update` method.
        """
        self.__ftpanel.Update()


class VariablePanel(wx.Panel):
    """The ``VariablePanel`` displays a list of available variables, allowing
    the user to choose between:

      - Displaying each variable value on a different row (``<any>``, the
        default). These variables are referred to as *varying*.

      - Displaying all variable value on the same row (``<all>``). These
        variables are referred to as *fixed*.

      - Displaying one specific variable value. These are also included as
        *varying* variables.
    """


    def __init__(self, parent, ftpanel):
        """Create a ``VariablePanel``

        :arg parent:  ``wx`` parent object
        :arg ftpanel: The :class:`.FileTreePanel`
        """

        wx.Panel.__init__(self, parent)

        self.__ftpanel  = ftpanel
        self.__varList  = wlist.WidgetList(self)
        self.__vars     = None

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__varList, flag=wx.EXPAND, proportion=1)


    def SetVariables(self, vars):
        """Set the variables to be displayed.

        :arg vars: Dict of ``{ var : [value] }`` mappings, containing
                   all variables, and all of their possible values.
        """

        self.__vars = None
        self.__varList.Clear()

        if vars is None or len(vars) == 0:
            return

        self.__vars = {}

        for var, vals in vars.items():

            if None in vals:
                vals.remove(None)
                vals = [ANYLBL, ALLLBL, NONELBL] + sorted(vals)
            else:
                vals = [ANYLBL, ALLLBL]          + sorted(vals)

            choice = wx.Choice(self.__varList, choices=vals, name=var)

            choice.SetSelection(0)
            choice.Bind(wx.EVT_CHOICE, self.__onVariable)

            self.__varList.AddWidget(choice, var)
            self.__vars[var] = vals


    def GetVaryings(self):
        """Return a dict of ``{ var : val }`` mappings containing all *varying*
        variables. The value for each variable may be one of:

         - ``'*'``, indicating that all possible values for this variable
           should be considered

         - ``None``, indicating that only instances  where this variable is
           absent should be considered.

         - A specific value, indicating that only this value should be
           considered.
        """

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
        """Returns a list containing the names of all *fixed* variables. """

        fixedvars = []

        for choice in self.__varList.GetWidgets():
            var    = choice.GetName()
            validx = choice.GetSelection()
            val    = self.__vars[var][validx]

            if val == ALLLBL:
                fixedvars.append(var)

        return fixedvars


    def __onVariable(self, ev):
        """Called when the user changes a variable setting. Calls the
        :meth:`FileTreePanel.Update` method.
        """
        self.__ftpanel.Update()


class FileListPanel(wx.Panel):
    """The ``FileListPanel`` displays a grid of filetree variable values
    and file types, allowing the user to step through the files in the data
    directory.

    The user can drag varying variable columns to re-order them - this will
    trigger a call to .FileTreeManager.reor
    """


    def __init__(self, parent, ftpanel):
        """Create a ``FileListPanel``.

        :arg parent:  ``wx`` parent object
        :arg ftpanel: The :class:`.FileTreePanel`
        """

        wx.Panel.__init__(self, parent)

        self.__ftpanel = ftpanel
        self.__mgr     = None
        self.__sizer   = wx.BoxSizer(wx.VERTICAL)
        self.__grid    = wgrid.WidgetGrid(
            self,
            style=(wx   .HSCROLL            |
                   wx   .VSCROLL            |
                   wgrid.WG_KEY_NAVIGATION  |
                   wgrid.WG_SELECTABLE_ROWS |
                   wgrid.WG_DRAGGABLE_COLUMNS))

        self.__sizer.Add(self.__grid, flag=wx.EXPAND, proportion=1)
        self.SetSizer(self.__sizer)

        self.__grid.Bind(wgrid.EVT_WG_SELECT,  self.__onSelect)
        self.__grid.Bind(wgrid.EVT_WG_REORDER, self.__onReorder)


    def ResetGrid(self, mgr):
        """Clear and re-populate the file tree grid.

        :arg mgr: The :class:`.FileTreeManager` from which the variable
                  and file information is retrieved.
        """

        self.__mgr = mgr
        varcols    = mgr.varcols
        fixedcols  = mgr.fixedcols
        fgroups    = mgr.filegroups
        grid       = self.__grid
        collabels  = self.__genColumnLabels(varcols, fixedcols)
        nrows      = len(fgroups)
        ncols      = len(collabels)

        grid.ClearGrid()
        grid.SetGridSize(nrows, ncols)
        grid.SetDragLimit(len(varcols) - 1)
        grid.SetColLabels(collabels)
        grid.ShowColLabels()
        self.__populateGrid()


    def __populateGrid(self):
        """Populates the contents of the file tree grid. The contents
        are retrieved from the :class:`.FileTreeManager`.
        """

        mgr     = self.__mgr
        grid    = self.__grid
        fgroups = mgr.filegroups
        varcols = mgr.varcols

        for rowi, fgroup in enumerate(fgroups):

            # Varying variable columns display
            # the current variable value
            for coli, col in enumerate(varcols):
                val = fgroup.varyings[col]
                if val is None:
                    val = NONELBL
                grid.SetText(rowi, coli, val)

            # Fixed variable columns have a
            # bullet indicating whether or
            # not each file is present
            for coli, filename in enumerate(fgroup.files, len(varcols)):
                if filename is not None: grid.SetText(rowi, coli, '\u2022')
                else:                    grid.SetText(rowi, coli, '')

        grid.Refresh()


    def __onSelect(self, ev):
        """Called when the user selects a row. Calls the
        :meth:`.FileTreeManager.Show` method.
        """

        group = self.__mgr.filegroups[ev.row]
        self.__mgr.show(group)


    def __onReorder(self, ev):
        """Called when the user drags a column to change the column order.
        Calls the :meth:`.FileTreeManager.reorder` method, and updates
        the grid contents.
        """

        mgr      = self.__mgr
        grid     = self.__grid
        nvarcols = len(mgr.varcols)
        varcols  = grid.GetColLabels()[:nvarcols]

        mgr.reorder(varcols)
        self.__populateGrid()


    def __genColumnLabels(self, varcols, fixedcols):
        """Called by :meth:`ResetGrid`. Generates a label for each column in
        the grid.

        :arg varcols:   List of varying variable names

        :arg fixedcols: List of ``(name, { var : val })`` tuples, containing
                        the file type and variable values of all fixed variable
                        columns.

        :returns:       A list of labels for each column
        """

        # The first set of columns correspond
        # to the varying variables - they are
        # just labelled with the variable name.
        collabels = list(varcols)

        # The second set of columns each
        # correspond to a combination of all
        # selected file types, and all
        # selected fixed variables.
        for ftype, ftvals in fixedcols:

            # No fixed variables for this type -
            # just use the file type name
            if len(ftvals) == 0:
                lbl = ftype

            # Generate a label containing the
            # file type name, and the values
            # of all fixed variables
            else:
                lbl = ['{}={}'.format(var, val) for var, val in ftvals.items()]
                lbl = ftype + '[' + ','.join(lbl) + ']'

            collabels.append(lbl)

        return collabels
