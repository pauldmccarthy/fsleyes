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

import fsleyes.icons    as icons
import fsleyes.strings  as strings
import fsleyes.tooltips as tooltips
import fsleyes.actions  as actions


from . import plottoolbar


class HistogramToolBar(plottoolbar.PlotToolBar):
    """The ``HistogramToolBar`` is a toolbar for use with a
    :class:`.HistogramPanel`. It extends :class:`.PlotToolBar`,
    and adds a few controls specific to the :class:`.HistogramPanel`.
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


        togControl = actions.ToggleActionButton(
            'toggleHistogramControl',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('spannerHighlight24'),
                  icons.findImageFile('spanner24')],
            tooltip=tooltips.actions[histPanel, 'toggleHistogramControl'])
 
        togList = actions.ToggleActionButton(
            'togglePlotList',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('listHighlight24'),
                  icons.findImageFile('list24')],
            tooltip=tooltips.actions[histPanel, 'togglePlotList']) 
 
        mode = props.Widget('histType',
                            labels=strings.choices[     histPanel, 'histType'],
                            tooltip=tooltips.properties[histPanel, 'histType'])

        togControl = props.buildGUI(self, histPanel, togControl)
        togList    = props.buildGUI(self, histPanel, togList)
        mode       = props.buildGUI(self, histPanel, mode)
        
        mode = self.MakeLabelledTool(mode,
                                     strings.properties[histPanel, 'histType'])

        self.InsertTools([togControl, togList], 0) 
        self.AddTool(mode)
