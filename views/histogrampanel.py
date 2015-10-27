#!/usr/bin/env python
#
# histogrampanel.py - The HistogramPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramPanel`, which is a *FSLeyes view*
that plots the histogram of data from :class:`.Image` overlays.  A
``HistogramPanel`` looks something like this:

.. image:: images/histogrampanel.png
   :scale: 50%
   :align: center


``HistogramPanel`` instances use the :class:`HistogramSeries` class (a
:class:`.DataSeries` sub-class) to encapsulate histogram data.
"""


import logging

import wx


import props

import fsl.data.image                             as fslimage
import fsl.data.strings                           as strings
import fsl.utils.dialog                           as fsldlg
import fsl.fsleyes.plotting.histogramseries       as histogramseries
import fsl.fsleyes.controls.histogramcontrolpanel as histogramcontrolpanel
import fsl.fsleyes.controls.histogramlistpanel    as histogramlistpanel
import                                               plotpanel


log = logging.getLogger(__name__)


class HistogramPanel(plotpanel.PlotPanel):
    """A :class:`.PlotPanel` which plots histograms from :class:`.Image`
    overlay data.

    A ``HistogramPanel`` plots one or more :class:`HistogramSeries` instances,
    each of which encapsulate histogram data from an :class:`.Image` overlay.

    In a similar manner to the :class:`.TimeSeriesPanel` a ``HistogramPanel``
    will, by default, plot a histogram from the currently selected overlay
    (dictated by the :attr:`.DisplayContext.selectedOverlay` property), if it
    is an :class:`.Image` instance.  This histogram series is referred to as
    the *current* histogram, and it can be enabled/disabled with the
    :attr:`showCurrent` setting.


    A couple of control panels may be shown on a ``HistogramPanel``:

    .. autosummary::
       :nosignatures:

       ~fsl.fsleyes.controls.histogramlistpanel.HistogramListPanel
       ~fsl.fsleyes.controls.histogramcontrolpanel.HistogramControlPanel

    The following actions are provided, in addition to those already provided
    by the :class:`.PlotPanel`:

    ========================== ============================================
    ``toggleHistogramList``    Show/hide a :class:`.HistogramListPanel`.
    ``toggleHistogramControl`` Show/hide a :class:`.HistogramControlPanel`.
    ========================== ============================================

    The ``HistogramListPanel`` and ``HistogramControlPanel`` are both shown
    by default when a new ``HistogramPanel`` is created.
    """


    autoBin = props.Boolean(default=True)
    """If ``True``, the number of bins used for each :class:`HistogramSeries`
    is calculated automatically. Otherwise, :attr:`HistogramSeries.nbins` bins
    are used.
    """

    
    showCurrent = props.Boolean(default=True)
    """If ``True``, a histogram for the currently selected overlay (if it is
    an :class:`.Image` instance) is always plotted.
    """

    
    histType = props.Choice(('probability', 'count'))
    """The histogram type:

    =============== ==========================================================
    ``count``       The y axis represents the absolute number of values within
                    each bin 
    ``probability`` The y axis represents the number of values within each
                    bin, divided by the total number of values.
    =============== ==========================================================
    """

    
    selectedSeries = props.Int(minval=0, clamped=True)
    """The currently selected :class:`HistogramSeries` - an index into the
    :attr:`.PlotPanel.dataSeries` list.

    This property is used by the :class:`.HistogramListPanel` and the
    :class:`.HistogramControlPanel`, to allow the user to change the settings
    of individual :class:`HistogramSeries` instances. 
    """
    

    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``HistogramPanel``.

        :arg parent:      The :mod:`wx` parent.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        actionz = {
            'toggleHistogramList'    : self.toggleHistogramList,
            'toggleHistogramControl' : lambda *a: self.togglePanel(
                histogramcontrolpanel.HistogramControlPanel,
                self,
                location=wx.TOP) 
        }

        plotpanel.PlotPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        figure = self.getFigure()
        
        figure.subplots_adjust(
            top=1.0, bottom=0.0, left=0.0, right=1.0)

        figure.patch.set_visible(False)

        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__overlayListChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)

        self.addListener('showCurrent', self._name, self.draw)
        self.addListener('histType',    self._name, self.draw)
        self.addListener('autoBin',     self._name, self.__autoBinChanged)
        self.addListener('dataSeries',  self._name, self.__dataSeriesChanged)

        # Creating a HistogramSeries is a bit expensive
        # as it needs to, well, create a histogram. So
        # we only create one HistogramSeries per overlay,
        # and we cache them here so that the user only
        # has to wait the first time they select an
        # overlay for its histogram to be calculated.
        #
        # When a HistogramSeries is added to the dataSeries
        # list, it is copied from the cached one so, again,
        # the histogram calculation doesn't need to be done.
        self.__histCache = {}
        self.__current   = None
        self.__updateCurrent()

        def addPanels():
            self.run('toggleHistogramControl') 
            self.run('toggleHistogramList')

        wx.CallAfter(addPanels) 


    def destroy(self):
        """Removes some property listeners, destroys all existing
        :class:`HistogramSeries` instances, and calls
        :meth:`.PlotPanel.destroy`.
        """
        
        self.removeListener('showCurrent', self._name)
        self.removeListener('histType',    self._name)
        self.removeListener('autoBin',     self._name)
        self.removeListener('dataSeries',  self._name)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        for hs in set(self.dataSeries[:] + self.__histCache.values()):
            hs.destroy()

        plotpanel.PlotPanel.destroy(self)


    def getCurrent(self):
        """Return the :class:`HistogramSeries` instance for the currently
        selected overlay. Returns ``None`` if :attr:`showCurrent` is
        ``False``, or the current overlay is not an :class:`.Image`.
        """
        if self.__current is None:
            self.__updateCurrent()

        if self.__current is None:
            return None

        return histogramseries.HistogramSeries(self.__current.overlay,
                                               self,
                                               self._displayCtx,
                                               self._overlayList,
                                               baseHs=self.__current) 


    def draw(self, *a):
        """Draws the current :class:`HistogramSeries` if there is one,, and
        any ``HistogramSeries`` that are in the :attr:`.PlotPanel.dataSeries`
        list, via a call to :meth:`.PlotPanel.drawDataSeries`.
        """

        extra = None

        if self.showCurrent:
            
            if self.__current is not None:
                extra = [self.__current]

        if self.smooth: self.drawDataSeries(extra)
        else:           self.drawDataSeries(extra, drawstyle='steps-pre')


    def toggleHistogramList(self, *a):
        """Shows/hides a :class:`.HistogramListPanel`. See the
        :meth:`.ViewPanel.togglePanel` method.
        """
        self.togglePanel(histogramlistpanel.HistogramListPanel,
                         self,
                         location=wx.TOP)


    def __dataSeriesChanged(self, *a):
        """Called when the :attr:`.PlotPanel.dataSeries` property changes.

        Updates the :attr:`selectedSeries` property accordingly.
        """
        self.setConstraint('selectedSeries',
                           'maxval',
                           len(self.dataSeries) - 1)

        listPanel = self.getPanel(histogramlistpanel.HistogramListPanel)

        if listPanel is None:
            self.selectedSeries = 0
        else:
            self.selectedSeries = listPanel.getListBox().GetSelection()

            
    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.

        Removes any :class:`HistogramSeries` from the
        :attr:`.PlotPanel.dataSeries` list which correspond to overlays that
        no longer exist.
        """
        
        self.disableListener('dataSeries', self._name)
        
        for ds in self.dataSeries:
            if ds.overlay not in self._overlayList:
                self.dataSeries.remove(ds)
                
        self.enableListener('dataSeries', self._name)

        # Remove any dead overlays
        # from the histogram cache
        for overlay in list(self.__histCache.keys()):
            if overlay not in self._overlayList:
                log.debug('Removing cached histogram series '
                          'for overlay {}'.format(overlay.name))
                hs = self.__histCache.pop(overlay)
                hs.destroy()
        
        self.__selectedOverlayChanged()

        
    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.

        Updates the current :class:`HistogramSeries`.
        """

        self.__updateCurrent()
        self.draw()

        
    def __autoBinChanged(self, *a):
        """Called when the :attr:`autoBin` property changes. Makes sure that
        all existing :class:`HistogramSeries` instances are updated before
        the plot is refreshed.
        """

        for ds in self.dataSeries:
            ds.update()

        if self.__current is not None:
            self.__current.update()

        self.draw()
        

    def __updateCurrent(self):
        """Creates/updates the current :class:`HistogramSeries` instance,
        if necessary.
        """

        # Make sure that the previous HistogramSeries
        # cleans up after itself, unless it has been
        # cached
        if self.__current is not None and \
           self.__current not in self.__histCache.values():
            self.__current.destroy()
            
        self.__current = None
        overlay        = self._displayCtx.getSelectedOverlay()

        if len(self._overlayList) == 0 or \
           not isinstance(overlay, fslimage.Image):
            return

        # See if there is already a HistogramSeries based on the
        # current overlay - if there is, use it as the 'base' HS
        # for the new one, as it will save us some processing time
        if overlay in self.__histCache:
            log.debug('Creating new histogram series for overlay {} '
                      'from cached copy'.format(overlay.name))
            baseHs = self.__histCache[overlay]
        else:
            baseHs = None

        def loadHs():
            return histogramseries.HistogramSeries(overlay,
                                                   self,
                                                   self._displayCtx,
                                                   self._overlayList,
                                                   baseHs=baseHs)

        # We are creating a new HS instance, so it
        # needs to do some initla data range/histogram
        # calculations. Show a message while this is
        # happening.
        if baseHs is None:
            hs = fsldlg.ProcessingDialog(
                None,
                strings.messages[self, 'calcHist'].format(overlay.name),
                loadHs).Run()

            # Put the initial HS instance for this
            # overlay in the cache so we don't have
            # to re-calculate it later
            log.debug('Caching histogram series for '
                      'overlay {}'.format(overlay.name))
            self.__histCache[overlay] = hs
            
        # The new HS instance is being based on the
        # current instance, so it can just copy the
        # histogram data over - no message dialog
        # is needed
        else:
            hs = loadHs()

        hs.colour      = [0, 0, 0]
        hs.alpha       = 1
        hs.lineWidth   = 1
        hs.lineStyle   = '-'
        hs.label       = None

        self.__current = hs
