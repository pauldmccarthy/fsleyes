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

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


def autoDisplay(overlay, overlayList, displayCtx):
    """Automatically configure display settings for the given overlay.

    :arg overlay:     The overlay object (e.g. an :class:`.Image` instance).
    :arg overlayList: The :class:`.OverlayList`.
    :arg displayCtx:  The :class:`.DisplayContext`.
    """     

    oType = type(overlay).__name__
    func  = getattr(sys.modules[__name__], '_{}Display'.format(oType), None)

    if func is None:
        log.warn('Unknown overlay type: {}'.format(oType))
        return

    log.debug('Applying default display arguments for {}'.format(overlay))
    func(overlay, overlayList, displayCtx)


def _ImageDisplay(overlay, overlayList, displayCtx):
    """Configure default display settings for the given :class:`.Image`
    overlay.
    """

    if _isStatImage(overlay):
        _statImageDisplay(overlay, overlayList, displayCtx)
    elif _isPEImage(overlay):
        _peImageDisplay(  overlay, overlayList, displayCtx)

    # Automatically configure nice display range?
        

def _isStatImage(overlay):
    """Returns ``True`` if the given :class:`.Image` overlay looks like a
    statistic image, ``False`` otherwise.
    """
    
    basename = op.basename(overlay.dataSource)
    basename = fslimage.removeExt(basename)
    tokens   = ['zstat', 'tstat', 'fstat', 'zfstat']
    pattern  = '_({})\d+'.format('|'.join(tokens))

    return re.search(pattern, basename) is not None


def _isPEImage(overlay):
    """Returns ``True`` if the given :class:`.Image` overlay looks like a
    statistic image, ``False`` otherwise.
    """ 
    basename = op.basename(overlay.dataSource)
    basename = fslimage.removeExt(basename)
    tokens   = ['cope', 'pe']
    pattern  = '^({})\d+'.format('|'.join(tokens))

    return re.search(pattern, basename) is not None 


def _statImageDisplay(overlay, overlayList, displayCtx):
    """Configure default display settings for the given statistic
    :class:`.Image` overlay.
    """ 

    opts        = displayCtx.getOpts(overlay)
    basename    = op.basename(overlay.dataSource)
    basename    = fslimage.removeExt(basename)
    
    nameTokens  = basename.split('_')
    pTokens     = ['p', 'corrp']
    statTokens  = ['zstat', 'tstat', 'zfstat']
    fStatTokens = ['fstat']

    # Rendered stat images (e.g.
    # rendered_thres_zstat1) are
    # generated specifically for
    # use with the Render1 colour
    # map.
    if 'rendered' in nameTokens:
        opts.cmap = 'Render1'
    
    # Give each normal stat image
    # a different colour map 
    else:
        cmap = _statImageDisplay.cmaps[_statImageDisplay.currentCmap]
        
        _statImageDisplay.currentCmap += 1
        _statImageDisplay.currentCmap %= len(_statImageDisplay.cmaps)
        opts.cmap                      = cmap
        
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

    opts.cmap           = 'Render3'
    opts.clippingRange  = [-1,   1]
    opts.displayRange   = [-100, 100]
    opts.centreRanges   = True
    opts.invertClipping = True


def _FEATImageDisplay(overlay, overlayList, displayCtx):
    """Automatically configure display settings for the given
    :class:`.FEATImage` overlay.
    """
    pass


def _MelodicImageDisplay(overlay, overlayList, displayCtx):
    """Automatically configure display settings for the given
    :class:`.MelodicImage` overlay.
    """ 

    opts = displayCtx.getOpts(overlay)

    opts.cmap           = 'Render3'
    opts.displayRange   = [-5.0, 5.0]
    opts.clippingRange  = [-1.5, 1.5]

    opts.centreRanges   = True
    opts.invertClipping = True


def _ModelDisplay(overlay, display, overlayList, displayCtx):
    """Automatically configure display settings for the given :class:`.Model`
    overlay.
    """

    # TODO some nice default colours?
    pass
