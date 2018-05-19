#!/usr/bin/env python
#
# saveperspective.py - deprecated.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - see :mod:`.savelayout`. """


import deprecation


from . import savelayout


class SavePerspectiveAction(savelayout.SaveLayoutAction):

    @deprecation.deprecated(deprecated_in='0.24.0',
                            removed_in='1.0.0',
                            details='use SaveLayoutAction')
    def __init__(self, *args, **kwargs):
        savelayout.SaveLayoutAction.__init__(self, *args, **kwargs)
