#!/usr/bin/env python
#
# loadperspective.py - deprecated.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - see :mod:`.loadlayout`. """


import fsl.utils.deprecated as deprecated


from . import loadlayout


class LoadPerspectiveAction(loadlayout.LoadLayoutAction):

    @deprecated.deprecated('0.24.0', '1.0.0', 'use LoadLayoutAction')
    def __init__(self, *args, **kwargs):
        loadlayout.LoadLayoutAction.__init__(self, *args, **kwargs)
