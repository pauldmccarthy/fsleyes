#!/usr/bin/env python
#
# powerspectrumtoolbar.py - The PowerSpectrumToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PowerSpectrumToolBar`, a toolbar for use
with a :class:`.PowerSpectrumPanel`.
"""


import fsleyes_props                    as props
import fsleyes.icons                    as icons
import fsleyes.tooltips                 as tooltips
import fsleyes.actions                  as actions
import fsleyes.views.powerspectrumpanel as powerspectrumpanel

from . import plottoolbar


class PowerSpectrumToolBar(plottoolbar.PlotToolBar):
    """The ``PowerSpectrumToolBar`` is a toolbar for use with a
    :class:`.PowerSpectrumPanel`. It extends :class:`.PlotToolBar`,
    and adds a few controls specific to the :class:`.PoweSpectrumPanel`.
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``PowerSpectrumToolBar`` is only intended to be added to
        :class:`.PowerSpectrumPanel` views.
        """
        return [powerspectrumpanel.PowerSpectrumPanel]


    @staticmethod
    def supportSubClasses():
        """Overrides :meth:`.ControlPanel.supportSubClasses`. Returns
        ``False`` - the ``PowerSpectrumToolBar`` is only intended to be
        used with the :class:`.PowerSpectrumPanel`.
        """
        return False


    def __init__(self, parent, overlayList, displayCtx, psPanel):
        """Create a ``PowerSpectrumToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg psPanel:     The :class:`.PowerSpectrumPanel` instance.
        """

        plottoolbar.PlotToolBar.__init__(
            self, parent, overlayList, displayCtx, psPanel)

        togControl = actions.ToggleActionButton(
            'PowerSpectrumControlPanel',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('spannerHighlight24'),
                  icons.findImageFile('spanner24')],
            tooltip=tooltips.actions[psPanel, 'PowerSpectrumControlPanel'])

        togList = actions.ToggleActionButton(
            'PlotListPanel',
            actionKwargs={'floatPane' : True},
            icon=[icons.findImageFile('listHighlight24'),
                  icons.findImageFile('list24')],
            tooltip=tooltips.actions[psPanel, 'PlotListPanel'])

        togControl = props.buildGUI(self, psPanel, togControl)
        togList    = props.buildGUI(self, psPanel, togList)

        self.InsertTools([togControl, togList], 0)

        nav = [togControl, togList] + self.getCommonNavOrder()

        self.setNavOrder(nav)
