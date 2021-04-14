#!/usr/bin/env python
#
# shortcuts.py - Keyboard shortcuts
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines keyboard shortcuts used throughout FSLeyes.
"""


import fsleyes_widgets.utils.typedict as td


actions = td.TypeDict({

    'LoadOverlayAction'        : 'Ctrl-O',
    'LoadOverlayFromDirAction' : 'Ctrl-D',
    'LoadStandardAction'       : 'Ctrl-S',
    'NewImageAction'           : 'Ctrl-Shift-N',
    'CopyOverlayAction'        : 'Ctrl-Shift-C',
    'SaveOverlayAction'        : 'Ctrl-Shift-S',
    'ReloadOverlayAction'      : 'Ctrl-Shift-R',
    'RemoveOverlayAction'      : 'Ctrl-Shift-W',

    'FSLeyesFrame.closeFSLeyes'           : 'Ctrl-Q',
    'FSLeyesFrame.openHelp'               : 'Ctrl-?',

    'FSLeyesFrame.layouts.default'        : 'Ctrl-Shift-D',

    'FSLeyesFrame.addOrthoPanel'          : 'Ctrl-1',
    'FSLeyesFrame.addLightBoxPanel'       : 'Ctrl-2',
    'FSLeyesFrame.addTimeSeriesPanel'     : 'Ctrl-3',
    'FSLeyesFrame.addHistogramPanel'      : 'Ctrl-4',
    'FSLeyesFrame.addPowerSpectrumPanel'  : 'Ctrl-5',
    'FSLeyesFrame.addScene3DPanel'        : 'Ctrl-6',
    'FSLeyesFrame.addShellPanel'          : 'Ctrl-7',

    'FSLeyesFrame.selectNextOverlay'       : 'Ctrl-Up',
    'FSLeyesFrame.selectPreviousOverlay'   : 'Ctrl-Down',
    'FSLeyesFrame.toggleOverlayVisibility' : 'Ctrl-F',

    # Shortcuts for next/prev volume

    # ViewPanel actions must use one
    # of CTRL, ALT or Shift due to
    # hacky things in FSLeyesFrame
    # (see __onViewPanelMenuItem)

    'ViewPanel.removeFromFrame'             : 'Ctrl-W',
    'ViewPanel.removeAllPanels'             : 'Ctrl-Alt-X',

    'CanvasPanel.OverlayListPanel'          : 'Ctrl-Alt-1',
    'CanvasPanel.LocationPanel'             : 'Ctrl-Alt-2',
    'CanvasPanel.OverlayDisplayPanel'       : 'Ctrl-Alt-4',
    'CanvasPanel.CanvasSettingsPanel'       : 'Ctrl-Alt-5',

    'CanvasPanel.OverlayDisplayToolBar'     : 'Ctrl-Alt-7',

    'OrthoPanel.OrthoToolBar'               : 'Ctrl-Alt-8',
    'LightBoxPanel.LightBoxToolBar'         : 'Ctrl-Alt-8',
    'Scene3DPanel.Scene3DToolBar'           : 'Ctrl-Alt-8',

    'CanvasPanel.OverlayInfoPanel'          : 'Ctrl-Alt-3',
    'CanvasPanel.AtlasPanel'                : 'Ctrl-Alt-6',
    'CanvasPanel.FileTreePanel'             : 'Ctrl-Alt-9',


    'OrthoPanel.AnnotationPanel'            : 'Ctrl-Alt-A',

    'CanvasPanel.toggleMovieMode'           : 'Alt-M',
    'CanvasPanel.toggleDisplaySync'         : 'Alt-S',

    'OrthoPanel.toggleEditMode'             : 'Alt-E',
    'OrthoPanel.resetDisplay'               : 'Alt-R',
    'OrthoPanel.centreCursor'               : 'Alt-P',
    'OrthoPanel.centreCursorWorld'          : 'Alt-O',
    'OrthoPanel.toggleLabels'               : 'Alt-L',
    'OrthoPanel.toggleCursor'               : 'Alt-C',
    'OrthoPanel.toggleXCanvas'              : 'Alt-X',
    'OrthoPanel.toggleYCanvas'              : 'Alt-Y',
    'OrthoPanel.toggleZCanvas'              : 'Alt-Z',

    'OrthoPanel.PearsonCorrelateAction'     : 'Alt-I',

    'PlotPanel.OverlayListPanel'          : 'Ctrl-Alt-1',
    'PlotPanel.PlotListPanel'             : 'Ctrl-Alt-2',
    'PlotPanel.importDataSeries'          : 'Ctrl-I',
    'PlotPanel.exportDataSeries'          : 'Ctrl-E',

    'TimeSeriesPanel.TimeSeriesToolBar'            : 'Ctrl-Alt-3',
    'TimeSeriesPanel.TimeSeriesControlPanel'       : 'Ctrl-Alt-4',
    'HistogramPanel.HistogramToolBar'              : 'Ctrl-Alt-3',
    'HistogramPanel.HistogramControlPanel'         : 'Ctrl-Alt-4',
    'PowerSpectrumPanel.PowerSpectrumToolBar'      : 'Ctrl-Alt-3',
    'PowerSpectrumPanel.PowerSpectrumControlPanel' : 'Ctrl-Alt-4',

    'OrthoEditProfile.undo'               : 'Ctrl-Z',
    'OrthoEditProfile.redo'               : 'Ctrl-Y',
    'OrthoEditProfile.createMask'         : 'Ctrl-N',
    'OrthoEditProfile.clearSelection'     : 'Ctrl-Shift-A',
    'OrthoEditProfile.fillSelection'      : 'Ctrl-B',
    'OrthoEditProfile.eraseSelection'     : 'Ctrl-E',
    'OrthoEditProfile.invertSelection'    : 'Ctrl-I',
    'OrthoEditProfile.copyPasteData'      : 'Ctrl-C',
    'OrthoEditProfile.copyPasteSelection' : 'Ctrl-P',
})
