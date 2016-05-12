#!/usr/bin/env python
#
# atlasoverlaypanel.py -  The AtlasOverlayPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`AtlasOverlayPanel`, which is a sub-panel
used by the :class:`.AtlasPanel`.
"""


import logging

import wx

import pwidgets.elistbox                  as elistbox
import pwidgets.placeholder_textctrl      as plctext

import fsl.data.atlases                   as atlases
import fsl.utils.status                   as status
import fsl.utils.async                    as async
from   fsl.utils.platform import platform as fslplatform
import fsleyes.panel                      as fslpanel
import fsleyes.strings                    as strings



log = logging.getLogger(__name__)
        

class AtlasOverlayPanel(fslpanel.FSLEyesPanel):
    """The ``AtlasOverlayPanel`` displays a list of all available FSL atlases
    (see the :mod:`.atlases` module), and allows the user to:

      1. Search across all atlases for regions, by name.

      2. Toggle overlays for atlases, and for individual regions from any
         atlas.

      3. Move the :attr:`.DisplayContext.location` to any region from any
         atlas.

    
    An ``AtlasOverlayPanel`` looks something like this:

    .. image:: images/atlasoverlaypanel.png
       :scale: 50%
       :align: center


    The ``AtlasOverlayPanel`` has three main sections:

      - The *atlas list* - a :class:`pwidgets.elistbox.EditableListBox` with
        an entry, and an :class:`OverlayListWidget` for every available atlas.
        The ``OverlayListWidget`` allows the user to turn on/off a summary
        overlay image for the atlas (see the section on
        :ref:`atlas panel overlays <atlas-panel-atlas-overlays>`).

      - The *region list* - an ``EditableListBox`` which contains one entry
        for every region in the atlas that is currently selected in the atlas
        list, and an ``OverlayListWidget`` alongside every region. The
        ``OverlayListWidget`` allows the user to navigate to a region, and
        to turn on/off a label or probabilistic region overlay.

      - The *region filter* - a ``wx.TextCtrl`` located above the region
        list. This allows the user to search for regions by name. When the
        user types a string into this field, the region list will be updated
        to show only regions that match the entered string (via a simple
        substring match), and the atlas list will be updated such that all
        atlases which have matching regions will be highlighted in bold.
    """ 

    def __init__(self, parent, overlayList, displayCtx, atlasPanel):
        """Create an ``AtlasOverlayPanel``.

        :arg parent:      the :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList` instance.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg atlasPanel:  The :class:`.AtlasPanel` instance that has created
                          this ``AtlasInfoPanel``. 
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        # See the enableAtlasPanel method 
        # for info about this attribute.
        self.__atlasPanelEnableStack = 0

        # References to an EditableListBox
        # for each atlas, containing a list
        # of its regions. These are created
        # on-demand in the __onAtlasSelect
        # method.
        self.__regionLists = []

        self.__atlasPanel      = atlasPanel
        self.__contentPanel    = wx.SplitterWindow(self,
                                                   style=wx.SP_LIVE_UPDATE)
        self.__atlasList       = elistbox.EditableListBox(
            self.__contentPanel,
            style=(elistbox.ELB_NO_ADD    |
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        self.__regionPanel     = wx.Panel(self.__contentPanel)
        self.__regionFilter    = plctext.PlaceholderTextCtrl(
            self.__regionPanel, placeholder='Search')

        self.__contentPanel.SetMinimumPaneSize(50)
        self.__contentPanel.SplitVertically(self.__atlasList,
                                            self.__regionPanel)
        self.__contentPanel.SetSashGravity(0.5) 
        
        self.__sizer       = wx.BoxSizer(wx.HORIZONTAL)
        self.__regionSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.__regionSizer.Add(self.__regionFilter, flag=wx.EXPAND)
        self.__regionSizer.AddStretchSpacer()
        
        self.__sizer      .Add(self.__contentPanel,
                               flag=wx.EXPAND,
                               proportion=1)
        
        self.__regionPanel.SetSizer(self.__regionSizer) 
        self              .SetSizer(self.__sizer)

        self.__regionFilter.Bind(wx.EVT_TEXT, self.__onRegionFilter)
        self.__atlasList.Bind(elistbox.EVT_ELB_SELECT_EVENT,
                              self.__onAtlasSelect)

        fslplatform.register(self._name, self.__fslDirChanged)

        self.__buildAtlasList()

        self.__regionSizer.Layout()
        self.__sizer      .Layout()

        self.SetMinSize(self.__sizer.GetMinSize())


    def setOverlayState(self, atlasID, labelIdx, summary, state):
        """Updates the *enabled* state of the specified atlas overlay.

        This method is called by the :class:`.AtlasPanel` when an atlas overlay
        is added/removed to/from the :class:`.OverlayList`. It ensures that the
        :class:`OverlayListWidget` controls for every atlas, and every region,
        are up to date.
        """

        atlasDesc = atlases.getAtlasDescription(atlasID)
        log.debug('Setting {}/{} overlay state to {}'.format(
            atlasID, labelIdx, state))

        if labelIdx is None:
            widget = self.__atlasList.GetItemWidget(atlasDesc.index)
            widget.SetEnableState(state)
        else:
            regionList = self.__regionLists[atlasDesc.index]
            
            if regionList is not None:
                regionList.GetItemWidget(labelIdx).SetEnableState(state)

                
    def __fslDirChanged(self, *a):
        """Called when the :attr:`.Platform.fsldir` changes. Refreshes
        the atlas list.
        """ 
        self.__buildAtlasList()

    
    def __buildAtlasList(self):
        """Clears and recreates the atlas list. Also clears all existing
        region lists.
        """

        atlasDescs = None

        # Don't bother if fsldir is not set
        if fslplatform.fsldir is None:
            return 

        # See AtlasInfoPanel.__buildAtlasList
        # for a more commented version of what
        # is essentially the same process as
        # below.
        #
        # TL,DR: Loading atlas descriptions might take
        #        time, so it is performed asynchronously
        #        on a separate thread.
        def loadAtlases():
            global atlasDescs
            atlasDescs = atlases.listAtlases()

        def buildList():
            global atlasDescs

            # We might have been destroyed
            # while the atlases were being
            # loaded.
            try:
                if self.destroyed():
                    return
            except wx.PyDeadObjectError:
                return
            
            # If a region list is currently
            # being shown, clear it. 
            regionList = self.__regionSizer.GetItem(1).GetWindow()
            if regionList is not None:
                self.__regionSizer.Remove(1)
                self.__regionSizer.AddStretchSpacer()

            # Destroy any existing region lists
            for regionList in self.__regionLists:
                if regionList is not None:
                    regionList.Destroy()

            self.__regionLists = [None] * len(atlasDescs)

            # Now clear and re-populate the atlas list
            self.__atlasList.Clear()
            for i, atlasDesc in enumerate(atlasDescs):
                self.__atlasList.Append(atlasDesc.name, atlasDesc)
                self.__updateAtlasState(i)
                widget = OverlayListWidget(self.__atlasList,
                                           atlasDesc.atlasID,
                                           i, 
                                           self.__atlasPanel,
                                           self)
                self.__atlasList.SetItemWidget(i, widget)

            self.__regionSizer.Layout()

        async.run(loadAtlases, onFinish=buildList)


    def __onRegionFilter(self, ev):
        """Called when the user enters some text in the region filter.

        Filters the region list (see the :meth:`.EditableListBox.ApplyFilter`
        method), and updates all items in the atlas list (see the
        :meth:`__updateAtlasState` method).
        """
        
        filterStr = self.__regionFilter.GetValue().lower().strip()

        for i, listBox in enumerate(self.__regionLists):

            self.__updateAtlasState(i)

            if listBox is not None:
                listBox.ApplyFilter(filterStr, ignoreCase=True)


    def __updateAtlasState(self, atlasIdx):
        """Updates the state of the atlas list item which corresponds to the
        atlas with the specified identifier.

        If the atlas has regions which match the current region filter string,
        the atlas label font is set to bold. Otherwise (or if the region filter
        string is empty), the atlas label font is set to normal.
        """

        filterStr = self.__regionFilter.GetValue().lower().strip()
        atlasDesc = self.__atlasList.GetItemData(atlasIdx)

        if filterStr == '':
            nhits = 0
        else:
            nhits = len([l for l in atlasDesc.labels
                         if filterStr in l.name.lower()])

        if nhits == 0:
            weight = wx.FONTWEIGHT_LIGHT
            colour = '#404040'
        else:
            weight = wx.FONTWEIGHT_BOLD
            colour = '#000000'

        font = self.__atlasList.GetItemFont(atlasIdx)
        font.SetWeight(weight)
        
        self.__atlasList.SetItemFont(atlasIdx, font)
        self.__atlasList.SetItemForegroundColour(atlasIdx, colour, colour) 
 
            
    def __onAtlasSelect(self, ev=None, atlasIdx=None, atlasDesc=None):
        """Called when the user selects an atlas in the atlas list, or
        the :meth:`selectAtlas` method is called.

        If a region list (a list of :class:`OverlayListWidget` items for every
        region in the atlas, to be displayed in the region list) has not yet
        been created, it is created - this is done asynchronously (via the
        :func:`async.idle` function), as it can take quite a long time for
        some of the atlases (e.g. the Talairach and Juelich).

        Then the region list is updated to show the regions for the newly
        selected atlas.
        """

        if ev is not None:
            atlasDesc  = ev.data
            atlasIdx   = ev.idx

        atlasPanelDisabled = False
        regionList         = self.__regionLists[atlasIdx]

        if regionList is None:

            # The region list for this atlas has not yet been
            # created. So we create the list, and then create
            # a widget for every region in the atlas. Some of
            # the atlases (Juelich and Talairach in particular)
            # have a large number of regions, so we create the
            # widgets asynchronously on the wx idle loop.
            regionList = elistbox.EditableListBox(
                self.__regionPanel,
                style=(elistbox.ELB_NO_ADD    |
                       elistbox.ELB_NO_REMOVE |
                       elistbox.ELB_NO_MOVE))
            regionList.Show(False)

            self.__regionLists[atlasIdx] = regionList

            def addToRegionList(label, i):

                # If the user kills this panel while
                # the region list is being updated,
                # suppress wx complaints.
                #
                # TODO You could make a chain of
                # async.idle functions. instead of
                # scheduling them all at once
                try:
                    regionList.Append(label.name)
                    widget = OverlayListWidget(regionList,
                                               atlasDesc.atlasID,
                                               i,
                                               self.__atlasPanel,
                                               self,
                                               label.index)
                    regionList.SetItemWidget(i, widget)
                    
                except wx.PyDeadObjectError:
                    pass

            log.debug('Creating region list for {} ({})'.format(
                atlasDesc.atlasID, id(regionList)))

            status.update(
                strings.messages[self, 'loadRegions'].format(atlasDesc.name),
                timeout=None)

            # Schedule addToRegionList on the
            # wx idle loop for every region.
            # Disable the panel while this is
            # occurring.
            atlasPanelDisabled = True
            self.enableAtlasPanel(False)
            for i, label in enumerate(atlasDesc.labels):
                async.idle(addToRegionList, label, i)

        # This function changes the displayed region
        # list. We schedule it on the wx idle loop,
        # so it will get called after the region list
        # has been populated (if it has not been
        # displayed before).
        def changeAtlasList():

            # See comment above about
            # suppressing wx complaints
            try:

                filterStr = self.__regionFilter.GetValue().lower().strip()
                regionList.ApplyFilter(filterStr, ignoreCase=True)

                self.__updateAtlasState(atlasIdx)

                status.update(strings.messages[self, 'regionsLoaded'].format(
                    atlasDesc.name))
                log.debug('Showing region list for {} ({})'.format(
                    atlasDesc.atlasID, id(regionList)))

                # Hide the currently
                # shown region list 
                old = self.__regionSizer.GetItem(1).GetWindow()
                if old is not None:
                    old.Show(False)

                regionList.Show(True)
                self.__regionSizer.Remove(1)
                self.__regionSizer.Insert(1,
                                          regionList,
                                          flag=wx.EXPAND,
                                          proportion=1)
                self.__regionSizer.Layout()

                if atlasPanelDisabled:
                    self.enableAtlasPanel()
                
            except wx.PyDeadObjectError:
                pass
 
        async.idle(changeAtlasList)


    def selectAtlas(self, atlasIdx, atlasDesc):
        """Selects the specified atlas. This method is used by
        :class:`OverlayListWidget` instances.

        :arg atlasIdx:  Index of the atlas in the atlas list.

        :arg atlasDesc: The :class:`.AtlasDescription` instance for the
                        atlas.
        """

        self.__atlasList.SetSelection(atlasIdx)
        self.__onAtlasSelect(atlasIdx=atlasIdx, atlasDesc=atlasDesc)


    def enableAtlasPanel(self, enable=True):
        """Disables/enables the :class:`.AtlasPanel` which contains this
        ``AtlasOverlayPanel``. This method is used by
        :class:`OverlayListWidget` instances.

        This method keeps a count of the number of times that it has been
        called - the count is increased every time a request is made
        to disable the ``AtlasPanel``, and decreased on requests to
        enable it. The ``AtlasPanel`` is only enabled when the count
        reaches 0.

        This ugly method solves an awkward problem - the ``AtlasOverlayPanel``
        disables the ``AtlasPanel`` when an atlas overlay is toggled on/off
        (via an ``OverlayListWidget``), and when an atlas region list is being
        generated (via the :meth:`__onAtlasSelect` method). If both of these
        things occur at the same time, the ``AtlasPanel`` could be prematurely
        re-enabled. This method overcomes this problem.
        """ 
        count = self.__atlasPanelEnableStack
        if enable:
            count -= 1

            if count <= 0:
                count = 0
                self.__atlasPanel.Enable()

        else:
            count += 1
            self.__atlasPanel.Disable()

        self.__atlasPanelEnableStack = count

        
class OverlayListWidget(wx.Panel):
    """``OverlayListWidget`` items are used by the :class:`AtlasOverlayPanel`
    in both the atlas list and the region list.

    For atlases, an ``OverlayListWidget`` contains a check box allowing the
    user to toggle the visibility of a summary (i.e. label) overlay for that
    atlas.

    For regions, an ``OverlayListWidget`` contains a check box and a button.
    The check box allows the user to toggle visibility of an atlas region
    overlay, and the button calls the :meth:`.AtlasPanel.locateRegion`
    method, allowing the user to locate the region.

    See the :class:`.AtlasPanel` class documentation, and the :mod:`.atlases`
    module for more details
    """

    
    def __init__(self,
                 parent,
                 atlasID,
                 listIdx,
                 atlasPanel,
                 atlasOvlPanel,
                 labelIdx=None):
        """Create an ``OverlayListWidget``.

        :arg parent:        The :mod:`wx` parent object - this is assumed to 
                            be an :class:`.EditableListBox`.
        
        :arg atlasID:       The atlas identifier.

        :arg listIdx:       The index of this ``OverlayListWidget`` in the
                            ``EditableListBox``.

        :arg atlasOvlPanel: The :class:`AtlasOverlayPanel` which created this
                            ``OverlayListWidget``.
        
        :arg atlasPanel:    The :class:`.AtlasPanel` which owns the
                            :class:`AtlasOverlayPanel` that created this
                            ``OverlayListWidget``.

        :arg labelIdx:      Label index of the region, if this
                            ``OverlatyListWidget`` corresponds to a region,
                            or ``None``  if it corresponds to an atlas.
        """

        wx.Panel.__init__(self, parent)
        
        self.__atlasID       = atlasID
        self.__atlasDesc     = atlases.getAtlasDescription(atlasID)
        self.__atlasPanel    = atlasPanel
        self.__atlasOvlPanel = atlasOvlPanel
        self.__atlasList     = parent
        self.__listIdx       = listIdx
        self.__labelIdx      = labelIdx

        self.__enableBox = wx.CheckBox(self)
        self.__enableBox.SetValue(False)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__enableBox, flag=wx.EXPAND)

        self.__enableBox.Bind(wx.EVT_CHECKBOX, self.__onEnable)
        
        if labelIdx is not None:
            self.__locateButton = wx.Button(self,
                                            label='+',
                                            style=wx.BU_EXACTFIT)
            self.__sizer.Add(self.__locateButton, flag=wx.EXPAND)

            self.__locateButton.Bind(wx.EVT_BUTTON, self.__onLocate)

            
    def SetEnableState(self, state):
        """Sets the enable overlay checkbox state to the specified state
        (``True`` or ``False``).
        """
        self.__enableBox.SetValue(state)

        
    def __onEnable(self, ev):
        """Called when the enable overlay checkbox is clicked. Calls the
        :meth:`.AtlasPanel.toggleOverlay` method, to toggle the overlay
        for the atlas/region associated with this ``OverlayListWidget``..
        """

        def onLoad():
            self.__atlasOvlPanel.enableAtlasPanel()

        self.__atlasOvlPanel.enableAtlasPanel(False)
        self.__atlasPanel.toggleOverlay(
            self.__atlasID,
            self.__labelIdx,
            self.__atlasDesc.atlasType == 'label',
            onLoad=onLoad)

        
    def __onLocate(self, ev):
        """Called when the locate region button is clicked only on
        ``OverlayListWidget`` items which are associated with an atlas
        region).

        Calls the :meth:`.AtlasPanel.locateRegion` method for the atlas/region
        associated with this ``OverlayListWidget``.
        """
        self.__atlasPanel.locateRegion(self.__atlasID, self.__labelIdx)
