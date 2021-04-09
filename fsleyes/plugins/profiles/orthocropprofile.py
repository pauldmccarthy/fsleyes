#!/usr/bin/env python
#
# orthocropprofile.py - The OrthoCropProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoCropProfile` class, an interaction
:class:`.Profile` for :class:`.OrthoPanel` views, which is used by the
:class:`.CropImagePanel`.
"""


import logging

import          wx
import numpy as np

import fsl.data.image                     as fslimage
import fsl.utils.run                      as fslrun
import fsl.utils.tempdir                  as tempdir
from   fsl.utils.platform import platform as fslplatform
import fsleyes_props                      as props
import fsleyes.actions                    as actions
import fsleyes.gl.annotations             as annotations
import fsleyes.profiles.orthoviewprofile  as orthoviewprofile


log = logging.getLogger(__name__)


class OrthoCropProfile(orthoviewprofile.OrthoViewProfile):
    """The ``OrthoCropProfile`` class is a :class:`.Profile` for the
    :class:`.OrthoPanel` class, which allows the user to define a cropping
    region for :class:`.Image` overlays.


    Ther ``OrthoCropProfile`` displays a cropping, or ROI, region on the
    ``OrthoPanel`` canvases, relative to the for the currently selected
    image, using :class:`.Rect` annotations. Mouse handlers are also
    defined, allowing the user to adjust the box.


    Once the user has selected a cropping region, the related
    :class:`.CropImagePanel` allows him/her to create a cropped copy of the
    image.


    The ``OrthoCropProfile`` class defines one mode, in addition to those
    inherited from the :class:`.OrthoViewProfile` class:


    ======== ===================================================
    ``crop`` Clicking and dragging allows the user to change the
             boundaries of a cropping region.
    ======== ===================================================


    .. note:: The crop overlay will only be shown if the
              :attr:`.DisplayContext.displaySpace` is set to the currently
              selected overlay. The :class:`.CropImagePanel` uses a
              :class:`.DisplaySpaceWarning` to inform the user.
    """


    cropBox = props.Bounds(ndims=3, real=False, minDistance=1, clamped=False)
    """This property keeps track of the current low/high limits
    of the cropping region, in the voxel coordinate system of the
    currently selected overlay.
    """


    @staticmethod
    def tempModes():
        """Returns the temporary mode map for the ``OrthoCropProfile``,
        which controls the use of modifier keys to temporarily enter other
        interaction modes.
        """
        return {
            ('crop',  wx.WXK_SHIFT)                  : 'nav',
            ('crop',  wx.WXK_CONTROL)                : 'zoom',
            ('crop',  wx.WXK_ALT)                    : 'pan',
            ('crop', (wx.WXK_CONTROL, wx.WXK_SHIFT)) : 'slice'}


    @staticmethod
    def altHandlers():
        """Returns the alternate handlers map, which allows event handlers
        defined in one mode to be re-used whilst in another mode.
        """
        return {('crop', 'MiddleMouseDrag') : ('pan', 'LeftMouseDrag')}


    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create an ``OrthoCropProfile``.

        :arg viewPanel:    An :class:`.OrthoPanel` instance.
        :arg overlayList:  The :class:`.OverlayList` instance.
        :arg displayCtx:   The :class:`.DisplayContext` instance.
        """

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            viewPanel,
            overlayList,
            displayCtx,
            ['crop'])
        self.mode = 'crop'

        # The currently selected overlay,
        # and the one for which the cropping
        # box is being shown/modified.
        self.__overlay = None

        # A cache of { overlay : cropBox }
        # which stores the last cropping
        # box for a given overlay. This
        # is used to cache boxes if the
        # user selects a different overlay
        # while the crop profile is active.
        self.__cachedCrops = {}

        # axis:   one of 0, 1, or 2 (X, Y, or Z) -
        #         the voxel axis of the crop box
        #         that is being adjusted
        #
        # limits: one of 0 or 1 (lo or hi) - the
        #         low/high limit of the crop box
        #         that is being adjusted
        #
        # These fields are set when the
        # user is dragging a crop box
        # boundary
        self.__dragAxis  = None
        self.__dragLimit = None

        self.__xcanvas = viewPanel.getXCanvas()
        self.__ycanvas = viewPanel.getYCanvas()
        self.__zcanvas = viewPanel.getZCanvas()

        # A rectangle is displayed on
        # each of the canvases, showing
        # the current cropping box.
        self.__xrect   = annotations.Rect(self.__xcanvas.getAnnotations(),
                                          0, 0, 0, 0,
                                          colour=(0.3, 0.3, 1.0),
                                          alpha=30)
        self.__yrect   = annotations.Rect(self.__ycanvas.getAnnotations(),
                                          0, 0, 0, 0,
                                          colour=(0.3, 0.3, 1.0),
                                          alpha=30)
        self.__zrect   = annotations.Rect(self.__zcanvas.getAnnotations(),
                                          0, 0, 0, 0,
                                          colour=(0.3, 0.3, 1.0),
                                          alpha=30)

        displayCtx .addListener('displaySpace',
                                self.name,
                                self.__displaySpaceChanged)
        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)
        self       .addListener('cropBox',
                                self.name,
                                self.__cropBoxChanged)

        self.__xcanvas.getAnnotations().obj(self.__xrect, hold=True)
        self.__ycanvas.getAnnotations().obj(self.__yrect, hold=True)
        self.__zcanvas.getAnnotations().obj(self.__zrect, hold=True)

        self.robustfov.enabled = fslplatform.fsldir is not None

        self.__selectedOverlayChanged()


    def destroy(self):
        """Must be called when this ``OrthoCropProfile`` is no longer
        needed. Removes property listeners and does some other clean up.
        """

        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.displayCtx .removeListener('displaySpace',    self.name)
        self            .removeListener('cropBox',         self.name)

        self.__xcanvas.getAnnotations().dequeue(self.__xrect, hold=True)
        self.__ycanvas.getAnnotations().dequeue(self.__yrect, hold=True)
        self.__zcanvas.getAnnotations().dequeue(self.__zrect, hold=True)

        orthoviewprofile.OrthoViewProfile.destroy(self)


    @actions.action
    def robustfov(self):
        """Call ``robustfov`` for the current overlay and set the
        :attr:`cropBox` based on the result.
        """

        overlay = self.__overlay

        if overlay is None:
            return

        try:
            with tempdir.tempdir():

                # in-memory image - create and
                # save a copy - use a copy
                # otherwise the original will
                # think that is has been saved
                # to disk.
                if overlay.dataSource is None:
                    overlay = fslimage.Image(overlay)
                    overlay.save('image')

                result = fslrun.runfsl('robustfov', '-i', overlay.dataSource)

                # robustfov returns two lines, the last
                # of which contains the limits, as:
                #
                #    xmin xlen ymin ylen zmin zlen
                limits = list(result.strip().split('\n')[-1].split())
                limits = [float(l) for l in limits]

                # Convert the lens to maxes
                limits[1]      += limits[0]
                limits[3]      += limits[2]
                limits[5]      += limits[4]
                self.cropBox[:] = limits

        except Exception as e:
            log.warning('Call to robustfov failed: {}'.format(str(e)))


    def __deregisterOverlay(self):
        """Called by :meth:`__selectedOverlayChanged`. Clears references
        associated with the previously selected overlay, if necessary.
        """

        if self.__overlay is None:
            return

        self.__cachedCrops[self.__overlay] = list(self.cropBox)
        self.__overlay = None


    def __registerOverlay(self, overlay):
        """Called by :meth:`__selectedOverlayChanged`. Sets up
        references associated with the given (newly selected) overlay.
        """
        self.__overlay = overlay


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` changes.
        If the overlay is a :class:`.Image` instance, it is set as the
        :attr:`.DisplayContext.displaySpace` reference, and the
        :attr:`cropBox` is configured to be relative to the newly selected
        overlay.
        """
        overlay = self.displayCtx.getSelectedOverlay()

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

        shape = overlay.shape[:3]
        crop  = self.__cachedCrops.get(overlay, None)

        if crop is None:
            crop = [0, shape[0], 0, shape[1], 0, shape[2]]

        with props.suppress(self, 'cropBox', notify=True):
            self.cropBox.xmin = 0
            self.cropBox.ymin = 0
            self.cropBox.zmin = 0
            self.cropBox.xmax = shape[0]
            self.cropBox.ymax = shape[1]
            self.cropBox.zmax = shape[2]
            self.cropBox      = crop


    def __displaySpaceChanged(self, *a):
        """Called when the :attr:`.DisplayContext.displaySpace` changes.
        Resets the :attr:`cropBox`.
        """
        cropBox     = self.cropBox
        cropBox.xlo = self.cropBox.xmin
        cropBox.ylo = self.cropBox.ymin
        cropBox.zlo = self.cropBox.zmin
        cropBox.xhi = self.cropBox.xmax
        cropBox.yhi = self.cropBox.ymax
        cropBox.zhi = self.cropBox.zmax


    def __cropBoxChanged(self, *a):
        """Called when the :attr:`cropBox` changes. Updates the :class:`.Rect`
        annotations on the :class:`.OrthoPanel` canvases.
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

        opts   = self.displayCtx.getOpts(self.__overlay)
        coords = opts.transformCoords(coords, 'voxel', 'display')

        mins = coords.min(axis=0)
        maxs = coords.max(axis=0)
        pads = (maxs - mins) * 0.01

        self.__xrect.x    = mins[1]
        self.__xrect.y    = mins[2]
        self.__xrect.w    = maxs[1] - mins[1]
        self.__xrect.h    = maxs[2] - mins[2]
        self.__xrect.zmin = mins[0] - pads[0]
        self.__xrect.zmax = maxs[0] + pads[0]

        self.__yrect.x    = mins[0]
        self.__yrect.y    = mins[2]
        self.__yrect.w    = maxs[0] - mins[0]
        self.__yrect.h    = maxs[2] - mins[2]
        self.__yrect.zmin = mins[1] - pads[1]
        self.__yrect.zmax = maxs[1] + pads[1]

        self.__zrect.x    = mins[0]
        self.__zrect.y    = mins[1]
        self.__zrect.w    = maxs[0] - mins[0]
        self.__zrect.h    = maxs[1] - mins[1]
        self.__zrect.zmin = mins[2] - pads[2]
        self.__zrect.zmax = maxs[2] + pads[2]

        # TODO Don't do this if you don't need to
        self.__xcanvas.Refresh()
        self.__ycanvas.Refresh()
        self.__zcanvas.Refresh()


    def __getVoxel(self, overlay, canvasPos):
        """Called by the mouse down/drag handlers. Figures out the voxel
        in the currently selected overlay which corresponds to the
        given canvas position.
        """
        vox = self.displayCtx.getOpts(overlay).getVoxel(
            canvasPos, clip=False, vround=False)
        return np.ceil(vox)


    def _cropModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on mouse down events. Calculates the nearest crop box
        boundary to the mouse click, adjusts the boundary accordingly,
        and saves the boundary/axis information for subsequent drag
        events (see :meth:`_cropModeLeftMouseDrag`).
        """

        copts   = canvas.opts
        overlay = self.__overlay

        if overlay is None:
            return

        # What canvas was the click on?
        if   copts.zax == 0: hax, vax = 1, 2
        elif copts.zax == 1: hax, vax = 0, 2
        elif copts.zax == 2: hax, vax = 0, 1

        # Figure out the distances from
        # the mouse click  to each crop
        # box boundary on the clicked
        # canvas
        vox        = self.__getVoxel(overlay, canvasPos)
        hlo, hhi   = self.cropBox.getLo(hax), self.cropBox.getHi(hax)
        vlo, vhi   = self.cropBox.getLo(vax), self.cropBox.getHi(vax)

        # We compare the click voxel
        # coords with each of the x/y
        # lo/hi crop box boundaries
        boundaries = np.array([
            [hlo,      vox[vax]],
            [hhi,      vox[vax]],
            [vox[hax], vlo],
            [vox[hax], vhi]])

        # As the display space is (should be) set
        # to this overlay, the display coordinate
        # system is equivalent to the scaled
        # voxel coordinate system of the
        # overlay. So we can just multiply the
        # 2D voxel coordinates by the
        # corresponding pixdims to get the
        # distances in the display coordinate
        # system.
        pixdim           = overlay.pixdim[:3]
        scVox            = [vox[hax] * pixdim[hax], vox[vax] * pixdim[vax]]
        boundaries[:, 0] = boundaries[:, 0] * pixdim[hax]
        boundaries[:, 1] = boundaries[:, 1] * pixdim[vax]

        # Calculate distance from click to
        # crop boundaries, and figure out
        # the screen axis (x/y) and limit
        # (lo/hi) to be dragged.
        dists       = (boundaries - scVox) ** 2
        dists       = np.sqrt(np.sum(dists, axis=1))
        axis, limit = np.unravel_index(np.argmin(dists), (2, 2))
        voxAxis     = [hax, vax][axis]

        axis  = int(axis)
        limit = int(limit)

        # Save these for the mouse drag handler
        self.__dragAxis  = voxAxis
        self.__dragLimit = limit

        # Update the crop box and location
        with props.suppress(self, 'cropBox', notify=True):
            self.cropBox.setLimit(voxAxis, limit, vox[voxAxis])

        self.displayCtx.location = canvasPos


    def _cropModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse drags. Updates the :attr:`cropBox` boudary
        which was clicked on (see :meth:`_cropModeLeftMouseDown`), so it
        follows the mouse location.
        """

        if self.__overlay is None or self.__dragAxis is None:
            return

        box      = self.cropBox
        axis     = self.__dragAxis
        limit    = self.__dragLimit
        oppLimit = 1 - limit
        vox      = self.__getVoxel(self.__overlay, canvasPos)

        newval = vox[axis]
        oppval = box.getLimit(axis, oppLimit)

        if   limit == 0 and newval >= oppval: newval = oppval - 1
        elif limit == 1 and newval <= oppval: newval = oppval + 1

        with props.suppress(self, 'cropBox', notify=True):
            self.cropBox.setLimit(axis, limit, newval)

        self.displayCtx.location = canvasPos


    def _cropModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse up events. Clears references used by the
        mouse down/drag handlers.
        """

        if self.__overlay is None or self.__dragAxis is None:
            return

        self.__dragAxis  = None
        self.__dragLimit = None
