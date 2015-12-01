#!/usr/bin/env python
#
# clusterpanel.py - The ClusterPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ClusterPanel` class, a *FSLeyes control*
panel for viewing cluster results from a FEAT analysis.
"""

import                        logging
import                        wx

import pwidgets.widgetgrid as widgetgrid

import fsl.fsleyes.panel   as fslpanel
import fsl.data.strings    as strings
import fsl.data.featimage  as featimage


log = logging.getLogger(__name__)


class ClusterPanel(fslpanel.FSLEyesPanel):
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
    """

    def __init__(self, parent, overlayList, displayCtx):
        """Create a ``ClusterPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__disabledText = wx.StaticText(
            self,
            style=(wx.ALIGN_CENTRE_HORIZONTAL |
                   wx.ALIGN_CENTRE_VERTICAL))

        self.__overlayName  = wx.StaticText(self)
        self.__addZStats    = wx.Button(    self)
        self.__addClustMask = wx.Button(    self)
        self.__statSelect   = wx.Choice(    self)
        self.__clusterList  = widgetgrid.WidgetGrid(self)

        self.__addZStats   .SetLabel(strings.labels[self, 'addZStats'])
        self.__addClustMask.SetLabel(strings.labels[self, 'addClustMask'])
        
        self.__clusterList.ShowRowLabels(False)
        self.__clusterList.ShowColLabels(True)
        
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
        self.__mainSizer.Add(self.__clusterList, flag=wx.EXPAND, proportion=1)

        # Only one of the disabledText or
        # mainSizer are shown at any one time
        self.__sizer.Add(self.__disabledText, **args)
        self.__sizer.Add(self.__mainSizer,    **args)

        overlayList.addListener('overlays',
                                self._name,
                                self.__overlayListChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
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
        :meth:`.FSLEyesPanel.destroy`.
        """
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        fslpanel.FSLEyesPanel.destroy(self)


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
        Called when the selected overlay  is not a :class:`.FEATImage`, or
        when cluster results cannot be displayed for some reason.
        """

        self.__disabledText.SetLabel(message)
        self.__sizer.Show(self.__disabledText, True)
        self.__sizer.Show(self.__mainSizer,    False)
        self.Layout()

        
    def __enable(self):
        """Enables the ``ClusterPanel``. This amounts to hiding the
        disabled message panel, and showing the :class:`.WidgetGrid`.
        """
        self.__sizer.Show(self.__disabledText, False)
        self.__sizer.Show(self.__mainSizer,    True)
        self.Layout() 

    
    def __statSelected(self, ev):
        """Called when a COPE is selected. Clears the cluster table, and
        displays clusters for the newly selected COPE (see the
        :meth:`__displayClusterData` method)
        """
        idx  = self.__statSelect.GetSelection() 
        data = self.__statSelect.GetClientData(idx)
        con  = idx + 1
        
        self.__disable(strings.messages[self, 'loadingCluster'].format(con))

        self.Refresh()
        self.Update()
 
        self.__displayClusterData(con, data)
        self.__enable()
        self.__enableOverlayButtons()


    def __addZStatsClick(self, ev):
        """Called when the *Add Z statistics* button is pushed. Retrieves
        the Z statistic image for the current COPE (see the
        :meth:`.FEATImage.getZStats` method), and adds it as an overlay
        to the :class:`.OverlayList`.
        """

        overlay  = self.__selectedOverlay
        contrast = self.__statSelect.GetSelection()
        zstats   = overlay.getZStats(contrast)

        for ol in self._overlayList:
            
            # Already in overlay list
            if ol.dataSource == zstats.dataSource:
                return

        log.debug('Adding Z-statistic {} to overlay list'.format(zstats.name))
        self._overlayList.append(zstats)

        opts   = self._displayCtx.getOpts(zstats)
        zthres = float(overlay.thresholds()['z'])

        # Set some display parameters if
        # we have a z value threshold
        if zthres is not None:

            absmax = max(map(abs, (opts.dataMin, opts.dataMax)))
            
            opts.cmap            = 'Render3'
            opts.invertClipping  = True 
            opts.displayRange.x  = -absmax, absmax
            opts.clippingRange.x = -zthres, zthres

    
    def __addClustMaskClick(self, ev):
        """Called when the *Add cluster mask* button is pushed. Retrieves the
        cluster mask image for the currewnt contrast (see the
        :meth:`.FEATImage.getClusterMask` method)

        """
        overlay  = self.__selectedOverlay
        contrast = self.__statSelect.GetSelection()
        mask     = overlay.getClusterMask(contrast)

        for ol in self._overlayList:
            
            # Already in overlay list
            if ol.dataSource == mask.dataSource:
                return

        log.debug('Adding cluster mask {} to overlay list'.format(mask.name))
        self._overlayList.append(mask)
        self._displayCtx.getDisplay(mask).overlayType = 'label'


    def __displayClusterData(self, contrast, clusters):
        """Updates the cluster table so that it is displaying the given list
        of clusters.

        :arg contrast: The number of the contrast to which the clusters are
                       related.

        :arg clusters: A sequence of objects, each representing one cluster.
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

        grid    = self.__clusterList
        overlay = self.__selectedOverlay
        opts    = self._displayCtx.getOpts(overlay)

        grid.SetGridSize(len(clusters), 10)

        for col, i in cols.items():
            grid.SetColLabel(i, strings.labels[self, col])

        def makeCoordButton(coords):

            label = wx.StaticText(grid, label='[{} {} {}]'.format(*coords))
            btn   = wx.Button(grid, label=u'\u2192', style=wx.BU_EXACTFIT)
            
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(label, flag=wx.EXPAND, proportion=1)
            sizer.Add(btn)

            def onClick(ev):
                dloc = opts.transformCoords([coords], 'voxel', 'display')[0]
                self._displayCtx.location = dloc

            btn.Bind(wx.EVT_BUTTON, onClick)

            return sizer

        for i, clust in enumerate(clusters):

            zmaxbtn    = makeCoordButton((clust.zmaxx,
                                          clust.zmaxy,
                                          clust.zmaxz))
            zcogbtn    = makeCoordButton((clust.zcogx,
                                          clust.zcogy,
                                          clust.zcogz))
            copemaxbtn = makeCoordButton((clust.copemaxx,
                                          clust.copemaxy,
                                          clust.copemaxz))

            fmt = lambda v: '{}'.format(v)
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

        grid.Refresh()
        

    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes. Updates the *Add Z
        statistic* and *Add cluster mask* buttons, in case the user removed
        them. Also calls :meth:`__selectedOverlayChanged`.
        """
        self.__selectedOverlayChanged()
        self.__enableOverlayButtons()


    def __enableOverlayButtons(self):
        """Enables/disables the *Add Z statistic* and *Add cluster mask*
        buttons depending on whether the corresponding overlays are in the
        :class:`.OverlayList`.
        """
        
        if self.__selectedOverlay is None:
            return

        overlay  = self.__selectedOverlay
        contrast = self.__statSelect.GetSelection()

        zstat     = overlay.getZStats(     contrast)
        clustMask = overlay.getClusterMask(contrast)

        dss = [ovl.dataSource for ovl in self._overlayList]

        self.__addZStats   .Enable(zstat    .dataSource not in dss)
        self.__addClustMask.Enable(clustMask.dataSource not in dss)
        
    
    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes,
        and by the :meth:`__overlayListChanged` method.

        If the newly selected overlay is a :class:`.FEATImage` which has
        cluster results, they are loaded in, and displayed on the cluster
        table.
        """

        prevOverlay            = self.__selectedOverlay
        self.__selectedOverlay = None
        
        # No overlays are loaded
        if len(self._overlayList) == 0:
            self.__disable(strings.messages[self, 'noOverlays'])
            return

        overlay = self._displayCtx.getSelectedOverlay()
        
        # Not a FEAT image, can't 
        # do anything with that
        if not isinstance(overlay, featimage.FEATImage):
            self.__disable(strings.messages[self, 'notFEAT'])
            return

        # Selected overlay is either the
        # same one (maybe the overlay list,
        # rather than the selected overlay,
        # changed) or the newly selected
        # overlay is from the same FEAT
        # analysis. No need to do anything.
        if prevOverlay is not None and (prevOverlay is overlay or 
           prevOverlay.getFEATDir() == overlay.getFEATDir()):
            self.__selectedOverlay = overlay
            return
            
        self.__statSelect .Clear()
        self.__clusterList.ClearGrid()
        self.__clusterList.Refresh()

        self.__selectedOverlay = overlay

        numCons  = overlay.numContrasts()
        conNames = overlay.contrastNames()

        try:
            # clusts is a list of (contrast, clusterList) tuples 
            clusts = [(c, overlay.clusterResults(c)) for c in range(numCons)]
            clusts = filter(lambda (con, clust): clust is not None, clusts)

        # Error parsing the cluster data
        except Exception as e:
            log.warning('Error parsing cluster data for '
                        '{}: {}'.format(overlay.name, str(e)), exc_info=True)
            self.__disable(strings.messages[self, 'badData'])
            return

        # No cluster results exist
        # for any contrast
        if len(clusts) == 0:
            self.__disable(strings.messages[self, 'noClusters'])
            return

        for contrast, clusterList in clusts:
            name = conNames[contrast]
            name = strings.labels[self, 'clustName'].format(contrast + 1, name)

            self.__statSelect.Append(name, clusterList)
            
        self.__overlayName.SetLabel(overlay.getAnalysisName())

        self.__statSelect.SetSelection(0)
        self.__displayClusterData(1, clusts[0][1])

        self.__enable()

        self.Layout()
