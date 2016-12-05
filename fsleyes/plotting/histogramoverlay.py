#!/usr/bin/env python
#
# histogramoverlay.py - The HistogramOverlay class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`HistogramOverlay` class, which is used by
:class:`.HistogramSeries` instances to manage 3D histogram overlays.
"""


import logging

import props

import fsleyes.overlay as fsloverlay


log = logging.getLogger(__name__)


class HistogramOverlay(object):
    """The ``HistogramOverlay`` class manages the creation, destruction, and
    display of a :class:`.ProxyImage` overlay which displays the voxels that
    are included in a histogram plot. The user can toggle the display of this
    overlay via the :attr:`.HistogramSeries.showOverlay` property.

    One ``HistogramOverlay`` is created by every :class:`.HistogramSeries``.
    """
    
    def __init__(self, histSeries, overlay, displayCtx, overlayList):
        """Create a ``HistogramOverlay``.

        :arg histSeries:  The :class:`.HistogramSeries` instance which owns
                          this ``HistobgramOverlay``.

        :arg overlay:     The :class:`.Image` overlay associated with this
                          ``HistogramOverlay``.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        
        :arg overlayList: The :class:`.OverlayList` instance. 
        """

        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__histSeries  = histSeries
        self.__overlay     = overlay
        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__histMask    = None

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        histSeries.addListener('showOverlay',
                                self.__name,
                                self.__showOverlayChanged)


    def destroy(self):
        """Must be called when this ``HistogramOverlay`` is no longer needed.
        """

        self.__overlayList.removeListener('overlays',    self.__name)
        self.__histSeries .removeListener('showOverlay', self.__name)
        
        if self.__histMask is not None:
            self.__overlayList.remove(self.__histMask)

        self.__histSeries  = None
        self.__overlay     = None 
        self.__displayCtx  = None
        self.__overlayList = None
        self.__histMask    = None 


    def __showOverlayChanged(self, *a):
        """Called when the :attr:`.HistogramSeries.showOverlay` property
        changes.

        Adds/removes a 3D mask :class:`.Image` to the :class:`.OverlayList`,
        which highlights the voxels that have been included in the histogram.
        The :class:`.MaskOpts.threshold` property is bound to the
        :attr:`.HistogramSeries.showOverlayRange` property, so the masked
        voxels are updated whenever the histogram overlay range changes, and
        vice versa.
        """

        hs = self.__histSeries

        if      hs.showOverlay  and (self.__histMask is not None): return
        if (not hs.showOverlay) and (self.__histMask is     None): return 

        if not hs.showOverlay:

            log.debug('Removing 3D histogram overlay mask for {}'.format(
                self.__overlay.name))

            if self.__histMask in self.__overlayList:
                self.__overlayList.remove(self.__histMask)
                
            self.__histMask = None

        else:

            log.debug('Creating 3D histogram overlay mask for {}'.format(
                self.__overlay.name))
            
            self.__histMask = fsloverlay.ProxyImage(
                self.__overlay,
                name='{}/histogram/mask'.format(self.__overlay.name))

            self.__overlayList.append(self.__histMask, overlayType='mask')

            opts = self.__displayCtx.getOpts(self.__histMask)

            opts.bindProps('volume',    hs)
            opts.bindProps('colour',    hs)
            opts.bindProps('threshold', hs, 'showOverlayRange')


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` changes.

        If a 3D mask overlay was being shown, and it has been removed from the
        ``OverlayList``, the :attr:`.HistogramSeries.showOverlay` property is
        updated accordingly.
        """
        
        if self.__histMask is None:
            return

        # If a 3D overlay was being shown, and it
        # has been removed from the overlay list
        # by the user, turn the showOverlay property
        # off
        if self.__histMask not in self.__overlayList:

            with props.skip(self.__histSeries, 'showOverlay', self.__name):
                self.__histSeries.showOverlay = False
                self.__showOverlayChanged()
