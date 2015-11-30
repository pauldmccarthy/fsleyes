#!/usr/bin/env python
#
# displaydefaults.py - Routines for configuring default overlay display
#                      settings.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`displayDefaults` function, which is used
for configuring default overlay display settings.

The :displayDefaults` function is called when *FSLeyes* is started, and when 
new overlays are loaded.
"""


import re
import sys
import logging

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


def displayDefaults(overlay, overlayList, displayCtx):
    """Configure default display settings for the given overlay.

    :arg overlay:     The overlay object (e.g. an :class:`.Image` instance).
    :arg overlayList: The :class:`.OverlayList`.
    :arg displayCtx:  The :class:`.DisplayContext`.
    """     

    oType = type(overlay).__name__
    func  = getattr(sys.modules[__name__], '_{}Defaults'.format(oType), None)

    if func is None:
        log.warn('Unknown overlay type: {}'.format(oType))
        return

    log.debug('Applying default display arguments for {}'.format(overlay))
    func(overlay, overlayList, displayCtx)


def _ImageDefaults(overlay, overlayList, displayCtx):
    """Configure default display settings for the given :class:`.Image`
    overlay.
    """

    if _isStatImage(overlay):
        _statImageDefaults(overlay, overlayList, displayCtx)
        

def _isStatImage(overlay):
    """Returns ``True`` if the given :class:`.Image` overlay looks like a
    statistic image, ``False`` otherwise.
    """
    
    basename = fslimage.removeExt(overlay.dataSource)
    tokens   = ['zstat', 'tstat', 'fstat', 'zfstat']
    pattern  = '_({})\d+'.format('|'.join(tokens))

    return re.search(pattern, basename) is not None


def _statImageDefaults(overlay, overlayList, displayCtx):
    """Configure default display settings for the given statistic
    :class:`.Image` overlay.
    """ 

    opts     = displayCtx.getOpts(overlay)
    basename = fslimage.removeExt(overlay.dataSource)
    cmap     = _statImageDefaults.cmaps[_statImageDefaults.currentCmap]

    nameTokens = '_'.split(basename)

    # Give each stat image
    # a different colour map
    _statImageDefaults.currentCmap += 1
    _statImageDefaults.currentCmap %= len(_statImageDefaults.cmaps)
    opts.cmap                       = cmap

    pTokens          = ['p', 'corrp']
    statTokens       = ['zstat', 'tstat', 'zfstat']
    fStatTokens      = ['fstat']

    # The order of these tests is
    # important, due to name overlap

    # P-value image ?
    if any([token in nameTokens for token in pTokens]):
        opts.displayRange  = [0.95, 1.0]
        opts.clippingRange = [0.95, 1.0]

    # T or Z stat image?
    elif any([token in nameTokens for token in statTokens]):
        
        opts.clippingRange  = [-0.1, 0.1]
        opts.displayRange   = [-7.5, 7.5]
        opts.centreRanges   = True
        opts.invertClipping = True

    # F stat image?
    elif any([token in nameTokens for token in fStatTokens]):
        opts.displayRange = [0, 10]


# Colour maps used for statistic images
_statImageDefaults.cmaps = ['red-yellow',
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
_statImageDefaults.currentCmap = 0


def _FEATImageDefaults(overlay, overlayList, displayCtx):
    """Configure default display settings for the given :class:`.FEATImage`
    overlay.
    """
    pass


def _MelodicImageDefaults(overlay, overlayList, displayCtx):
    """Configure default display settings for the given :class:`.MelodicImage`
    overlay.
    """ 

    opts = displayCtx.getOpts(overlay)

    opts.cmap           = 'Render3'
    opts.displayRange   = [-5.0, 5.0]
    opts.clippingRange  = [-1.5, 1.5]

    opts.centreRanges   = True
    opts.invertClipping = True


def _ModelDefaults(overlay, display, overlayList, displayCtx):
    """Configure default display settings for the given :class:`.Model`
    overlay.
    """

    # TODO some nice default colours
    pass
