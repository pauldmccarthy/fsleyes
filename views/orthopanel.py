#!/usr/bin/env python
#
# orthopanel.py - A wx/OpenGL widget for displaying and interacting with a
# collection of 3D overlays. 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :mod:`wx`/:mod:`OpenGL` widget for displaying and interacting with a
collection of 3D overlays.

Displays three canvases, each of which shows the same overlay(s) on a
different orthogonal plane. The displayed location is driven by the
:attr:`.DisplayContext.location` property.
"""

import logging

import wx

import fsl.data.strings                           as strings
import fsl.data.constants                         as constants
import fsl.utils.layout                           as fsllayout
import fsl.fsleyes.gl                             as fslgl
import fsl.fsleyes.colourmaps                     as colourmaps
import fsl.fsleyes.gl.wxglslicecanvas             as slicecanvas
import fsl.fsleyes.controls.overlaydisplaytoolbar as overlaydisplaytoolbar
import fsl.fsleyes.controls.orthotoolbar          as orthotoolbar
import fsl.fsleyes.controls.orthoedittoolbar      as orthoedittoolbar
import fsl.fsleyes.displaycontext.orthoopts       as orthoopts
import                                               canvaspanel


log = logging.getLogger(__name__)


class OrthoPanel(canvaspanel.CanvasPanel):


    def __init__(self, parent, overlayList, displayCtx):
        """
        Creates three SliceCanvas objects, each displaying the images
        in the given image list along a different axis. 
        """


        sceneOpts = orthoopts.OrthoOpts()

        actionz = {
            'toggleOrthoToolBar' : lambda *a: self.togglePanel(
                orthotoolbar.OrthoToolBar, ortho=self),
            'toggleEditToolBar' : lambda *a: self.togglePanel(
                orthoedittoolbar.OrthoEditToolBar, ortho=self), 
        }

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         sceneOpts,
                                         actionz)

        canvasPanel = self.getCanvasPanel()

        # The canvases themselves - each one displays a
        # slice along each of the three world axes
        self._xcanvas = slicecanvas.WXGLSliceCanvas(canvasPanel,
                                                    overlayList,
                                                    displayCtx,
                                                    zax=0)
        self._ycanvas = slicecanvas.WXGLSliceCanvas(canvasPanel,
                                                    overlayList,
                                                    displayCtx,
                                                    zax=1)
        self._zcanvas = slicecanvas.WXGLSliceCanvas(canvasPanel,
                                                    overlayList,
                                                    displayCtx,
                                                    zax=2)

        # Labels to show anatomical orientation,
        # stored in a dict for each canvas
        self._xLabels = {}
        self._yLabels = {}
        self._zLabels = {}
        for side in ('left', 'right', 'top', 'bottom'):
            self._xLabels[side] = wx.StaticText(canvasPanel)
            self._yLabels[side] = wx.StaticText(canvasPanel)
            self._zLabels[side] = wx.StaticText(canvasPanel)

        self._xcanvas.bindProps('showCursor',   sceneOpts)
        self._ycanvas.bindProps('showCursor',   sceneOpts)
        self._zcanvas.bindProps('showCursor',   sceneOpts)

        self._xcanvas.bindProps('bgColour',     sceneOpts)
        self._ycanvas.bindProps('bgColour',     sceneOpts)
        self._zcanvas.bindProps('bgColour',     sceneOpts)

        self._xcanvas.bindProps('cursorColour', sceneOpts)
        self._ycanvas.bindProps('cursorColour', sceneOpts)
        self._zcanvas.bindProps('cursorColour', sceneOpts)

        # Callbacks for ortho panel layout options
        sceneOpts.addListener('layout',     self._name, self._refreshLayout)
        sceneOpts.addListener('showLabels', self._name, self._refreshLabels)
        sceneOpts.addListener('bgColour'  , self._name, self.__bgColourChanged)

        self.__bgColourChanged()

        # Individual zoom control for each canvas
        self._xcanvas.bindProps('zoom', sceneOpts, 'xzoom')
        self._ycanvas.bindProps('zoom', sceneOpts, 'yzoom')
        self._zcanvas.bindProps('zoom', sceneOpts, 'zzoom')

        self._xcanvas.bindProps('renderMode',      sceneOpts)
        self._ycanvas.bindProps('renderMode',      sceneOpts)
        self._zcanvas.bindProps('renderMode',      sceneOpts)

        self._xcanvas.bindProps('softwareMode',    sceneOpts)
        self._ycanvas.bindProps('softwareMode',    sceneOpts)
        self._zcanvas.bindProps('softwareMode',    sceneOpts)

        self._xcanvas.bindProps('resolutionLimit', sceneOpts)
        self._ycanvas.bindProps('resolutionLimit', sceneOpts)
        self._zcanvas.bindProps('resolutionLimit', sceneOpts) 

        # And a global zoom which controls all canvases at once

        minZoom = sceneOpts.getConstraint('xzoom', 'minval')
        maxZoom = sceneOpts.getConstraint('xzoom', 'maxval')

        sceneOpts.setConstraint('zoom', 'minval', minZoom)
        sceneOpts.setConstraint('zoom', 'maxval', maxZoom)

        sceneOpts.addListener('zoom', self._name, self.__onZoom)

        # Callbacks for overlay list/selected overlay changes
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self._overlayListChanged)
        self._displayCtx .addListener('bounds',
                                      self._name,
                                      self._refreshLayout) 
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self._overlayListChanged)

        # Callback for the display context location - when it
        # changes, update the displayed canvas locations
        self._displayCtx.addListener('location',
                                     self._name,
                                     self._locationChanged) 

        # Callbacks for toggling x/y/z canvas display
        sceneOpts.addListener('showXCanvas',
                              self._name,
                              lambda *a: self._toggleCanvas('x'),
                              weak=False)
        sceneOpts.addListener('showYCanvas',
                              self._name,
                              lambda *a: self._toggleCanvas('y'),
                              weak=False)
        sceneOpts.addListener('showZCanvas',
                              self._name,
                              lambda *a: self._toggleCanvas('z'),
                              weak=False)

        # Call the _resize method to refresh
        # the slice canvases when the canvas
        # panel is resized, so aspect ratio
        # is maintained
        canvasPanel.Bind(wx.EVT_SIZE, self._onResize)

        # Initialise the panel
        self._refreshLayout()
        self._overlayListChanged()
        self._locationChanged()
        self.initProfile()

        # The FSLEyesFrame AuiManager seems to
        # struggle if we add these toolbars
        # immediately, so we'll do it asynchronously 
        def addToolbars():
            self.togglePanel(overlaydisplaytoolbar.OverlayDisplayToolBar,
                             viewPanel=self)
            self.togglePanel(orthotoolbar.OrthoToolBar,
                             ortho=self) 
            self.togglePanel(orthoedittoolbar.OrthoEditToolBar,
                             ortho=self) 

        wx.CallAfter(addToolbars)


    def destroy(self):
        """Called when this panel is closed. 
        
        The display context and image list will probably live longer than
        this OrthoPanel. So when this panel is destroyed, all those
        registered listeners are removed.
        """

        self._displayCtx .removeListener('location',        self._name)
        self._displayCtx .removeListener('bounds',          self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        self._xcanvas.destroy()
        self._ycanvas.destroy()
        self._zcanvas.destroy()

        # The _overlayListChanged method adds
        # listeners to individual overlays,
        # so we have to remove them too
        for ovl in self._overlayList:
            opts = self._displayCtx.getOpts(ovl)
            opts.removeListener('bounds', self._name)

        canvaspanel.CanvasPanel.destroy(self)


    def __bgColourChanged(self, *a):
        
        bg = self.getSceneOptions().bgColour[:3]
        fg = colourmaps.complementaryColour(bg[:3])

        bg = [int(round(c * 255)) for c in bg] + [255]
        fg = [int(round(c * 255)) for c in fg] + [255]

        self.getCanvasPanel().SetBackgroundColour(bg)
        self.getCanvasPanel().SetForegroundColour(fg)

        self._xcanvas.SetBackgroundColour(bg)
        self._ycanvas.SetBackgroundColour(bg)
        self._zcanvas.SetBackgroundColour(bg)

        for side in ('left', 'right', 'top', 'bottom'):
            self._xLabels[side].SetBackgroundColour(bg)
            self._yLabels[side].SetBackgroundColour(bg)
            self._zLabels[side].SetBackgroundColour(bg)
            self._xLabels[side].SetForegroundColour(fg)
            self._yLabels[side].SetForegroundColour(fg)
            self._zLabels[side].SetForegroundColour(fg) 

        self.Refresh()
        
            
    def __onZoom(self, *a):
        """Called when the :attr:`.SceneOpts.zoom` property changes.
        Propagates the change to the :attr:`.OrthoOpts.xzoom`, ``yzoom``,
        and ``zzoom`` properties.
        """
        opts       = self.getSceneOptions()
        opts.xzoom = opts.zoom
        opts.yzoom = opts.zoom
        opts.zzoom = opts.zoom

            
    def getGLCanvases(self):
        """Returns all of the :class:`.SliceCanvas` instances contained
        within this ``OrthoPanel``.
        """
        return [self._xcanvas, self._ycanvas, self._zcanvas]
    

    def getXCanvas(self):
        """Returns a reference to the :class:`.SliceCanvas` instance
        displaying the X axis.
        """
        return self._xcanvas

    
    def getYCanvas(self):
        """Returns a reference to the :class:`.SliceCanvas` instance
        displaying the Y axis.
        """ 
        return self._ycanvas

    
    def getZCanvas(self):
        """Returns a reference to the :class:`.SliceCanvas` instance
        displaying the Z axis.
        """ 
        return self._zcanvas 
        

    def _toggleCanvas(self, canvas):
        """Called when any of  show*Canvas properties are changed.
        
        Shows/hides the specified canvas ('x', 'y', or 'z') - this callback
        is configured in __init__ above.
        """

        opts = self.getSceneOptions()

        if canvas == 'x':
            canvas = self._xcanvas
            show   = opts.showXCanvas
            labels = self._xLabels
        elif canvas == 'y':
            canvas = self._ycanvas
            show   = opts.showYCanvas
            labels = self._yLabels
        elif canvas == 'z':
            canvas = self._zcanvas
            show   = opts.showZCanvas
            labels = self._zLabels

        self._canvasSizer.Show(canvas, show)
        for label in labels.values():
            if (not show) or (show and opts.showLabels):
                self._canvasSizer.Show(label, show)

        if opts.layout == 'grid':
            self._refreshLayout()

        self.PostSizeEvent()


    def _overlayListChanged(self, *a):
        """Called when the overlay list or selected overlay is changed.

        Adds a listener to the currently selected overlay, to listen
        for changes on its transformation matrix.
        """
        
        for i, ovl in enumerate(self._overlayList):

            opts = self._displayCtx.getOpts(ovl)

            # Update anatomy labels when 
            # overlay bounds change
            if i == self._displayCtx.selectedOverlay:
                opts.addListener('bounds',
                                 self._name,
                                 self._refreshLabels,
                                 overwrite=True)
            else:
                opts.removeListener('bounds', self._name)
                
        # anatomical orientation may have changed with an image change
        self._refreshLabels()

            
    def _onResize(self, ev):
        """
        Called whenever the panel is resized. Makes sure that the canvases
        are laid out nicely.
        """
        ev.Skip()
        self._calcCanvasSizes()


    def _refreshLabels(self, *a):
        """Shows/hides labels depicting anatomical orientation on each canvas.
        """

        allLabels = self._xLabels.values() + \
                    self._yLabels.values() + \
                    self._zLabels.values()

        # Are we showing or hiding the labels?
        if   len(self._overlayList) == 0:       show = False

        overlay = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        # Labels are only supported if we
        # have a volumetric reference image 
        if   overlay is None:                   show = False
        elif self.getSceneOptions().showLabels: show = True
        else:                                   show = False

        for lbl in allLabels:
            self._canvasSizer.Show(lbl, show)

        # If we're hiding the labels, do no more
        if not show:
            self.PostSizeEvent()
            return

        # Default colour is white - if the orientation labels
        # cannot be determined, the foreground colour will be
        # changed to red
        colour  = 'white'

        opts = self._displayCtx.getOpts(overlay)

        # The image is being displayed as it is stored on
        # disk - the image.getOrientation method calculates
        # and returns labels for each voxelwise axis.
        if opts.transform in ('pixdim', 'id'):
            xorient = overlay.getVoxelOrientation(0)
            yorient = overlay.getVoxelOrientation(1)
            zorient = overlay.getVoxelOrientation(2)

        # The overlay is being displayed in 'real world' space -
        # the definition of this space may be present in the
        # overlay meta data
        else:
            xorient = overlay.getWorldOrientation(0)
            yorient = overlay.getWorldOrientation(1)
            zorient = overlay.getWorldOrientation(2)
                
        if constants.ORIENT_UNKNOWN in (xorient, yorient, zorient):
            colour = 'red'

        xlo = strings.anatomy['Image', 'lowshort',  xorient]
        ylo = strings.anatomy['Image', 'lowshort',  yorient]
        zlo = strings.anatomy['Image', 'lowshort',  zorient]
        xhi = strings.anatomy['Image', 'highshort', xorient]
        yhi = strings.anatomy['Image', 'highshort', yorient]
        zhi = strings.anatomy['Image', 'highshort', zorient]

        for lbl in allLabels:
            lbl.SetForegroundColour(colour)

        self._xLabels['left']  .SetLabel(ylo)
        self._xLabels['right'] .SetLabel(yhi)
        self._xLabels['top']   .SetLabel(zlo)
        self._xLabels['bottom'].SetLabel(zhi)
        self._yLabels['left']  .SetLabel(xlo)
        self._yLabels['right'] .SetLabel(xhi)
        self._yLabels['top']   .SetLabel(zlo)
        self._yLabels['bottom'].SetLabel(zhi)
        self._zLabels['left']  .SetLabel(xlo)
        self._zLabels['right'] .SetLabel(xhi)
        self._zLabels['top']   .SetLabel(ylo)
        self._zLabels['bottom'].SetLabel(yhi)

        self.PostSizeEvent()


    def _calcCanvasSizes(self, *a):
        """Fixes the size for each displayed canvas (by setting their minimum
        and maximum sizes), so that they are scaled proportionally to each
        other.
        """
        
        opts   = self.getSceneOptions()
        layout = opts.layout

        width, height = self.getCanvasPanel().GetClientSize().Get()

        show     = [opts.showXCanvas, opts.showYCanvas, opts.showZCanvas]
        canvases = [self._xcanvas,    self._ycanvas,    self._zcanvas]
        labels   = [self._xLabels,    self._yLabels,    self._zLabels]

        if width == 0 or height == 0:   return
        if len(self._overlayList) == 0: return
        if not any(show):               return

        canvases, labels, _ = zip(*filter(lambda (c, l, s): s,
                                          zip(canvases, labels, show)))

        canvases = list(canvases)
        labels   = list(labels)

        # Grid layout with 2 or less canvases displayed
        # is identical to horizontal layout
        if layout == 'grid' and len(canvases) <= 2:
            layout = 'horizontal'

        # Calculate the width/height (in pixels) which
        # is available to lay out all of the canvases
        # (taking into account anatomical orientation
        # labels).
        if layout == 'horizontal':
            maxh = 0
            sumw = 0
            for l in labels:

                if opts.showLabels:
                    lw, lh = l['left']  .GetClientSize().Get()
                    rw, rh = l['right'] .GetClientSize().Get()
                    tw, th = l['top']   .GetClientSize().Get()
                    bw, bh = l['bottom'].GetClientSize().Get()
                else:
                    lw = rw = th = bh = 0

                sumw = sumw + lw + rw
                if th > maxh: maxh = th
                if bh > maxh: maxh = bh
            width  = width  -     sumw
            height = height - 2 * maxh
            
        elif layout == 'vertical':
            maxw = 0
            sumh = 0
            for l in labels:
                if opts.showLabels:
                    lw, lh = l['left']  .GetClientSize().Get()
                    rw, rh = l['right'] .GetClientSize().Get()
                    tw, th = l['top']   .GetClientSize().Get()
                    bw, bh = l['bottom'].GetClientSize().Get()
                else:
                    lw = rw = th = bh = 0
                    
                sumh = sumh + th + bh
                if lw > maxw: maxw = lw
                if rw > maxw: maxw = rw
                
            width  = width  - 2 * maxw
            height = height -     sumh
            
        else:
            canvases = [self._ycanvas, self._xcanvas, self._zcanvas]

            if opts.showLabels:
                xlw = self._xLabels['left']  .GetClientSize().GetWidth()
                xrw = self._xLabels['right'] .GetClientSize().GetWidth()
                ylw = self._yLabels['left']  .GetClientSize().GetWidth()
                yrw = self._yLabels['right'] .GetClientSize().GetWidth()
                zlw = self._zLabels['left']  .GetClientSize().GetWidth()
                zrw = self._zLabels['right'] .GetClientSize().GetWidth()             
                xth = self._xLabels['top']   .GetClientSize().GetHeight()
                xbh = self._xLabels['bottom'].GetClientSize().GetHeight()
                yth = self._yLabels['top']   .GetClientSize().GetHeight()
                ybh = self._yLabels['bottom'].GetClientSize().GetHeight()
                zth = self._zLabels['top']   .GetClientSize().GetHeight()
                zbh = self._zLabels['bottom'].GetClientSize().GetHeight()
            else:
                xlw = xrw = xth = xbh = 0
                ylw = yrw = yth = ybh = 0
                zlw = zrw = zth = zbh = 0

            width  = width  - max(xlw, zlw) - max(xrw, zrw) - ylw - yrw
            height = height - max(xth, yth) - max(xbh, ybh) - zth - zbh

        # Distribute the available width/height
        # to each of the displayed canvases -
        # fsl.utils.layout (a.k.a. fsllayout)
        # provides functions to do this for us
        canvasaxes = [(c.xax, c.yax) for c in canvases]
        axisLens   = [self._displayCtx.bounds.xlen,
                      self._displayCtx.bounds.ylen,
                      self._displayCtx.bounds.zlen]
        
        sizes = fsllayout.calcSizes(layout,
                                    canvasaxes,
                                    axisLens,
                                    width,
                                    height)

        for canvas, size in zip(canvases, sizes):
            canvas.SetMinSize(size)
            canvas.SetMaxSize(size)

        
    def _refreshLayout(self, *a):
        """Called when the layout property changes, or the canvas layout needs
        to be refreshed. Updates the orthopanel layout accordingly.
        """

        opts   = self.getSceneOptions()
        layout = opts.layout

        # For the grid layout if only one or two
        # canvases are being displayed, the layout
        # is equivalent to a horizontal layout
        nCanvases = 3
        nDisplayedCanvases = sum([opts.showXCanvas,
                                  opts.showYCanvas,
                                  opts.showZCanvas])
         
        if layout == 'grid' and nDisplayedCanvases <= 2:
            layout = 'horizontal'

        # Regardless of the layout, we use a
        # FlexGridSizer with varying numbers
        # of rows/columns, depending upon the
        # layout strategy
        if   layout == 'horizontal':
            nrows = 3
            ncols = nCanvases * 3
        elif layout == 'vertical':
            nrows = nCanvases * 3
            ncols = 3
        elif layout == 'grid': 
            nrows = nCanvases * 2
            ncols = nCanvases * 2
        # if layout is something other than the above three,
        # then something's gone wrong and I'm going to crash

        self._canvasSizer = wx.FlexGridSizer(nrows, ncols)

        # The rows/columns that contain
        # canvases must also be growable
        if layout == 'horizontal':
            self._canvasSizer.AddGrowableRow(1)
            for i in range(nCanvases):
                self._canvasSizer.AddGrowableCol(i * 3 + 1)
                
        elif layout == 'vertical':
            self._canvasSizer.AddGrowableCol(1)
            for i in range(nCanvases):
                self._canvasSizer.AddGrowableRow(i * 3 + 1)
                
        elif layout == 'grid':
            self._canvasSizer.AddGrowableRow(1)
            self._canvasSizer.AddGrowableRow(4)
            self._canvasSizer.AddGrowableCol(1)
            self._canvasSizer.AddGrowableCol(4) 

        # Make a list of widgets - the canvases,
        # anatomical labels (if displayed), and
        # spacers for the empty cells
        space = (1, 1)
        xlbls = self._xLabels
        ylbls = self._yLabels
        zlbls = self._zLabels
        
        if layout == 'horizontal':
            widgets = [space,         xlbls['top'],    space,
                       space,         ylbls['top'],    space,
                       space,         zlbls['top'],    space,
                       xlbls['left'], self._xcanvas,   xlbls['right'],
                       ylbls['left'], self._ycanvas,   ylbls['right'],
                       zlbls['left'], self._zcanvas,   zlbls['right'],
                       space,         xlbls['bottom'], space,
                       space,         ylbls['bottom'], space,
                       space,         zlbls['bottom'], space] 
                
        elif layout == 'vertical':
            widgets = [space,         xlbls['top'],    space,
                       xlbls['left'], self._xcanvas,   xlbls['right'],
                       space,         xlbls['bottom'], space,
                       space,         ylbls['top'],    space,
                       ylbls['left'], self._ycanvas,   ylbls['right'],
                       space,         ylbls['bottom'], space,
                       space,         zlbls['top'],    space,
                       zlbls['left'], self._zcanvas,   zlbls['right'],
                       space,         zlbls['bottom'], space]

        # The canvases are laid out in a different order
        # for orthographic, or 'grid' layout.  Assuming
        # that world axis X is left<->right, Y is
        # posterior<->anterior, and Z is inferior<->superior,
        # in order to achieve first angle orthographic
        # layout, we're laying out the canvases in the
        # following manner (the letter denotes the depth
        # axis for the respective canvas):
        #
        #    Y  X
        #    Z  - 
        elif layout == 'grid':
            widgets = [space,         ylbls['top'],    space,
                       space,         xlbls['top'],    space,
                       ylbls['left'], self._ycanvas,   ylbls['right'],
                       xlbls['left'], self._xcanvas,   xlbls['right'],
                       space,         ylbls['bottom'], space,
                       space,         xlbls['bottom'], space,
                       space,         zlbls['top'],    space,
                       space,         space,           space,
                       zlbls['left'], self._zcanvas,   zlbls['right'],
                       space,         space,           space,
                       space,         zlbls['bottom'], space,
                       space,         space,           space]

        # Add all those widgets to the grid sizer
        flag = wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL
        
        for w in widgets:
            self._canvasSizer.Add(w, flag=flag)
                                          
        self.getCanvasPanel().SetSizer(self._canvasSizer)

        # Calculate/ adjust the appropriate sizes
        # for each canvas, such that they are scaled
        # appropriately relative to each other, and
        # the displayed world space aspect ratio is
        # maintained
        self._calcCanvasSizes()

        self.Layout()
        self.getCanvasPanel().Layout()
        self.Refresh()


    def _locationChanged(self, *a):
        """
        Sets the currently displayed x/y/z position (in display
        coordinates).
        """

        xpos, ypos, zpos = self._displayCtx.location.xyz

        self._xcanvas.pos.xyz = [ypos, zpos, xpos]
        self._ycanvas.pos.xyz = [xpos, zpos, ypos]
        self._zcanvas.pos.xyz = [xpos, ypos, zpos]


class OrthoFrame(wx.Frame):
    """
    Convenience class for displaying an OrthoPanel in a standalone window.
    """

    def __init__(self, parent, overlayList, displayCtx, title=None):
        
        wx.Frame.__init__(self, parent, title=title)

        ctx, dummyCanvas = fslgl.getWXGLContext() 
        fslgl.bootstrap()
        
        self.panel = OrthoPanel(self, overlayList, displayCtx)
        self.Layout()

        if dummyCanvas is not None:
            dummyCanvas.Destroy()


class OrthoDialog(wx.Dialog):
    """
    Convenience class for displaying an OrthoPanel in a (possibly modal)
    dialog window.
    """

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 title=None,
                 style=None):

        if style is None: style =  wx.DEFAULT_DIALOG_STYLE
        else:             style |= wx.DEFAULT_DIALOG_STYLE

        wx.Dialog.__init__(self, parent, title=title, style=style)

        ctx, dummyCanvas = fslgl.getWXGLContext()
        fslgl.bootstrap()
        
        self.panel = OrthoPanel(self, overlayList, displayCtx)
        self.Layout()

        if dummyCanvas is not None:
            dummyCanvas.Destroy()
