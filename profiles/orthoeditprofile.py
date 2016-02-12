#!/usr/bin/env python
#
# orthoeditprofile.py - The OrthoEditProfile class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`OrthoEditProfile` class, an interaction
:class:`.Profile` for :class:`.OrthoPanel` views.
"""

import logging

import wx

import numpy                        as np

import                                 props
import fsl.data.image               as fslimage
import fsl.data.strings             as strings
import fsl.utils.dialog             as fsldlg
import fsl.utils.status             as status
import fsl.fsleyes.actions          as actions
import fsl.fsleyes.editor.editor    as fsleditor
import fsl.fsleyes.gl.annotations   as annotations

import orthoviewprofile


log = logging.getLogger(__name__)



_suppressDisplaySpaceWarning = False
"""Whenever an :class:`OrthoEditProfile` is active, and the
:attr:`.DisplayContext.selectedOverlay` changes, the ``OrthoEditProfile``
changes the :attr:`.DisplayContext.displaySpace` to the newly selected
overlay. If this boolean flag is ``True``, a warning message is shown
to the user. The message dialog has a checkbox which updates this attribute,
and thus allows the user to suppress the warning in the future.
"""


class OrthoEditProfile(orthoviewprofile.OrthoViewProfile):
    """The ``OrthoEditProfile`` class is an interaction profile for use with
    the :class:`.OrthoPanel` class. It gives the user the ability to make
    changes to :class:`.Image` overlays, by using the functionality of the
    :mod:`~fsl.fsleyes.editor` package.


    **Modes**
    

    The ``OrthoEditProfile`` has the following modes, in addition to those
    already defined by the :class:`.OrthoViewProfile`:

    ========== ===============================================================
    ``sel``    Select mode. The user is able to manually add voxels to the
               selection using a *cursor*. The cursor size can be changed
               with the :attr:`selectionSize` property, and the cursor can be
               toggled between a 2D square and a 3D cube via the
               :attr:`selectionIs3D` property.
    
    ``desel``  Deselect mode. Identical to ``sel`` mode, except that the
               cursor is used to remove voxels from the selection.
    
    ``selint`` Select by intensity mode.
    ========== ===============================================================


    **Actions**
    

    The ``OrthoEditProfile`` defines the following actions, on top of those
    already defined by the :class:`.OrthoViewProfile`:

    .. autosummary::
       :nosignatures:

       undo
       redo
       fillSelection
       clearSelection
       createMaskFromSelection
       createROIFromSelection

    
    **Annotations**


    The ``OrthoEditProfile`` class uses :mod:`.annotations` on the
    :class:`.SliceCanvas` panels, displayed in the :class:`.OrthoPanel`,
    to display information to the user. Two annotations are used:

     - The *cursor* annotation. This is a :class:`.Rect` annotation
       representing a cursor at the voxel, or voxels, underneath the
       current mouse location.
    
     - The *selection* annotation. This is a :class:`.VoxelSelection`
       annotation which displays the :class:`.Selection`.


    **The display space**

    
    The ``OrthoEditProfile`` class has been written in a way which requires
    the :class:`.Image` instance that is being edited to be displayed in
    *scaled voxel* (a.k.a. ``pixdim``) space.  Therefore, when an ``Image``
    overlay is selected, the ``OrthoEditProfile`` instance sets that ``Image``
    as the current :attr:`.DisplayContext.displaySpace` reference image.
    """


    selectionCursorColour = props.Colour(default=(1, 1, 0, 0.7))
    """Colour used for the cursor annotation. """

    
    selectionOverlayColour = props.Colour(default=(1, 0, 1, 0.7))
    """Colour used for the selection annotation, which displays the voxels
    that are currently selected.
    """
    
    
    selectionSize = props.Int(minval=1, default=3, clamped=True)
    """In ``sel`` and ``desel`` modes, defines the size of the selection
    cursor.
    """

    
    selectionIs3D = props.Boolean(default=False)
    """In ``sel`` and ``desel`` mode, toggles the cursor between a 2D square
    and a 3D cube.
    """

    
    fillValue = props.Real(default=0, clamped=True)
    """The value used by the ``fillSelection`` action - all voxels in the
    selection will be filled with this value.
    """
    

    intensityThres = props.Real(minval=0.0, default=10, clamped=True)
    """In ``selint`` mode, the maximum distance, in intensity, that a voxel
    can be from the seed location, in order for it to be selected.
    Passed as the ``precision`` argument to the
    :meth:`.Selection.selectByValue` method.
    """

    
    localFill = props.Boolean(default=False)
    """In ``selint`` mode, if this property is ``True``, voxels can only be
    selected if they are adjacent to an already selected voxel. Passed as the
    ``local`` argument to the :meth:`.Selection.selectByValue` method.
    """
    

    limitToRadius = props.Boolean(default=False)
    """In ``selint`` mode, if this property is ``True``, the search region
    will be limited to a sphere (in the voxel coordinate system) with its
    radius specified by the :attr:`searchRadius` property.
    """

    
    searchRadius = props.Real(minval=0.0, default=0.0, clamped=True)
    """In ``selint`` mode, if :attr:`limitToRadius` is true, this property
    specifies the search sphere radius. Passed as the ``searchRadius``
    argument to the :meth:`.Selection.selectByValue` method.
    """

    
    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create an ``OrthoEditProfile``.

        :arg viewPanel:   The :class:`.OrthoPanel` instance.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        # An Editor instance is created for each
        # Image overlay (on demand, as they are
        # selected), and kept in this dictionary
        # (which contains {Image : Editor} mappings).
        self.__editors           = {}
        self.__xcanvas           = viewPanel.getXCanvas()
        self.__ycanvas           = viewPanel.getYCanvas()
        self.__zcanvas           = viewPanel.getZCanvas() 
        self.__selAnnotation     = None
        self.__selecting         = False
        self.__currentOverlay    = None

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            viewPanel,
            overlayList,
            displayCtx,
            ['sel', 'desel', 'selint'])

        self.mode = 'nav'

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        
        self.addListener('selectionOverlayColour',
                         self._name,
                         self.__selectionColoursChanged)
        self.addListener('selectionCursorColour',
                         self._name,
                         self.__selectionColoursChanged) 

        self.__selectedOverlayChanged()
        self.__selectionChanged()
        self.__undoStateChanged()


    def destroy(self):
        """Removes some property listeners, destroys the :class:`.Editor`
        instances, and calls :meth:`.OrthoViewProfile.destroy`.
        """

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        for editor in self.__editors.values():
            editor.removeListener('canUndo', self._name)
            editor.removeListener('canRedo', self._name)
            editor.destroy()

        if self.__selAnnotation is not None:
            self.__selAnnotaiton.destroy()
            
        self.__editors        = None
        self.__xcanvas        = None
        self.__ycanvas        = None
        self.__zcanvas        = None
        self.__selAnnotation  = None
        self.__currentOverlay = None

        orthoviewprofile.OrthoViewProfile.destroy(self)

        
    def deregister(self):
        """Destroys all :mod:`.annotations`, and calls
        :meth:`.OrthoViewProfile.deregister`.
        """
        if self.__selAnnotation is not None:
            sa = self.__selAnnotation
            self.__xcanvas.getAnnotations().dequeue(sa, hold=True)
            self.__ycanvas.getAnnotations().dequeue(sa, hold=True)
            self.__zcanvas.getAnnotations().dequeue(sa, hold=True)
            sa.destroy()

        self.__selAnnotation = None
            
        orthoviewprofile.OrthoViewProfile.deregister(self)


    @actions.action
    def clearSelection(self):
        """Clears the current selection. See :meth:`.Editor.clearSelection`.
        """
        
        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        editor.getSelection().clearSelection()
        
        self._viewPanel.Refresh()


    @actions.action
    def fillSelection(self):
        """Fills the current selection with the :attr:`fillValue`. See
        :meth:`.Editor.fillSelection`.
        """
        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]
                
        editor.fillSelection(self.fillValue)
        editor.getSelection().clearSelection()


    @actions.action
    def eraseSelection(self):
        """Fills the current selection with zero. See
        :meth:`.Editor.fillSelection`.
        """
        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]
                
        editor.fillSelection(0)
        editor.getSelection().clearSelection() 


    @actions.action
    def createMaskFromSelection(self):
        """Creates a new mask :class:`.Image` from the current selection.
        See :meth:`.Editor.createMaskFromSelection`.
        """
        if self.__currentOverlay is None:
            return

        self.__editors[self.__currentOverlay].createMaskFromSelection()


    @actions.action
    def createROIFromSelection(self):
        """Creates a new ROI :class:`.Image` from the current selection.
        See :meth:`.Editor.createROIFromSelection`.
        """ 
        if self.__currentOverlay is None:
            return

        self.__editors[self.__currentOverlay].createROIFromSelection() 


    @actions.action
    def undo(self):
        """Un-does the most recent change to the selection or to the
        :class:`.Image` data. See :meth:`.Editor.undo`.
        """

        if self.__currentOverlay is None:
            return
        
        editor = self.__editors[self.__currentOverlay]

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
        editor.getSelection().disableNotification('selection')
        editor.undo()
        editor.getSelection().enableNotification('selection')
        
        self.__selectionChanged()
        self.__selAnnotation.texture.refresh()
        self._viewPanel.Refresh()


    @actions.action
    def redo(self):
        """Re-does the most recent undone change to the selection or to the
        :class:`.Image` data. See :meth:`.Editor.redo`.
        """

        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        editor.getSelection().disableNotification('selection')
        editor.redo()
        editor.getSelection().enableNotification('selection')
        
        self.__selectionChanged()
        self.__selAnnotation.texture.refresh()
        self._viewPanel.Refresh()
 

    def __undoStateChanged(self, *a):
        """Called when either of the :attr:`.Editor.canUndo` or
        :attr:`.Editor.canRedo` states change. Updates the state of the
        ``undo``/``redo`` actions accordingly.
        """
        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        log.debug('Editor ({}) undo/redo state '
                  'changed: undo={}, redo={}'.format(
                      self.__currentOverlay.name,
                      editor.canUndo,
                      editor.canRedo))
        
        self.undo.enable = editor.canUndo
        self.redo.enable = editor.canRedo


    def __selectionColoursChanged(self, *a):
        """Called when either of the :attr:`selectionOverlayColour` or
        :attr:`selectionCursorColour` properties change.
        
        Updates the  :mod:`.annotations` colours accordingly.
        """
        if self.__selAnnotation is not None:
            self.__selAnnotation.colour = self.selectionOverlayColour


    def __setFillValueLimits(self, overlay):
        """Called by the :meth:`__selectedOverlayChanged` method. Updates the
        min/max limits of the :attr:`fillValue` property so it can only be
        set to values within the overlay data range.
        """
        
        if issubclass(overlay.data.dtype.type, np.integer):
            dmin = np.iinfo(overlay.data.dtype).min
            dmax = np.iinfo(overlay.data.dtype).max
        else:
            dmin = None
            dmax = None

        self.setConstraint('fillValue', 'minval', dmin)
        self.setConstraint('fillValue', 'maxval', dmax)


    def __selectedOverlayChanged(self, *a):
        """Called when either the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` change.

        Destroys all old :mod:`.annotations`. If the newly selected overlay is
        an :class:`Image`, new annotations are created.
        """
        # Overview:
        #  1. Destroy Editor instances associated with
        #     overlays that no longer exist
        #
        #  2. Destroy old canvas annotations
        #
        #  3. Remove property listeners on editor/selection
        #     objects associated with the previous overlay
        #
        #  4. Load/create a new Editor for the new overlay
        #
        #  5. Transfer the exsiting selection to the new
        #     overlay if possible.
        #
        #  6. Add property listeners to the editor/selection
        #
        #  7. Create canvas annotations
        #
        # Here we go....

        # Destroy any Editor instances which are associated
        # with overlays that are no longer in the overlay list
        #
        # TODO - If the current overlay has been removed,
        #        this will cause an error later on. You
        #        need to handle this scenario here.
        # 
        # for overlay, editor in self.__editors:
        #     if overlay not in self._overlayList:
        #         self.__editors.pop(overlay)
        #         editor.destroy()

        oldOverlay = self.__currentOverlay
        overlay    = self._displayCtx.getSelectedOverlay()
        
        # If the selected overlay hasn't changed,
        # we don't need to do anything
        if overlay == oldOverlay:
            return

        # Destroy all existing canvas annotations
        xannot = self.__xcanvas.getAnnotations()
        yannot = self.__ycanvas.getAnnotations()
        zannot = self.__zcanvas.getAnnotations()        

        # Clear the selection annotation
        if self.__selAnnotation is not None:
            xannot.dequeue(self.__selAnnotation, hold=True)
            yannot.dequeue(self.__selAnnotation, hold=True)
            zannot.dequeue(self.__selAnnotation, hold=True)
            
            self.__selAnnotation.destroy()
            
        self.__selAnnotation = None

        # Remove property listeners from the
        # editor/selection instances associated
        # with the previously selected overlay
        if oldOverlay is not None:
            editor = self.__editors[oldOverlay]

            log.debug('De-registering listeners from Editor {} ({})'.format(
                id(editor), oldOverlay.name))
            editor.getSelection().removeListener('selection', self._name)
            editor               .removeListener('canUndo',   self._name)
            editor               .removeListener('canRedo',   self._name)

        self.__currentOverlay = overlay

        # If there is no selected overlay (the overlay
        # list is empty), don't do anything.
        if overlay is None:
            return

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        # Update the fillValue limits
        self.__setFillValueLimits(overlay)

        # Edit mode is only supported on
        # images with the 'volume' type
        if not isinstance(overlay, fslimage.Image) or \
           display.overlayType != 'volume':
            
            self.__currentOverlay = None
            return

        # Change the display space so that the newly
        # selected image is the reference image -
        # display a message to the user, as this may
        # otherwise be confusing
        if self._displayCtx.displaySpace != overlay:

            msg = strings.messages[self, 'displaySpaceChange']
            msg = msg.format(overlay.name)

            global _suppressDisplaySpaceWarning
            if not _suppressDisplaySpaceWarning:

                cbMsg = strings.messages[self, 'displaySpaceChange.suppress']
                title = strings.titles[  self, 'displaySpaceChange']
                
                dlg   = fsldlg.CheckBoxMessageDialog(
                    self._viewPanel,
                    title=title,
                    message=msg,
                    cbMessage=cbMsg,
                    cbState=_suppressDisplaySpaceWarning,
                    icon=wx.ICON_INFORMATION)

                dlg.ShowModal()

                _suppressDisplaySpaceWarning  = dlg.CheckBoxState()

            status.update(msg) 
            self._displayCtx.displaySpace = overlay

        # Load the editor for the overlay (create
        # one if necessary), and add listeners to
        # some editor/selection properties
        editor = self.__editors.get(overlay, None)
        
        if editor is None:
            editor = fsleditor.Editor(overlay,
                                      self._overlayList,
                                      self._displayCtx)
            self.__editors[overlay] = editor

        # Transfer the existing selection
        # to the new overlay, if possible.
        #
        # Currently we only transfer
        # the selection for images
        # with the same shape.
        if oldOverlay is not None                        and \
           oldOverlay.shape[:3]     == overlay.shape[:3] and \
           np.allclose(oldOverlay.voxToWorldMat, overlay.voxToWorldMat):

            log.debug('Transferring selection from {} to {}'.format(
                oldOverlay.name,
                overlay.name))
            
            oldSelection = self.__editors[oldOverlay].getSelection()
            newSelection = editor.getSelection()

            newSelection.setSelection(oldSelection.selection, (0, 0, 0))

        # Register property listeners with the
        # new Editor and Selection instances.
        log.debug('Registering listeners with Editor {} ({})'.format(
            id(editor),
            self.__currentOverlay.name))
        
        editor.getSelection().addListener('selection',
                                          self._name,
                                          self.__selectionChanged)
        editor.addListener('canUndo', self._name, self.__undoStateChanged)
        editor.addListener('canRedo', self._name, self.__undoStateChanged)
        
        # Update undo/redo button states, and
        # selection action button states
        self.__undoStateChanged()
        self.__selectionChanged()
    
        # Create a selection annotation and
        # queue it on the canvases for drawing
        self.__selAnnotation = annotations.VoxelSelection( 
            editor.getSelection(),
            opts.getTransform('pixdim', 'voxel'),
            opts.getTransform('voxel',  'pixdim'),
            colour=self.selectionOverlayColour)

        xannot.obj(self.__selAnnotation, hold=True)
        yannot.obj(self.__selAnnotation, hold=True)
        zannot.obj(self.__selAnnotation, hold=True)

        self._viewPanel.Refresh()


    def __selectionChanged(self, *a):
        """Called when the :attr:`.Selection.selection` is changed.
        Toggles action enabled states depending on the size of the selection.
        """

        if self.__currentOverlay is None:
            return

        editor    = self.__editors[self.__currentOverlay]
        selection = editor.getSelection()

        # TODO This is a big performance bottleneck, as
        #      it gets called on every mouse position
        #      change when mouse-dragging. The Selection
        #      object could cache its size? Or perhaps
        #      these actions could be toggled at the
        #      start/end of a mouse drag?
        selSize   = selection.getSelectionSize()

        self.createMaskFromSelection.enable = selSize > 0
        self.createROIFromSelection .enable = selSize > 0
        self.clearSelection         .enable = selSize > 0
        self.fillSelection          .enable = selSize > 0

    
    def __getVoxelLocation(self, canvasPos):
        """Returns the voxel location, for the currently selected overlay,
        which corresponds to the specified canvas position. Returns ``None``
        if the current canvas position is out of bounds for the current
        overlay.
        """
        
        opts = self._displayCtx.getOpts(self.__currentOverlay)
        return opts.getVoxel(canvasPos)


    def __drawCursorAnnotation(self, canvas, voxel, blockSize=None):
        """Draws the cursor annotation. Highlights the specified voxel with a
        :class:`~fsl.fsleyes.gl.annotations.Rect` annotation.
        
        This is used by mouse motion event handlers, so the user can
        see the possible selection, and thus what would happen if they
        were to click.

        :arg canvas:    The :class:`.SliceCanvas` on which to make the
                        annotation.
        :arg voxel:     Voxel which is at the centre of the cursor.
        :arg blockSize: Size of the cursor square/cube.
        """

        opts     = self._displayCtx.getOpts(self.__currentOverlay)
        canvases = [self.__xcanvas, self.__ycanvas, self.__zcanvas]

        # Create a cursor annotation for each canvas
        kwargs  = {'colour' : self.selectionCursorColour,
                   'width'  : 2}

        cursors = [annotations.Rect((0, 0), 0, 0, **kwargs),
                   annotations.Rect((0, 0), 0, 0, **kwargs),
                   annotations.Rect((0, 0), 0, 0, **kwargs)]

        # If we are running in a low
        # performance mode, the cursor
        # is only drawn on the current
        # canvas.
        if self._viewPanel.getSceneOptions().performance < 4:
            cursors  = [cursors[canvases.index(canvas)]]
            canvases = [canvas]

        if blockSize is None:
            blockSize = self.selectionSize

        # Figure out the selection
        # boundary coordinates
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
        # by -0.5 to get the corners.
        # 
        # (Assuming here that the image is
        # displayed in id/pixdim space)
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

        # Queue the cursors
        for cursor, canvas in zip(cursors, canvases):
            canvas.getAnnotations().obj(cursor)
            

    def __applySelection(self, canvas, voxel, add=True):
        """Called by ``sel`` mode mouse handlers. Adds/removes a block
        of voxels, centred at the specified voxel, to/from the current
        :class:`.Selection`.

        :arg canvas: The source :class:`.SliceCanvas`.
        :arg voxel:  Coordinates of centre voxel.
        :arg add:    If ``True`` a block is added to the selection,
                     otherwise it is removed.
        """

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.xax, canvas.yax)

        editor        = self.__editors[self.__currentOverlay]
        selection     = editor.getSelection()
        block, offset = selection.generateBlock(voxel,
                                                self.selectionSize,
                                                selection.selection.shape,
                                                axes)

        if add: selection.addToSelection(     block, offset)
        else:   selection.removeFromSelection(block, offset)


    def __refreshCanvases(self, ev, canvas, mousePos=None, canvasPos=None):
        """Called by mouse event handlers.

        If the current :class:`.ViewPanel` performance setting (see
        :attr:`.SceneOpts.performance`) is at its maximum, all three
        :class:`.OrthoPanel` :class:`.SliceCanvas` canvases are refreshed
        on selection updates.

        On all lower performance settings, only the source canvas is updated.
        """
        perf = self._viewPanel.getSceneOptions().performance
        if perf == 4:
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
        """Handles mouse wheel events in ``sel`` mode.

        Increases/decreases the current :attr:`selectionSize`.
        """

        if   wheelDir > 0: self.selectionSize -= 1
        elif wheelDir < 0: self.selectionSize += 1

        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__drawCursorAnnotation(canvas, voxel)
            self.__refreshCanvases(ev, canvas)


    def _selModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse motion events in ``sel`` mode.

        Draws a cursor annotation at the current mouse location
        (see :meth:`__draweCursorAnnotation`).
        """
        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__drawCursorAnnotation(canvas, voxel)
            self.__refreshCanvases(ev,  canvas)


    def _selModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``sel`` mode.

        Starts an :class:`.Editor` change group, and adds to the current
        :class:`Selection`.
        """
        if self.__currentOverlay is None:
            return
        
        editor = self.__editors[self.__currentOverlay]
        voxel  = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            editor.startChangeGroup()
            self.__applySelection(      canvas, voxel)
            self.__drawCursorAnnotation(canvas, voxel)
            self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)


    def _selModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse drag events in ``sel`` mode.

        Adds to the current :class:`Selection`.
        """        
        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__applySelection(      canvas, voxel)
            self.__drawCursorAnnotation(canvas, voxel)
            self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)


    def _selModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``sel`` mode.

        Ends the :class:`.Editor` change group that was started in the
        :meth:`_selModeLeftMouseDown` method.
        """
        if self.__currentOverlay is None:
            return
        
        editor = self.__editors[self.__currentOverlay] 
        editor.endChangeGroup()
        
        self._viewPanel.Refresh()


    def _selModeMouseLeave(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse leave events in ``sel`` mode. Makes sure that the
        selection cursor annotation is not shown on any canvas.
        """
        
        self.__refreshCanvases(ev, canvas)

        
    def _deselModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``desel`` mode.

        Starts an :class:`.Editor` change group, and removes from the current
        :class:`Selection`.        
        """
        if self.__currentOverlay is None:
            return
        
        editor = self.__editors[self.__currentOverlay]
        voxel  = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            editor.startChangeGroup()
            self.__applySelection(      canvas, voxel, False)
            self.__drawCursorAnnotation(canvas, voxel)
            self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)


    def _deselModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse drag events in ``desel`` mode.

        Removes from the current :class:`Selection`.        
        """ 
        voxel = self.__getVoxelLocation(canvasPos)
        
        if voxel is not None:
            self.__applySelection(      canvas, voxel, False)
            self.__drawCursorAnnotation(canvas, voxel)
            self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)

        
    def _deselModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``desel`` mode.

        Ends the :class:`.Editor` change group that was started in the
        :meth:`_deselModeLeftMouseDown` method.
        """
        if self.__currentOverlay is None:
            return
        
        editor = self.__editors[self.__currentOverlay]
        
        editor.endChangeGroup()
        self._viewPanel.Refresh()

            
    def __selintSelect(self, voxel, canvas):
        """Selects voxels by intensity, using the specified ``voxel`` as
        the seed location.

        Called by the :meth:`_selintModeLeftMouseDown`,
        :meth:`_selintModeLeftMouseDrag`, and and
        :meth:`_selintModeLeftMouseWheel` methods.  See
        :meth:`.Selection.selectByValue`.
        """
        
        overlay = self.__currentOverlay

        if overlay is None:
            return

        editor = self.__editors[self.__currentOverlay]
        
        if not self.limitToRadius or self.searchRadius == 0:
            searchRadius = None
        else:
            searchRadius = (self.searchRadius / overlay.pixdim[0],
                            self.searchRadius / overlay.pixdim[1],
                            self.searchRadius / overlay.pixdim[2])


        if self.selectionIs3D:
            restrict = None
        else:
            zax           = canvas.zax
            restrict      = [slice(None, None, None) for i in range(3)]
            restrict[zax] = slice(voxel[zax], voxel[zax] + 1)

        # Clear the whole selection before
        # selecting voxels. This is not
        # necessary if we are not limiting
        # to a search radius, as the
        # selectByValue method will
        # replace the selection in the
        # search region (either the whole
        # image, or the current slice).
        selection = editor.getSelection()
        if searchRadius is not None:
            selection.disableNotification('selection')
            selection.clearSelection(restrict)
            selection.enableNotification('selection')

        selection.selectByValue(
            voxel,
            precision=self.intensityThres,
            searchRadius=searchRadius,
            local=self.localFill,
            restrict=restrict)

        
    def _selintModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse motion events in ``selint`` mode. Draws a selection
        annotation at the current location (see
        :meth:`__drawCursorAnnotation`).
        """
        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__drawCursorAnnotation(canvas, voxel, 1)
            self.__refreshCanvases(ev,  canvas)

        
    def _selintModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``selint`` mode.

        Starts an :class:`.Editor` change group, then clears the current
        selection, and selects voxels by intensity (see
        :meth:`__selintSelect`).
        """

        if self.__currentOverlay is None:
            return
        
        editor = self.__editors[self.__currentOverlay]
        voxel  = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            editor.startChangeGroup()

            self.__selecting = True
            self.__selintSelect(voxel, canvas)
            self.__refreshCanvases(ev, canvas, mousePos, canvasPos)

        
    def _selintModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse drag events in ``selint`` mode.

        A select-by-intensity is re-run with the current mouse location.  See
        the :meth:`__selintSelect` method.
        """ 

        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            
            refreshArgs = (ev, canvas, mousePos, canvasPos)
            
            self.__drawCursorAnnotation(canvas, voxel, 1)
            self.__selintSelect(voxel, canvas)
            self.__refreshCanvases(*refreshArgs)

        
    def _selintModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        """Handles mouse wheel events in ``selint`` mode.

        If the mouse button is down, the :attr:`intensityThres` value is
        decreased/increased according to the mouse wheel direction, and
        select-by-intensity is re-run at the current mouse location.
        """

        if not self.__selecting:
            return

        overlay = self._displayCtx.getSelectedOverlay()
        opts    = self._displayCtx.getOpts(overlay)

        dataRange = opts.dataMax - opts.dataMin
        step      = 0.01 * dataRange

        if   wheel > 0: self.intensityThres += step
        elif wheel < 0: self.intensityThres -= step

        voxel = self.__getVoxelLocation(canvasPos) 

        if voxel is not None:
            self.__selintSelect(voxel, canvas)
            self.__refreshCanvases(ev, canvas)

        
    def _selintModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``selint`` mode. Ends the :class:`.Editor`
        change group that was started in the :meth:`_selintModeLeftMouseDown`
        method.
        """
        if self.__currentOverlay is None:
            return
        
        editor = self.__editors[self.__currentOverlay] 
        
        editor.endChangeGroup()
        
        self.__selecting = False
        self._viewPanel.Refresh()
