#!/usr/bin/env python
#
# clusterpanel.py - The ClusterPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ClusterPanel` class, a *FSLeyes control*
panel for viewing cluster results from a FEAT analysis.
"""

import itertools                     as it
import                                  logging
import                                  wx
import numpy                         as np

import fsl.utils.idle                as idle
import fsl.data.featimage            as featimage
import fsl.data.featanalysis         as featanalysis

import fsleyes_widgets               as fwidgets
import fsleyes_widgets.utils.status  as status
import fsleyes_widgets.widgetgrid    as widgetgrid
import fsleyes.views.canvaspanel     as canvaspanel
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.strings               as strings
import fsleyes.autodisplay           as autodisplay


log = logging.getLogger(__name__)


class ClusterPanel(ctrlpanel.ControlPanel):
    """The ``ClusterPanel`` shows a table of cluster results from the analysis
    associated with a :class:`.FEATImage` overlay. A ``ClusterPanel`` looks
    something like the following:

    .. image:: images/clusterpanel.png
       :scale: 50%
       :align: center

    The ``ClusterPanel`` contains controls which allow the user to:

      - Select the COPE or f-test for which cluster results are displayed

      - Add a Z statistic overlay for the currently displayed COPE/f-test

      - Add a cluster mask overlay for the currently displayed COPE/f-test

      - Navigate to the Z maximum location, Z centre-of-gravity location,
        or COPE maximum location, for a specific cluster.


    When an overlay is selected (detected via the
    :attr:`.DisplayContext.selectedOverlay` property), a ``ClusterPanel``
    tries to identify the FEAT analysis associated with the overlay. If
    the overlay is a :class:`.FEATImage`, then no work needs to be done.
    Otherwise, the ``ClusterPanel`` uses functions in the :mod:`.featanalysis`
    module to identify the FEAT directory. Ultimately, a reference to a
    :class:`.FEATImage` associated with the currently selected overlay is
    obtained, so the ``ClusterPanel`` can retrieve contrast and cluster
    information.


    A ``ClusterPanel`` uses a :class:`.WidgetGrid` to display information
    about the clusters associated with a contrast. Because creating all of the
    widgets contained in the ``WidgetGrid`` is expensive, a ``ClusterPanel``
    creates (on demand) and caches ``WidgetGrid`` instances for all
    :class:`.FEATImage` overlay and contrasts. This means that when the user
    changes the currently selected overlay, or the current contrast, the
    displayed cluster information is updated quickly.
    """


    @staticmethod
    def supportedViews():
        """The :class:`.ClusterPanel` is restricted for use with
        ``OrthoPanel``, ``LightBoxPanel`` and ``Scene3DPanel`` views.
        """
        return [canvaspanel.CanvasPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.TOP}


    def __init__(self, parent, overlayList, displayCtx, viewPanel):
        """Create a ``ClusterPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg viewPanel:   The :class:`.ViewPanel` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, viewPanel)

        self.__disabledText = wx.StaticText(
            self,
            style=(wx.ALIGN_CENTRE_HORIZONTAL |
                   wx.ALIGN_CENTRE_VERTICAL))

        self.__overlayName  = wx.StaticText(self)
        self.__addZStats    = wx.Button(    self)
        self.__addClustMask = wx.Button(    self)
        self.__statSelect   = wx.Choice(    self)

        # The featImages dictionary is a mapping
        # of { overlay : FEATImage } pairs. The
        # ClusterPanel will work with any overlay,
        # if that overlay is contained within a
        # feat analysis. The selectedOverlayChanged
        # method identifies the FEAT analysis
        # associated with the newly selected overlay,
        # and stores the mapping here. Note that the
        # FEATImage associated with an overlay might
        # not be in the overlay list.
        self.__featImages = {}

        # The clusterData dict is a mapping of {
        # FEATImage : clusters} pairs, containing
        # information about the significant clusters
        # for all COPEs/f-tests from the feat
        # analysis.  The cluster information is
        # loaded by the __loadClusterResults method
        # when a FEAT image is loaded/selected, or
        # when the user selects a contrast/f-test.
        self.__clusterData = {}

        # If more than one FEAT analysis is loaded,
        # the cluster panel will be reset when an
        # overlay from a different analysis is
        # selected. This dictionary is used to store
        # the selected statistic image for each
        # FEAT analysis so that when an analysis is
        # re-selected, the stat is set to its
        # previous value.
        self.__selectedStats = {}

        # A WidgetGrid is created for each contrast/
        # f-test of a FEAT image, and cached in this
        # dictionary. This is because it is quite
        # expensive to create the widget grids. This
        # dictionary contains {FEATImage :
        # [WidgetGrid]} mappings.
        self.__clusterGrids = {}

        self.__addZStats   .SetLabel(strings.labels[self, 'addZStats'])
        self.__addClustMask.SetLabel(strings.labels[self, 'addClustMask'])

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__topSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)

        args = {'flag' : wx.EXPAND, 'proportion' : 1}

        self.__topSizer.Add(self.__statSelect,   flag=wx.EXPAND, proportion=1)
        self.__topSizer.Add(self.__addZStats,    flag=wx.EXPAND, proportion=1)
        self.__topSizer.Add(self.__addClustMask, flag=wx.EXPAND, proportion=1)

        self.__mainSizer.Add(self.__overlayName, flag=wx.EXPAND)
        self.__mainSizer.Add(self.__topSizer,    flag=wx.EXPAND)

        # Only one of the disabledText or
        # mainSizer are shown at any one time
        self.__sizer.Add(self.__disabledText, **args)
        self.__sizer.Add(self.__mainSizer,    **args)

        overlayList.addListener('overlays',
                                self.name,
                                self.__overlayListChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)

        self.__statSelect  .Bind(wx.EVT_CHOICE, self.__statSelected)
        self.__addZStats   .Bind(wx.EVT_BUTTON, self.__addZStatsClick)
        self.__addClustMask.Bind(wx.EVT_BUTTON, self.__addClustMaskClick)

        self.SetMinSize(self.__calcMinSize())

        # We store a reference to the currently displayed
        # overlay, and store a reference to the corresponding
        # FEAT analysis in the __featImages dict. We need a
        # ref to the overlay in case the FEATImage is not in
        # the overlay list, and we need to do coordinate
        # transforms via a DisplayOpts instance.
        self.__displayedOverlay = None
        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``ClusterPanel`` is no longer needed.
        Removes some property listeners, and calls
        :meth:`.ControlPanel.destroy`.
        """

        for grids in self.__clusterGrids.values():
            for grid in grids:
                if grid is not None:
                    grid.Destroy()

        self.__clusterGrids     = None
        self.__featImages       = None
        self.__selectedStats    = None
        self.__displayedOverlay = None

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)

        ctrlpanel.ControlPanel.destroy(self)


    @property
    def statSelect(self):
        """Return a reference to the ``wx.Choice`` widget used to select
        the current contrast/f-test.
        """
        return self.__statSelect


    @property
    def addZStats(self):
        """Return a reference to the ``wx.Button`` widget used to add
        the Z-statistic image for the current test to the overlay list.
        """
        return self.__addZStats


    @property
    def addClustMask(self):
        """Return a reference to the ``wx.Button`` widget used to add
        the cluster mask image for the current test to the overlay list.
        """
        return self.__addClustMask


    def __calcMinSize(self):
        """Figures out the minimum size that this ``ClusterPanel`` should
        have. Called by :meth:`__init__`.

        When the ``ClusterPanel`` is created, the COPE combo box is not
        populated, so has no minimum size. Here, we figure out a good minimum
        size for it. We can then calculate a good minimum size for the entire
        panel.
        """

        dc = wx.ClientDC(self.__statSelect)

        dummyName = strings.labels[self, 'clustName'].format(1, 'WW')

        w, h = dc.GetTextExtent(dummyName)

        self.__statSelect .SetMinSize((w, h))
        self.__sizer.Layout()

        return self.__sizer.GetMinSize()


    def __disable(self, message):
        """Disables the ``ClusterPanel``, and displays the given message.
        Called when the selected overlay is not associated with a FEAT
        analysis, or when cluster results cannot be displayed for some reason.
        """

        self.__disabledText.SetLabel(message)
        self.__sizer.Show(self.__disabledText, True)
        self.__sizer.Show(self.__mainSizer,    False)
        self.Layout()


    def __enable(self):
        """Enables the ``ClusterPanel``. This amounts to hiding the
        disabled message panel, and showing the appropriate
        :class:`.WidgetGrid` for the currently selected overlay / contrast.
        The appropriate ``WidgetGrid`` is assumed to have already been
        created.
        """
        self.__sizer.Show(self.__disabledText, False)
        self.__sizer.Show(self.__mainSizer,    True)

        overlay   = self.__displayedOverlay
        featImage = self.__featImages[overlay]
        testidx   = self.__statSelect.GetSelection()

        for fimg, grids in self.__clusterGrids.items():
            for i, grid in enumerate(grids):
                if grid is not None:
                    show = fimg is featImage and i == testidx
                    self.__mainSizer.Show(grid, show)

        self.Layout()


    def __statSelected(self, ev=None):
        """Called when a COPE is selected. Retrieves a cached
        :class:`.WidgetGrid`, or creates a new one (via the
        :meth:`__genClusterGrid` method) which displays information about the
        clusters associated with the currently selected contrast or f-test.
        """
        overlay   = self.__displayedOverlay
        featImage = self.__featImages[overlay]
        idx       = self.__statSelect.GetSelection()

        # save the selection so we can
        # restore it later on if needed
        self.__selectedStats[featImage.dataSource] = idx

        self.Refresh()
        self.Update()

        if featImage not in self.__clusterGrids:
            cons   = [None] * featImage.numContrasts()
            ftests = [None] * featImage.numFTests()
            self.__clusterGrids[featImage] = cons + ftests

        grid = self.__clusterGrids[featImage][idx]

        if grid is None:
            grid = self.__genClusterGrid(overlay, featImage, idx)
            self.__clusterGrids[featImage][idx] = grid
            self.__mainSizer.Add(grid, flag=wx.EXPAND, proportion=1)

        self.__enable()
        self.__enableOverlayButtons()


    def __addZStatsClick(self, ev):
        """Called when the *Add Z statistics* button is pushed. Retrieves
        the Z statistic image for the current COPE (see the
        :meth:`.FEATImage.getZStats` method), and adds it as an overlay
        to the :class:`.OverlayList`.
        """

        overlay   = self.__displayedOverlay
        featImage = self.__featImages[overlay]

        # Get selected test, and convert
        # to a contrast or f-test index
        idx       = self.__statSelect.GetSelection()
        ftest     = self.__clusterData[featImage][idx][1]
        idx       = self.__clusterData[featImage][idx][0]

        if ftest: zstats = featImage.getZFStats(idx)
        else:     zstats = featImage.getZStats(idx)

        # Already in overlay list
        if self.overlayList.find(zstats.dataSource) is not None:
            return

        log.debug('Adding Z-statistic %s to overlay list', zstats.name)
        self.overlayList.append(zstats, overlayType='volume')

        zthres = featImage.thresholds()['z']

        autodisplay.autoDisplay(
            zstats,
            self.overlayList,
            self.displayCtx,
            zthres=zthres,
            posCmap='red-yellow',
            negCmap='blue-lightblue')


    def __addClustMaskClick(self, ev):
        """Called when the *Add cluster mask* button is pushed. Retrieves the
        cluster mask image for the currewnt contrast (see the
        :meth:`.FEATImage.getClusterMask` method)
        """
        overlay   = self.__displayedOverlay
        featImage = self.__featImages[overlay]

        # Get selected test, and convert
        # to a contrast or f-test index
        idx       = self.__statSelect.GetSelection()
        ftest     = self.__clusterData[featImage][idx][1]
        idx       = self.__clusterData[featImage][idx][0]

        if ftest: mask = featImage.getFClusterMask(idx)
        else:     mask = featImage.getClusterMask(idx)

        # Already in overlay list
        if self.overlayList.find(mask.dataSource) is not None:
            return

        log.debug('Adding cluster mask %s to overlay list', mask.name)
        self.overlayList.append(mask, overlayType='label', outline=True)


    def __genClusterGrid(self, overlay, featImage, testidx):
        """Creates and returns a :class:`.WidgetGrid` which contains the given
        list of clusters, which are related to the given contrast.


        .. note:: This method assumes that the given ``overlay`` is an
                  :class:`.Image` which has the same voxel dimensions as,
                  and shares the the same world coordinate system as the
                  ``featImage``.


        :arg overlay:   The overlay for which clusters are currently being
                        displayed.

        :arg featImage: The :class:`.FEATImage` to which the clusters are
                        related.

        :arg testidx:   The internal index identifying the contrast/f-test.
        """

        cols = {'index'         : 0,
                'nvoxels'       : 1,
                'p'             : 2,
                'logp'          : 3,
                'zmax'          : 4,
                'zmaxcoords'    : 5,
                'zcogcoords'    : 6,
                'copemax'       : 7,
                'copemaxcoords' : 8,
                'copemean'      : 9}

        grid = widgetgrid.WidgetGrid(self)
        opts = self.displayCtx.getOpts(overlay)

        # We store contrast/f-test results in
        # a single list, so need to look up the
        # test type, and the actual contrast/
        # f-test index used by the FEATImage
        testName = self.__clusterData[featImage][testidx][2]
        clusters = self.__clusterData[featImage][testidx][3]

        # We hide the grid and disable
        # this panel while the grid is
        # being created.
        grid.Hide()
        self.Disable()

        grid.SetGridSize(len(clusters), 10)
        grid.ShowRowLabels(False)
        grid.ShowColLabels(True)

        for col, i in cols.items():
            grid.SetColLabel(i, strings.labels[self, col])

        def makeCoordButton(coords):

            # Cluster results for f-tests don't
            # have copemax info - the coordinates
            # will all be nan
            if np.isnan(coords[0]):
                label = wx.StaticText(grid, label='[n/a]')
                btn   = (1, 1)
            else:
                x, y, z = coords
                label   = wx.StaticText(grid, label=f'[{x} {y} {z}]')
                btn     = wx.Button(grid, label='\u2192', style=wx.BU_EXACTFIT)

                def onClick(ev):
                    dloc = opts.transformCoords([coords], 'voxel', 'display')
                    self.displayCtx.location = dloc[0]

                btn.Bind(wx.EVT_BUTTON, onClick)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(label, flag=wx.EXPAND, proportion=1)
            sizer.Add(btn)

            return sizer

        # Creating all of the widgets could
        # take a bit of time, so we do it
        # asynchronously via on the wx idle
        # loop. Display a message while
        # doing so.
        status.update(strings.messages[self, 'loadingCluster'].format(
            testName), timeout=None)

        def addCluster(i, clust):

            if not fwidgets.isalive(grid):
                return

            zmaxbtn    = makeCoordButton((clust.zmaxx,
                                          clust.zmaxy,
                                          clust.zmaxz))
            zcogbtn    = makeCoordButton((clust.zcogx,
                                          clust.zcogy,
                                          clust.zcogz))
            copemaxbtn = makeCoordButton((clust.copemaxx,
                                          clust.copemaxy,
                                          clust.copemaxz))

            grid.SetText(  i, cols['index'],         f'{clust.index}')
            grid.SetText(  i, cols['nvoxels'],       f'{clust.nvoxels}')
            grid.SetText(  i, cols['p'],             f'{clust.p}')
            grid.SetText(  i, cols['logp'],          f'{clust.logp}')
            grid.SetText(  i, cols['zmax'],          f'{clust.zmax}')
            grid.SetWidget(i, cols['zmaxcoords'],    zmaxbtn)
            grid.SetWidget(i, cols['zcogcoords'],    zcogbtn)
            grid.SetText(  i, cols['copemax'],       f'{clust.copemax}')
            grid.SetWidget(i, cols['copemaxcoords'], copemaxbtn)
            grid.SetText(  i, cols['copemean'],      f'{clust.copemean}')

        # Refresh the grid widget when all
        # clusters have been added.
        def onFinish():

            if not fwidgets.isalive(grid):
                return

            status.update('All clusters loaded.')
            self.Enable()
            grid.Show()
            grid.Refresh()

        for i, clust in enumerate(clusters):
            idle.idle(addCluster, i, clust)

        idle.idle(onFinish)

        return grid


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Destroys any
        cached :class:`.WidgetGrid` instances as needed, updates the *Add Z
        statistic* and *Add cluster mask* buttons, in case the user removed
        them, and calls :meth:`__selectedOverlayChanged`.
        """

        # Remove and destroy any cached
        # WidgetGrid panels for overlays
        # that have been removed from the
        # list.
        for overlay in list(self.__featImages.keys()):
            if overlay in self.overlayList:
                continue

            featImage = self.__featImages.pop(overlay)

            # Do nothing if there any other overlays
            # associated with this FEAT analysis
            if featImage in self.__featImages.values():
                continue

            # Otherwise clear everything
            # we know about the analysis.
            self.__selectedStats.pop(featImage, None)
            self.__clusterData  .pop(featImage, None)

            grids = self.__clusterGrids.pop(featImage, [])
            for grid in grids:
                if grid is not None:
                    self.__mainSizer.Detach(grid)
                    grid.Destroy()

        if self.__displayedOverlay is not None and \
           self.__displayedOverlay not in self.overlayList:
            self.__displayedOverlay = None

        self.__selectedOverlayChanged()
        self.__enableOverlayButtons()


    def __enableOverlayButtons(self):
        """Enables/disables the *Add Z statistic* and *Add cluster mask*
        buttons depending on whether the corresponding overlays are in the
        :class:`.OverlayList`. The buttons are only enabled if the
        corresponding overlays are *not* already loaded.
        """

        if self.__displayedOverlay is None:
            return

        overlay   = self.__displayedOverlay
        featImage = self.__featImages[overlay]
        idx       = self.__statSelect.GetSelection()

        # No cluster results
        if idx < 0:
            self.__addZStats   .Enable(False)
            self.__addClustMask.Enable(False)
            return

        # Convert from our list of test results
        # to the actual contrast / f-test index.
        # (we store all contrast/f-test results
        # in a single list)
        ftest = self.__clusterData[featImage][idx][1]
        idx   = self.__clusterData[featImage][idx][0]

        if ftest:
            zstat     = featImage.getZFStats(     idx)
            clustMask = featImage.getFClusterMask(idx)
        else:
            zstat     = featImage.getZStats(     idx)
            clustMask = featImage.getClusterMask(idx)

        dss = [ovl.dataSource for ovl in self.overlayList]

        self.__addZStats   .Enable(zstat    .dataSource not in dss)
        self.__addClustMask.Enable(clustMask.dataSource not in dss)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes,
        and by the :meth:`__overlayListChanged` method.

        If the newly selected overlay is a :class:`.FEATImage` (or is otherwise
        associated with a FEAT analysis) which has cluster results, they are
        loaded in, and displayed on a :class:`.WidgetGrid`.
        """

        # No overlays are loaded
        if len(self.overlayList) == 0:
            self.__disable(strings.messages[self, 'noOverlays'])
            return

        overlay       = self.displayCtx.getSelectedOverlay()
        prevOverlay   = self.__displayedOverlay
        featImage     = self.__lookupFEATImage(overlay)
        prevFeatImage = self.__lookupFEATImage(prevOverlay)

        # selected a non-FEAT image - clear the
        # panel, or keep displaying the previous
        # analysis
        if featImage is None:
            if prevFeatImage is None:
                self.__disable(strings.messages[self, 'notFEAT'])
            return

        # The newly selected overlay is a
        # part of a FEAT analysis
        self.__displayedOverlay = overlay

        # New overlay from same FEAT analysis as
        # previous overlay - keep displaying it
        if featImage is prevFeatImage:
            return

        # Otherwise we have a new analysis to display.
        # Get the contrast/f-test cluster information
        # for the new FEAT analysis.
        results = self.__loadClusterResults(featImage)

        # No cluster results exist for any contrast
        if results is None or len(results) == 0:
            self.__disable(strings.messages[self, 'noClusters'])
            return

        # Populate the stat selection combo box
        self.__statSelect.Clear()
        for result in results:
            name = strings.labels[self, 'clustName'].format(result[2])
            self.__statSelect.Append(name)

        # Show the FEAT analysis name
        self.__overlayName.SetLabel(featImage.name)

        # restore the stat selection if this
        # analysis has been previously displayed
        stat = self.__selectedStats.get(featImage.dataSource, 0)
        self.__statSelect.SetSelection(stat)

        # Refresh the widget grid
        self.__statSelected()

        self.Layout()


    def __lookupFEATImage(self, overlay):
        """Searches for a :class:`.FEATImage` for the FEAT analysis that
        ``overlay`` is associated with. Loads and caches if if necessary.
        Returns ``None`` if ``overlay`` is not associated with a FEAT analysis.
        """

        # accept None, makes client code easier
        if overlay is None:
            return None

        # image has been removed
        if overlay not in self.overlayList:
            return None

        # in-memory overlay - cannot associate
        # with a FEAT analysis
        if overlay.dataSource is None:
            return None

        # already loaded
        if overlay in self.__featImages:
            return self.__featImages[overlay]

        # is this overlay from a FEAT analysis?
        featDir = featanalysis.getAnalysisDir(overlay.dataSource)
        if featDir is None:
            return None

        # Load the FEATImage for the FEAT analysis
        # that the overlay comes from.  If the
        # overlay itself is a FEATImage, then we
        # have nothing to do.
        if isinstance(overlay, featimage.FEATImage):
            featImage = overlay
        else:

            featImage  = None
            candidates = it.chain(self.__featImages.values(), self.overlayList)

            # See if the FEAT image has already
            # been loaded for another overlay,
            # or is in the overlay list
            for candidate in candidates:
                if isinstance(candidate, featimage.FEATImage) and \
                   candidate.getFEATDir() == featDir:
                    featImage = candidate

            # As a last resort, if the FEATImage is not
            # in the overlay list, we'll load it.
            if featImage is None:
                featImage = featimage.FEATImage(featDir)

        self.__featImages[overlay] = featImage

        log.debug('Identified FEAT analysis associated with overlay '
                  '%s: %s', overlay, featImage.getFEATDir())

        return featImage


    def __loadClusterResults(self, featImage):
        """Loads cluster results for all contrasts and f-tests from the FEAT
        analysis for ``featImage``.  Returns a list of tuples, with each
        tuple containing:
          - The test index, starting from 0, relative to the total number of
            contrasts/f-tests. Contrasts and f-tests are indexed separately.
          - A boolean indicating whether the test is a contrast or an f-test
          - The test name
          - A list of cluster results (see
            :meth:`.featanalysis.loadClusterResults`). This will be ``None``
            if the results could not be loaded for some reason.
        """

        if featImage in self.__clusterData:
            return self.__clusterData[featImage]

        ncons   = featImage.numContrasts()
        nftests = featImage.numFTests()
        results = []

        for i in range(ncons + nftests):

            ftest = i >= ncons

            if ftest:
                i    = i - ncons
                name =  f'F-test {i + 1}'
            else:
                name = featImage.contrastNames()[i]
                name = f'COPE{i + 1} ({name})'

            try:
                clusters = featImage.clusterResults(i, ftest=ftest)

            # Error parsing the cluster data
            except Exception as e:
                log.warning('Error parsing cluster data for %s (test %i %s): '
                            '%s', featImage.name, i, ftest, e, exc_info=True)
                clusters = None

            results.append((i, ftest, name, clusters))

        self.__clusterData[featImage] = results

        return results
