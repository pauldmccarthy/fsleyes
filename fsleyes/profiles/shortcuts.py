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

    'CanvasPanel.toggleOverlayList'         : 'Ctrl-Alt-1',
    'CanvasPanel.toggleLocationPanel'       : 'Ctrl-Alt-2',
    'CanvasPanel.toggleOverlayInfo'         : 'Ctrl-Alt-3',
    'CanvasPanel.toggleDisplayPanel'        : 'Ctrl-Alt-4',
    'CanvasPanel.toggleCanvasSettingsPanel' : 'Ctrl-Alt-5',
    'CanvasPanel.toggleAtlasPanel'          : 'Ctrl-Alt-6',

    'CanvasPanel.toggleDisplayToolBar'      : 'Ctrl-Alt-7',

    'OrthoPanel.toggleOrthoToolBar'         : 'Ctrl-Alt-8',
    'LightBoxPanel.toggleLightBoxToolBar'   : 'Ctrl-Alt-8',
    'Scene3DPanel.toggleScene3DToolBar'     : 'Ctrl-Alt-8',

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
    'OrthoPanel.pearsonCorrelation'         : 'Alt-I',

    'PlotPanel.toggleOverlayList'         : 'Ctrl-Alt-1',
    'PlotPanel.togglePlotList'            : 'Ctrl-Alt-2',
    'PlotPanel.importDataSeries'          : 'Ctrl-I',
    'PlotPanel.exportDataSeries'          : 'Ctrl-E',

    'TimeSeriesPanel.toggleTimeSeriesToolBar'       : 'Ctrl-Alt-3',
    'TimeSeriesPanel.toggleTimeSeriesControl'       : 'Ctrl-Alt-4',
    'HistogramPanel.toggleHistogramToolBar'         : 'Ctrl-Alt-3',
    'HistogramPanel.toggleHistogramControl'         : 'Ctrl-Alt-4',
    'PowerSpectrumPanel.togglePowerSpectrumToolBar' : 'Ctrl-Alt-3',
    'PowerSpectrumPanel.togglePowerSpectrumControl' : 'Ctrl-Alt-4',

    'OrthoEditProfile.undo'           : 'Ctrl-Z',
    'OrthoEditProfile.redo'           : 'Ctrl-Y',
    'OrthoEditProfile.createMask'     : 'Ctrl-N',
    'OrthoEditProfile.clearSelection' : 'Ctrl-Shift-A',
    'OrthoEditProfile.eraseSelection' : 'Ctrl-E',
    'OrthoEditProfile.fillSelection'  : 'Ctrl-B',
    'OrthoEditProfile.copySelection'  : 'Ctrl-C',
    'OrthoEditProfile.pasteSelection' : 'Ctrl-V',
})
