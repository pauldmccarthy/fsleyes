#!/usr/bin/env python
#
# orthoeditprofile.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                        as np

import                                 props
import fsl.data.image               as fslimage
import fsl.fsleyes.editor.editor    as editor
import fsl.fsleyes.gl.annotations   as annotations

import orthoviewprofile


log = logging.getLogger(__name__)


class OrthoEditProfile(orthoviewprofile.OrthoViewProfile):

    selectionSize  = props.Int(minval=1, default=3, clamped=True)
    selectionIs3D  = props.Boolean(default=False)
    fillValue      = props.Real(default=0)

    intensityThres = props.Real(minval=0.0, default=10, clamped=True)
    localFill      = props.Boolean(default=False)

    selectionCursorColour  = props.Colour(default=(1, 1, 0, 0.7))
    selectionOverlayColour = props.Colour(default=(1, 0, 1, 0.7))

    limitToRadius  = props.Boolean(default=False)
    searchRadius   = props.Real(minval=0.0, default=0.0, clamped=True)

    
    def clearSelection(self, *a):
        self._editor.getSelection().clearSelection()
        self._viewPanel.Refresh()


    def fillSelection(self, *a):
        self._editor.fillSelection(self.fillValue)
        self._editor.getSelection().clearSelection()


    def undo(self, *a):

        # We're disabling notification of changes to the selection
        # during undo/redo. This is because a single undo
        # will probably involve multiple modifications to the
        # selection (as changes are grouped by the editor),
        # with each of those changes causing the selection object
        # to notify its listeners. As one of these listeners is a
        # SelectionTexture, these notifications can get expensive,
        # due to updates to the GL texture buffer. So we disable
        # notification, and then manually refresh the texture
        # afterwards
        self._editor.getSelection().disableNotification('selection')
        self._editor.undo()
        self._editor.getSelection().enableNotification('selection')
        
        self._selectionChanged()
        self._selAnnotation.texture.refresh()
        self._viewPanel.Refresh()


    def redo(self, *a):

        self._editor.getSelection().disableNotification('selection')
        self._editor.redo()
        self._editor.getSelection().enableNotification('selection')
        self._selectionChanged()
        self._selAnnotation.texture.refresh()
        self._viewPanel.Refresh()
 

    def __init__(self, viewPanel, overlayList, displayCtx):

        self._editor            = editor.Editor(overlayList, displayCtx) 
        self._xcanvas           = viewPanel.getXCanvas()
        self._ycanvas           = viewPanel.getYCanvas()
        self._zcanvas           = viewPanel.getZCanvas() 
        self._selAnnotation     = None
        self._xCursorAnnotation = None
        self._yCursorAnnotation = None
        self._zCursorAnnotation = None
        self._selecting         = False
        self._lastDist          = None
        self._currentOverlay    = None
        
        actions = {
            'undo'                    : self.undo,
            'redo'                    : self.redo,
            'fillSelection'           : self.fillSelection,
            'clearSelection'          : self.clearSelection,
            'createMaskFromSelection' : self._editor.createMaskFromSelection,
            'createROIFromSelection'  : self._editor.createROIFromSelection}

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            viewPanel,
            overlayList,
            displayCtx,
            ['sel', 'desel', 'selint'],
            actions)

        self.mode = 'sel'

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self._selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self._selectedOverlayChanged)

        self._editor.addListener('canUndo',
                                 self._name,
                                 self._undoStateChanged)
        self._editor.addListener('canRedo',
                                 self._name,
                                 self._undoStateChanged)

        self.addListener('selectionOverlayColour',
                         self._name,
                         self._selectionColoursChanged)
        self.addListener('selectionCursorColour',
                         self._name,
                         self._selectionColoursChanged) 

        self._selectedOverlayChanged()
        self._selectionChanged()
        self._undoStateChanged()


    def destroy(self):

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self._editor     .removeListener('canUndo',         self._name)
        self._editor     .removeListener('canRedo',         self._name)

        self._editor.destroy()

        self._editor = None

        orthoviewprofile.OrthoViewProfile.destroy(self)


    def _undoStateChanged(self, *a):
        self.enable('undo', self._editor.canUndo)
        self.enable('redo', self._editor.canRedo)


    def _selectionColoursChanged(self, *a):
        if self._selAnnotation is not None:
            self._selAnnotation.colour = self.selectionOverlayColour

        if self._xCursorAnnotation is not None:
            self._xCursorAnnotation.colour = self.selectionCursorColour
        if self._yCursorAnnotation is not None:
            self._yCursorAnnotation.colour = self.selectionCursorColour
        if self._zCursorAnnotation is not None:
            self._zCursorAnnotation.colour = self.selectionCursorColour 


    def _selectedOverlayChanged(self, *a):

        overlay   = self._displayCtx.getSelectedOverlay()
        selection = self._editor.getSelection() 
        xannot    = self._xcanvas.getAnnotations()
        yannot    = self._ycanvas.getAnnotations()
        zannot    = self._zcanvas.getAnnotations()        

        # If the selected overlay hasn't changed,
        # we don't need to do anything
        if overlay == self._currentOverlay:
            return

        # If there's already an existing
        # selection object, clear it 
        if self._selAnnotation is not None:
            xannot.dequeue(self._selAnnotation, hold=True)
            yannot.dequeue(self._selAnnotation, hold=True)
            zannot.dequeue(self._selAnnotation, hold=True)
            
            self._selAnnotation.destroy()

        xca = self._xCursorAnnotation
        yca = self._yCursorAnnotation
        zca = self._zCursorAnnotation

        if xca is not None: xannot.dequeue(xca, hold=True)
        if yca is not None: yannot.dequeue(yca, hold=True)
        if zca is not None: yannot.dequeue(xca, hold=True)
            
        self._xCursorAnnotation = None
        self._yCursorAnnotation = None
        self._zCursorAnnotation = None
        self._selAnnotation     = None

        self._currentOverlay = overlay

        # If there is no selected overlay (the overlay
        # list is empty), don't do anything.
        if overlay is None:
            return

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        # Edit mode is only supported on images with
        # the 'volume' type, in 'id' or 'pixdim'
        # transformation for the time being
        if not isinstance(overlay, fslimage.Image) or \
           display.overlayType != 'volume'         or \
           opts.transform not in ('id', 'pixdim'):
            
            self._currentOverlay = None
            log.warn('Editing is only possible on volume '
                     'images, in ID or pixdim space.')
            return

        # Otherwise, create a selection annotation
        # and queue it on the canvases for drawing

        selection.addListener('selection', self._name, self._selectionChanged)

        self._selAnnotation = annotations.VoxelSelection( 
            selection,
            opts.getTransform('display', 'voxel'),
            opts.getTransform('voxel',   'display'),
            colour=self.selectionOverlayColour)

        kwargs = {'colour' : self.selectionCursorColour,
                  'width'  : 2}

        xca = annotations.Rect((0, 0), 0, 0, **kwargs)
        yca = annotations.Rect((0, 0), 0, 0, **kwargs)
        zca = annotations.Rect((0, 0), 0, 0, **kwargs)
        self._xCursorAnnotation = xca
        self._yCursorAnnotation = yca
        self._zCursorAnnotation = zca
        
        xannot.obj(self._selAnnotation,     hold=True)
        yannot.obj(self._selAnnotation,     hold=True)
        zannot.obj(self._selAnnotation,     hold=True)
        xannot.obj(self._xCursorAnnotation, hold=True)
        yannot.obj(self._yCursorAnnotation, hold=True)
        zannot.obj(self._zCursorAnnotation, hold=True)

        self._viewPanel.Refresh()


    def _selectionChanged(self, *a):
        selection = self._editor.getSelection()
        selSize   = selection.getSelectionSize()

        self.enable('createMaskFromSelection', selSize > 0)
        self.enable('createROIFromSelection',  selSize > 0)
        self.enable('clearSelection',          selSize > 0)
        self.enable('fillSelection',           selSize > 0)

    
    def deregister(self):
        if self._selAnnotation is not None:
            sa = self._selAnnotation
            self._xcanvas.getAnnotations().dequeue(sa, hold=True)
            self._ycanvas.getAnnotations().dequeue(sa, hold=True)
            self._zcanvas.getAnnotations().dequeue(sa, hold=True)
            sa.destroy()

        xca = self._xCursorAnnotation
        yca = self._yCursorAnnotation
        zca = self._zCursorAnnotation

        if xca is not None:
            self._xcanvas.getAnnotations().dequeue(xca, hold=True)
        if yca is not None:
            self._ycanvas.getAnnotations().dequeue(yca, hold=True)
        if zca is not None:
            self._zcanvas.getAnnotations().dequeue(zca, hold=True)

        self._selAnnotation     = None
        self._xCursorAnnotation = None
        self._yCursorAnnotation = None
        self._zCursorAnnotation = None
            
        orthoviewprofile.OrthoViewProfile.deregister(self)

        
    def _getVoxelLocation(self, canvasPos):
        """Returns the voxel location, for the currently selected overlay,
        which corresponds to the specified canvas position.
        """
        
        opts  = self._displayCtx.getOpts(self._currentOverlay)
        voxel = opts.transformCoords([canvasPos], 'display', 'voxel')[0]

        return np.int32(np.floor(voxel))


    def _makeSelectionAnnotation(
            self, canvas, voxel, canvasPos, blockSize=None):
        """Highlights the specified voxel with a selection annotation.
        This is used by mouse motion event handlers, so the user can
        see the possible selection, and thus what would happen if they
        were to click.
        """

        opts  = self._displayCtx.getOpts(self._currentOverlay)

        canvases = [self._xcanvas, self._ycanvas, self._zcanvas]
        cursors  = [self._xCursorAnnotation,
                    self._yCursorAnnotation,
                    self._zCursorAnnotation]

        # If we are running in a low
        # performance mode, the cursor
        # is only drawn on the current
        # canvas.
        if self._viewPanel.getSceneOptions().performance < 5:
            cursors  = [cursors[canvases.index(canvas)]]
            canvases = [canvas]

        if blockSize is None:
            blockSize = self.selectionSize

        # TODO Double check this, as it seems to be wrong
        lo = [(v)     - int(np.floor((blockSize - 1) / 2.0)) for v in voxel]
        hi = [(v + 1) + int(np.ceil(( blockSize - 1) / 2.0)) for v in voxel]

        if not self.selectionIs3D:
            lo[canvas.zax] = voxel[canvas.zax]
            hi[canvas.zax] = voxel[canvas.zax] + 1

        corners       = np.zeros((8, 3))
        corners[0, :] = lo[0], lo[1], lo[2]
        corners[1, :] = lo[0], lo[1], hi[2]
        corners[2, :] = lo[0], hi[1], lo[2]
        corners[3, :] = lo[0], hi[1], hi[2]
        corners[4, :] = hi[0], lo[1], lo[2]
        corners[5, :] = hi[0], lo[1], hi[2]
        corners[6, :] = hi[0], hi[1], lo[2]
        corners[7, :] = hi[0], hi[1], hi[2]

        # We want the selection to follow voxel
        # edges, but the transformCoords method
        # will map voxel coordinates to the
        # displayed voxel centre. So we offset
        # by -0.5 to get the corners
        corners = opts.transformCoords(corners - 0.5, 'voxel', 'display')

        cmin = corners.min(axis=0)
        cmax = corners.max(axis=0)

        for cursor, canvas in zip(cursors, canvases):
            xax = canvas.xax
            yax = canvas.yax
            zax = canvas.zax

            if canvas.pos.z < cmin[zax] or canvas.pos.z > cmax[zax]:
                cursor.w = 0
                cursor.h = 0
                continue
            
            cursor.xy = cmin[[xax, yax]]
            cursor.w  = cmax[xax] - cmin[xax]
            cursor.h  = cmax[yax] - cmin[yax]
            

    def _applySelection(self, canvas, voxel, add=True):

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)        

        selection     = self._editor.getSelection()
        block, offset = selection.generateBlock(voxel,
                                                self.selectionSize,
                                                selection.selection.shape,
                                                axes)

        if add: selection.addToSelection(     block, offset)
        else:   selection.removeFromSelection(block, offset)


    def _refreshCanvases(self, ev, canvas, mousePos=None, canvasPos=None):
        """
        """
        perf = self._viewPanel.getSceneOptions().performance
        if perf == 5:
            if mousePos is None or canvasPos is None:
                self._viewPanel.Refresh()

            # If running in high performance mode, we make
            # the canvas location track the edit cursor
            # location, so that the other two canvases
            # update to display the current cursor location.
            else:
                self._navModeLeftMouseDrag(ev, canvas, mousePos, canvasPos)
        else:
            canvas.Refresh()

            
    def _selModeMouseWheel(self, ev, canvas, wheelDir, mousePos, canvasPos):

        if   wheelDir > 0: self.selectionSize += 1
        elif wheelDir < 0: self.selectionSize -= 1

        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel, canvasPos)
        
        self._refreshCanvases(ev, canvas)


    def _selModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel, canvasPos)
        self._refreshCanvases(ev, canvas)


    def _selModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        self._editor.startChangeGroup()

        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel)
        self._makeSelectionAnnotation(canvas, voxel, canvasPos)
        self._refreshCanvases(ev, canvas, mousePos, canvasPos)


    def _selModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel)
        self._makeSelectionAnnotation(canvas, voxel, canvasPos)
        self._refreshCanvases(ev, canvas, mousePos, canvasPos)


    def _selModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._editor.endChangeGroup()
        self._viewPanel.Refresh()


    def _selModeMouseLeave(self, ev, canvas, mousePos, canvasPos):
        
        cursors = [self._xCursorAnnotation,
                   self._yCursorAnnotation,
                   self._zCursorAnnotation]

        for cursor in cursors:
            if cursor is not None:
                cursor.w = 0
                cursor.h = 0

        self._refreshCanvases(ev, canvas)

        
    def _deselModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        self._editor.startChangeGroup()

        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel, False)
        self._makeSelectionAnnotation(canvas, voxel, canvasPos)
        self._refreshCanvases(ev, canvas, mousePos, canvasPos)


    def _deselModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._applySelection(         canvas, voxel, False)
        self._makeSelectionAnnotation(canvas, voxel, canvasPos)
        self._refreshCanvases(ev, canvas, mousePos, canvasPos)

        
    def _deselModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._editor.endChangeGroup()
        self._viewPanel.Refresh()

        
    def _selintModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        voxel = self._getVoxelLocation(canvasPos)
        self._makeSelectionAnnotation(canvas, voxel, canvasPos, 1)
        self._refreshCanvases(ev, canvas)

        
    def _selintModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):

        self._editor.startChangeGroup()
        self._editor.getSelection().clearSelection() 
        self._selecting = True
        self._lastDist  = 0
        self._selintSelect(self._getVoxelLocation(canvasPos))
        self._refreshCanvases(ev, canvas, mousePos, canvasPos)

        
    def _selintModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):

        if not self.limitToRadius:
            voxel = self._getVoxelLocation(canvasPos)
            self._makeSelectionAnnotation(canvas, voxel, canvasPos, 1)

            refreshArgs = (ev, canvas, mousePos, canvasPos)
            
        else:
            mouseDownPos, canvasDownPos = self.getMouseDownLocation()
            voxel                       = self._getVoxelLocation(canvasDownPos)

            cx,  cy,  cz  = canvasPos
            cdx, cdy, cdz = canvasDownPos

            dist = np.sqrt((cx - cdx) ** 2 + (cy - cdy) ** 2 + (cz - cdz) ** 2)
            self.searchRadius = dist

            refreshArgs = (ev, canvas)

        self._selintSelect(voxel)
        self._refreshCanvases(*refreshArgs)

        
    def _selintModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):

        if not self._selecting:
            return

        overlay = self._displayCtx.getSelectedOverlay()
        opts    = self._displayCtx.getOpts(overlay)

        dataRange = opts.dataMax - opts.dataMin
        step      = 0.01 * dataRange

        if   wheel > 0: self.intensityThres += step
        elif wheel < 0: self.intensityThres -= step

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()
        voxel                       = self._getVoxelLocation(canvasDownPos) 

        self._selintSelect(voxel)
        self._refreshCanvases(ev, canvas)
        
            
    def _selintSelect(self, voxel):
        
        overlay = self._displayCtx.getSelectedOverlay()
        
        if not self.limitToRadius or self.searchRadius == 0:
            searchRadius = None
        else:
            searchRadius = (self.searchRadius / overlay.pixdim[0],
                            self.searchRadius / overlay.pixdim[1],
                            self.searchRadius / overlay.pixdim[2])

        # If the last selection covered a bigger radius
        # than this selection, clear the whole selection 
        if self._lastDist is None or \
           np.any(np.array(searchRadius) < self._lastDist):
            self._editor.getSelection().clearSelection()

        self._editor.getSelection().selectByValue(
            voxel,
            precision=self.intensityThres,
            searchRadius=searchRadius,
            local=self.localFill)

        self._lastDist = searchRadius

        
    def _selintModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        self._editor.endChangeGroup()
        self._selecting = False
        self._viewPanel.Refresh()
