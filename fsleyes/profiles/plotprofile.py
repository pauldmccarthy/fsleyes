#!/usr/bin/env python
#
# plotprofile.py - The PlotProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains the :class:`PlotProfile` class, a :class:`.Profile`
for use with :class:`.PlotPanel` views.
"""


from matplotlib.backends.backend_wx import NavigationToolbar2Wx

import fsleyes_props    as props
import fsleyes.profiles as profiles


class PlotProfile(profiles.Profile):
    """The ``PlotProfile`` class is the default interaction profile for
    :class:`.PlotPanel` vies. It provides pan and zoom functionality via
    a single :attr:`.Profile.mode` called ``panzoom``:

     - Left click and drag to pan the plot

     - Right click and drag to zoom the plot.
    """

    def __init__(self,
                 viewPanel,
                 overlayList,
                 displayCtx,
                 extraModes=None):
        """Create a ``PlotProfile``.

        :arg viewPanel:    A :class:`.PlotPanel` instance.

        :arg overlayList:  The :class:`.OverlayList` instance.

        :arg displayCtx:   The :class:`.DisplayContext` instance.

        :arg extraModes:   Extra modes to pass through to the
                           :class:`.Profile` constructor.
        """

        if extraModes is None:
            extraModes = []

        modes = ['panzoom'] + extraModes

        profiles.Profile.__init__(self,
                                  viewPanel,
                                  overlayList,
                                  displayCtx,
                                  modes)

        self.__canvas  = viewPanel.getCanvas()
        self.__axis    = viewPanel.getAxis()

        # Pan/zoom functionality is actually
        # implemented by the NavigationToolbar2Wx
        # class, but the toolbar is not actually
        # shown.
        self.__toolbar = NavigationToolbar2Wx(self.__canvas)
        self.__toolbar.Show(False)

        # This flag keeps track of
        # the toolbar pan state
        self.__panning = False


    def destroy(self):
        """Must be called when this ``PlotProfile`` is no longer needed. Clears
        references and calls the base class ``destroy`` method.
        """

        self.__toolbar.Destroy()

        self.__canvas  = None
        self.__axis    = None
        self.__toolbar = None

        profiles.Profile.destroy(self)


    def getEventTargets(self):
        """Overrides :meth:`.Profile.getEventTargets`. Returns the
        ``matplotlib`` ``Canvas`` object displayed in the :class:`.PlotPanel`.
        """

        return [self.__canvas]


    def __updateAxisLimits(self):
        """Called by the ``panzoom`` ``MouseDrag`` event handlers. Makes sure
        that the :attr:`.PlotPanel.limits` property is up to date.
        """

        xlims = list(self.__axis.get_xlim())
        ylims = list(self.__axis.get_ylim())

        with props.suppress(self.viewPanel, 'limits'):
            self.viewPanel.limits.x = xlims
            self.viewPanel.limits.y = ylims


    def _panzoomModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse clicks. Enables panning. """

        if not self.__panning:
            self.__toolbar.pan()
            self.__toolbar.press_pan(self.getMplEvent())
            self.__panning = True


    def _panzoomModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse drags. Updates the
        :attr:`.PlotPanel.limits` property - the panning logic is provided
        by the ``matplotlib`` ``NavigationToolbar2wx`` class.
        """
        self.__updateAxisLimits()


    def _panzoomModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Called on left mouse up events. Disables panning."""

        if self.__panning:
            self.__toolbar.pan()
            self.__panning = False


    def _panzoomModeRightMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Called on right mouse clicks. Enables zooming. """

        if not self.__panning:
            self.__toolbar.pan()
            self.__toolbar.press_pan(self.getMplEvent())
            self.__panning = True


    def _panzoomModeRightMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Called on right mouse drags. Updates the
        :attr:`.PlotPanel.limits` property - the zooming logic is provided
        by the ``matplotlib`` ``NavigationToolbar2wx`` class.
        """
        self.__updateAxisLimits()


    def _panzoomModeRightMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Called on right mouse up events. Disables panning. """
        if self.__panning:
            self.__toolbar.pan()
            self.__panning = False
