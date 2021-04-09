#!/usr/bin/env python
#
# atlaspanel.py - The AtlasPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`AtlasPanel`, a *FSLeyes control* panel
which allows the user to browse the FSL atlas images. See the
:mod:`~fsleyes` package documentation for more details on control panels,
and the :mod:`.atlases` module for more details on the atlases available in
FSL.
"""


import          logging

import numpy as np
import          wx

import fsl.data.image                as fslimage
import fsl.data.atlases              as atlases
import fsl.data.constants            as constants
import fsl.utils.idle                as idle

import fsleyes_props                 as props
import fsleyes_widgets.notebook      as notebook
import fsleyes_widgets.utils.status  as status

import fsleyes.views.canvaspanel     as canvaspanel
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.strings               as strings
from . import                           atlasmanagementpanel
from . import                           atlasoverlaypanel
from . import                           atlasinfopanel


log = logging.getLogger(__name__)


class AtlasPanel(ctrlpanel.ControlPanel):
    """An ``AtlasPanel`` is a :class:`.ControlPanel` which allows the user to
    view atlas information, and to browse through the atlases that come shipped
    with FSL. The ``AtlasPanel`` interface is provided by some sub-panels,
    which are displayed in a :class:`fsleyes_widgets.Notebook` panel. The
    ``AtlasPanel`` itself provides a number of convenience methods that are
    used by these sub-panels:


    ============================== ===========================================
    :class:`.AtlasInfoPanel`       Displays information for the current
                                   :attr:`.DisplayContext.location` from
                                   atlases selected by the user.

    :class:`.AtlasOverlayPanel`    Allows the user to search through all
                                   atlases for specific regions, and to toggle
                                   on/off overlays for those regions.

    :class:`.AtlasManagementPanel` Allows the user to add/remove atlases.
    ============================== ===========================================


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

      - A 3D image containing the statistic image for a single region,
        extracted from a :class:`.StatisticAtlas`. These images are added
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

      - ``overlayType`` is either ``label``, ``prob``, or ``stat``, depending on
        whether the overlay is a discrete label image, a probaility image, or
        a statistic image..

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


    @staticmethod
    def supportedViews():
        """The ``MelodicClassificationPanel`` is restricted for use with
        :class:`.OrthoPanel`, :class:`.LightBoxPanel` and
        :class:`.Scene3DPanel` viewws.
        """

        return [canvaspanel.CanvasPanel]


    @staticmethod
    def defaultLayout():
        """Returns a dictionary of arguments to be passed to the
        :meth:`.ViewPanel.togglePanel` method.
        """
        return {'location' : wx.BOTTOM}


    def __init__(self, parent, overlayList, displayCtx, viewPanel):
        """Create an ``AtlasPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg viewPanel:   The :class:`.ViewPanel` instance.
        """

        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, viewPanel)

        # Make sure the atlas
        # registry is up to date
        atlases.rescanAtlases()

        # See the enableAtlasPanel method
        # for info about this attribute.
        self.__atlasPanelEnableStack = 0

        # Cache of loaded atlases
        # and enabled atlas overlays.
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

        self.__managePanel = atlasmanagementpanel.AtlasManagementPanel(
            self.__notebook, overlayList, displayCtx, self)

        self.__notebook.AddPage(self.__infoPanel,
                                strings.titles[self.__infoPanel])
        self.__notebook.AddPage(self.__overlayPanel,
                                strings.titles[self.__overlayPanel])
        self.__notebook.AddPage(self.__managePanel,
                                strings.titles[self.__managePanel])

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__overlayListChanged)

        self.Layout()
        self.SetMinSize(self.__sizer.GetMinSize())


    def destroy(self):
        """Must be called on when this ``AtlasPanel`` is no longer needed.

        Calls the ``destroy`` methods of the :class:`.AtlasInfoPanel` and
        :class:`.AtlasOverlayPanel`, and then calls
        :meth:`.ControlPanel.destroy`.
        """
        self.__loadedAtlases   = None
        self.__enabledOverlays = None
        self.__infoPanel     .destroy()
        self.__overlayPanel  .destroy()
        self.__managePanel   .destroy()

        self.overlayList.removeListener('overlays', self.name)

        ctrlpanel.ControlPanel.destroy(self)


    def Enable(self, enable=True):
        """Enables/disables this ``AtlasPanel``. """

        self.__infoPanel   .Enable(enable)
        self.__overlayPanel.Enable(enable)
        self.__managePanel .Enable(enable)


    def Disable(self):
        """Disables this ``AtlasPanel``. """
        self.Enable(False)


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

        log.debug('enableAtlasPanel({}, count={})'.format(enable, count))

        if enable:
            count -= 1

            if count <= 0:
                count = 0
                self.Enable()

        else:
            count += 1
            self.Disable()

        self.__atlasPanelEnableStack = count


    def loadAtlas(self,
                  atlasID,
                  summary,
                  onLoad=None,
                  onError=None,
                  matchResolution=True):
        """Loads the atlas image with the specified ID. The atlas is loaded
        asynchronously (via the :mod:`.idle` module), as it can take some
        time. Use the `onLoad` argument if you need to do something when the
        atlas has been loaded.

        :arg onLoad:          Optional. A function which is called when the
                              atlas has been loaded, and which is passed the
                              loaded :class:`.Atlas` image.

        :arg onError:         Optional. A function which is called if the
                              atlas loading job raises an error. Passed the
                              ``Exception`` that was raised.

        :arg matchResolution: If ``True`` (the default), the version of the
                              atlas with the most suitable resolution, based
                              on the current contents of the
                              :class:`.OverlayList`, is loaded.

        See the :func:`.atlases.loadAtlas` function for details on the other
        arguments.
        """

        # Get the atlas description, and the
        # most suitable resolution to load.
        desc = atlases.getAtlasDescription(atlasID)
        res  = self.__getSuitableResolution(desc, matchResolution)

        if desc.atlasType == 'label':
            summary = True

        atlas = self.__loadedAtlases.get((atlasID, summary, res), None)

        if atlas is None:

            log.debug('Loading atlas {}/{}'.format(
                atlasID, 'label' if summary else 'prob'))

            status.update('Loading atlas {}...'.format(atlasID), timeout=None)

            def load():

                # the panel might get destroyed
                # before this function is called
                if self.destroyed:
                    return

                atlas = atlases.loadAtlas(atlasID, summary, resolution=res)

                # The atlas panel may be destroyed
                # before the atlas is loaded.
                if not self or self.destroyed:
                    return

                self.__loadedAtlases[atlasID, summary, res] = atlas

                status.update('Atlas {} loaded.'.format(atlasID))

                if onLoad is not None:
                    idle.idle(onLoad, atlas)

            idle.run(load, onError=onError)

        # If the atlas has already been loaded,
        # pass it straight to the onload function
        elif onLoad is not None:
            onLoad(atlas)


    def __getSuitableResolution(self, desc, matchResolution=True):
        """Used by the :meth:`loadAtlas` method. Determines a suitable
        atlas resolution to load, based on the current contents of the
        :class:`.OverlayList`.
        """

        niftis = [o for o in self.overlayList
                  if (isinstance(o, fslimage.Nifti) and
                      o.getXFormCode() == constants.NIFTI_XFORM_MNI_152)]

        # No overlays to match resolution against
        if len(niftis) == 0:
            matchResolution = False

        # If we don't need to match resolution,
        # return the highest available resolution
        # (the lowest value).
        if not matchResolution:
            return np.concatenate(desc.pixdims).min()

        # Find the highest resolution
        # in the overlay list
        pixdims = [o.pixdim[:3] for o in niftis]
        res     = np.concatenate(pixdims).min()

        # identify the atlas with the
        # nearest resolution to the
        # requested resolution
        reses = np.concatenate(desc.pixdims)
        res   = reses[np.argmin(np.abs(reses - res))]

        return res


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
        return self.overlayList.find(name) is not None


    def toggleOverlay(self,
                      atlasID,
                      labelIdx,
                      summary,
                      onLoad=None,
                      onError=None):
        """Adds or removes the specified overlay to/from the
        :class:`.OverlayList`.

        :arg onLoad:  Optional function to be called when the overlay has been
                      added/removed.

        :arg onError: Optional function to be called if an error occurs while
                      loading an overlay.

        See :meth:`getOverlayName` for details on the other arguments.
        """

        atlasDesc            = atlases.getAtlasDescription(atlasID)
        overlayName, summary = self.getOverlayName(atlasID, labelIdx, summary)
        overlay              = self.overlayList.find(overlayName)

        if overlay is not None:

            self.overlayList.disableListener('overlays', self.name)
            self.overlayList.remove(overlay)
            self.overlayList.enableListener('overlays', self.name)

            self.__enabledOverlays.pop(overlayName, None)
            self.__overlayPanel.setOverlayState(
                atlasDesc, labelIdx, summary, False)

            log.debug('Removed overlay {}'.format(overlayName))

            if onLoad is not None:
                onLoad()
            return

        def realOnLoad(atlas):
            initprops = {}
            # label image
            if labelIdx is None:
                overlay = fslimage.Image(atlas)
                initprops['overlayType'] = 'label'

            else:

                # regional label image
                if summary:
                    overlay = atlas.get(index=labelIdx, binary=False)
                    initprops['overlayType'] = 'mask'
                    initprops['colour']      = np.random.random(3)

                # regional statistic/probability image
                else:
                    overlay = atlas.get(index=labelIdx)
                    initprops['overlayType']   = 'volume'
                    initprops['cmap']          = 'hot'
                    initprops['displayRange']  = (atlasDesc.lower,
                                                  atlasDesc.upper)
                    initprops['clippingRange'] = (atlasDesc.lower,
                                                  atlasDesc.upper)

            overlay.name = overlayName

            with props.suppress(self.overlayList, 'overlays', self.name):
                self.overlayList.append(overlay, **initprops)

            self.__overlayPanel.setOverlayState(
                atlasDesc, labelIdx, summary, True)

            self.__enabledOverlays[overlayName] = (overlay,
                                                   atlasID,
                                                   labelIdx,
                                                   summary)

            log.debug('Added overlay {}'.format(overlayName))

            if onLoad is not None:
                onLoad()

        self.loadAtlas(atlasID, summary, onLoad=realOnLoad, onError=onError)


    def locateRegion(self, atlasID, labelIdx):
        """Moves the :attr:`.DisplayContext.location`  to the specified
        region in the specified atlas. See the :class:`.AtlasDescription`
        class for details on atlas identifiers/label indices.

        :arg atlasID:  Atlas identifier
        :arg labelIdx: Label index
        """

        atlasDesc = atlases.getAtlasDescription(atlasID)
        label     = atlasDesc.labels[labelIdx]
        overlay   = self.displayCtx.getReferenceImage(
            self.displayCtx.getSelectedOverlay())

        if overlay is None:
            log.warn('No reference image available - cannot locate region')

        opts     = self.displayCtx.getOpts(overlay)
        worldLoc = (label.x, label.y, label.z)
        dispLoc  = opts.transformCoords([worldLoc], 'world', 'display')[0]

        self.displayCtx.location.xyz = dispLoc


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.

        Makes sure that the :class:`.AtlasOverlayPanel` state is up to date -
        see the :meth:`.AtlasOverlayPanel.setOverlayState` method.
        """

        for overlayName in list(self.__enabledOverlays.keys()):

            overlay, atlasID, labelIdx, summary = \
                self.__enabledOverlays[overlayName]

            if overlay not in self.overlayList:

                self.__enabledOverlays.pop(overlayName)
                atlasDesc = atlases.getAtlasDescription(atlasID)
                self.__overlayPanel.setOverlayState(
                    atlasDesc, labelIdx, summary, False)
