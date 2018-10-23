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

from   fsl.utils.platform import platform as fslplatform
import fsleyes_widgets.utils.status       as status
import fsleyes.strings                    as strings
import fsleyes.state                      as fslstate
from . import                                base


log = logging.getLogger(__name__)


class DiagnosticReportAction(base.Action):
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
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        base.Action.__init__(self, self.__action)

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

        import wx

        dlg = wx.FileDialog(
            self.__frame,
            message=strings.titles[self, 'saveReport'],
            defaultDir=os.getcwd(),
            defaultFile='report.txt',
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

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

        import fsleyes.version as version

        report   = OrderedDict()
        overlays = []

        for i, ovl in enumerate(self.__overlayList):
            overlays.append(OrderedDict([
                ('type',   type(ovl).__name__),
                ('name',   ovl.name),
                ('source', ovl.dataSource)]))

        report['Platform']    = platform.platform()
        report['Python']      = '{}  {}'.format(platform.python_version(),
                                                platform.python_compiler())
        report['Version']     = version.__version__
        report['OpenGL']      = self.__openGLReport()
        report['Settings']    = self.__settingsReport()
        report['State']       = fslstate.getState(self.__frame)

        return report


    def __settingsReport(self):
        """Creates and returns a dictionary containing:

         - *FSLeyes* settings stored via the :mod:`.settings` module
        """

        import fsl.utils.settings as fslsettings

        report   = OrderedDict()
        settings = fslsettings.readAll()

        for k, v in settings.items():
            report[k] = v

        return report


    def __openGLReport(self):
        """Creates and returns a dictionary containing information about the
        OpenGL platform.
        """

        import OpenGL.GL as gl

        report = OrderedDict()

        version    = gl.glGetString( gl.GL_VERSION)   .decode('ascii')
        renderer   = gl.glGetString( gl.GL_RENDERER)  .decode('ascii')
        extensions = gl.glGetString( gl.GL_EXTENSIONS).decode('ascii')

        report['Version']       = version
        report['Compatibility'] = fslplatform.glVersion
        report['Renderer']      = renderer
        report['Texture size']  = str(gl.glGetInteger(gl.GL_MAX_TEXTURE_SIZE))
        report['Extensions']    = extensions.split(' ')

        return report


    def __formatReport(self, reportDict):
        """Converts the given hierarchical dictionary to a JSON-formatted
        string.
        """
        return json.dumps(reportDict, indent=2)
