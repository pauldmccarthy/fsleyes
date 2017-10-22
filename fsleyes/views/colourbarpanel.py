#!/usr/bin/env python
#
# colourbar.py - The ColourBarPanel.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBarPanel`, a :class:`.FSLeyesPanel`
which renders a colour bar.
"""


import wx

import fsleyes_props                        as props
import fsleyes.panel                        as fslpanel
import fsleyes.displaycontext               as fsldc
import fsleyes.displaycontext.colourmapopts as cmapopts
import fsleyes.gl.wxglcolourbarcanvas       as cbarcanvas


class ColourBarPanel(fslpanel.FSLeyesPanel):
    """The ``ColourBarPanel`` is a panel which shows a colour bar, depicting
    the data range of the currently selected overlay (if applicable). A
    :class:`.ColourBarCanvas` is used to render the colour bar.


    .. note:: Currently, the ``ColourBarPanel`` will only display a colour bar
              for overlays which are associated with a :class:`.ColourMapOpts`
              instance.
    """


    orientation = cbarcanvas.WXGLColourBarCanvas.orientation
    """Colour bar orientation - see :attr:`.ColourBarCanvas.orientation`. """


    labelSide   = cbarcanvas.WXGLColourBarCanvas.labelSide
    """Colour bar label side - see :attr:`.ColourBarCanvas.labelSide`."""


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 frame,
                 orientation='horizontal'):
        """Create a ``ColourBarPanel``.

        :arg parent:      The :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame`.

        :arg orientation: Initial orientation - either ``'horizontal'`` (the
                          default) or ``'vertical'``.
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__cbCanvas = cbarcanvas.WXGLColourBarCanvas(self)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__cbCanvas, flag=wx.EXPAND, proportion=1)

        self.bindProps('orientation', self.__cbCanvas)
        self.bindProps('labelSide',   self.__cbCanvas)

        self.addListener('orientation', self.name, self.__layout)

        self.overlayList.addListener('overlays',
                                     self.name,
                                     self.__selectedOverlayChanged)
        self.displayCtx .addListener('selectedOverlay',
                                     self.name,
                                     self.__selectedOverlayChanged)

        self.__selectedOverlay = None

        self.__layout()
        self.__selectedOverlayChanged()


    def getCanvas(self):
        """Returns the :class:`.ColourBarCanvas` which displays the rendered
        colour bar.
        """
        return self.__cbCanvas


    def destroy(self):
        """Must be called when this ``ColourBarPanel`` is no longer needed.

        Removes all registered listeners from the :class:`.OverlayList`,
        :class:`.DisplayContext`, and foom individual overlays.
        """


        self.overlayList.removeListener('overlays',        self.name)
        self.displayCtx .removeListener('selectedOverlay', self.name)

        overlay = self.__selectedOverlay

        if overlay is not None:
            try:
                display = self.displayCtx.getDisplay(overlay)
                opts    = display.opts

                if isinstance(opts, cmapopts.ColourMapOpts):
                    opts   .removeListener('displayRange',    self.name)
                    opts   .removeListener('cmap',            self.name)
                    opts   .removeListener('negativeCmap',    self.name)
                    opts   .removeListener('useNegativeCmap', self.name)
                    opts   .removeListener('invert',          self.name)
                    opts   .removeListener('cmapResolution',  self.name)
                    display.removeListener('name',            self.name)

            except fsldc.InvalidOverlayError:
                pass

        self.__cbCanvas      .destroy()
        fslpanel.FSLeyesPanel.destroy(self)


    def __layout(self, *a):
        """Called when this ``ColourBarPanel`` needs to be laid out.
        Sets the panel size, and calls the :meth:`__refreshColourBar` method.
        """

        # Fix the minor axis of the colour bar to 75 pixels
        if self.orientation == 'horizontal':
            self.__cbCanvas.SetSizeHints(-1, 60, -1, 60, -1, -1)
        else:
            self.__cbCanvas.SetSizeHints(60, -1, 60, -1, -1, -1)

        self.Layout()
        self.__refreshColourBar()


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.selectedOverlay` changes.

        If the newly selected overlay is being displayed with a
        :class:`.ColourMapOpts` instance, various property listeners are
        registered, and the :class:`.ColourBarCanvas` is refreshed.
        """

        overlay = self.__selectedOverlay

        if overlay is not None:
            try:
                display = self.displayCtx.getDisplay(overlay)
                opts    = display.opts

                opts   .removeListener('displayRange',    self.name)
                opts   .removeListener('cmap',            self.name)
                opts   .removeListener('negativeCmap',    self.name)
                opts   .removeListener('useNegativeCmap', self.name)
                opts   .removeListener('invert',          self.name)
                opts   .removeListener('cmapResolution',  self.name)
                display.removeListener('name',            self.name)

            # The previously selected overlay
            # has been removed from the list,
            # so its Display/Opts instances
            # have been thrown away
            except fsldc.InvalidOverlayError:
                pass

        self.__selectedOverlay = None

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            self.__refreshColourBar()
            return

        display = self.displayCtx.getDisplay(overlay)
        opts    = display.opts

        if not isinstance(opts, cmapopts.ColourMapOpts):
            self.__refreshColourBar()
            return

        self.__selectedOverlay = overlay

        # TODO register on overlayType property, in
        # case the overlay type changes to a type
        # that has a display range and colour map

        opts   .addListener('displayRange',
                            self.name,
                            self.__refreshColourBar)
        opts   .addListener('cmap',
                            self.name,
                            self.__refreshColourBar)
        opts   .addListener('negativeCmap',
                            self.name,
                            self.__refreshColourBar)
        opts   .addListener('useNegativeCmap',
                            self.name,
                            self.__refreshColourBar)
        opts   .addListener('invert',
                            self.name,
                            self.__refreshColourBar)
        opts   .addListener('cmapResolution',
                            self.name,
                            self.__refreshColourBar)
        display.addListener('name',
                            self.name,
                            self.__refreshColourBar)

        self.__refreshColourBar()


    def __refreshColourBar(self, *a):
        """Called when the :class:`.ColourBarCanvas` needs to be refreshed. """

        cmap            = None
        negativeCmap    = None
        useNegativeCmap = False
        cmapResolution  = 256
        invert          = False
        dmin, dmax      = 0.0, 0.0
        label           = ''

        overlay = self.__selectedOverlay

        if overlay is not None:
            display         = self.displayCtx.getDisplay(overlay)
            opts            = self.displayCtx.getOpts(   overlay)
            cmap            = opts.cmap
            negativeCmap    = opts.negativeCmap
            useNegativeCmap = opts.useNegativeCmap
            cmapResolution  = opts.cmapResolution
            invert          = opts.invert
            dmin, dmax      = opts.displayRange.x
            label           = display.name

        with props.suppressAll(self.__cbCanvas):
            self.__cbCanvas.cmap            = cmap
            self.__cbCanvas.negativeCmap    = negativeCmap
            self.__cbCanvas.useNegativeCmap = useNegativeCmap
            self.__cbCanvas.cmapResolution  = cmapResolution
            self.__cbCanvas.invert          = invert
            self.__cbCanvas.vrange          = dmin, dmax
            self.__cbCanvas.label           = label

        # Using inside knowledge about the
        # ColourBarCanvas here - it will
        # refresh itself on any property
        # change.
        self.__cbCanvas.propNotify('cmap')
