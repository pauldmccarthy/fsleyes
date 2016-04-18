#!/usr/bin/env python
#
# timeseriestoolbar.py - The TimeSeriesToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesToolBar`, a toolbar for use with
a :class:`.TimeSeriesPanel`.
"""


import props

import fsleyes.strings  as strings
import fsleyes.tooltips as tooltips

from . import plottoolbar


class TimeSeriesToolBar(plottoolbar.PlotToolBar):
    """The ``TimeSeriesToolBar`` is a toolbar for use with a
    :class:`.TimeSeriesPanel`.
    """

    def __init__(self, parent, overlayList, displayCtx, tsPanel):
        """Create a ``TimeSeriesToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg tsPanel:     The :class:`.TimeSeriesPanel` instance.
        """
        
        plottoolbar.PlotToolBar.__init__(
            self, parent, overlayList, displayCtx, tsPanel)

        mode = props.Widget('plotMode',
                            labels=strings.choices[     tsPanel, 'plotMode'],
                            tooltip=tooltips.properties[tsPanel, 'plotMode'])

        mode = props.buildGUI(self, tsPanel, mode)
        mode = self.MakeLabelledTool(mode,
                                     strings.properties[tsPanel, 'plotMode'])

        self.AddTool(mode)
