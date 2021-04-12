#!/usr/bin/env python
#
# scene3dtoolbar.py - The Scene3DToolBar class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Scene3DToolBar` class, a FSLeyes control
which implements a toolbar for use with the :class:`.Scene3DPanel`.
"""


import wx


import fsleyes_props                 as props
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.views.scene3dpanel    as scene3dpanel
import fsleyes.toolbar               as fsltoolbar
import fsleyes.strings               as strings
import fsleyes.actions               as actions
import fsleyes.icons                 as fslicons
import fsleyes.tooltips              as fsltooltips



class Scene3DToolBar(ctrlpanel.ControlToolBar):
    """The ``Scene3DToolBar`` is a FSLeyes control which implements a toolbar for
    use with the :class:`.Scene3DPanel`.
    """


    showCursorAndLegend = props.Boolean(default=True)
    """This property is linked to a button on the toolbar which allows the
    user to simultaneously toggle the :attr:`.SceneOpts.showCursor` and
    :attr:`.Scene3DOpts.showLegend` properties.
    """


    @staticmethod
    def supportedViews():
        """The ``Scene3DToolBar`` is restricted for use with the
        :class:`.Scene3DPanel`.
        """
        return [scene3dpanel.Scene3DPanel]


    def __init__(self, parent, overlayList, displayCtx, panel):
        """Create a ``Scene3DToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg panel:       The :class:`.Scene3DPanel` instance.
        """

        ctrlpanel.ControlToolBar.__init__(self,
                                          parent,
                                          overlayList,
                                          displayCtx,
                                          panel,
                                          height=24,
                                          kbFocus=True)

        self.panel = panel

        self.addListener('showCursorAndLegend',
                         self.name,
                         self.__showCursorAndLegendChanged)

        self.__makeTools()


    def destroy(self):
        """Must be called when this ``Scene3DToolBar`` is no longer in use.
        Removes some property listeners, and calls the base class
        implementation.
        """
        self.removeListener('showCursorAndLegend', self.name)

        ctrlpanel.ControlToolBar.destroy(self)


    def __makeTools(self):
        """Called by :meth:`__init__`. Creates the toolbar widgets. """

        panel   = self.panel
        opts    = panel.sceneOpts
        profile = panel.currentProfile

        icons = {
            'screenshot'          : fslicons.findImageFile('camera24'),
            'resetDisplay'        : fslicons.findImageFile('resetZoom24'),
            'showCursorAndLegend' : [
                fslicons.findImageFile('addHighlight24'),
                fslicons.findImageFile('add24')],
            'movieMode'        : [
                fslicons.findImageFile('movieHighlight24'),
                fslicons.findImageFile('movie24')],
            'CanvasSettingsPanel' : [
                fslicons.findImageFile('spannerHighlight24'),
                fslicons.findImageFile('spanner24')],
        }

        tooltips = {
            'screenshot'   : fsltooltips.actions[   panel,     'screenshot'],
            'resetDisplay' : fsltooltips.actions[   profile,   'resetDisplay'],
            'movieMode'    : fsltooltips.properties[panel,     'movieMode'],
            'showCursorAndLegend' : fsltooltips.properties[
                self, 'showCursorAndLegend'],
            'zoom'         : fsltooltips.properties[opts, 'zoom'],
            'CanvasSettingsPanel' : fsltooltips.actions[
                panel, 'CanvasSettingsPanel'],
        }

        targets = {
            'screenshot'          : panel,
            'resetDisplay'        : profile,
            'movieMode'           : panel,
            'showCursorAndLegend' : self,
            'zoom'                : opts,
            'CanvasSettingsPanel' : panel,
        }

        toolSpecs = [
            actions.ToggleActionButton(
                'CanvasSettingsPanel',
                actionKwargs={'floatPane' : True},
                icon=icons['CanvasSettingsPanel'],
                tooltip=tooltips['CanvasSettingsPanel']),
            actions.ActionButton('screenshot',
                                 icon=icons['screenshot'],
                                 tooltip=tooltips['screenshot']),
            'div',
            props  .Widget(      'movieMode',
                                 icon=icons['movieMode'],
                                 tooltip=tooltips['movieMode']),
            props  .Widget(      'showCursorAndLegend',
                                 icon=icons['showCursorAndLegend'],
                                 tooltip=tooltips['showCursorAndLegend']),
            actions.ActionButton('resetDisplay',
                                 icon=icons['resetDisplay'],
                                 tooltip=tooltips['resetDisplay']),
            props.Widget(        'zoom',
                                 spin=True,
                                 slider=True,
                                 showLimits=False,
                                 spinWidth=5,
                                 tooltip=tooltips['zoom']),
        ]

        tools = []
        nav   = []

        for spec in toolSpecs:

            if spec == 'div':
                tools.append(fsltoolbar.ToolBarDivider(self,
                                                       height=24,
                                                       orient=wx.VERTICAL))
                continue

            widget    = props.buildGUI(self, targets[spec.key], spec)
            navWidget = widget

            if spec.key in ('zoom', ):
                widget = self.MakeLabelledTool(
                    widget,
                    strings.properties[targets[spec.key], spec.key])

            tools.append(widget)
            nav  .append(navWidget)

        self.SetTools(tools, destroy=True)
        self.setNavOrder(nav)


    def __showCursorAndLegendChanged(self, *a):
        """Called when the :attr:`showCursorAndLegend` property is changed.
        Propagates the change on to the :attr:`.Scene3DOpts.showCursor` and
        :attr:`.Scene3DOpts.showLegend` properties.
        """

        opts            = self.panel.sceneOpts
        opts.showCursor = self.showCursorAndLegend
        opts.showLegend = self.showCursorAndLegend
