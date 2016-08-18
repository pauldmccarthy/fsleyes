#!/usr/bin/env python
#
# orthopanel.py - The OrthoPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoPanel` class, which displays a 2D
view of 3D overlays.

A couple of other classes are provided for convenience:

.. autosummary::
   :nosignatures:

   OrthoFrame
   OrthoDialog
"""


import logging
import itertools as it

import wx

import pwidgets.textpanel                     as textpanel

import fsl.data.constants                     as constants
import fsl.utils.layout                       as fsllayout
import fsleyes.strings                        as strings
import fsleyes.gl                             as fslgl
import fsleyes.actions                        as actions
import fsleyes.colourmaps                     as colourmaps
import fsleyes.gl.wxglslicecanvas             as slicecanvas
import fsleyes.controls.orthotoolbar          as orthotoolbar
import fsleyes.controls.orthoedittoolbar      as orthoedittoolbar
import fsleyes.displaycontext.orthoopts       as orthoopts
from . import                                    canvaspanel


log = logging.getLogger(__name__)


class OrthoPanel(canvaspanel.CanvasPanel):
    """The ``OrthoPanel`` class is a *FSLeyes view* which displays a 2D view
    of 3D overlays.  The ``OrthoPanel`` is the primary point of user
    interaction in *FSLeyes*.


    **Overview**

    
    An ``OrthoPanel`` contains three :class:`.SliceCanvas` panels, each of
    which provide a 2D view of the overlays in the :class:`.OverlayList` along
    one axis. These ``SliceCanvas`` instances can be accessed through the
    :meth:`getXCanvas`, :meth:`getYCanvas`, :meth:`getZCanvas`, and
    :meth:`getGLCanvases` methods.


    An ``OrthoPanel`` looks something like this:


    .. image:: images/orthopanel.png
       :scale: 50%
       :align: center


    **Anatomical labels**
    

    In addition to the three ``SliceCanvas`` panels, the ``OrthoPanel`` is
    capable of displaying labels around each panel, showing the user the
    anatomical orientation of the display on each panel. These labels are only
    shown if the currently selected overlay (as dicated by the
    :attr:`.DisplayContext.selectedOverlay` property) is a :class:`.Image`
    instance, **or** the :meth:`.DisplayOpts.getReferenceImage` method for the
    currently selected overlay returns an :class:`.Image` instance.


    **Display**


    The display of an ``OrthoPanel`` can be configured through all of the
    settings provided by the :class:`.OrthoOpts` class. The ``OrthoOpts``
    instance for a given ``OrthoPanel`` can be accessed via the
    :meth:`.CanvasPanel.getSceneOptions` method.


    **Interaction**


    Two interaction profiles are defined for use with the ``OrthoPanel`` (see
    the :class:`.ViewPanel` for an overview of *profiles*):

    ======== =========================================================
    ``view`` Viewing/navigation, using the :class:`.OrthoViewProfile`.
    
    ``edit`` Simple editing of :class:`.Image` overlays, using the
             :class:`.OrthoEditProfile` (see also the
             :mod:`~fsleyes.editor` package).
    ======== =========================================================
    

    **Actions and control panels**


    The ``OrthoPanel`` adds a few extra actions to those provided by the 
    :class:`.CanvasPanel` class:

    .. autosummary::
       :nosignatures:

       toggleEditMode
       toggleOrthoToolBar
    """


    def __init__(self, parent, overlayList, displayCtx):
        """Create an ``OrthoPanel``.

        :arg parent:      The :mod:`wx` parent.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        """

        sceneOpts = orthoopts.OrthoOpts()

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         sceneOpts)

        contentPanel = self.getContentPanel()

        # The canvases themselves - each one displays a
        # slice along each of the three world axes
        self.__xcanvas = slicecanvas.WXGLSliceCanvas(contentPanel,
                                                     overlayList,
                                                     displayCtx,
                                                     zax=0)
        self.__ycanvas = slicecanvas.WXGLSliceCanvas(contentPanel,
                                                     overlayList,
                                                     displayCtx,
                                                     zax=1)
        self.__zcanvas = slicecanvas.WXGLSliceCanvas(contentPanel,
                                                     overlayList,
                                                     displayCtx,
                                                     zax=2)

        # Labels to show anatomical orientation,
        # stored in a dict for each canvas
        self.__xLabels = {}
        self.__yLabels = {}
        self.__zLabels = {}
        
        for side in ('left', 'right', 'top', 'bottom'):
            self.__xLabels[side] = textpanel.TextPanel(contentPanel)
            self.__yLabels[side] = textpanel.TextPanel(contentPanel)
            self.__zLabels[side] = textpanel.TextPanel(contentPanel)

        self.__xcanvas.bindProps('showCursor',   sceneOpts)
        self.__ycanvas.bindProps('showCursor',   sceneOpts)
        self.__zcanvas.bindProps('showCursor',   sceneOpts)

        self.__xcanvas.bindProps('cursorGap',   sceneOpts)
        self.__ycanvas.bindProps('cursorGap',   sceneOpts)
        self.__zcanvas.bindProps('cursorGap',   sceneOpts) 

        self.__xcanvas.bindProps('bgColour',     sceneOpts)
        self.__ycanvas.bindProps('bgColour',     sceneOpts)
        self.__zcanvas.bindProps('bgColour',     sceneOpts)

        self.__xcanvas.bindProps('cursorColour', sceneOpts)
        self.__ycanvas.bindProps('cursorColour', sceneOpts)
        self.__zcanvas.bindProps('cursorColour', sceneOpts)

        # L/r flip
        self.__ycanvas.bindProps('invertX', displayCtx, 'lrFlip')
        self.__zcanvas.bindProps('invertX', displayCtx, 'lrFlip')

        # Callbacks for ortho panel layout options
        sceneOpts.addListener('layout',     self._name, self.__refreshLayout)
        sceneOpts.addListener('showLabels', self._name, self.__refreshLabels)
        sceneOpts.addListener('bgColour'  , self._name, self.__bgColourChanged)

        # Individual zoom control for each canvas
        self.__xcanvas.bindProps('zoom', sceneOpts, 'xzoom')
        self.__ycanvas.bindProps('zoom', sceneOpts, 'yzoom')
        self.__zcanvas.bindProps('zoom', sceneOpts, 'zzoom')

        self.__xcanvas.bindProps('renderMode',      sceneOpts)
        self.__ycanvas.bindProps('renderMode',      sceneOpts)
        self.__zcanvas.bindProps('renderMode',      sceneOpts)

        self.__xcanvas.bindProps('resolutionLimit', sceneOpts)
        self.__ycanvas.bindProps('resolutionLimit', sceneOpts)
        self.__zcanvas.bindProps('resolutionLimit', sceneOpts) 

        # Callbacks for overlay list/selected overlay changes
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self.__overlayListChanged)
        self._displayCtx .addListener('bounds',
                                      self._name,
                                      self.__refreshLayout)
        self._displayCtx .addListener('displaySpace',
                                      self._name,
                                      self.__refreshLabels)
        self._displayCtx .addListener('lrFlip',
                                      self._name,
                                      self.__refreshLabels) 
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self.__overlayListChanged)

        # Callback for the display context location - when it
        # changes, update the displayed canvas locations
        self._displayCtx.addListener('location',
                                     self._name,
                                     self.__locationChanged)

        # Callbacks for toggling x/y/z canvas display
        sceneOpts.addListener('showXCanvas', self._name, self.__toggleCanvas)
        sceneOpts.addListener('showYCanvas', self._name, self.__toggleCanvas)
        sceneOpts.addListener('showZCanvas', self._name, self.__toggleCanvas)

        self.toggleEditMode.addListener('toggled',
                                        self._name,
                                        self.__onToggleEditMode)

        # Call the __onResize method to refresh
        # the slice canvases when the canvas
        # panel is resized, so aspect ratio
        # is maintained
        contentPanel.Bind(wx.EVT_SIZE, self.__onResize)

        # Initialise the panel
        self.__refreshLayout()
        self.__bgColourChanged()
        self.__overlayListChanged()
        self.__locationChanged()
        self.centrePanelLayout()
        self.initProfile()


    def destroy(self):
        """Must be called when this ``OrthoPanel`` is closed.

        Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList` instances, destroys each of the three
        :class:`.SliceCanvas` panels, and calls :meth:`.CanvasPanel.destroy`.
        """

        self._displayCtx .removeListener('location',        self._name)
        self._displayCtx .removeListener('bounds',          self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        self.__xcanvas.destroy()
        self.__ycanvas.destroy()
        self.__zcanvas.destroy()

        # The _overlayListChanged method adds
        # listeners to individual overlays,
        # so we have to remove them too
        for ovl in self._overlayList:
            opts = self._displayCtx.getOpts(ovl)
            opts.removeListener('bounds', self._name)

        canvaspanel.CanvasPanel.destroy(self)


    @actions.toggleControlAction(orthotoolbar.OrthoToolBar)
    def toggleOrthoToolBar(self):
        """Shows/hides an :class:`.OrthoToolBar`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(orthotoolbar.OrthoToolBar, ortho=self)


    @actions.toggleControlAction(orthoedittoolbar.OrthoEditToolBar)
    def toggleEditMode(self):
        """Shows/hides an :class:`.OrthoEditToolBar`. This will also cause the
        :attr:`.ViewPanel.profile` to bechanged - see
        :meth:`__onToggleEditMode`.  See also :meth:`.ViewPanel.togglePanel`.
        """ 
        self.togglePanel(orthoedittoolbar.OrthoEditToolBar, ortho=self)


    def __onToggleEditMode(self, *args, **kwargs):
        """Called when the :meth:`toggleEditMode` action is triggered.
        Updates the :attr:`.ViewPanel.profile` to either ``'edit'`` or
        ``'view'`` accordingly.
        """

        if self.toggleEditMode.toggled: self.profile = 'edit'
        else:                           self.profile = 'view' 


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``OrthoPanel``.
        """
        actions = [self.screenshot,
                   self.showCommandLineArgs,
                   self.toggleEditMode,
                   self.toggleOverlayList,
                   self.toggleLocationPanel,
                   self.toggleOverlayInfo,
                   self.toggleDisplayPanel,
                   self.toggleCanvasSettingsPanel,
                   self.toggleAtlasPanel,
                   self.toggleDisplayToolBar, 
                   self.toggleOrthoToolBar,
                   self.toggleLookupTablePanel,
                   self.toggleClusterPanel,
                   self.toggleClassificationPanel] 

        names = [a.__name__ for a in actions]

        return list(zip(names, actions))

            
    def getGLCanvases(self):
        """Returns all of the :class:`.SliceCanvas` instances contained
        within this ``OrthoPanel``.
        """
        return [self.__xcanvas, self.__ycanvas, self.__zcanvas]
    

    def getXCanvas(self):
        """Returns the :class:`.SliceCanvas` instance displaying the X axis.
        """
        return self.__xcanvas

    
    def getYCanvas(self):
        """Returns the :class:`.SliceCanvas` instance displaying the Y axis.
        """ 
        return self.__ycanvas

    
    def getZCanvas(self):
        """Returns the :class:`.SliceCanvas` instance displaying the Z axis.
        """ 
        return self.__zcanvas 
        

    def __bgColourChanged(self, *a):
        """Called when the :class:`.SceneOpts.bgColour` property changes.
        Updates the panel and anatomical label background/foreground
        colours.
        
        The :attr:`.SliceCanvasOpts.bgColour` properties are bound to
        ``SceneOpts.bgColour``,(see :meth:`.HasProperties.bindProps`), so we
        don't need to manually update them.
        """
        
        bg = self.getSceneOptions().bgColour
        fg = colourmaps.complementaryColour(bg)

        # All wxwidgets things need colours
        # to be specified between 0 and 255
        intbg = [int(round(c * 255)) for c in bg]
        intfg = [int(round(c * 255)) for c in fg]

        self.getContentPanel().SetBackgroundColour(intbg)
        self.getContentPanel().SetForegroundColour(intfg)

        cbCanvas = self.getColourBarCanvas()
        if cbCanvas is not None:
            cbCanvas.textColour = fg

        self.__xcanvas.SetBackgroundColour(intbg)
        self.__ycanvas.SetBackgroundColour(intbg)
        self.__zcanvas.SetBackgroundColour(intbg)

        self.__setLabelColours(intbg, intfg)

        self.Refresh()
        self.Update()


    def __setLabelColours(self, bgColour, fgColour):
        """Used by the :meth:`__bgColourChanged` and :meth:`__refreshLabels`
        methods.

        Sets the background and foreground label colours to the given
        ``bgColour`` and ``fgColour``, which should be ``(r, g, b, a)``
        tuples with each value in the range  ``[0, 255]``.
        """

        bgColour = tuple(bgColour)
        fgColour = tuple(fgColour)

        overlay = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        allLabels = it.chain(self.__xLabels.values(),
                             self.__yLabels.values(),
                             self.__zLabels.values())

        if overlay is not None:
            opts  = self._displayCtx.getOpts(overlay)
            xform = opts.getTransform('world', 'display')
            
            xorient = overlay.getOrientation(0, xform)
            yorient = overlay.getOrientation(1, xform)
            zorient = overlay.getOrientation(2, xform)

            if constants.ORIENT_UNKNOWN in (xorient, yorient, zorient):

                # If the background colour is black or white,
                # make the foreground colour red, to highlight
                # the unknown orientation. It's too difficult
                # to do this for any background colour.
                if bgColour == (  0,   0,   0, 255) or \
                   bgColour == (255, 255, 255, 255):
                    fgColour = (255,   0,   0, 255)
        
        for lbl in allLabels:
            lbl.SetForegroundColour(fgColour)
            lbl.SetBackgroundColour(bgColour)

        
    def __toggleCanvas(self, *a):
        """Called when any of the :attr:`.OrthoOpts.showXCanvas`,
        :attr:`.OrthoOpts.showYCanvas`, or :attr:`.OrthoOpts.showZCanvas`
        properties are changed.

        Shows/hides each of the :class:`.SliceCanvas` panels and anatomical
        label panels accordingly.
        """

        opts      = self.getSceneOptions()
        canvases  = [self.__xcanvas,   self.__ycanvas,   self.__zcanvas]
        allLabels = [self.__xLabels,   self.__yLabels,   self.__zLabels]
        shows     = [opts.showXCanvas, opts.showYCanvas, opts.showZCanvas]

        for canvas, labels, show in zip(canvases, allLabels, shows):

            # See WXGLSliceCanvas.Show for
            # details of a horrible bug, and
            # equally horrible workaround..
            canvas.Show(show)

            for label in labels.values():
                self.__canvasSizer.Show(label, show and opts.showLabels)

        if opts.layout == 'grid':
            self.__refreshLayout()

        self.PostSizeEvent()


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` is changed.

        Adds a listener to the :attr:`.DisplayOpts.bounds` property for the
        currently selected overlay, to listen for changes to its bounds, which
        will trigger an update to the anatomical labels (see
        :meth:`__refreshLabels`).
        """
        
        for i, ovl in enumerate(self._overlayList):

            opts = self._displayCtx.getOpts(ovl)

            # Update anatomy labels when 
            # overlay bounds change
            opts.addListener('bounds',
                             self._name,
                             self.__refreshLabels,
                             overwrite=True)
                
        # anatomical orientation may have changed with an image change
        self.__refreshLabels()

        
    def __displaySpaceChanged(self, *a):
        """Called when the :attr:`.DisplayContext.displaySpace` changes.
        Refreshes the anatomical orientation labels.
        """
        self.__refreshLabels()

            
    def __onResize(self, ev):
        """Called whenever the panel is resized. Makes sure that the
        :class:`.SliceCanvas` panels are laid out nicely.
        """
        ev.Skip()
        self.__calcCanvasSizes()


    def __refreshLabels(self, *a):
        """Shows/hides labels depicting anatomical orientation on each
        :class:`.SliceCanvas`.
        """

        sopts = self.getSceneOptions()
        
        # Are we showing or hiding the labels?
        if len(self._overlayList) == 0:
            show = False

        overlay = self._displayCtx.getReferenceImage(
            self._displayCtx.getSelectedOverlay())

        # Labels are only supported if we
        # have a volumetric reference image 
        if   overlay is None:  showLabels = False
        elif sopts.showLabels: showLabels = True
        else:                  showLabels = False

        canvases  = [self.__xcanvas,    self.__ycanvas,    self.__zcanvas]
        allLabels = [self.__xLabels,    self.__yLabels,    self.__zLabels]
        shows     = [sopts.showXCanvas, sopts.showYCanvas, sopts.showZCanvas]

        for canvas, labels, show in zip(canvases, allLabels, shows):
            for lbl in labels.values():
                self.__canvasSizer.Show(lbl, show and showLabels)

        # If we're hiding the labels, do no more
        if not showLabels:
            self.PostSizeEvent()
            return

        log.debug('Refreshing orientation labels '
                  'according to {}'.format(overlay.name))

        # Figure out the orientation of the
        # image in the display coordinate system
        (xlo, ylo, zlo, xhi, yhi, zhi), vertOrient = self.__getLabels(overlay)
        
        log.debug('X orientation: {} - {}'.format(xlo, xhi))
        log.debug('Y orientation: {} - {}'.format(ylo, yhi))
        log.debug('Z orientation: {} - {}'.format(zlo, zhi))

        bg = sopts.bgColour
        fg = colourmaps.complementaryColour(bg)
        bg = [int(round(c * 255)) for c in bg]
        fg = [int(round(c * 255)) for c in fg]        

        self.__setLabelColours(bg, fg)

        xcxlo, xcxhi = ylo, yhi
        xcylo, xcyhi = zlo, zhi
        ycxlo, ycxhi = xlo, xhi
        ycylo, ycyhi = zlo, zhi
        zcxlo, zcxhi = xlo, xhi
        zcylo, zcyhi = ylo, yhi

        if self.__xcanvas.invertX: xcxlo, xcxhi = xcxhi, xcxlo
        if self.__xcanvas.invertY: xcylo, xcyhi = xcyhi, xcylo
        if self.__ycanvas.invertX: ycxlo, ycxhi = ycxhi, ycxlo
        if self.__ycanvas.invertY: ycylo, ycyhi = ycyhi, ycylo
        if self.__zcanvas.invertX: zcxlo, zcxhi = zcxhi, zcxlo
        if self.__zcanvas.invertY: zcylo, zcyhi = zcyhi, zcylo

        self.__xLabels['left']  .SetLabel(xcxlo)
        self.__xLabels['right'] .SetLabel(xcxhi)
        self.__xLabels['bottom'].SetLabel(xcylo)
        self.__xLabels['top']   .SetLabel(xcyhi)
        self.__yLabels['left']  .SetLabel(ycxlo)
        self.__yLabels['right'] .SetLabel(ycxhi)
        self.__yLabels['bottom'].SetLabel(ycylo)
        self.__yLabels['top']   .SetLabel(ycyhi)
        self.__zLabels['left']  .SetLabel(zcxlo)
        self.__zLabels['right'] .SetLabel(zcxhi)
        self.__zLabels['bottom'].SetLabel(zcylo)
        self.__zLabels['top']   .SetLabel(zcyhi)

        if vertOrient: vertOrient = wx.VERTICAL
        else:          vertOrient = wx.HORIZONTAL

        self.__xLabels['left'] .SetOrient(vertOrient)
        self.__yLabels['left'] .SetOrient(vertOrient)
        self.__zLabels['left'] .SetOrient(vertOrient)
        self.__xLabels['right'].SetOrient(vertOrient)
        self.__yLabels['right'].SetOrient(vertOrient)
        self.__zLabels['right'].SetOrient(vertOrient)

        self.PostSizeEvent()

        
    def __getLabels(self, refImage):
        """Generates some orientation labels to use for the given reference
        image (assumed to be a :class:`.Nifti` overlay).
        """
        
        opts = self._displayCtx.getOpts(refImage)

        vertOrient = False
        
        # If we are displaying in voxels/scaled voxels,
        # and this image is not the current display
        # image, then we do not show anatomical
        # orientation labels, as there's no guarantee
        # that all of the loaded overlays are in the
        # same orientation, and it can get confusing.
        if opts.transform in ('id', 'pixdim') and \
           self._displayCtx.displaySpace != refImage:
            xlo        = 'Xmin'
            xhi        = 'Xmax'
            ylo        = 'Ymin'
            yhi        = 'Ymax'
            zlo        = 'Zmin'
            zhi        = 'Zmax'
            vertOrient = True

        # Otherwise we assume that all images
        # are aligned to each other, so we
        # estimate the current image's orientation
        # in the display coordinate system
        else:

            vertOrient = False
            xform      = opts.getTransform('world', 'display')
            xorient    = refImage.getOrientation(0, xform)
            yorient    = refImage.getOrientation(1, xform)
            zorient    = refImage.getOrientation(2, xform)

            xlo        = strings.anatomy['Nifti', 'lowshort',  xorient]
            ylo        = strings.anatomy['Nifti', 'lowshort',  yorient]
            zlo        = strings.anatomy['Nifti', 'lowshort',  zorient]
            xhi        = strings.anatomy['Nifti', 'highshort', xorient]
            yhi        = strings.anatomy['Nifti', 'highshort', yorient]
            zhi        = strings.anatomy['Nifti', 'highshort', zorient]

        return (xlo, ylo, zlo, xhi, yhi, zhi), vertOrient


    def __calcCanvasSizes(self, *a):
        """Sets the size for each displayed :class:`.SliceCanvas`.

        The minimum/maximum size of each canvas is fixed so that they are
        scaled proportionally to each other, thus preserving the aspect ratio.
        The :mod:~fsl.utils.layout` module is used to perform the canvas size
        calculation.
        """
        
        opts   = self.getSceneOptions()
        layout = opts.layout

        width, height = self.getContentPanel().GetClientSize().Get()

        show     = [opts.showXCanvas,  opts.showYCanvas,  opts.showZCanvas]
        canvases = [self.__xcanvas,    self.__ycanvas,    self.__zcanvas]
        labels   = [self.__xLabels,    self.__yLabels,    self.__zLabels]

        if width == 0 or height == 0:   return
        if len(self._overlayList) == 0: return
        if not any(show):               return

        canvases, labels = zip(*[(c, l)
                                 for (c, l, s)
                                 in zip(canvases, labels, show)
                                 if s])

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
            canvases = [self.__ycanvas, self.__xcanvas, self.__zcanvas]

            if opts.showLabels:
                xlw = self.__xLabels['left']  .GetClientSize().GetWidth()
                xrw = self.__xLabels['right'] .GetClientSize().GetWidth()
                ylw = self.__yLabels['left']  .GetClientSize().GetWidth()
                yrw = self.__yLabels['right'] .GetClientSize().GetWidth()
                zlw = self.__zLabels['left']  .GetClientSize().GetWidth()
                zrw = self.__zLabels['right'] .GetClientSize().GetWidth()             
                xth = self.__xLabels['top']   .GetClientSize().GetHeight()
                xbh = self.__xLabels['bottom'].GetClientSize().GetHeight()
                yth = self.__yLabels['top']   .GetClientSize().GetHeight()
                ybh = self.__yLabels['bottom'].GetClientSize().GetHeight()
                zth = self.__zLabels['top']   .GetClientSize().GetHeight()
                zbh = self.__zLabels['bottom'].GetClientSize().GetHeight()
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

        
    def __refreshLayout(self, *a):
        """Called when the :attr:`.OrthoOpts.layout` property changes, or the
        canvas layout needs to be refreshed. Updates the layout accordingly.
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

        self.__canvasSizer = wx.FlexGridSizer(nrows, ncols, 0, 0)

        # The rows/columns that contain
        # canvases must also be growable
        if layout == 'horizontal':
            self.__canvasSizer.AddGrowableRow(1)
            for i in range(nCanvases):
                self.__canvasSizer.AddGrowableCol(i * 3 + 1)
                
        elif layout == 'vertical':
            self.__canvasSizer.AddGrowableCol(1)
            for i in range(nCanvases):
                self.__canvasSizer.AddGrowableRow(i * 3 + 1)
                
        elif layout == 'grid':
            self.__canvasSizer.AddGrowableRow(1)
            self.__canvasSizer.AddGrowableRow(4)
            self.__canvasSizer.AddGrowableCol(1)
            self.__canvasSizer.AddGrowableCol(4) 

        # Make a list of widgets - the canvases,
        # anatomical labels (if displayed), and
        # spacers for the empty cells
        space = (0, 0)
        xlbls = self.__xLabels
        ylbls = self.__yLabels
        zlbls = self.__zLabels
        
        if layout == 'horizontal':
            widgets = [space,         xlbls['top'],     space,
                       space,         ylbls['top'],     space,
                       space,         zlbls['top'],     space,
                       xlbls['left'], self.__xcanvas,   xlbls['right'],
                       ylbls['left'], self.__ycanvas,   ylbls['right'],
                       zlbls['left'], self.__zcanvas,   zlbls['right'],
                       space,         xlbls['bottom'],  space,
                       space,         ylbls['bottom'],  space,
                       space,         zlbls['bottom'],  space] 
                
        elif layout == 'vertical':
            widgets = [space,         xlbls['top'],     space,
                       xlbls['left'], self.__xcanvas,   xlbls['right'],
                       space,         xlbls['bottom'],  space,
                       space,         ylbls['top'],     space,
                       ylbls['left'], self.__ycanvas,   ylbls['right'],
                       space,         ylbls['bottom'],  space,
                       space,         zlbls['top'],     space,
                       zlbls['left'], self.__zcanvas,   zlbls['right'],
                       space,         zlbls['bottom'],  space]

        # The canvases are laid out in a different order
        # for orthographic, or 'grid' layout.  Assuming
        # that world axis X is left<->right, Y is
        # posterior<->anterior, and Z is inferior<->superior,
        # in order to achieve first angle orthographic
        # layout, we're laying out the canvases in the
        # following manner (the letter denotes the depth
        # axis for the respective canvas):
        #
        # TODO You need to horizonatlly flip the x canvas
        #      to achieve true orthographic display.
        #
        #    Y  X
        #    Z  - 
        elif layout == 'grid':
            widgets = [space,         ylbls['top'],     space,
                       space,         xlbls['top'],     space,
                       ylbls['left'], self.__ycanvas,   ylbls['right'],
                       xlbls['left'], self.__xcanvas,   xlbls['right'],
                       space,         ylbls['bottom'],  space,
                       space,         xlbls['bottom'],  space,
                       space,         zlbls['top'],     space,
                       space,         space,            space,
                       zlbls['left'], self.__zcanvas,   zlbls['right'],
                       space,         space,            space,
                       space,         zlbls['bottom'],  space,
                       space,         space,            space]

        # Add all those widgets to the grid sizer
        flag     = wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL
        canvases = [self.__xcanvas, self.__ycanvas, self.__zcanvas]
        
        for w in widgets:
            
            if w in canvases: self.__canvasSizer.Add(w, flag=flag | wx.EXPAND)
            else:             self.__canvasSizer.Add(w, flag=flag)
            
        self.getContentPanel().SetSizer(self.__canvasSizer)

        # Calculate/ adjust the appropriate sizes
        # for each canvas, such that they are scaled
        # appropriately relative to each other, and
        # the displayed world space aspect ratio is
        # maintained
        self.__calcCanvasSizes()

        # When in grid layout, flip the horizontal axis
        # of the X canvas (assumed to be A/P), to force
        # third angle orthographic projection.
        self.__xcanvas.invertX = layout == 'grid'

        self.Layout()
        self.getContentPanel().Layout()
        self.Refresh()


    def __locationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.locavtion` property changes.

        Sets the currently displayed x/y/z position (in display
        coordinates) on each of the :class:`.SliceCanvas` panels.
        """

        xpos, ypos, zpos = self._displayCtx.location.xyz

        self.__xcanvas.pos.xyz = [ypos, zpos, xpos]
        self.__ycanvas.pos.xyz = [xpos, zpos, ypos]
        self.__zcanvas.pos.xyz = [xpos, ypos, zpos]


class OrthoFrame(wx.Frame):
    """Convenience class for displaying an :class:`OrthoPanel` in a
    standalone frame.
    """

    def __init__(self, parent, overlayList, displayCtx, title=None):
        """Create an ``OrthoFrame``.

        :arg parent:      A :mod:`wx` parent object.
        
        :arg overlayList: An :class:`.OverlayList` instance.
        
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        
        :arg title:       Dialog title.
        """
        
        wx.Frame.__init__(self, parent, title=title)

        fslgl.getGLContext()
        fslgl.bootstrap()

        self.panel = OrthoPanel(self, overlayList, displayCtx)
        self.Layout()


class OrthoDialog(wx.Dialog):
    """Convenience class for displaying an :class:`OrthoPanel` in a (possibly
    modal) dialog window.
    """

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 title=None,
                 style=None):
        """Create an ``OrthoDialog``.

        :arg parent:      A :mod:`wx` parent object.
        
        :arg overlayList: An :class:`.OverlayList` instance.
        
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        
        :arg title:       Dialog title.
        
        :arg style:       Dialog style - defaults to
                          ``wx.DEFAULT_DIALOG_STYLE``.
        """

        if style is None:
            style = wx.DEFAULT_DIALOG_STYLE

        wx.Dialog.__init__(self, parent, title=title, style=style)

        fslgl.getGLContext()
        fslgl.bootstrap()
        
        self.panel = OrthoPanel(self, overlayList, displayCtx)
        self.Layout()
