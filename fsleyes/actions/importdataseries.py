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
import numpy   as np

import fsleyes_widgets.numberdialog as numdlg
import fsl.data.image               as fslimage
import fsl.utils.settings           as fslsettings

import fsleyes.strings              as strings
import fsleyes.plotting             as plotting
import fsleyes.colourmaps           as fslcm


from . import base


class ImportDataSeriesAction(base.Action):

    def __init__(self, overlayList, displayCtx, plotPanel):

        base.Action.__init__(self, overlayList, displayCtx, self.__doImport)
        self.__plotPanel = plotPanel


    def __doImport(self):

        import wx

        frame = wx.GetApp().GetTopWindow()

        # Ask the user where to get the data
        msg     = strings.messages[self, 'selectFile']
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.FileDialog(frame,
                                message=msg,
                                defaultDir=fromDir,
                                style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()
        fileName = op.basename(filePath)

        # Load the file, show an
        # error if it fails
        try:

            # Assuming that the data series
            # to plot are stored as columns
            data = np.loadtxt(filePath, dtype=float).T

            # Make sure the data is 2D, to
            # make code below easier and
            # happier.
            if len(data.shape) == 1:
                data = data.reshape((1, -1))

        except Exception as e:
            title = strings.titles[  self, 'error']
            msg   = strings.messages[self, 'error'].format(
                filePath,
                '{}: {}'.format(type(e).__name__, str(e)))

            wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK)
            return

        fslsettings.write('loadSaveOverlayDir', filePath)

        # Ask the user the x axis scaling factor.
        # If the currently selected overlay is
        # Nifti and 4D, default to its pixdim[3]
        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is not None                 and \
           isinstance(overlay, fslimage.Nifti) and \
           len(overlay.shape) == 4             and \
           self.__plotPanel.usePixdim:
            xscale = overlay.pixdim[3]

        else:
            xscale = 1

        title = strings.titles[  self, 'selectXScale']
        msg   = strings.messages[self, 'selectXScale']

        # If the user pushes 'Ok', the entered value
        # is used as a fixed X axis interval. Otherwise,
        # it is assumed that the first column in the
        # file is the x axis data.
        dlg   = numdlg.NumberDialog(
            frame,
            title=title,
            message=msg,
            initial=xscale,
            minValue=1e-5,
            cancelText=strings.labels[self, 'firstColumnIsX'])

        firstColumnIsX = dlg.ShowModal() != wx.ID_OK
        xscale         = dlg.GetValue()

        # Add the data series
        series = []

        if firstColumnIsX:
            xdata = data[0,  :]
            ydata = data[1:, :]
        else:
            xdata = np.arange(0, data.shape[1] * xscale, xscale, dtype=float)
            ydata = data

        for i, ydata in enumerate(ydata):

            x   = np.array(xdata)
            y   = np.array(ydata)
            fin = np.isfinite(x) & np.isfinite(y)
            x   = x[fin]
            y   = y[fin]

            ds = plotting.DataSeries(None,
                                     self.overlayList,
                                     self.displayCtx,
                                     self.__plotPanel.canvas)
            ds.setData(x, y)

            # If we recognise the file name,
            # we can give it a useful label.
            label = strings.plotLabels.get(
                '{}.{}'  .format(fileName, i),
                '{} [{}]'.format(fileName, i))

            ds.label     = label
            ds.lineWidth = 1
            ds.colour    = fslcm.randomDarkColour()

            series.append(ds)

        self.__plotPanel.canvas.dataSeries.extend(series)
