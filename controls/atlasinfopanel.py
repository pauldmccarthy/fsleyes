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

import wx
import wx.html             as wxhtml

import pwidgets.elistbox   as elistbox

import fsl.fsleyes.panel   as fslpanel
import fsl.data.atlases    as atlases
import fsl.data.strings    as strings
import fsl.data.constants  as constants


log = logging.getLogger(__name__)


class AtlasInfoPanel(fslpanel.FSLEyesPanel):
    """The ``AtlasInfoPanel`` displays region information about the current
    :attr:`.DisplayContext.location` from a set of :mod:`.atlases` chosen
    by the user.
    
    An ``AtlasInfoPanel`` looks something like this:
    
    .. image:: images/atlasinfopanel.png
       :scale: 50%
       :align: center
    
    The ``AtlasInfoPanel`` contains two main sections:

      - A :class:`pwidgets.elistbox.EditableListBox` filled with
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
        destroyed. De-registers various property listeners and calls
        :meth:`FSLEyesPanel.destroy`.
        """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('location',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        
        fslpanel.FSLEyesPanel.destroy(self)


    def enableAtlasInfo(self, atlasID):
        """Enables information display for the atlas with the specified ID
        (see the :mod:`.atlases` module for details on atlas IDs).
        """
        self.__enabledAtlases[atlasID] = self.__atlasPanel.loadAtlas(atlasID,
                                                                     False)
        self.__locationChanged()

        
    def disableAtlasInfo(self, atlasID):
        """Disables information display for the atlas with the specified ID.
        """
        self.__enabledAtlases.pop(atlasID)
        self.__locationChanged()


    def __locationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.location` property changes.
        Updates the information shown in the HTML window.
        """
        
        text    = self.__infoPanel
        overlay = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        topText = None
        
        if len(atlases.listAtlases()) == 0:
            text.SetPage(strings.messages['AtlasInfoPanel.atlasDisabled'])
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

        opts = self._displayCtx.getOpts(overlay)
        loc  = self._displayCtx.location
        loc  = opts.transformCoords([loc], 'display', 'world')[0]
        
        # Three types of hyperlink:
        #   - one for complete (summary) label atlases,
        #   - one for a region label mask image
        #   - one for a region probability image
        #
        # The hrefs are formatted as:
        #
        #     imageType atlasID labelIdx
        #
        # where "imageType" is one of "summary", "label", or "prob",
        # and "labelIdx" is "None" for complete/summary atlases.
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


    def __infoPanelLinkClicked(self, ev):
        """Called when a hyperlink is clicked in the HTML window. Toggles
        the respective atlas overlay - see the
        :meth:`.AtlasPanel.toggleOverlay` method.
        """

        # Decode the href - see comments
        # inside __locationChanged method
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
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.location` changes. Refreshes the displayed
        atlas information (see :meth:`__locationChanged`), and adds a listener
        to the :attr:`.DisplayOpts.bounds` property so that, when it changes,
        the atlas information is refreshed.
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


class AtlasListWidget(wx.CheckBox):
    """An ``AtlasListWidget`` is a ``wx.CheckBox`` which is used
    by the :class:`AtlasInfoPanel`. An ``AtlasListWidget`` is shown
    alongside each atlas in the atlas list.

    Toggling the checkbox will add/remove information for the respective atlas
    (see :meth:`AtlasInfoPanel.enableAtlasInfo` and
    :meth:`AtlasInfoPanel.disableAtlasInfo`).
    """

    
    def __init__(self, parent, atlasInfoPanel, atlasID):
        """Create an ``AtlasListWidget``.

        :arg parent:         The :mod:`wx` parent object.
        
        :arg atlasInfoPanel: the :class:`AtlasInfoPanel` instance that owns
                             this ``AtlasListWidget``.
        
        :arg atlasID:        The atlas identifier associated with this
                             ``AtlasListWidget``.
        """

        wx.CheckBox.__init__(self, parent)

        self.__atlasID        = atlasID
        self.__atlasInfoPanel = atlasInfoPanel

        self.Bind(wx.EVT_CHECKBOX, self.__onEnable)

        
    def __onEnable(self, ev):
        """Called when this ``AtlasListWidget`` is clicked. Toggles
        information display for the atlas associated with this widget.
        """

        if self.GetValue():
            self.__atlasInfoPanel.enableAtlasInfo( self.__atlasID)
        else:
            self.__atlasInfoPanel.disableAtlasInfo(self.__atlasID)
