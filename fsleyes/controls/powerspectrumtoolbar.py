#!/usr/bin/env python
#
# powerspectrumtoolbar.py - The PowerSpectrumToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PowerSpectrumToolBar`, a toolbar for use
with a :class:`.PowerSpectrumPanel`.
"""


import fsleyes_props    as props

import fsleyes.icons    as icons
import fsleyes.tooltips as tooltips
import fsleyes.actions  as actions


from . import plottoolbar


class PowerSpectrumToolBar(plottoolbar.PlotToolBar):
    """The ``PowerSpectrumToolBar`` is a toolbar for use with a
    :class:`.PowerSpectrumPanel`. It extends :class:`.PlotToolBar`,
    and adds a few controls specific to the :class:`.PoweSpectrumPanel`.
    """

    def __init__(self, parent, overlayList, displayCtx, frame, psPanel):
        """Create a ``PowerSpectrumToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg psPanel:     The :class:`.PowerSpectrumPanel` instance.
        """

        plottoolbar.PlotToolBar.__init__(
            self, parent, overlayList, displayCtx, frame, psPanel)

        togControl = actions.ToggleActionButton(
            'togglePowerSpectrumControl',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('spannerHighlight24'),
                  icons.findImageFile('spanner24')],
            tooltip=tooltips.actions[psPanel, 'togglePowerSpectrumControl'])

        togList = actions.ToggleActionButton(
            'togglePlotList',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('listHighlight24'),
                  icons.findImageFile('list24')],
            tooltip=tooltips.actions[psPanel, 'togglePlotList'])

        togControl = props.buildGUI(self, psPanel, togControl)
        togList    = props.buildGUI(self, psPanel, togList)

        self.InsertTools([togControl, togList], 0)

        nav = [togControl, togList] + self.getCommonNavOrder()

        self.setNavOrder(nav)


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``PowerSpectrumToolBar`` is only intended to be added to
        :class:`.PowerSpectrumPanel` views.
        """
        from fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
        return [PowerSpectrumPanel]
