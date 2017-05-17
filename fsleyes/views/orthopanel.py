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

import wx

import fsl.data.image                          as fslimage
import fsleyes_widgets.dialog                  as fsldlg
import fsleyes_widgets.utils.layout            as fsllayout

import fsleyes.strings                         as strings
import fsleyes.gl                              as fslgl
import fsleyes.actions                         as actions
import fsleyes.colourmaps                      as colourmaps
import fsleyes.gl.ortholabels                  as ortholabels
import fsleyes.gl.wxglslicecanvas              as slicecanvas
import fsleyes.controls.cropimagepanel         as cropimagepanel
import fsleyes.controls.edittransformpanel     as edittransformpanel
import fsleyes.controls.orthotoolbar           as orthotoolbar
import fsleyes.controls.orthoedittoolbar       as orthoedittoolbar
import fsleyes.controls.orthoeditactiontoolbar as orthoeditactiontoolbar
import fsleyes.controls.orthoeditsettingspanel as orthoeditsettingspanel
import fsleyes.displaycontext.orthoopts        as orthoopts
from . import                                     canvaspanel


log = logging.getLogger(__name__)


_suppressDisplaySpaceWarning = False
"""Sometimes the :attr:`.DisplayContext.displaySpace` must be changed to
perform certain operations (e.g. when the :meth:`toggleEditTransformPanel`
method is called). When this happens a warning message is shown to the user,
with the option to suppress future warnings. This flag keeps track of
whether the user has chosen to ignore future warnings.
"""


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


    The ``OrthoPanel`` creates an :class:`.OrthoLabels` instance, which
    manages the display of anatomical orientation labels on each of the
    three :class:`.SliceCanvas` instances.


    **Display**


    The display of an ``OrthoPanel`` can be configured through all of the
    settings provided by the :class:`.OrthoOpts` class. The ``OrthoOpts``
    instance for a given ``OrthoPanel`` can be accessed via the
    :meth:`.CanvasPanel.getSceneOptions` method.


    **Interaction**


    The following interaction profiles are defined for use with the
    ``OrthoPanel`` (see the :class:`.ViewPanel` for an overview of
    *profiles*):

    ======== =========================================================
    ``view`` Viewing/navigation, using the :class:`.OrthoViewProfile`.

    ``edit`` Simple editing of :class:`.Image` overlays, using the
             :class:`.OrthoEditProfile` (see also the
             :mod:`~fsleyes.editor` package).

    ``crop`` Allows the user to crop an ``Image`` overlay.
    ======== =========================================================


    **Actions and control panels**


    The ``OrthoPanel`` adds a few extra actions to those provided by the
    :class:`.CanvasPanel` class:

    .. autosummary::
       :nosignatures:

       toggleEditMode
       toggleCropMode
       toggleEditTransformPanel
       toggleEditPanel
       toggleOrthoToolBar
       resetDisplay
       centreCursor
       centreCursorWorld
       toggleCursor
       toggleLabels
       toggleXCanvas
       toggleYCanvas
       toggleZCanvas
    """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create an ``OrthoPanel``.

        :arg parent:      The :mod:`wx` parent.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        :arg displayCtx:  A :class:`.FSLeyesFrame` instance.
        """

        sceneOpts = orthoopts.OrthoOpts()

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         sceneOpts)

        name         = self.getName()
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

        self.__labelMgr = ortholabels.OrthoLabels(
            overlayList,
            displayCtx,
            sceneOpts,
            self.__xcanvas,
            self.__ycanvas,
            self.__zcanvas)

        # If an edit menu is added when in
        # 'edit' profile (see __profileChanged),
        # its name is stored here.
        self.__editMenuTitle = None

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

        # Callbacks for ortho panel layout options
        sceneOpts.addListener('layout',   name, self.__refreshLayout)
        sceneOpts.addListener('bgColour', name, self.__bgColourChanged)

        # Individual zoom control for each canvas
        self.__xcanvas.bindProps('zoom', sceneOpts, 'xzoom')
        self.__ycanvas.bindProps('zoom', sceneOpts, 'yzoom')
        self.__zcanvas.bindProps('zoom', sceneOpts, 'zzoom')

        self.__xcanvas.bindProps('renderMode',      sceneOpts)
        self.__ycanvas.bindProps('renderMode',      sceneOpts)
        self.__zcanvas.bindProps('renderMode',      sceneOpts)

        self.toggleCursor .bindProps('toggled', sceneOpts, 'showCursor')
        self.toggleLabels .bindProps('toggled', sceneOpts, 'showLabels')
        self.toggleXCanvas.bindProps('toggled', sceneOpts, 'showXCanvas')
        self.toggleYCanvas.bindProps('toggled', sceneOpts, 'showYCanvas')
        self.toggleZCanvas.bindProps('toggled', sceneOpts, 'showZCanvas')

        # Callbacks for overlay list/selected overlay changes
        overlayList.addListener('overlays',
                                name,
                                self.__overlayListChanged)
        displayCtx .addListener('bounds',
                                name,
                                self.__refreshLayout)
        displayCtx .addListener('displaySpace',
                                name,
                                self.__radioOrientationChanged)
        displayCtx .addListener('radioOrientation',
                                name,
                                self.__radioOrientationChanged)
        displayCtx .addListener('selectedOverlay',
                                name,
                                self.__overlayListChanged)

        # Callback for the display context location - when it
        # changes, update the displayed canvas locations
        displayCtx.addListener('location', name, self.__locationChanged)

        # Callbacks for toggling x/y/z canvas display
        sceneOpts.addListener('showXCanvas', name, self.__toggleCanvas)
        sceneOpts.addListener('showYCanvas', name, self.__toggleCanvas)
        sceneOpts.addListener('showZCanvas', name, self.__toggleCanvas)

        # Callbacks which just need to refresh
        def refresh(*a):
            self.Refresh()

        sceneOpts.addListener('labelSize',   name, refresh, weak=False)
        sceneOpts.addListener('labelColour', name, refresh, weak=False)
        sceneOpts.addListener('showLabels',  name, refresh, weak=False)

        self.addListener('profile', name, self.__profileChanged)

        # Call the __onResize method to refresh
        # the slice canvases when the canvas
        # panel is resized, so aspect ratio
        # is maintained
        contentPanel.Bind(wx.EVT_SIZE, self.__onResize)

        # Initialise the panel
        self.__radioOrientationChanged()
        self.__refreshLayout(refresh=False)
        self.__bgColourChanged(refresh=False)
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

        self._displayCtx .removeListener('location',         self._name)
        self._displayCtx .removeListener('bounds',           self._name)
        self._displayCtx .removeListener('selectedOverlay',  self._name)
        self._displayCtx .removeListener('displaySpace',     self._name)
        self._displayCtx .removeListener('radioOrientation', self._name)
        self._overlayList.removeListener('overlays',         self._name)

        self.__xcanvas.destroy()
        self.__ycanvas.destroy()
        self.__zcanvas.destroy()
        self.__labelMgr.destroy()
        self.__removeEditMenu()

        canvaspanel.CanvasPanel.destroy(self)


    @actions.toggleControlAction(orthotoolbar.OrthoToolBar)
    def toggleOrthoToolBar(self):
        """Shows/hides an :class:`.OrthoToolBar`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(orthotoolbar.OrthoToolBar, ortho=self)


    @actions.toggleControlAction(orthoedittoolbar.OrthoEditToolBar)
    def toggleEditMode(self):
        """Toggles the :attr:`.ViewPanel.profile` between ``'view'`` and
        ``'edit'``. See :meth:`__profileChanged`.
        """

        if self.profile == 'view': self.profile = 'edit'
        else:                      self.profile = 'view'


    @actions.toggleControlAction(cropimagepanel.CropImagePanel)
    def toggleCropMode(self):
        """Toggles the :attr:`.ViewPanel.profile` between ``'view'`` and
        ``'crop'``. See :meth:`__profileChanged`.
        """

        if self.profile == 'view': self.profile = 'crop'
        else:                      self.profile = 'view'


    @actions.toggleControlAction(edittransformpanel.EditTransformPanel)
    def toggleEditTransformPanel(self):
        """Shows/hides an :class:`.EditTransformPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(edittransformpanel.EditTransformPanel,
                         floatPane=True,
                         floatOnly=True,
                         closeable=False,
                         ortho=self)

        editing    = self.toggleEditTransformPanel.toggled
        displayCtx = self.getDisplayContext()
        overlay    = displayCtx.getSelectedOverlay()

        if editing and displayCtx.displaySpace != 'world':

            global _suppressDisplaySpaceWarning
            if not _suppressDisplaySpaceWarning and \
               overlay is not None:

                msg   = strings.messages[self,
                                         'toggleEditTransformPanel',
                                         'displaySpaceChange']
                hint  = strings.messages[self,
                                         'toggleEditTransformPanel',
                                         'displaySpaceChange.hint']
                msg   = msg .format(overlay.name)
                hint  = hint.format(overlay.name)
                cbMsg = strings.messages[self,
                                         'toggleEditTransformPanel',
                                         'displaySpaceChange.suppress']
                title = strings.titles[  self,
                                         'toggleEditTransformPanel',
                                         'displaySpaceChange']

                dlg   = fsldlg.CheckBoxMessageDialog(
                    self,
                    title=title,
                    message=msg,
                    cbMessages=[cbMsg],
                    cbStates=[_suppressDisplaySpaceWarning],
                    hintText=hint,
                    focus='yes',
                    icon=wx.ICON_INFORMATION)

                dlg.ShowModal()

                _suppressDisplaySpaceWarning  = dlg.CheckBoxState()

            displayCtx.displaySpace = 'world'



    @actions.toggleControlAction(orthoeditsettingspanel.OrthoEditSettingsPanel)
    def toggleEditPanel(self, floatPane=False):
        """Shows/hides an :class:`.OrthoEditSettingsPanel`. See
        :meth:`.ViewPanel.togglePanel`.
        """
        self.togglePanel(orthoeditsettingspanel.OrthoEditSettingsPanel,
                         ortho=self,
                         floatPane=floatPane)


    @actions.action
    def resetDisplay(self):
        """Calls :meth:`.OrthoViewProfile.resetDisplay`. """
        self.getCurrentProfile().resetDisplay()


    @actions.action
    def centreCursor(self):
        """Calls :meth:`.OrthoViewProfile.centreCursor`. """
        self.getCurrentProfile().centreCursor()


    @actions.action
    def centreCursorWorld(self):
        """Calls :meth:`.OrthoViewProfile.centreCursorWorld`. """
        self.getCurrentProfile().centreCursorWorld()


    @actions.toggleAction
    def toggleCursor(self):
        """Toggles the value of :attr:`.SceneOpts.showCursor`. """
        # The state of this action gets bound to
        # the showCursor attribute in __init__
        pass


    @actions.toggleAction
    def toggleLabels(self):
        """Toggles the value of :attr:`.OrthoOpts.showLabels`. """
        # The state of this action gets bound to
        # the showLabels attribute in __init__
        pass


    @actions.toggleAction
    def toggleXCanvas(self):
        """Toggles the value of :attr:`.OrthoOpts.showXCanvas`. """
        # The state of this action gets bound to
        # the showXCanvas attribute in __init__
        pass


    @actions.toggleAction
    def toggleYCanvas(self):
        """Toggles the value of :attr:`.OrthoOpts.showYCanvas`. """
        # The state of this action gets bound to
        # the showYCanvas attribute in __init__
        pass


    @actions.toggleAction
    def toggleZCanvas(self):
        """Toggles the value of :attr:`.OrthoOpts.showZCanvas`. """
        # The state of this action gets bound to
        # the showZCanvas attribute in __init__
        pass


    def getActions(self):
        """Overrides :meth:`.ActionProvider.getActions`. Returns all of the
        :mod:`.actions` that are defined on this ``OrthoPanel``.
        """
        actionz = [self.screenshot,
                   self.showCommandLineArgs,
                   self.applyCommandLineArgs,
                   None,
                   self.toggleMovieMode,
                   self.toggleDisplaySync,
                   self.toggleEditMode,
                   (strings.titles[self, 'toolMenu'], [
                       self.toggleCropMode,
                       self.toggleEditTransformPanel]),
                   None,
                   self.resetDisplay,
                   self.centreCursor,
                   self.centreCursorWorld,
                   None,
                   self.toggleLabels,
                   self.toggleCursor,
                   self.toggleXCanvas,
                   self.toggleYCanvas,
                   self.toggleZCanvas,
                   None,
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
                   self.toggleClassificationPanel,
                   self.removeAllPanels]

        def makeTuples(actionz):

            tuples = []

            for a in actionz:
                if isinstance(a, actions.Action):
                    tuples.append((a.__name__, a))

                elif isinstance(a, tuple):
                    tuples.append((a[0], makeTuples(a[1])))

                elif a is None:
                    tuples.append((None, None))

            return tuples

        return makeTuples(actionz)


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


    def __profileChanged(self, *a):
        """Called when the :attr:`.ViewPanel.profile` changes. If ``'edit'``
        mode has been enabled, :class:`.OrthEditToolBar` and
        :class:`.OrthEditActionToolBar` toolbars are added as control panels,
        and an "edit" menu is added to the :class:`.FSLeyesFrame` (if there
        is one).
        """

        CropImagePanel         = cropimagepanel.CropImagePanel
        OrthoEditToolBar       = orthoedittoolbar.OrthoEditToolBar
        OrthoEditActionToolBar = orthoeditactiontoolbar.OrthoEditActionToolBar
        OrthoEditSettingsPanel = orthoeditsettingspanel.OrthoEditSettingsPanel

        cropPanelOpen          = self.isPanelOpen(CropImagePanel)
        editToolBarOpen        = self.isPanelOpen(OrthoEditToolBar)
        editActionToolBarOpen  = self.isPanelOpen(OrthoEditActionToolBar)
        editPanelOpen          = self.isPanelOpen(OrthoEditSettingsPanel)

        inEdit                 = self.profile == 'edit'
        inCrop                 = self.profile == 'crop'

        # Toggle toolbars if they are open but should
        # be closed, or closed but should be open
        if (not editToolBarOpen) and      inEdit or \
                editToolBarOpen  and (not inEdit):
            self.togglePanel(orthoedittoolbar.OrthoEditToolBar, ortho=self)

        if (not editActionToolBarOpen) and      inEdit or \
                editActionToolBarOpen  and (not inEdit):
            self.togglePanel(orthoeditactiontoolbar.OrthoEditActionToolBar,
                             ortho=self,
                             location=wx.LEFT)

        if (not cropPanelOpen) and      inCrop or \
                cropPanelOpen  and (not inCrop):
            self.togglePanel(cropimagepanel.CropImagePanel,
                             ortho=self,
                             floatPane=True,
                             floatOnly=True,
                             closeable=False,
                             floatPos=(0.85, 0.3))

        # Don't open edit panel by default,
        # but close it when we leave edit mode
        if editPanelOpen and (not inEdit):
            self.togglePanel(orthoeditsettingspanel.OrthoEditSettingsPanel)

        # It's unlikely, but an OrthoPanel might be
        # created without a ref to a FSLeyesFrame.
        if self.getFrame() is not None:
            if inEdit: self.__addEditMenu()
            else:      self.__removeEditMenu()


    def __addEditMenu(self):
        """Called by :meth:`__profleChanged` when the
        :attr:`.ViewPanel.profile` is changed to ``'edit'``. Adds a
        menu to the :class:`.FSLeyesFrame`.
        """

        frame    = self.getFrame()
        menuName = strings.labels[self, 'editMenu']
        menuName = menuName.format(self.getFrame().getViewPanelID(self))
        menuBar  = frame.GetMenuBar()
        profile  = self.getCurrentProfile()
        idx      = menuBar.FindMenu(menuName)

        if  idx == wx.NOT_FOUND: editMenu = None
        else:                    editMenu = menuBar.GetMenu(idx)

        if editMenu is not None:
            return

        self.__editMenuTitle = menuName

        editMenu = wx.Menu()

        menuBar.Append(editMenu, menuName)

        actionz = ['undo',
                   'redo',
                   'createMask',
                   'clearSelection',
                   'fillSelection',
                   'eraseSelection',
                   'copySelection',
                   'pasteSelection']

        frame.populateMenu(editMenu,
                           profile,
                           actionz,
                           ignoreFocus=True)

        # Add a 'close' option too, but run it
        # on the idle loop, as its execution will
        # cause the owning menu to be destroyed.
        frame.populateMenu(editMenu,
                           self,
                           [None, 'toggleEditMode'],
                           ignoreFocus=True,
                           runOnIdle=True)



    def __removeEditMenu(self):
        """Called by :meth:`__profleChanged` when the
        :attr:`.ViewPanel.profile` is changed from ``'edit'``. If an edit
        menut has previously been added to the :class:`.FSLeyesFrame`, it
        is removed.
        """

        if self.__editMenuTitle is None:
            return

        frame        = self.getFrame()
        editMenuName = self.__editMenuTitle
        menuBar      = frame.GetMenuBar()
        idx          = menuBar.FindMenu(editMenuName)

        self.__editMenuTitle = None

        if  idx == wx.NOT_FOUND:
            return

        editMenu = menuBar.GetMenu(idx)

        menuBar.Remove(idx)
        wx.CallAfter(editMenu.Destroy)


    def __bgColourChanged(self, *a, **kwa):
        """Called when the :class:`.SceneOpts.bgColour` property changes.
        Updates the panel and anatomical label background/foreground
        colours.

        The :attr:`.SliceCanvasOpts.bgColour` properties are bound to
        ``SceneOpts.bgColour``,(see :meth:`.HasProperties.bindProps`), so we
        don't need to manually update them.

        :arg refresh: Must be passed as a keyword argument. If ``True`` (the
                      default), this ``OrthoPanel`` is refreshed.
        """

        refresh = kwa.pop('refresh', True)

        sceneOpts = self.getSceneOptions()
        bg        = sceneOpts.bgColour
        fg        = colourmaps.complementaryColour(bg)

        # All wxwidgets things need colours
        # to be specified between 0 and 255
        intbg = [int(round(c * 255)) for c in bg]
        intfg = [int(round(c * 255)) for c in fg]

        self.getContentPanel().SetBackgroundColour(intbg)
        self.getContentPanel().SetForegroundColour(intfg)

        sceneOpts.labelColour = fg

        cbCanvas = self.getColourBarCanvas()
        if cbCanvas is not None:
            cbCanvas.textColour = fg

        self.__xcanvas.SetBackgroundColour(intbg)
        self.__ycanvas.SetBackgroundColour(intbg)
        self.__zcanvas.SetBackgroundColour(intbg)

        if refresh:
            self.Refresh()
            self.Update()


    def __toggleCanvas(self, *a):
        """Called when any of the :attr:`.OrthoOpts.showXCanvas`,
        :attr:`.OrthoOpts.showYCanvas`, or :attr:`.OrthoOpts.showZCanvas`
        properties are changed.

        Shows/hides each of the :class:`.SliceCanvas` panels accordingly.
        """

        opts     = self.getSceneOptions()
        canvases = [self.__xcanvas,   self.__ycanvas,   self.__zcanvas]
        shows    = [opts.showXCanvas, opts.showYCanvas, opts.showZCanvas]

        for canvas, show in zip(canvases, shows):

            # See WXGLSliceCanvas.Show for
            # details of a horrible bug, and
            # equally horrible workaround..
            canvas.Show(show)

        # If layout == grid, then the actual
        # layout may be different depending
        # on how many canvases are displayed
        if opts.layout == 'grid':
            self.__refreshLayout()

        self.PostSizeEvent()


    def __radioOrientationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.radioOrientation` or
        :attr:`.DisplayContext.displaySpace` property changes. Figures out if
        the left-right canvas axes need to be flipped, and does so if
        necessary.
        """

        if len(self._overlayList) == 0:
            return

        inRadio = self._displayCtx.displaySpaceIsRadiological()
        flip    = self._displayCtx.radioOrientation != inRadio

        self.__ycanvas.invertX = flip
        self.__zcanvas.invertX = flip


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` is changed. Enables/disables
        various action methods based on the currently selected overlay.
        """

        # Disable actions that need an overlay
        haveOverlays = len(self._overlayList) > 0
        selOverlay   = self._displayCtx.getSelectedOverlay()

        if selOverlay is not None:

            display = self._displayCtx.getDisplay(selOverlay)
            isImage = isinstance(selOverlay, fslimage.Image) and \
                      display.overlayType in ('volume', 'mask', 'label')
        else:
            isImage = False

        self.resetDisplay            .enabled = haveOverlays
        self.centreCursor            .enabled = haveOverlays
        self.centreCursorWorld       .enabled = haveOverlays
        self.toggleEditMode          .enabled = isImage
        self.toggleEditTransformPanel.enabled = isImage
        self.toggleCropMode          .enabled = isImage


    def __onResize(self, ev):
        """Called whenever the panel is resized. Makes sure that the
        :class:`.SliceCanvas` panels  and :class:`.Text` annotations
        are drawn correctly.
        """
        ev.Skip()
        self.__calcCanvasSizes()


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

        if width == 0 or height == 0:   return
        if len(self._overlayList) == 0: return
        if not any(show):               return

        canvases = [c for (c, s) in zip(canvases, show) if s]

        # Grid layout with 2 or less canvases displayed
        # is identical to horizontal layout
        if layout == 'grid' and len(canvases) <= 2:
            layout = 'horizontal'

        # Grid layout canvas
        # order is YXZ
        if layout == 'grid':
            canvases = [canvases[1], canvases[0], canvases[2]]

        # Distribute the available width/height
        # to each of the displayed canvases -
        # fsleyes_widgets.utils.layout (a.k.a.
        # fsllayout) provides functions to do
        # this for us
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


    def __refreshLayout(self, *a, **kwa):
        """Called when the :attr:`.OrthoOpts.layout` property changes, or the
        canvas layout needs to be refreshed. Updates the layout accordingly.

        :arg refresh: Must be passed as a keyword argument. If ``True`` (the
                      default), this ``OrthoPanel`` is refreshed.
        """

        refresh = kwa.pop('refresh', True)

        opts   = self.getSceneOptions()
        layout = opts.layout

        # We lay out all canvases, even
        # the ones that are not shown.
        canvases  = [self.__xcanvas,   self.__ycanvas,   self.__zcanvas]
        shows     = [opts.showXCanvas, opts.showYCanvas, opts.showZCanvas]
        nCanvases = sum(shows)

        # For the grid layout if only one or two
        # canvases are being displayed, the layout
        # is equivalent to a horizontal layout.
        if layout == 'grid' and nCanvases <= 2:
            layout = 'horizontal'

        # For horizontal/vertical layout,
        # the canvas layout is:
        #
        #   | X/sagittal | Y/coronal | Z/axial |
        #
        # But for grid layout, the canvas
        # layout is:
        #
        #   | Y/coronal | X/sagittal |
        #   | Z/axial   |            |
        #
        if layout == 'grid':
            canvases = [self.__ycanvas, self.__xcanvas, self.__zcanvas]

        # Regardless of the layout, we use a
        # FlexGridSizer with varying numbers
        # of rows/columns, depending upon the
        # layout strategy
        if   layout == 'horizontal': nrows, ncols = 1, 3
        elif layout == 'vertical':   nrows, ncols = 3, 1
        elif layout == 'grid':       nrows, ncols = 2, 2

        self.__canvasSizer = wx.FlexGridSizer(nrows, ncols, 0, 0)

        # The rows/columns that contain
        # canvases must also be growable
        for row in range(nrows): self.__canvasSizer.AddGrowableRow(row)
        for col in range(ncols): self.__canvasSizer.AddGrowableCol(col)

        # For grid layout, the last cell is filled with empty space
        if layout == 'grid':
            canvases.append((0, 0))

        # Add all those widgets to the grid sizer
        flag = wx.ALIGN_CENTRE_HORIZONTAL | wx.ALIGN_CENTRE_VERTICAL

        for c in canvases:
            self.__canvasSizer.Add(c, flag=flag | wx.EXPAND)

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

        if refresh:
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

        self.panel = OrthoPanel(self, overlayList, displayCtx, None)
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

        self.panel = OrthoPanel(self, overlayList, displayCtx, None)
        self.Layout()
