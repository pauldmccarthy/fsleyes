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
import fsleyes_widgets.utils.layout            as fsllayout

import fsleyes.strings                         as strings
import fsleyes.gl                              as fslgl
import fsleyes.actions                         as actions
import fsleyes.editor                          as editor
import fsleyes.profiles.orthoviewprofile       as orthoviewprofile
import fsleyes.profiles.orthoeditprofile       as orthoeditprofile
import fsleyes.gl.ortholabels                  as ortholabels
import fsleyes.gl.wxglslicecanvas              as slicecanvas
import fsleyes.controls.locationpanel          as locationpanel
import fsleyes.controls.orthoedittoolbar       as orthoedittoolbar
import fsleyes.controls.orthoeditactiontoolbar as orthoeditactiontoolbar
import fsleyes.controls.orthoeditsettingspanel as orthoeditsettingspanel
import fsleyes.displaycontext.orthoopts        as orthoopts
from . import                                     canvaspanel


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


    The ``OrthoPanel`` creates an :class:`.OrthoLabels` instance, which
    manages the display of anatomical orientation labels on each of the
    three :class:`.SliceCanvas` instances.


    **Display**


    The display of an ``OrthoPanel`` can be configured through all of the
    settings provided by the :class:`.OrthoOpts` class. The ``OrthoOpts``
    instance for a given ``OrthoPanel`` can be accessed via the
    :meth:`.CanvasPanel.sceneOpts` method.


    **Interaction**


    The :class:`.OrthoPanel` uses the :class:`.OrthoViewProfile` to handle
    interaction with the user via the mouse and keyboard. Some control panels
    will activate other interaction profiles while they are open, such as:

    ========================== ==============================================
    :class:`.OrthoEditToolBar` Simple editing of :class:`.Image`
                               overlays, using the
                               :class:`.OrthoEditProfile` (see also
                               the :mod:`~fsleyes.editor` package).

    :class:`.CropImagePanel`   Allows the user to crop an ``Image`` overlay,
                               using the :class:`.OrthoCropProfile`.

    :class:`.AnnotationPanel`  Allows the user to draw text and shapes on the
                               :class:`.OrthoPanel` canvases, using the
                               :class:`.OrthoAnnotatePanel`.
    ========================== ==============================================

    See the :class:`.ViewPanel`, and the :mod:`.profiles` package for more
    information on interaction profiles.


    **Actions and control panels**


    The ``OrthoPanel`` adds a few extra actions to those provided by the
    :class:`.CanvasPanel` class:

    .. autosummary::
       :nosignatures:

       toggleEditMode
       resetDisplay
       centreCursor
       centreCursorWorld
       toggleCursor
       toggleLabels
       toggleXCanvas
       toggleYCanvas
       toggleZCanvas
    """


    def controlOptions(self, cpType):
        """Returns some options to be used by :meth:`.ViewPanel.togglePanel`
        for certain control panel types.
        """
        if cpType is locationpanel.LocationPanel:
            return {'showHistory' : True}


    @staticmethod
    def defaultLayout():
        """Returns a list of control panel types to be added for the default
        ortho panel layout.
        """
        return ['OverlayDisplayToolBar',
                'OrthoToolBar',
                'OverlayListPanel',
                'LocationPanel']


    @staticmethod
    def controlOrder():
        """Returns a list of control panel names, specifying the order in
        which they should appear in the  FSLeyes ortho panel settings menu.
        """
        return ['OverlayListPanel',
                'LocationPanel',
                'OverlayInfoPanel',
                'OverlayDisplayPanel',
                'CanvasSettingsPanel',
                'AtlasPanel',
                'OverlayDisplayToolBar',
                'OrthoToolBar',
                'FileTreePanel']


    @staticmethod
    def toolOrder():
        """Returns a list of tool names, specifying the order in which they
        should appear in the FSLeyes ortho panel settings menu.
        """
        return ['CropImageAction',
                'EditTransformAction',
                'SampleLineAction',
                'LoadAnnotationsAction',
                'SaveAnnotationsAction',
                'PearsonCorrelateAction']


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create an ``OrthoPanel``.

        :arg parent:      The :mod:`wx` parent.
        :arg overlayList: An :class:`.OverlayList` instance.
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        :arg displayCtx:  A :class:`.FSLeyesFrame` instance.
        """

        sceneOpts = orthoopts.OrthoOpts(self)

        canvaspanel.CanvasPanel.__init__(self,
                                         parent,
                                         overlayList,
                                         displayCtx,
                                         frame,
                                         sceneOpts)

        name         = self.name
        contentPanel = self.contentPanel

        # The canvases themselves - each one displays
        # a slice along each of the three world axes.
        # They are laid out in __refreshLayout
        self.__canvasSizer = None
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

        # Edit mode is entered via toggleEditMode,
        # which displays an edit toolbar. But we
        # do a bit more, in adding the edit action
        # toolbar, and edit menu. In order to keep
        # the menu state in sync with reality, we
        # need to listen for changes to the
        # interaction proflle, and store a ref
        # to the edit menu so we can delete it later.
        self.events.register(self.name, self.__profileChanged, 'profile')
        self.__editMenuTitle = None

        # The OrthoOpts and DisplayContext objects
        # contains the properties that the user
        # interacts with, but the slice canvases
        # are controlled by properties on a
        # SliceCanvsOpts object (one for each
        # canvas). So we bind properties of these
        # objects together.
        xopts = self.__xcanvas.opts
        yopts = self.__ycanvas.opts
        zopts = self.__zcanvas.opts

        xopts.bindProps('pos', displayCtx, 'location')
        yopts.bindProps('pos', displayCtx, 'location')
        zopts.bindProps('pos', displayCtx, 'location')

        xopts.bindProps('showCursor',   sceneOpts)
        yopts.bindProps('showCursor',   sceneOpts)
        zopts.bindProps('showCursor',   sceneOpts)

        xopts.bindProps('cursorGap',    sceneOpts)
        yopts.bindProps('cursorGap',    sceneOpts)
        zopts.bindProps('cursorGap',    sceneOpts)

        xopts.bindProps('bgColour',     sceneOpts)
        yopts.bindProps('bgColour',     sceneOpts)
        zopts.bindProps('bgColour',     sceneOpts)

        xopts.bindProps('cursorColour', sceneOpts)
        yopts.bindProps('cursorColour', sceneOpts)
        zopts.bindProps('cursorColour', sceneOpts)

        xopts.bindProps('zoom',         sceneOpts, 'xzoom')
        yopts.bindProps('zoom',         sceneOpts, 'yzoom')
        zopts.bindProps('zoom',         sceneOpts, 'zzoom')

        xopts.bindProps('renderMode',   sceneOpts)
        yopts.bindProps('renderMode',   sceneOpts)
        zopts.bindProps('renderMode',   sceneOpts)

        xopts.bindProps('highDpi',      sceneOpts)
        yopts.bindProps('highDpi',      sceneOpts)
        zopts.bindProps('highDpi',      sceneOpts)

        xopts.bindProps('invertX', sceneOpts, 'invertXHorizontal')
        xopts.bindProps('invertY', sceneOpts, 'invertXVertical')
        yopts.bindProps('invertX', sceneOpts, 'invertYHorizontal')
        yopts.bindProps('invertY', sceneOpts, 'invertYVertical')
        zopts.bindProps('invertX', sceneOpts, 'invertZHorizontal')
        zopts.bindProps('invertY', sceneOpts, 'invertZVertical')

        # Callbacks for ortho panel layout options
        sceneOpts.addListener('layout', name, self.__refreshLayout)

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

        # Callbacks for toggling x/y/z canvas display
        sceneOpts.addListener('showXCanvas', name, self.__toggleCanvas)
        sceneOpts.addListener('showYCanvas', name, self.__toggleCanvas)
        sceneOpts.addListener('showZCanvas', name, self.__toggleCanvas)

        # Callbacks which just need to refresh
        def refresh(*a):
            self.Refresh()

        sceneOpts.addListener('labelSize',   name, refresh, weak=False)
        sceneOpts.addListener('fgColour',    name, refresh, weak=False)
        sceneOpts.addListener('showLabels',  name, refresh, weak=False)

        # The lastFocusedCanvas method allows
        # a ref to the most recently focused
        # canvas to be obtained. We listen
        # for focus events on each canvas,
        # and update this ref each time
        self.__focusedCanvas = None
        self.__xcanvas.Bind(wx.EVT_SET_FOCUS, self.__onCanvasFocus)
        self.__ycanvas.Bind(wx.EVT_SET_FOCUS, self.__onCanvasFocus)
        self.__zcanvas.Bind(wx.EVT_SET_FOCUS, self.__onCanvasFocus)

        # Call the __onResize method to refresh
        # the slice canvases when the canvas
        # panel is resized, so aspect ratio
        # is maintained
        contentPanel.Bind(wx.EVT_SIZE, self.__onResize)

        # Initialise the panel
        self.__radioOrientationChanged()
        self.__refreshLayout(refresh=False)
        self.__overlayListChanged()
        self.centrePanelLayout()
        self.initProfile(orthoviewprofile.OrthoViewProfile)


    def destroy(self):
        """Must be called when this ``OrthoPanel`` is closed.

        Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList` instances, destroys each of the three
        :class:`.SliceCanvas` panels, and calls :meth:`.CanvasPanel.destroy`.
        """

        sceneOpts    = self.sceneOpts
        contentPanel = self.contentPanel

        sceneOpts       .removeListener('showXCanvas',      self.name)
        sceneOpts       .removeListener('showYCanvas',      self.name)
        sceneOpts       .removeListener('showZCanvas',      self.name)
        sceneOpts       .removeListener('labelSize',        self.name)
        sceneOpts       .removeListener('fgColour',         self.name)
        sceneOpts       .removeListener('showLabels',       self.name)
        self.displayCtx .removeListener('location',         self.name)
        self.displayCtx .removeListener('bounds',           self.name)
        self.displayCtx .removeListener('selectedOverlay',  self.name)
        self.displayCtx .removeListener('displaySpace',     self.name)
        self.displayCtx .removeListener('radioOrientation', self.name)
        self.overlayList.removeListener('overlays',         self.name)

        self.__labelMgr.destroy()
        self.__xcanvas.destroy()
        self.__ycanvas.destroy()
        self.__zcanvas.destroy()
        self.__removeEditMenu()

        contentPanel.Unbind(wx.EVT_SIZE)

        self.__xcanvas       = None
        self.__ycanvas       = None
        self.__zcanvas       = None
        self.__focusedCanvas = None
        self.__labelMgr      = None

        canvaspanel.CanvasPanel.destroy(self)


    @actions.toggleControlAction(orthoedittoolbar.OrthoEditToolBar)
    def toggleEditMode(self):
        """Shows/hides an :class:`.OrthoEditToolBar`. This causes the
        interaction profile to be changed, and a call to
        :meth:`__profileChanged`, which makes a few other changes to the
        interface.
        """
        self.togglePanel(orthoedittoolbar.OrthoEditToolBar)
        self.togglePanel(orthoeditactiontoolbar.OrthoEditActionToolBar,
                         location=wx.LEFT)

        if self.toggleEditMode.toggled and \
           self.isPanelOpen(orthoeditsettingspanel.OrthoEditSettingsPanel):
            self.togglePanel(orthoeditsettingspanel.OrthoEditSettingsPanel)


    def __profileChanged(self, inst, topic, value):
        """Called when the interaction profile changes (see
        :meth:`.ViewPanel.events`). If entering or exiting edit mode, an
        edit menu is added/removed from the menu bar.
        """

        old, new = value

        if new is orthoeditprofile.OrthoEditProfile:
            self.__addEditMenu()
        elif old is orthoeditprofile.OrthoEditProfile:
            self.__removeEditMenu()


    @actions.action
    def resetDisplay(self):
        """Calls :meth:`.OrthoViewProfile.resetDisplay`. """
        self.currentProfile.resetDisplay()


    @actions.action
    def centreCursor(self):
        """Calls :meth:`.OrthoViewProfile.centreCursor`. """
        self.currentProfile.centreCursor()


    @actions.action
    def centreCursorWorld(self):
        """Calls :meth:`.OrthoViewProfile.centreCursorWorld`. """
        self.currentProfile.centreCursorWorld()


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
                   self.movieGif,
                   self.showCommandLineArgs,
                   self.applyCommandLineArgs,
                   None,
                   self.toggleMovieMode,
                   self.toggleDisplaySync,
                   None,
                   self.resetDisplay,
                   self.centreCursor,
                   self.centreCursorWorld,
                   None,
                   self.toggleLabels,
                   self.toggleCursor,
                   self.toggleXCanvas,
                   self.toggleYCanvas,
                   self.toggleZCanvas]

        names = [a.actionName if a is not None else None for a in actionz]
        return list(zip(names, actionz))


    def getTools(self):
        """Returns a list of methods to be added to the ``FSLeyesFrame`` Tools
        menu for ``OrthoPanel`` views.
        """
        return [self.toggleEditMode]


    def getGLCanvases(self):
        """Returns all of the :class:`.SliceCanvas` instances contained
        within this ``OrthoPanel``.
        """
        canvas = [self.__xcanvas, self.__ycanvas, self.__zcanvas]
        return [c for c in canvas if c is not None]


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


    def lastFocusedCanvas(self):
        """Return a reference to the :class:`.SliceCanvas` which most recently
        had focus. Will be ``None`` if called before any canvas gains focus.
        """
        return self.__focusedCanvas


    def __onCanvasFocus(self, ev):
        """Called when any :class:`.SliceCanvas` gains focus. Updates the
        last focused canvas reference.
        """
        self.__focusedCanvas = ev.GetEventObject()


    def __addEditMenu(self):
        """Called by :meth:`__profleChanged` when the
        :attr:`.ViewPanel.profile` is changed to ``'edit'``. Adds a
        menu to the :class:`.FSLeyesFrame`.
        """

        frame    = self.frame
        menuName = strings.labels[self, 'editMenu']
        menuName = menuName.format(frame.getViewPanelID(self))
        menuBar  = frame.GetMenuBar()
        profile  = self.currentProfile
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
                   'invertSelection',
                   'copyPasteData',
                   'copyPasteSelection']

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

        frame        = self.frame
        editMenuName = self.__editMenuTitle
        menuBar      = frame.GetMenuBar()
        idx          = menuBar.FindMenu(editMenuName)

        self.__editMenuTitle = None

        if  idx == wx.NOT_FOUND:
            return

        editMenu = menuBar.GetMenu(idx)

        menuBar.Remove(idx)
        wx.CallAfter(editMenu.Destroy)


    def __toggleCanvas(self, *a):
        """Called when any of the :attr:`.OrthoOpts.showXCanvas`,
        :attr:`.OrthoOpts.showYCanvas`, or :attr:`.OrthoOpts.showZCanvas`
        properties are changed.

        Shows/hides each of the :class:`.SliceCanvas` panels accordingly.
        """

        opts     = self.sceneOpts
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

        if len(self.overlayList) == 0:
            return

        inRadio = self.displayCtx.displaySpaceIsRadiological()
        flip    = self.displayCtx.radioOrientation != inRadio

        self.__ycanvas.opts.invertX = flip
        self.__zcanvas.opts.invertX = flip


    def __overlayListChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` is changed. Enables/disables
        various action methods based on the currently selected overlay.
        """

        # Disable actions that need an overlay
        haveOverlays = len(self.overlayList) > 0
        selOverlay   = self.displayCtx.getSelectedOverlay()

        if selOverlay is not None:

            display    = self.displayCtx.getDisplay(selOverlay)
            isImage    = isinstance(selOverlay, fslimage.Image) and \
                             display.overlayType in ('volume',
                                                     'mask',
                                                     'label',
                                                     'mip')
            isEditable = editor.isEditable(selOverlay, self.displayCtx)
        else:
            isImage    = False
            isEditable = False

        # Kill edit mode if a non-
        # image has been selected
        if (not isEditable) and self.toggleEditMode.toggled:
            self.toggleEditMode()

        self.resetDisplay            .enabled = haveOverlays
        self.centreCursor            .enabled = haveOverlays
        self.centreCursorWorld       .enabled = haveOverlays
        self.toggleEditMode          .enabled = isEditable


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

        opts   = self.sceneOpts
        layout = opts.layout

        width, height = self.contentPanel.GetClientSize().Get()

        show     = [opts.showXCanvas,  opts.showYCanvas,  opts.showZCanvas]
        canvases = [self.__xcanvas,    self.__ycanvas,    self.__zcanvas]

        if width == 0 or height == 0:  return
        if len(self.overlayList) == 0: return
        if not any(show):              return

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
        canvasaxes = [(c.opts.xax, c.opts.yax) for c in canvases]
        axisLens   = [self.displayCtx.bounds.xlen,
                      self.displayCtx.bounds.ylen,
                      self.displayCtx.bounds.zlen]

        sizes = fsllayout.calcSizes(layout,
                                    canvasaxes,
                                    axisLens,
                                    width,
                                    height)

        for canvas, size in zip(canvases, sizes):
            canvas.SetMinSize((round(size[0]), round(size[1])))
            canvas.SetMaxSize((round(size[0]), round(size[1])))


    def __refreshLayout(self, *a, **kwa):
        """Called when the :attr:`.OrthoOpts.layout` property changes, or the
        canvas layout needs to be refreshed. Updates the layout accordingly.

        :arg refresh: Must be passed as a keyword argument. If ``True`` (the
                      default), this ``OrthoPanel`` is refreshed.
        """

        refresh = kwa.pop('refresh', True)

        opts   = self.sceneOpts
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

        if self.__canvasSizer is not None:
            self.__canvasSizer.Clear()
            self.__canvasSizer = None

        self.__canvasSizer = wx.FlexGridSizer(nrows, ncols, 0, 0)

        # The rows/columns that contain
        # canvases must also be growable
        for row in range(nrows): self.__canvasSizer.AddGrowableRow(row)
        for col in range(ncols): self.__canvasSizer.AddGrowableCol(col)

        # For grid layout, the last cell is filled with empty space
        if layout == 'grid':
            canvases.append((0, 0))

        # Add all those widgets to the grid sizer
        for c in canvases:
            self.__canvasSizer.Add(c, flag=wx.EXPAND)

        self.contentPanel.SetSizer(self.__canvasSizer)

        # Calculate/ adjust the appropriate sizes
        # for each canvas, such that they are scaled
        # appropriately relative to each other, and
        # the displayed world space aspect ratio is
        # maintained
        self.__calcCanvasSizes()

        # When in grid layout, flip the horizontal axis
        # of the X canvas (assumed to be A/P), to force
        # third angle orthographic projection.
        self.__xcanvas.opts.invertX = layout == 'grid'

        if refresh:
            self.Layout()
            self.contentPanel.Layout()
            self.Refresh()


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
