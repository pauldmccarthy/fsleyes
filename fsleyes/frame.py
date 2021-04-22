#!/usr/bin/env python
#
# frame.py - A wx.Frame which implements a 3D image viewer.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Taylor Hanayik <taylor.hanayik@ndcn.ox.ac.uk>
#
"""This module provides the :class:`FSLeyesFrame` which is the top level frame
for FSLeyes.
"""


from __future__ import division

import functools as ft
import itertools as it
import              logging

from typing import Type

import wx
import wx.lib.agw.aui               as aui

import fsl.utils.idle               as idle
import fsl.utils.settings           as fslsettings
import fsleyes_widgets              as fwidgets
import fsleyes_widgets.dialog       as fsldlg
import fsleyes_widgets.utils.status as status

import fsleyes.strings              as strings
import fsleyes.plugins              as plugins
import fsleyes.autodisplay          as autodisplay
import fsleyes.profiles.shortcuts   as shortcuts
import fsleyes.views.viewpanel      as viewpanel
import fsleyes.actions              as actions
import fsleyes.tooltips             as tooltips
import fsleyes.layouts              as layouts
import fsleyes.displaycontext       as displaycontext


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
    *Tools*    Options which invoke some sort of tool - some global tools are
               added to this menu, along with tools that are specific to each
               active view.
    ========== ==============================================================


    **Saving/restoring state**


    When a ``FSLeyesFrame`` is closed, it saves some display settings so that
    they can be restored the next time a ``FSLeyesFrame`` is opened. The
    settings are saved using the :class:`~fsl.utils.settings` module.
    Currently, the frame position, size, and layout (see the
    :mod:`.layout` module) are saved.


    **Programming interface**


    The ``FSLeyesFrame`` provides the following properties and methods for
    programmatically configuring the display:

    .. autosummary::
       :nosignatures:

       overlayList
       displayCtx
       viewPanels
       focusedViewPanel
       auiManager
       getViewPanelInfo
       getViewPanelID
       getViewPanelTitle
       addViewPanel
       viewPanelDefaultLayout
       removeViewPanel
       removeAllViewPanels
       refreshViewMenu
       refreshLayoutMenu
       refreshSettingsMenu
       refreshToolsMenu
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
                 save=True,
                 fontSize=None,
                 menu=True,
                 closeHandlers=None):
        """Create a ``FSLeyesFrame``.

        :arg parent:        The :mod:`wx` parent object.

        :arg overlayList:   The :class:`.OverlayList`.

        :arg displayCtx:    The master :class:`.DisplayContext`.

        :arg restore:       Restores previous saved layout. If ``False``, no
                            view panels will be displayed.

        :arg save:          Save current layout when closed.

        :arg fontSize:      Application-wide font size to use. Defaults to 10.

        :arg menu:          Whether or not to create a menu bar.

        :arg closeHandlers: List of functions to call when this
                            ``FSLeyesFrame`` is closing. Use this rather than
                            binding to the ``EVT_CLOSE`` event, so that the
                            ``FSLeyesFrame`` can guarantee that your handler
                            will be called when it is actually closing.
                            Otherwise the user might cancel the close, but
                            your handler will still get called.
        """
        wx.Frame.__init__(self, parent, title='FSLeyes')
        tooltips.initTooltips()

        # Default application font - this is
        # inherited by all child controls.
        font = self.GetFont()

        if fontSize is None:
            fontSize = 10

        font.SetPointSize(fontSize)
        font.SetWeight(wx.FONTWEIGHT_NORMAL)
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

        self.__auiManager.SetDockSizeConstraint(0.5, 0.5)

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
                except Exception:
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
        self.__haveMenu       = menu
        self.__menuBar        = None
        self.__fsleyesMenu    = None
        self.__overlayMenu    = None
        self.__fileMenu       = None
        self.__viewMenu       = None
        self.__layoutMenu     = None
        self.__settingsMenu   = None
        self.__toolsMenu      = None
        self.__recentPathMenu = None

        # Refs to Action objects that are managed
        # by this FSLeyesFrame, and are bound to
        # menu options, as { type : instance }
        # mappings. This includes items in the
        # File, Overlay, View, and Tools menus
        self.__menuActions = {}

        # We keep refs to the (Action, wx.MenuItem)
        # pairs for each menu, because when a menu
        # gets destroyed, we need to unbind the action
        # from the item
        self.__viewMenuActions      = []
        self.__viewPanelMenuActions = {}
        self.__layoutMenuActions    = []
        self.__overlayMenuActions   = []
        self.__toolsMenuActions     = []

        # The recent paths manager notifies us when
        # they change. See the __makeFileMenu and
        # __makeRecentPathsMenu methods
        import fsleyes.actions.loadoverlay as loadoverlay
        loadoverlay.recentPathManager.register(
            self.__name, self.__makeRecentPathsMenu)

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

        # Event handlers are called in order of
        # last bound first, first bound last.
        # Our __onClose handler may veto the
        # close (if the user cancels it), so
        # we have to bind our handler last.
        if closeHandlers is not None:
            for h in closeHandlers:
                self.Bind(wx.EVT_CLOSE, h)

        self.Bind(wx.EVT_CLOSE, self.__onClose)

        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.Layout()


    @property
    def overlayList(self):
        """Returns the :class:`.OverlayList` which contains the overlays
        being displayed by this ``FSLeyesFrame``.
        """
        return self.__overlayList


    @property
    def displayCtx(self):
        """Returns the top-level :class:`.DisplayContext` associated with this
        ``FSLeyesFrame``.
        """
        return self.__displayCtx


    @property
    def viewPanels(self):
        """Returns a list of all :class:`.ViewPanel` instances that are
        currenlty displayed in this ``FSLeyesFrame``.
        """
        return list(self.__viewPanels)


    @property
    def focusedViewPanel(self):
        """Returns the :class:`.ViewPanel` which currently has focus,
        the first ``ViewPanel`` if none have focus, or ``None`` if there
        are no ``ViewPanels``.
        """

        if len(self.viewPanels) == 0:
            return None

        focused = wx.Window.FindFocus()

        while focused is not None:

            if isinstance(focused, viewpanel.ViewPanel):
                return focused

            focused = focused.GetParent()

        return self.viewPanels[0]


    @property
    def menuActions(self):
        """Returns a dictionary containing all global :class:`.Action` objects
        that are bound to menu items.
        """
        return dict(self.__menuActions)


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


    @property
    def auiManager(self):
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


    def addViewPanel(
            self,
            panelCls      : Type[viewpanel.ViewPanel],
            title         : str  = None,
            defaultLayout : bool = True,
            **kwargs) -> viewpanel.ViewPanel:
        """Adds a new :class:`.ViewPanel` to the centre of the frame, and a
        menu item allowing the user to configure the view.

        :arg panelCls:      The :class:`.ViewPanel` type to be added.

        :arg title:         Title to give the view. If not provided, it is
                            assumed that a name is present for the view type
                            in :attr:`.strings.titles`.

        :arg defaultLayout: If ``True`` (the default),
                            :meth:`viewPanelDefaultLayout` is called, to add
                            a default set of control panels to the view.

        :returns: The newly created ``ViewPanel``.

        All other arguments are passed to the ``__init__`` method of the child
        :class:`.DisplayContext` that is created for the new view.
        """
        import fsleyes.views.plotpanel  as plotpanel
        import fsleyes.views.shellpanel as shellpanel

        if title is None:
            title = panelCls.title()
        if title is None:
            title = strings.titles.get(panelCls, panelCls.__name__)

        if len(self.__viewPanelIDs) == 0:
            panelId = 1
        else:
            panelId = max(self.__viewPanelIDs.values()) + 1

        # The PaneInfo Name contains the panel
        # class name - this is used for saving
        # and restoring layouts .
        name  = '{} {}'.format(panelCls.__name__, panelId)
        title = '{} {}'.format(title,             panelId)

        childDC = displaycontext.DisplayContext(
            self.__overlayList,
            parent=self.__displayCtx,
            **kwargs)

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

            # PlotPanels are initially
            # placed along the bottom
            if isinstance(panel, plotpanel.PlotPanel):
                paneInfo.Bottom().BestSize(width, height // 3)

            # As are ShellPanels, albeit
            # a bit smaller
            elif isinstance(panel, shellpanel.ShellPanel):
                paneInfo.Bottom().BestSize(width, height // 5)

            # Other panels (e.g. CanvasPanels)
            # are placed on the right
            else:
                paneInfo.Right().BestSize(width // 2, height)

        self.__viewPanels.append(panel)
        self.__viewPanelDCs[     panel] = childDC
        self.__viewPanelIDs[     panel] = panelId
        self.__viewPanelTitles[  panel] = title

        menu, actionItems = self.__addViewPanelMenu(  panel, title)
        self.__viewPanelMenus[      panel] = menu
        self.__viewPanelMenuActions[panel] = actionItems

        self.__auiManager.AddPane(panel, paneInfo)
        self.__configDisplaySync(panel)
        self.__auiManager.Update()
        self.__enableMenus(True)

        if defaultLayout:
            self.viewPanelDefaultLayout(panel)

        return panel


    def viewPanelDefaultLayout(self, viewPanel : viewpanel.ViewPanel):
        """After a :class:`.ViewPanel` is added via the view menu, this method
        is called to perform some basic initialisation on the panel. This
        basically amounts to adding toolbars.
        """

        viewPanel.removeAllPanels()
        ctrls = viewPanel.defaultLayout()
        if ctrls is None:
            return

        ctrls = [plugins.lookupControl(c) for c in ctrls]

        for ctrl in ctrls:
            viewPanel.togglePanel(ctrl)


    def refreshViewMenu(self):
        """Re-creates the *View* menu."""

        if not self.__haveMenu:
            return

        viewMenu = self.__viewMenu
        items    = self.__viewMenuActions

        for action, item in items:
            action.unbindWidget(item)

        for item in viewMenu.GetMenuItems():
            viewMenu.Delete(item.GetId())

        self.__viewMenuActions = self.__makeViewMenu()
        self.refreshLayoutMenu()


    def refreshLayoutMenu(self):
        """Re-creates the *View -> Layouts* sub-menu. """

        if not self.__haveMenu:
            return

        for action, item in self.__layoutMenuActions:
            action.unbindWidget(item)
            action.destroy()

        for item in self.__layoutMenu.GetMenuItems():
            self.__layoutMenu.Delete(item.GetId())

        self.__layoutMenuActions = self.__makeLayoutMenu()


    def refreshSettingsMenu(self):
        """Re-creates the *Settings* menu. """

        if not self.__haveMenu:
            return

        for action, item in it.chain(*self.__viewPanelMenuActions.values()):
            action.unbindWidget(item)

        for menu in self.__viewPanelMenus.values():
            menu = menu.GetSubMenu()
            for item in menu.GetMenuItems():
                menu.Delete(item.GetId())

        for item in self.__settingsMenu.GetMenuItems():
            self.__settingsMenu.Delete(item.GetId())

        self.__viewPanelMenus       = {}
        self.__viewPanelMenuActions = {}
        for panel, title in self.__viewPanelTitles.items():

            menu, actionItems = self.__addViewPanelMenu(panel, title)

            self.__viewPanelMenus[      panel] = menu
            self.__viewPanelMenuActions[panel] = actionItems


    def refreshToolsMenu(self):
        """Re-creates the *Tools* menu. """

        if not self.__haveMenu:
            return

        menu  = self.__toolsMenu
        items = self.__toolsMenuActions

        for action, item in items:
            action.unbindWidget(item)

        # all items from self.__toolMenuActions
        # will also be returned by GetMenuItems,
        # along with other things (e.g. section
        # dividers)
        for item in menu.GetMenuItems():
            menu.Delete(item.GetId())

        self.__toolsMenuActions = self.__makeToolsMenu()


    def populateMenu(self,
                     menu,
                     target,
                     actionNames=None,
                     actionTitles=None,
                     **kwargs):
        """Creates menu items for every :class:`.Action` available on the
        given ``target``, or for every named action in the ``actionNames``
        list.

        Called by the :meth:`__addViewPanelMenu` method to generate a menu
        for new :class:`.ViewPanel` instances, but can also be called for
        other purposes.

        :arg menu:         The ``wx.Menu`` to be populated.

        :arg target:       The object which has actions to be bound to the
                           menu items.

        :arg actionNames:  If provided, only menu items for the actions named
                           in this list will be created. May contain ``None``,
                           which indicates that a menu separator should be
                           added at that point.

        :arg actionTitles: Optional dict containing ``{name : title}`` mappings
                           for some actions. If not provided, it is assumed
                           that a name for the action exists in
                           :attr:`.strings.actions`.

        All other keyword arguments are passed through to the
        :meth:`__onViewPanelMenuItem` method.

        :returns: A list containing the ``(Action, wx.MenuItem)`` pairs that
                  were added to the menu.
        """
        if actionTitles is None:
            actionTitles = {}

        if actionNames is None:
            actionNames, actionObjs = list(zip(*target.getActions()))
        else:
            actionObjs = [target.getAction(name)
                          if name is not None else None
                          for name in actionNames]

        actionNames  = list(actionNames)
        actionObjs   = list(actionObjs)
        actionTitles = [actionTitles.get(
            n, strings.actions.get((target, n), n)) for n in actionNames]

        def configureActionItem(menu, actionName, actionObj, title):

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

                # If a shortcut uses characters
                # which are not in th platform
                # language, wx.MenuItem.GetAccel
                # returns None.
                accel = menuItem.GetAccel()

                if accel is not None:
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

            return menuItem

        actionItems = []
        for actionName, actionObj, actionTitle in zip(
                actionNames, actionObjs, actionTitles):

            # If actionObj is None, this is a
            # hacky hint to insert a separator
            # - see ActionProvider.getActions.
            if actionObj is None:
                menu.AppendSeparator()
                continue

            # A single normal action <-> menu item
            else:
                currentMenu = menu
                names       = [actionName]
                objs        = [actionObj]
                titles      = [actionTitle]

            for name, obj, title in zip(names, objs, titles):
                actionItems.append(
                    (obj, configureActionItem(currentMenu, name, obj, title)))

        return actionItems


    def __addViewPanelMenu(self, panel, title):
        """Called by :meth:`addViewPanel`. Adds a menu item for the newly
        created :class:`.ViewPanel` instance, and adds any tools
        for the view panel to the tools menu.

        :arg panel: The newly created ``ViewPanel`` instance.
        :arg title: The name given to the ``panel``.
        """

        if not self.__haveMenu:
            return None, []

        # The settings menu for a view is a list of its
        # actions, followed by a list of supported control
        # types. followed by a "removeAllPanels" action
        actionItems  = []
        actionNames  = [name for (name, obj) in panel.getActions()]
        actionTitles = {}
        pluginCtrls  = plugins.listControls(type(panel))

        if len(pluginCtrls) > 0:
            actionNames.append(None)

            # ViewPanel.controlOrder can suggest an ordering
            # of the control panels in the settings menu
            ctrlOrder = panel.controlOrder()
            if ctrlOrder is not None:
                names, clss = zip(*pluginCtrls.items())
                ctrlOrder   = [plugins.lookupControl(c) for c in ctrlOrder]
                indices     = [ctrlOrder.index(c) if c in ctrlOrder
                               else len(pluginCtrls) for c in clss]
                pluginCtrls = sorted(zip(indices, names, clss))
                pluginCtrls = {t[1] : t[2] for t in pluginCtrls}

            # ViewPanels have a ToggleControlPanelAction added as
            # an attributee for every supported control panel
            for ctrlName, ctrlType in pluginCtrls.items():
                name = ctrlType.__name__
                actionNames.append(name)
                actionTitles[name] = ctrlName

            # add a "remove all panels" item
            actionNames.append('removeAllPanels')

        if len(actionNames) == 0:
            return None, []

        menu    = wx.Menu()
        submenu = self.__settingsMenu.AppendSubMenu(menu, title)

        # We add a 'Close' action to the
        # menu for every panel, but put
        # another separator before it
        actionNames.append(None)
        actionNames.append('removeFromFrame')

        # Most of the work is
        # done in populateMenu
        actionItems.extend(self.populateMenu(
            menu,
            panel,
            actionNames=actionNames,
            actionTitles=actionTitles))

        # Make sure the tools
        # menu is up to date
        self.refreshToolsMenu()
        return submenu, actionItems


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
                          ``idle.idle`` loop. Otherwise (the default),
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
                idle.idle(func)
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

        viewPanel  = self.focusedViewPanel
        actionName = self.__viewPanelShortcuts[shortcut].get(viewPanel, None)

        if actionName is None:
            return

        func = viewPanel.getAction(actionName)

        if runOnIdle:
            idle.idle(func)
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

        self              .__viewPanels          .remove(panel)
        self              .__viewPanelIDs        .pop(   panel)
        self              .__viewPanelTitles     .pop(   panel)
        dctx        = self.__viewPanelDCs        .pop(   panel)
        menu        = self.__viewPanelMenus      .pop(   panel, None)
        actionItems = self.__viewPanelMenuActions.pop(   panel, None)

        for action, item in actionItems:
            action.unbindWidget(item)

        for shortcutList in self.__viewPanelShortcuts.values():
            for key in list(shortcutList.keys()):
                if key is panel:
                    shortcutList.pop(key)

        log.debug('Destroying {} ({}) and '
                  'associated DisplayContext ({})'.format(
                      type(panel).__name__,
                      id(panel),
                      id(dctx)))

        # Remove the view panel menu,
        # and make sure that the tools
        # menu is consistent
        if menu is not None:
            self.__settingsMenu.Delete(menu.GetId())

        self.refreshToolsMenu()

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

        # if there are no panels,
        # disable the menus
        self.__enableMenus(numPanels > 0)

        if displaySync:
            self.__configDisplaySync()


    def __configDisplaySync(self, newPanel=None):
        """Called by :meth:`addViewPanel` and :meth:`__onViewPanelClose`.

        This method ensures that the display properties, overlay order,
        and selected overlay for the :class:`.DisplayContext` of at least
        least one :class:`.CanvasPanel` is synced to the master
        :class:`.DisplayContext`.

        :arg newPanel: If this method has been called as a result of a new
                       :class:`.ViewPanel` being added, a reference to the
                       new panel.
        """

        import fsleyes.views.canvaspanel as canvaspanel
        import fsleyes.views.plotpanel   as plotpanel

        # Plot panel defaults
        if newPanel is not None and isinstance(newPanel, plotpanel.PlotPanel):
            newPanel.displayCtx.syncOverlayDisplay = True
            newPanel.displayCtx.syncOverlayVolume  = True
            newPanel.displayCtx.unsyncFromParent('overlayOrder')
            newPanel.displayCtx.unsyncFromParent('selectedOverlay')

        canvasPanels = [vp for vp in self.__viewPanels
                        if isinstance(vp, canvaspanel.CanvasPanel)]
        canvasCtxs   = [c.displayCtx for c in canvasPanels]
        numCanvases  = len(canvasPanels)

        # We only care about canvas
        # panels from here on.
        if numCanvases == 0:
            return

        # Is there at least one canvas panel
        # which has display properties/overlay
        # order synced to the master display
        # context?
        displaySynced = any([c.syncOverlayDisplay
                             for c in canvasCtxs
                             if c is not newPanel])
        volumeSynced = any([c.syncOverlayVolume
                             for c in canvasCtxs
                             if c is not newPanel])
        orderSynced   = any([c.isSyncedToParent('overlayOrder')
                             for c in canvasCtxs
                             if c is not newPanel])
        selOvlSynced  = any([c.isSyncedToParent('selectedOverlay')
                             for c in canvasCtxs
                             if c is not newPanel])

        # If an existing canvas panel is
        # already synced to the master,
        # then we set the new panel to
        # be unsynced
        if displaySynced and volumeSynced and orderSynced and selOvlSynced:
            if newPanel is not None and \
               isinstance(newPanel, canvaspanel.CanvasPanel):
                childDC                    = newPanel.displayCtx
                childDC.syncOverlayVolume  = True
                childDC.syncOverlayDisplay = False
                childDC.unsyncFromParent('overlayOrder')
                childDC.unsyncFromParent('selectedOverlay')

        # If no existing CanvasPanels are
        # synced to the master context,
        # re-sync the most recently added
        # one.
        else:
            if newPanel is not None: panel = newPanel
            else:                    panel = canvasPanels[-1]
            childDC = panel.displayCtx

            # Make sure that the parent context
            # inherits the values from this context
            displays = [childDC.getDisplay(o) for o in self.__overlayList]

            childDC.setBindingDirection(False)

            for display in displays:
                opts = display.opts
                display.setBindingDirection(False)
                opts   .setBindingDirection(False)

            childDC.syncOverlayDisplay = True
            childDC.syncOverlayVolume  = True
            childDC.syncToParent('overlayOrder')
            childDC.syncToParent('selectedOverlay')

            # Reset the binding directiona
            childDC.setBindingDirection(True)

            for display in displays:
                opts = display.opts
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
                    ev.Veto()
                    return

                save = result == wx.ID_YES

                fslsettings.write('fsleyes.frame.saveLayout', save)
                fslsettings.write('fsleyes.frame.askToSaveLayout',
                                  not dlg.CheckBoxState())

            if save:
                layout   = layouts.serialiseLayout(self)
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

        # The close is going ahead. We assume that this
        # EVT_CLOSE handler is the first that is called,
        # and can thus control whether any the event
        # gets propagated to other handlers.
        ev.Skip()

        # It's nice to explicitly clean
        # up our FSLeyesPanels, otherwise
        # they'll probably complain
        for panel in self.__viewPanels:
            panel.destroy()

        # (not created) self.__overlayMenuActions

        # Cleanly destroy all
        # menu action objects
        allactions = []
        allactions.extend([a for a, _ in self.__viewMenuActions])
        allactions.extend([a for a, _ in self.__layoutMenuActions])
        allactions.extend([a for a, _ in self.__overlayMenuActions])
        allactions.extend([a for a, _ in self.__toolsMenuActions])
        allactions.extend(self.__menuActions.values())
        for vpactions in self.__viewPanelMenuActions.values():
            allactions.extend([a for a, _ in vpactions])

        for action in allactions:
            # actions associated with some object
            # (e.g. a ViewPanel) will have already
            # been destroyed by them
            if not action.destroyed:
                action.destroy()

        self.__layoutMenuActions    = None
        self.__viewPanelMenuActions = None
        self.__toolsMenuActions     = None
        self.__menuActions          = None

        # Deregister loadoverlay listener
        # (registered in __init__)
        import fsleyes.actions.loadoverlay as loadoverlay
        loadoverlay.recentPathManager.deregister(self.__name)


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
            size    = list(wx.Display(0).GetGeometry().GetSize())
            size[0] = round(size[0] * 0.9)
            size[1] = round(size[1] * 0.9)
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
                    layouts.applyLayout(
                        self,
                        'fsleyes.frame.layout',
                        layout,
                        message=strings.messages[self, 'restoringLayout'])
                except Exception:
                    log.warning('Previous layout could not be restored - '
                                'falling back to default layout.')
                    log.debug('Layout restore error', exc_info=True)
                    layout = None

            if layout is None:
                layouts.loadLayout(self, 'default')


    def __makeMenuBar(self):
        """Constructs a bunch of menu items for this ``FSLeyesFrame``."""

        if not self.__haveMenu:
            return

        menuBar = wx.MenuBar()
        self.SetMenuBar(menuBar)

        # The menu bar on OSX/wxPython is a bit different
        # than the menu bar on OSX/wxPhoenix, or on Linux.
        # This is because under OSX/wxPython, we can't get
        # access to the built-in application menu.
        onOSX          = fwidgets.wxPlatform() in (fwidgets.WX_MAC_CARBON,
                                                   fwidgets.WX_MAC_COCOA)
        haveAppMenu    = (onOSX and
                          fwidgets.wxFlavour() == fwidgets.WX_PHOENIX)
        locationOffset = 0

        # On linux, we create a FSLeyes menu
        if not onOSX:
            locationOffset  = 1
            fsleyesMenu     = wx.Menu()
            menuBar.Append(fsleyesMenu, 'FSLeyes')

        # On OSX/wxPhoenix, we can
        # get the built-in app menu
        elif haveAppMenu:
            fsleyesMenu = menuBar.OSXGetAppleMenu()

        # On OSX/wxPython, we fudge
        # things a bit - see below.
        else:
            fsleyesMenu = None

        fileMenu     = wx.Menu()
        overlayMenu  = wx.Menu()
        viewMenu     = wx.Menu()
        settingsMenu = wx.Menu()
        toolsMenu    = wx.Menu()

        menuBar.Append(fileMenu,     'File')
        menuBar.Append(overlayMenu,  'Overlay')
        menuBar.Append(viewMenu,     'View')
        menuBar.Append(settingsMenu, 'Settings')
        menuBar.Append(toolsMenu,    'Tools')

        self.__menuBar      = menuBar
        self.__fsleyesMenu  = fsleyesMenu
        self.__overlayMenu  = overlayMenu
        self.__fileMenu     = fileMenu
        self.__viewMenu     = viewMenu
        self.__layoutMenu   = None
        self.__settingsMenu = settingsMenu
        self.__toolsMenu    = toolsMenu

        # store locations of some menus
        # for use by the __enableMenus
        # method
        self.__menuLocations = {
            'overlay'  : 1 + locationOffset,
            'settings' : 3 + locationOffset,
            'tools'    : 4 + locationOffset,
        }

        self.__makeFileMenu()

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

        self.__makeOverlayMenu()
        self.refreshToolsMenu()
        self.refreshViewMenu()


    def __enableMenus(self, state):
        """Enables/disables some of the menus. Only the menus which are useless
        without any view panels open are affected.
        """

        # we might be running without a menubar
        # if __init__ was called with menu=Falsee
        if self.__menuBar is None:
            return

        # overlay, settings, and tools menus
        self.__menuBar.EnableTop(self.__menuLocations['overlay'],  state)
        self.__menuBar.EnableTop(self.__menuLocations['settings'], state)
        self.__menuBar.EnableTop(self.__menuLocations['tools'],    state)


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
            (UpdateCheckAction(overlayList, displayCtx),
             strings.actions[      UpdateCheckAction],
             shortcuts.actions.get(UpdateCheckAction),
             wx.ID_ANY),
            (self.setFSLDIR,
             strings.actions[self, 'setFSLDIR'],
             shortcuts.actions.get((self, 'setFSLDIR')),
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

            self.__menuActions[type(action)] = action


    def __makeFileMenu(self):
        """Called by :meth:`__makeMenuBar`. Creates the *File* menu. """

        from fsleyes.actions.loadoverlay        import LoadOverlayAction
        from fsleyes.actions.loadoverlayfromdir import LoadOverlayFromDirAction
        from fsleyes.actions.loaddicom          import LoadDicomAction
        from fsleyes.actions.loadstandard       import LoadStandardAction
        from fsleyes.actions.loadatlas          import LoadAtlasAction
        from fsleyes.actions.browsexnat         import BrowseXNATAction
        from fsleyes.actions.newimage           import NewImageAction
        from fsleyes.actions.runscript          import RunScriptAction
        from fsleyes.actions.loadplugin         import LoadPluginAction
        from fsleyes.actions.notebook           import NotebookAction

        menu = self.__fileMenu

        fileActions = [LoadOverlayAction,
                       LoadOverlayFromDirAction,
                       LoadStandardAction,
                       NewImageAction,
                       LoadDicomAction,
                       BrowseXNATAction,
                       LoadAtlasAction,
                       NotebookAction,
                       LoadPluginAction,
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

            self.__menuActions[action] = actionObj

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

        if not self.__haveMenu:
            return

        import fsleyes.actions.loadoverlay as loadoverlay

        for path in self.__recentPathsMenu.GetMenuItems():
            self.__recentPathsMenu.Remove(path)

        paths = loadoverlay.recentPathManager.listRecentPaths()

        # We give each recent file menu item an identifying
        # number from 1-(numpaths) - this is used by the
        # __onRecentPath handler.
        for i, p in enumerate(reversed(paths), start=1):
            menuItem = self.__recentPathsMenu.Append(i, p)
            self.Bind(wx.EVT_MENU, self.__onRecentPath, menuItem)


    def __onRecentPath(self, ev):
        """Called when a recent path is selected from the
        "File -> Recent files" menu item. Loads the path.
        See the :meth:`__makeRecentPathsMenu` method.
        """

        import fsleyes.actions.loadoverlay as loadoverlay

        path = self.__recentPathsMenu.GetLabel(ev.GetId())

        def onLoad(paths, overlays):

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


    def __makeViewMenu(self):
        """Called by :meth:`refreshViewMenu`. Creates the view panel menu.

        :returns: A list containing the ``(Action, wx.MenuItem)`` pairs that
                  were added to the menu.
        """

        menu = self.__viewMenu

        # Shortcuts to open a new view panel
        vpActions = [self.addOrthoPanel,
                     self.addLightBoxPanel,
                     self.addTimeSeriesPanel,
                     self.addHistogramPanel,
                     self.addPowerSpectrumPanel,
                     self.addScene3DPanel,
                     self.addShellPanel]

        actionItems = []

        for action in vpActions:

            shortcut = shortcuts.actions.get((self, action.__name__))

            if shortcut is None: shortcut = ''
            else:                shortcut = '\t{}'.format(shortcut)

            title = '{}{}'.format(strings.actions[self, action.__name__],
                                  shortcut)

            item = menu.Append(wx.ID_ANY, title)
            action.bindToWidget(self, wx.EVT_MENU, item)
            actionItems.append((action, item))

        # Views provided by FSLeyes plugins
        pluginViews = plugins.listViews()
        if len(pluginViews) > 0:
            menu.AppendSeparator()
            for name, cls in pluginViews.items():
                func = ft.partial(self.addViewPanel, cls, title=name)
                item = menu.Append(wx.ID_ANY, name)
                self.Bind(wx.EVT_MENU, lambda ev, f=func : f(), item)

        # We create the layout menu,
        # but don't populate it - this
        # is performed  by the caller
        self.__layoutMenu = wx.Menu()
        menu.AppendSeparator()
        menu.AppendSubMenu(self.__layoutMenu, 'Layouts')
        return actionItems


    def __makeLayoutMenu(self):
        """Called by :meth:`refreshLayoutMenu`. Re-creates the *View->Layouts*
        menu.
        """

        if not self.__haveMenu:
            return []

        from fsleyes.actions.loadlayout   import LoadLayoutAction
        from fsleyes.actions.savelayout   import SaveLayoutAction
        from fsleyes.actions.clearlayouts import ClearLayoutsAction

        menu        = self.__layoutMenu
        actionItems = []

        builtIns = list(layouts.BUILT_IN_LAYOUTS.keys())
        saved    = layouts.getAllLayouts()

        # Add a menu item to load each built-in layouts
        for layout in builtIns:

            title    = strings.layouts.get(layout, layout)
            shortcut = shortcuts.actions.get((self, 'layouts', layout),
                                             None)

            if shortcut is not None:
                title = '{}\t{}'.format(title, shortcut)

            menuItem = menu.Append(wx.ID_ANY, title)

            actionObj = LoadLayoutAction(
                self.overlayList, self.displayCtx, self, layout)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)
            actionItems.append((actionObj, menuItem))

        if len(builtIns) > 0:
            menu.AppendSeparator()

        # Add a menu item to load each saved layout
        for layout in saved:

            menuItem  = menu.Append(
                wx.ID_ANY, strings.layouts.get(layout, layout))
            actionObj = LoadLayoutAction(
                self.overlayList, self.displayCtx, self, layout)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

            actionItems.append((actionObj, menuItem))

        # Add menu items for other layout
        # operations, but separate them
        # from the existing layouts
        if len(saved) > 0:
            menu.AppendSeparator()

        # TODO: Delete a single layout?
        #       Save to/load from file?
        layoutActions = [SaveLayoutAction,
                         ClearLayoutsAction]

        for la in layoutActions:

            actionObj = la(self.overlayList, self.displayCtx, self)
            menuItem  = menu.Append(wx.ID_ANY, strings.actions[la])

            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)
            actionItems.append((actionObj, menuItem))
        return actionItems


    def __makeOverlayMenu(self):
        """Called by :meth:`__makeMenuBar`. Creates/configures the *Overlay*
        menu.
        """

        from fsleyes.actions.removealloverlays import RemoveAllOverlaysAction
        from fsleyes.actions.copyoverlay       import CopyOverlayAction
        from fsleyes.actions.saveoverlay       import SaveOverlayAction
        from fsleyes.actions.reloadoverlay     import ReloadOverlayAction
        from fsleyes.actions.removeoverlay     import RemoveOverlayAction

        menu = self.__overlayMenu

        fileActions = ['selectNextOverlay',
                       'selectPreviousOverlay',
                       RemoveAllOverlaysAction,
                       'sep',
                       'name',
                       CopyOverlayAction,
                       SaveOverlayAction,
                       ReloadOverlayAction,
                       RemoveOverlayAction,
                       'toggleOverlayVisibility']

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
            if isinstance(action, str):

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
            self.__overlayMenuActions.append((actionObj, menuItem))


    def __makeToolsMenu(self):
        """Called by :meth:`refreshToolsMenu`. Populates the *Tools* menu with
        tools that are not bound to a specific ``ViewPanel`` (and which are
        always present), followed by tools which are specific to the open
        views.
        """

        menu        = self.__toolsMenu
        actionItems = []
        pluginTools = plugins.listTools()

        # Tools are either restricted for use with a
        # specific view, or independent of any view.
        # We create the latter here first, and then
        # use __makeViewPanelTools to create the former
        pluginTools = {n : c for n, c in pluginTools.items()
                       if c.supportedViews() is None}

        # Fix the ordering for view-independent plugins
        # (the equivalent of what is done with
        # ViewPanel.toolOrder, in __makeViewPanelTools).
        toolOrder   = ['ApplyFlirtXfmAction',
                       'SaveFlirtXfmAction',
                       'ResampleAction',
                       'ProjectImageToSurfaceAction']
        names, clss = zip(*pluginTools.items())
        toolOrder   = [plugins.lookupTool(t) for t in toolOrder]
        indices     = [toolOrder.index(c) if c in toolOrder
                       else len(pluginTools) for c in clss]
        pluginTools = sorted(zip(indices, names, clss))
        pluginTools = {t[1]: t[2] for t in pluginTools}

        for name, cls in pluginTools.items():

            # Refs to view-independent tools are stored in
            # __menuActions. This method may be called
            # multiple times, so we only create the Action
            # object on the first invocation.
            if cls in self.__menuActions:
                actionObj = self.__menuActions[cls]
            else:
                # plugin tools not coupled to a specific view
                # get a reference to me, the FSLeyesFrame
                actionObj = cls(self.__overlayList, self.__displayCtx, self)

            shortcut = shortcuts.actions.get(cls)

            if shortcut is not None:
                name = '{}\t{}'.format(name, shortcut)

            menuItem = menu.Append(wx.ID_ANY, name)
            actionObj.bindToWidget(self, wx.EVT_MENU, menuItem)

            actionItems.append((actionObj, menuItem))

        actionItems.extend(self.__makeViewPanelTools())
        return actionItems


    def __makeViewPanelTools(self):
        """Called when a view panel is added or removed. Refreshes the *Tools*
        menu.
        """

        if not self.__haveMenu:
            return

        menu = self.__toolsMenu

        from fsleyes.views.orthopanel         import OrthoPanel
        from fsleyes.views.lightboxpanel      import LightBoxPanel
        from fsleyes.views.scene3dpanel       import Scene3DPanel
        from fsleyes.views.timeseriespanel    import TimeSeriesPanel
        from fsleyes.views.histogrampanel     import HistogramPanel
        from fsleyes.views.powerspectrumpanel import PowerSpectrumPanel
        from fsleyes.views.shellpanel         import ShellPanel

        # Recreate tools for each view panel. We
        # ensure that the tools for different view
        # panel types are always in a consistent
        # order (i.e. ortho first, shell last)
        panels  = self.viewPanels
        vpOrder = [OrthoPanel,
                   LightBoxPanel,
                   Scene3DPanel,
                   TimeSeriesPanel,
                   HistogramPanel,
                   PowerSpectrumPanel,
                   ShellPanel]
        for p in panels:
            if type(p) not in vpOrder:
                vpOrder.append(type(p))
        panels = sorted(panels, key=lambda p: vpOrder.index(type(p)))

        actionItems  = []
        vpTypesAdded = set()

        for panel in panels:

            vpType = type(panel)

            # built-in tools, implemented
            # by the viewpanel itself
            toolNames  = [t.actionName for t in panel.getTools()]
            toolTitles = {}

            # Plugin-provided tools, which are created
            # by the ViewPanel and added as attributes
            # to itself (see ViewPanel.reloadPlugins)
            pluginTools = plugins.listTools(vpType)

            # ViewPanel.toolOrder can suggest an
            # ordering of plugin-provided tools.
            toolOrder = vpType.toolOrder()
            if len(pluginTools) > 0 and toolOrder is not None:
                names, clss = zip(*pluginTools.items())
                toolOrder   = [plugins.lookupTool(t) for t in toolOrder]
                indices     = [toolOrder.index(c) if c in toolOrder
                               else len(pluginTools) for c in clss]
                pluginTools = sorted(zip(indices, names, clss))
                pluginTools = {t[1] : t[2] for t in pluginTools}

            # See ViewPanel.reloadPlugins. and LoadPluginAction.
            # All supported tools are added as attributes to the
            # ViewPanel instance, with the class name used as
            # the attribute name.
            for toolName, cls in pluginTools.items():
                name = cls.__name__
                toolNames.append(name)
                toolTitles[name] = toolName

            # Only the first panel for each type
            # has its tools added to the menu.
            if len(toolNames) == 0 or vpType in vpTypesAdded:
                continue

            vpTypesAdded.add(vpType)

            # Each view panel added to the tools list
            # gets its own section, starting with a
            # separator, and the view panel title.
            menu.AppendSeparator()
            menu.Append(wx.ID_ANY, self.__viewPanelTitles[panel]).Enable(False)
            actionItems.extend(
                self.populateMenu(menu, panel, toolNames, toolTitles))

        return actionItems


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

        if not self.__haveMenu:
            return

        if haveOverlays:

            self.__display = self.__displayCtx.getDisplay(overlay)
            name = self.__display.name

            if name is None: name = ''
            else:            name = name.strip()

            if name == '':
                name = strings.labels[self, 'noName']
            self.__overlayNameMenuItem.SetItemLabel(name)

            if not self.__display.hasListener('name', self.__name):
                self.__display.addListener('name',
                                           self.__name,
                                           self.__selectedOverlayChanged)
        else:
            name = strings.labels[self, 'noOverlays']
            self.__overlayNameMenuItem.SetItemLabel(name)


class OverlayDropTarget(wx.FileDropTarget):
    """The ``OverlayDropTarget`` class allows overly files to be dragged and
    dropped onto a ``wx`` window. It uses the :func:`.loadOverlays` function.

    Associate an ``OverlayDropTarget`` `dt`` with a window ``w`` like so::

        w.SetDropTarget(dt)
    """


    def __init__(self, overlayList, displayCtx):
        """Create an ``OverlayDropTarget``. The master
        :class:`.DissplayContext` should be passed in, as opposed to any child
        instances.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  Thw master :class:`.DisplayConext`.
        """
        wx.FileDropTarget.__init__(self)
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx


    def __onLoad(self, paths, overlays):
        """Called by :func:`.loadOverlays` (which is called in
        :meth:`OnDropFiles`) when the dropped overlay files have been loaded.
        Adds the overlays to the :class:`.OverlayList`.
        """

        if len(overlays) == 0:
            return

        self.__overlayList.extend(overlays)

        if self.__displayCtx.autoDisplay:
            for overlay in overlays:
                autodisplay.autoDisplay(overlay,
                                        self.__overlayList,
                                        self.__displayCtx)


    def OnDropFiles(self, x, y, filenames):
        """Overrides ``wx.FileDropTarget.OnDropFiles``. Called when files
        are dropped onto the window. Passes the files to :func:`.loadOverlays`,
        along with :meth:`__onLoad` as a callback.
        """
        import fsleyes.actions.loadoverlay as loadoverlay

        if filenames is not None:
            loadoverlay.loadOverlays(
                filenames,
                onLoad=self.__onLoad,
                inmem=self.__displayCtx.loadInMemory)
            return True
        else:
            return False
