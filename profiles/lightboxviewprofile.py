#!/usr/bin/env python
#
# lightboxviewprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)



import fsl.fsleyes.profiles as profiles


class LightBoxViewProfile(profiles.Profile):
    def __init__(self, viewPanel, overlayList, displayCtx):
        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes=['view', 'zoom'])

        self._canvas = viewPanel.getCanvas()

        
    def getEventTargets(self):
        return [self._canvas]

        
    def _viewModeMouseWheel(self,
                            ev,
                            canvas,
                            wheel,
                            mousePos=None,
                            canvasPos=None):
        """Called when the mouse wheel is moved.

        Updates the top row displayed on the canvas.
        """

        if   wheel > 0: wheel = -1
        elif wheel < 0: wheel =  1

        self._viewPanel.getCanvas().topRow += wheel

        
    def _viewModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called when the mouse is clicked or dragged on the canvas.

        Updates the canvas and display context location.
        """

        if canvasPos is None:
            return

        self._displayCtx.location.xyz = canvasPos


    def _zoomModeMouseWheel(self,
                            ev,
                            canvas,
                            wheel,
                            mousePos=None,
                            canvasPos=None):
        """Called in zoom mode when the mouse wheel is moved.

        Zooms in/out of the canvas.
        """

        if   wheel > 0: wheel =  50
        elif wheel < 0: wheel = -50
        self._viewPanel.getSceneOptions().zoom += wheel 
