#!/usr/bin/env python
#
# atlasinfopanel.py - The AtlasInfoPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`AtlasInfoPanel`, which is a sub-panel
that is used by the :class:`.AtlasPanel`.
"""

import logging

import numpy                              as np
import                                       wx
import wx.html                            as wxhtml

import fsleyes_widgets.elistbox           as elistbox
import fsleyes.panel                      as fslpanel
import fsleyes.strings                    as strings
import fsl.utils.idle                     as idle
from   fsl.utils.platform import platform as fslplatform
import fsl.data.atlases                   as atlases
import fsl.data.constants                 as constants


log = logging.getLogger(__name__)


class AtlasInfoPanel(fslpanel.FSLeyesPanel):
    """The ``AtlasInfoPanel`` displays region information about the current
    :attr:`.DisplayContext.location` from a set of :mod:`.atlases` chosen
    by the user.

    An ``AtlasInfoPanel`` looks something like this:

    .. image:: images/atlasinfopanel.png
       :scale: 50%
       :align: center

    The ``AtlasInfoPanel`` contains two main sections:

      - A :class:`fsleyes_widgets.elistbox.EditableListBox` filled with
        :class:`AtlasListWidget` controls, one for each available atlas.
        The user is able to choose which atlases to show information for.

      - A ``wx.html.HtmlWindow`` which contains information for each
        selected atlas. The information contains hyperlinks for each atlas,
        and each region which, when clicked, toggles on/off relevant
        atlas overlays (see the :meth:`.AtlasPanel.toggleOverlay` method).
    """


    def __init__(self, parent, overlayList, displayCtx, atlasPanel):
        """Create an ``AtlasInfoPanel``.

        :arg parent:      the :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg atlasPanel:  The :class:`.AtlasPanel` instance that has created
                          this ``AtlasInfoPanel``.
        """
        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, atlasPanel.frame)

        self.__enabledAtlases = {}
        self.__atlasPanel     = atlasPanel
        self.__contentPanel   = wx.SplitterWindow(self,
                                                  style=wx.SP_LIVE_UPDATE)
        self.__infoPanel      = wxhtml.HtmlWindow(self.__contentPanel)
        self.__atlasList      = elistbox.EditableListBox(
            self.__contentPanel,
            vgap=5,
            style=(elistbox.ELB_NO_ADD    |
                   elistbox.ELB_NO_REMOVE |
                   elistbox.ELB_NO_MOVE))

        # Force the HTML info panel to
        # use the default font size
        self.__infoPanel.SetStandardFonts(self.GetFont().GetPointSize())

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__contentPanel, flag=wx.EXPAND, proportion=1)
        self.SetSizer(self.__sizer)

        self.__contentPanel.SetMinimumPaneSize(50)
        self.__contentPanel.SplitVertically(self.__atlasList,
                                            self.__infoPanel)
        self.__contentPanel.SetSashGravity(0.4)

        # The info panel contains clickable links
        # for the currently displayed regions -
        # when a link is clicked, the location
        # is centred at the corresponding region
        self.__infoPanel.Bind(wxhtml.EVT_HTML_LINK_CLICKED,
                              self.__infoPanelLinkClicked)

        fslplatform     .register(self.name,
                                  self.__fslDirChanged)
        atlases.registry.register(self.name,
                                  self.__atlasAdded,
                                  topic='add')
        atlases.registry.register(self.name,
                                  self.__atlasRemoved,
                                  topic='remove')

        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('location',
                                self.name,
                                self.__locationChanged)

        self.__atlasList.SetMinSize((50, 60))
        self.__infoPanel.SetMinSize((50, 60))
        self.SetMinSize(self.__sizer.GetMinSize())

        self.__buildAtlasList()
        self.__selectedOverlayChanged()

        # Enable the Harvard/Oxford
        # atlases by default. We do this
        # asynchronously because methods
        # on the AtlasPanel will be called,
        # and the AtlasPanel may not have
        # finished initialising itself.
        enable = ['harvardoxford-cortical', 'harvardoxford-subcortical']
        enable = [e for e in enable if atlases.hasAtlas(e)]
        for i, e in enumerate(enable):
            refresh = i == len(enable) - 1
            idle.idle(self.enableAtlasInfo, e, refresh=refresh)


    def destroy(self):
        """Must be called when this :class:`AtlasInfoPanel` is to be
        destroyed. De-registers various property listeners and calls
        :meth:`FSLeyesPanel.destroy`.
        """

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('location',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)

        atlases.registry.deregister(self.name, 'add')
        atlases.registry.deregister(self.name, 'remove')
        fslplatform     .deregister(self.name)

        fslpanel.FSLeyesPanel.destroy(self)


    def enableAtlasInfo(self, atlasID, refresh=True):
        """Enables information display for the atlas with the specified ID
        (see the :mod:`.atlases` module for details on atlas IDs).

        If ``refresh`` is ``True`` (the default), the HTML information panel
        is updated.
        """

        listWidget = self.__atlasList.GetItemWidget(
            self.__atlasList.IndexOf(atlasID))

        def onLoad(atlas):

            if not self or self.destroyed:
                return

            self.__enabledAtlases[atlasID] = atlas

            listWidget.SetValue(True)

            if refresh:
                self.__locationChanged()

            self.__atlasPanel.enableAtlasPanel()

        def onError(e):

            if not self or self.destroyed:
                return

            message = strings.messages[self, 'loadAtlasError']
            message = message.format(
                atlasID, '{} ({})'.format(type(e).__name__, str(e)))
            wx.MessageDialog(
                self.GetTopLevelParent(),
                message=message,
                style=(wx.ICON_EXCLAMATION | wx.OK)).ShowModal()

            listWidget.SetValue(False)
            self.__atlasPanel.enableAtlasPanel()

        self.__atlasPanel.enableAtlasPanel(False)
        self.__atlasPanel.loadAtlas(atlasID,
                                    summary=False,
                                    onLoad=onLoad,
                                    onError=onError,
                                    matchResolution=False)


    def disableAtlasInfo(self, atlasID):
        """Disables information display for the atlas with the specified ID.
        """

        # We set the elistbox client data
        # to the atlas ID, so we can get
        # the item index by atlasID here
        listWidget = self.__atlasList.GetItemWidget(
            self.__atlasList.IndexOf(atlasID))

        self.__enabledAtlases.pop(atlasID)
        self.__locationChanged()

        listWidget.SetValue(False)


    def __fslDirChanged(self, *a):
        """Called when the :attr:`.Platform.fsldir` changes. Refreshes
        the atlas list.
        """
        self.__buildAtlasList()
        self.__locationChanged()


    def __atlasAdded(self, registry, topic, atlasDesc):
        """Called when a new atlas is added to the :class:`.AtlasRegistry`.
        Re-generates the atlas list.
        """
        self.__buildAtlasList()
        self.__locationChanged()


    def __atlasRemoved(self, registry, topic, atlasDesc):
        """Called when an atlas is removed from the :class:`.AtlasRegistry`.
        Re-generates the atlas list.
        """
        self.__buildAtlasList()
        self.__locationChanged()


    def __buildAtlasList(self):
        """Clears and then builds the list of available atlases. The
        This is performed asynchronously, via the :func:`.idle.run` function,
        although the atlas list widget is updated on the ``wx`` idle loop.
        """

        # This method gets called whenever atlases
        # are added to/from the list.
        # We want to preserve the 'enabled' state of
        # any atlases that are still present in the
        # atlas registry.
        enabledAtlases = dict(self.__enabledAtlases)

        self.__enabledAtlases = {}

        self.__atlasList.Clear()

        atlasDescs = atlases.listAtlases()

        for i, atlasDesc in enumerate(atlasDescs):

            atlasID = atlasDesc.atlasID

            self.__atlasList.Append(atlasDesc.name, atlasID)

            enabled = atlasID in enabledAtlases
            widget  = AtlasListWidget(self.__atlasList,
                                      i,
                                      self,
                                      atlasID,
                                      enabled=enabled)

            self.__atlasList.SetItemWidget(i, widget)

            if enabled:
                self.__enabledAtlases[atlasID] = enabledAtlases[atlasID]


    def __locationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.location` property changes.
        Updates the information shown in the HTML window.
        """

        text    = self.__infoPanel
        overlay = self.displayCtx.getReferenceImage(
            self.displayCtx.getSelectedOverlay())

        topText = None

        if self.__atlasList.GetCount() == 0:
            text.SetPage(strings.messages['AtlasInfoPanel.atlasDisabled'])
            return

        if len(self.overlayList) == 0:
            text.SetPage(strings.messages['AtlasInfoPanel.noOverlays'])
            return

        if overlay is None or \
           overlay.getXFormCode() != constants.NIFTI_XFORM_MNI_152:
            topText = strings.messages['AtlasInfoPanel.notMNISpace']
            topText = '<font color="red">{}</font>'.format(topText)

        if len(self.__enabledAtlases) == 0:
            text.SetPage(strings.messages['AtlasInfoPanel.chooseAnAtlas'])
            return

        lines = []

        if topText is not None:
            lines.append(topText)

        if overlay is None:
            text.SetPage('<br>'.join(lines))
            text.Refresh()
            return

        opts = self.displayCtx.getOpts(overlay)
        loc  = self.displayCtx.location
        loc  = opts.transformCoords([loc], 'display', 'world')[0]

        # Three types of hyperlink:
        #   - one for complete (summary) label atlases,
        #   - one for a region label mask image
        #   - one for a region statistic/probability image
        #
        # The hrefs are formatted as:
        #
        #     imageType atlasID labelIdx
        #
        # where "imageType" is one of "summary", "label", or "stat"
        # and "labelIdx" is "None" for summary atlases.
        titleTemplate = '<b>{}</b> (<a href="summary {} {}">Show/Hide</a>)'
        labelTemplate = '{} (<a href="label {} {}">Show/Hide</a>)'

        statTemplate  = '{}{} {} (<a href="stat {} {}">Show/Hide</a>)'

        for atlasID in self.__enabledAtlases:

            atlas = self.__enabledAtlases[atlasID]

            lines.append(titleTemplate.format(atlas.desc.name, atlasID, None))

            if isinstance(atlas, atlases.StatisticAtlas):
                values = atlas.values(loc)

                if len(values) == 0:
                    continue

                vallabels = zip(values, atlas.desc.labels)

                for val, label in reversed(sorted(vallabels)):
                    if np.abs(val) < atlas.desc.lower:
                        continue
                    fmt = '{{:0.{}f}}'.format(atlas.desc.precision)
                    val = fmt.format(val)
                    lines.append(statTemplate.format(val,
                                                     atlas.desc.units,
                                                     label.name,
                                                     atlasID,
                                                     label.index))

            elif isinstance(atlas, atlases.LabelAtlas):

                labelVal = atlas.label(loc)

                if labelVal is None:
                    continue

                label = atlas.find(value=labelVal)

                lines.append(labelTemplate.format(label.name,
                                                  atlasID,
                                                  label.index))

        text.SetPage('<br>'.join(lines))

        text.Refresh()


    def __infoPanelLinkClicked(self, ev):
        """Called when a hyperlink is clicked in the HTML window. Toggles
        the respective atlas overlay - see the
        :meth:`.AtlasPanel.toggleOverlay` method.
        """

        # Decode the href - see comments
        # inside __locationChanged method
        showType, atlasID, labelIndex = ev.GetLinkInfo().GetHref().split()

        try:               labelIndex = int(labelIndex)
        except ValueError: labelIndex = None

        # showType is one of 'stat', 'label', or
        # 'summary'; the summary parameter controls
        # whether a probabilstic/stat or label image
        # is loaded
        summary = showType != 'stat'

        def onLoad():
            self.__atlasPanel.Enable()

        def onError(e):
            message = strings.messages[self, 'loadAtlasError']
            message = message.format(
                atlasID, '{} ({})'.format(type(e).__name__, str(e)))
            wx.MessageDialog(
                self.GetTopLevelParent(),
                message=message,
                style=(wx.ICON_EXCLAMATION | wx.OK)).ShowModal()
            self.__atlasPanel.Enable()

        self.__atlasPanel.Disable()
        self.__atlasPanel.toggleOverlay(atlasID,
                                        labelIndex,
                                        summary,
                                        onLoad=onLoad,
                                        onError=onError)


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.location` changes. Refreshes the displayed
        atlas information (see :meth:`__locationChanged`), and adds a listener
        to the :attr:`.DisplayOpts.bounds` property so that, when it changes,
        the atlas information is refreshed.
        """

        if len(self.overlayList) == 0:
            self.__locationChanged()
            return

        selOverlay = self.displayCtx.getSelectedOverlay()

        for ovl in self.overlayList:

            opts = self.displayCtx.getOpts(ovl)

            # Add a listener to the bounds property for
            # the selected overlay. Bounds is used as a
            # proxy for the overlay referene image (e.g.
            # Mesh overlays) - if the reference image
            # changes, the overlay may have been moved
            # into MNI152 space, so we can display
            # atlas info.
            if ovl == selOverlay:
                opts.addListener('bounds',
                                 self.name,
                                 self.__locationChanged,
                                 overwrite=True)
            else:
                opts.removeListener('bounds', self.name)

        self.__locationChanged()


class AtlasListWidget(wx.CheckBox):
    """An ``AtlasListWidget`` is a ``wx.CheckBox`` which is used
    by the :class:`AtlasInfoPanel`. An ``AtlasListWidget`` is shown
    alongside each atlas in the atlas list.

    Toggling the checkbox will add/remove information for the respective atlas
    (see :meth:`AtlasInfoPanel.enableAtlasInfo` and
    :meth:`AtlasInfoPanel.disableAtlasInfo`).
    """


    def __init__(self,
                 parent,
                 listIdx,
                 atlasInfoPanel,
                 atlasID,
                 enabled=False):
        """Create an ``AtlasListWidget``.

        :arg parent:         The :mod:`wx` parent object, assumed to be an
                             :class:`.EditableListBox`.

        :arg listIdx:        Index of this ``AtlasListWidget`` in the
                             ``EditableListBox``.

        :arg atlasInfoPanel: the :class:`AtlasInfoPanel` instance that owns
                             this ``AtlasListWidget``.

        :arg atlasID:        The atlas identifier associated with this
                             ``AtlasListWidget``.

        :arg enabled:        Initial checkbox state (defaults to False).
        """

        wx.CheckBox.__init__(self, parent)

        self.__atlasList      = parent
        self.__atlasID        = atlasID
        self.__listIdx        = listIdx
        self.__atlasInfoPanel = atlasInfoPanel

        self.SetValue(enabled)

        self.Bind(wx.EVT_CHECKBOX, self.__onEnable)

        self.SetMinSize(self.GetBestSize())


    def __onEnable(self, ev):
        """Called when this ``AtlasListWidget`` is clicked. Toggles
        information display for the atlas associated with this widget.
        """

        self.__atlasList.SetSelection(self.__listIdx)

        if self.GetValue():
            self.__atlasInfoPanel.enableAtlasInfo( self.__atlasID)
        else:
            self.__atlasInfoPanel.disableAtlasInfo(self.__atlasID)
