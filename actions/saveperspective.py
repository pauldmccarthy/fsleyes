#!/usr/bin/env python
#
# saveperspective.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""


import fsl.fsleyes.actions      as actions
import fsl.fsleyes.perspectives as perspectives


class SavePerspectiveAction(actions.Action):
    """
    """

    def __init__(self, frame):
        """
        """

        self.__frame = frame
         
        actions.Action.__init__(self, self.__savePerspective)

        
    def __savePerspective(self):
        """
        """

        # TODO prompt for name
        name = 'blah'

        perspectives.savePerspective(self.__frame, name)
