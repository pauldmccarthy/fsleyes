#!/usr/bin/env python
#
# exportdataseries.py - The ExportDataSeriesAction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ExportDataSeriesAction`, which is used by
:class:`.PlotPanel` views to export data series to a text file.
"""


import                          os
import os.path               as op
import numpy                 as np

import fsl.utils.settings    as fslsettings
import fsleyes.strings       as strings
from . import                   base


class ExportDataSeriesAction(base.Action):

    def __init__(self, overlayList, displayCtx, plotPanel):

        base.Action.__init__(self, overlayList, displayCtx, self.__doExport)
        self.__plotPanel = plotPanel


    def __doExport(self):

        import wx

        # Ask the user if they want to save the
        # x axis values as the first column
        dlg = wx.MessageDialog(
            wx.GetTopLevelWindows()[0],
            message=strings.messages[self, 'saveXColumn'],
            caption=strings.titles[  self, 'saveXColumn'],
            style=(wx.ICON_QUESTION |
                   wx.YES_NO        |
                   wx.CANCEL        |
                   wx.YES_DEFAULT))

        result = dlg.ShowModal()

        if result == wx.ID_CANCEL:
            return

        savex = result == wx.ID_YES

        # Ask the user where they want to save the data
        msg     = strings.messages[self, 'selectFile']
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.FileDialog(wx.GetApp().GetTopWindow(),
                                message=msg,
                                defaultDir=fromDir,
                                defaultFile='dataseries.txt',
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()

        dss = self.__plotPanel.canvas.getDrawnDataSeries()
        xs  = [ds[1] for ds in dss]
        ys  = [ds[2] for ds in dss]
        dss = [ds[0] for ds in dss]

        # Create some x data, unified
        # across all data series
        xdata = np.unique(np.concatenate(xs))

        # Linearly interpolate each data series
        # according to the merged x data
        ydata = [np.interp(xdata, x, y, left=np.nan, right=np.nan)
                 for x, y in zip(xs, ys)]

        # Turn it all into one big
        # array and save it out
        if savex: data = np.vstack([xdata] + ydata)
        else:     data = np.vstack( ydata)

        np.savetxt(filePath, data.T, fmt='% 0.8f')

        fslsettings.write('loadSaveOverlayDir', op.dirname(filePath))
