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
import fsleyes.views.plotpanel       as plotpanel
import fsleyes.tooltips              as fsltooltips
import fsleyes.displaycontext        as fsldisplay
import fsleyes.strings               as strings


class PlotControlPanel(ctrlpanel.SettingsPanel):
    """The ``PlotControlPanel`` is a *FSLeyes control* panel which allows
    the user to control a :class:`.OverlayPlotPanel`. The ``PlotControlPanel``
    is intended to be sub-classed.

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


    @staticmethod
    def supportedViews():
        """The ``PlotControlPanel`` is restricted for use with
        :class:`.OverlayPlotPanel` views. This method may be overridden by
        sub-classes.
        """
        return [plotpanel.OverlayPlotPanel]


    @staticmethod
    def ignoreControl():
        """The ``PlotControlPanel`` is not intended to be used directly. """
        return True


    def __init__(self, parent, overlayList, displayCtx, plotPanel):
        """Create a ``PlotControlPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList`.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg plotPanel:   The :class:`.PlotPanel` associated with this
                          ``PlotControlPanel``.
        """

        ctrlpanel.SettingsPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         plotPanel,
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

        plotCanvas = plotPanel.canvas
        plotCanvas.addListener('xAutoScale',
                               self.name,
                               self.__autoScaleChanged)
        plotCanvas.addListener('yAutoScale',
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

        # the plot panel may have already
        # cleared its canvas ref before we
        # get destroyed
        canvas = self.__plotPanel.canvas
        if canvas is not None:
            canvas.removeListener('xAutoScale', self.name)
            canvas.removeListener('yAutoScale', self.name)

        self.__plotPanel   = None
        self.__plotWidgets = None
        self.__dsWidgets   = None

        if self.__selectedOverlay is not None:
            display = self.displayCtx.getDisplay(self.__selectedOverlay)
            display.removeListener('name', self.name)

        ctrlpanel.SettingsPanel.destroy(self)


    @property
    def plotPanel(self):
        """Returns the :class:`.OverlayPlotPanel` associated with this
        ``PlotControlPanel``.
        """
        return self.__plotPanel


    @property
    def plotCanvas(self):
        """Returns the :class:`.PlotCanvas` associated with this
        ``PlotControlPanel``.
        """
        return self.__plotPanel.canvas


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
        plotPanel  = self.plotPanel
        plotCanvas = self.plotCanvas
        allWidgets = []

        plotProps = ['smooth',
                     'legend',
                     'ticks',
                     'grid',
                     'gridColour',
                     'bgColour']

        for prop in plotProps:
            widget = props.makeWidget(widgetList, plotCanvas, prop)
            allWidgets.append(widget)
            widgetList.AddWidget(
                widget,
                displayName=strings.properties[plotCanvas, prop],
                tooltip=fsltooltips.properties[plotCanvas, prop],
                groupName=groupName)

        limits     = props.makeListWidgets(widgetList, plotCanvas, 'limits')
        xlogscale  = props.makeWidget(widgetList, plotCanvas, 'xLogScale')
        ylogscale  = props.makeWidget(widgetList, plotCanvas, 'yLogScale')
        xinvert    = props.makeWidget(widgetList, plotCanvas, 'invertX')
        yinvert    = props.makeWidget(widgetList, plotCanvas, 'invertY')
        xscale     = props.makeWidget(widgetList, plotCanvas, 'xScale')
        yscale     = props.makeWidget(widgetList, plotCanvas, 'yScale')
        xoffset    = props.makeWidget(widgetList, plotCanvas, 'xOffset')
        yoffset    = props.makeWidget(widgetList, plotCanvas, 'yOffset')
        xautoscale = props.makeWidget(widgetList, plotCanvas, 'xAutoScale')
        yautoscale = props.makeWidget(widgetList, plotCanvas, 'yAutoScale')
        xlabel     = props.makeWidget(widgetList, plotCanvas, 'xlabel')
        ylabel     = props.makeWidget(widgetList, plotCanvas, 'ylabel')

        allWidgets.extend(limits)
        allWidgets.extend([xlogscale,
                           ylogscale,
                           xinvert,
                           yinvert,
                           xautoscale,
                           yautoscale,
                           xscale,
                           yscale,
                           xoffset,
                           yoffset,
                           xlabel,
                           ylabel])

        pairs = [('logscale',  xlogscale,  ylogscale),
                 ('invert',    xinvert,    yinvert),
                 ('autoscale', xautoscale, yautoscale),
                 ('scale',     xscale,     yscale),
                 ('offset',    xoffset,    yoffset),
                 ('labels',    xlabel,     ylabel)]

        for key, xwidget, ywidget in pairs:

            sizer = wx.BoxSizer(wx.HORIZONTAL)

            sizer.Add(wx.StaticText(widgetList,
                                    label=strings.labels[self, 'xlabel']))
            sizer.Add(xwidget, flag=wx.EXPAND, proportion=1)
            sizer.Add(wx.StaticText(widgetList,
                                    label=strings.labels[self, 'ylabel']))
            sizer.Add(ywidget, flag=wx.EXPAND, proportion=1)

            widgetList.AddWidget(
                sizer,
                displayName=strings.labels[self, key],
                tooltip=fsltooltips.misc[  self, key],
                groupName=groupName)

        # Store refs to the limit widgets
        # so they can be enabled/disabled
        # when xAutoScale/yAutoScale
        # changes.
        self.__xLimitWidgets = [limits[0], limits[1]]
        self.__yLimitWidgets = [limits[2], limits[3]]

        xlims = wx.BoxSizer(wx.HORIZONTAL)
        ylims = wx.BoxSizer(wx.HORIZONTAL)

        xlims.Add(limits[0], flag=wx.EXPAND, proportion=1)
        xlims.Add(limits[1], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[2], flag=wx.EXPAND, proportion=1)
        ylims.Add(limits[3], flag=wx.EXPAND, proportion=1)

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

        ds = self.plotPanel.getDataSeries(overlay)

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
            l.Enable(not self.plotCanvas.xAutoScale)
        for l in self.__yLimitWidgets:
            l.Enable(not self.plotCanvas.yAutoScale)
