#!/usr/bin/env python
#
# filetreepanel.py - The FileTreePanel
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FileTreePanel` class, which can be used
to browse the contents of structured directories which are described with
a `FileTree <https://git.fmrib.ox.ac.uk/ndcn0236/file-tree/>`_ specification.

See also the :mod:`.manager` module, which contains the logic for
generating the file list.
"""


import os.path   as op
import itertools as it
import              time
import              logging
import              collections

import              wx

import fsl.utils.idle                         as idle
import fsl.utils.settings                     as fslsettings
import fsleyes_widgets.utils.overlay          as fwoverlay
import fsleyes_widgets.widgetlist             as wlist
import fsleyes_widgets.widgetgrid             as wgrid
import fsleyes_widgets.elistbox               as elb

import fsleyes.strings                        as strings
import fsleyes.views.canvaspanel              as canvaspanel
import fsleyes.controls.controlpanel          as ctrlpanel
import fsleyes.plugins.controls.filetreepanel as filetree


log = logging.getLogger(__name__)

NONELBL    = strings.labels['VariablePanel.value.none']
ANYLBL     = strings.labels['VariablePanel.value.any']
ALLLBL     = strings.labels['VariablePanel.value.all']
PRESENTLBL = strings.labels['FileListPanel.present']


BUILTIN_TREE_FILTER = ['BedpostX', 'Diffusion', 'HCP_Surface', 'ProbtrackX',
                       'bet',      'dti',       'eddy',        'epi_reg',
                       'fast',     'topup',     'feat_reg',    'feat_stats']
"""Built-in ``.tree`` files with a name in this list are hidden from the
:class:`FileTreePanel` interface. These trees are not very useful for our
purposes of navigating multi-subject data directories.
"""


class FileTreePanel(ctrlpanel.ControlPanel):
    """The ``FileTreePanel`` can be used to browse the contents of structured
    directories which are described with a :mod:`.filetree`.

    The user needs to select a data directory, and a file tree. The file tree
    can be selected either from the drop down list of built-in trees, or a
    custom tree file can be selected.

    Once the user has selected a file tree and a data directory, the
    :class:`FileTypePanel` and :class:`VariablePanel` will be populated,
    allowing the user to choose which file types to display, and how to
    arrange them.

    When the user has selected some file types, the :class:`FileListPanel`
    will display a grid containing all of the matching files that exist in the
    directory. The user can select a row to view the relevant files.

    The :class:`.FileTreeManager` handles the logic of working with the
    :class:`.FileTree` and of displaying overlays.
    """


    customTrees = []
    """Whenever the user loads a custom tree file, its path is added to this
    list, so that the tree file dropdown box can be populated with previously
    loaded tree files.
    """


    @staticmethod
    def supportedViews():
        """The ``FileTreePanel`` is intended for use with
        :class:`.CanvasPanel` views (i.e. ortho, lightbox, 3D views).
        """
        return [canvaspanel.CanvasPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary of arguments to be passed to
        :meth:`.ViewPanel.togglePanel` when a ``FileTreePanel`` is opened.
        """
        return {'location' : wx.RIGHT}


    @staticmethod
    def ignoreControl():
        """If the ``file_tree`` library is not installed, returns ``True``,
        which causes the ``FileTreePanel`` to not be added as an option in
        the FSLeyes interface.
        """
        return filetree.file_tree is None


    def __init__(self, parent, overlayList, displayCtx, viewPanel):
        """Create a ``FileTreePanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg viewPanel:   The :class:`.ViewPanel` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, viewPanel)

        self.__tree  = None
        self.__query = None
        self.__mgr   = None

        self.__loadDir      = wx.Button(self)
        self.__customTree   = wx.Button(self)
        self.__treeChoice   = wx.Choice(self)
        self.__save         = wx.Button(self)
        self.__mainSplitter = wx.SplitterWindow(
            self, style=wx.SP_LIVE_UPDATE | wx.SP_BORDER)
        self.__leftPanel    = wx.Panel(self.__mainSplitter)
        self.__rightPanel   = wx.Panel(self.__mainSplitter)
        self.__notesLabel   = wx.StaticText(self.__leftPanel)
        self.__notesChoice  = wx.Choice(self.__leftPanel)
        self.__dirName      = wx.StaticText(
            self.__rightPanel, style=wx.ST_ELLIPSIZE_MIDDLE)

        self.__varPanel     = VariablePanel(self.__leftPanel,  self)
        self.__fileTypes    = FileTypePanel(self.__leftPanel,  self)
        self.__fileList     = FileListPanel(self.__rightPanel, self)

        self.__mainSplitter.SetMinimumPaneSize(50)
        self.__mainSplitter.SplitVertically(
            self.__leftPanel, self.__rightPanel)
        self.__mainSplitter.SetSashGravity(0.3)

        # Build a list of all built-in filetrees,
        # along with any custom ones that have been
        # previously loaded. We hide the BUILTIN
        # ones
        def filter(tf):
            name = op.splitext(op.basename(tf))[0]
            return name not in BUILTIN_TREE_FILTER

        treefiles   = [tf for tf in filetree.list_all_trees() if filter(tf)]
        treefiles   = list(sorted(treefiles))
        treefiles  += FileTreePanel.customTrees
        treefiles   = [op.abspath( tf) for tf in treefiles]
        treelabels  = [op.basename(tf) for tf in treefiles]

        for f, l in zip(treefiles, treelabels):
            self.__treeChoice.Append(l, clientData=f)

        notesChoices = list(strings.choices[self, 'notes'].items())
        for key, label in notesChoices:
            self.__notesChoice.Append(label, clientData=key)

        self.__treeChoice .SetSelection(0)
        self.__notesChoice.SetSelection(0)
        self.__fileList   .NotesColumn(notesChoices[0][0])

        self.__loadDir   .SetLabel(strings.labels[self, 'loadDir'])
        self.__customTree.SetLabel(strings.labels[self, 'customTree'])
        self.__save      .SetLabel(strings.labels[self, 'save'])
        self.__notesLabel.SetLabel(strings.labels[self, 'notes'])

        self.__mainSizer  = wx.BoxSizer(wx.VERTICAL)
        self.__topSizer   = wx.BoxSizer(wx.HORIZONTAL)
        self.__notesSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__leftSizer  = wx.BoxSizer(wx.VERTICAL)
        self.__rightSizer = wx.BoxSizer(wx.VERTICAL)

        self.__notesSizer.Add(self.__notesLabel,  flag=wx.EXPAND)
        self.__notesSizer.Add(self.__notesChoice, flag=wx.EXPAND, proportion=1)

        self.__leftSizer.Add(self.__fileTypes,  flag=wx.EXPAND, proportion=1)
        self.__leftSizer.Add(self.__varPanel,   flag=wx.EXPAND)
        self.__leftSizer.Add(self.__notesSizer, flag=wx.EXPAND)

        self.__rightSizer.Add(self.__dirName,  flag=wx.EXPAND)
        self.__rightSizer.Add(self.__fileList, flag=wx.EXPAND, proportion=1)

        self.__topSizer.Add(self.__treeChoice, flag=wx.EXPAND, proportion=1)
        self.__topSizer.Add(self.__loadDir,    flag=wx.EXPAND, proportion=1)
        self.__topSizer.Add(self.__customTree, flag=wx.EXPAND, proportion=1)
        self.__topSizer.Add(self.__save,       flag=wx.EXPAND, proportion=1)

        self.__mainSizer.Add(self.__topSizer,     flag=wx.EXPAND)
        self.__mainSizer.Add(self.__mainSplitter, flag=wx.EXPAND, proportion=1)

        self             .SetSizer(self.__mainSizer)
        self.__leftPanel .SetSizer(self.__leftSizer)
        self.__rightPanel.SetSizer(self.__rightSizer)

        self.__loadDir    .Bind(wx.EVT_BUTTON, self._onLoadDir)
        self.__customTree .Bind(wx.EVT_BUTTON, self._onCustomTree)
        self.__treeChoice .Bind(wx.EVT_CHOICE, self._onTreeChoice)
        self.__save       .Bind(wx.EVT_BUTTON, self._onSave)
        self.__notesChoice.Bind(wx.EVT_CHOICE, self._onNotesChoice)


    @property
    def varPanel(self):
        """Return a reference to the :class:`VariablePanel`."""
        return self.__varPanel


    @property
    def fileTypePanel(self):
        """Return a reference to the :class:`FileTypePanel`."""
        return self.__fileTypes


    @property
    def fileListPanel(self):
        """Return a reference to the :class:`FileListPanel`."""
        return self.__fileList


    @property
    def treeChoice(self):
        """Return a reference to the file tree ``wx.Choice`` widget."""
        return self.__treeChoice


    def UpdateFileList(self):
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


    def _loadTree(self, treename, dirname):
        """Called when a new tree or data directory is selected. Clears
        any previous file tree, and loads the new one. If either the tree
        or directory are ``None``, any existing file tree is cleared.

        :arg treename: File tree name or file
        :arg dirname:  Data directory
        """

        if treename is None or dirname is None:
            dirname   = None
            tree      = None
            query     = None
            mgr       = None
            allvars   = None
            filetypes = None
        else:
            tree      = filetree.read(treename, directory=dirname)
            query     = filetree.FileTreeQuery(tree)
            mgr       = filetree.FileTreeManager(self.overlayList,
                                                 self.displayCtx,
                                                 query)
            allvars   = query.variables()
            allvars   = [(var, vals) for var, vals in allvars.items()]
            allvars   = collections.OrderedDict(list(sorted(allvars)))
            filetypes = list(sorted(query.templates))

        self.__tree  = tree
        self.__query = query
        self.__mgr   = mgr

        self.__dirName  .SetLabel(dirname or '')
        self.__varPanel .SetVariables(allvars)
        self.__fileTypes.SetFileTypes(filetypes)
        self.__leftPanel.Layout()

        self.UpdateFileList()


    def _getTreeChoice(self):
        """Returns the current selection of the built-in filetree drop down
        box.
        """
        idx = self.__treeChoice.GetSelection()

        if idx == wx.NOT_FOUND:
            return None

        return self.__treeChoice.GetClientData(idx)


    def _onLoadDir(self, ev=None):
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
        treename = self._getTreeChoice()

        fslsettings.write('loadSaveOverlayDir', dirname)

        self._loadTree(treename, dirname)


    def _onTreeChoice(self, ev=None):
        """Called when the user changes the built-in file tree selection.
        Calls the :meth:`__loadTree` method.
        """
        dirname  = self.__dirName.GetLabel() or None
        treename = self._getTreeChoice()
        self._loadTree(treename, dirname)


    def _onCustomTree(self, ev=None):
        """Called when the user pushes the *load custom tree* button.
        Prompts the user to choose a file, then calls :meth:`__loadTree`.
        """
        msg = strings.messages[self, 'loadCustomTree']
        dlg = wx.FileDialog(wx.GetApp().GetTopWindow(),
                            message=msg,
                            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        # TODO make sure tree label is unique
        choice    = self.__treeChoice
        ntrees    = choice.GetCount()
        treefile  = op.abspath(dlg.GetPath())
        treelabel = op.basename(treefile)
        existing  = [choice.GetClientData(i) for i in range(ntrees)]

        try:               index = existing.index(treefile)
        except ValueError: index = -1

        if index == -1:
            index = ntrees
            choice.Append(treelabel, clientData=treefile)

        choice.SetSelection(index)
        self._onTreeChoice()


    def _onSave(self, ev=None):
        """Called when the *save* button is pushed. Prompts the user
        for a destination, and then saves the contents of the grid.
        """

        msg = strings.messages[self, 'save']
        dlg = wx.FileDialog(
            self,
            defaultFile='notes.txt',
            message=msg,
            style=wx.FD_SAVE)

        if dlg.ShowModal() != wx.ID_OK:
            return

        path = dlg.GetPath()
        grid = self.__fileList.GridContents()

        with open(path, 'wt') as f:
            for row in grid:
                f.write('\t'.join(row) + '\n')


    def _onNotesChoice(self, ev):
        """Called when the user changes the notes column position choice.
        Calls :meth:`FileListPanel.NotesColumn` accordingly.
        """
        sel = self.__notesChoice.GetSelection()
        sel = self.__notesChoice.GetClientData(sel)
        self.__fileList.NotesColumn(sel)


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
            self, parent, vgap=5, style=(elb.ELB_NO_ADD    |
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
            toggle.SetMinSize(toggle.GetBestSize())
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
        self.__ftpanel.UpdateFileList()


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
        self.__ftpanel.UpdateFileList()


class FileListPanel(wx.Panel):
    """The ``FileListPanel`` displays a grid of filetree variable values
    and file types, allowing the user to step through the files in the data
    directory.


    The user can drag varying variable columns to re-order them - this will
    trigger a call to :meth:`.FileTreeManager.reorder`.


    A *Notes* column contains text controls in each row, allowing the user to
    add notes. The position of this column can be set to either left or right
    of the fixed variable columns via the :meth:`NotesColumn` method.
    """


    def __init__(self, parent, ftpanel, notes='right'):
        """Create a ``FileListPanel``.

        :arg parent:  ``wx`` parent object
        :arg ftpanel: The :class:`.FileTreePanel`
        :arg notes:   Location of the *Notes* column - one of:

                        - ``'right'`` - right-most column (default)
                        - ``'left'``  - left-most column, after varying
                          columns

        The *Notes* column location can be changed later via the
        :meth:`NotesColumn` method.
        """

        if notes not in ('left', 'right'):
            raise ValueError('Invalid value for notes: {}'.format(notes))

        wx.Panel.__init__(self, parent)

        self.__ftpanel = ftpanel
        self.__notes   = notes
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

        if len(fgroups) == 0:
            return

        grid.SetGridSize(nrows, ncols)
        grid.SetDragLimit(len(varcols) - 1)
        grid.SetColLabels(collabels)
        grid.ShowColLabels()
        self.__populateGrid()
        self.__createNotes()
        grid.Refresh()


    def NotesColumn(self, notes):
        """Set the position of the *Notes* column, either ``'left'`` or
        ``'right'`` of the fixed variable columns.
        """

        if notes not in ('left', 'right'):
            raise ValueError('Invalid value for notes: {}'.format(notes))

        nrows, ncols = self.__grid.GetGridSize()
        oldnotes     = self.__notes
        self.__notes = notes

        if nrows    == 0:     return
        if oldnotes == notes: return

        nvarcols = len(self.__mgr.varcols)
        order    = list(range(ncols))

        if notes == 'left': order.insert(nvarcols, order.pop(-1))
        else:               order.append(order.pop(nvarcols))

        self.__grid.ReorderColumns(order)
        self.__grid.Refresh()


    def GridContents(self):
        """Returns the contents of the grid as a list of lists of strings. """

        grid         = self.__grid
        nrows, ncols = grid.GetGridSize()
        rows         = [[None] * ncols for i in range(nrows)]

        for row, col in it.product(range(nrows), range(ncols)):

            widget = grid.GetWidget(row, col)

            # widget is either a StaticText
            # or a TextCtrl (notes column)
            if isinstance(widget, wx.TextCtrl): value = widget.GetValue()
            else:                               value = widget.GetLabel()

            if value == PRESENTLBL:
                value = 'x'

            rows[row][col] = value

        rows = [grid.GetColLabels()] + rows
        return rows


    def __populateGrid(self):
        """Populates the contents of the file tree grid. The contents
        are retrieved from the :class:`.FileTreeManager`.
        """

        mgr      = self.__mgr
        grid     = self.__grid
        fgroups  = mgr.filegroups
        varcols  = mgr.varcols
        fixedoff = 1 if self.__notes == 'left' else 0
        msg      = strings.messages[self, 'buildingList']

        fwoverlay.textOverlay(self.__grid, msg)

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
            for coli, filename in enumerate(fgroup.files,
                                            len(varcols) + fixedoff):
                if filename is not None: grid.SetText(rowi, coli, PRESENTLBL)
                else:                    grid.SetText(rowi, coli, '')

        self.Refresh()
        self.Update()


    def __notesIndex(self):
        """Returns the column index of the notes column. Assumes that a
        :class:`.FileTreeManager` has been passed to :meth:`.ResetGrid`.
        """

        nvarcols   = len(self.__mgr.varcols)
        nfixedcols = len(self.__mgr.fixedcols)

        if self.__notes == 'left': return nvarcols
        else:                      return nvarcols + nfixedcols


    def __createNotes(self):
        """Called by :meth:`ResetGrid`. Creates a ``wx.TextCtrl`` for each
        row, and adds it to the end column.
        """

        grid         = self.__grid
        notesIdx     = self.__notesIndex()
        nrows, ncols = grid.GetGridSize()

        for i in range(nrows):
            note = wx.TextCtrl(grid, i)
            grid.SetWidget(i, notesIdx, note)
            note.Bind(wx.EVT_CHAR_HOOK, self.__noteCharHook)


    def __noteCharHook(self, ev):
        """Called on character events for any of the note controls. If the
        character is a tab, up, or down arrow, focus is shifted to the next
        or previous note.
        """

        key   = ev.GetKeyCode()
        shift = ev.ShiftDown()

        if key not in (wx.WXK_TAB, wx.WXK_DOWN, wx.WXK_UP):
            ev.Skip()
            return

        if (key == wx.WXK_UP) or ((key == wx.WXK_TAB) and shift): offset = -1
        else:                                                     offset = 1

        grid         = self.__grid
        notesIdx     = self.__notesIndex()
        nrows, ncols = grid.GetGridSize()
        oldrow       = ev.GetEventObject().GetId()
        newrow       = oldrow + offset

        if   newrow < 0:      newrow = 0
        elif newrow >= nrows: newrow = nrows - 1

        if newrow != oldrow:
            grid.GetWidget(newrow, notesIdx).SetFocus()
            grid.SetSelection(newrow, -1)


    def __onSelect(self, ev):
        """Called when the user selects a row. Calls the
        :meth:`.FileTreeManager.Show` method.
        """

        overlayList = self.__ftpanel.overlayList
        group       = self.__mgr.filegroups[ev.row]

        # Disable events on the grid while
        # the overlays are being swapped,
        # otherwise FSLeyes will explode.
        freezeTime = time.time()
        freezeMsg  = strings.messages[self, 'loading']

        def freeze():
            self.__grid.SetEvtHandlerEnabled(False)
            idle.idle(fwoverlay.textOverlay, self.__grid, freezeMsg)
            self.__mgr.show(group)

        def thaw():
            self.__grid.SetEvtHandlerEnabled(True)
            self.Refresh()
            self.Update()

        # Wait until every overlay is in the
        # overlay list, or 5 seconds have
        # elapsed, before re-enabling the grid.
        def thawWhen():

            thawTime = time.time()
            files    = [f for f in group.files if f is not None]
            allin    = all([overlayList.find(f) is not None for f in files])

            return allin or ((thawTime - freezeTime) >= 5)

        try:
            freeze()
        finally:
            idle.idleWhen(thaw, thawWhen)


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
        grid.Refresh()


    def __genColumnLabels(self, varcols, fixedcols):
        """Called by :meth:`ResetGrid`. Generates a label for each column in
        the grid, including the *Notes* column if it is visible.

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

        # notes column (if visible) is on the
        # left or right of the fixed columns
        if self.__notes == 'left':
            collabels.insert(len(varcols), strings.labels[self, 'notes'])
        else:
            collabels.append(strings.labels[self, 'notes'])

        return collabels
