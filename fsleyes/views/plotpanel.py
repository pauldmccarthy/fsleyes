#!/usr/bin/env python
#
# plotpanel.py - The PlotPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`PlotPanel` and :class:`.OverlayPlotPanel`
classes.  The ``PlotPanel`` class is the base class for all *FSLeyes views*
which display some sort of data plot. The ``OverlayPlotPanel`` is a
``PlotPanel`` which contains some extra logic for displaying plots related to
the currently selected overlay.

The actual plotting logic (using ``matplotilb``) is implemented within the
:class:`.PlotCanvas` class.
"""


import logging

import wx

import fsleyes_widgets.elistbox           as elistbox

import fsleyes.actions                    as actions
import fsleyes.overlay                    as fsloverlay
import fsleyes.colourmaps                 as fslcm
import fsleyes.views.viewpanel            as viewpanel
import fsleyes.plotting                   as plotting
import fsleyes.plotting.plotcanvas        as plotcanvas
import fsleyes.controls.overlaylistpanel  as overlaylistpanel



log = logging.getLogger(__name__)


class PlotPanel(viewpanel.ViewPanel):
    """The ``PlotPanel`` class is the base class for all *FSLeyes views*
    which display some sort of 2D data plot, such as the
    :class:`.TimeSeriesPanel`, and the :class:`.HistogramPanel`.

    .. note:: See also the :class:`OverlayPlotPanel`, which contains extra
              logic for displaying plots related to the currently selected
              overlay, and which is the actual base class used by the
              ``TimeSeriesPanel``, ``HistogramPanel`` and
              ``PowerSpectrumPanel``.


    ``PlotPanel`` uses a :class:`.PlotCanvas`, which in turn uses
    :mod`:matplotlib` for its plotting.  The ``PlotCanvas`` instance used by a
    ``PlotPanel`` can be accessed via the :meth:`canvas` method, which in turn
    can be used to manipulate the plot display settings. The ``matplotlib``
    ``Figure``, ``Axis``, and ``Canvas`` instances can be accessed via the
    ``PlotCanvas`` instance, if they are needed.


    **Sub-class requirements**

    Sub-class implementations of ``PlotPanel`` must do the following:

      1. Call the ``PlotPanel`` constructor.

      2. Define one or more :class:`.DataSeries` sub-classes if needed.

      3. Override the :meth:`draw` method, so it calls the
         :meth:`.PlotCanvas.drawDataSeries` and
         :meth:`.PlotCanvas.drawArtists` methods (:meth:`draw` is passed
         to the ``PlotCanvas`` as a custom ``drawFunc``).

      4. If necessary, override the :meth:`prepareDataSeries` method to
         perform any preprocessing on ``extraSeries`` passed to the
         :meth:`drawDataSeries` method (but not applied to
         :class:`.DataSeries` that have been added to the :attr:`dataSeries`
         list) (:meth:`prepareDataSeries` is passed
         to the ``PlotCanvas`` as a custom ``prepareFunc``).

      5. If necessary, override the :meth:`destroy` method, but make
         sure that the base-class implementation is called.

    **Plot panel actions**

    A number of :mod:`actions` are also provided by the ``PlotPanel`` class:

    .. autosummary::
       :nosignatures:

       screenshot
       importDataSeries
       exportDataSeries
    """


    def controlOptions(self, cpType):
        """Returns some options to be used by :meth:`.ViewPanel.togglePanel`
        for certain control panel types.
        """
        # Tell the overlay list panel to disable
        # all overlays that aren't being plotted.
        #
        # This OverlayPlotPanel will always be
        # notified about a new overlay before
        # this OverlayListPanel, so a DataSeries
        # instance will always have been created
        # by the time the list panel calls this
        # filter function.
        def listFilter(overlay):
            return self.getDataSeries(overlay) is not None

        if cpType is overlaylistpanel.OverlayListPanel:
            return dict(showVis=True,
                        showSave=False,
                        showGroup=False,
                        propagateSelect=True,
                        elistboxStyle=(elistbox.ELB_REVERSE      |
                                       elistbox.ELB_TOOLTIP_DOWN |
                                       elistbox.ELB_NO_ADD       |
                                       elistbox.ELB_NO_REMOVE    |
                                       elistbox.ELB_NO_MOVE),
                        location=wx.LEFT,
                        filterFunc=listFilter)


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 frame):
        """Create a ``PlotPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """

        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, frame)
        self.__canvas = plotcanvas.PlotCanvas(
            self, self.draw, self.prepareDataSeries)
        self.centrePanel = self.__canvas.canvas


    def destroy(self):
        """Removes some property listeners, and then calls
        :meth:`.ViewPanel.destroy`.
        """
        self.__canvas.destroy()
        self.__canvas = None
        viewpanel.ViewPanel.destroy(self)


    @property
    def canvas(self):
        """Returns a reference to the :class:`.PlotCanvas`. """
        return self.__canvas


    def draw(self, *a):
        """This method must be overridden by ``PlotPanel`` sub-classes.
        Sub-class implementations should call the :meth:`drawDataSeries`
        and meth:`drawArtists` methods.
        """
        raise NotImplementedError()


    def prepareDataSeries(self, ds):
        """Prepares the data from the given :class:`.DataSeries` so it is
        ready to be plotted. Called by the :meth:`__drawOneDataSeries` method
        for any ``extraSeries`` passed to the :meth:`drawDataSeries` method
        (but not applied to :class:`.DataSeries` that have been added to the
        :attr:`dataSeries` list).

        This implementation just returns :class:`.DataSeries.getData` -
        override it to perform any custom preprocessing.
        """
        return ds.getData()


    @actions.action
    def screenshot(self, *a):
        """Prompts the user to select a file name, then saves a screenshot
        of the current plot.

        See the :class:`.ScreenshotAction`.
        """
        from fsleyes.actions.screenshot import ScreenshotAction
        ScreenshotAction(self.overlayList, self.displayCtx, self)()


    @actions.action
    def importDataSeries(self, *a):
        """Imports data series from a text file.

        See the :class:`.ImportDataSeriesAction`.
        """
        from fsleyes.actions.importdataseries import ImportDataSeriesAction
        ImportDataSeriesAction(self.overlayList, self.displayCtx, self)()


    @actions.action
    def exportDataSeries(self, *args, **kwargs):
        """Exports displayed data series to a text file.

        See the :class:`.ExportDataSeriesAction`.
        """
        from fsleyes.actions.exportdataseries import ExportDataSeriesAction
        ExportDataSeriesAction(self.overlayList, self.displayCtx, self)()


class OverlayPlotPanel(PlotPanel):
    """The ``OverlayPlotPanel`` is a :class:`.PlotPanel` which contains
    some extra logic for creating, storing, and drawing :class:`.DataSeries`
    instances for each overlay in the :class:`.OverlayList`.


    **Subclass requirements**

    Sub-classes must:

     1. Implement the :meth:`createDataSeries` method, so it creates a
        :class:`.DataSeries` instance for a specified overlay.

     2. Implement the :meth:`PlotPanel.draw` method so it calls the
        :meth:`.PlotCanvas.drawDataSeries`, passing :class:`.DataSeries`
        instances for all overlays where :attr:`.Display.enabled` is
        ``True``, and the call :meth:`.PlotCanvas.drawArtists` method.

     3. Optionally implement the :meth:`prepareDataSeries` method to
        perform any custom preprocessing.


    **The internal data series store**


    The ``OverlayPlotPanel`` maintains a store of :class:`.DataSeries`
    instances, one for each compatible overlay in the
    :class:`.OverlayList`. The ``OverlayPlotPanel`` manages the property
    listeners that must be registered with each of these ``DataSeries`` to
    refresh the plot.  These instances are created by the
    :meth:`createDataSeries` method, which is implemented by sub-classes. The
    following methods are available to sub-classes, for managing the internal
    store of :class:`.DataSeries` instances:

    .. autosummary::
       :nosignatures:

       getDataSeries
       getDataSeriesToPlot
       clearDataSeries
       updateDataSeries
       addDataSeries
       removeDataSeries


    **Proxy images**


    The ``OverlayPlotPanel`` will replace all :class:`.ProxyImage` instances
    with their base images. This functionality was originally added to support
    the :attr:`.HistogramSeries.showOverlay` functionality - it adds a mask
    image to the :class:`.OverlayList` to display the histogram range.
    Sub-classes may wish to adhere to the same logic (replacing ``ProxyImage``
    instances with their bases)


    **Control panels**


    The :class:`.PlotControlPanel`, :class:`.PlotListPanel`, and
    :class:`.OverlayListPanel` are *FSLeyes control* panels which work with
    the :class:`.OverlayPlotPanel`. The ``PlotControlPanel`` is not intended
    to be used directly - view-specific sub-classes are used instead. These
    panels can be added/removed via the :meth:`.ViewPanel.togglePanel`
    method.


    **Sub-classes**


    The ``OverlayPlotPanel`` is the base class for:

    .. autosummary::
       :nosignatures:

       ~fsleyes.views.timeseriespanel.TimeSeriesPanel
       ~fsleyes.views.histogrampanel.HistogramPanel
       ~fsleyes.views.powerspectrumpanel.PowerSpectrumPanel
    """


    plotColours = {}
    """This dictionary is used to store a collection of ``{overlay : colour}``
    mappings. It is shared across all ``OverlayPlotPanel`` instances, so that
    the same (initial) colour is used for the same overlay, across multiple
    plots.

    See also :attr:`plotStyles`.

    Sub-classes should use the :meth:`getOverlayPlotColour` and
    :meth:`getOverlayPlotStyle` methods to retrieve the initial colour and
    linestyle to use for a given overlay.
    """


    plotStyles = {}
    """This dictionary is used to store a collection of ``{overlay : colour}``
    mappings - it is used in conjunction with :attr:`plotColours`.
    """


    def __init__(self, *args, **kwargs):
        """Create an ``OverlayPlotPanel``.

        :arg initialState: Must be passed as a keyword argument. Allows you to
                           specify the initial enabled/disabled state for each
                           overlay. See :meth:`updateDataSeries`. If not
                           provided, only the data series for the currently
                           selected overlay is shown (if possible).

        All other argumenst are passed through to :meth:`PlotPanel.__init__`.
        """

        initialState = kwargs.pop('initialState', None)

        PlotPanel.__init__(self, *args, **kwargs)

        self.__name = 'OverlayPlotPanel_{}'.format(self.name)

        # The dataSeries attribute is a dictionary of
        #
        #   {overlay : DataSeries}
        #
        # mappings, containing a DataSeries instance for
        # each compatible overlay in the overlay list.
        #
        # refreshProps is a dict of
        #
        #   {overlay : ([targets], [propNames]}
        #
        # mappings, containing the target instances and
        # properties which, when those properties change,
        # need to trigger a refresh of the plot.
        #
        # refreshCounts is a dict of:
        #
        #   {target, propName : dscount}

        # mappings, containing all targets and
        # associated property names on which a listener
        # is currently registered, and the count of
        # DataSeries instances which are interested
        # in them.
        self.__dataSeries    = {}
        self.__refreshProps  = {}
        self.__refreshCounts = {}

        # Pre-generated default colours and line
        # styles to use - see plotColours, plotStyles,
        # getOverlayPlotColour, and getOverlayPlotStyle
        lut    = fslcm.getLookupTable('paul_tol_accessible')
        styles = plotting.DataSeries.lineStyle.getChoices()
        limit  = min(len(lut), len(styles))
        self.__defaultColours = [l.colour for l in lut[   :limit]]
        self.__defaultStyles  = [s        for s in styles[:limit]]

        self.canvas     .addListener('dataSeries',
                                     self.__name,
                                     self.__dataSeriesChanged)
        self.overlayList.addListener('overlays',
                                     self.__name,
                                     self.__overlayListChanged)

        self.__overlayListChanged(initialState=initialState)
        self.__dataSeriesChanged()


    def destroy(self):
        """Must be called when this ``OverlayPlotPanel`` is no longer needed.
        Removes some property listeners, and calls :meth:`PlotPanel.destroy`.
        """
        self.overlayList.removeListener('overlays',   self.__name)
        self.canvas     .removeListener('dataSeries', self.__name)

        for overlay in list(self.__dataSeries.keys()):
            self.clearDataSeries(overlay)

        self.__dataSeries    = None
        self.__refreshProps  = None
        self.__refreshCounts = None

        PlotPanel.destroy(self)


    def getDataSeriesToPlot(self):
        """Convenience method which returns a list of overlays which have
        :class:`.DataSeries` that should be plotted.
        """

        overlays = self.overlayList[:]

        # Display.enabled
        overlays = [o for o in overlays
                    if self.displayCtx.getDisplay(o).enabled]

        # Replace proxy images
        overlays = [o.getBase() if isinstance(o, fsloverlay.ProxyImage)
                    else o for o in overlays]

        # Have data series
        dss = [self.getDataSeries(o) for o in overlays]
        dss = [ds for ds in dss if ds is not None]

        # Gather any extra time series
        # associated with the base time
        # series objects.
        for i, ds in enumerate(list(reversed(dss))):

            extras = ds.extraSeries()
            dss    = dss[:i + 1] + extras + dss[i + 1:]

            # If a base time series is disabled,
            # its additional ones should also
            # be disabled
            for eds in extras:
                eds.enabled = ds.enabled

        # Remove duplicates
        unique = []
        for ds in dss:
            if ds not in unique:
                unique.append(ds)

        return unique


    def getDataSeries(self, overlay):
        """Returns the :class:`.DataSeries` instance associated with the
        specified overlay, or ``None`` if there is no ``DataSeries`` instance.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        return self.__dataSeries.get(overlay)


    def getOverlayPlotColour(self, overlay):
        """Returns an initial colour to use for plots associated with the
        given overlay. If a colour is present in the  :attr:`plotColours`
        dictionary, it is returned. Otherwise a random colour is generated,
        added to ``plotColours``, and returned.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        colour = self.plotColours.get(overlay)

        if colour is None:
            idx    = len(self.plotColours) % len(self.__defaultColours)
            colour = self.__defaultColours[idx]
            self.plotColours[overlay] = colour

        return colour


    def getOverlayPlotStyle(self, overlay):
        """Returns an initial line style to use for plots associated with the
        given overlay. If a colour is present in the  :attr:`plotStyles`
        dictionary, it is returned. Otherwise a line style is generated,
        added to ``plotStyles``, and returned.

        The format of the returned line style is suitable for use with the
        ``linestyle`` argument of the ``matplotlib`` ``plot`` functions.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        style = self.plotStyles.get(overlay)

        if style is None:
            idx   = len(self.plotStyles) % len(self.__defaultStyles)
            style = self.__defaultStyles[idx]
            self.plotStyles[overlay] = style

        return style


    @actions.action
    def addDataSeries(self):
        """Every :class:`.DataSeries` which is currently plotted, and has not
        been added to the :attr:`.PlotCanvas.dataSeries` list, is added to said
        list.
        """

        # Get all the DataSeries objects which
        # have been drawn, and are not in the
        # dataSeries list.
        toAdd = self.canvas.getDrawnDataSeries()
        toAdd = [d[0] for d in toAdd if d[0] not in self.canvas.dataSeries]

        if len(toAdd) == 0:
            return

        # Replace each DataSeries instance with a copy.
        # This is necessary because some DataSeries
        # sub-classes have complicated behaviour (e.g.
        # changing their data when some properties
        # change). But we just want to 'freeze' the
        # data as it is currently shown. So we create
        # a dumb copy.
        for i, ds  in enumerate(toAdd):

            copy           = plotting.DataSeries(ds.overlay,
                                                 self.overlayList,
                                                 self.displayCtx,
                                                 self.canvas)
            toAdd[i]       = copy

            copy.alpha     = ds.alpha
            copy.lineWidth = ds.lineWidth
            copy.lineStyle = ds.lineStyle
            copy.label     = ds.label
            copy.colour    = ds.colour

            # We have to re-generate the data,
            # because the x/y data returned by
            # the getDrawnDataSeries method
            # above may have had post-processing
            # applied to it (e.g. smoothing)
            xdata, ydata = self.prepareDataSeries(ds)

            copy.setData(xdata, ydata)

            # This is disgraceful. It wasn't too bad
            # when this function was defined in the
            # PlotListPanel class, but is a horrendous
            # hack now that it is defined here in the
            # PlotPanel class.
            #
            # At some stage I will remove this offensive
            # code, and figure out a more robust system
            # for appending this metadata to DataSeries
            # instances.
            #
            # When the user selects a data series in
            # the list, we want to change the selected
            # overlay/location/volume/etc to the
            # properties associated with the data series.
            # So here we're adding some attributes to
            # each data series instance so that the
            # PlotListPanel.__onListSelect method can
            # update the display properties.
            opts = self.displayCtx.getOpts(ds.overlay)
            if isinstance(ds, (plotting.MelodicTimeSeries,
                               plotting.MelodicPowerSpectrumSeries)):
                copy._volume = opts.volume

            elif isinstance(ds, plotting.VoxelDataSeries):
                copy._location = opts.getVoxel()

        self.canvas.dataSeries.extend(toAdd)


    @actions.action
    def removeDataSeries(self, *a):
        """Removes the most recently added :class:`.DataSeries` from the
        :attr:`.PlotCanvas.dataSeries`.
        """
        if len(self.canvas.dataSeries) > 0:
            self.canvas.dataSeries.pop()


    def createDataSeries(self, overlay):
        """This method must be implemented by sub-classes. It must create and
        return a :class:`.DataSeries` instance for the specified overlay.


        .. note:: Sub-class implementations should set the
                  :attr:`.DataSeries.colour` property to that returned by
                  the :meth:`getOverlayPlotColour` method, and the
                  :attr:`.DataSeries.lineStyle` property to that returned by
                  the :meth:`getOverlayPlotStyle` method


        Different ``DataSeries`` types need to be re-drawn when different
        properties change. For example, a :class:`.VoxelTimeSeries`` instance
        needs to be redrawn when the :attr:`.DisplayContext.location` property
        changes, whereas a :class:`.MelodicTimeSeries` instance needs to be
        redrawn when the :attr:`.VolumeOpts.volume` property changes.


        Therefore, in addition to creating and returning a ``DataSeries``
        instance for the given overlay, sub-class implementations must also
        specify the properties which affect the state of the ``DataSeries``
        instance. These must be specified as two lists:

         - the *targets* list, a list of objects which own the dependant
           properties (e.g. the :class:`.DisplayContext` or
           :class:`.VolumeOpts` instance).

         - The *properties* list, a list of names, each specifying the
           property on the corresponding target.

        This method must therefore return a tuple containing:

          - A :class:`.DataSeries` instance, or ``None`` if the overlay
            is incompatible.
          - A list of *target* instances.
          - A list of *property names*.

        The target and property name lists must have the same length.
        """
        raise NotImplementedError('createDataSeries must be '
                                  'implemented by sub-classes')


    def clearDataSeries(self, overlay):
        """Destroys the internally cached :class:`.DataSeries` for the given
        overlay.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        ds                 = self.__dataSeries  .pop(overlay, None)
        targets, propNames = self.__refreshProps.pop(overlay, ([], []))

        if ds is not None:

            log.debug('Destroying {} for {}'.format(
                type(ds).__name__, overlay))

            for propName in ds.redrawProperties():
                ds.removeListener(propName, self.__name)
            ds.destroy()

        for t, p in zip(targets, propNames):
            count = self.__refreshCounts[t, p]

            if count - 1 == 0:
                self.__refreshCounts.pop((t, p))
                t.removeListener(p, self.__name)
            else:
                self.__refreshCounts[t, p] = count - 1


    def updateDataSeries(self, initialState=None):
        """Makes sure that a :class:`.DataSeries` instance has been created
        for every compatible overlay, and that property listeners are
        correctly registered, so the plot can be refreshed when needed.

        :arg initialState: If provided, must be a ``dict`` of ``{ overlay :
                           bool }`` mappings, specifying the initial value
                           of the :attr:`.DataSeries.enabled` property for
                           newly created instances. If not provided, only
                           the data series for the currently selected
                           overlay (if it has been newly added) is initially
                           enabled.
        """

        # Default to showing the
        # currently selected overlay
        if initialState is None:
            if len(self.overlayList) > 0:
                initialState = {self.displayCtx.getSelectedOverlay() : True}
            else:
                initialState = {}

        # Make sure that a DataSeries
        # exists for every compatible overlay
        newOverlays = []
        for ovl in self.overlayList:

            if ovl in self.__dataSeries:
                continue

            if isinstance(ovl, fsloverlay.ProxyImage):
                continue

            ds, refreshTargets, refreshProps = self.createDataSeries(ovl)
            display                          = self.displayCtx.getDisplay(ovl)

            if ds is None:

                # "Disable" overlays which don't have any data
                # to plot. We do this mostly so the overlay
                # appears greyed out in the OverlayListPanel.
                display.enabled = False
                continue

            # Display.enabled == DataSeries.enabled
            ds.bindProps('enabled', display)

            ds.enabled = initialState.get(ovl, False)

            log.debug('Created {} for overlay {} (enabled: {})'.format(
                type(ds).__name__, ovl, ds.enabled))

            newOverlays.append(ovl)

            self.__dataSeries[  ovl] = ds
            self.__refreshProps[ovl] = (refreshTargets, refreshProps)

        # Make sure that property listeners are
        # registered all of these overlays
        for overlay in newOverlays:

            targets, propNames = self.__refreshProps.get(overlay, (None, None))

            if targets is None:
                continue

            ds = self.__dataSeries[overlay]

            for propName in ds.redrawProperties():
                ds.addListener(propName,
                               self.__name,
                               self.canvas.asyncDraw,
                               overwrite=True)

            for target, propName in zip(targets, propNames):

                count = self.__refreshCounts.get((target, propName), 0)
                self.__refreshCounts[target, propName] = count + 1

                if count == 0:

                    log.debug('Adding listener on {}.{} for {} data '
                              'series'.format(type(target).__name__,
                                              propName,
                                              overlay))

                    target.addListener(propName,
                                       self.__name,
                                       self.canvas.asyncDraw,
                                       overwrite=True)


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`.PlotCanvas.dataSeries` list
        changes. Enables/disables the :meth:`removeDataSeries` action
        accordingly.
        """
        self.removeDataSeries.enabled = len(self.canvas.dataSeries) > 0


    def __overlayListChanged(self, *a, **kwa):
        """Called when the :class:`.OverlayList` changes. Makes sure that
        there are no :class:`.DataSeries` instances in the
        :attr:`.PlotCanvas.dataSeries` list, or in the internal cache, which
        refer to overlays that no longer exist.

        :arg initialState: Must be passed as a keyword argument. If provided,
                           passed through to the :meth:`updateDataSeries`
                           method.
        """

        initialState = kwa.get('initialState', None)

        for ds in list(self.canvas.dataSeries):
            if ds.overlay is not None and ds.overlay not in self.overlayList:
                self.canvas.dataSeries.remove(ds)
                ds.destroy()

        for overlay in list(self.__dataSeries.keys()):
            if overlay not in self.overlayList:
                self.clearDataSeries(overlay)

        for overlay in self.overlayList:
            display = self.displayCtx.getDisplay(overlay)

            # PlotPanels use the Display.enabled property
            # to toggle on/off overlay plots. We don't want
            # this to interfere with CanvasPanels, which
            # use Display.enabled to toggle on/off overlays.
            display.detachFromParent('enabled')

        self.updateDataSeries(initialState=initialState)
        self.canvas.asyncDraw()
