#!/usr/bin/env python


import os
import os.path as op

from fsleyes.plugins.controls.filetreepanel import FileTreePanel

from fsleyes.tests import run_with_orthopanel, realYield, MockFileDialog

from .test_filetree_manager import _query

def test_filetreepanel():
    run_with_orthopanel(_test_filetreepanel)


def _test_filetreepanel(ortho, overlayList, displayCtx):

    with _query(realdata=True) as query:

        ortho.togglePanel(FileTreePanel)
        realYield()

        ftpanel = [p for p in ortho.getPanels()
                   if isinstance(p, FileTreePanel)][0]

        datadir = os.getcwd()
        tree    = op.join(datadir, 'tree.tree')

        idx = ftpanel.treeChoice.GetStrings().index('tree.tree')
        ftpanel.treeChoice.SetSelection(idx)
        ftpanel._onTreeChoice()

        with MockFileDialog(True) as dlg:
            dlg.GetPath_retval = datadir
            ftpanel._onLoadDir()

        realYield()

        assert sorted(ftpanel.fileTypePanel.GetLabels()) == \
            ['T1w', 'T2w', 'surface']
        assert ftpanel.varPanel.GetVaryings() == {
            'subject' : '*',
            'session' : '*',
            'hemi' : '*',
            'surf' : '*'}
