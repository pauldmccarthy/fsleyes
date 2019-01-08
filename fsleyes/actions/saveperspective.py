#!/usr/bin/env python
#
# saveperspective.py - deprecated.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - see :mod:`.savelayout`. """


import fsl.utils.deprecated as deprecated


from . import savelayout


class SavePerspectiveAction(savelayout.SaveLayoutAction):

    @deprecated.deprecated('0.24.0', '1.0.0', 'use SaveLayoutAction')
    def __init__(self, *args, **kwargs):
        savelayout.SaveLayoutAction.__init__(self, *args, **kwargs)
