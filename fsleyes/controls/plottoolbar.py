#!/usr/bin/env python
#
# plottoolbar.py - The PlotToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PlotToolBar` class, a toolbar for use with
an :class:`.OverlayPlotPanel`.
"""


import fsleyes_props    as props

import fsleyes.icons    as icons
import fsleyes.actions  as actions
import fsleyes.tooltips as tooltips
import fsleyes.toolbar  as fsltoolbar


class PlotToolBar(fsltoolbar.FSLeyesToolBar):
    """The ``PlotToolBar`` is a toolbar for use with an
    :class:`.OverlayPlotPanel`. It creates toolbar controls which
    are common to all :class:`.OverlayPlotPanel` types.
    """

    def __init__(self, parent, overlayList, displayCtx, frame, plotPanel):
        """Create a ``PlotToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg plotPanel:   The :class:`.PlotPanel` instance.
        """

        fsltoolbar.FSLeyesToolBar.__init__(self,
                                           parent,
                                           overlayList,
                                           displayCtx,
                                           frame,
                                           height=24,
                                           kbFocus=True)

        self.__plotPanel = plotPanel

        import_     = actions.ActionButton(
            'importDataSeries',
            icon=icons.findImageFile('importDataSeries24'),
            tooltip=tooltips.actions[plotPanel, 'importDataSeries'])
        export      = actions.ActionButton(
            'exportDataSeries',
            icon=icons.findImageFile('exportDataSeries24'),
            tooltip=tooltips.actions[plotPanel, 'exportDataSeries'])
        add        = actions.ActionButton(
            'addDataSeries',
            icon=icons.findImageFile('add24'),
            tooltip=tooltips.actions[plotPanel, 'addDataSeries'])
        remove     = actions.ActionButton(
            'removeDataSeries',
            icon=icons.findImageFile('remove24'),
            tooltip=tooltips.actions[plotPanel, 'removeDataSeries'])
        screenshot = actions.ActionButton(
            'screenshot',
            icon=icons.findImageFile('camera24'),
            tooltip=tooltips.actions[plotPanel, 'screenshot'])

        screenshot = props.buildGUI(self, plotPanel, screenshot)
        import_    = props.buildGUI(self, plotPanel, import_)
        export     = props.buildGUI(self, plotPanel, export)
        add        = props.buildGUI(self, plotPanel, add)
        remove     = props.buildGUI(self, plotPanel, remove)

        self.__commonTools = [screenshot, import_, export, add, remove]
        self.__commonNav   = [screenshot, import_, export, add, remove]

        self.SetTools([screenshot, import_, export, add, remove])


    def destroy(self):
        """Must be called when this ``PlotToolBar`` is no longer needed.
        Clears some references and calls the base class implementation.
        """
        self.__commonTools = None
        self.__commonNav   = None

        fsltoolbar.FSLeyesToolBar.destroy(self)


    def getCommonTools(self):
        """Returns a list containing the toolbar widgets added by this
        ``PlotToolBar``.
        """
        return list(self.__commonTools)


    def getCommonNavOrder(self):
        """Returns a list containing the navigation order for tools added
        by this ``PlotToolBar``.
        """
        return list(self.__commonNav)


    def getPlotPanel(self):
        """Returns the :class:`.OverlayPlotPanel` bound to this ``PlotToolBar``.
        """
        return self.__plotPanel
