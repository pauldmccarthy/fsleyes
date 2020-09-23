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


import re
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
    func  = getattr(sys.modules[__name__], '_{}Display'.format(oType), None)

    if func is None:
        log.warn('Unknown overlay type: {}'.format(oType))
        return

    log.debug('Applying default display arguments for {}'.format(overlay))
    func(overlay, overlayList, displayCtx, **kwargs)


def _ImageDisplay(overlay, overlayList, displayCtx, **kwargs):
    """Configure default display settings for the given :class:`.Image`
    overlay.
    """

    if _isStatImage(overlay):
        _statImageDisplay(overlay, overlayList, displayCtx, **kwargs)
    elif _isPEImage(overlay):
        _peImageDisplay(  overlay, overlayList, displayCtx, **kwargs)

    # Automatically configure nice display range?


def _isStatImage(overlay):
    """Returns ``True`` if the given :class:`.Image` overlay looks like a
    statistic image, ``False`` otherwise.
    """

    basename = op.basename(overlay.dataSource)
    basename = fslimage.removeExt(basename)
    tokens   = ['zstat', 'tstat', 'fstat', 'zfstat']
    pattern  = r'({})\d+'.format('|'.join(tokens))

    return re.search(pattern, basename) is not None


def _isPEImage(overlay):
    """Returns ``True`` if the given :class:`.Image` overlay looks like a
    statistic image, ``False`` otherwise.
    """
    basename = op.basename(overlay.dataSource)
    basename = fslimage.removeExt(basename)
    tokens   = ['cope', 'pe']
    pattern  = r'^({})\d+'.format('|'.join(tokens))

    return re.search(pattern, basename) is not None


def _statImageDisplay(overlay,
                      overlayList,
                      displayCtx,
                      zthres=3.0,
                      posCmap=None,
                      negCmap=None):
    """Configure default display settings for the given statistic
    :class:`.Image` overlay.
    """

    opts        = displayCtx.getOpts(overlay)
    basename    = op.basename(overlay.dataSource)
    basename    = fslimage.removeExt(basename)

    pTokens     = ['p', 'corrp']
    statTokens  = ['zstat', 'tstat', 'zfstat']
    fStatTokens = ['fstat']

    # Rendered stat images (e.g.
    # rendered_thres_zstat1) are
    # generated specifically for
    # use with the Render1 colour
    # map.
    if 'rendered' in basename:
        opts.cmap = 'Render1'

    # Give each normal stat image
    # a different colour map
    else:
        cmap = _statImageDisplay.cmaps[_statImageDisplay.currentCmap]

        if posCmap is None: posCmap = cmap
        if negCmap is None: negCmap = cmap

        _statImageDisplay.currentCmap += 1
        _statImageDisplay.currentCmap %= len(_statImageDisplay.cmaps)
        opts.cmap                      = posCmap
        opts.negativeCmap              = negCmap

    # The order of these tests is
    # important, due to name overlap

    # P-value image ?
    if any([token in basename for token in pTokens]):
        opts.displayRange  = [0.95, 1.0]
        opts.clippingRange = [0.95, 1.0]

    # T or Z stat image?
    elif any([token in basename for token in statTokens]) and \
       'rendered' not in basename:

        maxVal               = overlay.dataRange[1]
        opts.useNegativeCmap = True
        opts.clippingRange   = [zthres, maxVal]
        opts.displayRange    = [zthres, min((7.5, maxVal))]

    # F stat image?
    elif any([token in basename for token in fStatTokens]):
        opts.displayRange = [0, 10]


# Colour maps used for statistic images
_statImageDisplay.cmaps = ['red-yellow',
                           'blue-lightblue',
                           'green',
                           'cool',
                           'hot',
                           'blue',
                           'red',
                           'yellow',
                           'pink',
                           'copper']


# Index into the cmaps list, pointing to the
# next colour map to use for statistic images.
_statImageDisplay.currentCmap = 0


def _peImageDisplay(overlay, overlayList, displayCtx):
    """Automatically configure display settings for the given PE/COPE
    :class:`.Image` overlay.
    """
    opts = displayCtx.getOpts(overlay)

    opts.cmap            = 'Red-Yellow'
    opts.negativeCmap    = 'Blue-LightBlue'
    opts.useNegativeCmap = True
    opts.displayRange    = [1.0, 100.0]
    opts.clippingRange   = [1.0, overlay.dataRange[1]]


def _FEATImageDisplay(overlay, overlayList, displayCtx):
    """Automatically configure display settings for the given
    :class:`.FEATImage` overlay.
    """
    pass


def _MelodicImageDisplay(overlay, overlayList, displayCtx):
    """Automatically configure display settings for the given
    :class:`.MelodicImage` overlay.
    """

    opts        = displayCtx.getOpts(overlay)
    dmin, dmax  = np.abs(overlay.dataRange)

    # clip low values by default
    if dmax > 3:
        dmin = 3
        dmax = 10

    opts.cmap            = 'Red-Yellow'
    opts.negativeCmap    = 'Blue-LightBlue'
    opts.useNegativeCmap = True
    opts.displayRange    = [dmin, dmax]
    opts.clippingRange   = [dmin, dmax]

    # Add the mean as an underlay
    idx      = overlayList.index(overlay)
    meanFile = overlay.getMeanFile()
    existing = [op.abspath(o.dataSource) for o in overlayList]

    # But only if it's not
    # already in the list
    if meanFile not in existing:

        log.debug('Inserting mean melodic image into '
                  'overlay list: {}'.format(meanFile))

        meanImg = fslimage.Image(meanFile)
        overlayList.insert(idx, meanImg)
