#!/usr/bin/env python
#
# perspectives.py - Deprecated - use layouts.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - see the :mod:`.layouts` module. """


import fsl.utils.deprecated as deprecated

from . import layouts


def deprecate(func):
    return deprecated.deprecated(
        '0.24.0', '1.0.0', 'Use the fsleyes.layout module')(func)


getAllPerspectives     = deprecate(layouts.getAllLayouts)
loadPerspective        = deprecate(layouts.loadLayout)
applyPerspective       = deprecate(layouts.applyLayout)
savePerspective        = deprecate(layouts.saveLayout)
removePerspective      = deprecate(layouts.removeLayout)
serialisePerspective   = deprecate(layouts.serialiseLayout)
deserialisePerspective = deprecate(layouts.deserialiseLayout)
BUILT_IN_PERSPECTIVES  =           layouts.BUILT_IN_LAYOUTS
