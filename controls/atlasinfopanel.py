#!/usr/bin/env python
#
# atlasinfopanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx
import wx.html             as wxhtml

import pwidgets.elistbox   as elistbox

import fsl.fsleyes.panel   as fslpanel
import fsl.data.atlases    as atlases
import fsl.data.strings    as strings
import fsl.data.constants  as constants


log = logging.getLogger(__name__)


class AtlasListWidget(wx.CheckBox):

    def __init__(self, parent, atlasInfoPanel, atlasID):

        wx.CheckBox.__init__(self, parent)

        self.atlasID        = atlasID
        self.atlasInfoPanel = atlasInfoPanel

        self.Bind(wx.EVT_CHECKBOX, self.onEnable)

        
    def onEnable(self, ev):

        if self.GetValue():
            self.atlasInfoPanel.enableAtlasInfo(self.atlasID)
        else:
            self.atlasInfoPanel.disableAtlasInfo(self.atlasID)


# Info panel, containing atlas-based regional
# proportions/labels for the current location

# Atlas list, containing a list of atlases
# that the user can choose from
class AtlasInfoPanel(fslpanel.FSLEyesPanel):

    def __init__(self, parent, overlayList, displayCtx, atlasPanel):
        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self.__enabledAtlases = {}
        self.__atlasPanel     = atlasPanel
        self.__contentPanel   = wx.SplitterWindow(self,
                                                  style=wx.SP_LIVE_UPDATE)
        self.__infoPanel      = wxhtml.HtmlWindow(self.__contentPanel)
        self.__atlasList      = elistbox.EditableListBox(
            self.__contentPanel,
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
        
        for i, atlasDesc in enumerate(atlases.listAtlases()):
            
            self.__atlasList.Append(atlasDesc.name, atlasDesc.atlasID)
            widget = AtlasListWidget(self.__atlasList,
                                     self,
                                     atlasDesc.atlasID)
            self.__atlasList.SetItemWidget(i, widget)        

        # The info panel contains clickable links
        # for the currently displayed regions -
        # when a link is clicked, the location
        # is centred at the corresponding region
        self.__infoPanel.Bind(wxhtml.EVT_HTML_LINK_CLICKED,
                              self.__infoPanelLinkClicked)

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('location',
                                self._name,
                                self.__locationChanged)

        self.__selectedOverlayChanged()
        self.Layout()

        self.SetMinSize(self.__sizer.GetMinSize())

        
    def destroy(self):
        """Must be called when this :class:`AtlasInfoPanel` is to be
        destroyed. De-registers various property listeners.
        """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('location',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        
        fslpanel.FSLEyesPanel.destroy(self)


    def enableAtlasInfo(self, atlasID):
        self.__enabledAtlases[atlasID] = self.__atlasPanel.loadAtlas(atlasID,
                                                                     False)
        self.__locationChanged()

        
    def disableAtlasInfo(self, atlasID):
        self.__enabledAtlases.pop(atlasID)
        self.__atlasPanel.clearAtlas(atlasID, False)
        self.__locationChanged()


    def __infoPanelLinkClicked(self, ev):

        showType, atlasID, labelIndex = ev.GetLinkInfo().GetHref().split()
        
        try:    labelIndex = int(labelIndex)
        except: labelIndex = None

        # showType is one of 'prob', 'label', or
        # 'summary'; the summary parameter controls
        # whether a probabilstic or label image
        # is loaded
        summary = showType != 'prob'

        self.__atlasPanel.toggleOverlay(atlasID, labelIndex, summary)


    def __selectedOverlayChanged(self, *a):
        """
        """

        if len(self._overlayList) == 0:
            self.__locationChanged()
            return

        selOverlay = self._displayCtx.getSelectedOverlay()

        for ovl in self._overlayList:

            opts = self._displayCtx.getOpts(ovl)

            if ovl == selOverlay:
                opts.addListener('bounds',
                                 self._name,
                                 self.__locationChanged,
                                 overwrite=True)
            else:
                opts.removeListener('bounds', self._name)

        self.__locationChanged()


    def __locationChanged(self, *a):
        
        text    = self.__infoPanel
        overlay = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())
        
        if len(atlases.listAtlases()) == 0:
            text.SetPage(strings.messages['AtlasInfoPanel.atlasDisabled'])
            return

        if overlay is None:
            text.SetPage(strings.messages['AtlasInfoPanel.noReference'])
            return 

        if overlay.getXFormCode() != constants.NIFTI_XFORM_MNI_152:
            text.SetPage(strings.messages['AtlasInfoPanel.notMNISpace'])
            return

        if len(self.__enabledAtlases) == 0:
            text.SetPage(strings.messages['AtlasInfoPanel.chooseAnAtlas'])
            return

        opts = self._displayCtx.getOpts(overlay)
        loc  = self._displayCtx.location
        loc  = opts.transformCoords([loc], 'display', 'world')[0]

        lines         = []
        titleTemplate = '<b>{}</b> (<a href="summary {} {}">Show/Hide</a>)'
        labelTemplate = '{} (<a href="label {} {}">Show/Hide</a>)'
        probTemplate  = '{:0.1f}% {} (<a href="prob {} {}">Show/Hide</a>)'

        for atlasID in self.__enabledAtlases:

            atlas = self.__enabledAtlases[atlasID]

            lines.append(titleTemplate.format(atlas.desc.name, atlasID, None))

            if isinstance(atlas, atlases.ProbabilisticAtlas):
                proportions = atlas.proportions(loc)

                for label, prop in zip(atlas.desc.labels, proportions):
                    if prop == 0.0:
                        continue
                    lines.append(probTemplate.format(prop,
                                                     label.name,
                                                     atlasID,
                                                     label.index,
                                                     atlasID,
                                                     label.index))
            
            elif isinstance(atlas, atlases.LabelAtlas):
                
                labelVal = atlas.label(loc)
                label    = atlas.desc.labels[int(labelVal)]
                lines.append(labelTemplate.format(label.name,
                                                  atlasID,
                                                  label.index,
                                                  atlasID,
                                                  label.index))

        text.SetPage('<br>'.join(lines))

        text.Refresh()
