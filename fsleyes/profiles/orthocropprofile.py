#!/usr/bin/env python
#
# orthocropprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

import props

import fsl.data.image         as fslimage
import fsleyes.gl.annotations as annotations
from . import                    orthoviewprofile


class OrthoCropProfile(orthoviewprofile.OrthoViewProfile):


    # cropBox: voxel coordinates [(xlo, xhi), (ylo, yhi), (zlo, zhi)]
    cropBox = props.Bounds(ndims=3, real=False, minDistance=1)


    def __init__(self, viewPanel, overlayList, displayCtx):


        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            viewPanel,
            overlayList,
            displayCtx,
            ['crop'])
        self.mode = 'crop'

        self.__overlay = None

        # { overlay : cropBox }
        self.__cachedCrops = {}

        # axes:   X / Y / Z
        # limits: lo / hi
        # 
        # when the user is dragging
        # a crop box boundary
        self.__dragAxes   = None
        self.__dragLimits = None
        
        self.__xcanvas = viewPanel.getXCanvas()
        self.__ycanvas = viewPanel.getYCanvas()
        self.__zcanvas = viewPanel.getZCanvas()

        self.__xrect   = annotations.Rect(1, 2, (0, 0), 0, 0,
                                          colour=(0.3, 0.3, 1.0),
                                          filled=True)
        self.__yrect   = annotations.Rect(0, 2, (0, 0), 0, 0,
                                          colour=(0.3, 0.3, 1.0),
                                          filled=True)
        self.__zrect   = annotations.Rect(0, 1, (0, 0), 0, 0,
                                          colour=(0.3, 0.3, 1.0),
                                          filled=True)

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        self       .addListener('cropBox',
                                self._name,
                                self.__cropBoxChanged)

        self.__xcanvas.getAnnotations().obj(self.__xrect, hold=True)
        self.__ycanvas.getAnnotations().obj(self.__yrect, hold=True)
        self.__zcanvas.getAnnotations().obj(self.__zrect, hold=True)

        self.__selectedOverlayChanged()


    def destroy(self):
        """
        """
        
        self.__xcanvas.getAnnotations().dequeue(self.__xrect, hold=True)
        self.__ycanvas.getAnnotations().dequeue(self.__yrect, hold=True)
        self.__zcanvas.getAnnotations().dequeue(self.__zrect, hold=True)
        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self             .removeListener('cropBox',         self._name)
        
        orthoviewprofile.OrthoViewProfile.destroy(self) 


    def __deregisterOverlay(self):
        """
        """
        
        if self.__overlay is None:
            return

        # TODO put current crop in crop cache
        
        self.__overlay = None

        
    def __registerOverlay(self, overlay):
        """
        """ 
        self.__overlay = overlay

        
    def __selectedOverlayChanged(self, *a):
        """
        """ 
        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is self.__overlay:
            return

        self.__deregisterOverlay()

        enabled = isinstance(overlay, fslimage.Image)

        self.__xrect.enabled = enabled
        self.__yrect.enabled = enabled
        self.__zrect.enabled = enabled

        if not enabled:
            return

        self.__registerOverlay(overlay)

        # TODO Show a warning (like in OrthoEditProfile)
        if self._displayCtx.displaySpace != overlay:
            self._displayCtx.displaySpace = overlay

        crop = self.__cachedCrops.get(overlay, None)

        if crop is None:
            shape = overlay.shape[:3]
            crop  = [0, shape[0], 0, shape[1], 0, shape[2]]

        with props.suppress(self, 'cropBox', notify=True):
            self.cropBox.xmin = 0
            self.cropBox.ymin = 0
            self.cropBox.zmin = 0
            self.cropBox.xmax = shape[0]
            self.cropBox.ymax = shape[1]
            self.cropBox.zmax = shape[2]
            self.cropBox      = crop


    def __cropBoxChanged(self, *a):
        """
        """

        xlo, xhi = self.cropBox.x
        ylo, yhi = self.cropBox.y
        zlo, zhi = self.cropBox.z

        xlo     -= 0.5
        ylo     -= 0.5
        zlo     -= 0.5
        xhi     -= 0.5
        yhi     -= 0.5
        zhi     -= 0.5
        coords   = np.array([
            [xlo, ylo, zlo],
            [xlo, ylo, zhi],
            [xlo, yhi, zlo],
            [xlo, yhi, zhi],
            [xhi, ylo, zlo],
            [xhi, ylo, zhi],
            [xhi, yhi, zlo],
            [xhi, yhi, zhi]])

        opts   = self._displayCtx.getOpts(self.__overlay)
        coords = opts.transformCoords(coords, 'voxel', 'display')

        mins = coords.min(axis=0)
        maxs = coords.max(axis=0)

        self.__xrect.xy = mins[1],  mins[2]
        self.__xrect.w  = maxs[1] - mins[1]
        self.__xrect.h  = maxs[2] - mins[2]
        
        self.__yrect.xy = mins[0],  mins[2]
        self.__yrect.w  = maxs[0] - mins[0]
        self.__yrect.h  = maxs[2] - mins[2]

        self.__zrect.xy = mins[0],  mins[1]
        self.__zrect.w  = maxs[0] - mins[0]
        self.__zrect.h  = maxs[1] - mins[1]

        # TODO Don't do this if you don't need to 
        self.__xcanvas.Refresh()
        self.__ycanvas.Refresh()
        self.__zcanvas.Refresh()
        

    def _cropModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        if self.__overlay is None:
            return

        vox = self._displayCtx.getOpts(self.__overlay).getVoxel(
            canvasPos, vround=True)

        if vox is None:
            return

        # Figure out what axis (X, Y, or Z) and limit
        # (lo, hi) the mouse click was closest to

        # What canvas was the click on? 
        if   canvas.zax == 0: hax, vax = 1, 2
        elif canvas.zax == 1: hax, vax = 0, 2
        elif canvas.zax == 2: hax, vax = 0, 1

        # Distances from the mouse 
        # click to each crop box 
        # boundary on the clicked
        # canvas
        hlo, hhi = self.cropBox.getLo(hax), self.cropBox.getHi(hax)
        vlo, vhi = self.cropBox.getLo(vax), self.cropBox.getHi(vax)

        if abs(vox[hax] - hlo) < abs(vox[hax] - hhi): hlimit = 0
        else:                                         hlimit = 1
        if abs(vox[vax] - vlo) < abs(vox[vax] - vhi): vlimit = 0
        else:                                         vlimit = 1 
            
        # print 'Crop box: x {}'.format(self.cropBox.x)
        # print '          y {}'.format(self.cropBox.y)
        # print '          z {}'.format(self.cropBox.z)
        # print 'Voxel:      {}'.format(vox)
        # print 'Screen ax:  {}'.format(['horizontal', 'vertical'][scrAx])
        # print 'Voxel ax:   {}'.format('xyz'[voxAx])
        # print 'Limit:      {}'.format(['low', 'high'][limit])

        self.__dragAxes   = (hax,    vax)
        self.__dragLimits = (hlimit, vlimit)

        # Update the crop box
        with props.suppress(self, 'cropBox', notify=True):
            self.cropBox.setLimit(hax, hlimit, vox[hax])
            self.cropBox.setLimit(vax, vlimit, vox[vax])

        self._displayCtx.location = canvasPos


    def _cropModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        
        if self.__overlay is None or self.__dragAxes is None:
            return

        hax, vax   = self.__dragAxes
        hlim, vlim = self.__dragLimits
        vox        = self._displayCtx.getOpts(self.__overlay).getVoxel(
            canvasPos, vround=True)

        if vox is None:
            return

        hval = vox[hax]
        vval = vox[vax]

        oldhlo, oldhhi = self.cropBox.getRange(hax)
        oldvlo, oldvhi = self.cropBox.getRange(vax)

        if   hlim == 0 and hval >= oldhhi: hval = oldhhi - 1
        elif hlim == 1 and hval <= oldhlo: hval = oldhlo + 1
        if   vlim == 0 and vval >= oldvhi: vval = oldvhi - 1
        elif vlim == 1 and vval <= oldvlo: vval = oldvlo + 1

        with props.suppress(self, 'cropBox', notify=True):
            self.cropBox.setLimit(hax, hlim, hval)
            self.cropBox.setLimit(vax, vlim, vval)

        self._displayCtx.location = canvasPos

    
    def _cropModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        
        if self.__overlay is None or self.__dragAxes is None:
            return

        self.__dragAxes   = None
        self.__dragLimits = None
