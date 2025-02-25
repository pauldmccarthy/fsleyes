#!/usr/bin/env python
#
# autodisplay.py - Routines for configuring default overlay display
#                  settings.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`audoDisplay` function, which is used
for automatically configuring overlay display settings.

The :autoDisplay` function is called when *FSLeyes* is started, and when
new overlays are loaded.
"""


import sys
import logging
import os.path as op

import numpy as np

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


def autoDisplay(overlay, overlayList, displayCtx, **kwargs):
    """Automatically configure display settings for the given overlay.

    :arg overlay:     The overlay object (e.g. an :class:`.Image` instance).
    :arg overlayList: The :class:`.OverlayList`.
    :arg displayCtx:  The :class:`.DisplayContext`.
    :arg kwargs:      Passed through to the overlay-type specific function.
    """

    oType = type(overlay).__name__
    func  = getattr(sys.modules[__name__], f'_{oType}Display', None)

    if func is None:
        log.warn('Unknown overlay type: %s', oType)
        return

    log.debug('Applying default display arguments for %s', overlay)
    func(overlay, overlayList, displayCtx, **kwargs)


def _ImageDisplay(overlay, overlayList, displayCtx, **kwargs):
    """Configure default display settings for the given :class:`.Image`
    overlay. If the image looks like it is from a FEAT analysis,
    some display settings are changed.
    """

    displayFuncs = {
        'zstat'                  : _statImageDisplay,
        'tstat'                  : _statImageDisplay,
        'fstat'                  : _statImageDisplay,
        'zfstat'                 : _statImageDisplay,
        'rendered_thresh_zstat'  : _renderedStatImageDisplay,
        'rendered_thresh_zfstat' : _renderedStatImageDisplay,
        'thresh_zstat'           : _threshStatImageDisplay,
        'thresh_zfstat'          : _threshStatImageDisplay,
        'cope'                   : _peImageDisplay,
        'pe'                     : _peImageDisplay,
        'varcope'                : _peImageDisplay,
        'cluster_mask_zfstat'    : _clusterMaskImageDisplay,
        'cluster_mask_zstat'     : _clusterMaskImageDisplay,
    }
    basename    = op.basename(overlay.dataSource)
    basename    = fslimage.removeExt(basename)
    imageId     = basename.rstrip('0123456789')
    displayFunc = displayFuncs.get(imageId, None)

    if displayFunc is not None:
        displayFunc(basename, overlay, displayCtx, **kwargs)


def _getStatImageColourMaps(overlay, posCmap=None, negCmap=None):
    # Cycle through these colour maps for statistic images
    cmaps = ['red-yellow',
             'blue-lightblue',
             'green',
             'cool',
             'hot',
             'blue',
             'red',
             'yellow',
             'pink',
             'copper']
    idx = _getStatImageColourMaps.currentCmap

    if posCmap is None:
        posCmap = cmaps[idx]
        idx     = (idx + 1) % len(cmaps)
        _getStatImageColourMaps.currentCmap = idx

    if negCmap is None:
        negCmap = posCmap

    return posCmap, negCmap

# Index into the cmaps list, pointing to the
# next colour map to use for statistic images.
_getStatImageColourMaps.currentCmap = 0


def _statImageDisplay(basename,
                      overlay,
                      displayCtx,
                      zthres=3.1,
                      posCmap=None,
                      negCmap=None):
    """Configure default display settings for the given FEAT statistic
    image (e.g. ``zstat1.nii.gz``).
    """

    opts              = displayCtx.getOpts(overlay)
    posCmap, negCmap  = _getStatImageColourMaps(posCmap, negCmap)
    opts.cmap         = posCmap
    opts.negativeCmap = negCmap

    # f-stat image?
    if basename.startswith('fstat'):
        opts.displayRange = [0, 10]

    # modulate alpha by intensity for regular stat images
    else:
        maxVal                 = overlay.dataRange[1]
        opts.useNegativeCmap   = True
        opts.linkLowRanges     = False
        opts.clippingRange.xlo = 0
        opts.modulateAlpha     = True
        opts.modulateRange     = [0, zthres]
        opts.displayRange      = [zthres, min((7.5, maxVal))]


def _renderedStatImageDisplay(basename, overlay, displayCtx, **kwargs):
    """Automatically configure display settings for the given FEAT
    pre-renderered stats image (e.g ``rendered_thresh_zstat1.nii.gz``).
    """
    opts      = displayCtx.getOpts(overlay)
    opts.cmap = 'Render1'


def _peImageDisplay(basename, overlay, displayCtx, **kwargs):
    """Automatically configure display settings for the given FEAT PE/COPE
    image (e.g  ``pe1.nii.gz``).
    """

    opts = displayCtx.getOpts(overlay)

    if basename.startswith('varcope'):
        maxVal                 = overlay.dataRange[1]
        opts.cmap              = 'Red-Yellow'
        opts.displayRange      = [1.0, np.sqrt(maxVal)]
        opts.clippingRange.xlo =  1.0

    else:
        opts.cmap              = 'Red-Yellow'
        opts.negativeCmap      = 'Blue-LightBlue'
        opts.useNegativeCmap   = True
        opts.displayRange      = [1.0, 100.0]
        opts.clippingRange.xlo =  1.0


def _threshStatImageDisplay(basename,
                            overlay,
                            displayCtx,
                            zthres=3.1,
                            posCmap=None,
                            negCmap=None,
                            **kwargs):
    """Automatically configure display settings for the given FEAT
    thresholded statistic image (e.g. ``thresh_zstat1.nii.gz``)
    """
    opts                   = displayCtx.getOpts(overlay)
    posCmap, negCmap       = _getStatImageColourMaps(overlay, posCmap, negCmap)
    maxVal                 = overlay.dataRange[1]
    opts.cmap              = posCmap
    opts.negativeCmap      = negCmap
    opts.useNegativeCmap   = True
    opts.clippingRange.xlo =  zthres
    opts.displayRange      = [zthres, min((7.5, maxVal))]


def _clusterMaskImageDisplay(basename, overlay, displayCtx, **kwargs):
    """Automatically configure display settings for the given FEAT
    cluster mask image (e.g. ``cluster_mask_zstat1.nii.gz``)
    """
    display             = displayCtx.getDisplay(overlay)
    display.overlayType = 'mask'
    opts                = displayCtx.getOpts(   overlay)
    opts.outline        = True
    opts.outlineWidth   = 2


def _MelodicImageDisplay(overlay, overlayList, displayCtx):
    """Automatically configure display settings for the given
    :class:`.MelodicImage` overlay.
    """

    opts             = displayCtx.getOpts(overlay)
    datamin, datamax = np.abs(overlay.dataRange)

    # Arbitrarily set display range to 3-10
    if datamax > 3:
        dispmin, dispmax = 3, 10
        modmin,  modmax  = 0, 3
    else:
        dispmin, dispmax = datamin, datamax
        modmin,  modmax  = datamin, datamax

    opts.cmap            = 'Red-Yellow'
    opts.negativeCmap    = 'Blue-LightBlue'
    opts.useNegativeCmap = True
    opts.linkLowRanges   = False
    opts.modulateAlpha   = True
    opts.displayRange    = [dispmin, dispmax]
    opts.clippingRange   = [0,       datamax]
    opts.modulateRange   = [modmin,  modmax]

    # Add the mean as an underlay
    idx      = overlayList.index(overlay)
    meanFile = overlay.getMeanFile()
    existing = [op.abspath(o.dataSource) for o in overlayList]

    # But only if it's not
    # already in the list
    if meanFile not in existing:

        log.debug('Inserting mean melodic image into '
                  'overlay list: %s', meanFile)

        meanImg = fslimage.Image(meanFile)

        with displayCtx.preserveSelection():
            overlayList.insert(idx, meanImg)
