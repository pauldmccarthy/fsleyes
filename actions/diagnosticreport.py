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
    """The ``DiagnosticReportAction`` generates a JSON-formatted report file
    containing information about the current state of *FSLeyes*. When the this
    :class:`.Action` is run, the user is prompted to select a location to save
    the file Then the report is generated, and written out to the specified
    location.
    """

    
    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``DiagnosticReportAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The master :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLEyesFrame`.
        """

        action.Action.__init__(self, self.__action)

        self.__frame       = frame
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __action(self):
        """This method is the guts of the ``DiagnosticReportAction``. It does
        the following:

          1. Prompts the user to select a location to save the report file.

          2. Generates the report.

          3. Formats the report as JSON.

          4. Saves the report to the specified location.
        """

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
        """Generates and returns a *report*, a hierarchical dictionary
        containing information about the current system and *FSLeyes*
        state.
        """

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
        """Creates and returns a hierarchical dictionary containing
        information about the given :class:`.DisplayContext` and the
        :class:`.Display`/:class:`.DisplayOpts` instances which it
        is managing.
        """

        report   = OrderedDict()
        overlays = []
        props    = displayCtx.getAllProperties()[0]

        for overlay in overlayList:

            display = displayCtx.getDisplay(overlay)
            opts    = displayCtx.getOpts(   overlay)

            overlays.append(OrderedDict([
                ('Display',     self.__displayReport(    display)),
                ('DisplayOpts', self.__displayOptsReport(opts))]))

        for prop in props:
            report[prop] = str(getattr(displayCtx, prop))
            
        report['overlays'] = overlays

        return report

    
    def __displayReport(self, display):
        """Creates and returns a dictionary containing informtion about
        the given :class:`.Display` instance.
        """
        
        report = OrderedDict()
        props  = display.getAllProperties()[0]

        for prop in props:
            report[prop] = str(getattr(display, prop))
        
        return report 

    
    def __displayOptsReport(self, opts):
        """Creates and returns a dictionary containing informtion about
        the given :class:`.DisplayOpts` instance.
        """ 
        
        report = OrderedDict()

        report['type'] = type(opts).__name__

        props  = opts.getAllProperties()[0]

        for prop in props:
            value = getattr(opts, prop)
            if prop in ('cmap', 'negativeCmap'):
                value = value.name
                
            report[prop] = str(value)

        return report

    
    def __viewPanelReport(self, viewPanel):
        """Creates and returns a dictionary containing informtion about
        the given :class:`.ViewPanel`.
        """ 

        import fsl.fsleyes.views as views
        
        report = OrderedDict()
        props  = viewPanel.getAllProperties()[0]

        report['type'] = type(viewPanel).__name__

        for prop in props:
            report[prop] = str(getattr(viewPanel, prop))

        if isinstance(viewPanel, views.CanvasPanel):
            
            sceneOptsReport = OrderedDict()
            sceneOpts       = viewPanel.getSceneOptions()
            props           = sceneOpts.getAllProperties()[0]

            sceneOptsReport['type'] = type(sceneOpts).__name__
            
            for prop in props:
                sceneOptsReport[prop] = str(getattr(sceneOpts, prop))

            report['SceneOpts'] = sceneOptsReport
        
        return report

    
    def __formatReport(self, reportDict):
        """Converts the given hierarchical dictionary to a JSON-formatted
        string.
        """
        return json.dumps(reportDict, indent=2)
