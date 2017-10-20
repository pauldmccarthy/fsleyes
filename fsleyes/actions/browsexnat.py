#!/usr/bin/env python
#
# browsexnat.py - Action which allows the user to connect to and browse an
# XNAT repository.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`BrowseXNATAction`, which allows the user
to connect to and browse an XNAT repository.
"""


import os.path as op
import            tempfile

import wx
import wxnat

import fsl.utils.settings  as fslsettings
import fsleyes.strings     as strings
import fsleyes.autodisplay as autodisplay

from . import base
from . import loadoverlay


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
        base.Action.__init__(self, self.__openBrowser)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame


    def __openBrowser(self):
        """Opens a :class:`XNATBrowser`, then adds any files that the user
        selected to the :class:`.OverlayList`.
        """

        hosts    = fslsettings.read('fsleyes.xnat.hosts',    [])
        accounts = fslsettings.read('fsleyes.xnat.accounts', {})

        hosts    = ['10.1.1.17', 'central.xnat.org', 'xw2017-01.xnat.org']
        accounts = {
            'central.xnat.org'   : ('guest', 'guest'),
            '10.1.1.17'          : ('admin', 'admin'),
            'xw2017-01.xnat.org' : ('admin', 'R0tt3rd@m')
        }

        dlg = XNATBrowser(self.__frame, hosts, accounts)

        dlg.Layout()
        dlg.Fit()
        dlg.SetSize((-1, 400))
        dlg.CentreOnParent()

        if dlg.ShowModal() != wx.ID_OK:
            return

        paths    = dlg.GetPaths()
        hosts    = dlg.GetHosts()
        accounts = dlg.GetAccounts()

        # No files downloaded
        if len(paths) == 0:
            return

        # Save successful hosts/credentials
        fslsettings.write('fsleyes.xnat.hosts',    hosts)
        fslsettings.write('fsleyes.xnat.accounts', accounts)

        def onLoad(overlays):

            if len(overlays) == 0:
                return

            self.__overlayList.extend(overlays)

            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[-1]

            if self.__displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.__overlayList,
                                            self.__displayCtx)

        loadoverlay.loadOverlays(paths,
                                 onLoad=onLoad,
                                 saveDir=False,
                                 inmem=self.__displayCtx.loadInMemory)


class XNATBrowser(wx.Dialog):
    """The ``XNATBrowser`` contains a ``wxnat.XNATBrowserPanel``, allowing the
    user to connect to and browse an XNAT repository. It contains a *Download*
    button which, when clicked, downloads all selected files from the
    repository into a temporary directory. Once the files have been downloaded,
    their paths can be retrieved via the :meth:`GetPaths` method.
    """


    def __init__(self,
                 parent,
                 knownHosts=None,
                 knownAccounts=None,
                 saveTo=None):
        """Create a ``XNATBrowser``.

        :arg parent:        ``wx`` parent object

        :arg knownHosts:    List of hosts to use as auto-complete options

        :arg knownAccounts: Mapping containing login credentials, in the
                            ``{ host : (username, password) }``.

        :arg saveTo:        Directory to save downloaded files to. If ``None``,
                            a temporary directory is created and used.
        """

        wx.Dialog.__init__(self,
                           parent,
                           title=strings.titles[self],
                           style=wx.RESIZE_BORDER)

        filters = {'file' : '*.nii|*.nii.gz|*.img|*.img.gz|*.gii|*.vtk'}

        self.__panel = wxnat.XNATBrowserPanel(
            self,
            knownHosts=knownHosts,
            knownAccounts=knownAccounts,
            filterType='glob',
            filters=filters)

        self.__ok       = wx.Button(self, wx.ID_OK)
        self.__cancel   = wx.Button(self, wx.ID_CANCEL)
        self.__btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer    = wx.BoxSizer(wx.VERTICAL)

        self.__ok    .SetLabel(strings.labels[self, 'ok'])
        self.__cancel.SetLabel(strings.labels[self, 'cancel'])

        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND, proportion=1)
        self.__btnSizer.Add(self.__ok,     flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND)
        self.__btnSizer.Add(self.__cancel, flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND)

        self.__sizer.Add((1, 10),         flag=wx.EXPAND)
        self.__sizer.Add(self.__panel,    flag=wx.EXPAND, proportion=1)
        self.__sizer.Add((1, 10),         flag=wx.EXPAND)
        self.__sizer.Add(self.__btnSizer, flag=wx.EXPAND)
        self.__sizer.Add((1, 10),         flag=wx.EXPAND)

        self.SetSizer(self.__sizer)
        self.__ok.SetDefault()

        self.__panel .Bind(wxnat.EVT_XNAT_FILE_SELECT_EVENT, self.__onOk)
        self.__ok    .Bind(wx.EVT_BUTTON,                    self.__onOk)
        self.__cancel.Bind(wx.EVT_BUTTON,                    self.__onCancel)

        self.__saveTo = saveTo
        self.__paths  = []


    def GetPaths(self):
        """Returns paths to the files that were downloaded. """
        return self.__paths


    def __onOk(self, ev):
        """Called when the *Ok* button is pushed. Downloads the files to a
        temporary directory.
        """

        files = self.__panel.GetSelectedFiles()

        if len(files) == 0:
            self.EndModal(wx.ID_OK)

        if self.__saveTo is None: destdir = tempfile.mkdtemp('fsleyes_xnat')
        else:                     destdir = self.__saveTo

        for f in files:
            dest = op.join(destdir, f.id)
            self.__panel.DownloadFile(f, dest)
            self.__paths.append(dest)

        self.__panel.EndSession()
        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the *Cancel* button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_CANCEL)
