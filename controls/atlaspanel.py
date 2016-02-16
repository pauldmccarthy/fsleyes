#!/usr/bin/env python
#
# atlaspanel.py - The AtlasPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`AtlasPanel`, a *FSLeyes control* panel
which allows the user to browse the FSL atlas images. See the
:mod:`~fsl.fsleyes` package documentation for more details on control panels,
and the :mod:`.atlases` module for more details on the atlases available in
FSL.
"""


import          logging

import numpy as np
import          wx

import pwidgets.notebook as notebook

import fsl.data.image    as fslimage
import fsl.data.atlases  as atlases
import fsl.data.strings  as strings
import fsl.utils.status  as status
import fsl.utils.async   as async
import fsl.fsleyes.panel as fslpanel
import                      atlasoverlaypanel
import                      atlasinfopanel 


log = logging.getLogger(__name__)


class AtlasPanel(fslpanel.FSLEyesPanel):
    """An ``AtlasPanel`` is a :class:`.FSLEyesPanel` which allows the user to
    view atlas information, and to browse through the atlases that come
    shipped with FSL. The ``AtlasPanel`` interface is provided by two
    sub-panels, which are displayed in a :class:`pwidgets.Notebook` panel. The
    ``AtlasPanel`` itself provides a number of convenience methods that are
    used by these sub-panels:


    =========================== =============================================
    :class:`.AtlasInfoPanel`    Displays information for the current
                                :attr:`.DisplayContext.location` from atlases
                                selected by the user.
    :class:`.AtlasOverlayPanel` Allows the user to search through all atlases
                                for specific regions, and to toggle on/off
                                overlays for those regions.
    =========================== =============================================


    **Loading atlases**


    The :class:`AtlasPanel` class provides the :meth:`loadAtlas` method, which
    is used by sub-panels to load atlas images.

    
    .. _atlas-panel-atlas-overlays:
    
    **Toggling atlas overlays**


    Both of the sub-panels allow the user to add/remove overlays to/from the
    :class:`.OverlayList`. The following overlay types can be added:

      - A complete summary :class:`.LabelAtlas`, which is a 3D image where
        each region has a discrete integer label. These images are added with
        a :attr:`.Display.overlayType` of ``label``.

      - A mask image containing a single region, extracted from a
        :class:`.LabelAtlas`. These images are added with a
        :attr:`.Display.overlayType` of ``mask``.

      - A 3D image containing the probabilty image for a single region,
        extracted from a :class:`.ProbabilisticAtlas`. These images are added
        with a :attr:`.Display.overlayType` of ``volume``.


    The following methods allow these overlays to be toggled on/off, and to
    query their state:

    .. autosummary::
       :nosignatures:

       toggleOverlay
       getOverlayName
       getOverlayState


    .. _atlas-panel-overlay-names:
    
    **Atlas overlay names**


    When an atlas overlay is added, its :attr:`.Image.name` (and subsequently
    its :attr:`.Display.name`) are set to a name which has the following
    structure::

        atlasID/overlayType/regionName

    where:

      - ``atlasID`` is the atlas identifier (see the :mod:`.atlases` module).
    
      - ``overlayType`` is either ``label`` or ``prob``, depending on whether
        the overlay is a discrete label image, or a probaility image.
    
      - ``regionName`` is the name of the region, or ``all`` if the overlay
        is a complete :class:`.LabelAtlas`.


    .. image:: images/atlaspanel_overlay_names.png
       :scale: 50%
       :align: center
    

    
    This name is used by the ``AtlasPanel`` to identify the overlay in the
    :class:`.OverlayList`.

    
    .. warning:: If the name of these overlays is changed, the ``AtlasPanel``
                 will not be able to find them in the :class:`.OverlayList`,
                 and the :meth:`toggleOverlay` and :meth:`getOverlayState`
                 methods will stop working properly.  So don't change the
                 atlas overlay names!


    **Locating regions**


    Finally, the :meth:`locateRegion` method allows the
    :attr:`.DisplayContext.location` to be moved to the location of a specific
    region in a specific atlas.
    """


    def __init__(self, parent, overlayList, displayCtx):
        """Create an ``AtlasPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        # Cache of loaded atlases
        # and enabled atlas overlays
        self.__enabledOverlays = {}
        self.__loadedAtlases   = {}

        self.__notebook = notebook.Notebook(self)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__notebook, flag=wx.EXPAND, proportion=1)
 
        self.SetSizer(self.__sizer)

        self.__infoPanel = atlasinfopanel.AtlasInfoPanel(
            self.__notebook, overlayList, displayCtx, self)

        # Overlay panel, containing a list of regions,
        # allowing the user to add/remove overlays
        self.__overlayPanel = atlasoverlaypanel.AtlasOverlayPanel(
            self.__notebook, overlayList, displayCtx, self)
        
        self.__notebook.AddPage(self.__infoPanel,
                                strings.titles[self.__infoPanel])
        self.__notebook.AddPage(self.__overlayPanel,
                                strings.titles[self.__overlayPanel])

        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__overlayListChanged)

        self.Layout()
        self.SetMinSize(self.__sizer.GetMinSize())


    def destroy(self):
        """Must be called on when this ``AtlasPanel`` is no longer needed.

        Calls the ``destroy`` methods of the :class:`.AtlasInfoPanel` and
        :class:`.AtlasOverlayPanel`, and then calls
        :meth:`.FSLEyesPanel.destroy`.
        """
        self.__loadedAtlases   = None
        self.__enabledOverlays = None
        self.__infoPanel     .destroy()
        self.__overlayPanel  .destroy()
        fslpanel.FSLEyesPanel.destroy(self)


    def loadAtlas(self, atlasID, summary, onLoad=None):
        """Loads the atlas image with the specified ID. The atlas is loaded
        asynchronously (via the :mod:`.async` module), as it can take some
        time. Use the `onLoad` argument if you need to do something when the
        atlas has been loaded.

        :arg onLoad: Optional. A function which is called when the atlas has
                     been loaded.

        See the :func:`.atlases.loadAtlas` function for details on the other
        arguments.
        """

        desc = atlases.getAtlasDescription(atlasID)

        if desc.atlasType == 'summary':
            summary = True

        atlas = self.__loadedAtlases.get((atlasID, summary), None)

        if atlas is None:
            
            log.debug('Loading atlas {}/{}'.format(
                atlasID, 'label' if summary else 'prob'))

            status.update('Loading atlas {}...'.format(atlasID), timeout=None)

            def load():
            
                atlas = atlases.loadAtlas(atlasID, summary)
                self.__loadedAtlases[atlasID, summary] = atlas

                status.update('Atlas {} loaded.'.format(atlasID))                    

                if onLoad is not None:
                    async.idle(onLoad, atlas)

            async.run(load)

        # If the atlas has already been loaded,
        # pass it straight to the onload function
        elif onLoad is not None:
            onLoad(atlas)
                    


    def getOverlayName(self, atlasID, labelIdx, summary):
        """Returns a name to be used for the specified atlas (see the section
        on :ref:`atlas names <atlas-panel-overlay-names>`).

        :arg atlasID:  Atlas identifier
        
        :arg labelIdx: Label index, or ``None`` for a complete atlas.
        
        :arg summary:  ``True`` corresponds to a label atlas, ``False`` to a
                       probabilistic atlas.
        """
        atlasDesc = atlases.getAtlasDescription(atlasID)

        if atlasDesc.atlasType == 'summary' or labelIdx is None:
            summary = True

        if summary: overlayType = 'label'
        else:       overlayType = 'prob'

        if labelIdx is None:
            overlayName = '{}/{}/all'.format(atlasID, overlayType)
        else:
            overlayName = '{}/{}/{}' .format(atlasID,
                                             overlayType,
                                             atlasDesc.labels[labelIdx].name)
 
        return overlayName, summary

    
    def getOverlayState(self, atlasID, labelIdx, summary):
        """Returns ``True`` if the specified atlas overlay is in the
        :class:`.OverlayList`, ``False`` otherwise.  See
        :meth:`getOverlayName` for details on the arguments.
        """

        name, _ = self.getOverlayName(atlasID, labelIdx, summary)
        return self._overlayList.find(name) is not None
    

    def toggleOverlay(self, atlasID, labelIdx, summary):
        """Adds or removes the specified overlay to/from the
        :class:`.OverlayList`. See :meth:`getOverlayName` for details on the
        arguments.
        """

        atlasDesc            = atlases.getAtlasDescription(atlasID)
        overlayName, summary = self.getOverlayName(atlasID, labelIdx, summary)
        overlay              = self._overlayList.find(overlayName)
 
        if overlay is not None:
            
            self._overlayList.disableListener('overlays', self._name)
            self._overlayList.remove(overlay)
            self._overlayList.enableListener('overlays', self._name)

            self.__enabledOverlays.pop(overlayName, None)
            self.__overlayPanel.setOverlayState(
                atlasID, labelIdx, summary, False)
            
            log.debug('Removed overlay {}'.format(overlayName))
            return

        def onLoad(atlas):
            # label image
            if labelIdx is None:
                overlayType = 'label'
                data        = atlas.data

            else:

                # regional label image
                if summary:
                    if   atlasDesc.atlasType == 'probabilistic':
                        labelVal = labelIdx + 1
                    elif atlasDesc.atlasType == 'label':
                        labelVal = labelIdx

                    overlayType = 'mask' 
                    data        = np.zeros(atlas.shape, dtype=np.uint16)
                    data[atlas.data == labelIdx] = labelVal

                # regional probability image
                else:
                    overlayType = 'volume' 
                    data        = atlas.data[:, :, :, labelIdx]

            overlay = fslimage.Image(
                data,
                header=atlas.nibImage.get_header(),
                name=overlayName)

            self._overlayList.disableListener('overlays', self._name)
            self._overlayList.append(overlay)
            self._overlayList.enableListener('overlays', self._name)

            self.__overlayPanel.setOverlayState(
                atlasID, labelIdx, summary, True) 

            self.__enabledOverlays[overlayName] = (overlay,
                                                   atlasID,
                                                   labelIdx,
                                                   summary)

            log.debug('Added overlay {}'.format(overlayName))

            display             = self._displayCtx.getDisplay(overlay)
            display.overlayType = overlayType
            opts                = display.getDisplayOpts()

            if   overlayType == 'mask':   opts.colour = np.random.random(3)
            elif overlayType == 'volume': opts.cmap   = 'hot'
            elif overlayType == 'label':

                # The Harvard-Oxford atlases
                # have special colour maps
                if   atlasID == 'HarvardOxford-Cortical':
                    opts.lut = 'harvard-oxford-cortical'
                elif atlasID == 'HarvardOxford-Subcortical':
                    opts.lut = 'harvard-oxford-subcortical'
                else:
                    opts.lut = 'random'

        self.loadAtlas(atlasID, summary, onLoad)


    def locateRegion(self, atlasID, labelIdx):
        """Moves the :attr:`.DisplayContext.location`  to the specified
        region in the specified atlas. See the :class:`.AtlasDescription`
        class for details on atlas identifiers/label indices.

        :arg atlasID:  Atlas identifier
        :arg labelIdx: Label index
        """
        
        atlasDesc = atlases.getAtlasDescription(atlasID)
        label     = atlasDesc.labels[labelIdx]
        overlay   = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        if overlay is None:
            log.warn('No reference image available - cannot locate region')
        
        opts     = self._displayCtx.getOpts(overlay)
        worldLoc = (label.x, label.y, label.z)
        dispLoc  = opts.transformCoords([worldLoc], 'world', 'display')[0]

        self._displayCtx.location.xyz = dispLoc


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.

        Makes sure that the :class:`.AtlasOverlayPanel` state is up to date -
        see the :meth:`.AtlasOverlayPanel.setOverlayState` method.
        """

        for overlayName in list(self.__enabledOverlays.keys()):

            overlay, atlasID, labelIdx, summary = \
                self.__enabledOverlays[overlayName]

            if overlay not in self._overlayList:
                
                self.__enabledOverlays.pop(overlayName)
                self.__overlayPanel.setOverlayState(
                    atlasID, labelIdx, summary, False)
