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

import collections.abc as abc

import numpy as np

import fsleyes.actions    as actions
from . import                selection


log = logging.getLogger(__name__)


class Editor(actions.ActionProvider):
    """The ``Editor`` class provides functionality to edit the data of an
    :class:`.Image` overlay. An ``Editor`` instance is associated with a
    specific ``Image`` overlay, passed to :meth:`__init__`.


    An ``Editor`` instance uses a :class:`.selection.Selection` object which
    allows voxel selections to be made, and keeps track of all changes to both
    the selection and image data.


    **The editing process**


    Making changes to the data in an :class:`.Image` involves two steps:

     1. Create a selection

     2. Change the value of voxels in that selection


    The first step can be peformed by working directly with the ``Selection``
    object - this is accessible via the :meth:`getSelection` method. The
    :meth:`fillSelection` method can be used to perform the second step.


    Some convenience methods are also provided for working with selections:

    .. autosummary::
       :nosignatures:

       getSelection
       fillSelection
       copySelection
       pasteSelection


    **Change tracking**


    An ``Editor`` instance keeps track of all changes made to the
    :class:`Image` data and to the ``Selection``  Every selection/data
    change made is recorded using :class:`SelectionChange` and
    :class:`.ValueChange` instances, which are stored in a list. These changes
    can be undone (and redone), through the :meth:`undo` and :meth:`redo`
    "action" methods (see the :mod:`.actions` module). Changes to the
    ``Selection`` object are, by default, only recorded when the selection is
    cleared. However, you can track *all* selection changes by initialising
    an ``Editor`` instance with ``recordSelection=True``.


    Sometimes it is useful to treat many small changes as a single large
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


    def __init__(self,
                 image,
                 overlayList,
                 displayCtx,
                 recordSelection=False):
        """Create an ``Editor``.

        :arg image:           The :class:`.Image` instance being edited.

        :arg overlayList:     The :class:`.OverlayList` instance.

        :arg displayCtx:      The :class:`.DisplayContext` instance.

        :arg recordSelection: Defaults to ``False``. If ``True``, changes to
                              the :class:`.selection.Selection` are recorded
                              in the change history.
        """

        actions.ActionProvider.__init__(self, overlayList, displayCtx)

        self.__name      = '{}_{}'.format(self.__class__.__name__, id(self))
        self.__image     = image
        self.__selection = selection.Selection(
            image, displayCtx.getDisplay(image))

        if recordSelection:
            self.__selection.register(self.__name, self.__selectionChanged)

        # A list of state objects, providing
        # records of what has been done. The
        # doneIndex points to the current
        # state. Everything before the doneIndex
        # represents previous states, and
        # everything after the doneIndex
        # represents states which have been
        # undone.
        self.__doneList        = []
        self.__doneIndex       = -1
        self.__inGroup         = False
        self.__recordChanges   = True
        self.__recordSelection = recordSelection
        self.undo.enabled      = False
        self.redo.enabled      = False

        log.debug('{}.init ({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message."""
        if log:
            log.debug('{}.del ({})'.format(type(self).__name__, id(self)))


    def destroy(self):
        """Removes some property listeners, and clears references to objects
        to prevent memory leaks.
        """
        actions.ActionProvider.destroy(self)
        self.__selection.deregister(self.__name)
        self.__image     = None
        self.__selection = None
        self.__doneList  = None


    def getImage(self):
        """Returns the :class:`~fsl.data.image.Image` associated with this
        ``Editor``.
        """
        return self.__image


    def getSelection(self):
        """Returns the :class:`.selection.Selection` instance currently in use.
        """
        return self.__selection


    def clearSelection(self, *args, **kwargs):
        """Clears the :class:`.selection.Selection` (see
        :meth:`.selection.Selection.clearSelection`). If this ``Editor`` is
        not recording all selection changes (``recordSelection=False`` in
        :meth:`__init__`), the selection state before being cleared is saved
        in the change history.

        All arguments are passed through to :meth:`.Selection.clearSelection`.
        """
        self.__selection.clearSelection(*args, **kwargs)

        if (not self.__recordSelection) and self.__recordChanges:

            old, new, offset = self.__selection.getLastChange()

            # getLastChange will return None
            # if there is no last change
            if old is not None:
                change = SelectionChange(self.__image, offset, old, new)
                self.__changeMade(change)


    def invertSelection(self):
        """Inverts the current selection. """

        image    = self.__image
        sel      = self.__selection.getSelection()
        inverted = np.array(sel == 0, dtype=np.uint8)

        change = SelectionChange(image, (0, 0, 0), sel, inverted)

        self.__applyChange(change)
        self.__changeMade( change)


    def fillSelection(self, newVals):
        """Fills the current selection with the specified value or values.

        :arg newVals: A scalar value, or a sequence containing the same
                      number of values as the current selection size.
        """

        image               = self.__image
        opts                = self.displayCtx.getOpts(image)
        selectBlock, offset = self.__selection.getBoundedSelection()

        if not isinstance(newVals, abc.Sequence):
            nv = np.zeros(selectBlock.shape, dtype=np.float32)
            nv.fill(newVals)
            newVals = nv
        else:
            newVals = np.array(newVals)

        xlo, ylo, zlo = offset
        xhi = xlo + selectBlock.shape[0]
        yhi = ylo + selectBlock.shape[1]
        zhi = zlo + selectBlock.shape[2]

        slc     = opts.index((slice(xlo, xhi),
                              slice(ylo, yhi),
                              slice(zlo, zhi)))
        oldVals = image[slc]

        selectBlock = selectBlock == 0
        newVals[selectBlock] = oldVals[selectBlock]

        oldVals = np.array(oldVals)
        change  = ValueChange(image, opts.volume, offset, oldVals, newVals)

        self.__applyChange(change)
        self.__changeMade( change)


    def startChangeGroup(self):
        """Starts a change group. All subsequent changes will be grouped
        together, for :meth:`undo`/:meth:`redo` purposes, until a call to
        :meth:`endChangeGroup`.
        """

        if not self.__recordChanges:
            return

        del self.__doneList[self.__doneIndex + 1:]

        self.__inGroup    = True
        self.__doneIndex += 1
        self.__doneList.append([])

        log.debug('{}: starting change group - merging subsequent '
                  'changes at index {} of {}'.format(self.__image.name,
                                                     self.__doneIndex,
                                                     len(self.__doneList)))


    def endChangeGroup(self):
        """Ends a change group previously started by a call to
        :meth:`startChangeGroup`.
        """

        if not self.__recordChanges:
            return

        self.__inGroup = False
        log.debug('{}: ending change group at {} of {}'.format(
            self.__image.name,
            self.__doneIndex,
            len(self.__doneList)))


    def recordChanges(self, record=True):
        """Cause this ``Editor`` to either record or ignore any changes that
        are made to the selection or the image data until further notice.

        :arg record: If ``True``, changes are recorded. Otherwise they are
                     ignored.
        """

        self.__recordChanges = record

        if self.__recordSelection:
            self.__selection.enable(self.__name, enable=record)


    def ignoreChanges(self):
        """Cause this ``Editor`` to ignore any changes that are made to the
        selection or the image data until further notice. Call the
        :meth:`recordChanges` method to resume recording changes.
        """
        self.recordChanges(False)


    @actions.action
    def undo(self):
        """Un-does the most recent change.  Returns a list containing all
        change objects that were undone - either :class:`ValueChange` or
        :class:`SelectionChange` objects.
        """
        if self.__doneIndex == -1:
            return []

        log.debug('{}: undo change {} of {}'.format(
            self.__image.name,
            self.__doneIndex,
            len(self.__doneList)))

        change = self.__doneList[self.__doneIndex]

        if not isinstance(change, abc.Sequence):
            change = [change]

        for c in reversed(change):
            self.__revertChange(c)

        self.__doneIndex -= 1

        self.__inGroup = False
        self.redo.enabled = True
        if self.__doneIndex == -1:
            self.undo.enabled = False

        return change


    @actions.action
    def redo(self):
        """Re-does the most recent undone change.  Returns a list containing
        all change objects that were undone - either :class:`ValueChange` or
        :class:`SelectionChange` objects.
        """
        if self.__doneIndex == len(self.__doneList) - 1:
            return []

        log.debug('{}: redo change {} of {}'.format(
            self.__image.name,
            self.__doneIndex + 1,
            len(self.__doneList)))

        change = self.__doneList[self.__doneIndex + 1]

        if not isinstance(change, abc.Sequence):
            change = [change]

        for c in change:
            self.__applyChange(c)

        self.__doneIndex += 1

        self.__inGroup = False
        self.undo.enabled = True
        if self.__doneIndex == len(self.__doneList) - 1:
            self.redo.enabled = False

        return change


    def copySelection(self):
        """Copies the ``Image`` data in the current selection. Returns the
        data in a format that can be passed directly to the
        :meth:`pasteSelection` method of this, or another, ``Editor`` instance.

        .. note:: The format of the returned data might change, so I haven't
                  specified it.
        """

        image     = self.__image
        opts      = self.displayCtx.getOpts(image)
        selection = np.array(self.__selection.getSelection() > 0)
        data      = np.zeros(image.shape[:3], dtype=image.dtype)

        data[selection] = image[opts.index()][selection]

        return data, selection


    def pasteSelection(self, clipboard):
        """Pastes the data in the given ``clipboard`` into the ``Image`` that
        is managed by this ``Editor``.

        The ``clipboard`` is assumed to have been created by the
        :meth:`copySelection` method of another ``Editor`` instance which is
        managing an ``Image`` that has the same resolution and dimensions as
        the ``Image`` managed by this instance.
        """

        data, sel = clipboard
        self.__image[sel] = data[sel]


    def __selectionChanged(self, *a):
        """Called when the current :attr:`.Selection.selection` changes.

        Saves a record of the change with a :class:`SelectionChange` object.
        """

        if not self.__recordChanges:
            return

        old, new, offset = self.__selection.getLastChange()

        if old is not None:
            change = SelectionChange(self.__image, offset, old, new)
            self.__changeMade(change)


    def __changeMade(self, change):
        """Called by the :meth:`fillSelection` and :meth:`__selectionChanged`
        methods, whenever a data/selection change is made.

        Saves the change, and updates the state of the :meth:`undo`/
        :meth:`redo` methods.
        """

        if not self.__recordChanges:
            return

        if self.__inGroup:
            self.__doneList[self.__doneIndex].append(change)
        else:
            del self.__doneList[self.__doneIndex + 1:]
            self.__doneList.append(change)
            self.__doneIndex += 1

        self.undo.enabled = True
        self.redo.enabled = False

        log.debug('{}: new change to {} ({} of {})'.format(
            self.__image.name,
            change.overlay.name,
            self.__doneIndex,
            len(self.__doneList)))


    def __applyChange(self, change):
        """Called by the :meth:`fillSelection`  and :meth:`redo` methods.

        Applies the given ``change`` (either a :class:`ValueChange` or a
        :class:`SelectionChange`).
        """

        image = change.overlay
        opts  = self.displayCtx.getOpts(image)

        if isinstance(change, ValueChange):
            log.debug('%s: changing image %s data - offset '
                      '%s, volume %s, size %s',
                      self.__image.name,
                      change.overlay.name,
                      change.offset,
                      change.volume,
                      change.oldVals.shape)

            sliceobj = self.__makeSlice(change.offset,
                                        change.newVals.shape,
                                        opts.index()[3:])
            image[sliceobj] = change.newVals

        elif isinstance(change, SelectionChange):
            recording = self.__recordSelection
            if recording: self.__selection.disable(self.__name)
            self.__selection.setSelection(change.newSelection, change.offset)
            if recording: self.__selection.enable(self.__name)


    def __revertChange(self, change):
        """Called by the :meth:`undo` method. Reverses the change made by the
        given ``change`` object, (either a :class:`ValueChange` or a
        :class:`SelectionChange`)
        """

        image = change.overlay
        opts  = self.displayCtx.getOpts(image)

        if isinstance(change, ValueChange):
            log.debug('{}: reverting image {} data change - offset '
                      '{}, volume {}, size {}'.format(
                          self.__image.name,
                          change.overlay.name,
                          change.offset,
                          change.volume,
                          change.oldVals.shape))

            sliceobj = self.__makeSlice(change.offset,
                                        change.oldVals.shape,
                                        opts.index()[3:])
            image[sliceobj] = change.oldVals

        elif isinstance(change, SelectionChange):
            recording = self.__recordSelection
            if recording: self.__selection.disable(self.__name)
            self.__selection.setSelection(change.oldSelection, change.offset)
            if recording: self.__selection.enable(self.__name)


    def __makeSlice(self, offset, shape, volume=None):
        """Generate a tuple of ``slice`` objects and/or integers, suitable for
        indexing a region of an image at the given ``offset``, with the given
        ``shape``. If the image has more than three dimensions, the generated
        slice will index the specified ``volume`` (assumed to be a sequence of
        indices).
        """

        sliceobjs = []

        offset = [int(o) for o in offset]
        shape  = [int(s) for s in shape]

        for i in range(len(offset)):
            sliceobjs.append(slice(offset[i], offset[i] + shape[i], 1))

        if volume is not None:
            sliceobjs.extend(volume)

        return tuple(sliceobjs)


class ValueChange(object):
    """Represents a change which has been made to the data for an
    :class:`.Image` instance. Stores the location, the old values,
    and the new values.
    """


    def __init__(self, overlay, volume, offset, oldVals, newVals):
        """Create a ``ValueChange``.

        :arg overlay: The :class:`.Image` instance.
        :arg volume:  Sequence of volume indices, if ``overlay`` has more
                      than 3 dimensions.
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
    """Represents a change which has been made to a
    :class:`.selection.Selection` instance. Stores the location, the old
    selection, and the new selection.
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
