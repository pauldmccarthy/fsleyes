#!/usr/bin/env python
#
# canvaspanel.py - Base class for all panels that display overlay data.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasPanel` class, which is the base
class for all panels which display image data (e.g. the :class:`.OrthoPanel`
and the :class:`.LightBoxPanel`).
"""

import os
import os.path as op
import logging
import collections

import wx

import numpy            as np
import matplotlib.image as mplimg

import props

import fsl.fsleyes.fsleyes_parseargs as fsleyes_parseargs
import fsl.utils.dialog              as fsldlg
import fsl.utils.settings            as fslsettings
import fsl.data.image                as fslimage
import fsl.data.strings              as strings
import fsl.fsleyes.displaycontext    as displayctx
import fsl.fsleyes.controls          as fslcontrols
import                                  colourbarpanel
import                                  viewpanel


log = logging.getLogger(__name__)



class CanvasPanel(viewpanel.ViewPanel):
    """
    """

    syncLocation       = props.Boolean(default=True)
    syncOverlayOrder   = props.Boolean(default=True)
    syncOverlayDisplay = props.Boolean(default=True)
    movieMode          = props.Boolean(default=False)
    movieRate          = props.Int(minval=100,
                                   maxval=1000,
                                   default=250,
                                   clamped=True)
    

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 sceneOpts,
                 extraActions=None):

        if extraActions is None:
            extraActions = {}

        actionz = [
            ('screenshot',              self.screenshot),
            ('showCommandLineArgs',     self.showCommandLineArgs),
            ('toggleOverlayList',       lambda *a: self.togglePanel(
                fslcontrols.OverlayListPanel,
                location=wx.BOTTOM)),
            ('toggleOverlayInfo',       lambda *a: self.togglePanel(
                fslcontrols.OverlayInfoPanel,
                location=wx.RIGHT)), 
            ('toggleAtlasPanel',        lambda *a: self.togglePanel(
                fslcontrols.AtlasPanel,
                location=wx.BOTTOM)),
            ('toggleDisplayProperties', lambda *a: self.togglePanel(
                fslcontrols.OverlayDisplayToolBar,
                viewPanel=self)),
            ('toggleLocationPanel',     lambda *a: self.togglePanel(
                fslcontrols.LocationPanel,
                location=wx.BOTTOM)),
            ('toggleClusterPanel',      lambda *a: self.togglePanel(
                fslcontrols.ClusterPanel,
                location=wx.TOP)), 
            ('toggleLookupTablePanel',  lambda *a: self.togglePanel(
                fslcontrols.LookupTablePanel,
                location=wx.TOP))]

        actionz += extraActions.items()

        actionz += [
            ('toggleShell', lambda *a: self.togglePanel(
                fslcontrols.ShellPanel,
                self.getSceneOptions(),
                location=wx.BOTTOM))]
        
        actionz = collections.OrderedDict(actionz)
        
        viewpanel.ViewPanel.__init__(
            self, parent, overlayList, displayCtx, actionz)

        self.__opts = sceneOpts
        
        # Bind the sync* properties of this
        # CanvasPanel to the corresponding
        # properties on the DisplayContext
        # instance. 
        if displayCtx.getParent() is not None:
            self.bindProps('syncLocation',
                           displayCtx,
                           displayCtx.getSyncPropertyName('location'))
            self.bindProps('syncOverlayOrder',
                           displayCtx,
                           displayCtx.getSyncPropertyName('overlayOrder'))
            self.bindProps('syncOverlayDisplay', displayCtx) 
            
        # If the displayCtx instance does not
        # have a parent, this means that it is
        # a top level instance
        else:
            self.disableProperty('syncLocation')
            self.disableProperty('syncOverlayOrder')

        self.__canvasContainer = wx.Panel(self)
        self.__canvasPanel     = wx.Panel(self.__canvasContainer)

        self.setCentrePanel(self.__canvasContainer)

        # Stores a reference to a wx.Timer
        # when movie mode is enabled
        self.__movieTimer    = None

        self.addListener('movieMode',
                         self._name,
                         self.__movieModeChanged)
        self.addListener('movieRate',
                         self._name,
                         self.__movieRateChanged)

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self.__canvasSizer   = None
        self.__colourBar     = None

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.__opts.addListener('colourBarLocation', lName, self.__layout)
        self.__opts.addListener('showColourBar',     lName, self.__layout)
        
        self.__layout()


    def destroy(self):
        """Makes sure that any remaining control panels are destroyed
        cleanly.
        """

        if self.__colourBar is not None:
            self.__colourBar.destroy()
            
        viewpanel.ViewPanel.destroy(self)

    
    def screenshot(self, *a):
        _screenshot(self._overlayList, self._displayCtx, self)


    def showCommandLineArgs(self, *a):
        _showCommandLineArgs(self._overlayList, self._displayCtx, self)


    def getSceneOptions(self):
        return self.__opts
                
        
    def getCanvasPanel(self):
        """Returns the ``wx.Panel`` which is the parent of all
        :class:`.SliceCanvas` instances displayed in this ``CanvasPanel``.
        """
        return self.__canvasPanel


    def getCanvasContainer(self):
        """Returns the ``wx.Panel`` which is the parent of the canvas
        panel (see :meth:`getCanvasPanel`), and of the :class:`.ColourBarPanel`
        if one is being displayed.
        """
        return self.__canvasContainer


    def getGLCanvases(self):
        """This must be implemented by subclasses, and must return a list
        containing all :class:`.SliceCanvas` instances which are being
        displayed.
        """
        raise NotImplementedError(
            'getGLCanvases has not been implemented '
            'by {}'.format(type(self).__name__))


    def getColourBarCanvas(self):
        """If a colour bar is being displayed, this method returns
        the :class:`.ColourBarCanvas` instance which renders the colour bar.
        
        Otherwise, ``None`` is returned.
        """
        if self.__colourBar is not None:
            return self.__colourBar.getCanvas()
        return None


    def __layout(self, *a):

        if not self.__opts.showColourBar:

            if self.__colourBar is not None:
                self.__opts.unbindProps('colourBarLabelSide',
                                        self.__colourBar,
                                        'labelSide')
                self.__colourBar.destroy()
                self.__colourBar.Destroy()
                self.__colourBar = None
                
            self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.__canvasSizer.Add(self.__canvasPanel,
                                   flag=wx.EXPAND,
                                   proportion=1)

            self.__canvasContainer.SetSizer(self.__canvasSizer)
            self.PostSizeEvent()
            return

        if self.__colourBar is None:
            self.__colourBar = colourbarpanel.ColourBarPanel(
                self.__canvasContainer, self._overlayList, self._displayCtx)

        self.__opts.bindProps('colourBarLabelSide',
                              self.__colourBar,
                              'labelSide') 
            
        if   self.__opts.colourBarLocation in ('top', 'bottom'):
            self.__colourBar.orientation = 'horizontal'
        elif self.__opts.colourBarLocation in ('left', 'right'):
            self.__colourBar.orientation = 'vertical'
        
        if self.__opts.colourBarLocation in ('top', 'bottom'):
            self.__canvasSizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__canvasContainer.SetSizer(self.__canvasSizer)

        if self.__opts.colourBarLocation in ('top', 'left'):
            self.__canvasSizer.Add(self.__colourBar,   flag=wx.EXPAND)
            self.__canvasSizer.Add(self.__canvasPanel, flag=wx.EXPAND,
                                   proportion=1)
        else:
            self.__canvasSizer.Add(self.__canvasPanel, flag=wx.EXPAND,
                                   proportion=1)
            self.__canvasSizer.Add(self.__colourBar,   flag=wx.EXPAND)

        # Force the canvas panel to resize itself
        self.PostSizeEvent()


    def __movieModeChanged(self, *a):

        if self.__movieTimer is not None:
            self.__movieTimer.Stop()
            self.__movieTimer = None

        if not self.movieMode:
            return
        
        self.__movieTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.__movieUpdate)
        self.__movieTimer.Start(self.movieRate)
        

    def __movieRateChanged(self, *a):
        if not self.movieMode:
            return

        self.__movieModeChanged()

        
    def __movieUpdate(self, ev):

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        if not isinstance(overlay, fslimage.Image):
            return

        if not overlay.is4DImage():
            return

        opts = self._displayCtx.getOpts(overlay)

        if not isinstance(opts, displayctx.VolumeOpts):
            return

        limit = overlay.shape[3]

        if opts.volume == limit - 1: opts.volume  = 0
        else:                        opts.volume += 1



def _genCommandLineArgs(overlayList, displayCtx, canvas):

    argv = []

    # Add scene options
    sceneOpts = canvas.getSceneOptions()
    argv += fsleyes_parseargs.generateSceneArgs(
        overlayList,
        displayCtx,
        sceneOpts,
        exclude=['performance'])

    # Add ortho specific options, if it's 
    # an orthopanel we're dealing with
    if isinstance(sceneOpts, displayctx.OrthoOpts):

        xcanvas = canvas.getXCanvas()
        ycanvas = canvas.getYCanvas()
        zcanvas = canvas.getZCanvas()
        
        argv += ['--{}'.format(fsleyes_parseargs.ARGUMENTS[sceneOpts,
                                                           'xcentre'][1])]
        argv += ['{}'.format(c) for c in xcanvas.pos.xy]
        argv += ['--{}'.format(fsleyes_parseargs.ARGUMENTS[sceneOpts,
                                                           'ycentre'][1])]
        argv += ['{}'.format(c) for c in ycanvas.pos.xy]
        argv += ['--{}'.format(fsleyes_parseargs.ARGUMENTS[sceneOpts,
                                                           'zcentre'][1])]
        argv += ['{}'.format(c) for c in zcanvas.pos.xy]

    # Add display options for each overlay
    for overlay in overlayList:

        fname   = overlay.dataSource
        ovlArgv = fsleyes_parseargs.generateOverlayArgs(overlay, displayCtx)
        argv   += [fname] + ovlArgv

    return argv


def _showCommandLineArgs(overlayList, displayCtx, canvas):

    args = _genCommandLineArgs(overlayList, displayCtx, canvas)
    dlg  = fsldlg.TextEditDialog(
        canvas,
        title=strings.messages[  canvas, 'showCommandLineArgs', 'title'],
        message=strings.messages[canvas, 'showCommandLineArgs', 'message'],
        text=' '.join(args),
        icon=wx.ICON_INFORMATION,
        style=(fsldlg.TED_OK        |
               fsldlg.TED_READONLY  |
               fsldlg.TED_MULTILINE |
               fsldlg.TED_COPY))

    dlg.CentreOnParent()

    dlg.ShowModal()


def _screenshot(overlayList, displayCtx, canvasPanel):

    def relativePosition(child, ancestor):
        """Calculates the position of the given ``child``, relative
        to its ``ancestor``. We use this to locate all GL canvases
        relative to the canvas panel container, as they are not
        necessarily direct children of the container.
        """

        if child.GetParent() is ancestor:
            return child.GetPosition().Get()

        xpos, ypos = child.GetPosition().Get()
        xoff, yoff = relativePosition(child.GetParent(), ancestor)

        return xpos + xoff, ypos + yoff
    
    # Ask the user where they want 
    # the screenshot to be saved

    fromDir = fslsettings.read('canvasPanelScreenshotLastDir',
                               default=os.getcwd())
    
    dlg = wx.FileDialog(
        canvasPanel,
        message=strings.messages['CanvasPanel.screenshot'],
        defaultDir=fromDir,
        style=wx.FD_SAVE)

    if dlg.ShowModal() != wx.ID_OK:
        return

    filename = dlg.GetPath()

    # Make the dialog go away before
    # the screenshot gets taken
    dlg.Close()
    dlg.Destroy()
    wx.Yield()


    def doScreenshot():

        # The typical way to get a screen grab of a wx
        # Window is to use a wx.WindowDC, and a wx.MemoryDC,
        # and to 'blit' a region from the window DC into
        # the memory DC.
        #
        # This is precisely what we're doing here, but
        # the process is complicated by the fact that,
        # under OSX, the contents of wx.glcanvas.GLCanvas
        # instances are not captured by WindowDCs.
        #
        # So I'm grabbing a screenshot of the canvas
        # panel in the standard wxWidgets way, and then
        # manually patching in bitmaps of each GLCanvas
        # that is displayed in the canvas panel.

        # Get all the wx GLCanvas instances
        # which are displayed in the panel,
        # including the colour bar canvas
        glCanvases = canvasPanel.getGLCanvases()
        glCanvases.append(canvasPanel.getColourBarCanvas())

        # The canvas panel container is the
        # direct parent of the colour bar
        # canvas, and an ancestor of the
        # other GL canvases
        parent        = canvasPanel.getCanvasContainer()
        width, height = parent.GetClientSize().Get()
        windowDC      = wx.WindowDC(parent)
        memoryDC      = wx.MemoryDC()
        bmp           = wx.EmptyBitmap(width, height)

        wx.Yield()

        # Copy the contents of the canvas container
        # to the bitmap
        memoryDC.SelectObject(bmp)
        memoryDC.Blit(
            0,
            0,
            width,
            height,
            windowDC,
            0,
            0)
        memoryDC.SelectObject(wx.NullBitmap)

        # Make a H*W*4 bitmap array 
        data = np.zeros((height, width, 4), dtype=np.uint8)
        rgb  = bmp.ConvertToImage().GetData()
        rgb  = np.fromstring(rgb, dtype=np.uint8)

        data[:, :, :3] = rgb.reshape(height, width, 3)

        # Patch in bitmaps for every GL canvas
        for glCanvas in glCanvases:

            # If the colour bar is not displayed,
            # the colour bar canvas will be None
            if glCanvas is None:
                continue

            pos   = relativePosition(glCanvas, parent)
            size  = glCanvas.GetClientSize().Get()

            xstart = pos[0]
            ystart = pos[1]
            xend   = xstart + size[0]
            yend   = ystart + size[1]

            bmp = glCanvas.getBitmap()

            # There seems to ber a size/position miscalculation
            # somewhere, such that if the last canvas is on the
            # hard edge of the parent, the canvas size spills
            # over the parent size byt a couple of pixels.. If
            # this occurs, I truncate the canvas bitmap accordingly.
            if xend > width or yend > height:
                xend = width
                yend = height
                w    = xend - xstart
                h    = yend - ystart
                bmp  = bmp[:h, :w, :]
            
            data[ystart:yend, xstart:xend] = bmp

        data[:, :,  3] = 255

        mplimg.imsave(filename, data)

    fsldlg.ProcessingDialog(
        canvasPanel.GetTopLevelParent(),
        strings.messages['CanvasPanel.screenshot.pleaseWait'],
        doScreenshot).Run(mainThread=True)

    fslsettings.write('canvasPanelScreenshotLastDir', op.dirname(filename))
