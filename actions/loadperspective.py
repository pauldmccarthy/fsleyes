#!/usr/bin/env python
#
# loadperspective.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""


import fsl.fsleyes.actions      as actions
import fsl.fsleyes.perspectives as perspectives


class LoadPerspectiveAction(actions.Action):
    """
    """

    def __init__(self, frame, perspective):
        """
        """

        self.__frame       = frame
        self.__perspective = perspective
         
        actions.Action.__init__(self, self.__loadPerspective)

        
    def __loadPerspective(self):
        """
        """
        perspectives.loadPerspective(self.__frame, self.__perspective)
