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

import numpy                        as np

import                                 props
import fsl.data.image               as fslimage
import fsl.fsleyes.editor.editor    as editor
import fsl.fsleyes.gl.annotations   as annotations

import orthoviewprofile


log = logging.getLogger(__name__)


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

    =========================== ============================================
    ``undo``                    Un-does the most recent action.
    ``redo``                    Re-does the most recent undone action.
    ``fillSelection``           Fills the current selection with the current
                                :attr:`fillValue`.
    ``clearSelection``          Clears the current selection.
    ``createMaskFromSelection`` Creates a mask :class:`.Image` from the
                                current selection.
    ``createROIFromSelection``  Creates a ROI :class:`.Image` from the
                                current selection.
    =========================== ============================================

    
    **Annotations**


    The ``OrthoEditProfile`` class uses :mod:`.annotations` on the
    :class:`.SliceCanvas` panels, displayed in the :class:`.OrthoPanel`,
    to display information to the user. Two annotations are used:

     - The *cursor* annotation. This is a :class:`.Rect` annotation
       representing a cursor at the voxel, or voxels, underneath the
       current mouse location.
    
     - The *selection* annotation. This is a :class:`.VoxelSelection`
       annotation which displays the :class:`.Selection`.
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

    
    fillValue = props.Real(default=0)
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

        self.__editor            = editor.Editor(overlayList, displayCtx) 
        self.__xcanvas           = viewPanel.getXCanvas()
        self.__ycanvas           = viewPanel.getYCanvas()
        self.__zcanvas           = viewPanel.getZCanvas() 
        self.__selAnnotation     = None
        self.__xCursorAnnotation = None
        self.__yCursorAnnotation = None
        self.__zCursorAnnotation = None
        self.__selecting         = False
        self.__lastDist          = None
        self.__currentOverlay    = None
        
        actions = {
            'undo'                    : self.undo,
            'redo'                    : self.redo,
            'fillSelection'           : self.fillSelection,
            'clearSelection'          : self.clearSelection,
            'createMaskFromSelection' : self.__editor.createMaskFromSelection,
            'createROIFromSelection'  : self.__editor.createROIFromSelection}

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
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__editor.addListener('canUndo',
                                  self._name,
                                  self.__undoStateChanged)
        self.__editor.addListener('canRedo',
                                  self._name,
                                  self.__undoStateChanged)

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
        instance, and calls :meth:`.OrthoViewProfile.destroy`.
        """

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.__editor    .removeListener('canUndo',         self._name)
        self.__editor    .removeListener('canRedo',         self._name)

        self.__editor.destroy()

        self.__editor = None

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

        xca = self.__xCursorAnnotation
        yca = self.__yCursorAnnotation
        zca = self.__zCursorAnnotation

        if xca is not None:
            self.__xcanvas.getAnnotations().dequeue(xca, hold=True)
        if yca is not None:
            self.__ycanvas.getAnnotations().dequeue(yca, hold=True)
        if zca is not None:
            self.__zcanvas.getAnnotations().dequeue(zca, hold=True)

        self.__selAnnotation     = None
        self.__xCursorAnnotation = None
        self.__yCursorAnnotation = None
        self.__zCursorAnnotation = None
            
        orthoviewprofile.OrthoViewProfile.deregister(self)

    
    def clearSelection(self, *a):
        """Clears the current selection. See :meth:`.Editor.clearSelection`.
        """
        self.__editor.getSelection().clearSelection()
        self._viewPanel.Refresh()


    def fillSelection(self, *a):
        """Fills the current selection with the :attr:`fillValue`. See
        :meth:`.Editor.fillSelection`.
        """
        self.__editor.fillSelection(self.fillValue)
        self.__editor.getSelection().clearSelection()


    def undo(self, *a):
        """Un-does the most recent change to the selection or to the
        :class:`.Image` data. See :meth:`.Editor.undo`.
        """

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
        self.__editor.getSelection().disableNotification('selection')
        self.__editor.undo()
        self.__editor.getSelection().enableNotification('selection')
        
        self.__selectionChanged()
        self.__selAnnotation.texture.refresh()
        self._viewPanel.Refresh()


    def redo(self, *a):
        """Re-does the most recent undone change to the selection or to the
        :class:`.Image` data. See :meth:`.Editor.redo`.
        """ 

        self.__editor.getSelection().disableNotification('selection')
        self.__editor.redo()
        self.__editor.getSelection().enableNotification('selection')
        self.__selectionChanged()
        self.__selAnnotation.texture.refresh()
        self._viewPanel.Refresh()
 

    def __undoStateChanged(self, *a):
        """Called when either of the :attr:`.Editor.canUndo` or
        :attr:`.Editor.canRedo` states change. Updates the state of the
        ``undo``/``redo`` actions accordingly.
        """
        self.enable('undo', self.__editor.canUndo)
        self.enable('redo', self.__editor.canRedo)


    def __selectionColoursChanged(self, *a):
        """Called when either of the :attr:`selectionOverlayColour` or
        :attr:`selectionCursorColour` properties change.
        
        Updates the  :mod:`.annotations` colours accordingly.
        """
        if self.__selAnnotation is not None:
            self.__selAnnotation.colour = self.selectionOverlayColour

        if self.__xCursorAnnotation is not None:
            self.__xCursorAnnotation.colour = self.selectionCursorColour
        if self.__yCursorAnnotation is not None:
            self.__yCursorAnnotation.colour = self.selectionCursorColour
        if self.__zCursorAnnotation is not None:
            self.__zCursorAnnotation.colour = self.selectionCursorColour 


    def __selectedOverlayChanged(self, *a):
        """Called when either the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` change.

        Destroys all old :mod:`.annotations`. If the newly selected overlay is
        an :class:`Image`, new annotations are created.
        """

        overlay   = self._displayCtx.getSelectedOverlay()
        selection = self.__editor.getSelection() 
        xannot    = self.__xcanvas.getAnnotations()
        yannot    = self.__ycanvas.getAnnotations()
        zannot    = self.__zcanvas.getAnnotations()        

        # If the selected overlay hasn't changed,
        # we don't need to do anything
        if overlay == self.__currentOverlay:
            return

        # If there's already an existing
        # selection object, clear it 
        if self.__selAnnotation is not None:
            xannot.dequeue(self.__selAnnotation, hold=True)
            yannot.dequeue(self.__selAnnotation, hold=True)
            zannot.dequeue(self.__selAnnotation, hold=True)
            
            self.__selAnnotation.destroy()

        xca = self.__xCursorAnnotation
        yca = self.__yCursorAnnotation
        zca = self.__zCursorAnnotation

        if xca is not None: xannot.dequeue(xca, hold=True)
        if yca is not None: yannot.dequeue(yca, hold=True)
        if zca is not None: yannot.dequeue(xca, hold=True)
            
        self.__xCursorAnnotation = None
        self.__yCursorAnnotation = None
        self.__zCursorAnnotation = None
        self.__selAnnotation     = None

        self.__currentOverlay = overlay

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
            
            self.__currentOverlay = None
            log.warn('Editing is only possible on volume '
                     'images, in ID or pixdim space.')
            return

        # Otherwise, create a selection annotation
        # and queue it on the canvases for drawing

        selection.addListener('selection', self._name, self.__selectionChanged)

        self.__selAnnotation = annotations.VoxelSelection( 
            selection,
            opts.getTransform('display', 'voxel'),
            opts.getTransform('voxel',   'display'),
            colour=self.selectionOverlayColour)

        kwargs = {'colour' : self.selectionCursorColour,
                  'width'  : 2}

        xca = annotations.Rect((0, 0), 0, 0, **kwargs)
        yca = annotations.Rect((0, 0), 0, 0, **kwargs)
        zca = annotations.Rect((0, 0), 0, 0, **kwargs)
        self.__xCursorAnnotation = xca
        self.__yCursorAnnotation = yca
        self.__zCursorAnnotation = zca
        
        xannot.obj(self.__selAnnotation,     hold=True)
        yannot.obj(self.__selAnnotation,     hold=True)
        zannot.obj(self.__selAnnotation,     hold=True)
        xannot.obj(self.__xCursorAnnotation, hold=True)
        yannot.obj(self.__yCursorAnnotation, hold=True)
        zannot.obj(self.__zCursorAnnotation, hold=True)

        self._viewPanel.Refresh()


    def __selectionChanged(self, *a):
        """Called when the :attr:`.Selection.selection` is changed.
        Toggles action enabled states depending on the size of the selection.
        """

        selection = self.__editor.getSelection()

        # TODO This is a big performance bottleneck, as
        #      it gets called on every mouse position
        #      change when mouse-dragging. The Selection
        #      object could cache its size? Or perhaps
        #      these actions could be toggled at the
        #      start/end of a mouse drag?
        selSize   = selection.getSelectionSize()

        self.enable('createMaskFromSelection', selSize > 0)
        self.enable('createROIFromSelection',  selSize > 0)
        self.enable('clearSelection',          selSize > 0)
        self.enable('fillSelection',           selSize > 0)

    
    def __getVoxelLocation(self, canvasPos):
        """Returns the voxel location, for the currently selected overlay,
        which corresponds to the specified canvas position.
        """
        
        opts  = self._displayCtx.getOpts(self.__currentOverlay)
        voxel = opts.transformCoords([canvasPos], 'display', 'voxel')[0]

        return np.int32(np.floor(voxel))


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

        opts  = self._displayCtx.getOpts(self.__currentOverlay)

        canvases = [self.__xcanvas, self.__ycanvas, self.__zcanvas]
        cursors  = [self.__xCursorAnnotation,
                    self.__yCursorAnnotation,
                    self.__zCursorAnnotation]

        # If we are running in a low
        # performance mode, the cursor
        # is only drawn on the current
        # canvas.
        if self._viewPanel.getSceneOptions().performance < 5:
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

        selection     = self.__editor.getSelection()
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
        """Handles mouse wheel events in ``sel`` mode.

        Increases/decreases the current :attr:`selectionSize`.
        """

        if   wheelDir > 0: self.selectionSize += 1
        elif wheelDir < 0: self.selectionSize -= 1

        voxel = self.__getVoxelLocation(canvasPos)
        self.__drawCursorAnnotation(canvas, voxel)
        self.__refreshCanvases(ev, canvas)


    def _selModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse motion events in ``sel`` mode.

        Draws a cursor annotation at the current mouse location
        (see :meth:`__draweCursorAnnotation`).
        """
        voxel = self.__getVoxelLocation(canvasPos)
        self.__drawCursorAnnotation(canvas, voxel)
        self.__refreshCanvases(ev,  canvas)


    def _selModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``sel`` mode.

        Starts an :class:`.Editor` change group, and adds to the current
        :class:`Selection`.
        """
        self.__editor.startChangeGroup()

        voxel = self.__getVoxelLocation(canvasPos)
        self.__applySelection(      canvas, voxel)
        self.__drawCursorAnnotation(canvas, voxel)
        self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)


    def _selModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse drag events in ``sel`` mode.

        Adds to the current :class:`Selection`.
        """        
        voxel = self.__getVoxelLocation(canvasPos)
        self.__applySelection(      canvas, voxel)
        self.__drawCursorAnnotation(canvas, voxel)
        self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)


    def _selModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``sel`` mode.

        Ends the :class:`.Editor` change group that was started in the
        :meth:`_selModeLeftMouseDown` method.
        """ 
        self.__editor.endChangeGroup()
        self._viewPanel.Refresh()


    def _selModeMouseLeave(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse leave events in ``sel`` mode. Makes sure that the
        selection cursor annotation is not shown on any canvas.
        """
        
        cursors = [self.__xCursorAnnotation,
                   self.__yCursorAnnotation,
                   self.__zCursorAnnotation]

        for cursor in cursors:
            if cursor is not None:
                cursor.w = 0
                cursor.h = 0

        self.__refreshCanvases(ev, canvas)

        
    def _deselModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``desel`` mode.

        Starts an :class:`.Editor` change group, and removes from the current
        :class:`Selection`.        
        """

        self.__editor.startChangeGroup()

        voxel = self.__getVoxelLocation(canvasPos)
        self.__applySelection(      canvas, voxel, False)
        self.__drawCursorAnnotation(canvas, voxel)
        self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)


    def _deselModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse drag events in ``desel`` mode.

        Removes from the current :class:`Selection`.        
        """ 
        voxel = self.__getVoxelLocation(canvasPos)
        self.__applySelection(      canvas, voxel, False)
        self.__drawCursorAnnotation(canvas, voxel)
        self.__refreshCanvases(ev,  canvas, mousePos, canvasPos)

        
    def _deselModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``desel`` mode.

        Ends the :class:`.Editor` change group that was started in the
        :meth:`_deselModeLeftMouseDown` method.
        """        
        self.__editor.endChangeGroup()
        self._viewPanel.Refresh()

            
    def __selintSelect(self, voxel):
        """Selects voxels by intensity, using the specified ``voxel`` as
        the seed location.

        Called by the :meth:`_selintModeLeftMouseDown`,
        :meth:`_selintModeLeftMouseDrag`, and and
        :meth:`_selintModeLeftMouseWheel` methods.  See
        :meth:`.Selection.selectByValue`.
        """
        
        overlay = self._displayCtx.getSelectedOverlay()
        
        if not self.limitToRadius or self.searchRadius == 0:
            searchRadius = None
        else:
            searchRadius = (self.searchRadius / overlay.pixdim[0],
                            self.searchRadius / overlay.pixdim[1],
                            self.searchRadius / overlay.pixdim[2])

        # If the last selection covered a bigger radius
        # than this selection, clear the whole selection 
        if self.__lastDist is None or \
           np.any(np.array(searchRadius) < self.__lastDist):
            self.__editor.getSelection().clearSelection()

        self.__editor.getSelection().selectByValue(
            voxel,
            precision=self.intensityThres,
            searchRadius=searchRadius,
            local=self.localFill)

        self.__lastDist = searchRadius

        
    def _selintModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse motion events in ``selint`` mode. Draws a selection
        annotation at the current location (see
        :meth:`__drawCursorAnnotation`).
        """
        voxel = self.__getVoxelLocation(canvasPos)
        self.__drawCursorAnnotation(canvas, voxel, 1)
        self.__refreshCanvases(ev,  canvas)

        
    def _selintModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``selint`` mode.

        Starts an :class:`.Editor` change group, then clears the current
        selection, and selects voxels by intensity (see
        :meth:`__selintSelect`).
        """

        self.__editor.startChangeGroup()
        self.__editor.getSelection().clearSelection() 
        self.__selecting = True
        self.__lastDist  = 0
        self.__selintSelect(self.__getVoxelLocation(canvasPos))
        self.__refreshCanvases(ev, canvas, mousePos, canvasPos)

        
    def _selintModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse drag events in ``selint`` mode.

        If :attr:`limitToRadius` is ``True``, the :attr:`searchRadius` is
        increased to the distance between the current mouse location, and
        the mouse down location, and a select-by-intensity is re-run with
        the same seed location (the mouse down location), and the new
        search radius.

        If ``limitToRadius`` is ``False``, a select-by-intensity is re-run
        with the current mouse location.  See the :meth:`__selintSelect`
        method.
        """ 

        if not self.limitToRadius:
            voxel = self.__getVoxelLocation(canvasPos)
            self.__drawCursorAnnotation(canvas, voxel, 1)

            refreshArgs = (ev, canvas, mousePos, canvasPos)
            
        else:
            mouseDownPos, canvasDownPos = self.getMouseDownLocation()
            voxel = self.__getVoxelLocation(
                canvasDownPos)

            cx,  cy,  cz  = canvasPos
            cdx, cdy, cdz = canvasDownPos

            dist = np.sqrt((cx - cdx) ** 2 + (cy - cdy) ** 2 + (cz - cdz) ** 2)
            self.searchRadius = dist

            refreshArgs = (ev, canvas)

        self.__selintSelect(voxel)
        self.__refreshCanvases(*refreshArgs)

        
    def _selintModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        """Handles mouse wheel events in ``selint`` mode.

        If the mouse button is down, the :attr:`intensityThres` value is
        decreased/increased according to the mouse wheel direction, and
        select-by-intensity is re-run with the mouse-down location as
        the seed location.
        """

        if not self.__selecting:
            return

        overlay = self._displayCtx.getSelectedOverlay()
        opts    = self._displayCtx.getOpts(overlay)

        dataRange = opts.dataMax - opts.dataMin
        step      = 0.01 * dataRange

        if   wheel > 0: self.intensityThres += step
        elif wheel < 0: self.intensityThres -= step

        mouseDownPos, canvasDownPos = self.getMouseDownLocation()
        voxel                       = self.__getVoxelLocation(canvasDownPos) 

        self.__selintSelect(voxel)
        self.__refreshCanvases(ev, canvas)

        
    def _selintModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``selint`` mode. Ends the :class:`.Editor`
        change group that was started in the :meth:`_selintModeLeftMouseDown`
        method.
        """
        self.__editor.endChangeGroup()
        self.__selecting = False
        self._viewPanel.Refresh()
