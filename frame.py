#!/usr/bin/env python
#
# frame.py - A wx.Frame which implements a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLEyesFrame` which is the top level frame
for the FSLEyes application, providing functionality to view 3D/4D images,
and other types of data.
"""


import logging
import collections

import wx
import wx.lib.agw.aui     as aui

import fsl.data.strings   as strings
import fsl.utils.settings as fslsettings

import views
import actions
import displaycontext


log = logging.getLogger(__name__)


class FSLEyesFrame(wx.Frame):
    """A frame which implements a 3D image viewer."""

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 restore=True):
        """
        :arg parent:
        
        :arg overlayList:
        
        :arg displayCtx:
        
        :arg restore:    Restores previous saved layout (not currently
                         implemented). If ``False``, no view panels will
                         be displayed.
        """
        
        wx.Frame.__init__(self, parent, title='FSLEyes')

        # Default application font - this is
        # inherited by all child controls.
        font = self.GetFont()

        if wx.Platform == '__WXGTK__': font.SetPointSize(8)
        else:                          font.SetPointSize(10)
        font.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.SetFont(font)
        
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__auiManager  = aui.AuiManager(
            self,
            agwFlags=(aui.AUI_MGR_RECTANGLE_HINT |
                      aui.AUI_MGR_NO_VENETIAN_BLINDS_FADE |
                      aui.AUI_MGR_LIVE_RESIZE))

        # Keeping track of all open view panels
        # 
        # The __viewPanels dict contains
        # {AuiPaneInfo : ViewPanel} mappings
        #
        # The other dicts contain
        # {ViewPanel : something} mappings
        # 
        self.__viewPanels     = collections.OrderedDict()
        self.__viewPanelDCs   = {}
        self.__viewPanelMenus = {}
        self.__viewPanelIDs   = {}

        self.__makeMenuBar()
        self.__restoreState(restore)

        self.__auiManager.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onViewPanelClose)
        self             .Bind(wx.EVT_CLOSE,           self.__onClose)

        
    def getViewPanels(self):
        """Returns a list of all view panels that currently exist. """
        return self.__viewPanels.values()


    def addViewPanel(self, panelCls):
        """Adds a view panel to the centre of the frame, and a menu item
        allowing the user to configure the view.
        """

        self.Freeze()

        if len(self.__viewPanelIDs) == 0:
            panelId = 1
        else:
            panelId = max(self.__viewPanelIDs.values()) + 1
            
        title   = '{} {}'.format(strings.titles[panelCls], panelId)

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
        if panelId > 1 and issubclass(panelCls, views.CanvasPanel):
            childDC.syncOverlayDisplay = False
        
        panel = panelCls(
            self,
            self.__overlayList,
            childDC)

        log.debug('Created new {} ({}) with DisplayContext {}'.format(
            panelCls.__name__,
            id(panel),
            id(childDC)))

        paneInfo = (aui.AuiPaneInfo()
                    .Name(title)
                    .Caption(title)
                    .Dockable()
                    .CloseButton()
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
            paneInfo.Centre().CaptionVisible(False)
            
        # But then re-show it when another
        # panel is added. The __viewPanels
        # dict is an OrderedDict, so the
        # first key is the AuiPaneInfo of
        # the first panel that was added.
        else:
            self.__viewPanels.keys()[0].CaptionVisible(True)

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

        self.__viewPanels[  paneInfo] = panel
        self.__viewPanelDCs[panel]    = childDC
        self.__viewPanelIDs[panel]    = panelId
        
        self.__auiManager.AddPane(panel, paneInfo)
        self.__addViewPanelMenu(  panel, title)

        self.__auiManager.Update()

        self.Thaw()


    def __addViewPanelMenu(self, panel, title):

        actionz = panel.getActions()

        if len(actionz) == 0:
            return

        menu    = wx.Menu()
        submenu = self.__settingsMenu.AppendSubMenu(menu, title)

        self.__viewPanelMenus[panel] = submenu

        for actionName, actionObj in actionz.items():
            
            menuItem = menu.Append(
                wx.ID_ANY,
                strings.actions[panel, actionName])
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        # Add a 'Close' action to
        # the menu for every panel 
        def closeViewPanel(ev):
            paneInfo = self.__auiManager.GetPane(panel)
            self.__onViewPanelClose(    paneInfo=paneInfo)
            self.__auiManager.ClosePane(paneInfo)
            self.__auiManager.Update()

        closeItem = menu.Append(
            wx.ID_ANY,
            strings.actions[self, 'closeViewPanel'])
        self.Bind(wx.EVT_MENU, closeViewPanel, closeItem)
            
    

    def __onViewPanelClose(self, ev=None, paneInfo=None):

        if ev is not None:
            ev.Skip()
            paneInfo = ev.GetPane()

        panel = self .__viewPanels.pop(paneInfo, None)        

        if panel is None:
            return

        self       .__viewPanelIDs  .pop(panel)
        dctx = self.__viewPanelDCs  .pop(panel)
        menu = self.__viewPanelMenus.pop(panel, None)

        log.debug('Destroying {} ({}) and '
                  'associated DisplayContext ({})'.format(
                      type(panel).__name__,
                      id(panel),
                      id(dctx)))

        # Unbind view panel menu
        # items, and remove the menu
        for actionName, actionObj in panel.getActions().items():
            actionObj.unbindAllWidgets()

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
        
        if numPanels == 1 or (numPanels > 0 and wasCentre):
            paneInfo = self.__viewPanels.keys()[0]
            paneInfo.Centre().CaptionVisible(False)

        
    def __onClose(self, ev):
        """Called on requests to close this :class:`FSLEyesFrame`.

        Saves the frame position, size, and layout, so it may be preserved the
        next time it is opened. See the :meth:`_restoreState` method.
        """

        ev.Skip()

        size     = self.GetSize().Get()
        position = self.GetScreenPosition().Get()

        fslsettings.write('framesize',     str(size))
        fslsettings.write('frameposition', str(position))

        # It's nice to explicitly clean
        # up our FSLEyesPanels, otherwise
        # they'll probably complain
        for panel in self.__viewPanels.values():
            panel.destroy()

        
    def __parseSavedSize(self, size):
        """Parses the given string, which is assumed to contain a size tuple.
        """
        
        try:    return tuple(map(int, size[1:-1].split(',')))
        except: return None

        
    __parseSavedPoint = __parseSavedSize
    """A proxy for the :meth:`__parseSavedSize` method.
    """ 

            
    def __parseSavedLayout(self, layout):
        """Parses the given string, which is assumed to contain an encoded
        :class:`.AuiManager` perspective (see
        :meth:`.AuiManager.SavePerspective`).

        Returns a list of class names, specifying the control panels
        (e.g. :class:`.ImageListPanel`) which were previously open, and need
        to be created.
        """

        try:

            names    = [] 
            sections = layout.split('|')[1:]

            for section in sections:
                
                if section.strip() == '': continue
                
                attrs = section.split(';')
                attrs = dict([tuple(nvpair.split('=')) for nvpair in attrs])

                if 'name' in attrs:
                    names.append(attrs['name'])

            return names
        except:
            return []

    
    def __restoreState(self, restore=True):
        """Called on :meth:`__init__`. If any frame size/layout properties
        have previously been saved, they are applied to this frame.

        :arg bool default: If ``True``, any saved state is ignored.
        """

        from operator import itemgetter as iget

        # Restore the saved frame size/position
        size     = self.__parseSavedSize(
            fslsettings.read('framesize'))
        position = self.__parseSavedPoint(
            fslsettings.read('frameposition'))        

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

        # TODO Restore the previous view panel layout
        if restore:

            self.addViewPanel(views.OrthoPanel)

            viewPanel = self.getViewPanels()[0]

            # Set up a default for ortho views
            # layout (this will hopefully eventually
            # be restored from a saved state)
            import fsl.fsleyes.controls.overlaylistpanel as olp
            import fsl.fsleyes.controls.locationpanel    as lop

            viewPanel.togglePanel(olp.OverlayListPanel)
            viewPanel.togglePanel(lop.LocationPanel)

            
    def __makeMenuBar(self):
        """Constructs a bunch of menu items for this ``FSLEyesFrame``."""

        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

        fileMenu     = wx.Menu()
        viewMenu     = wx.Menu()
        settingsMenu = wx.Menu() 
 
        menuBar.Append(fileMenu,     'File')
        menuBar.Append(viewMenu,     'View')
        menuBar.Append(settingsMenu, 'Settings') 

        self.__fileMenu     = fileMenu
        self.__viewMenu     = viewMenu
        self.__settingsMenu = settingsMenu

        viewPanels = views   .listViewPanels()
        actionz    = actions .listGlobalActions()

        for action in actionz:
            menuItem = fileMenu.Append(wx.ID_ANY, strings.actions[action])
            
            actionObj = action(self.__overlayList, self.__displayCtx)

            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        for viewPanel in viewPanels:
            viewAction = viewMenu.Append(wx.ID_ANY, strings.titles[viewPanel]) 
            self.Bind(wx.EVT_MENU,
                      lambda ev, vp=viewPanel: self.addViewPanel(vp),
                      viewAction)
