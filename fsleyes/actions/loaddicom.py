#!/usr/bin/env python
#
# loaddicom.py - The LoadDicomAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadDicomAction` class, an :class:`.Action`
which allows the user to load images from a DICOM directory.

A few standalone functions are also defined in this module:

.. autosummary::
   :nosignatures:

   loadDicom
"""


import                 os
import os.path      as op
from   datetime import datetime

import wx

import fsleyes_widgets.widgetgrid     as wg
import fsleyes_widgets.utils.status   as status
import fsleyes_widgets.utils.progress as progress
import fsl.utils.settings             as fslsettings
import fsl.data.dicom                 as fsldcm
import fsleyes.strings                as strings
import fsleyes.autodisplay            as autodisplay
from . import                            base


class LoadDicomAction(base.Action):
    """The ``LoadDicomAction`` is an :class:`.Action` which allows the user to
    load images from a DICOM directory. When invoked, the ``LoadDicomAction``
    does the following:

    1. Prompts the user to select a DICOM directory
    2. Identifies the data series that are present in the directory
    3. Prompts the user to select which series they would like to load
    4. Loads the selected series.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create a ``LoadDicomAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__loadDicom)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame

        # permanently disable if
        # fsl.data.dicom says it
        # is disabled
        self.enabled = fsldcm.enabled()


    def __loadDicom(self):
        """Called when this ``LoadDicomAction`` is invoked. Calls the
        :func:`loadDicom` function.
        """

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

        loadDicom(parent=self.__frame, callback=onLoad)


def loadDicom(dcmdir=None, parent=None, callback=None):
    """Does the following:

      1. Prompts the user to select a DICOM directory (unless
         ``dcmdir is not None``)

      2. Loads metadata about all of the data series in the
         DICOM directory

      3. Uses a :class:`.BrowseDicomDialog` to allow the user
         to choose which data series they wish to load

      4. Loads the selected series, and passes them to the
         ``callback`` function if it is provided.

    :arg dcmdir:   Directory to load DICOMs from. If not provided, the user is
                   prompted to select a directory.

    :arg parent:   ``wx`` parent object.

    :arg callback: Function which is passed the loaded DICOM series
                   (:class:`.Image` objects).
    """

    if parent is None:
        parent = wx.GetTopLevelWindows()[0]

    # 1. prompt user to select dicom directory
    if dcmdir is None:
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.DirDialog(
            parent,
            message=strings.messages['loadDicom.selectDir'],
            defaultPath=fromDir,
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() != wx.ID_OK:
            return

        dcmdir = dlg.GetPath()

    # 2. load metadata about all data series in
    #    the DICOM directory. This is performed
    #    on a separate thread via the
    #    progress.runWithBounce function.
    series = []
    images = []

    def scan():
        try:
            series.extend(fsldcm.scanDir(dcmdir))
            if len(series) == 0:
                raise Exception('Could not find any DICOM '
                                'data series in {}'.format(dcmdir))

        except Exception as e:
            series.append(e)

    # 3. ask user which data series
    #    they want to load. This is called
    #    after the scan function has
    #    finished - see runWithBounce.
    def postScan(completed):

        # did the user cancel the progress dialog?
        if not completed:
            return

        # did an error occur in the scan step above?
        if isinstance(series[0], Exception):
            errTitle = strings.titles[  'loadDicom.scanError']
            errMsg   = strings.messages['loadDicom.scanError']
            status.reportError(errTitle, errMsg, series[0])
            return

        dlg = BrowseDicomDialog(parent, series)
        dlg.CentreOnParent()

        if dlg.ShowModal() != wx.ID_OK:
            return

        # load the selected series - this is
        # done asynchronously via another
        # call to runWithBounce.
        for i in reversed(list(range(len(series)))):
            if not dlg.IsSelected(i):
                series.pop(i)

        title = strings.titles[  'loadDicom.loading']
        msg   = strings.messages['loadDicom.loading']
        progress.runWithBounce(load, title, msg, callback=postLoad)

    # 4. Load the selected series. This is run
    #    on a separate thread via runWithBounce
    def load():
        try:
            for s in series:
                images.extend(fsldcm.loadSeries(s))

            if len(images) == 0:
                raise Exception('No images could be loaded '
                                'from {}'.format(dcmdir))

        except Exception as e:
            images.insert(0, e)

    # Pass the loaded images to the calback
    # function. This is called after the
    # load function has finished.
    def postLoad(completed):

        # Did the user cancel the progress dialog?
        if not completed:
            return

        # Did an error occur in the load step above?
        if isinstance(images[0], Exception):
            errTitle = strings.titles[  'loadDicom.loadError']
            errMsg   = strings.messages['loadDicom.loadError']
            status.reportError(errTitle, errMsg, images[0])
            return

        fslsettings.write('loadSaveOverlayDir',
                          op.dirname(dcmdir.rstrip(op.sep)))

        if callback is not None:
            callback(images)

    # Kick off the process
    title = strings.titles[  'loadDicom.scanning']
    msg   = strings.messages['loadDicom.scanning']
    progress.runWithBounce(scan, title, msg, callback=postScan)


class BrowseDicomDialog(wx.Dialog):
    """The ``BrowseDicomDialog`` contains a ``BrowseDicomPanel``, and a
    couple of buttons, allowing the user to select which DICOM series
    they would like to load.
    """

    def __init__(self, parent, dcmseries):
        """Create a ``BrowseDicomDialog``.

        :arg parent:    ``wx`` parent object
        :arg dcmseries: List of DICOM data series, as returned by the
                        :func:`fsl.data.dicom.scanDir` function.
        """

        wx.Dialog.__init__(self, parent, title=strings.titles[self])

        self.__browser = BrowseDicomPanel(self, dcmseries)
        self.__load    = wx.Button(self, id=wx.ID_OK)
        self.__cancel  = wx.Button(self, id=wx.ID_CANCEL)

        self.__load  .SetDefault()
        self.__load  .SetLabel(strings.labels[self, 'load'])
        self.__cancel.SetLabel(strings.labels[self, 'cancel'])

        self.__sizer    = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND, proportion=1)
        self.__btnSizer.Add(self.__load,   flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND)
        self.__btnSizer.Add(self.__cancel, flag=wx.EXPAND)
        self.__btnSizer.Add((10, 1),       flag=wx.EXPAND)

        self.__sizer.Add((1, 10),         flag=wx.EXPAND)
        self.__sizer.Add(self.__browser,  flag=wx.EXPAND, proportion=1)
        self.__sizer.Add((1, 10),         flag=wx.EXPAND)
        self.__sizer.Add(self.__btnSizer, flag=wx.EXPAND)
        self.__sizer.Add((1, 10),         flag=wx.EXPAND)

        self.SetSizer(self.__sizer)
        self.Layout()
        self.Fit()

        self.__load  .Bind(wx.EVT_BUTTON, self.__onLoad)
        self.__cancel.Bind(wx.EVT_BUTTON, self.__onCancel)


    def __onLoad(self, ev):
        """Called when the *Load* button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_OK)


    def __onCancel(self, ev):
        """Called when the *Cancel* button is pushed. Closes the dialog. """
        self.EndModal(wx.ID_CANCEL)


    def IsSelected(self, sidx):
        """Returns ``True`` if the DICOM series at the given index has
        been selected by the user, ``False`` otherwise.
        """
        return self.__browser.IsSelected(sidx)



class BrowseDicomPanel(wx.Panel):
    """The ``BrowseDicomPanel`` displayes information about a collection of
    DICOM data series, and allows the user to select which series they would
    like to load.
    """


    def __init__(self, parent, dcmseries):
        """Create a ``BrowseDicomPanel``.

        :arg parent:    ``wx`` parent object
        :arg dcmseries: List of DICOM data series, as returned by the
                        :func:`fsl.data.dicom.scanDir` function.
        """

        wx.Panel.__init__(self, parent)

        # we assume that this metadata
        # is the same across all series
        date        = dcmseries[0].get('AcquisitionDateTime', '')
        dcmdir      = dcmseries[0].get('DicomDir',            '')
        patient     = dcmseries[0].get('PatientName',         '')
        institution = dcmseries[0].get('InstitutionName',     '')

        try:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
            date = '{:4d}-{:2d}-{:2d}'.format(date.year, date.month, date.day)
        except ValueError:
            date = ''

        self.__dcmdirLabel      = wx.StaticText(self)
        self.__dateLabel        = wx.StaticText(self)
        self.__patientLabel     = wx.StaticText(self)
        self.__institutionLabel = wx.StaticText(self)

        self.__dcmdir      = wx.StaticText(self, style=wx.ST_ELLIPSIZE_START)
        self.__date        = wx.StaticText(self)
        self.__patient     = wx.StaticText(self)
        self.__institution = wx.StaticText(self)
        self.__series      = wg.WidgetGrid(self, style=0)

        self.__loadCheckboxes = [wx.CheckBox(self) for s in dcmseries]

        self.__dcmdirLabel     .SetLabel(strings.labels[self, 'dicomdir'])
        self.__dateLabel       .SetLabel(strings.labels[self, 'date'])
        self.__patientLabel    .SetLabel(strings.labels[self, 'patient'])
        self.__institutionLabel.SetLabel(strings.labels[self, 'institution'])
        self.__dcmdir          .SetLabel(dcmdir)
        self.__date            .SetLabel(date)
        self.__patient         .SetLabel(patient)
        self.__institution     .SetLabel(institution)

        self.__mainSizer   = wx.BoxSizer(wx.VERTICAL)
        self.__titleSizer  = wx.FlexGridSizer(2, 5, 5)
        self.__titleSizer.AddGrowableCol(1)

        self.__titleSizer.Add(self.__dcmdirLabel, flag=wx.EXPAND)
        self.__titleSizer.Add(self.__dcmdir, flag=wx.EXPAND)
        self.__titleSizer.Add(self.__dateLabel, flag=wx.EXPAND)
        self.__titleSizer.Add(self.__date, flag=wx.EXPAND)
        self.__titleSizer.Add(self.__patientLabel, flag=wx.EXPAND)
        self.__titleSizer.Add(self.__patient, flag=wx.EXPAND)
        self.__titleSizer.Add(self.__institutionLabel, flag=wx.EXPAND)
        self.__titleSizer.Add(self.__institution, flag=wx.EXPAND)

        self.__mainSizer.Add(self.__titleSizer,
                             flag=wx.EXPAND | wx.ALL,
                             border=5)
        self.__mainSizer.Add(self.__series,
                             flag=wx.EXPAND | wx.ALL,
                             border=5,
                             proportion=1)

        self.SetSizer(self.__mainSizer)

        # columns:
        #   SeriesNumber
        #   SeriesDescription
        #   ReconMatrix
        #   Load (checkbox)
        # TODO For other useful information,
        #      you might need to look in the niftis

        # set up the grid
        self.__series.SetGridSize(len(dcmseries), 4, growCols=(0, 1))
        self.__series.ShowColLabels()
        self.__series.SetColLabel(0, strings.labels[self, 'SeriesNumber'])
        self.__series.SetColLabel(1, strings.labels[self, 'SeriesDescription'])
        self.__series.SetColLabel(2, strings.labels[self, 'Matrix'])
        self.__series.SetColLabel(3, strings.labels[self, 'Load'])

        for i, s in enumerate(dcmseries):

            num  = s['SeriesNumber']
            desc = s['SeriesDescription']
            size = s['ReconMatrixPE']

            self.__series.SetText(  i, 0, str(num))
            self.__series.SetText(  i, 1, desc)
            self.__series.SetText(  i, 2, '{}x{}'.format(size, size))
            self.__series.SetWidget(i, 3, self.__loadCheckboxes[i])

        self.__series.Refresh()


    def IsSelected(self, sidx):
        """Returns ``True`` if the DICOM series at the given index has
        been selected by the user, ``False`` otherwise.
        """
        return self.__loadCheckboxes[sidx].GetValue()
