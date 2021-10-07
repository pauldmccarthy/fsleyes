#!/usr/bin/env python
#
# browsexnat.py - Action which allows the user to connect to and browse an
# XNAT repository.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`BrowseXNATAction`, which allows the user
to connect to and browse an XNAT repository. If ``wxnatpy``
(https://github.com/pauldmccarthy/wxnatpy) is not present, the action is
disabled.
"""


import            os
import os.path as op

import wx

import fsl.utils.settings  as fslsettings
import fsleyes.strings     as strings
import fsleyes.autodisplay as autodisplay

from . import base
from . import loadoverlay

# if wxnatpy is not present, the
# action is permanently disabled
try:
    import wxnat
except ImportError:
    wxnat = None


class BrowseXNATAction(base.Action):
    """The ``BrowseXNATAction`` allows the user to open files from an XNAT
    repository. It opens a :class:`XNATBrowser``, and adds the files that
    the user selected into the :class:`.OverlayList`.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``BrowseXNATAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, overlayList, displayCtx, self.__openBrowser)
        self.__frame = frame

        if wxnat is None:
            self.enabled = False


    def __openBrowser(self):
        """Opens a :class:`XNATBrowser`, then adds any files that the user
        selected to the :class:`.OverlayList`.
        """

        def onLoad(paths, overlays):

            if len(overlays) == 0:
                return

            self.overlayList.extend(overlays)
            self.displayCtx.selectedOverlay = self.displayCtx.overlayOrder[-1]

            if self.displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.overlayList,
                                            self.displayCtx)

        def load(paths):
            if len(paths) == []:
                return
            loadoverlay.loadOverlays(paths,
                                     onLoad=onLoad,
                                     saveDir=False,
                                     inmem=self.displayCtx.loadInMemory)


        dlg = XNATBrowser(self.__frame, load)
        dlg.Layout()
        dlg.Fit()
        dlg.SetSize((-1, 400))
        dlg.CentreOnParent()
        dlg.Show()


class XNATBrowser(wx.Dialog):
    """The ``XNATBrowser`` contains a ``wxnat.XNATBrowserPanel``, allowing the
    user to connect to and browse an XNAT repository. It contains a *Download*
    button which, when clicked, downloads all selected files from the
    repository into a temporary directory, and passes the file paths to a
    provided callback function.
    """


    def __init__(self, parent, loadFunc=None):
        """Create a ``XNATBrowser``.

        :arg parent:   ``wx`` parent object

        :arg loadFunc: Function to call when the user has downloaded
                       some files. Passed a list of files paths.
        """

        if wxnat is None:
            raise RuntimeError('wxnatpy is not available!')

        wx.Dialog.__init__(self,
                           parent,
                           title=strings.titles[self],
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        hosts    = fslsettings.read('fsleyes.xnat.hosts',    [])
        accounts = fslsettings.read('fsleyes.xnat.accounts', {})
        filters  = {'file' : '*.nii|*.nii.gz|*.img|*.img.gz|*.gii|*.vtk'}

        self.__loadFunc = loadFunc
        self.__destDir  = None
        self.__panel    = wxnat.XNATBrowserPanel(
            self,
            knownHosts=hosts,
            knownAccounts=accounts,
            filterType='glob',
            filters=filters)

        self.__download     = wx.Button(self, wx.ID_OK)
        self.__close        = wx.Button(self, wx.ID_CANCEL)
        self.__fullPathsLbl = wx.StaticText(self)
        self.__fullPaths    = wx.CheckBox(self)
        self.__ctrlSizer    = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer        = wx.BoxSizer(wx.VERTICAL)

        self.__fullPathsLbl.SetLabel(strings.labels[self, 'fullPaths'])
        self.__download    .SetLabel(strings.labels[self, 'download'])
        self.__close       .SetLabel(strings.labels[self, 'close'])

        self.__ctrlSizer.Add((10, 1),             flag=wx.EXPAND, proportion=1)
        self.__ctrlSizer.Add(self.__fullPathsLbl, flag=wx.EXPAND)
        self.__ctrlSizer.Add(self.__fullPaths,    flag=wx.EXPAND)
        self.__ctrlSizer.Add((10, 1),             flag=wx.EXPAND)
        self.__ctrlSizer.Add(self.__download,     flag=wx.EXPAND)
        self.__ctrlSizer.Add((10, 1),             flag=wx.EXPAND)
        self.__ctrlSizer.Add(self.__close,        flag=wx.EXPAND)
        self.__ctrlSizer.Add((10, 1),             flag=wx.EXPAND)

        self.__sizer.Add((1, 10),          flag=wx.EXPAND)
        self.__sizer.Add(self.__panel,     flag=wx.EXPAND, proportion=1)
        self.__sizer.Add((1, 10),          flag=wx.EXPAND)
        self.__sizer.Add(self.__ctrlSizer, flag=wx.EXPAND)
        self.__sizer.Add((1, 10),          flag=wx.EXPAND)

        self.SetSizer(self.__sizer)
        self.__download.SetDefault()

        self.__panel   .Bind(wxnat.EVT_XNAT_ITEM_HIGHLIGHT_EVENT,
                             self.__onHighlight)
        self.__panel   .Bind(wxnat.EVT_XNAT_FILE_SELECT_EVENT,
                             self.__onDownload)
        self.__download.Bind(wx.EVT_BUTTON, self.__onDownload)
        self.__close   .Bind(wx.EVT_BUTTON, self.__onCloseButton)
        self           .Bind(wx.EVT_CLOSE,  self.__onClose)

        self.__fullPaths.SetValue(True)

        # ok/download button only enabled when file
        # items are selected in the tree view
        self.__download.Disable()


    def GetHosts(self):
        """Wraps ``wxnat.XNATBrowserPanel.GetHosts``. """
        return self.__panel.GetHosts()


    def GetAccounts(self):
        """Wraps ``wxnat.XNATBrowserPanel.GetAccounts``. """
        return self.__panel.GetAccounts()


    def __onHighlight(self, ev):
        """Called when the item selection in the tree browser is changed.
        Enables/disables the download button depending on whether any
        files are highlighted.
        """
        self.__download.Enable(len(self.__panel.GetSelectedFiles()) > 0)


    def __onDownload(self, ev):
        """Called when the *Download* button is pushed. Prompts the user to
        select a directory, and then downloads the files.
        """

        files = self.__panel.GetSelectedFiles()

        if len(files) == 0:
            return

        destDir = self.__destDir

        if destDir is None:
            destDir = fslsettings.read('fsleyes.xnat.downloaddir', os.getcwd())
            dlg     = wx.DirDialog(self,
                                   strings.labels[self, 'choosedir'],
                                   defaultPath=destDir)

            if dlg.ShowModal() != wx.ID_OK:
                return

            destDir        = dlg.GetPath()
            self.__destDir = destDir

        paths = []

        for f in files:
            if self.__fullPaths.GetValue():
                dest = wxnat.generateFilePath(f)
                dest = op.join(destDir, dest)
                os.makedirs(op.dirname(dest), exist_ok=True)
            else:
                dest = op.join(destDir, op.basename(dest))

            dest = self.__panel.DownloadFile(f, dest)

            if dest is not None:
                paths.append(dest)

        if self.__loadFunc is not None:
            self.__loadFunc(paths)

        fslsettings.write('fsleyes.xnat.downloaddir', destDir)


    def __onClose(self, ev):
        """Called on EVT_CLOSE events. Destroys this dialog. """
        self.__panel.EndSession()
        fslsettings.write('fsleyes.xnat.hosts',    self.GetHosts())
        fslsettings.write('fsleyes.xnat.accounts', self.GetAccounts())

        if self.IsModal(): self.EndModal(wx.ID_CANCEL)
        else:              self.Destroy()


    def __onCloseButton(self, ev):
        """Called when the *Close* button is pushed. Closes the dialog. """
        self.Close()
