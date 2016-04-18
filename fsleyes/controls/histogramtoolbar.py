#!/usr/bin/env python
#
# histogramtoolbar.py - The HistogramToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramToolBar`, a toolbar for use with
a :class:`.HistogramPanel`.
"""


import props

import fsleyes.strings  as strings
import fsleyes.tooltips as tooltips

from . import plottoolbar


class HistogramToolBar(plottoolbar.PlotToolBar):
    """The ``HistogramToolBar`` is a toolbar for use with a
    :class:`.HistogramPanel`.
    """

    def __init__(self, parent, overlayList, displayCtx, histPanel):
        """Create a ``HistogramToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg histPanel:   The :class:`.HistogramPanel` instance.
        """
        
        plottoolbar.PlotToolBar.__init__(
            self, parent, overlayList, displayCtx, histPanel)

        mode = props.Widget('histType',
                            labels=strings.choices[     histPanel, 'histType'],
                            tooltip=tooltips.properties[histPanel, 'histType'])

        mode = props.buildGUI(self, histPanel, mode)
        mode = self.MakeLabelledTool(mode,
                                     strings.properties[histPanel, 'histType'])

        self.AddTool(mode)
