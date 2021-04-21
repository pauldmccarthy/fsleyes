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

import fsl.data.atlases                     as atlases
import fsl.utils.idle                       as idle
from   fsl.utils.platform import platform   as fslplatform

import fsleyes_widgets.elistbox             as elistbox
import fsleyes_widgets.placeholder_textctrl as plctext
import fsleyes_widgets.utils.status         as status
import fsleyes.panel                        as fslpanel
import fsleyes.strings                      as strings



log = logging.getLogger(__name__)


class AtlasOverlayPanel(fslpanel.FSLeyesPanel):
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

      - The *atlas list* - a :class:`fsleyes_widgets.elistbox.EditableListBox`
        with an entry, and an :class:`OverlayListWidget` for every available
        atlas.  The ``OverlayListWidget`` allows the user to turn on/off a
        summary overlay image for the atlas (see the section on :ref:`atlas
        panel overlays <atlas-panel-atlas-overlays>`).

      - The *region list* - an ``EditableListBox`` which contains one entry
        for every region in the atlas that is currently selected in the atlas
        list, and an ``OverlayListWidget`` alongside every region. The
        ``OverlayListWidget`` allows the user to navigate to a region, and
        to turn on/off a label or statistic/probabilistic region overlay.

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

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, atlasPanel.frame)

        # References to an EditableListBox
        # for each atlas, containing a list
        # of its regions. These are created
        # on-demand in the __onAtlasSelect
        # method.
        self.__regionLists = {}

        self.__atlasPanel      = atlasPanel
        self.__contentPanel    = wx.SplitterWindow(self,
                                                   style=wx.SP_LIVE_UPDATE)
        self.__atlasList       = elistbox.EditableListBox(
            self.__contentPanel,
            vgap=5,
            style=(elistbox.ELB_NO_ADD    |
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        self.__regionPanel     = wx.Panel(self.__contentPanel)
        self.__regionFilter    = plctext.PlaceholderTextCtrl(
            self.__regionPanel, placeholder='Search')

        self.__contentPanel.SetMinimumPaneSize(50)
        self.__contentPanel.SplitVertically(self.__atlasList,
                                            self.__regionPanel)
        self.__contentPanel.SetSashGravity(0.4)

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

        fslplatform.register(     self.name, self.__fslDirChanged)
        atlases.registry.register(self.name, self.__atlasAdded,   'add')
        atlases.registry.register(self.name, self.__atlasRemoved, 'remove')

        self.__buildAtlasList()

        self.__regionSizer.Layout()
        self.__sizer      .Layout()

        # Allow the atlas list
        # to be minimised
        self.__atlasList.SetMinSize((50, -1))

        self.SetMinSize(self.__sizer.GetMinSize())


    def destroy(self):
        """Performs some clean up operations. """
        fslplatform.deregister(self.name)
        fslpanel.FSLeyesPanel.destroy(self)


    def Enable(self, enable=True):
        """Enables/disables this ``AtlasOverlayPanel``. """

        self.__atlasList.Enable(enable)

        for atlasID, regionList in self.__regionLists.items():
            regionList.Enable(enable)


    def Disable(self):
        """Disables this ``AtlasOverlayPanel``. """
        self.Enable(False)


    def setOverlayState(self, atlasDesc, labelIdx, summary, state):
        """Updates the *enabled* state of the specified atlas overlay.

        This method is called by the :class:`.AtlasPanel` when an atlas overlay
        is added/removed to/from the :class:`.OverlayList`. It ensures that the
        :class:`OverlayListWidget` controls for every atlas, and every region,
        are up to date.
        """

        atlasIdx = self.__atlasList.IndexOf(atlasDesc)

        log.debug('Setting {}/{} overlay state to {}'.format(
            atlasDesc.atlasID, labelIdx, state))

        if labelIdx is None:
            widget = self.__atlasList.GetItemWidget(atlasIdx)
            widget.SetEnableState(state)
        else:

            regionList = self.__regionLists.get(atlasDesc.atlasID, None)
            if regionList is not None:
                regionList.GetItemWidget(labelIdx).SetEnableState(state)


    def __fslDirChanged(self, *a):
        """Called when the :attr:`.Platform.fsldir` changes. Refreshes
        the atlas list.
        """
        self.__buildAtlasList()


    def __atlasAdded(self, *a):
        """Called when a new atlas is added to the :class:`.AtlasRegistry`.
        Re-generates the atlas list.
        """
        self.__buildAtlasList()


    def __atlasRemoved(self, *a):
        """Called when an atlas is removed from the :class:`.AtlasRegistry`.
        Re-generates the atlas list.
        """
        self.__buildAtlasList()


    def __buildAtlasList(self):
        """Clears and recreates the atlas list. Also clears all existing
        region lists.
        """

        atlasDescs = atlases.listAtlases()

        # This method is called whenever any
        # atlases are added/removed. We want
        # to preserve any region lists for
        # atlases that are still in the atlas
        # registry.
        regionLists = dict(self.__regionLists)

        # If a region list is currently
        # being shown, clear it.
        regionList = self.__regionSizer.GetItem(1).GetWindow()
        if regionList is not None:
            regionList.Show(False)
            self.__regionSizer.Remove(1)
            self.__regionSizer.AddStretchSpacer()

        self.__regionLists = {}

        # Now clear and re-populate the atlas list
        self.__atlasList.Clear()
        for i, atlasDesc in enumerate(atlasDescs):

            self.__atlasList.Append(atlasDesc.name, atlasDesc)
            self.__updateAtlasState(atlasDesc)

            widget = OverlayListWidget(self.__atlasList,
                                       atlasDesc.atlasID,
                                       self.__atlasPanel,
                                       self)

            self.__atlasList.SetItemWidget(i, widget)

        # Restore references to region lists
        # for atlases that still exist
        for atlasID, regionList in regionLists.items():
            if atlases.hasAtlas(atlasID):
                self.__regionLists[atlasID] = regionList
            else:
                regionList.Destroy()

        self.__regionSizer.Layout()


    def __onRegionFilter(self, ev):
        """Called when the user enters some text in the region filter.

        Filters the region list (see the :meth:`.EditableListBox.ApplyFilter`
        method), and updates all items in the atlas list (see the
        :meth:`__updateAtlasState` method).
        """

        filterStr = self.__regionFilter.GetValue().lower().strip()

        for atlasDesc in atlases.listAtlases():

            self.__updateAtlasState(atlasDesc)

            listBox = self.__regionLists.get(atlasDesc.atlasID, None)

            if listBox is not None:
                listBox.ApplyFilter(filterStr, ignoreCase=True)


    def __updateAtlasState(self, atlasDesc):
        """Updates the state of the atlas list item which corresponds to the
        atlas with the specified identifier.

        If the atlas has regions which match the current region filter string,
        the atlas label font is set to bold. Otherwise (or if the region filter
        string is empty), the atlas label font is set to normal.
        """

        atlasIdx  = self.__atlasList.IndexOf(atlasDesc)
        filterStr = self.__regionFilter.GetValue().lower().strip()
        atlasDesc = self.__atlasList.GetItemData(atlasIdx)

        if filterStr == '':
            nhits = 0
        else:
            nhits = len([l for l in atlasDesc.labels
                         if filterStr in l.name.lower()])

        if nhits == 0:
            weight = wx.FONTWEIGHT_LIGHT
        else:
            weight = wx.FONTWEIGHT_BOLD

        font = self.__atlasList.GetItemFont(atlasIdx)
        font.SetWeight(weight)

        self.__atlasList.SetItemFont(atlasIdx, font)


    def __onAtlasSelect(self, ev=None, atlasDesc=None):
        """Called when the user selects an atlas in the atlas list, or
        the :meth:`selectAtlas` method is called.

        If a region list (a list of :class:`OverlayListWidget` items for every
        region in the atlas, to be displayed in the region list) has not yet
        been created, it is created - this is done asynchronously (via the
        :func:`idle.idle` function), as it can take quite a long time for
        some of the atlases (e.g. the Talairach and Juelich).

        Then the region list is updated to show the regions for the newly
        selected atlas.
        """

        if ev is not None:
            atlasDesc = ev.data

        regionList         = self.__regionLists.get(atlasDesc.atlasID, None)
        atlasPanelDisabled = regionList is None

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

                self.__updateAtlasState(atlasDesc)

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
                    self.__atlasPanel.enableAtlasPanel()

            except RuntimeError:
                pass

        if regionList is None:

            # The region list for this atlas has not yet been
            # created. So we create the list, and then create
            # a widget for every region in the atlas. Some of
            # the atlases (Juelich and Talairach in particular)
            # have a large number of regions, so we create the
            # widgets asynchronously on the wx idle loop.
            regionList = elistbox.EditableListBox(
                self.__regionPanel,
                vgap=5,
                style=(elistbox.ELB_NO_ADD    |
                       elistbox.ELB_NO_REMOVE |
                       elistbox.ELB_NO_MOVE))
            regionList.Show(False)

            self.__regionLists[atlasDesc.atlasID] = regionList

            # Add blockSize labels, starting from label[i],
            # to the region list. Then, if necessary,
            # schedule more labels be added, starting from
            # label[i + blockSize].
            blockSize = 20
            nlabels   = len(atlasDesc.labels)

            def addToRegionList(start):

                # If the user kills this panel while
                # the region list is being updated,
                # suppress wx complaints.
                try:

                    for i in range(start, min(start + blockSize, nlabels)):
                        label = atlasDesc.labels[i]
                        widget = OverlayListWidget(regionList,
                                                   atlasDesc.atlasID,
                                                   self.__atlasPanel,
                                                   self,
                                                   label.index)
                        regionList.Append(label.name, extraWidget=widget)

                    if i < nlabels - 1: idle.idle(addToRegionList, i + 1)
                    else:               idle.idle(changeAtlasList)

                except RuntimeError:
                    pass

            log.debug('Creating region list for {} ({})'.format(
                atlasDesc.atlasID, id(regionList)))

            status.update(
                strings.messages[self, 'loadRegions'].format(atlasDesc.name),
                timeout=None)

            # Schedule addToRegionList on the
            # wx idle loop for the first region.
            # The function will recursively
            # schedule itself to run for subsequent
            # regions.
            #
            # Disable the panel while this is
            # occurring.

            atlasPanelDisabled = True

            self.__atlasPanel.enableAtlasPanel(False)
            idle.idle(addToRegionList, 0)
        else:
            idle.idle(changeAtlasList)


    def selectAtlas(self, atlasDesc):
        """Selects the specified atlas. This method is used by
        :class:`OverlayListWidget` instances.

        :arg atlasID:   The atlas identifier
        """

        atlasIdx = self.__atlasList.IndexOf(atlasDesc)

        self.__atlasList.SetSelection(atlasIdx)
        self.__onAtlasSelect(atlasDesc=atlasDesc)


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
                 atlasPanel,
                 atlasOvlPanel,
                 labelIdx=None):
        """Create an ``OverlayListWidget``.

        :arg parent:        The :mod:`wx` parent object - this is assumed to
                            be an :class:`.EditableListBox`.

        :arg atlasID:       The atlas identifier.

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

            if not self or \
               not self.__atlasOvlPanel or \
               self.__atlasOvlPanel.destroyed:
                return

            self.__atlasPanel.enableAtlasPanel()

        def onError(e):
            message = strings.messages[self.__atlasOvlPanel, 'loadAtlasError']
            message = message.format(
                self.__atlasID, '{} ({})'.format(type(e).__name__, str(e)))
            wx.MessageDialog(
                self.GetTopLevelParent(),
                message=message,
                style=(wx.ICON_EXCLAMATION | wx.OK)).ShowModal()

            self.__atlasPanel.enableAtlasPanel()
            self.__enableBox.SetValue(
                self.__atlasPanel.getOverlayState(
                    self.__atlasID,
                    self.__labelIdx,
                    self.__atlasDesc.atlasType == 'label'))

        self.__atlasPanel.enableAtlasPanel(False)

        log.debug('Toggling atlas {}'.format(self.__atlasID))

        self.__atlasPanel.toggleOverlay(
            self.__atlasID,
            self.__labelIdx,
            self.__atlasDesc.atlasType == 'label',
            onLoad=onLoad,
            onError=onError)

        if self.__labelIdx is None:
            self.__atlasOvlPanel.selectAtlas(self.__atlasDesc)


    def __onLocate(self, ev):
        """Called when the locate region button is clicked only on
        ``OverlayListWidget`` items which are associated with an atlas
        region).

        Calls the :meth:`.AtlasPanel.locateRegion` method for the atlas/region
        associated with this ``OverlayListWidget``.
        """
        self.__atlasPanel.locateRegion(self.__atlasID, self.__labelIdx)
