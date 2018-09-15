#!/usr/bin/env python
#
# orthotoolbar.py - The OrthoToolBar class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoToolBar` class, which is a
:class:`.ControlToolBar` for use with the :class:`.OrthoPanel`.
"""


import wx

import fsleyes_props    as props

import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.toolbar               as fsltoolbar
import fsleyes.icons                 as fslicons
import fsleyes.tooltips              as fsltooltips
import fsleyes.actions               as actions
import fsleyes.strings               as strings


class OrthoToolBar(ctrlpanel.ControlToolBar):
    """The ``OrthoToolBar`` is a :class:`.ControlToolBar` for use with the
    :class:`.OrthoPanel`. An ``OrthoToolBar`` looks something like this:


    .. image:: images/orthotoolbar.png
       :scale: 50%
       :align: center


    The ``OrthoToolBar`` allows the user to control important parts of the
    :class:`.OrthoPanel` display, and also to display a
    :class:`.CanvasSettingsPanel`, which allows control over all aspects of
    an ``OrthoPanel``.

    The ``OrthoToolBar`` contains controls which modify properties, or run
    actions, defined on the following classes:

    .. autosummary::
       :nosignatures:

       ~fsleyes.views.orthopanel.OrthoPanel
       ~fsleyes.displaycontext.orthoopts.OrthoOpts
       ~fsleyes.profiles.orthoviewprofile.OrthoViewProfile
    """


    showCursorAndLabels = props.Boolean(default=True)
    """This property is linked to a button on the toolbar which allows the
    user to simultaneously toggle the :attr:`.SceneOpts.showCursor` and
    :attr:`.OrthoOpts.showLabels` properties.
    """


    def __init__(self, parent, overlayList, displayCtx, frame, ortho):
        """Create an ``OrthoToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """

        ctrlpanel.ControlToolBar.__init__(self,
                                          parent,
                                          overlayList,
                                          displayCtx,
                                          frame,
                                          height=24,
                                          kbFocus=True)

        self.orthoPanel = ortho

        # The toolbar has buttons bound to some actions
        # on the Profile  instance - when the profile
        # changes (between 'view' and 'edit'), the
        # Profile instance changes too, so we need
        # to re-create these action buttons. I'm being
        # lazy and just re-generating the entire toolbar.
        ortho.addListener('profile', self.name, self.__makeTools)

        self.addListener('showCursorAndLabels',
                         self.name,
                         self.__showCursorAndLabelsChanged)

        self.__makeTools()


    def destroy(self):
        """Must be called when this ``OrthoToolBar`` is no longer in use.
        Removes some property listeners, and calls the base class
        implementation.
        """
        self.orthoPanel.removeListener('profile',             self.name)
        self           .removeListener('showCursorAndLabels', self.name)

        ctrlpanel.ControlToolBar.destroy(self)


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``OrthoToolBar`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        from fsleyes.views.orthopanel import OrthoPanel
        return [OrthoPanel]


    def __makeTools(self, *a):
        """Called by :meth:`__init__`, and whenever the
        :attr:`.ViewPanel.profile` property changes.

        Re-creates all tools shown on this ``OrthoToolBar``.
        """

        ortho     = self.orthoPanel
        orthoOpts = ortho.sceneOpts
        profile   = ortho.getCurrentProfile()

        coronalIcon          = 'coronalSlice24'
        coronalHighlightIcon = 'coronalSliceHighlight24'

        icons = {
            'screenshot'       : fslicons.findImageFile('camera24'),
            'resetDisplay'     : fslicons.findImageFile('resetZoom24'),
            'showCursorAndLabels' : [
                fslicons.findImageFile('addHighlight24'),
                fslicons.findImageFile('add24')],
            'movieMode'        : [
                fslicons.findImageFile('movieHighlight24'),
                fslicons.findImageFile('movie24')],
            'showXCanvas'      : [
                fslicons.findImageFile('sagittalSliceHighlight24'),
                fslicons.findImageFile('sagittalSlice24')],
            'showYCanvas'      : [
                fslicons.findImageFile(coronalHighlightIcon),
                fslicons.findImageFile(coronalIcon)],
            'showZCanvas'      : [
                fslicons.findImageFile('axialSliceHighlight24'),
                fslicons.findImageFile('axialSlice24')],
            'toggleCanvasSettingsPanel' : [
                fslicons.findImageFile('spannerHighlight24'),
                fslicons.findImageFile('spanner24')],

            'layout' : {
                'horizontal' : [
                    fslicons.findImageFile('horizontalLayoutHighlight24'),
                    fslicons.findImageFile('horizontalLayout24')],
                'vertical'   : [
                    fslicons.findImageFile('verticalLayoutHighlight24'),
                    fslicons.findImageFile('verticalLayout24')],
                'grid'       : [
                    fslicons.findImageFile('gridLayoutHighlight24'),
                    fslicons.findImageFile('gridLayout24')]}
        }

        tooltips = {
            'screenshot'   : fsltooltips.actions[   ortho,     'screenshot'],
            'resetDisplay' : fsltooltips.actions[   profile,   'resetDisplay'],
            'movieMode'    : fsltooltips.properties[ortho,     'movieMode'],
            'showCursorAndLabels' : fsltooltips.properties[
                self, 'showCursorAndLabels'],
            'zoom'         : fsltooltips.properties[orthoOpts, 'zoom'],
            'layout'       : fsltooltips.properties[orthoOpts, 'layout'],
            'showXCanvas'  : fsltooltips.properties[orthoOpts, 'showXCanvas'],
            'showYCanvas'  : fsltooltips.properties[orthoOpts, 'showYCanvas'],
            'showZCanvas'  : fsltooltips.properties[orthoOpts, 'showZCanvas'],
            'toggleCanvasSettingsPanel' : fsltooltips.actions[
                ortho, 'toggleCanvasSettingsPanel'],

        }

        targets    = {'screenshot'                : ortho,
                      'movieMode'                 : ortho,
                      'showCursorAndLabels'       : self,
                      'resetDisplay'              : profile,
                      'zoom'                      : orthoOpts,
                      'layout'                    : orthoOpts,
                      'showXCanvas'               : orthoOpts,
                      'showYCanvas'               : orthoOpts,
                      'showZCanvas'               : orthoOpts,
                      'toggleCanvasSettingsPanel' : ortho}


        toolSpecs = [

            actions.ToggleActionButton(
                'toggleCanvasSettingsPanel',
                actionKwargs={'floatPane' : True},
                icon=icons['toggleCanvasSettingsPanel'],
                tooltip=tooltips['toggleCanvasSettingsPanel']),
            actions.ActionButton('screenshot',
                                 icon=icons['screenshot'],
                                 tooltip=tooltips['screenshot']),
            'div',
            props  .Widget(      'showXCanvas',
                                 icon=icons['showXCanvas'],
                                 tooltip=tooltips['showXCanvas']),
            props  .Widget(      'showYCanvas',
                                 icon=icons['showYCanvas'],
                                 tooltip=tooltips['showYCanvas']),
            props  .Widget(      'showZCanvas',
                                 icon=icons['showZCanvas'],
                                 tooltip=tooltips['showZCanvas']),
            'div',
            props  .Widget(      'layout',
                                 icons=icons['layout'],
                                 tooltip=tooltips['layout']),
            'div',
            props  .Widget(      'movieMode',
                                 icon=icons['movieMode'],
                                 tooltip=tooltips['movieMode']),
            props  .Widget(      'showCursorAndLabels',
                                 icon=icons['showCursorAndLabels'],
                                 tooltip=tooltips['showCursorAndLabels']),
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


    def __showCursorAndLabelsChanged(self, *a):
        """Called when the :attr:`showCursorAndLabels` property is changed.
        Propagates the change on to the :attr:`.SceneOpts.showCursor` and
        :attr:`.OrthoOpts.showLabels` properties.
        """

        opts            = self.orthoPanel.sceneOpts
        opts.showCursor = self.showCursorAndLabels
        opts.showLabels = self.showCursorAndLabels
