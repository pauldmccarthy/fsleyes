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
    # 'LoadStandardAction'       : 'Ctrl-?',
    'CopyOverlayAction'        : 'Ctrl-C',
    'SaveOverlayAction'        : 'Ctrl-S',
    'ReloadOverlayAction'      : 'Ctrl-R',
    'RemoveOverlayAction'      : 'Ctrl-W',

    'FSLEyesFrame.closeFSLeyes'           : 'Ctrl-Q',
    'FSLEyesFrame.openHelp'               : 'Ctrl-H',
    'FSLEyesFrame.removeFocusedViewPanel' : 'Ctrl-X',
    
    'FSLEyesFrame.addOrthoPanel'          : 'Ctrl-1',
    'FSLEyesFrame.addLightBoxPanel'       : 'Ctrl-2',
    'FSLEyesFrame.addTimeSeriesPanel'     : 'Ctrl-3',
    'FSLEyesFrame.addPowerSpectrumPanel'  : 'Ctrl-4',
    'FSLEyesFrame.addHistogramPanel'      : 'Ctrl-5',
    'FSLEyesFrame.addShellPanel'          : 'Ctrl-6',

    # ViewPanel actions must use one
    # of CTRL/ALT or Shift due to
    # hacky things in FSLEyesFrame.

    'CanvasPanel.toggleOverlayList'         : 'Ctrl-Alt-1',
    'CanvasPanel.toggleLocationPanel'       : 'Ctrl-Alt-2',
    'CanvasPanel.toggleOverlayInfo'         : 'Ctrl-Alt-3',
    'CanvasPanel.toggleDisplayPanel'        : 'Ctrl-Alt-4',
    'CanvasPanel.toggleCanvasSettingsPanel' : 'Ctrl-Alt-5',
    'CanvasPanel.toggleAtlasPanel'          : 'Ctrl-Alt-6',

    'CanvasPanel.toggleDisplayToolBar'      : 'Ctrl-Alt-7',
    
    'OrthoPanel.toggleOrthoToolBar'         : 'Ctrl-Alt-8',
    'OrthoPanel.toggleEditMode'             : 'Ctrl-E',

    'LightBoxPanel.toggleLightBoxToolBar'   : 'Ctrl-Alt-8',


    'PlotPanel.toggleOverlayList'         : 'Ctrl-Alt-1',
    'PlotPanel.togglePlotList'            : 'Ctrl-Alt-2',
})
