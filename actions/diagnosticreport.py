#!/usr/bin/env python
#
# diagnosticreport.py - The DiagnosticReportAction
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`DiagnosticReportAction`, which allows
the user to generate a report of the current *FSLeyes* state, to send to me
for bug reporting purposes.
"""


import os
import json
import logging
import platform
from collections import OrderedDict

import wx

import                     action
import fsl.data.strings as strings
import fsl.utils.status as status


log = logging.getLogger(__name__)


class DiagnosticReportAction(action.Action):
    """
    """

    def __init__(self, overlayList, displayCtx, frame):

        action.Action.__init__(self, self.__action)

        self.__frame       = frame
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __action(self):

        dlg = wx.FileDialog( 
            self.__frame,
            message=strings.titles[self, 'saveReport'],
            defaultDir=os.getcwd(),
            defaultFile='report.txt',
            style=wx.FD_SAVE)

        if dlg.ShowModal()  != wx.ID_OK:
            return

        path = dlg.GetPath()

        status.update('Writing diagnostic report to {}...'.format(path))

        report = self.__generateReport()
        report = self.__formatReport(report)

        log.debug('Diagnostic report:\n{}'.format(report))

        with open(path, 'wt') as f:
            f.write(report)



    def __generateReport(self):

        import fsl.version              as version
        import fsl.fsleyes.perspectives as perspectives

        report   = OrderedDict()
        overlays = []
        
        for i, ovl in enumerate(self.__overlayList):
            overlays.append(OrderedDict([
                ('type',   type(ovl).__name__),
                ('name',   ovl.name),
                ('source', ovl.dataSource)]))

        report['Platform'] = platform.platform()
        report['Python']   = '{}  {}'.format(platform.python_version(),
                                             platform.python_compiler())
        report['Version']  = version.__version__
        report['Layout']   = perspectives.serialisePerspective(self.__frame)
        report['Overlays'] = overlays

        report['Master display context'] = self.__displayContextReport(
            self.__overlayList,
            self.__displayCtx)

        for viewPanel in self.__frame.getViewPanels():

            # Accessing the undocumented
            # AuiPaneInfo.name attribute
            vpName       = self.__frame.getViewPanelInfo(viewPanel).name
            vpDisplayCtx = viewPanel.getDisplayContext()

            report[vpName] = OrderedDict([
                ('View',            self.__viewPanelReport(viewPanel)),
                ('Display context', self.__displayContextReport(
                    self.__overlayList,
                    vpDisplayCtx))])

        return report


    def __displayContextReport(self, overlayList, displayCtx):
        
        pass

    def __viewPanelReport(self, viewPanel):
        pass


    def __formatReport(self, reportDict):

        return json.dumps(reportDict, indent=2)
