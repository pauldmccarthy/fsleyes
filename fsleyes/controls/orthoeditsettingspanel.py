#!/usr/bin/env python
#
# orthoeditsettingspanel.py - The OrthoEditSettingsPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoEditSettingsPanel`, a *FSLeyes*
control panel which contains settings to manage an
:class:`.OrthoEditProfile`.
"""


import fsleyes.controls.controlpanel     as ctrlpanel
import fsleyes.profiles.orthoeditprofile as orthoeditprofile
import fsleyes_props                     as props
import fsleyes.strings                   as strings
import fsleyes.tooltips                  as fsltooltips


class OrthoEditSettingsPanel(ctrlpanel.SettingsPanel):
    """The ``OrthoEditSettingsPanel`` is a *FSLeyes* control panel which
    displays widgets allowing the user to adjust properties of an
    :class:`.OrthoEditProfile`.
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``OrthoEditSettingsPanel`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        from fsleyes.views.orthopanel import OrthoPanel
        return [OrthoPanel]


    @staticmethod
    def profileCls():
        """The ``OrthoEditSettingsPanel`` is intended to be activated with the
        :class:`.OrthoEditProfile`.
        """
        return orthoeditprofile.OrthoEditProfile


    @staticmethod
    def ignoreControl():
        """The ``OrthoEditSettingsPanel`` is not intended to be explicitly
        added by the user - it is added a button on the
        :class:`OrthoEditActionToolBar`. Overriding this method tells the
        :class:`.FSLeyesFrame` that it should not be added to the ortho panel
        settings menu.
        """
        return True


    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create an ``OrthoEditSettingsPanel``.

        :arg parent:      The :mod:`wx` parent object
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        ctrlpanel.SettingsPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         ortho,
                                         kbFocus=True)

        self.__ortho = ortho
        self.__makeTools()


    def __makeTools(self):
        """Generates all of the tools and adds them to the :class:`.WidgetList`
        (see :class:`.SettingsPanel`),
        """

        ortho   = self.__ortho
        widgets = self.getWidgetList()
        profile = ortho.currentProfile

        generalProps = [
            props.Widget('mode',
                         labels=strings.choices[profile, 'mode'],
                         fixChoices=['nav', 'sel', 'desel', 'fill', 'selint']),
            props.Widget('drawMode'),
            props.Widget('selectionIs3D'),
            props.Widget('selectionSize',
                         slider=False,
                         spin=True,
                         showLimits=False),
            props.Widget('fillValue',  slider=False, spin=True),
            props.Widget('eraseValue', slider=False, spin=True),

            # 'showSelectionOutline',

            props.Widget('selectionCursorColour'),
            props.Widget('selectionOverlayColour'),
            props.Widget(
                'locationFollowsMouse',
                dependencies=['drawMode'],
                enabledWhen=lambda p, m: not m),
            props.Widget(
                'showSelection',
                dependencies=['drawMode'],
                enabledWhen=lambda p, m: not m)
        ]

        selintProps = [

            props.Widget(
                'localFill',
                dependencies=['mode'],
                enabledWhen=lambda p, m: m == 'selint'),
            props.Widget(
                'limitToRadius',
                dependencies=['mode'],
                enabledWhen=lambda p, m: m == 'selint'),

            props.Widget(
                'intensityThresLimit',
                spin=True,
                slider=False,
                showLimits=False,
                dependencies=['mode'],
                enabledWhen=lambda p, m: m == 'selint'),

            props.Widget(
                'intensityThres',
                spin=True,
                slider=True,
                showLimits=False,
                dependencies=['mode'],
                enabledWhen=lambda p, m: m == 'selint'),

            props.Widget(
                'searchRadius',
                spin=True,
                slider=True,
                showLimits=False,
                dependencies=['mode', 'limitToRadius'],
                enabledWhen=lambda p, m, r: m == 'selint' and r),
        ]

        widgets.AddGroup('general', strings.labels[self, 'general'])
        widgets.AddGroup('selint',  strings.labels[self, 'selint'])

        allWidgets = []

        for spec in generalProps:

            widget = props.buildGUI(widgets, profile, spec)
            allWidgets.append(widget)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[profile, spec.key],
                tooltip=fsltooltips.properties[profile, spec.key],
                groupName='general')

        for spec in selintProps:

            widget = props.buildGUI(widgets, profile, spec)
            allWidgets.append(widget)
            widgets.AddWidget(
                widget,
                displayName=strings.properties[profile, spec.key],
                tooltip=fsltooltips.properties[profile, spec.key],
                groupName='selint')

        self.setNavOrder(allWidgets)
        widgets.Expand('general')
        widgets.Expand('selint')
