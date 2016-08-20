#!/usr/bin/env python
#
# importdataseries.py - The ImportDataSeriesAction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ImportDataSeriesAction`, which is used by
:class:`.PlotPanel` views to import data series from a text file.
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


class ImportDataSeriesAction(action.Action):

    def __init__(self, overlayList, displayCtx, plotPanel):

        action.Action.__init__(self, self.__doImport)
        
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__plotPanel   = plotPanel

        

    def __doImport(self):

        import wx
        
        # Ask the user where to get the data
        msg     = strings.messages[self, 'selectFile']
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.FileDialog(self.__plotPanel,
                                message=msg,
                                defaultDir=fromDir,
                                style=wx.FD_OPEN | wx.FD_MULTIPLE)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()
        fileName = op.basename(filePath)

        # Load the file, show an
        # error if it fails
        try:
            
            # Assuming that the data series 
            # to plot are stored as columns
            data = np.loadtxt(filePath).T
            
        except Exception as e:
            title = strings.titles[  self, 'error']
            msg   = strings.messages[self, 'error'].format(
                filePath,
                '{}: {}'.format(type(e).__name__, str(e)))
            
            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK)
            return

        # Ask the user the x axis scaling factor.
        # If the currently selected overlay is
        # Nifti and 4D, default to its pixdim[3]
        overlay = self.__displayCtx.getSelectedOverlay()
        
        if all((overlay is not None,
                isinstance(overlay, fslimage.Nifti),
                len(overlay.shape) == 4)):
            xscale = overlay.pixdim[3]
            
        else:
            xscale = 1

        title = strings.titles[  self, 'selectXScale']
        msg   = strings.messages[self, 'selectXScale']
        dlg   = numdlg.NumberDialog(self.__plotPanel,
                                    title=title,
                                    message=msg,
                                    initial=xscale,
                                    minValue=1e-5)

        if dlg.ShowModal() != wx.ID_OK:
            return

        # Add the data series
        series = []

        for i, ydata in enumerate(data):

            xdata = np.arange(0, len(ydata) * xscale, xscale)
            ds    = plotting.DataSeries(None)
            ds.setData(xdata, ydata)

            # If we recognise the file name,
            # we can give it a useful label.
            label = strings.plotLabels.get(
                '{}.{}'  .format(fileName, i),
                '{} [{}]'.format(fileName, i))

            ds.label     = label
            ds.lineWidth = 1
            ds.colour    = fslcm.randomDarkColour()
            
            series.append(ds)

        self.__plotPanel.dataSeries.extend(series)
