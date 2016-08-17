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
})
