#!/usr/bin/env python
#
# clearperspective.py - deprecated.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - see :mod:`.clearlayouts`. """


import fsl.utils.deprecated as deprecated

from . import clearlayouts


class ClearPerspectiveAction(clearlayouts.ClearLayoutsAction):

    @deprecated.deprecated('0.24.0', '1.0.0', 'use ClearLayoutsAction')
    def __init__(self, *args, **kwargs):
        clearlayouts.ClearLayoutsAction.__init__(self, *args, **kwargs)
