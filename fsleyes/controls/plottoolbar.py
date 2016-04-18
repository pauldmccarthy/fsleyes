#!/usr/bin/env python
#
# plottoolbar.py - The PlotToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PlotToolBar` class, a toolbar for use with
an :class:`.OverlayPlotPanel`.
"""


import props

import fsleyes.icons    as icons
import fsleyes.actions  as actions
import fsleyes.tooltips as tooltips
import fsleyes.strings  as strings
import fsleyes.toolbar  as fsltoolbar


class PlotToolBar(fsltoolbar.FSLEyesToolBar):
    """The ``PlotToolBar`` is a toolbar for use with an
    :class:`.OverlayPlotPanel`.
    """

    def __init__(self, parent, overlayList, displayCtx, plotPanel):
        """Create a ``PlotToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg plotPanel:   The :class:`.PlotPanel` instance.
        """
        
        fsltoolbar.FSLEyesToolBar.__init__(
            self, parent, overlayList, displayCtx, 24)

        self.__plotPanel = plotPanel

        add        = actions.ActionButton(
            'addDataSeries',
            icon=icons.findImageFile('add24'))
        remove     = actions.ActionButton(
            'removeDataSeries',
            icon=icons.findImageFile('remove24'))
        screenshot = actions.ActionButton(
            'screenshot',
            icon=icons.findImageFile('camera24'),
            tooltip=tooltips.actions[plotPanel, 'screenshot'])
        mode       = props.Widget(
            'showMode',
            labels=strings.choices[     plotPanel, 'showMode'],
            tooltip=tooltips.properties[plotPanel, 'showMode'])

        screenshot = props.buildGUI(self, plotPanel, screenshot)
        add        = props.buildGUI(self, plotPanel, add)
        remove     = props.buildGUI(self, plotPanel, remove)
        mode       = props.buildGUI(self, plotPanel, mode)

        mode = self.MakeLabelledTool(
            mode, strings.properties[plotPanel, 'showMode'])

        self.SetTools([screenshot, add, remove, mode])

        
    def getPlotPanel(self):
        """Returns the :class:`.OverlayPlotPanel` bound to this ``PlotToolBar``.
        """
        return self.__plotPanel
