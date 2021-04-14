#!/usr/bin/env python
#
# lightboxviewprofile.py - The LightBoxViewProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LightBoxViewProfile` class, an interaction
:class:`.Profile` for :class:`.LightBoxPanel` views.
"""

import logging

import wx

import fsleyes.profiles as profiles
import fsl.utils.idle   as idle


log = logging.getLogger(__name__)


class LightBoxViewProfile(profiles.Profile):
    """The ``LightBoxViewProfile`` is an interaction profile for
    :class:`.LightBoxPanel` views. It defines mouse/keyboard handlers which
    allow the user to navigate through the ``LightBoxPanel`` display of the
    overlays in the :class:`.OverlayList`.

    ``LightBoxViewProfile`` defines two *modes* (see the :class:`.Profile`
    class documentation):

    ======== ==================================================================
    ``view`` The user can change the :attr:`.DisplayContext.location` via
             left mouse drags, and can change the
             :attr:`.LightBoxCanvasOpts.topRow` via the mouse wheel.

    ``zoom`` The user can change the :attr:`.LightBoxCanvasOpts.ncols` property
             with the mouse wheel (effectively zooming in/out of the canvas).
    ======== ==================================================================
    """


    @staticmethod
    def supportedView():
        """Returns the :class:`.LightBoxPanel` class. """
        import fsleyes.views.lightboxpanel as lightboxpanel
        return lightboxpanel.LightBoxPanel


    @staticmethod
    def tempModes():
        """Returns the temporary mode map for the ``LightBoxViewProfile``,
        which controls the use of modifier keys to temporarily enter other
        interaction modes.
        """
        # Command/CTRL puts the user in zoom mode,
        # and ALT puts the user in pan mode
        return {('view', wx.WXK_CONTROL) : 'zoom'}


    @staticmethod
    def altHandlers():
        """Returns the alternate handlers map, which allows event handlers
        defined in one mode to be re-used whilst in another mode.
        """
        return { ('view', 'LeftMouseDown') :('view', 'LeftMouseDrag')}


    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create a ``LightBoxViewProfile``.

        :arg viewPanel:    A :class:`.LightBoxPanel` instance.
        :arg overlayList:  The :class:`.OverlayList` instance.
        :arg displayCtx:   The :class:`.DisplayContext` instance.
        """

        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes=['view', 'zoom'])

        self.__canvas = viewPanel.getCanvas()


    def getEventTargets(self):
        """Returns the :class:`.LightBoxCanvas` contained in the
        :class:`.LightBoxPanel`, which is the target for all mouse/keyboard
        events.
        """
        return [self.__canvas]


    def _viewModeMouseWheel(self,
                            ev,
                            canvas,
                            wheel,
                            mousePos=None,
                            canvasPos=None):
        """Handles mouse wheel events in ``view`` mode.

        Updates the :attr:.LightBoxCanvasOpts.topRow` property, thus scrolling
        through the slices displayed on the canvas.
        """

        # When we scroll up, we move to lower slices,
        # so a positive scroll direction corresponds
        # to negative slice direction, and vice versa.
        if   wheel > 0: wheel = -1
        elif wheel < 0: wheel =  1
        else:           return False

        opts = self.__canvas.opts

        # See comment in OrthoViewProfile._zoomModeMouseWheel
        # about timeout
        def update():
            opts.topRow += wheel

        idle.idle(update, timeout=0.1)

        return True


    def _viewModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles left mouse drags in ``view`` mode.

        Updates the :attr:`.DisplayContext.location` property to track the
        mouse location.
        """

        if canvasPos is None:
            return False

        self.displayCtx.location.xyz = canvasPos

        return True


    def _zoomModeMouseWheel(self,
                            ev,
                            canvas,
                            wheel,
                            mousePos=None,
                            canvasPos=None):
        """Handles mouse wheel events in ``zoom`` mode.

        Zooms in/out of the canvas by updating the :attr:`.SceneOpts.zoom`
        property.
        """

        if   wheel > 0: wheel =  50
        elif wheel < 0: wheel = -50
        else:           return False

        opts = self.viewPanel.sceneOpts

        # see comment in OrthoViewProfile._zoomModeMouseWheel
        # about timeout
        def update():
            opts.zoom += wheel

        idle.idle(update, timeout=0.1)

        return True
