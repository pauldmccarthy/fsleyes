#!/usr/bin/env python
#
# plotcontrolpanel.py - The PlotControlPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PlotControlPanel` class, which is a
*FSLeyes control* panel base-class for use with :class:`.OverlayPlotPanel`
views.
"""


import wx

import fsleyes_props                 as props

import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.tooltips              as fsltooltips
import fsleyes.displaycontext        as fsldisplay
import fsleyes.strings               as strings


class PlotControlPanel(ctrlpanel.SettingsPanel):
    """The ``PlotControlPanel`` is a *FSLeyes control* panel which allows
    the user to control a :class:`.OverlayPlotPanel`. The ``PlotControlPanel``
    may be used as is, or may be sub-classed for more customisation.


    Sub-class implementations may:

      - Override :meth:`generatePlotPanelWidgets` to add to the default group
        of widgets controlling :class:`.PlotPanel` properties.

      - Override :meth:`generateCustomPlotPanelWidgets` to create a new group
        of widgets controlling :class:`.PlotPanel` properties.

      - Override :meth:`generateDataSeriesWidgets` to add to the default group
        of widgets controlling :class:`.DataSeries` properties.

      - Override :meth:`generateDataSeriesWidgets` to create a new group
        of widgets controlling :class:`.DataSeries` properties.


    The first two methods are called by :meth:`__init__`, and the created
    widgets persist for the lifetime of the ``PlotControlPanel``. The last
    two methods are called whenever the
    :class:`.DisplayContext.selectedOverlay` changes, and may also be called
    at other times.


    The following methods are available on a :class:`.PlotControlPanel`:

    .. autosummary::
       :nosignatures:

       getPlotPanel
       getWidgetList
       refreshDataSeriesWidgets
    """


    def __init__(self, parent, overlayList, displayCtx, frame, plotPanel):
        """Create a ``PlotControlPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList`.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame` instance.

        :arg plotPanel:   The :class:`.PlotPanel` associated with this
                          ``PlotControlPanel``.
        """

        ctrlpanel.SettingsPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         kbFocus=True)

        self.__plotPanel = plotPanel

        widgetList = self.getWidgetList()

        widgetList.AddGroup(
            'customPlotSettings',
            strings.labels[self, 'customPlotSettings'])

        widgetList.AddGroup(
            'plotSettings',
            strings.labels[self, 'plotSettings'])

        # A reference to the x/y plot limit widgets
        # is stored here by the generatePlotPanelWidgets
        # method, so they can be enabled/disabled when
        # xAutoScale/yAutoScale changes
        self.__xLimitWidgets = None
        self.__yLimitWidgets = None

        # These lists store the current
        # set of plot/data series widgets
        self.__dsWidgets   = []
        self.__plotWidgets = \
            self.generateCustomPlotPanelWidgets('customPlotSettings') + \
            self.generatePlotPanelWidgets(      'plotSettings')

        # Delete the custom group if
        # nothing has been added to it
        if widgetList.GroupSize('customPlotSettings') == 0:
            widgetList.RemoveGroup('customPlotSettings')

        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)

        plotPanel.addListener('xAutoScale',
                              self.name,
                              self.__autoScaleChanged)
        plotPanel.addListener('yAutoScale',
                              self.name,
                              self.__autoScaleChanged)

        # This attribute keeps track of the currently
        # selected overlay, so the widget list group
        # names can be updated if the overlay name
        # changes.
        self.setNavOrder(self.__plotWidgets)
        self.__selectedOverlay = None
        self.__selectedOverlayChanged()
        self.__autoScaleChanged()


    def destroy(self):
        """Must be called when this ``PlotControlPanel`` is no longer
        needed. Removes some property listeners, and calls the
        :meth:`.SettingsPanel.destroy` method.
        """
        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.overlayList.removeListener('overlays',        self.name)
        self.__plotPanel.removeListener('limits',          self.name)

        self.__plotWidgets = None
        self.__dsWidgets   = None

        if self.__selectedOverlay is not None:
            display = self.displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('name', self.name)

        ctrlpanel.SettingsPanel.destroy(self)


    def getPlotPanel(self):
        """Returns the :class:`.OverlayPlotPanel` associated with this
        ``PlotControlPanel``.
        """
        return self.__plotPanel


    def generateCustomPlotPanelWidgets(self, groupName):
        """May be overridden by sub-classes to add a group of widgets
        controlling :class:`.OverlayPlotPanel` properties.
        The default implementation does nothing.

        :arg groupName: The :class:`.WidgetList` group name.

        :returns: A list of the widgets that were created, and should be
                  included in keyboard navigation (see
                  :meth:`.FSLeyesPanel.setNavOrder`).
        """
        return []


    def generatePlotPanelWidgets(self, groupName):
        """Adds a collection of widgets to the given :class:`.WidgetList`,
        allowing the properties of the given :class:`.PlotPanel` instance
        to be changed.

        This method may be overridden by sub-classes to change/add to the
        list of properties that are added by default.

        :arg groupName: The :class:`.WidgetList` group name.

        :returns: A list of the widgets that were created, and should be
                  included in keyboard navigation (see
                  :meth:`.FSLeyesPanel.setNavOrder`).
        """

        widgetList = self.getWidgetList()
        plotPanel  = self.__plotPanel
        allWidgets = []

        plotProps = ['xLogScale',
                     'yLogScale',
                     'smooth',
                     'legend',
                     'ticks',
                     'grid',
                     'gridColour',
                     'bgColour',
                     'xAutoScale',
                     'yAutoScale']

        for prop in plotProps:
            widget = props.makeWidget(widgetList, plotPanel, prop)
            allWidgets.append(widget)
            widgetList.AddWidget(
                widget,
                displayName=strings.properties[plotPanel, prop],
                tooltip=fsltooltips.properties[plotPanel, prop],
                groupName=groupName)

        limits = props.makeListWidgets(widgetList, plotPanel, 'limits')
        xlims  = wx.BoxSizer(wx.HORIZONTAL)
        ylims  = wx.BoxSizer(wx.HORIZONTAL)

        allWidgets.extend(limits)

        # Store refs to the limit widgets
        # so they can be enabled/disabled
        # when xAutoScale/yAutoScale
        # changes.
        self.__xLimitWidgets = [limits[0], limits[1]]
        self.__yLimitWidgets = [limits[2], limits[3]]

        xlims.Add(limits[0], flag=wx.EXPAND, proportion=1)
        xlims.Add(limits[1], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[2], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[3], flag=wx.EXPAND, proportion=1)

        xlabel = props.makeWidget(widgetList, plotPanel, 'xlabel')
        ylabel = props.makeWidget(widgetList, plotPanel, 'ylabel')
        labels = wx.BoxSizer(wx.HORIZONTAL)

        allWidgets.extend([xlabel, ylabel])

        labels.Add(wx.StaticText(widgetList,
                                 label=strings.labels[self, 'xlabel']))
        labels.Add(xlabel, flag=wx.EXPAND, proportion=1)
        labels.Add(wx.StaticText(widgetList,
                                 label=strings.labels[self, 'ylabel']))
        labels.Add(ylabel, flag=wx.EXPAND, proportion=1)

        widgetList.AddWidget(
            xlims,
            displayName=strings.labels[self, 'xlim'],
            tooltip=fsltooltips.misc[  self, 'xlim'],
            groupName=groupName)
        widgetList.AddWidget(
            ylims,
            displayName=strings.labels[self, 'ylim'],
            tooltip=fsltooltips.misc[  self, 'ylim'],
            groupName=groupName)
        widgetList.AddWidget(
            labels,
            displayName=strings.labels[self, 'labels'],
            tooltip=fsltooltips.misc[  self, 'labels'],
            groupName=groupName)

        return allWidgets


    def refreshDataSeriesWidgets(self):
        """Re-creates all of the widgets controlling properties of the
        current :class:`.DataSeries` instance.
        """

        widgetList = self.getWidgetList()

        if self.__selectedOverlay is not None:
            try:
                display = self.displayCtx.getDisplay(self.__selectedOverlay)
                display.removeListener('name', self.name)

            # The overlay may have been
            # removed from the overlay list
            except fsldisplay.InvalidOverlayError:
                pass

            self.__selectedOverlay = None

        if widgetList.HasGroup('currentDSSettings'):
            widgetList.RemoveGroup('currentDSSettings')
        if widgetList.HasGroup('customDSSettings'):
            widgetList.RemoveGroup('customDSSettings')

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        ds = self.__plotPanel.getDataSeries(overlay)

        if ds is None:
            return

        self.__selectedOverlay = overlay

        display = self.displayCtx.getDisplay(overlay)

        display.addListener('name',
                            self.name,
                            self.__selectedOverlayNameChanged)

        widgetList.AddGroup(
            'currentDSSettings',
            strings.labels[self, 'currentDSSettings'].format(display.name))
        widgetList.AddGroup(
            'customDSSettings',
            strings.labels[self, 'customDSSettings'].format(display.name))

        dsWidgets = \
            self.generateDataSeriesWidgets(      ds, 'currentDSSettings') + \
            self.generateCustomDataSeriesWidgets(ds, 'customDSSettings')

        # Delete the custom group if
        # nothing has been added to it
        if widgetList.GroupSize('customDSSettings') == 0:
            widgetList.RemoveGroup('customDSSettings')

        self.__dsWidgets = dsWidgets

        self.setNavOrder(self.__plotWidgets + self.__dsWidgets)


    def generateDataSeriesWidgets(self, ds, groupName):
        """Adds a collection of widgets to the given :class:`.WidgetList`,
        allowing the properties of the given :class:`.DataSeries` instance
        to be changed. This method may be overridden by sub-classes which
        need to customise the list of widgets.

        :arg ds: The :class:`.DataSeries` instance.
        :arg groupName: The :class:`.WidgetList` group name.

        :returns: A list of the widgets that were created, and should be
                  included in keyboard navigation (see
                  :meth:`.FSLeyesPanel.setNavOrder`).
        """

        widgetList = self.getWidgetList()

        colour    = props.makeWidget(widgetList, ds, 'colour')
        alpha     = props.makeWidget(widgetList, ds, 'alpha',
                                     showLimits=False, spin=False)
        lineWidth = props.makeWidget(widgetList, ds, 'lineWidth')
        lineStyle = props.makeWidget(
            widgetList,
            ds,
            'lineStyle',
            labels=strings.choices[ds, 'lineStyle'])

        widgetList.AddWidget(
            colour,
            displayName=strings.properties[ds, 'colour'],
            tooltip=fsltooltips.properties[ds, 'colour'],
            groupName=groupName)
        widgetList.AddWidget(
            alpha,
            displayName=strings.properties[ds, 'alpha'],
            tooltip=fsltooltips.properties[ds, 'alpha'],
            groupName=groupName)
        widgetList.AddWidget(
            lineWidth,
            displayName=strings.properties[ds, 'lineWidth'],
            tooltip=fsltooltips.properties[ds, 'lineWidth'],
            groupName=groupName)
        widgetList.AddWidget(
            lineStyle,
            displayName=strings.properties[ds, 'lineStyle'],
            tooltip=fsltooltips.properties[ds, 'lineStyle'],
            groupName=groupName)

        return [colour, alpha, lineWidth, lineStyle]


    def generateCustomDataSeriesWidgets(self, ds, groupName):
        """May be overridden by sub-classes to create a group of widgets for
        controlling :class:`.DataSeries` properties. The default
        implementation does nothing.

        :arg ds:        The :class:`.DataSeries` instance.
        :arg groupName: The :class:`.WidgetList` group name.

        :returns: A list of the widgets that were created, and should be
                  included in keyboard navigation (see
                  :meth:`.FSLeyesPanel.setNavOrder`).
        """
        return []


    def __selectedOverlayNameChanged(self, *a):
        """Called when the :attr:`.Display.name` property for the currently
        selected overlay changes. Updates the display name of the
        :class:`.DataSeries` settings sections if necessary.
        """

        widgets = self.getWidgetList()
        display = self.displayCtx.getDisplay(self.__selectedOverlay)

        if widgets.HasGroup('currentDSSettings'):
            widgets.RenameGroup(
                'currentDSSettings',
                strings.labels[self, 'currentDSSettings'].format(display.name))

        if widgets.HasGroup('customDSSettings'):
            widgets.RenameGroup(
                'customDSSettings',
                strings.labels[self, 'customDSSettings'].format(display.name))


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` changes.
        """

        # Double check that the selected overlay has
        # changed before refreshing the panel, as it
        # may not have (e.g. new overlay added, but
        # selected overlay stayed the same).
        if self.displayCtx.getSelectedOverlay() is not self.__selectedOverlay:
            self.refreshDataSeriesWidgets()


    def __autoScaleChanged(self, *a):
        """Called when the :attr:`.PlotPanel.xAutoScale` or
        :attr:`.PlotPanel.yAutoScale` properties change. If widgets have been
        created for the :attr:`.PlotPanel.limits`, they are enabled/disabled
        according to the new ``xAutoScale`` ``yAutoScale`` value.
        """

        if self.__xLimitWidgets is None or self.__yLimitWidgets is None:
            return

        for l in self.__xLimitWidgets:
            l.Enable(not self.__plotPanel.xAutoScale)
        for l in self.__yLimitWidgets:
            l.Enable(not self.__plotPanel.yAutoScale)
