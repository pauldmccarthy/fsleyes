#!/usr/bin/env python
#
# editor.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import collections

import numpy as np

import props
import selection

import fsl.data.image as fslimage


class ValueChange(object):
    def __init__(self, overlay, volume, offset, oldVals, newVals):
        self.overlay = overlay
        self.volume  = volume
        self.offset  = offset
        self.oldVals = oldVals
        self.newVals = newVals


class SelectionChange(object):
    def __init__(self, overlay, offset, oldSelection, newSelection):
        self.overlay      = overlay
        self.offset       = offset
        self.oldSelection = oldSelection
        self.newSelection = newSelection


class Editor(props.HasProperties):

    canUndo = props.Boolean(default=False)
    canRedo = props.Boolean(default=False)

    def __init__(self, overlayList, displayCtx):

        self._name           = '{}_{}'.format(self.__class__.__name__,
                                              id(self))
        self._overlayList    = overlayList
        self._displayCtx     = displayCtx
        self._selection      = None
        self._currentOverlay = None
 
        # A list of state objects, providing
        # records of what has been done. The
        # doneIndex points to the current
        # state. Everything before the doneIndex
        # represents previous states, and
        # everything after the doneIndex
        # represents states which have been
        # undone.
        self._doneList  = []
        self._doneIndex = -1
        self._inGroup   = False

        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self._selectedOverlayChanged)
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self._selectedOverlayChanged) 

        self._selectedOverlayChanged()

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        log.memory('{}.del ({})'.format(type(self).__name__, id(self)))

        
    def destroy(self):
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        
        if self._selection is not None:
            self._selection.removeListener('selection', self._name)

        self._overlayList    = None
        self._displayCtx     = None
        self._selection      = None
        self._currentOverlay = None
        self._doneList       = None


    def _selectedOverlayChanged(self, *a):
        overlay = self._displayCtx.getSelectedOverlay()

        if self._currentOverlay == overlay:
            return

        if overlay is None:
            self._currentOverlay = None
            self._selection      = None
            return

        display = self._displayCtx.getDisplay(overlay)

        if not isinstance(overlay, fslimage.Image) or \
           display.overlayType != 'volume':
            self._currentOverlay = None
            self._selection      = None
            return

        if self._selection is not None:
            oldSel = self._selection.transferSelection(
                overlay, display)
        else:
            oldSel = None
                        
        self._currentOverlay = overlay
        self._selection      = selection.Selection(overlay,
                                                   display,
                                                   oldSel)

        self._selection.addListener('selection',
                                    self._name,
                                    self._selectionChanged)


    def _selectionChanged(self, *a):

        old, new, offset = self._selection.getLastChange()
        
        change = SelectionChange(self._currentOverlay, offset, old, new)
        self._changeMade(change)


    def getSelection(self):
        return self._selection


    def fillSelection(self, newVals):

        overlay = self._currentOverlay

        if overlay is None:
            return
        
        opts = self._displayCtx.getOpts(overlay)

        selectBlock, offset = self._selection.getBoundedSelection()

        if not isinstance(newVals, collections.Sequence):
            nv = np.zeros(selectBlock.shape, dtype=np.float32)
            nv.fill(newVals)
            newVals = nv
        else:
            newVals = np.array(newVals)

        xlo, ylo, zlo = offset
        xhi = xlo + selectBlock.shape[0]
        yhi = ylo + selectBlock.shape[1]
        zhi = zlo + selectBlock.shape[2]

        if   len(overlay.shape) == 3:
            oldVals = overlay.data[xlo:xhi, ylo:yhi, zlo:zhi]
        elif len(overlay.shape) == 4:
            oldVals = overlay.data[xlo:xhi, ylo:yhi, zlo:zhi, opts.volume]
        else:
            raise RuntimeError('Only 3D and 4D images are currently supported')

        selectBlock = selectBlock == 0
        newVals[selectBlock] = oldVals[selectBlock]

        oldVals = np.array(oldVals)
        
        change = ValueChange(overlay, opts.volume, offset, oldVals, newVals)
        self._applyChange(change)
        self._changeMade( change)

        
    def startChangeGroup(self):
        del self._doneList[self._doneIndex + 1:]
        
        self._inGroup    = True
        self._doneIndex += 1
        self._doneList.append([])

        log.debug('Starting change group - merging subsequent '
                  'changes at index {} of {}'.format(self._doneIndex,
                                                     len(self._doneList)))

        
    def endChangeGroup(self):
        self._inGroup = False
        log.debug('Ending change group at {} of {}'.format(
            self._doneIndex, len(self._doneList))) 

        
    def _changeMade(self, change):

        if self._inGroup:
            self._doneList[self._doneIndex].append(change)
        else:
            del self._doneList[self._doneIndex + 1:]
            self._doneList.append(change)
            self._doneIndex += 1
            
        self.canUndo = True
        self.canRedo = False

        log.debug('New change ({} of {})'.format(self._doneIndex,
                                                 len(self._doneList)))


    def undo(self):
        if self._doneIndex == -1:
            return

        log.debug('Undo change {} of {}'.format(self._doneIndex,
                                                len(self._doneList)))        

        change = self._doneList[self._doneIndex]

        if not isinstance(change, collections.Sequence):
            change = [change]

        for c in reversed(change):
            self._revertChange(c)

        self._doneIndex -= 1

        self._inGroup = False
        self.canRedo  = True
        if self._doneIndex == -1:
            self.canUndo = False
        

    def redo(self):
        if self._doneIndex == len(self._doneList) - 1:
            return

        log.debug('Redo change {} of {}'.format(self._doneIndex + 1,
                                                len(self._doneList))) 

        change = self._doneList[self._doneIndex + 1]
        
        if not isinstance(change, collections.Sequence):
            change = [change] 

        for c in change:
            self._applyChange(c)

        self._doneIndex += 1

        self._inGroup = False
        self.canUndo  = True
        if self._doneIndex == len(self._doneList) - 1:
            self.canRedo = False


    def _applyChange(self, change):

        overlay = change.overlay
        opts    = self._displayCtx.getOpts(overlay)

        if overlay.is4DImage(): volume = opts.volume
        else:                   volume = None
        
        self._displayCtx.selectOverlay(overlay)

        if isinstance(change, ValueChange):
            log.debug('Changing image data - offset '
                      '{}, volume {}, size {}'.format(
                          change.offset, change.volume, change.oldVals.shape))
            change.overlay.applyChange(change.offset, change.newVals, volume)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.newSelection, change.offset)
            self._selection.enableListener('selection', self._name)

        
    def _revertChange(self, change):

        overlay = change.overlay
        opts    = self._displayCtx.getOpts(overlay)
        
        self._displayCtx.selectOverlay(overlay)

        if overlay.is4DImage(): volume = opts.volume
        else:                   volume = None 

        if isinstance(change, ValueChange):
            log.debug('Reverting image data change - offset '
                      '{}, volume {}, size {}'.format(
                          change.offset, change.volume, change.oldVals.shape))
            change.overlay.applyChange(change.offset, change.oldVals, volume)
            
        elif isinstance(change, SelectionChange):
            self._selection.disableListener('selection', self._name)
            self._selection.setSelection(change.oldSelection, change.offset)
            self._selection.enableListener('selection', self._name)


    def createMaskFromSelection(self):

        overlay = self._currentOverlay
        if overlay is None:
            return

        overlayIdx = self._overlayList.index(overlay)
        mask       = np.array(self._selection.selection, dtype=np.uint8)
        header     = overlay.nibImage.get_header()
        name       = '{}_mask'.format(overlay.name)

        roiImage = fslimage.Image(mask, name=name, header=header)
        self._overlayList.insert(overlayIdx + 1, roiImage) 


    def createROIFromSelection(self):

        overlay = self._currentOverlay
        if overlay is None:
            return

        overlayIdx = self._overlayList.index(overlay) 
        opts       = self._displayCtx.getDisplay(overlay)
        
        roi       = np.zeros(overlay.shape[:3], dtype=overlay.data.dtype)
        selection = self._selection.selection > 0

        if   len(overlay.shape) == 3:
            roi[selection] = overlay.data[selection]
        elif len(overlay.shape) == 4:
            roi[selection] = overlay.data[:, :, :, opts.volume][selection]
        else:
            raise RuntimeError('Only 3D and 4D images are currently supported')

        header = overlay.nibImage.get_header()
        name   = '{}_roi'.format(overlay.name)

        roiImage = fslimage.Image(roi, name=name, header=header)
        self._overlayList.insert(overlayIdx + 1, roiImage)
