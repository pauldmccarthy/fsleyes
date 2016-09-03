#!/usr/bin/env python
#
# correlate.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy                  as np
import scipy.spatial.distance as spd

import fsl.data.image     as fslimage
import fsl.utils.dialog   as fsldlg
import fsl.utils.settings as fslsettings
import fsleyes.strings    as strings
from . import                action


class CorrelateAction(action.Action):
    """
    """

    def __init__(self, overlayList, displayCtx, frame):
        """
        """
        action.Action.__init__(self, self.__correlate)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)

        self.__correlateOverlays = {}
        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList`, and calls :meth:`.Action.destroy`.
        """

        self.__displayCtx .removeListener('selectedOverlay', self.__name)
        self.__overlayList.removeListener('overlays',        self.__name)
        action.Action.destroy(self)

        
    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list, changes.
        
        Enables/disables this action depending on the nature of the selected
        overlay.
        """
        
        ovl          = self.__displayCtx.getSelectedOverlay()
        self.enabled = ((ovl is not None)             and
                        (type(ovl) == fslimage.Image) and
                        len(ovl.shape) == 4           and
                        ovl.shape[3] > 1)


    def __overlayListChanged(self, *a):
        """
        """
        self.__clearCorrelateOverlays()
        self.__selectedOverlayChanged()


    def __clearCorrelateOverlays(self):
        """
        """

        for overlay, corrOvl in list(self.__correlateOverlays.items()):
            if overlay not in self.__overlayList or \
               corrOvl not in self.__overlayList:
                self.__correlateOverlays.pop(overlay)


    def __createCorrelateOverlay(self, overlay):

        display = self.__displayCtx.getDisplay(overlay)
        shape   = overlay.shape[:3]
        data    = np.zeros(shape, dtype=np.float32)
        name    = '{}/correlation'.format(display.name)
        corrOvl = fslimage.Image(data, name=name, header=overlay.header)

        self.__overlayList.append(corrOvl, overlayType='volume')
        self.__correlateOverlays[overlay] = corrOvl

        corrOpts = self.__displayCtx.getOpts(corrOvl)

        corrOpts.cmap              = 'red-yellow'
        corrOpts.negativeCmap      = 'blue-lightblue'
        corrOpts.useNegativeCmap   = True
        corrOpts.displayRange      = [0.05, 1]
        corrOpts.clippingRange.xlo = 0.05

        return corrOvl


    def __correlate(self):

        ovl     = self.__displayCtx.getSelectedOverlay()
        corrOvl = self.__correlateOverlays.get(ovl, None)

        if corrOvl is None:
            corrOvl = self.__createCorrelateOverlay(ovl)

        opts        = self.__displayCtx.getOpts(   ovl)
        corrDisplay = self.__displayCtx.getDisplay(corrOvl)
        corrOpts    = self.__displayCtx.getOpts(   corrOvl)

        x, y, z     = opts.getVoxel(vround=True)

        data        = ovl.nibImage.get_data()
        npoints     = data.shape[3]
 
        seed        = data[x, y, z, :].reshape(1, npoints)
        targets     = data.reshape(-1, npoints)

        correlation = 1 - spd.cdist(seed, targets, metric='correlation')

        self.__displayCtx.freezeOverlay(corrOvl)

        corrOvl[:]  = correlation.reshape(data.shape[:3])

        self.__displayCtx.thawOverlay(corrOvl)
