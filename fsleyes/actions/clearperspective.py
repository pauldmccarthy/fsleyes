#!/usr/bin/env python
#
# clearperspective.py - deprecated.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - see :mod:`.clearlayouts`. """


import deprecation


from . import clearlayouts


class ClearPerspectiveAction(clearlayouts.ClearLayoutsAction):

    @deprecation.deprecated(deprecated_in='0.24.0',
                            removed_in='1.0.0',
                            details='use ClearLayoutsAction')
    def __init__(self, *args, **kwargs):
        clearlayouts.ClearLayoutsAction.__init__(self, *args, **kwargs)
