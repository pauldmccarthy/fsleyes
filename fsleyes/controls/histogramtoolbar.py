#!/usr/bin/env python
#
# histogramtoolbar.py - The HistogramToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramToolBar`, a toolbar for use with
a :class:`.HistogramPanel`.
"""


import fsleyes_props    as props

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

    def __init__(self, parent, overlayList, displayCtx, frame, histPanel):
        """Create a ``HistogramToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg histPanel:   The :class:`.HistogramPanel` instance.
        """

        plottoolbar.PlotToolBar.__init__(
            self, parent, overlayList, displayCtx, frame, histPanel)

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

        togOverlay = actions.ToggleActionButton(
            'toggleHistogramOverlay',
            icon=[icons.findImageFile('histogramOverlayHighlight24'),
                  icons.findImageFile('histogramOverlay24')])

        mode    = props.Widget(
            'histType',
            labels=strings.choices[     histPanel, 'histType'],
            tooltip=tooltips.properties[histPanel, 'histType'])


        togControl = props.buildGUI(self, histPanel, togControl)
        togList    = props.buildGUI(self, histPanel, togList)
        togOverlay = props.buildGUI(self, histPanel, togOverlay)
        mode       = props.buildGUI(self, histPanel, mode)

        lblMode = self.MakeLabelledTool(
            mode, strings.properties[histPanel, 'histType'])

        self.InsertTools([togControl, togList], 0)
        self.AddTool(togOverlay)
        self.AddTool(lblMode)


        nav = [togControl, togList]    + \
              self.getCommonNavOrder() + \
              [togOverlay, mode]

        self.setNavOrder(nav)


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``HistogramToolBar`` is only intended to be added to
        :class:`.HistogramPanel` views.
        """
        from fsleyes.views.histogrampanel import HistogramPanel
        return [HistogramPanel]
