#!/usr/bin/env python
#
# applyflirtxfm.py - The ApplyFlirtXfmAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ApplyFlirtXfmAction` class, an
:class:`.Action` which allows the user to load a FLIRT transformation
matrix and apply it to an :class:`.Image` overlay.


A number of related standalone classes and functions are also defined in this
module:

   .. autosummary::
      :nosignatures:

      FlirtFileDialog
      promptForFlirtFiles
      guessFlirtFiles
      calculateTransform
"""


import os.path as op

import numpy as np

import wx

import fsl.data.image      as fslimage
import fsl.utils.transform as transform
import fsleyes.strings     as strings
from . import                 base


class ApplyFlirtXfmAction(base.Action):
    """The ``ApplyFlirtXfmAction`` class is an action which allows the user to
    load a FLIRT transformation matrix and apply it to the currently selected
    overlay, if it is an :class:`.Image` instance.


    A :class:`FlirtFileDialog` is used to prompt the user to select a
    transformation matrix and reference image. The :func:`calculateTransform`
    function is used to calculate the source voxel -> reference world
    transformation, and the image ``voxToWorldMat`` is then updated
    accordingly.
    """


    def __init__(self, overlayList, displayCtx, frame):
        """Create an ``ApplyFlirtXfmAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """
        base.Action.__init__(self, self.__applyFlirtXfm)

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__frame       = frame
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        Updates the :attr:`.Action.enabled` state of this action.
        """

        overlay      = self.__displayCtx.getSelectedOverlay()
        self.enabled = isinstance(overlay, fslimage.Image)


    def __applyFlirtXfm(self):
        """Called when this action is executed.
        """

        displayCtx  = self.__displayCtx
        overlayList = self.__overlayList
        overlay     = displayCtx.getSelectedOverlay()

        matFile, refFile = promptForFlirtFiles(
            self.__frame, overlay, overlayList, displayCtx)

        if matFile is None or refFile is None:
            return

        xform = calculateTransform(
            overlay, overlayList, displayCtx, matFile, refFile)

        overlay.voxToWorldMat = xform


def calculateTransform(overlay, overlayList, displayCtx, matFile, refFile):
    """Calculates a source voxel -> reference world transformation matrix
    from the given FLIRT transform and refernece image files.

    See the :func:`fsl.utils.transform.flirtMatrixToSform` function.

    :arg overlay:     The :class:`.Image` overlay - the source image of the
                      FLIRT transformation.

    :arg overlayList: The :class:`.OverlayList`.

    :arg displayCtx:  The :class:`.DisplayContext`.

    :arg matFile:     Path to the FLIRT transformation matrix file.

    :arg refFile:     Path to the FLIRT reference image file.
    """

    # The reference image might
    # already be in the overlay list.
    refImg = overlayList.find(refFile)

    if refImg is None:
        refImg = fslimage.Image(refFile, loadData=False)

    flirtMat = np.loadtxt(matFile)

    return transform.flirtMatrixToSform(flirtMat, overlay, refImg)


def promptForFlirtFiles(parent, overlay, overlayList, displayCtx, save=False):
    """Displays a dialog prompting the user to select a FLIRT
    transformation matrix file and associated reference image for
    the given overlay.

    :arg parent:      The :mod:`wx` parent object.
    :arg overlay:     The overlay to load a FLIRT matrix for.
    :arg overlayList: The :class:`.OverlayList` instance.
    :arg displayCtx:  The :class:`.DisplayContext` instance.
    :arg save:        Prompt the user to save a transformation matrix instead.
    """

    import wx

    if overlay.dataSource is not None:
        matFile, refFile = guessFlirtFiles(overlay.dataSource)
    else:
        matFile, refFile = None, None

    refOptFiles = []
    refOpts     = []
    selectedRef = None

    for ovl in reversed(overlayList):

        if not isinstance(ovl, fslimage.Image): continue

        refOptFiles.append(ovl.dataSource)
        refOpts    .append(displayCtx.getDisplay(ovl).name)

        # If a reference file has been
        # guesed, make sure it is
        # selected in the drop down box
        if refFile is not None and ovl.dataSource == refFile:
            selectedRef = len(refOpts) - 1

    if len(refOpts) == 0:
        refOpts     = None
        refOptFiles = None

    dlg = FlirtFileDialog(parent,
                          overlay.dataSource,
                          refOpts=refOpts,
                          refOptFiles=refOptFiles,
                          selectedRef=selectedRef,
                          matFile=matFile,
                          refFile=refFile,
                          save=save)

    dlg.Layout()
    dlg.Fit()
    dlg.CentreOnParent()

    # TODO A checkbox/dropdown box allowing
    #      the user to load a 'raw' transform,
    #      instead of a FLIRT one?

    if dlg.ShowModal() == wx.ID_OK: return dlg.GetMatFile(), dlg.GetRefFile()
    else:                           return None, None


def guessFlirtFiles(path):
    """Given a ``path`` to a NIFTI image file, tries to guess an appropriate
    FLIRT transformation matrix file and reference image. The guess is based
    on the path location (e.g. if it is a FEAT or MELODIC image).

    Returns a tuple containing paths to the matrix file and reference image,
    or ``(None, None)`` if a guess couldn't be made.
    """

    import fsl.data.featanalysis    as featanalysis
    import fsl.data.melodicanalysis as melodicanalysis

    if path is None:
        return None, None

    filename  = op.basename(path)
    dirname   = op.dirname( path)
    regDir    = None
    srcRefMap = {}

    func2struc = 'example_func2highres.mat'
    struc2std  = 'highres2standard.mat'

    featDir = featanalysis   .getAnalysisDir(dirname)
    melDir  = melodicanalysis.getAnalysisDir(dirname)

    # TODO more heuristics
    if featDir is not None:

        regDir    = op.join(featDir, 'reg')
        srcRefMap = {
            'example_func'            : ('highres',  func2struc),
            'filtered_func_data'      : ('highres',  func2struc),
            'mean_func'               : ('highres',  func2struc),
            'thresh_zstat'            : ('highres',  func2struc),
            op.join('stats', 'zstat') : ('highres',  func2struc),
            op.join('stats', 'tstat') : ('highres',  func2struc),
            op.join('stats', 'cope')  : ('highres',  func2struc),
            op.join('stats', 'pe')    : ('highres',  func2struc),
            'highres'                 : ('standard', struc2std),
            'highres_head'            : ('standard', struc2std),
            'struc'                   : ('standard', struc2std),
            'struct'                  : ('standard', struc2std),
            'struct_brain'            : ('standard', struc2std),
            'struc_brain'             : ('standard', struc2std),
        }

    elif melodicanalysis.isMelodicDir(dirname):

        if melDir.startswith('filtered_func_data'):
            regDir = op.join(melDir, '..', 'reg')
        else:
            regDir = op.join(melDir, 'reg')

        srcRefMap = {
            'filtered_func_data' : ('highres',  func2struc),
            'melodic_IC'         : ('highres',  func2struc),
            'example_func'       : ('highres',  func2struc),
            'mean_func'          : ('highres',  func2struc),
            'highres'            : ('standard', struc2std),
            'highres_head'       : ('standard', struc2std),
            'struc'              : ('standard', struc2std),
            'struct'             : ('standard', struc2std),
            'struct_brain'       : ('standard', struc2std),
            'struc_brain'        : ('standard', struc2std),
        }

    matFile = None
    refFile = None

    for src, (ref, mat) in srcRefMap.items():

        if not filename.startswith(src):
            continue

        mat = op.join(regDir, mat)
        ref = op.join(regDir, ref)

        try:    ref = fslimage.addExt(ref)
        except: continue

        if op.exists(mat):
            matFile = mat
            refFile = ref
            break

    return matFile, refFile


class FlirtFileDialog(wx.Dialog):
    """The ``FlirtFileDialog`` class is a ``wx.Dialog`` which prompts the
    user to select a FLIRT transformation matrix and reference image associated
    with a source image.

    The user can select a reference image either from a drop down box, or
    by selecting a file in the file system.
    """


    def __init__(self,
                 parent,
                 srcFile,
                 refOpts=None,
                 refOptFiles=None,
                 selectedRef=None,
                 matFile=None,
                 refFile=None,
                 save=False):
        """Create a ``FlirtFileDialog``.

        :arg parent:      The ``wx`` parent object.

        :arg srcFile:     Path to the FLIRT source image file

        :arg refOpts:     Options to use in the reference image drop down box.

        :arg refOptFiles: File paths which correspond to the ``refOpts``.

        :arg selectedRef: Index of initially selected ``refOpt``.

        :arg matFile:     Initial path to a FLIRT transformation matrix file

        :arg refFile:     Initial Path to a FLIRT reference image file

        :arg save:        If ``True``, the user will be prompted to save a
                          FLIRT matrix. Otherwise (the default), the user will
                          be prompted to load an existing FLIRT matrix.
        """

        wx.Dialog.__init__(self,
                           parent,
                           style=(wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP))

        if refOpts     is None: refOpts     = []
        if refOptFiles is None: refOptFiles = []
        if selectedRef is None: selectedRef = 0

        self.__srcFile     = srcFile
        self.__refOpts     = list(refOpts)
        self.__refOptFiles = list(refOptFiles)
        self.__matFile     = None
        self.__refFile     = None
        self.__save        = save

        refOpts = list(refOpts) + [strings.labels[self, 'refChoiceSelectFile']]

        overlayName    = wx.StaticText(self, style=wx.ALIGN_CENTRE_HORIZONTAL)
        label          = wx.StaticText(self, style=wx.ALIGN_CENTRE_HORIZONTAL)
        refChoiceLabel = wx.StaticText(self)
        matFileLabel   = wx.StaticText(self)
        refFileLabel   = wx.StaticText(self)
        refChoice      = wx.Choice(self, choices=refOpts)
        matFileText    = wx.TextCtrl(self)
        refFileText    = wx.TextCtrl(self)
        matFileButton  = wx.Button(self)
        refFileButton  = wx.Button(self)
        okButton       = wx.Button(self, wx.ID_OK)
        cancelButton   = wx.Button(self, wx.ID_CANCEL)

        self.__matFileText   = matFileText
        self.__refFileText   = refFileText
        self.__refFileLabel  = refFileLabel
        self.__refFileButton = refFileButton
        self.__refChoice     = refChoice

        srcName = op.basename(srcFile)
        srcName = fslimage.removeExt(srcFile)

        overlayName   .SetLabel(strings.labels[self, 'source'].format(srcName))
        refChoiceLabel.SetLabel(strings.labels[self, 'refFile'])
        matFileLabel  .SetLabel(strings.labels[self, 'matFile'])
        refFileLabel  .SetLabel(strings.labels[self, 'refFile'])
        matFileButton .SetLabel(strings.labels[self, 'selectFile'])
        refFileButton .SetLabel(strings.labels[self, 'selectFile'])
        okButton      .SetLabel(strings.labels[self, 'ok'])
        cancelButton  .SetLabel(strings.labels[self, 'cancel'])
        refChoice     .SetSelection(selectedRef)

        if save: label.SetLabel(strings.labels[self, 'save.message'])
        else:    label.SetLabel(strings.labels[self, 'load.message'])

        if matFile is not None:
            matFileText.SetValue(matFile)
            matFileText.SetInsertionPointEnd()
        if refFile is not None:
            refFileText.SetValue(refFile)
            refFileText.SetInsertionPointEnd()

        sizer       = wx.BoxSizer(wx.VERTICAL)
        widgetSizer = wx.FlexGridSizer(3, 3, 0, 0)
        btnSizer    = wx.BoxSizer(wx.HORIZONTAL)

        widgetSizer.AddGrowableCol(1)

        sizer.Add((1, 10),     flag=wx.EXPAND)
        sizer.Add(overlayName, flag=wx.ALIGN_CENTRE)
        sizer.Add((1, 10),     flag=wx.EXPAND)
        sizer.Add(label,       flag=wx.ALIGN_CENTRE)
        sizer.Add((1, 10),     flag=wx.EXPAND)
        sizer.Add(widgetSizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        sizer.Add((1, 10),     flag=wx.EXPAND)
        sizer.Add(btnSizer,    flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        sizer.Add((1, 10),     flag=wx.EXPAND)

        if refOpts is not None:
            widgetSizer.Add(refChoiceLabel, flag=wx.ALL,    border=3)
            widgetSizer.Add(refChoice,      flag=wx.EXPAND, proportion=1)
            widgetSizer.Add((-1, -1))
        else:
            widgetSizer.Add((-1, -1))
            widgetSizer.Add((-1, -1))
            widgetSizer.Add((-1, -1))

        widgetSizer.Add(refFileLabel,  flag=wx.ALL,    border=3)
        widgetSizer.Add(refFileText,   flag=wx.EXPAND, proportion=1)
        widgetSizer.Add(refFileButton, flag=wx.EXPAND)
        widgetSizer.Add(matFileLabel,  flag=wx.ALL,    border=3)
        widgetSizer.Add(matFileText,   flag=wx.EXPAND, proportion=1)
        widgetSizer.Add(matFileButton, flag=wx.EXPAND)

        btnSizer.Add((10, 1),      flag=wx.EXPAND, proportion=1)
        btnSizer.Add(okButton,     flag=wx.EXPAND)
        btnSizer.Add((10, 1),      flag=wx.EXPAND)
        btnSizer.Add(cancelButton, flag=wx.EXPAND)
        btnSizer.Add((10, 1),      flag=wx.EXPAND, proportion=1)

        matFileText.SetMinSize((400, -1))
        refFileText.SetMinSize((400, -1))

        okButton.SetDefault()
        self.SetSizer(sizer)

        okButton     .Bind(wx.EVT_BUTTON, self.__onOkButton)
        cancelButton .Bind(wx.EVT_BUTTON, self.__onCancelButton)
        matFileButton.Bind(wx.EVT_BUTTON, self.__onMatFileButton)
        refFileButton.Bind(wx.EVT_BUTTON, self.__onRefFileButton)
        refChoice    .Bind(wx.EVT_CHOICE, self.__onRefChoice)

        if len(refOpts) == 1:
            refChoice     .Disable()
            refChoiceLabel.Disable()
        else:
            self.__onRefChoice(None)


    def GetMatFile(self):
        """Returns the current value of the matrix file as a string, or
        ``None``, if the file path is not valid.
        """

        matFile = self.__matFileText.GetValue()

        if self.__save or op.exists(matFile): return op.abspath(matFile)
        else:                                 return None


    def GetRefFile(self):
        """Returns the current value of the reference file, as a string, or
        ``None``, if the file path is not valid.
        """

        choice = self.__refChoice.GetSelection()

        if choice < len(self.__refOpts):
            refFile = self.__refOptFiles[choice]
        else:
            refFile = self.__refFileText.GetValue()

        if op.exists(refFile): return op.abspath(refFile)
        else:                  return None


    def __onOkButton(self, ev):
        """Called when the user clicks the ok button. Closes the dialog.
        """
        self.EndModal(wx.ID_OK)


    def __onCancelButton(self, ev):
        """Called when the user clicks the cancel button. Closes the dialog.
        """
        self.__matFileText.SetValue('')
        self.__refFileText.SetValue('')
        self.EndModal(wx.ID_CANCEL)


    def __onRefChoice(self, ev):
        """Called when the user changes the selection in the reference image
        drop down box. Enables/disables the reference image file selection
        widgets as necessary.
        """

        choice     = self.__refChoice.GetSelection()
        selectFile = choice >= len(self.__refOpts)

        self.__refFileLabel .Enable(selectFile)
        self.__refFileText  .Enable(selectFile)
        self.__refFileButton.Enable(selectFile)


    def __onMatFileButton(self, ev):
        """Called when the user clicks the matrix file select button.
        Displays a file dialog prompting the user to select a matrix file.
        """

        if self.__save: style = wx.FD_SAVE
        else:           style = wx.FD_OPEN

        matFile = self.__matFileText.GetValue().strip()
        if matFile == '':
            dirName  = op.dirname(self.__srcFile)
            fileName = 'xform.mat'
        else:
            dirName, fileName = op.split(matFile)

        dlg = wx.FileDialog(
            self,
            defaultDir=dirName,
            defaultFile=fileName,
            message=strings.messages[self, 'matFile'],
            style=style)

        if dlg.ShowModal() == wx.ID_OK:
            self.__matFileText.SetValue(dlg.GetPath())


    def __onRefFileButton(self, ev):
        """Called when the user clicks the reference file select button.
        Displays a file dialog prompting the user to select a reference file.
        """

        refFile = self.__refFileText.GetValue()
        if refFile == '':
            refFile = self.__srcFile

        dlg = wx.FileDialog(
            self,
            defaultFile=refFile,
            message=strings.messages[self, 'refFile'],
            style=wx.FD_OPEN)

        if dlg.ShowModal() == wx.ID_OK:
            self.__refFileText.SetValue(dlg.GetPath())
