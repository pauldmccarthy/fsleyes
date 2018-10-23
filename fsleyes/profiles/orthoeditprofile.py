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

import fsl.data.image               as fslimage
import fsl.utils.idle               as idle
import fsleyes_props                as props
import fsleyes.displaycontext       as fsldisplay
import fsleyes.actions              as actions
import fsleyes.actions.copyoverlay  as copyoverlay
import fsleyes.editor.editor        as fsleditor
import fsleyes.gl.routines          as glroutines
import fsleyes.gl.annotations       as annotations
from . import                          orthoviewprofile


log = logging.getLogger(__name__)


class OrthoEditProfile(orthoviewprofile.OrthoViewProfile):
    """The ``OrthoEditProfile`` class is an interaction profile for use with
    the :class:`.OrthoPanel` class. It gives the user the ability to make
    changes to :class:`.Image` overlays, by using the functionality of the
    :mod:`~fsleyes.editor` package.


    **Modes**


    The ``OrthoEditProfile`` has the following modes, in addition to those
    already defined by the :class:`.OrthoViewProfile`:

    =========== ===============================================================
    ``sel``     Select mode. The user is able to manually add voxels to the
                selection using a *cursor*. The cursor size can be changed
                with the :attr:`selectionSize` property, and the cursor can be
                toggled between a 2D square and a 3D cube via the
                :attr:`selectionIs3D` property. If the :attr:`drawMode`
                property is ``True``, selected voxels are immediately filled
                with the :attr:`fillValue` when the mouse is released.

    ``desel``   Deselect mode. Identical to ``sel`` mode, except that the
                cursor is used to remove voxels from the selection. If the
                :attr:`drawMode` property is ``True``, selected voxels are
                immediately set to 0 when the mouse is released.

    ``chsize``  Change-size mode. The use can change the :attr:`selectionSize`
                attribute via the mouse wheel.

    ``selint``  Select by intensity mode. The user can select a voxel, and
                grow the selected region based on its intensity.

    ``fill``    Fill mode. The user can click on a voxel and set its
                selected state, and the state of adjacent voxels. Restricted
                to 2D (see :attr:`selectionIs3D`).

    ``chthres`` Change-threshold mode. The user can change the
                :attr:`intensityThres` via the mouse wheel.

    ``chrad``   Change-radius mode. The user can change the
                :attr:`searchRadius` via the mouse wheel.
    =========== ===============================================================


    **Actions**


    The ``OrthoEditProfile`` defines the following actions, on top of those
    already defined by the :class:`.OrthoViewProfile`:

    .. autosummary::
       :nosignatures:

       undo
       redo
       clearSelection
       fillSelection
       invertSelection
       eraseSelection
       copySelection
       pasteSelection


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
    *scaled voxel* (a.k.a. ``pixdim``) space.  The :class:`.OrthoEditToolBar`
    uses a :class:`.DisplaySpaceWarning` widget to warn the user if the
    :attr:`.DisplayContext.displaySpace` is not set appropriately.
    """


    selectionCursorColour = props.Colour(default=(1, 1, 0, 0.7))
    """Colour used for the cursor annotation. """


    selectionOverlayColour = props.Colour(default=(1, 0.25, 1, 0.4))
    """Colour used for the selection annotation, which displays the voxels
    that are currently selected.
    """


    locationFollowsMouse = props.Boolean(deafult=True)
    """If ``True``, when the user is drawing/erasing/selectiong by clicking and
    dragging with the mouse, the :attr:`.DisplayContext.location` is updated to
    track the mouse.

    Users running on a slower machine may wish to disable this option.
    """


    showSelection = props.Boolean(default=True)
    """When :attr:`drawMode` is ``False,` the selection overlay can be hidden
    by setting this to ``False``.
    """


    selectionSize = props.Int(minval=1, maxval=100, default=3, clamped=True)
    """In ``sel`` and ``desel`` modes, defines the size of the selection
    cursor.
    """


    selectionIs3D = props.Boolean(default=False)
    """In ``sel`` and ``desel`` mode, toggles the cursor between a 2D square
    and a 3D cube. In ``selint`` mode, toggles the selection space between the
    current slice, and the full 3D volume.
    """


    fillValue = props.Real(default=1, clamped=True)
    """The value used when drawing/filling voxel values - all voxels in the
    selection will be filled with this value.
    """


    eraseValue = props.Real(default=0, clamped=True)
    """The value used when erasing voxel values - all voxels in the
    selection will be filled with this value.
    """


    drawMode = props.Boolean(default=True)
    """If ``True``, when in ``sel`` or ``desel`` mode, clicks and click+
    drags cause the image to be immediately modified. Otherwise, editing
    is a two stage process (as described in the :class:`.Editor` class
    documentation).

    This setting is enabled by default, because it causes FSLeyes to behave
    like FSLView. However, all advanced editing/selection capabilities are
    disabled when ``drawMode`` is ``True``.
    """


    intensityThres = props.Real(
        minval=0.0, maxval=1.0, default=0, clamped=False)
    """In ``selint`` mode, the maximum distance, in intensity, that a voxel
    can be from the seed location, in order for it to be selected.
    Passed as the ``precision`` argument to the
    :meth:`.Selection.selectByValue` method.
    """


    intensityThresLimit = props.Real(minval=0.0, default=0, clamped=True)
    """This setting controls the maximum value for the :attr:`itensityThres`
    property. It is set automatically from the data when an :class:`.Image`
    is first selected, but can also be manually controlled via this property.
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


    searchRadius = props.Real(
        minval=0.01, maxval=200, default=0.0, clamped=False)
    """In ``selint`` mode, if :attr:`limitToRadius` is true, this property
    specifies the search sphere radius. Passed as the ``searchRadius``
    argument to the :meth:`.Selection.selectByValue` method.
    """


    targetImage = props.Choice()
    """By default, all modifications that the user makes will be made on the
    currently selected overlay (the :attr:`.DisplayContext.selectedOverlay`).
    However, this property  can be used to select a different image as the
    target for modifications.

    This proprty is mostly useful when in ``selint`` mode - the selection
    can be made based on the voxel intensities in the currently selected
    image, but the selection can be filled in another iamge (e.g. a
    mask/label image).

    This property is updated whenever the :class:`.OverlayList` or the
    currently selected overlay changes, so that it contains all other
    overlays which have the same dimensions as the selected overlay.
    """


    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create an ``OrthoEditProfile``.

        :arg viewPanel:   The :class:`.OrthoPanel` instance.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        """

        # The currently selected overlay -
        # the overlay being edited.
        self.__currentOverlay = None

        # The 'clipboard' is created by
        # the copySelection method - it
        # contains a numpy array which
        # was copied from another overlay.
        # The clipboard source refers to
        # the overlay that the clipboard
        # was copied from.
        self.__clipboard       = None
        self.__clipboardSource = None

        # An Editor instance is created for each
        # Image overlay (on demand, as they are
        # selected), and kept in this dictionary
        # (which contains {Image : Editor} mappings).
        self.__editors = {}

        # Ref to each canvas on the ortho panel
        self.__xcanvas = viewPanel.getXCanvas()
        self.__ycanvas = viewPanel.getYCanvas()
        self.__zcanvas = viewPanel.getZCanvas()

        # The current selection is shown on each
        # canvas - a ref to the SelectionAnnotation
        # is kept here
        self.__xselAnnotation = None
        self.__yselAnnotation = None
        self.__zselAnnotation = None

        # When in draw/select/deselect/selint
        # modes, a Rect annotation is shown
        # on the canvases at the current mouse
        # location.
        self.__xcurAnnotation = None
        self.__ycurAnnotation = None
        self.__zcurAnnotation = None

        # A few performance optimisations are made
        # when in selint mode and limitToRadius is
        # active - the __record/__getSelectionMerger
        # methods populate these fields.
        self.__mergeMode   = None
        self.__mergeBlock  = None
        self.__merge3D     = None
        self.__mergeRadius = None

        # If the view panel performance is not
        # set to maximum, set the initial
        # locationFollowsMouse value to False
        perf = viewPanel.sceneOpts.performance
        self.locationFollowsMouse = perf == 3

        # These property values are cached
        # on a per-overlay basis. When an
        # overlay is re-selected, its values
        # are restored from the cache.
        self.__cache = props.PropCache(
            self,
            ['targetImage',
             'intensityThres',
             'intensityThresLimit',
             'searchRadius'],
            self.currentOverlay,
            [(overlayList, 'overlays'),
             (displayCtx,  'selectedOverlay')])

        orthoviewprofile.OrthoViewProfile.__init__(
            self,
            viewPanel,
            overlayList,
            displayCtx,
            ['sel', 'desel', 'chsize', 'selint',
             'fill', 'chthres', 'chrad'])

        self.mode = 'nav'

        displayCtx .addListener('selectedOverlay',
                                self.name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)

        self.addListener('targetImage',
                         self.name,
                         self.__targetImageChanged)
        self.addListener('mode',
                         self.name,
                         self.__modeChanged)
        self.addListener('drawMode',
                         self.name,
                         self.__drawModeChanged)
        self.addListener('selectionOverlayColour',
                         self.name,
                         self.__selectionColoursChanged)
        self.addListener('selectionCursorColour',
                         self.name,
                         self.__selectionColoursChanged)
        self.addListener('showSelection',
                         self.name,
                         self.__showSelectionChanged)
        self.addListener('intensityThresLimit',
                         self.name,
                         self.__selintThresLimitChanged)
        self.addListener('intensityThres',
                         self.name,
                         self.__selintPropertyChanged)
        self.addListener('searchRadius',
                         self.name,
                         self.__selintPropertyChanged)
        self.addListener('localFill',
                         self.name,
                         self.__selintPropertyChanged)
        self.addListener('limitToRadius',
                         self.name,
                         self.__selintPropertyChanged)

        self.__selectedOverlayChanged()
        self.__drawModeChanged()


    def destroy(self):
        """Removes some property listeners, destroys the :class:`.Editor`
        instances, and calls :meth:`.OrthoViewProfile.destroy`.
        """

        self.displayCtx .removeListener('selectedOverlay', self.name)
        self.overlayList.removeListener('overlays',        self.name)

        for editor in self.__editors.values():
            editor.destroy()

        self.__destroyAnnotations()

        self.__editors         = None
        self.__xcanvas         = None
        self.__ycanvas         = None
        self.__zcanvas         = None
        self.__xselAnnotation  = None
        self.__yselAnnotation  = None
        self.__zselAnnotation  = None
        self.__xcurAnnotation  = None
        self.__ycurAnnotation  = None
        self.__zcurAnnotation  = None
        self.__currentOverlay  = None
        self.__clipboard       = None
        self.__clipboardSource = None
        self.__cache           = None

        orthoviewprofile.OrthoViewProfile.destroy(self)


    def deregister(self):
        """Destroys all :mod:`.annotations`, and calls
        :meth:`.OrthoViewProfile.deregister`.
        """

        self.__destroyAnnotations()
        orthoviewprofile.OrthoViewProfile.deregister(self)


    def __destroyAnnotations(self):
        """Called by other methods. Destroys the :class:`.SelectionAnnotation`
        and :class:`.Rect` cursor annotation objects, if they exist.
        """

        xannot = self.__xcanvas.getAnnotations()
        yannot = self.__ycanvas.getAnnotations()
        zannot = self.__zcanvas.getAnnotations()

        annots = [(self.__xselAnnotation, xannot),
                  (self.__xcurAnnotation, xannot),
                  (self.__yselAnnotation, yannot),
                  (self.__ycurAnnotation, yannot),
                  (self.__zselAnnotation, zannot),
                  (self.__zcurAnnotation, zannot)]

        for annotObj, annotMgr in annots:
            if annotObj is not None:
                annotMgr.dequeue(annotObj, hold=True)
                annotObj.destroy()

        self.__xselAnnotation = None
        self.__yselAnnotation = None
        self.__zselAnnotation = None
        self.__xcurAnnotation = None
        self.__ycurAnnotation = None
        self.__zcurAnnotation = None


    def currentOverlay(self):
        """Returns the overlay that is currently registered with this
        ``OrthoEditProfile``.
        """
        return self.__currentOverlay


    def editor(self, overlay):
        """Return the :class:`.Editor` associated with the given overlay.
        Raises a :exc:`KeyError` if there is no editor fo the overlay.
        """
        return self.__editors[overlay]


    @actions.action
    def createMask(self):
        """Create a 3D mask which has the same size as the currently selected
        overlay, and insert it into the overlay list.
        """
        if self.__currentOverlay is None:
            return

        overlay = self.__currentOverlay
        editor  = self.__editors[overlay]
        display = self.displayCtx.getDisplay(overlay)
        name    = '{}_mask'.format(display.name)
        data    = editor.getSelection().getSelection()
        data    = np.array(data, dtype=overlay.dtype)
        mask    = copyoverlay.copyImage(self.overlayList,
                                        self.displayCtx,
                                        self.__currentOverlay,
                                        createMask=True,
                                        copy4D=False,
                                        copyDisplay=False,
                                        name=name,
                                        data=data)
        self.displayCtx.selectOverlay(mask)


    @actions.action
    def clearSelection(self):
        """Clears the current selection. See :meth:`.Editor.clearSelection`.
        """

        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        editor.getSelection().clearSelection()

        self.__refreshCanvases()


    @actions.action
    def fillSelection(self):
        """Fills the current selection with the :attr:`fillValue`. See
        :meth:`.Editor.fillSelection`.
        """
        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        if self.targetImage is not None:
            editor = self.__getTargetImageEditor(editor)

        # TODO  You could get the bounded selection from
        # fillSelection, and pass it to clearSelection
        editor.startChangeGroup()
        editor.fillSelection(self.fillValue)
        editor.clearSelection()
        editor.endChangeGroup()


    @actions.action
    def invertSelection(self):
        """Inverts the current selection. See :meth:`.Editor.invertSelection`.
        """
        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        if self.targetImage is not None:
            editor = self.__getTargetImageEditor(editor)

        editor.startChangeGroup()
        editor.invertSelection()
        editor.endChangeGroup()


    @actions.action
    def eraseSelection(self):
        """Fills the current selection with zero. See
        :meth:`.Editor.fillSelection`.
        """
        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        if self.targetImage is not None:
            editor = self.__getTargetImageEditor(editor)

        # See TODO in fillSaelection
        editor.startChangeGroup()
        editor.fillSelection(self.eraseValue)
        editor.clearSelection()
        editor.endChangeGroup()


    @actions.action
    def copySelection(self):
        """Copies the data within the selection from the currently selected
        overlay, and stores it in an internal "clipboard".
        """

        overlay = self.__currentOverlay

        if overlay is None:
            return

        editor = self.__editors[overlay]

        self.__clipboard       = editor.copySelection()
        self.__clipboardSource = overlay

        self.__setCopyPasteState()


    @actions.action
    def pasteSelection(self):
        """Pastes the data currently stored in the clipboard into the currently
        selected image, if possible.
        """

        if self.__currentOverlay is None:
            return

        overlay         = self.__currentOverlay
        clipboard       = self.__clipboard
        clipboardSource = self.__clipboardSource

        if     overlay   is None:                  return
        if     clipboard is None:                  return
        if not clipboardSource.sameSpace(overlay): return

        editor = self.__editors[overlay]

        if self.targetImage is not None:
            editor = self.__getTargetImageEditor(editor)

        editor.startChangeGroup()
        editor.pasteSelection(clipboard)
        editor.clearSelection()
        editor.endChangeGroup()


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
        with editor.getSelection().skipAll():
            change = editor.undo()

        if any([isinstance(c, fsleditor.SelectionChange) for c in change]):
            if not self.__xselAnnotation.destroyed():
                self.__xselAnnotation.texture.refresh()

        self.__refreshCanvases()


    @actions.action
    def redo(self):
        """Re-does the most recent undone change to the selection or to the
        :class:`.Image` data. See :meth:`.Editor.redo`.
        """

        if self.__currentOverlay is None:
            return

        editor = self.__editors[self.__currentOverlay]

        with editor.getSelection().skipAll():
            change = editor.redo()

        if any([isinstance(c, fsleditor.SelectionChange) for c in change]):
            if not self.__xselAnnotation.destroyed():
                self.__xselAnnotation.texture.refresh()

        self.__refreshCanvases()


    def isEditable(self, overlay):
        """Returns ``True`` if the given overlay is editable, ``False``
        otherwise.
        """

        # will raise if overlay is
        # None, or has been removed
        try:
            display = self.displayCtx.getDisplay(overlay)
        except (ValueError, fsldisplay.InvalidOverlayError) as e:
            display = None

        # Edit mode is only supported on
        # images with the 'volume', 'mask'
        # or 'label' types
        return overlay is not None                 and \
               isinstance(overlay, fslimage.Image) and \
               display.overlayType in ('volume', 'mask', 'label')


    def __modeChanged(self, *a):
        """Called when the :attr:`.Profile.mode` changes. If the mode is
        changed to ``'fill'``, the :attr:`selectionIs3D` option is set to
        ``False``.
        """

        if self.mode == 'fill':
            self.selectionIs3D = False


    def __drawModeChanged(self, *a):
        """Called when the :attr:`drawMode` changes. Updates the enabled
        state of various actions that are irrelevant when in draw mode.
        """

        # The only possible profile modes when
        # drawMode==True are sel/desel/fill.
        if self.drawMode and self.mode not in ('nav', 'sel', 'desel', 'fill'):
            self.mode = 'sel'

        if self.drawMode: self.getProp('mode').disableChoice('selint', self)
        else:             self.getProp('mode').enableChoice( 'selint', self)

        self.clearSelection .enabled = not self.drawMode
        self.fillSelection  .enabled = not self.drawMode
        self.eraseSelection .enabled = not self.drawMode
        self.invertSelection.enabled = not self.drawMode

        with props.skip(self, 'showSelection', self.name):
            self.showSelection = True

        self.__updateTargetImage()
        self.__setCopyPasteState()

        if self.__currentOverlay is not None:
            editor = self.__editors[self.__currentOverlay]
            editor.getSelection().clearSelection()
            self.__refreshCanvases()


    def __setCopyPasteState(self):
        """Enables/disables the :meth:`copySelection`/ :meth:`pasteSelection`
        actions as needed.
        """

        overlay   = self.__currentOverlay
        clipboard = self.__clipboard
        source    = self.__clipboardSource

        enableCopy  = (not self.drawMode)     and \
                      (overlay is not None)

        enablePaste =  enableCopy             and \
                      (clipboard is not None) and \
                      (overlay.sameSpace(source))

        self.copySelection .enabled = enableCopy
        self.pasteSelection.enabled = enablePaste


    def __selectionColoursChanged(self, *a):
        """Called when either of the :attr:`selectionOverlayColour` or
        :attr:`selectionCursorColour` properties change.

        Updates the  :mod:`.annotations` colours accordingly.
        """
        if self.__xselAnnotation is None:
            return

        self.__xselAnnotation.colour = self.selectionOverlayColour
        self.__yselAnnotation.colour = self.selectionOverlayColour
        self.__zselAnnotation.colour = self.selectionOverlayColour


    def __showSelectionChanged(self, *a):
        """Called when the :attr:`showSelection` property changes. Shows/
        hides the :class:`.VoxelSelection` annotations accordingly.
        """
        if self.__xselAnnotation is None:
            return

        self.__xselAnnotation.enabled = self.showSelection
        self.__yselAnnotation.enabled = self.showSelection
        self.__zselAnnotation.enabled = self.showSelection
        self.__refreshCanvases()


    def __updateTargetImage(self):
        """Resets the value and choices on the :attr:`targetImage`.
        It is populated with all :class:`.Image` instances which are in the
        same space as the currently selected overlay.
        """

        with props.suppress(self, 'targetImage'):
            self.targetImage = None

        overlay = self.__currentOverlay

        if overlay is None:
            return

        compatibleOverlays = [None]
        if not self.drawMode:
            for ovl in self.overlayList:
                if ovl is not overlay   and \
                   self.isEditable(ovl) and \
                   overlay.sameSpace(ovl):
                    compatibleOverlays.append(ovl)

        self.getProp('targetImage').setChoices(compatibleOverlays,
                                               instance=self)


    def __getTargetImageEditor(self, srcEditor):
        """If the :attr:`targetImage` is set to an image other than the
        currently selected one, this method returns an :class:`.Editor`
        for the target image.
        """

        if self.targetImage is None:
            return srcEditor

        tgtEditor = self.__editors[self.targetImage]
        srcSel    = srcEditor.getSelection()
        tgtSel    = tgtEditor.getSelection()

        tgtSel.setSelection(srcSel.getSelection(), (0, 0, 0))
        srcSel.clearSelection()

        return tgtEditor


    def __targetImageChanged(self, *a):
        """Called every time the :attr:`targetImage` is changed. Makes sure
        that an :class:`.Editor` instance for the selected target image exists.
        """

        image = self.targetImage

        if image is None: image = self.__currentOverlay
        if image is None: return

        editor = self.__editors.get(image, None)

        if editor is None:
            editor = fsleditor.Editor(image,
                                      self.overlayList,
                                      self.displayCtx)
            self.__editors[image] = editor


    def __setPropertyLimits(self):
        """Called by the :meth:`__selectedOverlayChanged` method.
        """

        overlay = self.__currentOverlay
        if overlay is None:
            # TODO Set to defaults? Probably
            #      not necessary
            return

        # If the image data is of an integer
        # type, we set limits on the fill/
        # erase values, so the user can't
        # enter an out-of-bounds value.
        if issubclass(overlay.dtype.type, np.integer):
            dmin = np.iinfo(overlay.dtype).min
            dmax = np.iinfo(overlay.dtype).max
        else:
            dmin = None
            dmax = None

        self.setAttribute('fillValue',  'minval', dmin)
        self.setAttribute('fillValue',  'maxval', dmax)
        self.setAttribute('eraseValue', 'minval', dmin)
        self.setAttribute('eraseValue', 'maxval', dmax)

        # Retrieve cached values. The cached
        # targetImage is set in the
        # __selecteDOverlayChanged method.
        thres  = self.__cache.get(overlay, 'intensityThres',      None)
        limit  = self.__cache.get(overlay, 'intensityThresLimit', None)
        radius = self.__cache.get(overlay, 'searchRadius',        None)

        # Set sensible initial values
        if limit is None or limit == 0:
            dmin, dmax = overlay.dataRange
            limit      = (dmax - dmin) / 2.0

        if thres is None: thres = 0
        else:             thres = min(thres, limit)

        # Set (what I think to be) a sensible
        # upper limit for the search radius.
        # This is just for slider widgets -
        # the seacrhRadius is unclamped, so
        # the user can manually enter any
        # value in spin boxes.
        dimSizes    = np.array(overlay.pixdim[:3]) * overlay.shape[:3]
        radiusLimit = max(dimSizes) / 4.0
        if radius is None or radius == 0:
            radius = radiusLimit / 4.0

        # Initialise property values, or
        # restore them from the cache.
        with props.skip(self, 'searchRadius', self.name):
            self.setAttribute('searchRadius', 'maxval', radiusLimit)
            self.searchRadius = radius

        with props.skip(self, 'intensityThres', self.name):
            self.setAttribute('intensityThres', 'maxval', limit)
            self.intensityThres = thres

        with props.skip(self, 'intensityThresLimit', self.name):
            self.intensityThresLimit = limit


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

        oldOverlay = self.__currentOverlay
        overlay    = self.displayCtx.getSelectedOverlay()

        # If the selected overlay hasn't changed,
        # we don't need to do anything
        if overlay == oldOverlay:
            self.__updateTargetImage()
            return

        # Destroy all existing canvas annotations
        self.__destroyAnnotations()

        # Remove property listeners from the
        # editor/selection instances associated
        # with the previously selected overlay
        if oldOverlay is not None:
            editor = self.__editors[oldOverlay]

            log.debug('De-registering listeners from Editor {} ({})'.format(
                id(editor), oldOverlay.name))
            self.undo.unbindProps('enabled', editor.undo)
            self.redo.unbindProps('enabled', editor.redo)

        # Make sure that the newly
        # selected overlay is editable
        if self.isEditable(overlay):
            self.__currentOverlay = overlay
        else:
            self.__currentOverlay = None

        # Update the limits/options
        # on all properties.
        self.__updateTargetImage()
        self.__setPropertyLimits()
        self.__setCopyPasteState()

        # If there is no selected overlay,
        # don't do anything more.
        if self.__currentOverlay is None:
            return

        # Update the limits/options on all properties.
        self.__setPropertyLimits()
        self.__setCopyPasteState()

        # Load the editor for the overlay (create
        # one if necessary), and add listeners to
        # some editor/selection properties
        editor = self.__editors.get(overlay, None)

        if editor is None:
            editor = fsleditor.Editor(overlay,
                                      self.overlayList,
                                      self.displayCtx)
            self.__editors[overlay] = editor

        # Transfer or clear the selection
        # for the old overlay.
        if oldOverlay is not None:

            oldSel = self.__editors[oldOverlay].getSelection()

            # Currently we only transfer
            # the selection for images
            # with the same dimensions/space
            if oldOverlay.sameSpace(overlay):

                log.debug('Transferring selection from {} to {}'.format(
                    oldOverlay.name,
                    overlay.name))

                newSel = editor.getSelection()
                newSel.setSelection(oldSel.getSelection(), (0, 0, 0))
            else:
                oldSel.clearSelection()

        # Restore the targetImage for this
        # overlay, if there is a cached value
        targetImage = self.__cache.get(overlay, 'targetImage', None)
        if targetImage not in self.overlayList:
            targetImage = None

        with props.skip(self, 'targetImage', self.name):
            self.targetImage = targetImage

        # Register property listeners with the
        # new Editor and Selection instances.
        log.debug('Registering listeners with Editor {} ({})'.format(
            id(editor),
            self.__currentOverlay.name))

        # Bind undo/redo action enabled states
        self.undo.bindProps('enabled', editor.undo)
        self.redo.bindProps('enabled', editor.redo)

        # Create a selection annotation and
        # a cursor annotation for each canvas
        sels         = []
        curs         = []
        cursorKwargs = {'colour'  : self.selectionCursorColour,
                        'width'   : 2,
                        'expiry'  : 0.5,
                        'enabled' : False}

        opts = self.displayCtx.getOpts(overlay)

        for c in [self.__xcanvas, self.__ycanvas, self.__zcanvas]:

            sels.append(annotations.VoxelSelection(
                c.getAnnotations(),
                editor.getSelection(),
                opts,
                colour=self.selectionOverlayColour))

            curs.append(annotations.Rect(
                c.getAnnotations(),
                (0, 0), 0, 0,
                **cursorKwargs))

        self.__xselAnnotation = sels[0]
        self.__yselAnnotation = sels[1]
        self.__zselAnnotation = sels[2]
        self.__xcurAnnotation = curs[0]
        self.__ycurAnnotation = curs[1]
        self.__zcurAnnotation = curs[2]

        xannot = self.__xcanvas.getAnnotations()
        yannot = self.__ycanvas.getAnnotations()
        zannot = self.__zcanvas.getAnnotations()

        xannot.obj(self.__xselAnnotation, hold=True)
        xannot.obj(self.__xcurAnnotation, hold=True)
        yannot.obj(self.__yselAnnotation, hold=True)
        yannot.obj(self.__ycurAnnotation, hold=True)
        zannot.obj(self.__zselAnnotation, hold=True)
        zannot.obj(self.__zcurAnnotation, hold=True)

        self.__refreshCanvases()


    def __getVoxelLocation(self, canvasPos):
        """Returns the voxel location, for the currently selected overlay,
        which corresponds to the specified canvas position. Returns ``None``
        if the current canvas position is out of bounds for the current
        overlay.
        """

        if self.__currentOverlay is None:
            return None

        opts = self.displayCtx.getOpts(self.__currentOverlay)
        return opts.getVoxel(canvasPos)


    def __hideCursorAnnotation(self):
        """Configures all of the :class:`.Rect` cursor annotations so that
        they will not be shown on the next canvas refresh.
        """
        xcur = self.__xcurAnnotation
        ycur = self.__ycurAnnotation
        zcur = self.__zcurAnnotation

        if xcur is not None: xcur.enabled = False
        if ycur is not None: ycur.enabled = False
        if zcur is not None: zcur.enabled = False


    def __drawCursorAnnotation(self, canvas, voxel, blockSize=None):
        """Draws the cursor annotation. Highlights the specified voxel with a
        :class:`~fsleyes.gl.annotations.Rect` annotation.

        This is used by mouse motion event handlers, so the user can
        see the possible selection, and thus what would happen if they
        were to click.

        :arg canvas:    The :class:`.SliceCanvas` on which to make the
                        annotation.
        :arg voxel:     Voxel which is at the centre of the cursor.
        :arg blockSize: Size of the cursor square/cube.
        """

        overlay  = self.__currentOverlay
        dopts    = self.displayCtx.getOpts(overlay)
        canvases = [self.__xcanvas,
                    self.__ycanvas,
                    self.__zcanvas]
        cursors  = [self.__xcurAnnotation,
                    self.__ycurAnnotation,
                    self.__zcurAnnotation]

        # If the selected overlay is changed, this
        # method might get called during the overlay
        # changeover (in __selectedOverlayChanged,
        # when the display space warning dialog gets
        # shown). At this point in time, the cursor
        # annotations for the new overlay will not
        # yet have been created, so we can't draw
        # them.
        if any([c is None for c in cursors]):
            return

        # If a block size was not specified,
        # it defaults to selectionSize
        if blockSize is None:
            blockSize = self.selectionSize

        # We need to specify the block
        # size in scaled voxels along
        # each voxel dimension. So we
        # scale the block size by the
        # shortest voxel axis - we're
        # aiming for a square (if 2D)
        # or a cube (if 3D) selection.
        blockSize = np.min(overlay.pixdim) * blockSize
        blockSize = [blockSize] * 3

        # Limit to the current plane
        # if in 2D selection mode
        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (canvas.opts.xax, canvas.opts.yax)

        # Calculate a box in the voxel coordinate
        # system, centred at the current voxel,
        # and of the specified block size
        corners = glroutines.voxelBox(voxel,
                                      overlay.shape,
                                      overlay.pixdim,
                                      blockSize,
                                      axes=axes,
                                      bias='high')

        if corners is None:
            self.__hideCursorAnnotation()
            return

        # We want the selection to follow voxel
        # edges, but the transformCoords method
        # will map voxel coordinates to the
        # displayed voxel centre. So we offset
        # by -0.5 to get the corners.
        corners = dopts.transformCoords(corners - 0.5, 'voxel', 'display')

        cmin = corners.min(axis=0)
        cmax = corners.max(axis=0)

        for cur, can in zip(cursors, canvases):
            copts = can.opts
            xax   = copts.xax
            yax   = copts.yax
            zax   = copts.zax

            if copts.pos[zax] < cmin[zax] or copts.pos[zax] > cmax[zax]:
                cur.w = 0
                cur.h = 0
                continue

            cur.xy = cmin[[xax, yax]]
            cur.w  = cmax[xax] - cmin[xax]
            cur.h  = cmax[yax] - cmin[yax]

        # Only draw the cursor on the current
        # canvas if locFolMouse is false
        for cur, can in zip(cursors, canvases):
            cur.resetExpiry()
            cur.enabled = can is canvas or self.locationFollowsMouse


    def __refreshCanvases(self):
        """Short cut to refresh the canvases of the :class:`.OrthoPanel`.

        .. note:: This is done instead of calling ``OrthoPanel.Refresh``
                  because the latter introduces flickering.
        """
        self.__xcanvas.Refresh()
        self.__ycanvas.Refresh()
        self.__zcanvas.Refresh()


    def __dynamicRefreshCanvases(self,
                                 ev,
                                 canvas,
                                 mousePos=None,
                                 canvasPos=None):
        """Called by mouse event handlers when the user is interacting with
        a canvas.

        If :attr:`locationFollowsMouse` is ``True``, the
        :attr:`.DisplayContext.location` is set to the current mouse location.
        """

        # If the given location is already
        # equal to the display location,
        # calling _navModeLeftMouseDrag we
        # will not trigger a refresh, so
        # we will force the refresh instead.
        forceRefresh = (
            canvasPos is not None and
            np.all(np.isclose(canvasPos, self.displayCtx.location.xyz)))

        # If locationFollowsMouse==True, we make
        # the canvas location track the edit cursor
        # location, so that the other two canvases
        # update to display the current cursor location.
        if self.locationFollowsMouse and \
           (mousePos  is not None)   and \
           (canvasPos is not None):

            self._navModeLeftMouseDrag(ev, canvas, mousePos, canvasPos)

            if forceRefresh:
                for c in self.getEventTargets():
                    c.Refresh()

        # Otherwise just update the canvas
        # that triggered the event
        else:
            canvas.Refresh()


    def __applySelection(self,
                         canvas,
                         voxel,
                         add=True,
                         combine=False,
                         from_=None):
        """Called by ``sel`` mode mouse handlers. Adds/removes a block
        of voxels, centred at the specified voxel, to/from the current
        :class:`.Selection`.

        :arg canvas:  The source :class:`.SliceCanvas`.

        :arg voxel:   Coordinates of centre voxel.

        :arg add:     If ``True`` a block is added to the selection,
                      otherwise it is removed.

        :arg combine: Tell the :class:`.Selection` object to combine this
                      change with the most recent one.

        :arg from_:   If provided, use the :meth:`.Selection.selectLine`
                      or :meth:`.Selection.deselectLine` methods - should
                      be another voxel coordinate.
        """

        opts = canvas.opts

        if self.selectionIs3D: axes = (0, 1, 2)
        else:                  axes = (opts.xax, opts.yax)

        overlay   = self.__currentOverlay
        editor    = self.__editors[overlay]
        selection = editor.getSelection()
        blockSize = self.selectionSize * np.min(overlay.pixdim)

        if from_ is not None:

            args = (from_, voxel, blockSize, axes, 'high', combine)

            if add: block, offset = selection.selectLine(  *args)
            else:   block, offset = selection.deselectLine(*args)

        else:

            block, offset = glroutines.voxelBlock(
                voxel,
                overlay.shape,
                overlay.pixdim,
                blockSize,
                axes=axes,
                bias='high')

            if add: selection.addToSelection(     block, offset, combine)
            else:   selection.removeFromSelection(block, offset, combine)

        if add: self.__recordSelectionMerger('sel',   offset, block.shape)
        else:   self.__recordSelectionMerger('desel', offset, block.shape)


    def __recordSelectionMerger(self, mode, offset, size):
        """This method is called whenever a change is made to the
        :class:`.Selection` object. It stores some information which is used
        to improve subsequent selection performance when in ``selint`` mode,
        and when :attr:`limitToRadius` is ``True``.


        Basically, if the current selection is limited by radius, and a new,
        similarly limited selection is made, we do not need to clear the
        entire selection before making the new selection - we just need to
        clear the cuboid region in which the previous selection was located.


        This behaviour is referred to as a 'merge' because, ultimately, the
        region of the first selection is merged with the region of the second
        selection, and only this part of the ``Selection`` image is refreshed.


        This method (and the :meth:`__getSelectionMerger` method) contains some
        simple, but awkward, logic which figures out when a merge can happen
        and, conversely, when the full selection does need to be cleared.


        :arg offset: Offset into the selection array of the change.
        :arg size:   Shape of the change.
        """

        # If the user has manually selected anything,
        # we can't merge
        if self.__mergeMode == 'sel':
            return

        self.__mergeMode   = mode
        self.__merge3D     = self.selectionIs3D
        self.__mergeRadius = self.limitToRadius

        # We only care about merging
        # selint+radius blocks
        if mode == 'selint' and self.__mergeRadius:
            self.__mergeBlock  = offset, size


    def __getSelectionMerger(self):
        """This method is called just before a select-by-intensity selection
        is about to happen. It rteturns one of three values:

          - The string ``'clear'``, indicating that the whole selection (or
            the whole slice, if :attr:`selectionIs3D` is ``False``) needs to
            be cleared.

          - The value ``None`` indicating that the selection does not need to
            be cleared, and a merge does not need to be made.

          - A tuple containing the ``(offset, size)`` of a previous change
            to the selection, specifying the portion of the selection which
            needs to be cleared, and which can be subsequently merged with
            a new selection.
        """

        try:
            # If not limiting by radius, the new
            # selectByValue call will clobber the
            # old selection, so we don't need to
            # merge or clear it.
            if not self.limitToRadius:
                return None

            # If the user was selecting voxels,
            # we don't know where those selected
            # voxels are, so we have to clear
            # the full selection.
            if self.__mergeMode == 'sel':
                return 'clear'

            # If the user was just deselecting,
            # we can merge the old block
            if self.__mergeMode == 'desel':
                return self.__mergeBlock

            # If the user was in 2D, but is now
            # in 3D, we have to clear the whole
            # selection. Similarly, if the user
            # was not limiting by radius, but
            # now is, we have to clear.
            if (not self.__merge3D)     and self.selectionIs3D: return 'clear'
            if (not self.__mergeRadius) and self.limitToRadius: return 'clear'

            # Otherwise we can merge the old
            # selection with the new selection.
            return self.__mergeBlock

        finally:
            self.__mergeMode   = None
            self.__merge3D     = None
            self.__mergeRadius = None
            self.__mergeBlock  = None


    def _selModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse motion events in ``sel`` mode.

        Draws a cursor annotation at the current mouse location
        (see :meth:`__draweCursorAnnotation`).
        """
        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__drawCursorAnnotation(canvas, voxel)
            self.__dynamicRefreshCanvases(ev,  canvas)

        return voxel is not None


    def _selModeLeftMouseDown(self,
                              ev,
                              canvas,
                              mousePos,
                              canvasPos,
                              add=True,
                              mode='sel'):
        """Handles mouse down events in ``sel`` mode.

        Starts an :class:`.Editor` change group, and adds to the current
        :class:`Selection`.

        This method is also used by :meth:`_deselModeLeftMouseDown`, which
        may set the ``add`` parameter to ``False``.

        :arg add:  If ``True`` (default) a block at the cursor is added to the
                   selection. Otherwise it is removed.

        :arg mode: The current profile mode (defaults to ``'sel'``).
        """
        if self.__currentOverlay is None:
            return False

        # We clear the Selection object's most
        # recent saved change - all additions
        # to the selection during this click+drag
        # event are merged together (by using
        # the combine flag to addToSelection -
        # see __applySelection). Then, if we are
        # in immediate draw mode, on the
        # up event, we know what part of the
        # selection needs to be refreshed.
        selection = self.__editors[self.__currentOverlay].getSelection()
        selection.setChange(None, None)

        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__applySelection(      canvas, voxel, add=add, combine=True)
            self.__drawCursorAnnotation(canvas, voxel)
            self.__dynamicRefreshCanvases(ev,  canvas, mousePos, canvasPos)

        return voxel is not None


    def _selModeLeftMouseDrag(self,
                              ev,
                              canvas,
                              mousePos,
                              canvasPos,
                              add=True,
                              mode='sel'):
        """Handles mouse drag events in ``sel`` mode.

        Adds to the current :class:`Selection`.

        This method is also used by :meth:`_deselModeLeftMouseDown`, which
        may set the ``add`` parameter to ``False``.

        :arg add:  If ``True`` (default) a block at the cursor is added to the
                   selection. Otherwise it is removed.

        :arg mode: The current profile mode (defaults to ``'sel'``).
        """
        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:

            lastPos = self.getLastMouseLocation()[1]
            lastPos = self.__getVoxelLocation(lastPos)

            self.__applySelection(      canvas,
                                        voxel,
                                        add=add,
                                        combine=True,
                                        from_=lastPos)
            self.__drawCursorAnnotation(canvas, voxel)
            self.__dynamicRefreshCanvases(ev,  canvas, mousePos, canvasPos)

        return voxel is not None


    def _selModeLeftMouseUp(
            self, ev, canvas, mousePos, canvasPos, fillValue=None):
        """Handles mouse up events in ``sel`` mode.

        Ends the :class:`.Editor` change group that was started in the
        :meth:`_selModeLeftMouseDown` method.

        This method is also used by :meth:`_deselModeLeftMouseUp`, which
        sets ``fillValue`` to :attr:`eraseValue`.

        :arg fillValue: If :attr:`drawMode` is ``True``, the value to
                        fill the selection with. If not provided, defaults
                        to :attr:`fillValue`.
        """

        if self.__currentOverlay is None:
            return False

        editor    = self.__editors[self.__currentOverlay]
        selection = editor.getSelection()

        # Immediate draw mode - fill
        # and clear the selection.
        if self.drawMode:

            if fillValue is None:
                fillValue = self.fillValue

            editor.fillSelection(fillValue)

            # The Selection object contains the
            # full extent of the changes that
            # were made to the selection during
            # this click+drag event. We only need
            # to clear this part of the selection.
            old, new, off = selection.getLastChange()
            restrict      = [slice(o, o + s) for o, s in zip(off, new.shape)]

            selection.clearSelection(restrict=restrict)

        self.__refreshCanvases()

        return True


    def _selModeMouseLeave(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse leave events in ``sel`` mode. Makes sure that the
        selection cursor annotation is not shown on any canvas.
        """

        self.__hideCursorAnnotation()
        self.__dynamicRefreshCanvases(ev, canvas)


    def _deselModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``desel`` mode.

        Calls :meth:`_selModeLeftMouseDown`.
        """
        self._selModeLeftMouseDown(ev,
                                   canvas,
                                   mousePos,
                                   canvasPos,
                                   add=self.drawMode,
                                   mode='desel')


    def _deselModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse drag events in ``desel`` mode.

        Calls :meth:`_selModeLeftMouseDrag`.
        """
        self._selModeLeftMouseDrag(ev,
                                   canvas,
                                   mousePos,
                                   canvasPos,
                                   add=self.drawMode,
                                   mode='desel')


    def _deselModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``desel`` mode.

        Calls :meth:`_selModeLeftMouseUp`.
        """
        self._selModeLeftMouseUp(
            ev, canvas, mousePos, canvasPos, fillValue=self.eraseValue)


    def _chsizeModeMouseWheel(self, ev, canvas, wheelDir, mousePos, canvasPos):
        """Handles mouse wheel events in ``chsize`` mode.

        Increases/decreases the current :attr:`selectionSize`.
        """

        if   wheelDir > 0: self.selectionSize += 1
        elif wheelDir < 0: self.selectionSize -= 1

        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is None:
            return False

        # See comment in OrthoViewProfile._zoomModeMouseWheel
        # about timeout
        def update():
            self.__drawCursorAnnotation(canvas, voxel)
            self.__dynamicRefreshCanvases(ev, canvas)

        idle.idle(update, timeout=0.1)

        return True


    def __selintPropertyChanged(self, *a):
        """Called when the :attr:`intensityThres`, :attr:`localFill`,
        :attr:`limitToRadius`, or :attr:`searchRadius` properties change.
        Re-runs select-by-intensity (via :meth:`__selintSelect`), with
        the new settings.
        """

        if self.__currentOverlay is None:
            return

        # If the last mouse up was not
        # select-by-intensity, don't
        # adjust the selection
        if self.getLastMouseUpHandler()[0] != 'selint':
            return

        mousePos, canvasPos = self.getLastMouseUpLocation()
        canvas              = self.getLastCanvas()

        if mousePos is None or canvas is None:
            return

        voxel = self.__getVoxelLocation(canvasPos)

        def update():
            self.__selintSelect(voxel, canvas)
            self.__refreshCanvases()

        if voxel is not None:

            # Asynchronously update the select-by-intensity
            # selection - we do it async, and with a time out,
            # so we don't queue loads of redundant jobs while
            # the user is e.g. dragging the intensityThres
            # slider real fast.
            idle.idle(update, timeout=0.1)


    def __selintThresLimitChanged(self, *a):
        """Called when the :attr:`intensityThresLimit` changes. Updates the
        maximum value on the :attr:`intensityThres` accordingly.
        """
        self.setAttribute('intensityThres',
                          'maxval',
                          self.intensityThresLimit)


    def __selintSelect(self, voxel, canvas):
        """Selects voxels by intensity, using the specified ``voxel`` as
        the seed location.

        Called by the :meth:`_selintModeLeftMouseDown`,
        :meth:`_selintModeLeftMouseDrag`,
        :meth:`_selintModeLeftMouseWheel`, and :meth:`__selintPropertyChanged`
        methods.  See :meth:`.Selection.selectByValue`.
        """

        overlay = self.__currentOverlay

        if overlay is None:
            return False

        editor = self.__editors[self.__currentOverlay]

        # The searchRadius/intensityThres
        # properties are unclamped, so we
        # have to make sure that they have
        # valid values.
        if self.searchRadius   > 0: searchRadius   = self.searchRadius
        else:                       searchRadius   = 0
        if self.intensityThres > 0: intensityThres = self.intensityThres
        else:                       intensityThres = 0

        if not self.limitToRadius:
            searchRadius = None
        else:
            searchRadius = (searchRadius / overlay.pixdim[0],
                            searchRadius / overlay.pixdim[1],
                            searchRadius / overlay.pixdim[2])

        if self.selectionIs3D:
            restrict = None
        else:
            zax           = canvas.opts.zax
            restrict      = [slice(None, None, None) for i in range(3)]
            restrict[zax] = slice(voxel[zax], voxel[zax] + 1)

        # We may need to manually clear part or all
        # of the selection before running the select
        # by value routine. The get/recordSelectionMerger
        # methods take care of the logic needed to
        # figure out what we need to do.
        selection = editor.getSelection()
        merge     = self.__getSelectionMerger()

        # The whole selection/slice needs clearing.
        # We suppress any notification by the Selection
        # object at this point - notification will
        # happen via the selectByValue method call below.
        if merge == 'clear':
            with selection.skipAll():
                selection.clearSelection(restrict=restrict)

        # We only need to clear a region
        # within the selection
        elif merge is not None:

            # Note that we are telling the
            # selectByValuem method below
            # 'combine' any previous selection
            # change with the new one, This
            # means that the entire selection
            # image is going to be replaced
            with selection.skipAll():

                # If we're in 2D mode, we just clear
                # the whole slice, as it should be fast
                # enough.
                if not self.selectionIs3D:

                    selection.clearSelection(restrict=restrict)

                # Otherwise we just clear the region
                else:
                    off, size  = merge
                    clearBlock = [slice(o, o + s) for o, s in zip(off, size)]

                    selection.clearSelection(restrict=clearBlock)

        # The 'combine' flag tells the selection object
        # to merge the last change (the clearSelection
        # call above) with the new change, so that the
        # Selection.getLastChange method will return
        # the union of those two regions.
        #
        # This is important, because the SelectionTexture
        # object, which is listening to changes on the
        # Selection object, will only need to update that
        # part of the GL texture.
        selected, offset = selection.selectByValue(
            voxel,
            precision=intensityThres,
            searchRadius=searchRadius,
            local=self.localFill,
            restrict=restrict,
            combine=merge is not None)

        self.__recordSelectionMerger('selint', offset, selected.shape)

        return True


    def _selintModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse motion events in ``selint`` mode. Draws a selection
        annotation at the current location (see
        :meth:`__drawCursorAnnotation`).
        """
        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__drawCursorAnnotation(canvas, voxel, 1)
            self.__dynamicRefreshCanvases(ev,  canvas)

        return voxel is not None


    def _selintModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``selint`` mode.

        Starts an :class:`.Editor` change group, then clears the current
        selection, and selects voxels by intensity (see
        :meth:`__selintSelect`).
        """

        if self.__currentOverlay is None:
            return False

        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__selintSelect(voxel, canvas)
            self.__dynamicRefreshCanvases(ev, canvas, mousePos, canvasPos)

        return voxel is not None


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
            self.__dynamicRefreshCanvases(*refreshArgs)

        return voxel is not None


    def _selintModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse up events in ``selint`` mode. Ends the :class:`.Editor`
        change group that was started in the :meth:`_selintModeLeftMouseDown`
        method.
        """
        if self.__currentOverlay is None:
            return False

        self.__refreshCanvases()

        return True


    def _selintModeMouseLeave(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse leave events in ``selint`` mode. Makes sure that
        the selection cursor annotation is not shown on any canvas.
        """
        self.__hideCursorAnnotation()
        self.__dynamicRefreshCanvases(ev, canvas)


    def _fillModeMouseMove(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse motion events in ``fill`` mode. Draws a selection
        annotation at the current location (see
        :meth:`__drawCursorAnnotation`).
        """
        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is not None:
            self.__drawCursorAnnotation(canvas, voxel, 1)
            self.__dynamicRefreshCanvases(ev,  canvas)

        return voxel is not None


    def _fillModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """Handles mouse down events in ``fill`` mode. Calls
        :meth:`.Selection.invertRegion` at the current location.
        """

        if self.__currentOverlay is None:
            return False

        voxel = self.__getVoxelLocation(canvasPos)

        if voxel is None:
            return False

        zax           = canvas.opts.zax
        restrict      = [slice(None, None, None) for i in range(3)]
        restrict[zax] = slice(voxel[zax], voxel[zax] + 1)
        editor        = self.__editors[self.__currentOverlay]
        selection     = editor.getSelection()

        # draw mode - works in essentially the
        # same manner as select-by-intensity,
        # but we use a threshold of 0.5
        # (intended for binary masks), and
        # immediately fill the selected region.
        if self.drawMode:
            editor.startChangeGroup()
            selected, offset = selection.selectByValue(
                voxel,
                precision=0.5,
                local=True,
                restrict=restrict)
            editor.fillSelection(self.fillValue)
            selection.clearSelection(restrict=restrict)
            editor.endChangeGroup()

        # select mode - we invert the select
        # state of the clicked-on region.
        else:
            selection.invertRegion(voxel, restrict=restrict)

        self.__dynamicRefreshCanvases(ev, canvas, mousePos, canvasPos)

        return True


    def _chthresModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        """Handles mouse wheel events in ``chthres`` mode.

        The :attr:`intensityThres` value is decreased/increased according to
        the mouse wheel direction. If the mouse button is down,
        select-by-intensity is re-run at the current mouse location.
        """
        overlay   = self.displayCtx.getSelectedOverlay()
        dataRange = overlay.dataRange[1] - overlay.dataRange[0]
        step      = 0.01 * dataRange

        if   wheel > 0: offset =  step
        elif wheel < 0: offset = -step
        else:           return False

        self.intensityThres += offset

        return True


    def _chradModeMouseWheel(self, ev, canvas, wheel, mousePos, canvasPos):
        """Handles mouse wheel events in ``chrad`` mode.

        The :attr:`searchRadius` value is decreased/increased according
        to the mouse wheel direction. If the mouse button is down,
        select-by-intensity is re-run at the current mouse location.
        """

        if   wheel > 0: offset =  2.5
        elif wheel < 0: offset = -2.5
        else:           return False

        self.searchRadius += offset

        return True
