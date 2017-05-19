#!/usr/bin/env python
#
# frame.py - A wx.Frame which implements a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLeyesFrame` which is the top level frame
for FSLeyes.
"""


from __future__ import division

import logging

import six

import wx
import wx.lib.agw.aui                     as aui

import fsl.utils.async                    as async
import fsl.utils.settings                 as fslsettings
from   fsl.utils.platform import platform as fslplatform
import fsleyes_widgets.dialog             as fsldlg
import fsleyes_widgets.utils.status       as status

import fsleyes.strings                    as strings
import fsleyes.autodisplay                as autodisplay
import fsleyes.profiles.shortcuts         as shortcuts

from . import actions
from . import tooltips
from . import perspectives
from . import displaycontext


log = logging.getLogger(__name__)


class FSLeyesFrame(wx.Frame):
    """A ``FSLeyesFrame`` is a simple :class:`wx.Frame` which acts as a
    container for :class:`.ViewPanel` instances.


    A :class:`wx.lib.agw.aui.AuiManager` is used so that ``ViewPanel`` panels
    can be dynamically laid out and reconfigured by the user.


    **Menus**


    The ``FSLeyesFrame`` has the following menus:

    ========== ==============================================================
    *FSLeyes*  General actions, such as help, quit, about.
    *File*     File actions such as adding a new overlay.
    *Overlay*  Actions for working with overlays.
    *View*     Options to open a new :class:`.ViewPanel`.
    *Settings* Options which are specific to the currently visible
               :class:`.ViewPanel` instances. A separate sub-menu is added
               for each visible ``ViewPanel``. All ``ViewPanel`` classes
               inherit from the :class:`.ActionProvider` class - any actions
               that have been defined are added as menu items here.
    ========== ==============================================================


    **Saving/restoring state**


    When a ``FSLeyesFrame`` is closed, it saves some display settings so that
    they can be restored the next time a ``FSLeyesFrame`` is opened. The
    settings are saved using the :class:`~fsl.utils.settings` module.
    Currently, the frame position, size, and layout (see the
    :mod:`.perspectives` module) are saved.


    **Programming interface**


    The ``FSLeyesFrame`` provides the following methods for programmatically
    configuring the display:

    .. autosummary::
       :nosignatures:

       getOverlayList
       getDisplayContext
       getViewPanels
       getViewPanelInfo
       getViewPanelID
       getViewPanelTitle
       getFocusedViewPanel
       addViewPanel
       viewPanelDefaultLayout
       removeViewPanel
       removeAllViewPanels
       getAuiManager
       refreshPerspectiveMenu
       runScript
       populateMenu
       Close


    **Actions**


    The :mod:`fsleyes.actions.frameactions` module contains some
    :mod:`.actions` which are monkey-patched into the ``FSLeyesFrame`` class.
    These actions are made available to the user via menu items and/or keyboard
    shortcuts.


    .. note:: All of the functions defined in the
              :mod:`fsleyes.actions.frameactions` module are treated as
              first-class methods of the ``FSLeyesFrame`` class (i.e. they are
              assumed to be present). They are only in a separate module to
              keep file sizes down.
    """


    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 restore=False,
                 save=True):
        """Create a ``FSLeyesFrame``.

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

        if fslplatform.wxPlatform == fslplatform.WX_GTK: font.SetPointSize(8)
        else:                                            font.SetPointSize(10)

        font.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.SetFont(font)

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))
        self.__mainPanel   = wx.Panel(self)
        self.__statusBar   = wx.StaticText(self)

        # Even though the FSLeyesFrame does not allow
        # panels to be floated, I am specifying the
        # docking guide style for complicated reasons...
        #
        # Each ViewPanel contained in this FSLeyesFrame
        # has an AuiManager of its own; these child
        # AuiManagers do support floating of their
        # child panels. However, it seems that when
        # a floating child panel of a ViewPanel is
        # docked, this top-level AuiManager is called
        # to draw the docking guides. This is because
        # the wx.lib.agw.aui.framemanager.GetManager
        # function uses the wx event handling system
        # to figure out which AuiManager should be used
        # to manage the docking (which is a ridiculous
        # way to do this, in my opinion).
        #
        # Anyway, this means that the docking guides
        # will be drawn according to the style set up
        # in this AuiManager, instead of the ViewPanel
        # AuiManager, which is the one that is actually
        # managing the panel being docked.
        #
        # This wouldn't be a problem, if not for the fact
        # that, when running over SSH/X11, the default
        # docking guides seem to get sized incorrectly,
        # and look terrible (probably related to the
        # AuiDockingGuide monkey-patch at the bottom of
        # viewpanel.py).
        #
        # This problem does not occur with the aero/
        # whidbey guides.
        self.__auiManager  = aui.AuiManager(
            self.__mainPanel,
            agwFlags=(aui.AUI_MGR_RECTANGLE_HINT          |
                      aui.AUI_MGR_NO_VENETIAN_BLINDS_FADE |
                      aui.AUI_MGR_AERO_DOCKING_GUIDES     |
                      aui.AUI_MGR_LIVE_RESIZE))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.__sizer.Add(self.__mainPanel, flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__statusBar, flag=wx.EXPAND)

        self.SetSizer(self.__sizer)

        # Re-direct status updates
        # to the status bar.
        def update(msg):

            # Do the update via wx.CallAfter to
            # make sure that the status bar is
            # updated on the main loop.
            def realUpdate():

                # This function might get called after
                # the status bar has been destroyed,
                # so we'll absorb any errors.
                try:
                    self.__statusBar.SetLabel(msg)
                    self.__statusBar.Refresh()
                    self.__statusBar.Update()
                except:
                    pass

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
        self.__viewPanels      = []
        self.__viewPanelDCs    = {}
        self.__viewPanelMenus  = {}
        self.__viewPanelIDs    = {}
        self.__viewPanelTitles = {}

        # Refs to menus
        self.__menuBar        = None
        self.__perspMenu      = None
        self.__recentPathMenu = None

        # The recent paths manager notifies us when
        # they change. See the __makeFileMenu and
        # __makeRecentPathsMenu methods
        import fsleyes.actions.loadoverlay as loadoverlay
        loadoverlay.recentPathManager.register(
            'FSLeyesFrame', self.__makeRecentPathsMenu)

        # This dictionary contains mappings of the form
        #
        #   { keyboard-shortcut : { ViewPanel : actionName } }
        #
        # See the __onViewPanelMenuItem method for details.
        self.__viewPanelShortcuts = {}

        self.__makeMenuBar()
        self.__restoreState(restore)

        # These flags control whether the user is
        # prompted before FSLeyes closes - they are
        # used in the Close and __onClose methods
        self.__saveLayout = save
        self.__askUnsaved = True

        self.__auiManager.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onViewPanelClose)
        self             .Bind(wx.EVT_CLOSE,           self.__onClose)

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.Layout()


    def getOverlayList(self):
        """Returns the :class:`.OverlayList` which contains the overlays
        being displayed by this ``FSLeyesFrame``.
        """
        return self.__overlayList


    def getDisplayContext(self):
        """Returns the top-level :class:`.DisplayContext` associated with this
        ``FSLeyesFrame``.
        """
        return self.__displayCtx


    def getViewPanels(self):
        """Returns a list of all :class:`.ViewPanel` instances that are
        currenlty displayed in this ``FSLeyesFrame``.
        """
        return list(self.__viewPanels)


    def getViewPanelID(self, viewPanel):
        """Returns the ID that was assigned to the given :class:`.ViewPanel`.
        This is a sequentially increasing integer, starting from 1.
        """
        return self.__viewPanelIDs[viewPanel]


    def getViewPanelTitle(self, viewPanel):
        """Returns the ID that was assigned to the given :class:`.ViewPanel`.
        This is a sequentially increasing integer, starting from 1.
        """
        return self.__viewPanelTitles[viewPanel]


    def getViewPanelInfo(self, viewPanel):
        """Returns the ``AuiPaneInfo`` class which contains layout information
        about the given :class:`.ViewPanel`.
        """
        return self.__auiManager.GetPane(viewPanel)


    def getAuiManager(self):
        """Returns the ``wx.lib.agw.aui.AuiManager` object which is managing
        the layout of this ``FSLeyesFrame``.
        """
        return self.__auiManager


    def removeViewPanel(self, viewPanel):
        """Removes the given :class:`.ViewPanel` from this ``FSLeyesFrame``.
        """

        paneInfo = self.__auiManager.GetPane(viewPanel)

        self.__onViewPanelClose(panel=viewPanel)

        self.__auiManager.ClosePane(paneInfo)
        self.__auiManager.Update()


    def getFocusedViewPanel(self):
        """Returns the :class:`.ViewPanel` which currently has focus, or
        ``None`` if no ``ViewPanel`` has focus.
        """
        import fsleyes.views.viewpanel as viewpanel

        focused = wx.Window.FindFocus()

        while focused is not None:

            if isinstance(focused, viewpanel.ViewPanel):
                return focused

            focused = focused.GetParent()
        return None


    def removeAllViewPanels(self):
        """Removes all view panels from this ``FSLeyesFrame``.

        .. note:: This method should be used to clear the frame, rather than
                  removing each :class:`.ViewPanel` individually via
                  :meth:`removeViewPanel`. This is because when one
                  ``ViewPanel`` is closed, the display settings of the
                  remaining ``ViewPanel`` instances may be modified.  If these
                  remaining ``ViewPanels`` are then immediately closed, thay
                  may not have had enough time to reconfigure themselves (e.g.
                  :class:`.GLVolume` instances re-creating their
                  :class:`.ImageTexture` instance due to a change in
                  :attr:`.DisplayContext.syncOverlayDisplay`), and ugly things
                  will happen (e.g. an :class:`.ImageTexture` trying to
                  configure itself *after* it has already been destroyed).

                  So just use this method instead.
        """
        for vp in list(self.__viewPanels):

            paneInfo = self.__auiManager.GetPane(vp)
            self.__onViewPanelClose(panel=vp, displaySync=False)
            self.__auiManager.ClosePane(paneInfo)

        self.__auiManager.Update()


    def addViewPanel(self, panelCls):
        """Adds a new :class:`.ViewPanel` to the centre of the frame, and a
        menu item allowing the user to configure the view.

        :arg panelCls: The :class:`.ViewPanel` type to be added.
        """
        import fsleyes.views.plotpanel  as plotpanel
        import fsleyes.views.shellpanel as shellpanel

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

        panel = panelCls(self.__mainPanel, self.__overlayList, childDC, self)

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

            # PlotPanels/ShellPanels are
            # initially placed along the
            # bottom
            if isinstance(panel, (plotpanel.PlotPanel, shellpanel.ShellPanel)):
                paneInfo.Bottom().BestSize(width // 4, height // 3)

            # Other panels (e.g. CanvasPanels)
            # are placed on the right
            else:
                paneInfo.Right().BestSize(width // 3, height // 4)

        self.__viewPanels.append(panel)
        self.__viewPanelDCs[     panel] = childDC
        self.__viewPanelIDs[     panel] = panelId
        self.__viewPanelTitles[  panel] = title

        self.__auiManager.AddPane(panel, paneInfo)
        self.__addViewPanelMenu(  panel, title)

        self.__configDisplaySync(panel)

        self.__auiManager.Update()

        return panel


    def viewPanelDefaultLayout(self, viewPanel):
        """After a :class:`.ViewPanel` is added via a menu item (see the
        :meth:`__makeViewPanelMenu` method), this a method is called to
        perform some basic initialisation on the panel. This basically amounts
        to adding toolbars.
        """

        from fsleyes.views.orthopanel         import OrthoPanel
        from fsleyes.views.lightboxpanel      import LightBoxPanel
        from fsleyes.views.timeseriespanel    import TimeSeriesPanel
        from fsleyes.views.histogrampanel     import HistogramPanel
        from fsleyes.views.powerspectrumpanel import PowerSpectrumPanel

        viewPanel.removeAllPanels()

        if isinstance(viewPanel, TimeSeriesPanel):
            viewPanel.toggleTimeSeriesToolBar()
            viewPanel.toggleOverlayList()
            viewPanel.togglePlotList()

        elif isinstance(viewPanel, HistogramPanel):
            viewPanel.toggleHistogramToolBar()
            viewPanel.toggleOverlayList()
            viewPanel.togglePlotList()

        elif isinstance(viewPanel, PowerSpectrumPanel):
            viewPanel.togglePowerSpectrumToolBar()
            viewPanel.toggleOverlayList()
            viewPanel.togglePlotList()

        elif isinstance(viewPanel, OrthoPanel):
            viewPanel.toggleDisplayToolBar()
            viewPanel.toggleOrthoToolBar()
            viewPanel.toggleOverlayList()
            viewPanel.toggleLocationPanel()

        elif isinstance(viewPanel, LightBoxPanel):
            viewPanel.toggleDisplayToolBar()
            viewPanel.toggleLightBoxToolBar()
            viewPanel.toggleOverlayList()
            viewPanel.toggleLocationPanel()


    def refreshPerspectiveMenu(self):
        """Re-creates the *View -> Perspectives* sub-menu. """
        self.__makePerspectiveMenu()


    def runScript(self, script=None):
        """Runs a custom python script, via a :class:`.RunScriptAction`. """

        from fsleyes.actions.runscript import RunScriptAction

        rsa = RunScriptAction(self.__overlayList, self.__displayCtx, self)

        rsa(script)


    def populateMenu(self, menu, target, actionNames=None, **kwargs):
        """Creates menu items for every :class:`.Action` available on the
        given ``target``, or for every named action in the ``actionNames``
        list.

        Called by the :meth:`__addViewPanelMenu` method to generate a menu
        for new :class:`.ViewPanel` instances, but can also be called for
        other purposes.

        :arg menu:        The ``wx.Menu`` to be populated.

        :arg target:      The object which has actions to be bound to the
                          menu items.

        :arg actionNames: If provided, only menu items for the actions named
                          in this list will be created. May contain ``None``,
                          which indicates that a menu separator should be
                          added at that point.

        All other keyword arguments are passed through to the
        :meth:`__onViewPanelMenuItem` method.
        """

        if actionNames is None:
            actionNames, actionObjs = list(zip(*target.getActions()))
        else:
            actionObjs = [target.getAction(name)
                          if name is not None else None
                          for name in actionNames]

        def configureActionItem(menu, actionName, actionObj):
            title    = strings  .actions.get((target, actionName), actionName)
            shortcut = shortcuts.actions.get((target, actionName))

            if shortcut is not None:
                title = '{}\t{}'.format(title, shortcut)

            if isinstance(actionObj, actions.ToggleAction):
                itemType = wx.ITEM_CHECK
            else:
                itemType = wx.ITEM_NORMAL

            menuItem = menu.Append(wx.ID_ANY, title, kind=itemType)

            # If this action can be called from a
            # keyboard shortcut, we save it in a
            # dictionary for reasons explained
            # in the __onViewPanelMenuItem method.
            #
            # We formalise the shortcut string to the
            # wx representation, so it is consistent
            # regardless of whatever we have put in
            # the fsleyes.profiles.shortcuts module.
            if shortcut is not None:

                shortcut     = menuItem.GetAccel().ToString()
                shortcutList = self.__viewPanelShortcuts.get(shortcut, {})

                shortcutList[target] = actionName

                self.__viewPanelShortcuts[shortcut] = shortcutList

            # The __onViewPanelMenuItem method
            # needs to know which view panel/action
            # is associated with each callback.
            def wrapper(ev, vp=target, aname=actionName, sc=shortcut):
                self.__onViewPanelMenuItem(vp, aname, sc, **kwargs)

            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem, wrapper)

        for actionName, actionObj in zip(actionNames, actionObjs):

            # If actionObj is None, this is a
            # hacky hint to insert a separator
            # - see ActionProvider.getActions.
            if actionObj is None:
                menu.AppendSeparator()
                continue

            # If actionObj is a list, this is a4
            # hacky hint to insert a sub-menu.
            elif isinstance(actionObj, list):
                names, objs = list(zip(*actionObj))
                currentMenu = wx.Menu()
                menu.AppendSubMenu(currentMenu, actionName)

            else:

                currentMenu = menu
                names       = [actionName]
                objs        = [actionObj]

            for name, obj in zip(names, objs):
                configureActionItem(currentMenu, name, obj)



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

        # Most of the work is
        # done in populateMenu
        self.populateMenu(menu, panel)

        # We add a 'Close' action to the
        # menu for every panel, but put
        # another separator before it
        if len(actionz) > 0:
            menu.AppendSeparator()

        title = strings.actions[self, 'removeFocusedViewPanel']
        shortcut = shortcuts.actions.get((self, 'removeFocusedViewPanel'))

        if shortcut is not None:
            title = '{}\t{}'.format(title, shortcut)

        closeItem = menu.Append(wx.ID_ANY, title)
        self.removeFocusedViewPanel.bindToWidget(self, wx.EVT_MENU, closeItem)


    def __onViewPanelMenuItem(self,
                              target,
                              actionName,
                              shortcut,
                              ignoreFocus=False,
                              runOnIdle=False):
        """Called when a menu item from a :class:`.ViewPanel` menu, or a menu
        otherwise created via :meth:`createMenu`, is selected, either via menu
        selection, or from a bound keyboard shortcut. This callback is
        configured in the :meth:`createMenu` method.

        :arg target:      The target instance for the action, most often a
                          :class:`.ViewPanel`.

        :arg actionName:  The name of the :class:`.Action` which is associated
                          with the menu item.

        :arg shortcut:    The keyboard shortcut code (see
                          ``wx.AcceleratorEntry.ToString``) associated with the
                          menu item, of ``None`` if there is no shortcut.

        :arg ignoreFocus: If ``True``, the action is executed on the
                          ``target``. Otherwise (the default), the action
                          is executed on the currently focused
                          :class:`.ViewPanel`.

        :arg runOnIdle:   If ``True``, the action is executed on the
                          ``async.idle`` loop. Otherwise (the default),
                          the action is executed on the calling thread.
        """

        # Hacky way to see if this menu item
        # callback was triggered via a keyboard
        # shortcut or via direct menu item
        # selection.
        keyDown = any((wx.GetKeyState(wx.WXK_CONTROL),
                       wx.GetKeyState(wx.WXK_ALT),
                       wx.GetKeyState(wx.WXK_SHIFT)))

        # If there is no keyboard shortcut associated
        # with this action, or the menu item was selected
        # directly, we just execute the action directly
        # on the target which is associated with the
        # menu.
        if ignoreFocus or shortcut is None or (not keyDown):
            func = target.getAction(actionName)
            if runOnIdle:
                async.idle(func)
            else:
                func()
            return

        # Otherwise we assume that the menu item was
        # triggered via a keyboard shortcut. In this case,
        # we want the currently focused ViewPanel to be
        # the receiver of the action callback.
        #
        # However, the same keyboard shortcut might be
        # used for different ViewPanel actions - for
        # example, Ctrl-Alt-1 might be bound to
        # toggleOverlayList on an OrthoPanel, but bound
        # to toggleTimeSeriesList on a TimeSeriesPanel.
        #
        # The idea is that, when the user presses such a
        # shortcut, the relevant action should be
        # executed on the currently focused ViewPanel
        # (if it has an action associated with the
        # shortcut).
        #
        # The __viewPanelShortcuts dictionary contains
        # mappings from keyboard shortcuts to ViewPanel
        # actions, so we can easily figure out which
        # ViewPanel/action to execute based on the
        # keyboard shortcut.

        viewPanel  = self.getFocusedViewPanel()
        actionName = self.__viewPanelShortcuts[shortcut].get(viewPanel, None)

        if actionName is None:
            return

        func = viewPanel.getAction(actionName)

        if runOnIdle:
            async.idle(func)
        else:
            func()


    def __onViewPanelClose(self, ev=None, panel=None, displaySync=True):
        """Called when the user closes a :class:`.ViewPanel`. May also
        be called programmatically via the :meth:`removeViewPanel` or
        :removeAllViewPanels` :method.

        The :meth:`__addViewPanelMenu` method adds a *Close* menu item
        for every view panel, and binds it to this method.

        This method does the following:

         1. Makes sure that the ``ViewPanel``: is destroyed correctly
         2. Removes the *Settings* sub-menu corresponding to the ``ViewPanel``.
         3. Makes sure that any remaining ``ViewPanel`` panels are arranged
            nicely.
         4. If the ``displaySync`` parameter is ``True``, calls
            :meth:`__configDisplaySync`.

        :arg ev:          ``wx`` event, passed when a :class:`.ViewPanel` is
                          closed by the user:

        :arg panel:       If called programmatically, the :class:`.ViewPanel`
                          to close.

        :arg displaySync: If ``True`` (the default), and only one ``ViewPanel``
                          remains after this one is removed, that remaining
                          ``ViewPanel`` is synchronised to the master
                          :class:`.DisplayContext`.
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

        self       .__viewPanels     .remove(panel)
        self       .__viewPanelIDs   .pop(   panel)
        self       .__viewPanelTitles.pop(   panel)
        dctx = self.__viewPanelDCs   .pop(   panel)
        menu = self.__viewPanelMenus .pop(   panel, None)

        log.debug('Destroying {} ({}) and '
                  'associated DisplayContext ({})'.format(
                      type(panel).__name__,
                      id(panel),
                      id(dctx)))

        # Remove the view panel menu
        if menu is not None:
            self.__settingsMenu.Remove(menu.GetId())

        # Calling fslpanel.FSLeyesPanel.destroy()
        # and DisplayContext.destroy() - the
        # AUIManager should do the
        # wx.Window.Destroy side of things ...
        panel.destroy()
        dctx .destroy()

        # If the removed panel was the centre
        # pane, move another panel to the centre
        numPanels = len(self.__viewPanels)
        wasCentre = paneInfo.dock_direction_get() == aui.AUI_DOCK_CENTRE

        if numPanels >= 1 and wasCentre:
            paneInfo = self.__auiManager.GetPane(self.__viewPanels[0])
            paneInfo.Centre()

        # If there is only one panel
        # left, hide its title bar
        if numPanels == 1:
            paneInfo = self.__auiManager.GetPane(self.__viewPanels[0])
            paneInfo.Dockable(False).CaptionVisible(False)

        if displaySync:
            self.__configDisplaySync()


    def __configDisplaySync(self, newPanel=None):
        """Called by :meth:`addViewPanel` and :meth:`__onViewPanelClose`.

        This method ensures that at the display properties and overlay order
        for the :class:`.DisplayContext` of at least least one
        :class:`.CanvasPanel` is synced to the master
        :class:`.DisplayContext`.

        :arg newPanel: If this method has been called as a result of a new
                       :class:`.ViewPanel` being added, a reference to the
                       new panel.
        """

        import fsleyes.views.canvaspanel as canvaspanel

        canvasPanels = [vp for vp in self.__viewPanels
                        if isinstance(vp, canvaspanel.CanvasPanel)]
        canvasCtxs   = [c.getDisplayContext() for c in canvasPanels]
        numCanvases  = len(canvasPanels)

        # We only care about
        # canvas panels.
        if numCanvases == 0:
            return

        # Is there at least one canvas panel
        # which has display properties/overlay
        # order synced to the master display
        # context?
        displaySynced = any([c.syncOverlayDisplay
                             for c in canvasCtxs
                             if c is not newPanel])
        orderSynced   = any([c.isSyncedToParent('overlayOrder')
                             for c in canvasCtxs
                             if c is not newPanel])

        # If there is only one CanvasPanel
        # open, sync its overlay display
        # properties to the master context
        if numCanvases == 1:
            childDC = canvasPanels[0].getDisplayContext()
            childDC.syncToParent('overlayOrder')
            childDC.syncOverlayDisplay = True

        # If an existing canvas panel is
        # already synced to the master,
        # then we set the new panel to
        # be unsynced
        elif displaySynced and orderSynced:
            if newPanel is not None:
                childDC = newPanel.getDisplayContext()
                childDC.syncOverlayDisplay = False
                childDC.unsyncFromParent('overlayOrder')

        # If no existing CanvasPanels are
        # synced to the master context,
        # re-sync the most recently added
        # one.
        else:
            if newPanel is not None: panel = newPanel
            else:                    panel = canvasPanels[0]
            childDC = panel.getDisplayContext()

            # Make sure that the parent context
            # inherits the values from this context
            displays = [childDC.getDisplay(o) for o in self.__overlayList]

            childDC.setBindingDirection(False)

            for display in displays:
                opts = display.getDisplayOpts()
                display.setBindingDirection(False)
                opts   .setBindingDirection(False)

            childDC.syncOverlayDisplay = True
            childDC.syncToParent('overlayOrder')

            # Reset the binding directiona
            childDC.setBindingDirection(True)

            for display in displays:
                opts = display.getDisplayOpts()
                display.setBindingDirection(True)
                opts   .setBindingDirection(True)


    def Close(self, **kwargs):
        """Closes this ``FSLeyesFrame``. See :meth:`__onClose`.

        :arg askUnsaved: Defaults to ``True``. If ``False``, the user is not
                         asked whether they want to save any unsaved overlays.

        :arg askLayout:  Defaults to the ``save`` value passed to
                         :meth:`__init__`. Controls whether the user is asked
                         if they want to save the current layout.
        """

        askUnsaved = kwargs.pop('askUnsaved', True)
        askLayout  = kwargs.pop('askLayout',  self.__saveLayout)

        self.__askUnsaved = askUnsaved
        self.__saveLayout = askLayout

        super(FSLeyesFrame, self).Close()


    def __onClose(self, ev):
        """Called when the user closes this ``FSLeyesFrame``.

        Saves the frame position, size, and layout, so it may be preserved the
        next time it is opened. See the :meth:`_restoreState` method.
        """

        ev.Skip()

        import fsleyes.actions.saveoverlay as saveoverlay

        # Check to see if there are any unsaved images
        allSaved = saveoverlay.checkOverlaySaveState(
            self.__overlayList, self.__displayCtx)

        # If there are, get the
        # user to confirm quit
        if not allSaved and self.__askUnsaved:

            msg   = strings.messages[self, 'unsavedOverlays']
            title = strings.titles[  self, 'unsavedOverlays']

            dlg = wx.MessageDialog(self,
                                   message=msg,
                                   caption=title,
                                   style=(wx.YES_NO        |
                                          wx.NO_DEFAULT    |
                                          wx.CENTRE        |
                                          wx.ICON_WARNING))

            dlg.CentreOnParent()
            if dlg.ShowModal() == wx.ID_NO:
                ev.Skip(False)
                ev.Veto()
                return

        if self.__saveLayout:

            # Ask the user if they want to save the layout,
            # as some people might not like the previous
            # layout being restored on startup.
            save      = fslsettings.read('fsleyes.frame.saveLayout',      True)
            askToSave = fslsettings.read('fsleyes.frame.askToSaveLayout', True)

            if askToSave:

                # Give the user the option of suppressing
                # this dialog forever more
                dlg = fsldlg.CheckBoxMessageDialog(
                    self,
                    strings.titles[self, 'saveLayout'],
                    message=strings.messages[self, 'saveLayout'],
                    cbMessages=[strings.messages[self, 'dontAskToSaveLayout']],
                    cbStates=[False],
                    yesText='Yes',
                    noText='No',
                    cancelText='Cancel',
                    focus='no',
                    icon=wx.ICON_QUESTION)

                result = dlg.ShowModal()

                if result == wx.ID_CANCEL:
                    ev.Skip(False)
                    ev.Veto()
                    return

                save = result == wx.ID_YES

                fslsettings.write('fsleyes.frame.saveLayout', save)
                fslsettings.write('fsleyes.frame.askToSaveLayout',
                                  not dlg.CheckBoxState())

            if save:
                layout   = perspectives.serialisePerspective(self)
                size     = self.GetSize().Get()
                position = self.GetScreenPosition().Get()

                log.debug('Saving size: {}'    .format(size))
                log.debug('Saving position: {}'.format(position))
                log.debug('Saving layout: {}'  .format(layout))

                fslsettings.write('fsleyes.frame.size',     size)
                fslsettings.write('fsleyes.frame.position', position)
                fslsettings.write('fsleyes.frame.layout',   layout)
            else:
                fslsettings.delete('fsleyes.frame.size')
                fslsettings.delete('fsleyes.frame.position')
                fslsettings.delete('fsleyes.frame.layout')

        # It's nice to explicitly clean
        # up our FSLeyesPanels, otherwise
        # they'll probably complain
        for panel in self.__viewPanels:
            panel.destroy()


    def __restoreState(self, restore):
        """Called by :meth:`__init__`.

        If any frame size/layout properties have previously been saved via the
        :mod:`~fsl.utils.settings` module, they are read in, and applied to
        this frame.

        :arg restore: If ``False``, any saved layout state is ignored.
        """

        from operator import itemgetter as iget

        # Restore the saved frame size/position
        size     = fslsettings.read('fsleyes.frame.size')
        position = fslsettings.read('fsleyes.frame.position')
        layout   = fslsettings.read('fsleyes.frame.layout')

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
            if ratio < 0.9:

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
                        'fsleyes.frame.layout',
                        layout,
                        message=strings.messages[self, 'restoringLayout'])
                except:
                    log.warn('Previous layout could not be restored - '
                             'falling back to default layout.')
                    log.debug('Layout restore error', exc_info=True)
                    layout = None

            if layout is None:
                perspectives.loadPerspective(self, 'default')


    def __makeMenuBar(self):
        """Constructs a bunch of menu items for this ``FSLeyesFrame``."""

        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

        # The menu bar on OSX/wxPython is a bit different
        # than the menu bar on OSX/wxPhoenix, or on Linux.
        # This is because under OSX/wxPython, we can't get
        # access to the built-in application menu.
        onOSX       = fslplatform.wxPlatform in (fslplatform.WX_MAC_CARBON,
                                                 fslplatform.WX_MAC_COCOA)
        haveAppMenu = (onOSX and
                       fslplatform.wxFlavour == fslplatform.WX_PHOENIX)

        # On linux, we create a FSLeyes menu
        if not onOSX:
            fsleyesMenu = wx.Menu()
            menuBar.Append(fsleyesMenu, 'FSLeyes')

        # On OSX/wxPhoenix, we can
        # get the built-in app menu
        elif haveAppMenu:
            fsleyesMenu = menuBar.OSXGetAppleMenu()

        # On OSX/wxPython, we fudge
        # things a bit - see below.
        else:
            fsleyesMenu = None

        fileMenu        = wx.Menu()
        overlayMenu     = wx.Menu()
        viewMenu        = wx.Menu()
        perspectiveMenu = wx.Menu()
        settingsMenu    = wx.Menu()

        self.__menuBar   = menuBar
        self.__perspMenu = perspectiveMenu

        menuBar.Append(fileMenu,     'File')
        menuBar.Append(overlayMenu,  'Overlay')
        menuBar.Append(viewMenu,     'View')
        menuBar.Append(settingsMenu, 'Settings')

        self.__fsleyesMenu  = fsleyesMenu
        self.__overlayMenu  = overlayMenu
        self.__fileMenu     = fileMenu
        self.__viewMenu     = viewMenu
        self.__settingsMenu = settingsMenu

        self.__makeFileMenu(fileMenu)

        # We have a FSLeyes menu
        if fsleyesMenu is not None:
            self.__makeFSLeyesMenu(fsleyesMenu)

        # We don't have a FSLeyes menu -
        # throw all of the FSLeyes menu
        # stuff onto the end of the File
        # menu.
        else:
            fileMenu.AppendSeparator()
            self.__makeFSLeyesMenu(fileMenu)

        self.__makeOverlayMenu(overlayMenu)

        self.__makeViewPanelMenu(viewMenu)

        # Perspectives
        viewMenu.AppendSeparator()
        viewMenu.AppendSubMenu(perspectiveMenu, 'Perspectives')
        self.__makePerspectiveMenu()


    def __makeFSLeyesMenu(self, menu):
        """Called by :meth:`__makeMenuBar`. Creates the *FSLeyes* menu. """

        overlayList = self.__overlayList
        displayCtx  = self.__displayCtx

        from fsleyes.actions.about            import AboutAction
        from fsleyes.actions.diagnosticreport import DiagnosticReportAction
        from fsleyes.actions.clearsettings    import ClearSettingsAction
        from fsleyes.actions.updatecheck      import UpdateCheckAction

        fsleyesActions = [
            (AboutAction(overlayList, displayCtx, self),
             strings.actions[      AboutAction],
             shortcuts.actions.get(AboutAction),
             wx.ID_ABOUT),
            (DiagnosticReportAction(overlayList, displayCtx, self),
             strings.actions[      DiagnosticReportAction],
             shortcuts.actions.get(DiagnosticReportAction),
             wx.ID_ANY),
            (ClearSettingsAction(overlayList, displayCtx, self),
             strings.actions[ClearSettingsAction],
             None,
             wx.ID_ANY),
            (UpdateCheckAction(),
             strings.actions[      UpdateCheckAction],
             shortcuts.actions.get(UpdateCheckAction),
             wx.ID_ANY),
            (self.openHelp,
             strings.actions[       self, 'openHelp'],
             shortcuts.actions.get((self, 'openHelp')),
             wx.ID_HELP),
            (self.closeFSLeyes,
             strings.actions[       self, 'closeFSLeyes'],
             shortcuts.actions.get((self, 'closeFSLeyes')),
             wx.ID_EXIT)]

        for action, title, shortcut, wxid in fsleyesActions:

            if shortcut is None: shortcut = ''
            else:                shortcut = '\t{}'.format(shortcut)

            title = '{}{}'.format(title, shortcut)

            item = menu.Append(wxid, title)
            action.bindToWidget(self, wx.EVT_MENU, item)


    def __makeFileMenu(self, menu):
        """Called by :meth:`__makeMenuBar`. Creates the *File* menu. """

        from fsleyes.actions.loadoverlay        import LoadOverlayAction
        from fsleyes.actions.loadoverlayfromdir import LoadOverlayFromDirAction
        from fsleyes.actions.loadstandard       import LoadStandardAction
        from fsleyes.actions.loadatlas          import LoadAtlasAction
        from fsleyes.actions.runscript          import RunScriptAction

        fileActions = [LoadOverlayAction,
                       LoadOverlayFromDirAction,
                       LoadStandardAction,
                       LoadAtlasAction,
                       RunScriptAction]

        for action in fileActions:

            if action == 'sep':
                menu.AppendSeparator()
                continue

            title    = strings.actions[  action]
            shortcut = shortcuts.actions.get(action)

            if shortcut is not None:
                title = '{}\t{}'.format(title, shortcut)

            menuItem  = menu.Append(wx.ID_ANY, title)
            actionObj = action(self.__overlayList, self.__displayCtx, self)

            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        # The last option in the file
        # menu is a 'Recent files' list.
        # The list gets populated when
        # it is clicked.
        self.__recentPathsMenu = wx.Menu()
        menu.AppendSubMenu(self.__recentPathsMenu,
                           strings.labels[self, 'recentPathsMenu'])
        self.__makeRecentPathsMenu()


    def __makeRecentPathsMenu(self, *a):
        """Populates the "File -> Recent files" menu. This method is called
        by the :meth:`__makeFileMenu`, and also by the
        :class:`.RecentPathManager` when paths are added.
        """

        import fsleyes.actions.loadoverlay as loadoverlay

        for path in self.__recentPathsMenu.GetMenuItems():
            # RemoveItem is deprecated in phoenix
            if fslplatform.wxFlavour == fslplatform.WX_PHOENIX:
                self.__recentPathsMenu.Remove(path)
            else:
                self.__recentPathsMenu.RemoveItem(path)

        paths = loadoverlay.recentPathManager.listRecentPaths()

        # We give each recent file menu item an identifying
        # number from 1-(numpaths) - this is used by the
        # __onRecentPath handler.
        for i, p in enumerate(paths, start=1):
            menuItem = self.__recentPathsMenu.Append(i, p)
            self.Bind(wx.EVT_MENU, self.__onRecentPath, menuItem)


    def __onRecentPath(self, ev):
        """Called when a recent path is selected from the
        "File -> Recent files" menu item. Loads the path.
        See the :meth:`__makeRecentPathsMenu` method.
        """

        import fsleyes.actions.loadoverlay as loadoverlay

        path = self.__recentPathsMenu.GetLabel(ev.GetId())

        def onLoad(overlays):

            if len(overlays) == 0:
                return

            self.__overlayList.extend(overlays)

            self.__displayCtx.selectedOverlay = \
                self.__displayCtx.overlayOrder[-1]

            if self.__displayCtx.autoDisplay:
                for overlay in overlays:
                    autodisplay.autoDisplay(overlay,
                                            self.__overlayList,
                                            self.__displayCtx)

        loadoverlay.loadOverlays([path],
                                 onLoad=onLoad,
                                 inmem=self.__displayCtx.loadInMemory)


    def __makeViewPanelMenu(self, menu):
        """Called by :meth:`__makeMenuBar`. Creates the view panel menu. """

        # Shortcuts to open a new view panel
        vpActions = [self.addOrthoPanel,
                     self.addLightBoxPanel,
                     self.addTimeSeriesPanel,
                     self.addHistogramPanel,
                     self.addPowerSpectrumPanel,
                     self.addShellPanel]

        for action in vpActions:

            shortcut = shortcuts.actions.get((self, action.__name__))

            if shortcut is None: shortcut = ''
            else:                shortcut = '\t{}'.format(shortcut)

            title = '{}{}'.format(strings.actions[self, action.__name__],
                                  shortcut)

            item = menu.Append(wx.ID_ANY, title)
            self.Bind(wx.EVT_MENU, action, item)


    def __makePerspectiveMenu(self):
        """Called by :meth:`__makeMenuBar` and :meth:`refreshPerspectiveMenu`.
        Re-creates the *View->Perspectives* menu.
        """

        from fsleyes.actions.loadperspective  import LoadPerspectiveAction
        from fsleyes.actions.saveperspective  import SavePerspectiveAction
        from fsleyes.actions.clearperspective import ClearPerspectiveAction

        perspMenu = self.__perspMenu

        # Remove any existing menu items
        for item in perspMenu.GetMenuItems():
            perspMenu.Delete(item.GetId())

        builtIns = list(perspectives.BUILT_IN_PERSPECTIVES.keys())
        saved    = perspectives.getAllPerspectives()

        # Add a menu item to load each built-in perspectives
        for persp in builtIns:

            title    = strings.perspectives.get(persp, persp)
            shortcut = shortcuts.actions.get((self, 'perspectives', persp),
                                             None)

            if shortcut is not None:
                title = '{}\t{}'.format(title, shortcut)

            menuItem = perspMenu.Append(wx.ID_ANY, title)

            actionObj = LoadPerspectiveAction(self, persp)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        if len(builtIns) > 0:
            perspMenu.AppendSeparator()

        # Add a menu item to load each saved perspective
        for persp in saved:

            menuItem  = perspMenu.Append(
                wx.ID_ANY, strings.perspectives.get(persp, persp))
            actionObj = LoadPerspectiveAction(self, persp)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

        # Add menu items for other perspective
        # operations, but separate them from the
        # existing perspectives
        if len(saved) > 0:
            perspMenu.AppendSeparator()

        # TODO: Delete a single perspective?
        #       Save to/load from file?
        perspActions = [SavePerspectiveAction,
                        ClearPerspectiveAction]

        for pa in perspActions:

            actionObj     = pa(self)
            perspMenuItem = perspMenu.Append(wx.ID_ANY, strings.actions[pa])

            actionObj.bindToWidget(self, wx.EVT_MENU, perspMenuItem)


    def __makeOverlayMenu(self, menu):
        """Called by :meth:`__makeMenuBar`. Creates/configures the *Overlay*
        menu.
        """

        from fsleyes.actions.removealloverlays import RemoveAllOverlaysAction
        from fsleyes.actions.copyoverlay       import CopyOverlayAction
        from fsleyes.actions.saveoverlay       import SaveOverlayAction
        from fsleyes.actions.reloadoverlay     import ReloadOverlayAction
        from fsleyes.actions.removeoverlay     import RemoveOverlayAction
        from fsleyes.actions.correlate         import PearsonCorrelateAction
        from fsleyes.actions.applyflirtxfm     import ApplyFlirtXfmAction
        from fsleyes.actions.saveflirtxfm      import SaveFlirtXfmAction

        fileActions = ['selectNextOverlay',
                       'selectPreviousOverlay',
                       RemoveAllOverlaysAction,
                       'sep',
                       'name',
                       CopyOverlayAction,
                       SaveOverlayAction,
                       ReloadOverlayAction,
                       RemoveOverlayAction,
                       'toggleOverlayVisibility',
                       'sep',
                       PearsonCorrelateAction,
                       ApplyFlirtXfmAction,
                       SaveFlirtXfmAction]

        for action in fileActions:

            # A dummy menu item which contains the
            # name of the currently selected overlay.
            if action == 'name':
                self.__overlayNameMenuItem = menu.Append(wx.ID_ANY, '<')
                self.__overlayNameMenuItem.Enable(False)
                continue

            if action == 'sep':

                menu.AppendSeparator()
                continue

            # Method on this FSLeyesFrame
            if isinstance(action, six.string_types):

                title     = strings.actions[  self, action]
                shortcut  = shortcuts.actions.get((self, action))
                actionObj = getattr(self, action)

            # Action class
            else:
                title     = strings.actions[  action]
                shortcut  = shortcuts.actions.get(action)
                actionObj = action(self.__overlayList, self.__displayCtx, self)

            if shortcut is not None:
                title = '{}\t{}'.format(title, shortcut)

            menuItem = menu.Append(wx.ID_ANY, title)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay`, or
        when the :attr:`.Display.name` property of the currently selected
        overlay changes. Updates the overlay name item in the *Overlay*
        menu*.
        """

        oldDisplay = getattr(self, '__display', None)

        if oldDisplay is not None:
            oldDisplay.removeListener('name', self.__name)
            self.__display = None

        overlay = self.__displayCtx.getSelectedOverlay()

        haveOverlays = overlay is not None

        self.selectNextOverlay      .enabled = haveOverlays
        self.selectPreviousOverlay  .enabled = haveOverlays
        self.toggleOverlayVisibility.enabled = haveOverlays

        if haveOverlays:

            self.__display = self.__displayCtx.getDisplay(overlay)
            name = self.__display.name

            if name is None: name = ''
            else:            name = name.strip()

            if name == '':
                name = strings.labels[self, 'noName']
            self.__overlayNameMenuItem.SetText(name)

            if not self.__display.hasListener('name', self.__name):
                self.__display.addListener('name',
                                           self.__name,
                                           self.__selectedOverlayChanged)
        else:
            name = strings.labels[self, 'noOverlays']
            self.__overlayNameMenuItem.SetText(name)
