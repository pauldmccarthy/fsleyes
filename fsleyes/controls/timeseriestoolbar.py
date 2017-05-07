#!/usr/bin/env python
#
# timeseriestoolbar.py - The TimeSeriesToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesToolBar`, a toolbar for use with
a :class:`.TimeSeriesPanel`.
"""


import fsleyes_props    as props

import fsleyes.icons    as icons
import fsleyes.strings  as strings
import fsleyes.tooltips as tooltips
import fsleyes.actions  as actions

from . import plottoolbar


class TimeSeriesToolBar(plottoolbar.PlotToolBar):
    """The ``TimeSeriesToolBar`` is a toolbar for use with a
    :class:`.TimeSeriesPanel`. It extends :class:`.PlotToolBar`,
    and adds a few controls specific to the :class:`.TimeSeriesPanel`.
    """

    def __init__(self, parent, overlayList, displayCtx, frame, tsPanel):
        """Create a ``TimeSeriesToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg tsPanel:     The :class:`.TimeSeriesPanel` instance.
        """

        plottoolbar.PlotToolBar.__init__(
            self, parent, overlayList, displayCtx, frame, tsPanel)

        togControl = actions.ToggleActionButton(
            'toggleTimeSeriesControl',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('spannerHighlight24'),
                  icons.findImageFile('spanner24')],
            tooltip=tooltips.actions[tsPanel, 'toggleTimeSeriesControl'])

        togList = actions.ToggleActionButton(
            'togglePlotList',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('listHighlight24'),
                  icons.findImageFile('list24')],
            tooltip=tooltips.actions[tsPanel, 'togglePlotList'])

        mode = props.Widget('plotMode',
                            labels=strings.choices[     tsPanel, 'plotMode'],
                            tooltip=tooltips.properties[tsPanel, 'plotMode'])

        togControl = props.buildGUI(self, tsPanel, togControl)
        togList    = props.buildGUI(self, tsPanel, togList)
        mode       = props.buildGUI(self, tsPanel, mode)

        lblMode = self.MakeLabelledTool(
            mode, strings.properties[tsPanel, 'plotMode'])

        self.InsertTools([togControl, togList], 0)
        self.AddTool(lblMode)

        nav = [togControl, togList] + self.getCommonNavOrder() + [mode]
        self.setNavOrder(nav)
