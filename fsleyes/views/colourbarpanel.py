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

import fsl.data.image                     as fslimage
import fsleyes_props                      as props

import fsleyes.panel                      as fslpanel
import fsleyes.displaycontext             as fsldc
import fsleyes.displaycontext.volumeopts  as volumeopts
import fsleyes.gl.wxglcolourbarcanvas     as cbarcanvas


class ColourBarPanel(fslpanel.FSLeyesPanel):
    """The ``ColourBarPanel`` is a panel which shows a colour bar, depicting
    the data range of the currently selected overlay (if applicable). A
    :class:`.ColourBarCanvas` is used to render the colour bar.


    .. note:: Currently, the ``ColourBarPanel`` will only display a colour bar
              for :class:`.Image` overlays which are being displayed with a
              ``'volume'`` overlay type (see the :class:`.VolumeOpts` class).
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

        self.__cbPanel = cbarcanvas.WXGLColourBarCanvas(self)

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__cbPanel, flag=wx.EXPAND, proportion=1)

        self.bindProps('orientation', self.__cbPanel)
        self.bindProps('labelSide'  , self.__cbPanel)

        self.SetBackgroundColour('black')

        self.addListener('orientation', self._name, self.__layout)

        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__selectedOverlayChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__selectedOverlayChanged)

        self.__selectedOverlay = None

        self.__layout()
        self.__selectedOverlayChanged()


    def getCanvas(self):
        """Returns the :class:`.ColourBarCanvas` which displays the rendered
        colour bar.
        """
        return self.__cbPanel


    def destroy(self):
        """Must be called when this ``ColourBarPanel`` is no longer needed.

        Removes all registered listeners from the :class:`.OverlayList`,
        :class:`.DisplayContext`, and foom individual overlays.
        """


        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        overlay = self.__selectedOverlay

        if overlay is not None:
            try:
                display = self._displayCtx.getDisplay(overlay)
                opts    = display.getDisplayOpts()

                if isinstance(opts, volumeopts.VolumeOpts):
                    opts   .removeListener('displayRange',    self._name)
                    opts   .removeListener('cmap',            self._name)
                    opts   .removeListener('negativeCmap',    self._name)
                    opts   .removeListener('useNegativeCmap', self._name)
                    opts   .removeListener('invert',          self._name)
                    opts   .removeListener('cmapResolution',  self._name)
                    display.removeListener('name',            self._name)

            except fsldc.InvalidOverlayError:
                pass

        self.__cbPanel       .destroy()
        fslpanel.FSLeyesPanel.destroy(self)


    def __layout(self, *a):
        """Called when this ``ColourBarPanel`` needs to be laid out.
        Sets the panel size, and calls the :meth:`__refreshColourBar` method.
        """

        # Fix the minor axis of the colour bar to 75 pixels
        if self.orientation == 'horizontal':
            self.__cbPanel.SetSizeHints(-1, 60, -1, 60, -1, -1)
        else:
            self.__cbPanel.SetSizeHints(60, -1, 60, -1, -1, -1)

        self.Layout()
        self.__refreshColourBar()


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or the
        :attr:`.DisplayContext.selectedOverlay` changes.

        If the newly selected overlay is an :class:`.Image` which is being
        displayed as a ``'volume'``, registers some listeners on the
        properties of the associated :class:`.Display` and
        :class:`.VolumeOpts` instanaces, and refreshes the
        :class:`.ColourBarCanvas`.
        """

        overlay = self.__selectedOverlay

        if overlay is not None:
            try:
                display = self._displayCtx.getDisplay(overlay)
                opts    = display.getDisplayOpts()

                opts   .removeListener('displayRange',    self._name)
                opts   .removeListener('cmap',            self._name)
                opts   .removeListener('negativeCmap',    self._name)
                opts   .removeListener('useNegativeCmap', self._name)
                opts   .removeListener('invert',          self._name)
                opts   .removeListener('cmapResolution',  self._name)
                display.removeListener('name',            self._name)

            # The previously selected overlay
            # has been removed from the list,
            # so its Display/Opts instances
            # have been thrown away
            except fsldc.InvalidOverlayError:
                pass

        self.__selectedOverlay = None

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            self.__refreshColourBar()
            return

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        # TODO support for other overlay types
        # TODO support for other types (where applicable)
        if not isinstance(overlay, fslimage.Image) or \
           not isinstance(opts,    volumeopts.VolumeOpts):
            self.__refreshColourBar()
            return

        self.__selectedOverlay = overlay

        # TODO register on overlayType property, in
        # case the overlay type changes to a type
        # that has a display range and colour map

        opts   .addListener('displayRange',
                            self._name,
                            self.__refreshColourBar)
        opts   .addListener('cmap',
                            self._name,
                            self.__refreshColourBar)
        opts   .addListener('negativeCmap',
                            self._name,
                            self.__refreshColourBar)
        opts   .addListener('useNegativeCmap',
                            self._name,
                            self.__refreshColourBar)
        opts   .addListener('invert',
                            self._name,
                            self.__refreshColourBar)
        opts   .addListener('cmapResolution',
                            self._name,
                            self.__refreshColourBar)
        display.addListener('name',
                            self._name,
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
            display         = self._displayCtx.getDisplay(overlay)
            opts            = self._displayCtx.getOpts(   overlay)
            cmap            = opts.cmap
            negativeCmap    = opts.negativeCmap
            useNegativeCmap = opts.useNegativeCmap
            cmapResolution  = opts.cmapResolution
            invert          = opts.invert
            dmin, dmax      = opts.displayRange.x
            label           = display.name

        with props.suppressAll(self.__cbPanel):
            self.__cbPanel.cmap            = cmap
            self.__cbPanel.negativeCmap    = negativeCmap
            self.__cbPanel.useNegativeCmap = useNegativeCmap
            self.__cbPanel.cmapResolution  = cmapResolution
            self.__cbPanel.invert          = invert
            self.__cbPanel.vrange          = dmin, dmax
            self.__cbPanel.label           = label

        # Using inside knowledge about the
        # ColourBarCanvas here - it will
        # refresh itself on any property
        # change.
        self.__cbPanel.propNotify('cmap')
