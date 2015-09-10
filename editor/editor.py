#!/usr/bin/env python
#
# editor.py - The Editor class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Editor` class, which provides
functionality to edit the data in an :class:`.Image` overlay.
"""


import logging

import collections

import numpy as np

import props
import selection

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


class Editor(props.HasProperties):
    """The ``Editor`` class provides functionality to edit the data of an
    :class:`.Image` overlay.

    An ``Editor`` instance uses a :class:`.Selection` object which allows
    voxel selections to be made, and keeps track of all changes to the
    selection and image.


    .. autosummary::
       :nosignatures:
    
       getSelection
       fillSelection
       createMaskFromSelection
       createROIFromSelection

    Undo/redo and change groups.

    .. autosummary::
       :nosignatures:

       undo
       redo
       startChangeGroup
       endChangeGroup
    """

    canUndo = props.Boolean(default=False)
    """
    """

    
    canRedo = props.Boolean(default=False)
    """
    """

    
    def __init__(self, overlayList, displayCtx):

        self.__name           = '{}_{}'.format(self.__class__.__name__,
                                               id(self))
        self.__overlayList    = overlayList
        self.__displayCtx     = displayCtx
        self.__selection      = None
        self.__currentOverlay = None
 
        # A list of state objects, providing
        # records of what has been done. The
        # doneIndex points to the current
        # state. Everything before the doneIndex
        # represents previous states, and
        # everything after the doneIndex
        # represents states which have been
        # undone.
        self.__doneList  = []
        self.__doneIndex = -1
        self.__inGroup   = False

        self.__displayCtx .addListener('selectedOverlay',
                                       self.__name,
                                       self.__selectedOverlayChanged)
        self.__overlayList.addListener('overlays',
                                       self.__name,
                                       self.__selectedOverlayChanged) 

        self.__selectedOverlayChanged()

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        log.memory('{}.del ({})'.format(type(self).__name__, id(self)))

        
    def destroy(self):
        self.__displayCtx .removeListener('selectedOverlay', self.__name)
        self.__overlayList.removeListener('overlays',        self.__name)
        
        if self.__selection is not None:
            self.__selection.removeListener('selection', self.__name)

        self.__overlayList    = None
        self.__displayCtx     = None
        self.__selection      = None
        self.__currentOverlay = None
        self.__doneList       = None


    def getSelection(self):
        return self.__selection


    def fillSelection(self, newVals):

        overlay = self.__currentOverlay

        if overlay is None:
            return
        
        opts = self.__displayCtx.getOpts(overlay)

        selectBlock, offset = self.__selection.getBoundedSelection()

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
        self.__applyChange(change)
        self.__changeMade( change)

            
    def createMaskFromSelection(self):

        overlay = self.__currentOverlay
        if overlay is None:
            return

        overlayIdx = self.__overlayList.index(overlay)
        mask       = np.array(self.__selection.selection, dtype=np.uint8)
        header     = overlay.nibImage.get_header()
        name       = '{}_mask'.format(overlay.name)

        roiImage = fslimage.Image(mask, name=name, header=header)
        self.__overlayList.insert(overlayIdx + 1, roiImage) 


    def createROIFromSelection(self):

        overlay = self.__currentOverlay
        if overlay is None:
            return

        overlayIdx = self.__overlayList.index(overlay) 
        opts       = self.__displayCtx.getDisplay(overlay)
        
        roi       = np.zeros(overlay.shape[:3], dtype=overlay.data.dtype)
        selection = self.__selection.selection > 0

        if   len(overlay.shape) == 3:
            roi[selection] = overlay.data[selection]
        elif len(overlay.shape) == 4:
            roi[selection] = overlay.data[:, :, :, opts.volume][selection]
        else:
            raise RuntimeError('Only 3D and 4D images are currently supported')

        header = overlay.nibImage.get_header()
        name   = '{}_roi'.format(overlay.name)

        roiImage = fslimage.Image(roi, name=name, header=header)
        self.__overlayList.insert(overlayIdx + 1, roiImage)

        
    def startChangeGroup(self):
        del self.__doneList[self.__doneIndex + 1:]
        
        self.__inGroup    = True
        self.__doneIndex += 1
        self.__doneList.append([])

        log.debug('Starting change group - merging subsequent '
                  'changes at index {} of {}'.format(self.__doneIndex,
                                                     len(self.__doneList)))

        
    def endChangeGroup(self):
        self.__inGroup = False
        log.debug('Ending change group at {} of {}'.format(
            self.__doneIndex, len(self.__doneList))) 


    def undo(self):
        if self.__doneIndex == -1:
            return

        log.debug('Undo change {} of {}'.format(self.__doneIndex,
                                                len(self.__doneList)))        

        change = self.__doneList[self.__doneIndex]

        if not isinstance(change, collections.Sequence):
            change = [change]

        for c in reversed(change):
            self.__revertChange(c)

        self.__doneIndex -= 1

        self.__inGroup = False
        self.canRedo  = True
        if self.__doneIndex == -1:
            self.canUndo = False
        

    def redo(self):
        if self.__doneIndex == len(self.__doneList) - 1:
            return

        log.debug('Redo change {} of {}'.format(self.__doneIndex + 1,
                                                len(self.__doneList))) 

        change = self.__doneList[self.__doneIndex + 1]
        
        if not isinstance(change, collections.Sequence):
            change = [change] 

        for c in change:
            self.__applyChange(c)

        self.__doneIndex += 1

        self.__inGroup = False
        self.canUndo  = True
        if self.__doneIndex == len(self.__doneList) - 1:
            self.canRedo = False


    def __selectedOverlayChanged(self, *a):
        overlay = self.__displayCtx.getSelectedOverlay()

        if self.__currentOverlay == overlay:
            return

        if overlay is None:
            self.__currentOverlay = None
            self.__selection      = None
            return

        display = self.__displayCtx.getDisplay(overlay)

        if not isinstance(overlay, fslimage.Image) or \
           display.overlayType != 'volume':
            self.__currentOverlay = None
            self.__selection      = None
            return

        if self.__selection is not None:
            oldSel = self.__selection.transferSelection(
                overlay, display)
        else:
            oldSel = None
                        
        self.__currentOverlay = overlay
        self.__selection      = selection.Selection(overlay,
                                                    display,
                                                    oldSel)

        self.__selection.addListener('selection',
                                     self.__name,
                                     self.__selectionChanged)


    def __selectionChanged(self, *a):

        old, new, offset = self.__selection.getLastChange()
        
        change = SelectionChange(self.__currentOverlay, offset, old, new)
        self.__changeMade(change)

        
    def __changeMade(self, change):

        if self.__inGroup:
            self.__doneList[self.__doneIndex].append(change)
        else:
            del self.__doneList[self.__doneIndex + 1:]
            self.__doneList.append(change)
            self.__doneIndex += 1
            
        self.canUndo = True
        self.canRedo = False

        log.debug('New change ({} of {})'.format(self.__doneIndex,
                                                 len(self.__doneList)))


    def __applyChange(self, change):

        overlay = change.overlay
        opts    = self.__displayCtx.getOpts(overlay)

        if overlay.is4DImage(): volume = opts.volume
        else:                   volume = None
        
        self.__displayCtx.selectOverlay(overlay)

        if isinstance(change, ValueChange):
            log.debug('Changing image data - offset '
                      '{}, volume {}, size {}'.format(
                          change.offset, change.volume, change.oldVals.shape))
            change.overlay.applyChange(change.offset, change.newVals, volume)
            
        elif isinstance(change, SelectionChange):
            self.__selection.disableListener('selection', self.__name)
            self.__selection.setSelection(change.newSelection, change.offset)
            self.__selection.enableListener('selection', self.__name)

        
    def __revertChange(self, change):

        overlay = change.overlay
        opts    = self.__displayCtx.getOpts(overlay)
        
        self.__displayCtx.selectOverlay(overlay)

        if overlay.is4DImage(): volume = opts.volume
        else:                   volume = None 

        if isinstance(change, ValueChange):
            log.debug('Reverting image data change - offset '
                      '{}, volume {}, size {}'.format(
                          change.offset, change.volume, change.oldVals.shape))
            change.overlay.applyChange(change.offset, change.oldVals, volume)
            
        elif isinstance(change, SelectionChange):
            self.__selection.disableListener('selection', self.__name)
            self.__selection.setSelection(change.oldSelection, change.offset)
            self.__selection.enableListener('selection', self.__name)


class ValueChange(object):
    """Represents a change which has been made to the data for an
    :class:`.Image` instance. Stores the location, the old values,
    and the new values.
    """

    
    def __init__(self, overlay, volume, offset, oldVals, newVals):
        """Create a ``ValueChange``.

        :arg overlay: The :class:`.Image` instance.
        :arg volume:  Volume index, if ``overlay`` is 4D.
        :arg offset:  Location (voxel coordinates) of the change.
        :arg oldVals: A ``numpy`` array containing the old image values.
        :arg newVals: A ``numpy`` array containing the new image values.
        """
        
        self.overlay = overlay
        self.volume  = volume
        self.offset  = offset
        self.oldVals = oldVals
        self.newVals = newVals


class SelectionChange(object):
    """Represents a change which has been made to a :class:`.Selection`
    instance. Stores the location, the old selection, and the new selection.
    """

    
    def __init__(self, overlay, offset, oldSelection, newSelection):
        """Create a ``SelectionChange``.
        
        :arg overlay:      The :class:`.Image` instance.
        :arg offset:       Location (voxel coordinates) of the change.
        :arg oldSelection: A ``numpy`` array containing the old selection.
        :arg newSelection: A ``numpy`` array containing the new selection.
        """
        
        self.overlay      = overlay
        self.offset       = offset
        self.oldSelection = oldSelection
        self.newSelection = newSelection
