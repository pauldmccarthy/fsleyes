#!/usr/bin/env python
#
# clusterpanel.py - The ClusterPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ClusterPanel` class, a *FSLeyes control*
panel for viewing cluster results from a FEAT analysis.
"""

import                                  logging
import                                  wx
import                                  six

import fsl.utils.idle                as idle
import fsl.data.image                as fslimage
import fsl.data.featimage            as featimage
import fsl.data.featanalysis         as featanalysis

import fsleyes_widgets               as fwidgets
import fsleyes_widgets.utils.status  as status
import fsleyes_widgets.widgetgrid    as widgetgrid
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

      - Select the COPE for which cluster results are displayed

      - Add a Z statistic overlay for the currently displayed COPE

      - Add a cluster mask overlay for the currently displayed COPE

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

    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``ClusterPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

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

        # A WidgetGrid is created for each
        # contrast of a FEAT image, and cached
        # in this dictionary. This is because
        # it is quite expensive to create the
        # grid widgets. This dictionary contains
        # {FEATImage : [WidgetGrid]} mappings.
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

        self.__selectedOverlay = None
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

        self.__clusterGrids = None
        self.__featImages   = None

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)

        ctrlpanel.ControlPanel.destroy(self)


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

        overlay   = self.__selectedOverlay
        featImage = self.__featImages[overlay]
        contrast  = self.__statSelect.GetSelection()

        for fimg, grids in self.__clusterGrids.items():
            for i, grid in enumerate(grids):
                if grid is not None:
                    show = fimg is featImage and i == contrast
                    self.__mainSizer.Show(grid, show)

        self.Layout()


    def __statSelected(self, ev=None):
        """Called when a COPE is selected. Retrieves a cached
        :class:`.WidgetGrid`, or creates a new one (via the
        :meth:`__genClusterGrid` method) which displays information
        about the clusters associated with the currently selected contrast.
        """
        overlay   = self.__selectedOverlay
        featImage = self.__featImages[overlay]
        idx       = self.__statSelect.GetSelection()
        data      = self.__statSelect.GetClientData(idx)

        self.Refresh()
        self.Update()

        if featImage not in self.__clusterGrids:
            self.__clusterGrids[featImage] = [None] * featImage.numContrasts()

        grid = self.__clusterGrids[featImage][idx]

        if grid is None:
            grid = self.__genClusterGrid(overlay, featImage, idx, data)
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

        overlay   = self.__selectedOverlay
        featImage = self.__featImages[overlay]
        contrast  = self.__statSelect.GetSelection()
        zstats    = featImage.getZStats(contrast)

        for ol in self.overlayList:

            # Already in overlay list
            if ol.dataSource == zstats.dataSource:
                return

        log.debug('Adding Z-statistic {} to overlay list'.format(zstats.name))
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
        overlay   = self.__selectedOverlay
        featImage = self.__featImages[overlay]
        contrast  = self.__statSelect.GetSelection()
        mask      = featImage.getClusterMask(contrast)

        for ol in self.overlayList:

            # Already in overlay list
            if ol.dataSource == mask.dataSource:
                return

        log.debug('Adding cluster mask {} to overlay list'.format(mask.name))
        self.overlayList.append(mask, overlayType='label')


    def __genClusterGrid(self, overlay, featImage, contrast, clusters):
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

        :arg contrast:  The (0-indexed) number of the contrast to which the
                        clusters are related.

        :arg clusters:  A sequence of objects, each representing one cluster.
                        See the :meth:`.FEATImage.clusterResults` method.
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

        grid    = widgetgrid.WidgetGrid(self)
        conName = featImage.contrastNames()[contrast]
        opts    = self.displayCtx.getOpts(overlay)

        # We hide the grid and disable
        # this panle while the grid is
        # being created.
        grid.Hide()
        self.Disable()

        grid.SetGridSize(len(clusters), 10)

        grid.ShowRowLabels(False)
        grid.ShowColLabels(True)

        for col, i in cols.items():
            grid.SetColLabel(i, strings.labels[self, col])

        def makeCoordButton(coords):

            label = wx.StaticText(grid, label='[{} {} {}]'.format(*coords))
            btn   = wx.Button(grid,
                              label=six.u('\u2192'),
                              style=wx.BU_EXACTFIT)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(label, flag=wx.EXPAND, proportion=1)
            sizer.Add(btn)

            def onClick(ev):
                dloc = opts.transformCoords([coords], 'voxel', 'display')[0]
                self.displayCtx.location = dloc

            btn.Bind(wx.EVT_BUTTON, onClick)

            return sizer

        # Creating all of the widgets could
        # take a bit of time, so we'll
        # do it asynchronously via idle.idle
        # display a message while doing so.
        status.update(strings.messages[self, 'loadingCluster'].format(
            contrast + 1, conName), timeout=None)

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

            def fmt(v):
                return '{}'.format(v)

            grid.SetText(  i, cols['index'],         fmt(clust.index))
            grid.SetText(  i, cols['nvoxels'],       fmt(clust.nvoxels))
            grid.SetText(  i, cols['p'],             fmt(clust.p))
            grid.SetText(  i, cols['logp'],          fmt(clust.logp))
            grid.SetText(  i, cols['zmax'],          fmt(clust.zmax))
            grid.SetWidget(i, cols['zmaxcoords'],    zmaxbtn)
            grid.SetWidget(i, cols['zcogcoords'],    zcogbtn)
            grid.SetText(  i, cols['copemax'],       fmt(clust.copemax))
            grid.SetWidget(i, cols['copemaxcoords'], copemaxbtn)
            grid.SetText(  i, cols['copemean'],      fmt(clust.copemean))

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
            if overlay not in self.overlayList:

                featImage = self.__featImages.pop(overlay)

                # Has the feat image associated with
                # this overlay also been removed?
                if featImage is overlay or \
                   featImage not in self.overlayList:

                    # The grid widgets for the feat image
                    # associated with this overlay may
                    # have already been destroyed.
                    try:             grids = self.__clusterGrids.pop(featImage)
                    except KeyError: grids = []

                    for grid in grids:
                        if grid is not None:
                            self.__mainSizer.Detach(grid)
                            grid.Destroy()

        self.__selectedOverlayChanged()
        self.__enableOverlayButtons()


    def __enableOverlayButtons(self):
        """Enables/disables the *Add Z statistic* and *Add cluster mask*
        buttons depending on whether the corresponding overlays are in the
        :class:`.OverlayList`.
        """

        if self.__selectedOverlay is None:
            return

        overlay   = self.__selectedOverlay
        featImage = self.__featImages[overlay]
        contrast  = self.__statSelect.GetSelection()

        # No cluster results
        if contrast < 0:
            self.__addZStats   .Enable(False)
            self.__addClustMask.Enable(False)
            return

        zstat     = featImage.getZStats(     contrast)
        clustMask = featImage.getClusterMask(contrast)

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

        prevOverlay            = self.__selectedOverlay
        self.__selectedOverlay = None

        # No overlays are loaded
        if len(self.overlayList) == 0:
            self.__disable(strings.messages[self, 'noOverlays'])
            return

        overlay = self.displayCtx.getSelectedOverlay()

        # Overlay is in-memory
        if overlay.dataSource is None:
            self.__disable(strings.messages[self, 'notFEAT'])
            return

        featDir = featanalysis.getAnalysisDir(overlay.dataSource)

        # No FEAT analysis, or not an Image,
        # can't do anything with that
        if featDir is None or not isinstance(overlay, fslimage.Nifti):
            log.debug('Overlay {} is not part of a feat '
                      'analysis, or is not Nifti'.format(overlay))
            self.__disable(strings.messages[self, 'notFEAT'])
            return

        # Selected overlay is either the
        # same one (maybe the overlay list,
        # rather than the selected overlay,
        # changed) or the newly selected
        # overlay is from the same FEAT
        # analysis. No need to do anything.
        if prevOverlay is not None:

            prevFeatImage = self.__featImages.get(prevOverlay)

            if prevOverlay is overlay or \
               (prevFeatImage is not None and
                    featDir == prevFeatImage.getFEATDir()):

                log.debug('Overlay {} is already selected.'.format(overlay))

                # Make sure the overlay -> FEATImage
                # mapping is present, and (re-)cache
                # a reference to the selected overlay.
                self.__featImages[overlay] = prevFeatImage
                self.__selectedOverlay     = overlay

                return

        # We're in business. The newly selected
        # overlay is a part of a FEAT analysis
        # which is not currently being displayed.
        self.__selectedOverlay = overlay

        # Clear the stat selection combo box.
        self.__statSelect.Clear()

        # Get the FEATImage associated with
        # this overlay, so we can get
        # information about the FEAT analysis
        featImage = self.__featImages.get(overlay)
        if featImage is None:

            # If the overlay itself is a FEATImage,
            # then we have nothing to do.
            if isinstance(overlay, featimage.FEATImage):
                featImage = overlay
            else:
                # The FEATImage might already
                # be in the overlay list -
                # let's search for it.
                for ovl in self.overlayList:
                    if isinstance(ovl, featimage.FEATImage) and \
                       ovl.getFEATDir() == featDir:
                        featImage = ovl

            # As a last resort, if the FEATImage is not
            # in the overlay list, we'll create one.
            if featImage is None:
                featImage = featimage.FEATImage(featDir,
                                                loadData=False,
                                                calcRange=False)

            self.__featImages[overlay] = featImage

        log.debug('Identified FEAT analysis associated with overlay '
                  '{}: {}'.format(overlay, featImage.getFEATDir()))

        # Get the contrast and cluster
        # information for the FEAT analysis.
        display  = self.displayCtx.getDisplay(overlay)
        numCons  = featImage.numContrasts()
        conNames = featImage.contrastNames()

        try:
            # clusts is a list of (contrast, clusterList) tuples
            clusts = [(c, featImage.clusterResults(c)) for c in range(numCons)]
            clusts = [c for c in clusts if c[1] is not None]

        # Error parsing the cluster data
        except Exception as e:
            log.warning('Error parsing cluster data for '
                        '{}: {}'.format(featImage.name, str(e)), exc_info=True)
            self.__disable(strings.messages[self, 'badData'])
            return

        # No cluster results exist
        # for any contrast
        if len(clusts) == 0:
            self.__disable(strings.messages[self, 'noClusters'])
            return

        # Populate the stat selection combo box
        for contrast, clusterList in clusts:
            name = conNames[contrast]
            name = strings.labels[self, 'clustName'].format(contrast + 1, name)

            self.__statSelect.Append(name, clusterList)

        self.__overlayName.SetLabel(display.name)

        # Refresh the widget grid
        self.__statSelect.SetSelection(0)
        self.__statSelected()

        self.Layout()
