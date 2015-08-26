#!/usr/bin/env python
#
# labelopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

import volumeopts

import fsl.fsleyes.colourmaps as fslcm


class LabelOpts(volumeopts.ImageOpts):

    lut          = props.Choice()
    outline      = props.Boolean(default=False)
    outlineWidth = props.Real(minval=0, maxval=1, default=0.25, clamped=True)
    showNames    = props.Boolean(default=False)


    def __init__(self, overlay, *args, **kwargs):
        volumeopts.ImageOpts.__init__(self, overlay, *args, **kwargs)

        luts  = fslcm.getLookupTables()
        alts  = [[l.name, l.key] for l in luts]

        lutChoice = self.getProp('lut')
        lutChoice.setChoices(luts, alternates=alts)
