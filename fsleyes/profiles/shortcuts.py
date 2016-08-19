#!/usr/bin/env python
#
# shortcuts.py - Keyboard shortcuts
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines keyboard shortcuts used throughout FSLeyes.
"""

import fsl.utils.typedict as td


actions = td.TypeDict({
    
    'LoadOverlayAction'        : 'Ctrl-O',
    'LoadOverlayFromDirAction' : 'Ctrl-D',
    'LoadStandardAction'       : 'Ctrl-S',
    'CopyOverlayAction'        : 'Ctrl-Alt-C',
    'SaveOverlayAction'        : 'Ctrl-Alt-S',
    'ReloadOverlayAction'      : 'Ctrl-Alt-R',
    'RemoveOverlayAction'      : 'Ctrl-Alt-W',

    'FSLEyesFrame.closeFSLeyes'           : 'Ctrl-Q',
    'FSLEyesFrame.openHelp'               : 'Ctrl-H',
    'FSLEyesFrame.removeFocusedViewPanel' : 'Ctrl-X',
    
    'FSLEyesFrame.addOrthoPanel'          : 'Ctrl-1',
    'FSLEyesFrame.addLightBoxPanel'       : 'Ctrl-2',
    'FSLEyesFrame.addTimeSeriesPanel'     : 'Ctrl-3',
    'FSLEyesFrame.addHistogramPanel'      : 'Ctrl-4',
    'FSLEyesFrame.addPowerSpectrumPanel'  : 'Ctrl-5',
    'FSLEyesFrame.addShellPanel'          : 'Ctrl-6',
    
    'FSLEyesFrame.selectNextOverlay'       : 'Ctrl-Up',
    'FSLEyesFrame.selectPreviousOverlay'   : 'Ctrl-Down',
    'FSLEyesFrame.toggleOverlayVisibility' : 'Ctrl-Z',
 

    # ViewPanel actions must use one
    # of CTRL, ALT or Shift due to
    # hacky things in FSLEyesFrame.

    'CanvasPanel.toggleOverlayList'         : 'Ctrl-Alt-1',
    'CanvasPanel.toggleLocationPanel'       : 'Ctrl-Alt-2',
    'CanvasPanel.toggleOverlayInfo'         : 'Ctrl-Alt-3',
    'CanvasPanel.toggleDisplayPanel'        : 'Ctrl-Alt-4',
    'CanvasPanel.toggleCanvasSettingsPanel' : 'Ctrl-Alt-5',
    'CanvasPanel.toggleAtlasPanel'          : 'Ctrl-Alt-6',

    'CanvasPanel.toggleDisplayToolBar'      : 'Ctrl-Alt-7',
    
    'OrthoPanel.toggleOrthoToolBar'         : 'Ctrl-Alt-8',

    'CanvasPanel.toggleMovieMode'            : 'Alt-M',
    
    'OrthoPanel.toggleEditMode'             : 'Alt-E',
    'OrthoPanel.resetDisplay'               : 'Alt-R',
    'OrthoPanel.centreCursor'               : 'Alt-P',
    'OrthoPanel.centreCursorWorld'          : 'Alt-O',
    'OrthoPanel.toggleLabels'               : 'Alt-L',
    'OrthoPanel.toggleCursor'               : 'Alt-C',
    'OrthoPanel.toggleXCanvas'              : 'Alt-X',
    'OrthoPanel.toggleYCanvas'              : 'Alt-Y',
    'OrthoPanel.toggleZCanvas'              : 'Alt-Z',

    'LightBoxPanel.toggleLightBoxToolBar'   : 'Ctrl-Alt-8',

    'PlotPanel.toggleOverlayList'         : 'Ctrl-Alt-1',
    'PlotPanel.togglePlotList'            : 'Ctrl-Alt-2',

    'TimeSeriesPanel.toggleTimeSeriesToolBar'       : 'Ctrl-Alt-3',
    'TimeSeriesPanel.toggleTimeSeriesControl'       : 'Ctrl-Alt-4',
    'HistogramPanel.toggleHistogramToolBar'         : 'Ctrl-Alt-3',
    'HistogramPanel.toggleHistogramControl'         : 'Ctrl-Alt-4',
    'PowerSpectrumPanel.togglePowerSpectrumToolBar' : 'Ctrl-Alt-3',
    'PowerSpectrumPanel.togglePowerSpectrumControl' : 'Ctrl-Alt-4', 
})
