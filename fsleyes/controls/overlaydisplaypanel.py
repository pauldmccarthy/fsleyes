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

import wx

import fsleyes_props                  as props

import fsleyes.strings                as strings
import fsleyes.tooltips               as fsltooltips
import fsleyes.panel                  as fslpanel
import fsleyes.actions.loadcolourmap  as loadcmap
import fsleyes.actions.loadvertexdata as loadvdata
import fsleyes.displaycontext         as displayctx

from . import overlaydisplaywidgets   as odwidgets


log = logging.getLogger(__name__)


class OverlayDisplayPanel(fslpanel.FSLeyesSettingsPanel):
    """The ``OverlayDisplayPanel`` is a :Class:`.FSLeyesPanel` which allows
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
        :class:`.DisplayOpts` sub-classes.


    The settings that are displayed on an ``OverlayDisplayPanel`` are
    defined in the :attr:`_DISPLAY_PROPS` and :attr:`_DISPLAY_WIDGETS`
    dictionaries.
    """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create an ``OverlayDisplayPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        fslpanel.FSLeyesSettingsPanel.__init__(self,
                                               parent,
                                               overlayList,
                                               displayCtx,
                                               frame,
                                               kbFocus=True)

        displayCtx .addListener('selectedOverlay',
                                 self._name,
                                 self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                 self._name,
                                 self.__selectedOverlayChanged)

        self.__viewPanel      = parent
        self.__widgets        = None
        self.__currentOverlay = None

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``OverlayDisplayPanel`` is no longer
        needed. Removes property listeners, and calls the
        :meth:`.FSLeyesPanel.destroy` method.
        """

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:

            display = self._displayCtx.getDisplay(self.__currentOverlay)

            display.removeListener('overlayType', self._name)

        self.__viewPanel      = None
        self.__widgets        = None
        self.__currentOverlay = None

        fslpanel.FSLeyesPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes. Refreshes this
        ``OverlayDisplayPanel`` so that the display settings for the newly
        selected overlay are shown.
        """
        from fsleyes.views.scene3dpanel import Scene3DPanel

        vp          = self.__viewPanel
        overlay     = self._displayCtx.getSelectedOverlay()
        lastOverlay = self.__currentOverlay
        widgetList  = self.getWidgetList()

        if overlay is None:
            self.__currentOverlay = None
            self.__widgets        = None
            widgetList.Clear()
            self.Layout()
            return

        if overlay is lastOverlay:
            return

        self.__currentOverlay = overlay
        self.__widgets        = collections.OrderedDict()

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        if isinstance(vp, Scene3DPanel):
            groups  = ['display', 'opts', '3d']
            targets = [ display,   opts,   opts]
            labels  = [strings.labels[self, display],
                       strings.labels[self, opts],
                       strings.labels[self, '3d']]

        else:
            groups  = ['display', 'opts']
            targets = [ display,   opts]
            labels  = [strings.labels[self, display],
                       strings.labels[self, opts]]

        keepExpanded = {g : True for g in groups}

        if lastOverlay is not None and \
           lastOverlay in self._overlayList:

            lastDisplay = self._displayCtx.getDisplay(lastOverlay)
            lastDisplay.removeListener('overlayType', self._name)

        if lastOverlay is not None:
            for g in groups:
                keepExpanded[g] = widgetList.IsExpanded(g)

        display.addListener('overlayType', self._name, self.__ovlTypeChanged)

        widgetList.Clear()

        for g, l, t in zip(groups, labels, targets):

            widgetList.AddGroup(g, l)
            self.__widgets[g] = self.__updateWidgets(t, g)
            widgetList.Expand(g, keepExpanded[g])

        self.setNavOrder()
        self.Layout()


    def setNavOrder(self):

        allWidgets = self.__widgets.items()
        allWidgets = functools.reduce(lambda a, b: a + b, allWidgets)

        fslpanel.FSLeyesSettingsPanel.setNavOrder(self, allWidgets)


    def __ovlTypeChanged(self, *a):
        """Called when the :attr:`.Display.overlayType` of the current overlay
        changes. Refreshes the :class:`.DisplayOpts` settings which are shown,
        as a new :class:`.DisplayOpts` instance will have been created for the
        overlay.
        """

        opts       = self._displayCtx.getOpts(self.__currentOverlay)
        widgetList = self.getWidgetList()

        self.__widgets[opts] = self.__updateWidgets(opts, 'opts')

        widgetList.RenameGroup('opts', strings.labels[self, opts])

        if '3d' in self.__widgets:
            self.__widgets['3d'] = self.__updateWidgets(opts, '3d')

        self.setNavOrder()
        self.Layout()


    def __updateWidgets(self, target, groupName):
        """Called by the :meth:`__selectedOverlayChanged` and
        :meth:`__ovlTypeChanged` methods. Re-creates the controls on this
        ``OverlayDisplayPanel`` for the specified group.

        :arg target:    A :class:`.Display` or :class:`.DisplayOpts` instance,
                        which contains the properties that controls are to be
                        created for.

        :arg groupName: Either ``'display'`` or ``'opts'``, corresponding
                        to :class:`.Display` or :class:`.DisplayOpts`
                        properties.

        :returns:       A list containing all of the new widgets that
                        were created.
        """

        widgetList = self.getWidgetList()

        widgetList.ClearGroup( groupName)

        if groupName == '3d':
            dispProps = odwidgets.get3DPropertyList(target)
            dispSpecs = odwidgets.get3DWidgetSpecs( target)
        else:
            dispProps = odwidgets.getPropertyList(target)
            dispSpecs = odwidgets.getWidgetSpecs( target)

        dispSpecs = [dispSpecs[p] for p in dispProps]

        labels   = [strings.properties.get((target, p.key), p.key)
                    for p in dispSpecs]
        tooltips = [fsltooltips.properties.get((target, p.key), None)
                    for p in dispSpecs]

        widgets         = []
        returnedWidgets = []

        for s in dispSpecs:

            widget   = props.buildGUI(widgetList, target, s)
            toReturn = [widget]

            # Build a panel for the ColourMapOpts
            # colour map controls.
            if isinstance(target, displayctx.ColourMapOpts):
                if s.key == 'cmap':
                    cmapWidget    = widget
                    widget, extra = self.__buildColourMapWidget(
                        target, cmapWidget)
                    toReturn = [cmapWidget] + list(extra)

            # Special case for VolumeOpts props
            if isinstance(target, displayctx.VolumeOpts):
                if s.key == 'enableOverrideDataRange':
                    enableWidget  = widget
                    widget, extra = self.__buildOverrideDataRangeWidget(
                        target, enableWidget)
                    toReturn = [enableWidget] + list(extra)

            # More special cases for MeshOpts
            elif isinstance(target, displayctx.MeshOpts):
                if s.key == 'vertexData':
                    vdataWidget   = widget
                    widget, extra = self.__buildVertexDataWidget(
                        target, vdataWidget)
                    toReturn = [vdataWidget] + list(extra)

                if s.key == 'lut':
                    lutWidget   = widget
                    widget, extra = self.__buildMeshOptsLutWidget(
                        target, lutWidget)
                    toReturn = [lutWidget] + list(extra)

            returnedWidgets.extend(toReturn)
            widgets        .append(widget)

        for label, tooltip, widget in zip(labels, tooltips, widgets):
            widgetList.AddWidget(
                widget,
                label,
                tooltip=tooltip,
                groupName=groupName)

        self.Layout()

        return returnedWidgets


    def __buildColourMapWidget(self, target, cmapWidget):
        """Builds a panel which contains widgets for controlling the
        :attr:`.VolumeOpts.cmap`, :attr:`.VolumeOpts.negativeCmap`, and
        :attr:`.VolumeOpts.useNegativeCmap`.

        :returns: A ``wx.Sizer`` containing all of the widgets, and a list
                  containing the extra widgets that were added.
        """

        widgets = self.getWidgetList()

        # Button to load a new
        # colour map from file
        loadAction = loadcmap.LoadColourMapAction(self._overlayList,
                                                  self._displayCtx)

        loadButton = wx.Button(widgets)
        loadButton.SetLabel(strings.labels[self, 'loadCmap'])

        loadAction.bindToWidget(self, wx.EVT_BUTTON, loadButton)

        # Negative colour map widget
        negCmap    = odwidgets.getWidgetSpecs(target)['negativeCmap']
        useNegCmap = odwidgets.getWidgetSpecs(target)['useNegativeCmap']

        negCmap    = props.buildGUI(widgets, target, negCmap)
        useNegCmap = props.buildGUI(widgets, target, useNegCmap)

        useNegCmap.SetLabel(strings.properties[target, 'useNegativeCmap'])

        sizer = wx.FlexGridSizer(2, 2, 0, 0)
        sizer.AddGrowableCol(0)

        sizer.Add(cmapWidget, flag=wx.EXPAND)
        sizer.Add(loadButton, flag=wx.EXPAND)
        sizer.Add(negCmap,    flag=wx.EXPAND)
        sizer.Add(useNegCmap, flag=wx.EXPAND)

        return sizer, [negCmap, useNegCmap]


    def __buildVertexDataWidget(self, target, vdataWidget):
        """Builds a panel which contains a widget for controlling the
        :attr:`.MeshOpts.vertexData` property, and also has a button
        which opens a file dialog, allowing the user to select other
        data.
        """
        widgets = self.getWidgetList()

        loadAction = loadvdata.LoadVertexDataAction(self._overlayList,
                                                    self._displayCtx)
        loadButton = wx.Button(widgets)
        loadButton.SetLabel(strings.labels[self, 'loadVertexData'])

        loadAction.bindToWidget(self, wx.EVT_BUTTON, loadButton)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(vdataWidget, flag=wx.EXPAND, proportion=1)
        sizer.Add(loadButton,  flag=wx.EXPAND)

        return sizer, []


    def __buildMeshOptsLutWidget(self, target, lutWidget):
        """Builds a panel which contains the provided :attr:`.MeshOpts.lut`
        widget, and also a widget for :attr:`.MeshOpts.useLut`.
        """
        widgets = self.getWidgetList()

        # enable lut widget
        enableWidget = odwidgets.getWidgetSpecs(target)['useLut']
        enableWidget = props.buildGUI(widgets, target, enableWidget)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(enableWidget,  flag=wx.EXPAND)
        sizer.Add(lutWidget, flag=wx.EXPAND, proportion=1)

        return sizer, [enableWidget]


    def __buildOverrideDataRangeWidget(self, target, enableWidget):
        """Builds a panel which contains widgets for enabling and adjusting
        the :attr:`.VolumeOpts.overrideDataRange`.

        :returns: a ``wx.Sizer`` containing all of the widgets.
        """

        widgets = self.getWidgetList()

        # Override data range widget
        ovrRange = odwidgets.getWidgetSpecs(target)['overrideDataRange']
        ovrRange = props.buildGUI(widgets, target, ovrRange)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(enableWidget, flag=wx.EXPAND)
        sizer.Add(ovrRange,     flag=wx.EXPAND, proportion=1)

        return sizer, [ovrRange]
