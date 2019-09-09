#!/usr/bin/env python
#
# updatecheck.py - The UpdateCheckAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.UpdateCheckAction`, which checks to see
if a new version of FSLeyes is available.
"""


import logging

import urllib.request as request
import ssl

import wx

# The HyperLinkCtrl is in wx.adv in wxPython/Phoenix
try:
    import wx.adv as wxadv

# But it is in wx in wxpython 3.
except ImportError:
    wxadv = wx

import fsl.version                  as fslversion

import fsleyes_widgets.utils.status as status
import fsleyes.version              as version
import fsleyes.strings              as strings
from . import                          base


log = logging.getLogger(__name__)


_FSLEYES_URL = 'https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSLeyes'
"""A url to direct the user towards to download the latest version of FSLeyes.
"""


_FSLEYES_VERSION_URL = 'https://fsl.fmrib.ox.ac.uk/'\
                       'fsldownloads/fsleyes/version.txt'
"""A url which points to a text file that contains the most recently released
FSLeyes version number.
"""


class UpdateCheckAction(base.Action):
    """The :class:`.UpdateCheckAction` is an :class:`.Action` which checks to
    see if a new version of FSLeyes is available, and tells the user if there
    is.
    """


    def __init__(self, overlayList, displayCtx):
        """Create an ``UpdateCheckAction``. """
        base.Action.__init__(
            self, overlayList, displayCtx, self.__checkForUpdates)


    def __checkForUpdates(self,
                          showUpToDateMessage=True,
                          showErrorMessage=True,
                          ignorePoint=False):
        """Run this action. Downloads a text file from a URL which contains
        the latest available version of FSLeyes. Compares that version with
        the running version. Displays a message to the user.

        :arg showUpToDateMessage: Defaults to ``True``. If ``False``, and
                                  the current version of FSLeyes is up to
                                  date, the user is not informed.

        :arg showErrorMessage:    Defaults to ``True``. If ``False``, and
                                  some error occurs while checking for
                                  updates, the user is not informed.

        :arg ignorePoint:         Defaults to ``False``. If ``True``, the
                                  point release number is ignored in the
                                  comparison.
        """

        errMsg   = strings.messages[self, 'newVersionError']
        errTitle = strings.titles[  self, 'newVersionError']

        with status.reportIfError(errTitle,
                                  errMsg,
                                  raiseError=False,
                                  report=showErrorMessage):

            log.debug('Checking for FSLeyes updates ({})'.format(
                _FSLEYES_VERSION_URL))

            ctx                = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode    = ssl.CERT_NONE

            f        = request.urlopen(_FSLEYES_VERSION_URL, context=ctx)
            latest   = f.read().decode('utf-8').strip()
            current  = version.__version__
            upToDate = fslversion.compareVersions(latest,
                                                  current,
                                                  ignorePoint) <= 0

            log.debug('This version of FSLeyes ({}) is '
                      '{} date (latest: {})'.format(
                          current,
                          'up to' if upToDate else 'out of',
                          latest))

            if upToDate and not showUpToDateMessage:
                return

            urlMsg = strings.messages[self, 'updateUrl']

            if upToDate:
                title = strings.titles[  self, 'upToDate']
                msg   = strings.messages[self, 'upToDate']
                msg   = msg.format(current)

            else:
                title = strings.titles[  self, 'newVersionAvailable']
                msg   = strings.messages[self, 'newVersionAvailable']
                msg   = msg.format(current, latest, _FSLEYES_URL)

            parent = wx.GetTopLevelWindows()[0]
            dlg    = UrlDialog(parent, title, msg, urlMsg, _FSLEYES_URL)

            dlg.CentreOnParent()
            dlg.ShowModal()


class UrlDialog(wx.Dialog):
    """Custom ``wx.Dialog`` used by the :class:`UpdateCheckAction` to
    display a message containing the FSLeyes download URL to the user.
    """


    def __init__(self,
                 parent,
                 title,
                 msg,
                 urlMsg=None,
                 url=None):
        """Create a ``UrlDialog``.

        :arg parent: ``wx`` parent object
        :arg title:  Dialog title
        :arg msg:    Message to display
        :arg urlMsg: Message to display next to the URL. Not shown if a URL
                     is not provided.
        :arg url:    URL to display.
        """

        wx.Dialog.__init__(self,
                           parent,
                           title=title,
                           style=wx.DEFAULT_DIALOG_STYLE)

        ok  = wx.Button(    self, label='Ok', id=wx.ID_OK)
        msg = wx.StaticText(self, label=msg)

        self.__ok = ok

        if urlMsg is not None:
            urlMsg = wx.StaticText(self, label=urlMsg)
        if url is not None:
            url = wxadv.HyperlinkCtrl(self, url=url)

        sizer    = wx.BoxSizer(wx.VERTICAL)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add((1, 20),  flag=wx.EXPAND, proportion=1)
        sizer.Add(msg,      flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)
        sizer.Add((1, 20),  flag=wx.EXPAND, proportion=1)

        if urlMsg is not None and url is not None:
            sizer.Add(urlMsg,  flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)
            sizer.Add((1, 5),  flag=wx.EXPAND, proportion=1)

        if url is not None:
            sizer.Add(url,     flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=20)
            sizer.Add((1, 20), flag=wx.EXPAND, proportion=1)

        btnSizer.Add((20, 1),  flag=wx.EXPAND, proportion=1)
        btnSizer.Add(ok,       flag=wx.EXPAND)
        btnSizer.Add((20, 1),  flag=wx.EXPAND)

        sizer.Add(btnSizer, flag=wx.EXPAND)
        sizer.Add((1, 20),  flag=wx.EXPAND, proportion=1)

        ok.SetDefault()
        self.SetSizer(sizer)
        self.Layout()
        self.Fit()


    @property
    def ok(self):
        """Return a reference to the OK button. """
        return self.__ok
