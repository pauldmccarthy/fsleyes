#!/usr/bin/env python
#
# overlaydisplaypanel.py - The OverlayDisplayPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""This module provides the :class:`OverlayDisplayPanel` class, a *FSLeyes
control* panel which allows the user to change overlay display settings.
"""


import logging
import functools
import collections
import collections.abc as abc

import wx

import fsleyes_props                  as props
import fsleyes.views.canvaspanel      as canvaspanel
import fsleyes.controls.controlpanel  as ctrlpanel
import fsleyes.strings                as strings
import fsleyes.tooltips               as fsltooltips

from . import overlaydisplaywidgets   as odw


log = logging.getLogger(__name__)


class OverlayDisplayPanel(ctrlpanel.SettingsPanel):
    """The ``OverlayDisplayPanel`` is a :class:`.SettingsPanel` which allows
    the user to change the display settings of the currently selected
    overlay (which is defined by the :attr:`.DisplayContext.selectedOverlay`
    property). The display settings for an overlay are contained in the
    :class:`.Display` and :class:`.DisplayOpts` instances associated with
    that overlay. An ``OverlayDisplayPanel`` looks something like the
    following:

    .. image:: images/overlaydisplaypanel.png
       :scale: 50%
       :align: center

    An ``OverlayDisplayPanel`` uses a :class:`.WidgetList` to organise the
    settings into two main sections:

      - Settings which are common across all overlays - these are defined
        in the :class:`.Display` class.

      - Settings which are specific to the current
        :attr:`.Display.overlayType` - these are defined in the
        :class:`.DisplayOpts` sub-classes, and may be split across multiple
        sections.

    The settings that are displayed on an ``OverlayDisplayPanel`` are
    defined in the :mod:`.overlaydisplaywidgets` module.
    """


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``OverlayDisplayPanel`` is only intended to be added to
        :class:`.OrthoPanel`, :class:`.LightBoxPanel`, or
        :class:`.Scene3DPanel` views.
        """
        return [canvaspanel.CanvasPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.LEFT}


    def __init__(self, parent, overlayList, displayCtx, canvasPanel):
        """Create an ``OverlayDisplayPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg canvasPanel: The :class:`.CanvasPanel` instance.
        """

        from fsleyes.views.scene3dpanel import Scene3DPanel

        ctrlpanel.SettingsPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         canvasPanel,
                                         kbFocus=True)

        displayCtx .addListener('selectedOverlay',
                                 self.name,
                                 self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                 self.name,
                                 self.__selectedOverlayChanged)

        self.__threedee       = isinstance(parent, Scene3DPanel)
        self.__widgets        = None
        self.__currentOverlay = None

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``OverlayDisplayPanel`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.SettingsPanel.destroy` method.
        """

        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.overlayList.removeListener('overlays',        self.name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self.overlayList:

            display = self.displayCtx.getDisplay(self.__currentOverlay)

            display.removeListener('overlayType', self.name)

        self.__widgets        = None
        self.__currentOverlay = None

        ctrlpanel.SettingsPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes. Refreshes this
        ``OverlayDisplayPanel`` so that the display settings for the newly
        selected overlay are shown.
        """

        overlay     = self.displayCtx.getSelectedOverlay()
        lastOverlay = self.__currentOverlay
        widgetList  = self.getWidgetList()

        if overlay is None:
            self.__currentOverlay = None
            self.__widgets        = None
            widgetList.Clear()
            self.Layout()
            return

        self.__currentOverlay = overlay
        self.__widgets        = collections.OrderedDict()

        display = self.displayCtx.getDisplay(overlay)
        opts    = display.opts

        optgroups =  list(odw.getPropertyList(opts, self.__threedee).keys())
        groups     = ['display'] + optgroups
        targets    = [display] + [opts] * len(optgroups)
        labels     = [strings.labels[self, display]] + \
                     [strings.labels[self, opts, grp] for grp in optgroups]

        # Initial expanded state of each widget group
        keepExpanded = {g : False for g in groups}
        keepExpanded['display'] = True
        for grp in odw.EXPANDED_GROUPS[opts]:
            keepExpanded[grp] = True

        if lastOverlay is not None and lastOverlay in self.overlayList:

            lastDisplay = self.displayCtx.getDisplay(lastOverlay)
            lastDisplay.removeListener('overlayType', self.name)

        # Preserve expanded state if changing
        # between similar overlay types
        if lastOverlay is not None:
            for g in groups:
                if widgetList.HasGroup(g):
                    keepExpanded[g] = widgetList.IsExpanded(g)

        display.addListener('overlayType',
                            self.name,
                            self.__selectedOverlayChanged)

        widgetList.Clear()

        for grp, lbl, tgt in zip(groups, labels, targets):

            widgetList.AddGroup(grp, lbl)
            self.__widgets[grp] = self.__updateWidgets(tgt, grp)
            widgetList.Expand(grp, keepExpanded[grp])

        self.setNavOrder()
        self.Layout()


    def setNavOrder(self):

        allWidgets = self.__widgets.items()
        allWidgets = functools.reduce(lambda a, b: a + b, allWidgets)

        ctrlpanel.SettingsPanel.setNavOrder(self, allWidgets)


    def updateWidgets(self, target, groupName):
        """Re-generates the widgets for the given target/group. """

        self.__widgets[target] = self.__updateWidgets(target, groupName)
        self.setNavOrder()
        self.Layout()


    def __updateWidgets(self, target, groupName):
        """Called by the :meth:`__selectedOverlayChanged` and
        :meth:`__ovlTypeChanged` methods. Re-creates the controls on this
        ``OverlayDisplayPanel`` for the specified group.

        :arg target:    A :class:`.Display` or :class:`.DisplayOpts` instance,
                        which contains the properties that controls are to be
                        created for.

        :arg groupName: Name of the widget group to update - see the
                        individual ``_initPropertyList`` functions in
                        :mod:`.overlaydisplaywidgets`

        :returns:       A list containing all of the new widgets that
                        were created.
        """

        widgetList = self.getWidgetList()

        widgetList.ClearGroup(groupName)

        dispProps = odw.getPropertyList(target, self.__threedee)[groupName]
        dispSpecs = odw.getWidgetSpecs( target, self.displayCtx)

        allLabels     = []
        allTooltips   = []
        allWidgets    = []
        allContainers = []

        for p in dispProps:

            spec  = dispSpecs[p]

            specs    = [spec]
            labels   = [strings    .properties.get((target, p), None)]
            tooltips = [fsltooltips.properties.get((target, p), None)]

            if callable(spec):

                # Will either return a contsiner
                # widget/sizer and a list of widgets
                # for setting the navigation order,
                # or will return a list of specs
                # (with an irrelevant second parameter)
                container, widgets = spec(
                    target,
                    widgetList,
                    self,
                    self.overlayList,
                    self.displayCtx)

                if isinstance(container, abc.Sequence):
                    specs    = container
                    keys     = [s.key for s in specs]
                    labels   = [strings.properties.get((target, k), None)
                                for k in keys]
                    tooltips = [fsltooltips.properties.get((target, k), None)
                                for k in keys]

                else:
                    allContainers.append(container)
                    allWidgets   .extend(widgets)
                    specs = []

            for s in specs:
                widget = props.buildGUI(widgetList, target, s)

                allWidgets   .append(widget)
                allContainers.append(widget)

            allLabels  .extend(labels)
            allTooltips.extend(tooltips)

        for widget, label, tooltip in zip(allContainers,
                                          allLabels,
                                          allTooltips):
            if label is None:
                label = ''
            widgetList.AddWidget(
                widget,
                label,
                tooltip=tooltip,
                groupName=groupName)

        return allWidgets
