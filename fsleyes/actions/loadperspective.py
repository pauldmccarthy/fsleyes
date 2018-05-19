#!/usr/bin/env python
#
# loadperspective.py - deprecated.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Deprecated - see :mod:`.loadlayout`. """


import deprecation


from . import loadlayout


class LoadPerspectiveAction(loadlayout.LoadLayoutAction):

    @deprecation.deprecated(deprecated_in='0.24.0',
                            removed_in='1.0.0',
                            details='use LoadLayoutAction')
    def __init__(self, *args, **kwargs):
        loadlayout.LoadLayoutAction.__init__(self, *args, **kwargs)
