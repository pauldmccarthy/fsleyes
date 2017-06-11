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

from six.moves.urllib import request

import fsl.version                  as fslversion

import fsleyes_widgets.utils.status as status
import fsleyes.version              as version
import fsleyes.strings              as strings
from . import                          base


log = logging.getLogger(__name__)


_FSLEYES_URL = 'https://users.fmrib.ox.ac.uk/~paulmc/fsleyes/dist/'
"""A url which contains the latest version of FSLeyes for download. """


_FSLEYES_VERSION_URL = '{}version.txt'.format(_FSLEYES_URL)
"""A url which points to a text file that contains the most recently released
FSLeyes version number.
"""


class UpdateCheckAction(base.Action):
    """The :class:`.UpdateCheckAction` is an :class:`.Action` which checks to
    see if a new version of FSLeyes is available, and tells the user if there
    is.
    """


    def __init__(self):
        """Create an ``UpdateCheckAction``. """
        base.Action.__init__(self, self.__checkForUpdates)


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

        import wx

        errMsg   = strings.messages[self, 'newVersionError']
        errTitle = strings.titles[  self, 'newVersionError']

        with status.reportIfError(errTitle, errMsg, report=showErrorMessage):

            log.debug('Checking for FSLeyes updates ({})'.format(
                _FSLEYES_VERSION_URL))

            f        = request.urlopen(_FSLEYES_VERSION_URL)
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

            if upToDate:
                title = strings.titles[  self, 'upToDate']
                msg   = strings.messages[self, 'upToDate']
                msg   = msg.format(current)

            else:
                title = strings.titles[  self, 'newVersionAvailable']
                msg   = strings.messages[self, 'newVersionAvailable']
                msg   = msg.format(current, latest, _FSLEYES_URL)

            # TODO Make a custom dialog with a clickable URL.
            #      MessageBox only supports plain text
            wx.MessageBox(msg, title, wx.OK | wx.ICON_INFORMATION)
