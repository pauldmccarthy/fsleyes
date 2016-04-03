#!/usr/bin/env python
#
# loadperspective.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""


import fsleyes.perspectives as perspectives
from . import                  action


class LoadPerspectiveAction(action.Action):
    """
    """

    def __init__(self, frame, perspective):
        """
        """

        self.__frame       = frame
        self.__perspective = perspective
         
        action.Action.__init__(self, self.__loadPerspective)

        
    def __loadPerspective(self):
        """
        """
        perspectives.loadPerspective(self.__frame, self.__perspective)
