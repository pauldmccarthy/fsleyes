#!/usr/bin/env python
#
# loadlayout.py - The LoadLayoutAction class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadLayoutAction` class, a FSLeyes action
which allows the user to load a built-in or previously saved layout.
"""


import fsleyes.layouts as layouts
from . import             base


class LoadLayoutAction(base.Action):
    """The ``LoadLayoutAction`` class allows the user to load a specific
    saved layout.
    """


    def __init__(self, overlayList, displayCtx, frame, layout):
        """Create a ``LoadLayoutAction`` instance.

        :arg frame:  The :class:`.FSLeyesFrame`
        :arg layout: Name of the layout to load.
        """

        self.__frame  = frame
        self.__layout = layout
        base.Action.__init__(self, overlayList, displayCtx, self.__loadLayout)


    def __loadLayout(self):
        """Load the layout specified in :meth:`__init__`. """
        layouts.loadLayout(self.__frame, self.__layout)
