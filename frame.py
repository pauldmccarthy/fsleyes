#!/usr/bin/env python
#
# frame.py - A wx.Frame which implements a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLEyesFrame` which is the top level frame
for FSLeyes.
"""


import logging

import wx
import wx.lib.agw.aui     as aui

import fsl.data.strings   as strings
import fsl.utils.settings as fslsettings
import fsl.utils.status   as status

import views
import actions
import tooltips
import perspectives

import displaycontext


log = logging.getLogger(__name__)


class FSLEyesFrame(wx.Frame):
    """A ``FSLEyesFrame`` is a simple :class:`wx.Frame` which acts as a
    container for :class:`.ViewPanel` instances.

    
    A :class:`wx.lib.agw.aui.AuiManager` is used so that ``ViewPanel`` panels
    can be dynamically laid out and reconfigured by the user.

    
    **Menus**

    
    The ``FSLEyesFrame`` has three menus:

    ========== ==============================================================
    *File*     Global actions, such as adding a new overlay
    *View*     Options to open a new :class:`.ViewPanel`.
    *Settings* Options which are specific to the currently visible
               :class:`.ViewPanel` instances. A separate sub-menu is added
               for each visible ``ViewPanel``. All ``ViewPanel`` classes
               inherit from the :class:`.ActionProvider` class - any actions
               that have been defined are added as menu items here.
    ========== ==============================================================

    
    **Saving/restoring state**


    When a ``FSLEyesFrame`` is closed, it saves some display settings so that
    they can be restored the next time a ``FSLEyesFrame`` is opened. The
    settings are saved using the :class:`~fsl.utils.settings` module.
    Currently, the frame position, size, and layout (see the
    :mod:`.perspectives` module) are saved.


    **Programming interface**

    
    The ``FSLEyesFrame`` provides the following methods for programmatically
    configuring the display:

    .. autosummary::
       :nosignatures:

       getViewPanels
       getViewPanelInfo
       addViewPanel
       removeViewPanel 
       getAuiManager
       refreshPerspectiveMenu
    """

    
    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 restore=False,
                 save=True):
        """Create a ``FSLEyesFrame``.

        .. note:: The ``restore`` functionality is not currently implemented.
                  If ``restore=True``, an :class:`.OrthoPanel` is added to
                  the frame.
        
        :arg parent:      The :mod:`wx` parent object.
        
        :arg overlayList: The :class:`.OverlayList`.
        
        :arg displayCtx:  The master :class:`.DisplayContext`.
        
        :arg restore:     Restores previous saved layout. If ``False``, no 
                          view panels will be displayed.

        :arg save:        Save current layout when closed. 
        """
        
        wx.Frame.__init__(self, parent, title='FSLeyes')

        tooltips.initTooltips()

        # Default application font - this is
        # inherited by all child controls.
        font = self.GetFont()

        if wx.Platform == '__WXGTK__': font.SetPointSize(8)
        else:                          font.SetPointSize(10)
        font.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.SetFont(font)
        
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__mainPanel   = wx.Panel(self)
        self.__statusBar   = wx.StaticText(self)
        self.__auiManager  = aui.AuiManager(
            self.__mainPanel,
            agwFlags=(aui.AUI_MGR_RECTANGLE_HINT |
                      aui.AUI_MGR_NO_VENETIAN_BLINDS_FADE |
                      aui.AUI_MGR_LIVE_RESIZE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.__sizer.Add(self.__mainPanel, flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__statusBar, flag=wx.EXPAND)

        self.SetSizer(self.__sizer)

        # Re-direct status updates to the
        # status bar. Make sure that the
        # status bar is updated on the main
        # loop
        def update(msg):
            def realUpdate():
                self.__statusBar.SetLabel(msg)
                self.__statusBar.Refresh()
                self.__statusBar.Update()
            wx.CallAfter(realUpdate)
        status.setTarget(update)

        # Keeping track of all open view panels
        # 
        # The __viewPanels list contains all
        # [ViewPanel] instances
        #
        # The other dicts contain
        # {ViewPanel : something} mappings
        # 
        self.__viewPanels     = []
        self.__viewPanelDCs   = {}
        self.__viewPanelMenus = {}
        self.__viewPanelIDs   = {}

        self.__menuBar   = None
        self.__perspMenu = None
        
        self.__makeMenuBar()
        self.__restoreState(restore)

        self.__saveLayout = save

        self.__auiManager.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onViewPanelClose)
        self             .Bind(wx.EVT_CLOSE,           self.__onClose)

        self.Layout()

        
    def getViewPanels(self):
        """Returns a list of all :class:`.ViewPanel` instances that are
        currenlty displayed in this ``FSLEyesFrame``.
        """
        return list(self.__viewPanels)


    def getViewPanelInfo(self, viewPanel):
        """Returns the ``AuiPaneInfo`` class which contains layout information
        about the given :class:`.ViewPanel`.
        """
        return self.__auiManager.GetPane(viewPanel)


    def getAuiManager(self):
        """Returns the ``wx.lib.agw.aui.AuiManager` object which is managing
        the layout of this ``FSLEyesFrame``.
        """
        return self.__auiManager


    def removeViewPanel(self, viewPanel):
        """Removes the given :class:`.ViewPanel` from this ``FSLEyesFrame``.
        """

        paneInfo = self.__auiManager.GetPane(viewPanel)
        
        self.__onViewPanelClose(panel=viewPanel)
        
        self.__auiManager.ClosePane(paneInfo)
        self.__auiManager.Update() 


    def addViewPanel(self, panelCls):
        """Adds a new :class:`.ViewPanel` to the centre of the frame, and a
        menu item allowing the user to configure the view.

        :arg panelCls: The :class:`.ViewPanel` type to be added.
        """

        self.Freeze()

        if len(self.__viewPanelIDs) == 0:
            panelId = 1
        else:
            panelId = max(self.__viewPanelIDs.values()) + 1

        # The PaneInfo Name contains the panel
        # class name - this is used for saving
        # and restoring perspectives .
        name  = '{} {}'.format(panelCls.__name__,        panelId)
        title = '{} {}'.format(strings.titles[panelCls], panelId)

        childDC = displaycontext.DisplayContext(
            self.__overlayList,
            parent=self.__displayCtx)
        
        # Create a child DisplayContext. The DC
        # for the first view panel is synced to
        # the master DC, but by default the
        # overlay display settings for subsequent
        # CanvasPanels are unsynced; other
        # ViewPanels (e.g. TimeSeriesPanel) remain
        # synced by default.
        if panelId == 1:
            childDC.syncToParent('overlayOrder')
            childDC.syncOverlayDisplay = True
            
        elif issubclass(panelCls, views.CanvasPanel):
            childDC.syncOverlayDisplay = False

        panel = panelCls(
            self.__mainPanel,
            self.__overlayList,
            childDC)

        log.debug('Created new {} ({}) with DisplayContext {}'.format(
            panelCls.__name__,
            id(panel),
            id(childDC)))

        paneInfo = (aui.AuiPaneInfo()
                    .Name(name)
                    .Caption(title)
                    .CloseButton()
                    .Dockable()
                    .Resizable()
                    .DestroyOnClose())

        # When there is only one view panel
        # displayed, the AuiManager seems to
        # have trouble drawing the caption
        # bar - it is drawn, but then the
        # panel is drawn over the top of it.
        # So if we only have one panel, we
        # hide the caption bar
        if panelId == 1:
            paneInfo.Centre().Dockable(False).CaptionVisible(False)
            
        # But then re-show it when another
        # panel is added. The __viewPanels
        # dict is an OrderedDict, so the
        # first key is the AuiPaneInfo of
        # the first panel that was added.
        else:
            self.__auiManager.GetPane(self.__viewPanels[0])\
                             .CaptionVisible(True)

        # If this is not the first view panel,
        # give it a sensible initial size.
        if panelId > 1:
            width, height = self.GetClientSize().Get()

            # PlotPanels are initially
            # placed along the bottom
            if isinstance(panel, views.PlotPanel):
                paneInfo.Bottom().BestSize(-1, height / 3)

            # Other panels (e.g. CanvasPanels)
            # are placed on the right
            else:
                paneInfo.Right().BestSize(width / 3, -1)

        self.__viewPanels.append(panel)
        self.__viewPanelDCs[     panel] = childDC
        self.__viewPanelIDs[     panel] = panelId
        
        self.__auiManager.AddPane(panel, paneInfo)
        self.__addViewPanelMenu(  panel, title)

        self.__auiManager.Update()

        # PlotPanels don't draw themselves
        # automatically when created.
        if isinstance(panel, views.PlotPanel):
            panel.draw()

        self.Thaw()


    def refreshPerspectiveMenu(self):
        """Re-creates the *View -> Perspectives* sub-menu. """
        self.__makePerspectiveMenu()


    def __addViewPanelMenu(self, panel, title):
        """Called by :meth:`addViewPanel`. Adds a menu item for the newly
        created :class:`.ViewPanel` instance.

        :arg panel: The newly created ``ViewPanel`` instance.
        :arg title: The name given to the ``panel``.
        """

        actionz = panel.getActions()

        if len(actionz) == 0:
            return

        menu    = wx.Menu()
        submenu = self.__settingsMenu.AppendSubMenu(menu, title)

        self.__viewPanelMenus[panel] = submenu

        # Separate out the normal actions from
        # the toggle actions, as we will put a
        # separator between them.
        regularActions = []
        toggleActions  = []

        for actionName, actionObj in actionz:
            if isinstance(actionObj, actions.ToggleAction):
                toggleActions .append((actionName, actionObj))
            else:
                regularActions.append((actionName, actionObj))

        # Non-toggle actions
        for actionName, actionObj in regularActions:
            menuItem = menu.Append(
                wx.ID_ANY,
                strings.actions[panel, actionName],
                kind=wx.ITEM_NORMAL)
            
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        # Separator
        if len(regularActions) > 0 and len(toggleActions) > 0:
            menu.AppendSeparator()

        # Toggle actions
        for actionName, actionObj in toggleActions:

            menuItem = menu.Append(
                wx.ID_ANY,
                strings.actions[panel, actionName],
                kind=wx.ITEM_CHECK)
            
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        # Add a 'Close' action to
        # the menu for every panel 
        def closeViewPanel(ev):
            self.removeViewPanel(panel)

        # But put another separator before it
        if len(regularActions) > 0 or len(toggleActions) > 0:
            menu.AppendSeparator()

        closeItem = menu.Append(
            wx.ID_ANY,
            strings.actions[self, 'closeViewPanel'])
        self.Bind(wx.EVT_MENU, closeViewPanel, closeItem)
    

    def __onViewPanelClose(self, ev=None, panel=None):
        """Called when the user closes a :class:`.ViewPanel`.

        The :meth:`__addViewPanelMenu` method adds a *Close* menu item
        for every view panel, and binds it to this method.

        This method does the following:

         1. Makes sure that the ``ViewPanel``: is destroyed correctly
         2. Removes the *Settings* sub-menu corresponding to the ``ViewPanel``.
         3. Makes sure that any remaining ``ViewPanel`` panels are arranged
            nicely.
        """

        if ev is not None:
            ev.Skip()
            
            # Undocumented - the window associated with an
            # AuiPaneInfo is available as an attribute called
            # 'window'. Honestly, I don't know why there is
            # not a method available on the AuiPaneInfo or
            # AuiManager to retrieve a managed Window given
            # the associated AuiPaneInfo object.
            paneInfo = ev.GetPane()
            panel    = paneInfo.window
            
        elif panel is not None:
            paneInfo = self.__auiManager.GetPane(panel)

        # This method may get called when
        # the user closes a control panel
        if panel is None or panel not in self.__viewPanels:
            return

        self       .__viewPanels    .remove(panel)
        self       .__viewPanelIDs  .pop(   panel)
        dctx = self.__viewPanelDCs  .pop(   panel)
        menu = self.__viewPanelMenus.pop(   panel, None)

        log.debug('Destroying {} ({}) and '
                  'associated DisplayContext ({})'.format(
                      type(panel).__name__,
                      id(panel),
                      id(dctx)))

        # Remove the view panel menu
        if menu is not None:
            self.__settingsMenu.Remove(menu.GetId())

        # Calling fslpanel.FSLEyesPanel.destroy()
        # and DisplayContext.destroy() - the
        # AUIManager should do the
        # wx.Window.Destroy side of things ...
        panel.destroy()
        dctx .destroy()

        # If the removed panel was the centre
        # pane, or if there is only one panel
        # left, move another panel to the centre
        numPanels = len(self.__viewPanels)
        wasCentre = paneInfo.dock_direction_get() == aui.AUI_DOCK_CENTRE
        
        if numPanels >= 1 and wasCentre:
            paneInfo = self.__auiManager.GetPane(self.__viewPanels[0])
            paneInfo.Centre().Dockable(False).CaptionVisible(numPanels > 1)
            
        # If there's only one panel left,
        # and it is a canvas panel, sync
        # its display properties to the
        # master display context.
        if numPanels == 1 and \
           isinstance(self.__viewPanels[0], views.CanvasPanel):
            
            dctx     = self.__viewPanels[0].getDisplayContext()
            displays = [dctx.getDisplay(o) for o in self.__overlayList]

            # Make sure that the parent context
            # inherits the values from this context
            dctx.setBindingDirection(False)

            for display in displays:
                opts = display.getDisplayOpts()
                display.setBindingDirection(False)
                opts   .setBindingDirection(False)
            
            dctx.syncOverlayDisplay = True
            dctx.syncToParent('overlayOrder')

            # Reset the binding directiona
            dctx.setBindingDirection(True)

            for display in displays:
                opts = display.getDisplayOpts()
                display.setBindingDirection(True)
                opts   .setBindingDirection(True) 

            
    def __onClose(self, ev):
        """Called when the user closes this ``FSLEyesFrame``.

        Saves the frame position, size, and layout, so it may be preserved the
        next time it is opened. See the :meth:`_restoreState` method.
        """

        ev.Skip()

        if self.__saveLayout:
            
            size     = self.GetSize().Get()
            position = self.GetScreenPosition().Get()
            layout   = perspectives.serialisePerspective(self)


            log.debug('Saving size: {}'    .format(size))
            log.debug('Saving position: {}'.format(position))
            log.debug('Saving layout: {}'  .format(layout))
            
            fslsettings.write('framesize',     str(size))
            fslsettings.write('frameposition', str(position))
            fslsettings.write('framelayout',   layout)
        
        # It's nice to explicitly clean
        # up our FSLEyesPanels, otherwise
        # they'll probably complain
        for panel in self.__viewPanels:
            panel.destroy()

        
    def __parseSavedSize(self, size):
        """Parses the given string, which is assumed to contain a size tuple.
        """
        
        try:    return tuple(map(int, size[1:-1].split(',')))
        except: return None

        
    def __parseSavedPoint(self, size):
        """A proxy for the :meth:`__parseSavedSize` method.""" 
        return self.__parseSavedSize(size)

    
    def __restoreState(self, restore):
        """Called by :meth:`__init__`.

        If any frame size/layout properties have previously been saved via the
        :mod:`~fsl.utils.settings` module, they are read in, and applied to
        this frame.

        :arg restore: If ``False``, any saved layout state is ignored.
        """

        from operator import itemgetter as iget

        # Restore the saved frame size/position
        size     = self.__parseSavedSize( fslsettings.read('framesize'))
        position = self.__parseSavedPoint(fslsettings.read('frameposition'))
        layout   =                        fslsettings.read('framelayout')

        if (size is not None) and (position is not None):

            # Turn the saved size/pos into
            # a (tlx, tly, brx, bry) tuple
            frameRect = [position[0],
                         position[1],
                         position[0] + size[0],
                         position[1] + size[1]]

            # Now make a bounding box containing the
            # space made up of all available displays.
            # Get the bounding rectangles of each 
            # display, and change them from
            # (x, y, w, h) into (tlx, tly, brx, bry).
            displays  = [wx.Display(i)   for i in range(wx.Display.GetCount())]
            dispRects = [d.GetGeometry() for d in displays]
            dispRects = [[d.GetTopLeft()[    0],
                          d.GetTopLeft()[    1],
                          d.GetBottomRight()[0],
                          d.GetBottomRight()[1]] for d in dispRects]

            # get the union of these display
            # rectangles (tlx, tly, brx, bry)
            dispRect = [min(dispRects, key=iget(0))[0],
                        min(dispRects, key=iget(1))[1],
                        max(dispRects, key=iget(2))[2],
                        max(dispRects, key=iget(3))[3]]

            # Now we have our two rectangles - the
            # rectangle of our saved frame position,
            # and the rectangle of the available
            # display space.

            # Calculate the area of intersection
            # betwen the two rectangles, and the
            # area of our saved frame position
            xOverlap  = max(0, min(frameRect[2], dispRect[2]) -
                               max(frameRect[0], dispRect[0]))
            yOverlap  = max(0, min(frameRect[3], dispRect[3]) -
                               max(frameRect[1], dispRect[1]))

            intArea   = xOverlap * yOverlap
            frameArea = ((frameRect[2] - frameRect[0]) *
                         (frameRect[3] - frameRect[1]))

            # If the ratio of (frame-display intersection) to
            # (saved frame position) is 'not decent', then 
            # forget it, and use a default frame position/size
            ratio = intArea / float(frameArea)
            if ratio < 0.5:

                log.debug('Intersection of saved frame area with available '
                          'display area is too small ({}) - reverting to '
                          'default frame size/position'.format(ratio))
                
                size     = None
                position = None

        if size is not None:
            log.debug('Restoring previous size: {}'.format(size))
            self.SetSize(size)
            
        else:
            
            # Default size is 90% of
            # the first display size
            size     = list(wx.Display(0).GetGeometry().GetSize())
            size[0] *= 0.9
            size[1] *= 0.9
            log.debug('Setting default frame size: {}'.format(size))
            self.SetSize(size)

        if position is not None:
            log.debug('Restoring previous position: {}'.format(position))
            self.SetPosition(position)
        else:
            self.Centre()

        if restore:
            if layout is not None:
                log.debug('Restoring previous layout: {}'.format(layout))

                try:
                    perspectives.applyPerspective(
                        self,
                        'framelayout',
                        layout,
                        message=strings.messages[self, 'restoringLayout'])
                except:
                    log.warn('Previous layout could not be restored - '
                             'falling back to default layout.')
                    layout = None

            if layout is None:
                perspectives.loadPerspective(self, 'default')
                

            
    def __makeMenuBar(self):
        """Constructs a bunch of menu items for this ``FSLEyesFrame``."""

        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

        fileMenu        = wx.Menu()
        viewMenu        = wx.Menu()
        perspectiveMenu = wx.Menu() 
        settingsMenu    = wx.Menu()

        self.__menuBar   = menuBar
        self.__perspMenu = perspectiveMenu
        
        menuBar.Append(fileMenu,     'File')
        menuBar.Append(viewMenu,     'View')
        menuBar.Append(settingsMenu, 'Settings') 

        self.__fileMenu     = fileMenu
        self.__viewMenu     = viewMenu
        self.__settingsMenu = settingsMenu

        # Global actions
        actionz = [actions.OpenFileAction,
                   actions.OpenDirAction,
                   actions.OpenStandardAction,
                   'sep',
                   actions.CopyOverlayAction,
                   actions.SaveOverlayAction,
                   actions.RemoveOverlayAction,
                   actions.RemoveAllOverlaysAction]
 
        for action in actionz:

            if action == 'sep':
                fileMenu.AppendSeparator()
                continue
            menuItem  = fileMenu.Append(wx.ID_ANY, strings.actions[action])
            actionObj = action(self.__overlayList, self.__displayCtx, self)

            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        # Shortcuts to open a new view panel
        viewPanels = [views.OrthoPanel,
                      views.LightBoxPanel,
                      views.TimeSeriesPanel,
                      views.PowerSpectrumPanel,
                      views.HistogramPanel]
        
        for viewPanel in viewPanels:
            viewAction = viewMenu.Append(wx.ID_ANY, strings.titles[viewPanel]) 
            self.Bind(wx.EVT_MENU,
                      lambda ev, vp=viewPanel: self.addViewPanel(vp),
                      viewAction)

        # Perspectives
        viewMenu.AppendSeparator()
        viewMenu.AppendSubMenu(perspectiveMenu, 'Perspectives')
        self.__makePerspectiveMenu()

        
    def __makePerspectiveMenu(self):
        """Re-creates the *View->Perspectives* menu. """

        perspMenu = self.__perspMenu

        # Remove any existing menu items
        for item in perspMenu.GetMenuItems():
            perspMenu.DeleteItem(item)

        builtIns = perspectives.BUILT_IN_PERSPECTIVES.keys()
        saved    = perspectives.getAllPerspectives()

        # Add a menu item to load each built-in perspectives
        for persp in builtIns:
            menuItem  = perspMenu.Append(
                wx.ID_ANY, strings.perspectives.get(persp, persp))
            
            actionObj = actions.LoadPerspectiveAction(self, persp)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        if len(builtIns) > 0:
            perspMenu.AppendSeparator()

        # Add a menu item to load each saved perspective
        for persp in saved:
            
            menuItem  = perspMenu.Append(
                wx.ID_ANY, strings.perspectives.get(persp, persp))
            actionObj = actions.LoadPerspectiveAction(self, persp)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        # Add menu items for other perspective
        # operations, but separate them from the
        # existing perspectives
        if len(saved) > 0:
            perspMenu.AppendSeparator()

        # TODO: Delete a single perspective?
        #       Save to/load from file? 
        perspActions = [actions.SavePerspectiveAction,
                        actions.ClearPerspectiveAction]

        for pa in perspActions:

            actionObj     = pa(self)
            perspMenuItem = perspMenu.Append(wx.ID_ANY, strings.actions[pa])
            
            actionObj.bindToWidget(self, wx.EVT_MENU, perspMenuItem)
