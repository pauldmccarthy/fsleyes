#!/usr/bin/env python
#
# colourbar.py - Provides the ColourBarPanel, a panel for displaying a colour
#                bar.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :class:`.FSLEyesPanel` which renders a colour bar depicting the colour
range of the currently selected overlay (if applicable).

"""

import logging
log = logging.getLogger(__name__)

import wx

import fsl.data.image                         as fslimage
import fsl.fsleyes.panel                      as fslpanel
import fsl.fsleyes.displaycontext             as fsldc
import fsl.fsleyes.displaycontext.volumeopts  as volumeopts
import fsl.fsleyes.gl.wxglcolourbarcanvas     as cbarcanvas


class ColourBarPanel(fslpanel.FSLEyesPanel):
    """A panel which shows a colour bar, depicting the data range of the
    currently selected overlay.
    """

    
    orientation = cbarcanvas.ColourBarCanvas.orientation
    """Draw the colour bar horizontally or vertically. """

    
    labelSide   = cbarcanvas.ColourBarCanvas.labelSide
    """Draw colour bar labels on the top/left/right/bottom."""
                  

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 orientation='horizontal'):

        fslpanel.FSLEyesPanel.__init__(self, parent, overlayList, displayCtx)

        self._cbPanel = cbarcanvas.ColourBarCanvas(self)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)
        self._sizer.Add(self._cbPanel, flag=wx.EXPAND, proportion=1)

        self.bindProps('orientation', self._cbPanel)
        self.bindProps('labelSide'  , self._cbPanel)

        self.SetBackgroundColour('black')

        self.addListener('orientation', self._name, self._layout)
        
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self._selectedOverlayChanged)
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self._selectedOverlayChanged)

        self._selectedOverlay = None
        
        self._layout()
        self._selectedOverlayChanged()


    def getCanvas(self):
        """Returns the :class:`.ColourBarCanvas` which displays the rendered
        colour bar.
        """
        return self._cbPanel


    def destroy(self):
        """Removes all registered listeners from the overlay list, display
        context, and individual overlays.
        """

        
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        overlay = self._selectedOverlay

        if overlay is not None:
            try:
                display = self._displayCtx.getDisplay(overlay)
                opts    = display.getDisplayOpts()

                if isinstance(opts, volumeopts.VolumeOpts):
                    display.removeListener('name',         self._name)
                    opts   .removeListener('cmap',         self._name)
                    opts   .removeListener('displayRange', self._name)
                    
            except fsldc.InvalidOverlayError:
                pass

        self._cbPanel        .destroy()
        fslpanel.FSLEyesPanel.destroy(self)
 
            
    def _layout(self, *a):
        """
        """

        # Fix the minor axis of the colour bar to 75 pixels
        if self.orientation == 'horizontal':
            self._cbPanel.SetSizeHints(-1, 75, -1, 75, -1, -1)
        else:
            self._cbPanel.SetSizeHints(75, -1, 75, -1, -1, -1)

        self.Layout()
        self._refreshColourBar()
                          

    def _selectedOverlayChanged(self, *a):
        """
        """

        overlay = self._selectedOverlay
        
        if overlay is not None:
            try:
                display = self._displayCtx.getDisplay(overlay)
                opts    = display.getDisplayOpts()

                opts   .removeListener('displayRange', self._name)
                opts   .removeListener('cmap',         self._name)
                display.removeListener('name',         self._name)

            # The previously selected overlay
            # has been removed from the list,
            # so its Display/Opts instances
            # have been thrown away
            except fsldc.InvalidOverlayError:
                pass
            
        self._selectedOverlay = None
            
        overlay = self._displayCtx.getSelectedOverlay()
 
        if overlay is None:
            self._refreshColourBar()
            return

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        # TODO support for other overlay types
        # TODO support for other types (where applicable)
        if not isinstance(overlay, fslimage.Image) or \
           not isinstance(opts,    volumeopts.VolumeOpts):
            self._refreshColourBar()
            return

        self._selectedOverlay = overlay

        # TODO register on overlayType property, in
        # case the overlay type changes to a type
        # that has a display range and colour map

        opts   .addListener('displayRange',
                            self._name,
                            self._displayRangeChanged)
        opts   .addListener('cmap',
                            self._name,
                            self._refreshColourBar)
        display.addListener('name',
                            self._name,
                            self._overlayNameChanged)

        self._overlayNameChanged()
        self._displayRangeChanged()
        self._refreshColourBar()


    def _overlayNameChanged(self, *a):
        """
        """

        if self._selectedOverlay is not None:
            display = self._displayCtx.getDisplay(self._selectedOverlay)
            label   = display.name
        else:
            label = ''
            
        self._cbPanel.label = label

        
    def _displayRangeChanged(self, *a):
        """
        """

        overlay = self._selectedOverlay

        if overlay is not None:
            
            opts       = self._displayCtx.getOpts(overlay)
            dmin, dmax = opts.displayRange.getRange(0)
        else:
            dmin, dmax = 0.0, 0.0

        self._cbPanel.vrange.x = (dmin, dmax)


    def _refreshColourBar(self, *a):
        """
        """

        overlay = self._selectedOverlay

        if overlay is not None:
            opts = self._displayCtx.getOpts(overlay)
            cmap = opts.cmap
        else:
            cmap = None

        self._cbPanel.cmap = cmap
