#!/usr/bin/env python
#
# exportdataseries.py - The ExportDataSeriesAction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ExportDataSeriesAction`, which is used by
:class:`.PlotPanel` views to export data series to a text file.
"""

import            os 
import os.path as op

import numpy                 as np

import pwidgets.numberdialog as numdlg

import fsl.data.image        as fslimage
import fsl.utils.settings    as fslsettings
import fsleyes.strings       as strings
import fsleyes.plotting      as plotting
import fsleyes.colourmaps    as fslcm


from . import action


class ExportDataSeriesAction(action.Action):

    def __init__(self, overlayList, displayCtx, plotPanel):

        action.Action.__init__(self, self.__doExport)
        
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__plotPanel   = plotPanel

        

    def __doExport(self, extraSeries=None):
        
        import wx

        # Ask the user where they want to save the data
        msg     = strings.messages[self, 'exportDataSeries']
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.FileDialog(self,
                                message=msg,
                                defaultDir=fromDir,
                                defaultFile='dataseries.txt',
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() != wx.ID_OK:
            return

        for ds in self.dataSeries:
            pass 
