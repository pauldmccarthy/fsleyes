#!/usr/bin/env python
#
# timeseriestoolbar.py - The TimeSeriesToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TimeSeriesToolBar`, a toolbar for use with
a :class:`.TimeSeriesPanel`.
"""


import fsleyes_props                 as props
import fsleyes.icons                 as icons
import fsleyes.strings               as strings
import fsleyes.tooltips              as tooltips
import fsleyes.actions               as actions
import fsleyes.views.timeseriespanel as timeseriespanel

from . import plottoolbar


class TimeSeriesToolBar(plottoolbar.PlotToolBar):
    """The ``TimeSeriesToolBar`` is a toolbar for use with a
    :class:`.TimeSeriesPanel`. It extends :class:`.PlotToolBar`,
    and adds a few controls specific to the :class:`.TimeSeriesPanel`.
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``TimeSeriesToolBar`` is only intended to be added to
        :class:`.TimeSeriesPanel` views.
        """
        return [timeseriespanel.TimeSeriesPanel]


    def __init__(self, parent, overlayList, displayCtx, tsPanel):
        """Create a ``TimeSeriesToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg tsPanel:     The :class:`.TimeSeriesPanel` instance.
        """

        plottoolbar.PlotToolBar.__init__(
            self, parent, overlayList, displayCtx, tsPanel)

        togControl = actions.ToggleActionButton(
            'TimeSeriesControlPanel',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('spannerHighlight24'),
                  icons.findImageFile('spanner24')],
            tooltip=tooltips.actions[tsPanel, 'TimeSeriesControlPanel'])

        togList = actions.ToggleActionButton(
            'PlotListPanel',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('listHighlight24'),
                  icons.findImageFile('list24')],
            tooltip=tooltips.actions[tsPanel, 'PlotListPanel'])

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
