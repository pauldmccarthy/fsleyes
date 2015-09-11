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
    voxel selections to be made, and keeps track of all changes to both the
    selection and image data.

    
    **The editing process**

    
    Making changes to the data in an :class:`.Image` involves two steps:

     1. Create a selection

     2. Change the value of voxels in that selection

    
    The first step can be peformed by working directly with the
    :class:`.Selection` object - this is accessible via the
    :meth:`getSelection` method. The :meth:`fillSelection` method can be used
    to perform the second step.

    
    .. warning:: An important point to keep in mind is that whenever the
                 :attr:`.DisplayContext.selectedOverlay` property changes, the
                 ``Editor`` will discard the current :class:`.Selection`
                 instance, and create a new one, which matches the resolution
                 of the newly selected overlay (if the new overlay is not an
                 :class:`.Image`, a ``Selection`` object is not created).
                 Therefore, it is probably a bad idea to store your own
                 reference to the current ``Selection`` object - just use the
                 :meth:`getSelection` method.

                 I may change this behaviour in the future, as it is a
                 potential bug source. I will possibly change the structure so
                 that ``Editor`` instances are created/destroyed for
                 individual overlays.

    
    Some convenience methods are also provided for working with selections:

    .. autosummary::
       :nosignatures:
    
       createMaskFromSelection
       createROIFromSelection


    **Change tracking**


    An ``Editor`` instance keeps track of all changes made to both the
    :class:`Selection` object, and to the :class:`Image` data. Every
    selection/data change made is recorded with the :class:`SelectionChange`
    and :class:`.ValueChange` classes, and stored in a list. This allows these
    changes to be undone (and redone), through the :meth:`undo` and
    :meth:`redo` methods. The ``Editor`` class also has two properties,
    :attr:`canUndo` and :attr:`canRedo`, which reflect the current state of
    the ``Editor`` with respect to its ability to undo/redo operations.

    
    Sometimes it is useful to treat may small changes as a single large
    change.  For example, if a selection is being updated by dragging the
    mouse across a canvas, storing a separate change for every change in mouse
    position would result in many small changes which, if the user then wishes
    to undo, would have to be undone one by one. This problem can be overcome
    by the use of *change groups*. Whenever an operation similar to the above
    begins, you can call the :meth:`startChangeGroup` method - from now on,
    all changes will be aggregated into one group. When the operation
    completes, call the :meth:`endChangeGroup` to stop group changes.  When
    undoing/redoing changes, all of the changes in a change group will be
    undone/redone together.
    """

    
    canUndo = props.Boolean(default=False)
    """This property will be ``True`` when the ``Editor`` has changes which
    can be undone, and ``False`` otherwise.
    """

    
    canRedo = props.Boolean(default=False)
    """This property will be ``True`` when the ``Editor`` has changes which
    can be redone, and ``False`` otherwise.
    """    

    
    def __init__(self, overlayList, displayCtx):
        """Create an ``Editor``.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

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
        """Prints a log message."""
        log.memory('{}.del ({})'.format(type(self).__name__, id(self)))

        
    def destroy(self):
        """Removes some property listeners, and clears references to objects
        to prevent memory leaks.
        """
        
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
        """Returns the :class:`.Selection` instance currently in use. """
        return self.__selection


    def fillSelection(self, newVals):
        """Fills the currnent selection with the specified value or values.

        :arg newVals: A scalar value, or a sequence containing the same
                      number of values as the current selection size.
        """

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
        """Creates a new :class:`.Image` overlay, which represents a mask
        of the current selection. The new ``Image`` is inserted into the
        :class:`.OverlayList`.
        """

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
        """Creates a new :class:`.Image` overlay, which contains the values
        from the current ``Image``, where the current selection is non-zero,
        and zeroes everywhere else.
        
        The new ``Image`` is inserted into the :class:`.OverlayList`.
        """ 

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
        """Starts a change group. All subsequent changes will be grouped
        together, for :meth:`undo`/:meth:`redo` purposes, until a call to
        :meth:`endChangeGroup`.
        """
        del self.__doneList[self.__doneIndex + 1:]
        
        self.__inGroup    = True
        self.__doneIndex += 1
        self.__doneList.append([])

        log.debug('Starting change group - merging subsequent '
                  'changes at index {} of {}'.format(self.__doneIndex,
                                                     len(self.__doneList)))

        
    def endChangeGroup(self):
        """Ends a change group previously started by a call to
        :meth:`startChangeGroup`.
        """
        self.__inGroup = False
        log.debug('Ending change group at {} of {}'.format(
            self.__doneIndex, len(self.__doneList))) 


    def undo(self):
        """Un-does the most recent change. """
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
        """Re-does the most recent undone change. """
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
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes.

        Discards the current :class:`Selection` instance, if there is one.
        If the newly selected overlay is an :class:`.Image` instance, a
        new ``Selection`` instance is created.
        """
        overlay = self.__displayCtx.getSelectedOverlay()

        # TODO You should cull any *Change instances that
        # refer to overlays which no longer exist

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
        """Called when the current :attr:`.Selection.selection` changes.

        Saves a record of the change with a :class:`SelectionChange` object.
        """

        old, new, offset = self.__selection.getLastChange()
        
        change = SelectionChange(self.__currentOverlay, offset, old, new)
        self.__changeMade(change)

        
    def __changeMade(self, change):
        """Called by the :meth:`fillSelection` and :meth:`__selectionChanged`
        methods, whenever a data/selection change is made.

        Saves the change, and updates the :attr:`canUndo`/:attr:`canRedo`
        properties.
        """

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
        """Called by the :meth:`fillSelection`  and :meth:`redo` methods.

        Applies the given ``change`` (either a :class:`ValueChange` or a
        :class:`SelectionChange`).
        """

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
        """Called by the :meth:`undo` method. Reverses the change made by the
        given ``change`` object, (either a :class:`ValueChange` or a
        :class:`SelectionChange`)
        """

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
