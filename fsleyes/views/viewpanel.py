#!/usr/bin/env python
#
# viewpanel.py - Superclass for all FSLeyes view panels.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ViewPanel` class, which is the base-class
for all of the *FSLeyes view* panels. See the :mod:`fsleyes` package
documentation for more details.
"""


import              logging
import itertools as it

import                                  wx
import wx.lib.agw.aui                as aui
import wx.lib.agw.aui.framemanager   as auifm

import fsl.utils.notifier            as notifier
import fsleyes_widgets               as fwidgets

import fsleyes.panel                 as fslpanel
import fsleyes.toolbar               as fsltoolbar
import fsleyes.plugins               as plugins
import fsleyes.controls.controlpanel as ctrlpanel
import fsleyes.profiles              as profiles
import fsleyes.strings               as strings
import fsleyes.actions               as actions


log = logging.getLogger(__name__)


class ViewPanel(fslpanel.FSLeyesPanel):
    """The ``ViewPanel`` class is the base-class for all *FSLeyes views*.

    A ``ViewPanel`` displays some sort of view of the overlays in an
    :class:`.OverlayList`. The settings for a ``ViewPanel`` are defined by a
    :class:`.DisplayContext` instance.


    **Panels and controls**


    A ``ViewPanel`` class uses a ``wx.lib.agw.aui.AuiManager`` to lay out its
    children. A ``ViewPanel`` has one central panel, which contains the
    primary view; and may have one or more secondary panels, which contain
    *controls* - see the :mod:`.controls` package. The centre panel can be set
    via the :meth:`centrePanel` property, and secondary panels can be
    added/removed to/from with the :meth:`togglePanel` method. The current
    state of a secondary panel (i.e. whether one is open or not) can be
    queried with the :meth:`isPanelOpen` method, and existing secondary panels
    can be accessed via the :meth:`getPanel` method.  Secondary panels must be
    derived from either the :class:`.ControlPanel` or :class:`.ControlToolBar`
    base-classes.


    **Profiles**


    The logic which defines the way that a user interacts with a view panel
    is defined by a  :class:`.Profile` object, which contains mouse and
    keyboard event handlers for reacting to user input.

    Sub-classes must call the :meth:`initProfile` method to initialise their
    default profile. Other profiles may be associated with a particular
    control panel - these profiles can be temporarily activated and deactivated
    when the control panel is toggled via the :meth:`togglePanel` method.

    The currently active interaction profile can be accessed with the
    :meth:`currentProfile` method. See the :mod:`.profiles` package for
    more information on interaction profiles.


    **Programming interface**


    The following methods are available on a ``Viewpanel`` for programmatically
    controlling its display and layout:


    .. autosummary::
       :nosignatures:

       togglePanel
       isPanelOpen
       getPanel
       getPanels
       getTools
       removeFromFrame
       removeAllPanels
       getPanelInfo
       auiManager
    """


    def controlOptions(self, cpType):
        """May be overridden by sub-classes. Given a control panel type,
        may return a dictionary containing arguments to be passed to
        the  ``__init__`` method when the control panel is created.
        """
        return None


    @staticmethod
    def title():
        """May be overridden by sub-classes. Returns a title for this
        ``ViewPanel``, to be used in menus and window title bars.
        """
        return None


    @staticmethod
    def controlOrder():
        """May be overridden by sub-classes. Returns a list of names of
        control panel types, specifying a suggested order for the
        settings menu for views of this type.
        """
        return None


    @staticmethod
    def toolOrder():
        """May be overridden by sub-classes. Returns a list of names of
        tools, specifying a suggested order for the corresponding entries
        in the FSLeyes tools menu. Note that the ordering of tools returned
        by the :meth:`getTools` method is honoured - the ordering returned
        by *this* method relates to tools which are implemented as plugins.
        """
        return None


    @staticmethod
    def defaultLayout():
        """May be overridden by sub-classes. Should return a list of names of
        FSLeyes :class:`.ControlPanel` types which form the default layout for
        this view.
        """
        return None


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``ViewPanel``.

        :arg parent:         ``wx`` parent object
        :arg overlayList:    The :class:`.OverlayList`
        :arg displayCtx:     A :class:`.DisplayContext` object unique to this
                             ``ViewPanel``
        :arg frame:          The :class:`.FSLeyesFrame`
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        # Currently only two profiles are allowed at
        # any one time - the default profile, passed
        # to initProfiles. and one more profile
        # associated with a control panel.
        #
        # If the default profile is active, and a
        # new control is opened which needs a different
        # profile, that profile is activated.
        #
        # If a non-default profile (#1) is active, and
        # a new control is opened which needs a
        # different profile (#2), all controls which
        # require profile #1 are closed, and profile
        # #2 is activated.
        #
        # This all happens in togglePanel.
        self.__profileManager = profiles.ProfileManager(
            self, overlayList, displayCtx, 2)

        # The __centrePanel attribute stores a reference
        # to the main (centre) panel on this ViewPanel.
        # It is set by sub-class implementations via
        # the centrePanel property.
        #
        # The panels dictionary stores a collection
        # of {type : instance} mappings of active
        # FSLeyes control panels that are contained
        # in this view panel.
        self.__centrePanel = None
        self.__panels      = {}

        # Notifier instance for emitting events.
        # Currently only two events are emitted
        # - one of them is profile changes, and
        # the profilemanager emits these events
        # anyway, so we can just use it. As for
        # the other event (aui layout changes),
        # well, we're being a bit dodgy and
        # emitting these events via the
        # profilemanager.
        self.__events = self.__profileManager

        # See note in FSLeyesFrame about
        # the user of aero docking guides.
        self.__auiMgr = aui.AuiManager(
            self,
            agwFlags=(aui.AUI_MGR_RECTANGLE_HINT          |
                      aui.AUI_MGR_NO_VENETIAN_BLINDS_FADE |
                      aui.AUI_MGR_ALLOW_FLOATING          |
                      aui.AUI_MGR_AERO_DOCKING_GUIDES     |
                      aui.AUI_MGR_LIVE_RESIZE))

        self.__auiMgr.SetDockSizeConstraint(0.5, 0.5)
        self.__auiMgr.Bind(aui.EVT_AUI_PANE_CLOSE,
                           self.__onPaneClose)
        self.__auiMgr.Bind(aui.EVT_AUI_PERSPECTIVE_CHANGED,
                           self.__onPerspectiveChange)

        # A very shitty necessity. When panes are floated,
        # the AuiManager sets the size of the floating frame
        # to the minimum size of the panel, without taking
        # into account the size of its borders/title bar,
        # meaning that the panel size is too small. Here,
        # we're just creating a dummy MiniFrame (from which
        # the AuiFloatingFrame derives), and saving the size
        # of its trimmings for later use in the togglePanel
        # method.
        ff         = wx.MiniFrame(self)
        size       = ff.GetSize().Get()
        clientSize = ff.GetClientSize().Get()
        self.__floatOffset = (size[0] - clientSize[0],
                              size[1] - clientSize[1])
        ff.Destroy()

        self.reloadPlugins()


    def reloadPlugins(self):
        """Called by :meth:`__init__`, and by the :class:`.LoadPluginAction`
        when new plugins are registered.

        This is a bit of a hack, but less hacky than it used to be.  All
        plugin-provided control panels and tools which support this
        ``ViewPanel`` are looked up via the :mod:`.plugins.` module. Then, for
        each control, we create a :class:`.ToggleControlPanelAction`, and add
        it as an attribute on this ``ViewPanel``.

        Similarly, all plugin-provided tools which support this ``ViewPanel``
        are created and added as attributes.

        In both cases, the class name of the control/tool is used as the
        attribute name.

        This is done so that these actions will work with the
        :class:`.ActionProvider` interface, and hence the
        :meth:`.FSLEeyesFrame.populateMenu` method.

        This implementation may change in the future if it becomes problematic
        (e.g. due to naming conflicts).
        """

        # controls
        for ctrlTitle, ctrlType in plugins.listControls(type(self)).items():
            name = ctrlType.__name__
            if not hasattr(self, name):
                act = actions.ToggleControlPanelAction(
                    self.overlayList,
                    self.displayCtx,
                    self,
                    ctrlType,
                    name=name,
                    title=ctrlTitle)
                setattr(self, name, act)

        # tools
        for toolType in plugins.listTools(type(self)).values():
            name = toolType.__name__
            if not hasattr(self, name):
                act = toolType(self.overlayList, self.displayCtx, self)
                setattr(self, name, act)


    def destroy(self):
        """Removes some property listeners, destroys all child panels,
        destroys the :class:`.ProfileManager`, and ``AuiManager``, and
        calls :meth:`.FSLeyesPanel.destroy`.
        """

        # Order of operations is important. For example,
        # FSLeyesPanel.destroy will result in all Actions
        # associated with this ViewPanel being destroyed,
        # and their destroy routines may interact with
        # this ViewPanel.

        # remove listeners from overlaylist and display context
        lName = 'ViewPanel_{}'.format(self.name)
        self.overlayList.removeListener('overlays',        lName)
        self.displayCtx .removeListener('selectedOverlay', lName)

        fslpanel.FSLeyesPanel.destroy(self)

        # Make sure that any control panels are correctly destroyed
        for panel in self.__panels.values():
            self.__auiMgr.DetachPane(panel)
            panel.destroy()

        # Disable the  ProfileManager
        self.__profileManager.destroy()

        # Un-initialise the AUI manager
        self.__auiMgr.UnInit()

        # The AUI manager does not clear its
        # reference to this panel, so let's
        # do it here.
        self.__auiMgr._frame  = None
        self.__profileManager = None
        self.__auiMgr         = None
        self.__panels         = None
        self.__centrePanel    = None
        self.__events         = None


    @property
    def events(self) -> notifier.Notifier:
        """Return a reference to a :class:`.Notifier` instance which can be
        used to be notified when certain events occur. Currently the following
        events are emitted:

         - ``'profile'``, when the current interaction profile changes.
           Callbacks which are registered with the ``'profile'`` topic will
           be passed a tuple containing the types (:class:`.Profile`
           sub-classes) of the de-registered and newly registered profiles.

         - ``'aui_perspective'``, when the AUI-managed layout changes, e.g.
           sash resizes, control panels added/removed, etc. This event is
           emitted whenever the ``AuiManager`` emits a
           ``EVT_AUI_PERSPECTIVE_CHANGED`` event. It is re-emitted via the
           :class:`.Notifer` interface so that non-wx entities can be
           notified (see e.g. the :class:`.ToggleControlPanelAction`).
        """
        return self.__events


    def initProfile(self, defaultProfile):
        """Must be called by subclasses, after they have initialised all
        of the attributes which may be needed by their associated
        :class:`.Profile` instances.

        :arg defaultProfile: Default profile type
        """
        self.__profileManager.activateProfile(defaultProfile)


    @property
    def currentProfile(self):
        """Returns the :class:`.Profile` instance currently in use. """
        return self.__profileManager.getCurrentProfile()


    @property
    def profileManager(self):
        """Returns a reference to the :class:`.ProfileManager` used by
        this ``ViewPanel``.
        """
        return self.__profileManager


    @property
    def centrePanel(self):
        """Returns the primary (centre) panel on this ``ViewPanel``.
        """
        return self.__centrePanel


    @centrePanel.setter
    def centrePanel(self, panel):
        """Set the primary centre panel for this ``ViewPanel``. This method
        is only intended to be called by sub-classes.
        """

        panel.Reparent(self)
        paneInfo = (aui.AuiPaneInfo()
                    .Name(type(panel).__name__)
                    .CentrePane())

        self.__auiMgr.AddPane(panel, paneInfo)
        self.__auiMgrUpdate()
        self.__centrePanel = panel


    def togglePanel(self, panelType, *args, **kwargs):
        """Add/remove the secondary control panel of the specified type to/from
        this ``ViewPanel``.

        If no keyword argunents are specified, the arguments returned by the
        :meth:`.ControlMixin.defaultLayout` method are returned.

        :arg panelType: Type of the secondary panel.

        :arg args:      All positional arguments are passed to the
                        ``panelType`` constructor.

        :arg floatPane: If ``True``, the secondary panel is initially floated.
                        Defaults to ``False``.

        :arg floatOnly: If ``True``, and ``floatPane=True``, the panel will
                        be permanently floated (i.e. it will not be dockable).

        :arg floatPos:  If provided, and ``floatPane`` is ``True``, specifies
                        the location of the floating panel as ``(w, h)``
                        proportions between 0 and 1, relative to this view
                        panel.

        :arg closeable: If ``False``, and ``floatPane=True``, the panel will
                        not have a close button when it is floated.

        :arg location:  If ``floatPane=False``, the initial dock position of
                        the panel - either ``wx.TOP``, ``wx.BOTTOM``,
                        ``wx.LEFT``, or ``wx.RIGHT. Defaults to ``wx.BOTTOM``.

        :arg title:     Title to give the control. If not provided, it is
                        assumed that a title for ``panelType`` is in
                        :attr:`.strings.titles`.

        :arg kwargs:    All other keyword arguments, are passed to the
                        ``panelType`` constructor.

        :returns:       The newly created control panel.

        .. note::       The ``panelType`` type must be a sub-class of
                        :class:`.ControlPanel` or :class:`.ControlToolBar`,
                        which can be created like so::

                            panel = panelType(parent,
                                              overlayList,
                                              displayCtx,
                                              frame,
                                              *args,
                                              **kwargs)

        .. warning:: Do not define a control (a.k.a. secondary) panel
                     constructor to accept arguments with the names
                     ``floatPane``, ``floatOnly``, ``floatPos``,
                     ``closeable``, or ``location``, as arguments with those
                     names will get eaten by this method before they can be
                     passed to the constructor.
        """

        # Merge in default options for this control,
        # with precedence (highest to lowest):
        #  1. kwargs
        #  2. ViewPanel.controlOptions
        #  3. ControlPanel.defaultLayout
        layout = panelType.defaultLayout()
        cpopts = self.controlOptions(panelType)

        if layout is None: layout = {}
        if cpopts is None: cpopts = {}

        for k, v in it.chain(cpopts.items(), layout.items()):
            if k not in kwargs:
                kwargs[k] = v

        location   = kwargs.pop('location',  None)
        floatPane  = kwargs.pop('floatPane', False)
        floatOnly  = kwargs.pop('floatOnly', False)
        closeable  = kwargs.pop('closeable', True)
        title      = kwargs.pop('title',     None)
        floatPos   = kwargs.pop('floatPos',  (0.5, 0.5))
        profileCls = panelType.profileCls()

        if title is None:
            title = panelType.title()
        if title is None:
            title = strings.titles.get(panelType, panelType.__name__)

        if location not in (None, wx.TOP, wx.BOTTOM, wx.LEFT, wx.RIGHT):
            raise ValueError('Invalid value for location')

        supported = panelType.supportedViews()
        if supported is not None and not isinstance(self, tuple(supported)):
            raise ValueError(
                '{} views are not supported by {} controls'.format(
                    type(self).__name__, panelType.__name__))

        # The panel is already open - close it
        window = self.__panels.get(panelType, None)
        if window is not None:
            self.__onPaneClose(None, window)
            return

        # Otherwise, create a new panel of the specified type.
        # If this control is associated with a custom interaction
        # profile, check that that profile is active, create it
        # if needed, and close down any controls which are not
        # compatible with the new profile.
        profile = self.currentProfile
        if profileCls is not None and not isinstance(profile, profileCls):

            log.debug('New control %s requires interaction profile %s but '
                      'profile %s is active', panelType.__name__,
                      profileCls.__name__, type(profile).__name__)

            # close down incompatible controls
            for ctype, cpanel in list(self.__panels.items()):
                cprofileCls = ctype.profileCls()
                if cprofileCls is not None and \
                   not issubclass(cprofileCls, profileCls):
                    log.debug('Closing down control %s as it is incompatible '
                              'with profile %s', ctype.__name__,
                              profileCls.__name__)
                    self.__onPaneClose(None, cpanel)

            # change profile
            self.__profileManager.activateProfile(profileCls)

        # The PaneInfo Name is the control panel class name -
        # this is used for saving and restoring layouts.
        window = panelType(self,
                           self.overlayList,
                           self.displayCtx,
                           self,
                           *args,
                           **kwargs)
        # save a ref to the control if it has a custom
        # profile so, when it is destroyed, we know
        if profileCls is not None:
            self.__activeControl = window

        paneInfo = self.__layoutNewPanel(window, title, location, floatPane,
                                         floatPos, floatOnly, closeable)
        self.__auiMgr.AddPane(window, paneInfo)
        self.__panels[panelType] = window
        self.__auiMgrUpdate(newPanel=window)
        return window


    def __layoutNewPanel(self,
                         panel,
                         title,
                         location,
                         floatPane,
                         floatPos,
                         floatOnly,
                         closeable):
        """Sub-method of :meth:`togglePanel`. Creates and returns an
        ``AuiPaneInfo`` instance describing the initial layout of a new
        control panel. See ``togglePanel`` for an explanation of the
        arguments.
        """
        paneInfo  = aui.AuiPaneInfo().Name(type(panel).__name__)
        isToolbar = isinstance(panel, ctrlpanel.ControlToolBar)

        if isToolbar:

            # ToolbarPane sets the panel layer to 10
            paneInfo.ToolbarPane()

            if panel.GetOrient() == wx.VERTICAL:
                paneInfo.GripperTop()

            # We are going to put any new toolbars on
            # the top of the panel, below any existing
            # toolbars. This is annoyingly complicated,
            # because the AUI designer(s) decided to
            # give the innermost layer an index of 0.
            #
            # So in order to put a new toolbar at the
            # innermost layer, we need to adjust the
            # layers of all other existing toolbars

            for p in self.__panels.values():
                if isinstance(p, ctrlpanel.ControlToolBar):
                    info = self.__auiMgr.GetPane(p)

                    # This is nasty - the agw.aui.AuiPaneInfo
                    # class doesn't have any publicly documented
                    # methods of querying its current state.
                    # So I'm accessing its undocumented instance
                    # attributes (determined by browsing the
                    # source code)
                    if info.IsDocked() and \
                       info.dock_direction == aui.AUI_DOCK_TOP:
                        info.Layer(info.dock_layer + 1)

            # When the toolbar contents change,
            # update the layout, so that the
            # toolbar's new size is accommodated
            panel.Bind(fsltoolbar.EVT_TOOLBAR_EVENT, self.__auiMgrUpdate)

        paneInfo.Caption(title)

        # Dock the pane at the position specified
        # by the location parameter
        if not floatPane:

            if location is None:
                if isToolbar: location = aui.AUI_DOCK_TOP
                else:         location = aui.AUI_DOCK_BOTTOM

            elif location == wx.TOP:    location = aui.AUI_DOCK_TOP
            elif location == wx.BOTTOM: location = aui.AUI_DOCK_BOTTOM
            elif location == wx.LEFT:   location = aui.AUI_DOCK_LEFT
            elif location == wx.RIGHT:  location = aui.AUI_DOCK_RIGHT

            # Make sure the pane is
            # resizable in case it
            # gets floated later on
            paneInfo.Direction(location) \
                    .Resizable(not isToolbar)

        # Or, for floating panes, centre the
        # floating pane on this ViewPanel
        else:

            selfPos    = self.GetScreenPosition().Get()
            selfSize   = self.GetSize().Get()
            selfCentre = (selfPos[0] + selfSize[0] * floatPos[0],
                          selfPos[1] + selfSize[1] * floatPos[1])

            paneSize = panel.GetBestSize().Get()
            panePos  = (selfCentre[0] - paneSize[0] * 0.5,
                        selfCentre[1] - paneSize[1] * 0.5)

            paneInfo.Float()                 \
                    .Resizable(True)         \
                    .Dockable(not floatOnly) \
                    .CloseButton(closeable)  \
                    .FloatingPosition(panePos)

        return paneInfo


    def isPanelOpen(self, panelType):
        """Returns ``True`` if a panel of type ``panelType`` is open,
        ``False`` otherwise.
        """
        return self.getPanel(panelType) is not None


    def getPanel(self, panelType):
        """If an instance of ``panelType`` exists, it is returned.
        Otherwise ``None`` is returned.
        """
        if panelType in self.__panels: return self.__panels[panelType]
        else:                          return None


    @actions.action
    def removeAllPanels(self):
        """Remove all control panels from this ``ViewPanel``."""
        for panelType in list(self.__panels.keys()):
            self.togglePanel(panelType)


    @actions.action
    def removeFromFrame(self):
        """Remove this ``ViewPanel`` from the :class:`.FSLeyesFrame`.

        Will raise an error if this ``ViewPanel`` is not in a
        ``FSLeyesFrame``.
        """
        self.frame.removeViewPanel(self)


    def getPanels(self):
        """Returns a list containing all control panels currently shown in this
        ``ViewPanel``.
        """
        return list(self.__panels.values())


    def getPanelInfo(self, panel):
        """Returns the ``AuiPaneInfo`` object which contains information about
        the given control panel.
        """
        return self.__auiMgr.GetPane(panel)


    @property
    def auiManager(self):
        """Returns the ``wx.lib.agw.aui.AuiManager`` object which manages the
        layout of this ``ViewPanel``.
        """
        return self.__auiMgr


    def getTools(self):
        """This method should be overridden by sub-classes (if necessary), and
        should return any ``action`` methods which should be added to the
        :class:`.FSLeyesFrame` *Tools* menu.

        See also the :meth:`.ActionProvider.getActions` method, which can
        also be overridden, and controls the actions which get added to the
        FSLeyes *settings* menu.
        """
        return []


    def __auiMgrUpdate(self, *args, **kwargs):
        """Called whenever a panel is added/removed to/from this ``ViewPanel``.

        Calls the ``Update`` method on the ``AuiManager`` instance that is
        managing this panel.

        :arg newPanel: Must be passed as a keyword argument. When a new panel
                       is added, it should be passed here.
        """

        newPanel = kwargs.pop('newPanel', None)

        # This method makes sure that size hints
        # for all existing and new panels are
        # set on their AuiPaneInfo objects, and
        # then calls AuiManager.Update.

        # We first loop through all panels, and
        # figure out their best sizes. Each entry
        # in this list is a tuple containing:
        #
        #    - Panel
        #    - AuiPaneInfo instance
        #    - Dock direction (None for floating panels)
        #    - Layer number (None for floating panels)
        #    - Minimum size
        bestSizes = []

        for panel in self.__panels.values():

            if isinstance(panel, ctrlpanel.ControlToolBar):
                continue

            pinfo = self.__auiMgr.GetPane(panel)

            # If the panel is floating, use its
            # current size as its 'best' size,
            # as otherwise the AuiManager will
            # immediately resize the panel to
            # its best size.
            if pinfo.IsFloating():
                dockDir  = None
                layer    = None
                bestSize = panel.GetSize().Get()

                # Unless its current size is tiny
                # (which probably means that it has
                # just been added)
                if bestSize[0] <= 20 or \
                   bestSize[1] <= 20:
                    bestSize = panel.GetBestSize().Get()

            else:
                dockDir  = pinfo.dock_direction
                layer    = pinfo.dock_layer
                bestSize = panel.GetBestSize().Get()

            bestSizes.append((panel, pinfo, dockDir, layer, bestSize))

        # Now we loop through one final time, and
        # set all of the necessary size hints on
        # the AuiPaneInfo instances.
        for panel, pinfo, dockDir, layer, bestSize in bestSizes:

            parent = panel.GetParent()

            # When a panel is added/removed from the AuiManager,
            # the position of floating panels seems to get reset
            # to their original position, when they were created.
            # Here, we explicitly set the position of each
            # floating frame, so the AuiManager doesn't move our
            # windows about the place.
            if pinfo.IsFloating() and \
               isinstance(parent, aui.AuiFloatingFrame):
                pinfo.FloatingPosition(parent.GetScreenPosition())

            # See comments in __init__ about
            # this silly 'float offset' thing
            floatSize = (bestSize[0] + self.__floatOffset[0],
                         bestSize[1] + self.__floatOffset[1])

            log.debug('New size for panel {} - '
                      'best: {}, float: {}'.format(
                          type(panel).__name__, bestSize, floatSize))

            pinfo.MinSize(     (1, 1))  \
                 .BestSize(    bestSize) \
                 .FloatingSize(floatSize) \
                 .Resizable(   True)

            # This is a terrible hack which forces
            # the AuiManager to grow a dock when a
            # new panel is added, which is bigger
            # than the existing dock contents.
            if panel is newPanel and not pinfo.IsFloating():
                docks = aui.FindDocks(self.__auiMgr._docks, dockDir, layer)
                for d in docks:
                    d.size = 0

        self.__auiMgr.Update()


    def __onPaneClose(self, ev=None, panel=None):
        """Called when the user closes a control (a.k.a. secondary) panel.
        Calls the
        :class:`.ControlPanel.destroy`/:class:`.ControlToolBar.destroy`
        method on the panel.
        """

        if ev is not None:
            ev.Skip()
            panel = ev.GetPane().window

        # If the user has grouped multiple control panels
        # into a single tabbed notebook, and then closed
        # the entire notebook, the AuiManager will generate
        # a single close event, and will pass us that
        # notebook. So we have to look in the notebook
        # to see which control panels were actually closed.
        if isinstance(panel, wx.lib.agw.aui.AuiNotebook):
            panels = [panel.GetPage(i) for i in range(panel.GetPageCount())]
        else:
            panels = [panel]

        for panel in list(panels):

            # note: in theory, all panels  should be sub-classes
            # of ControlPanel/ControlToolBar. But this check is
            # kept here to support third party scripts which don't
            # honour the FSLeyes plugin rules.
            if isinstance(panel, (ctrlpanel.ControlPanel,
                                  ctrlpanel.ControlToolBar)):

                # WTF AUI. Sometimes this method gets called
                # twice for a panel, the second time with a
                # reference to a wx._wxpyDeadObject; in such
                # situations, the Destroy method call below
                # would result in an exception being raised.
                if self.__panels.pop(type(panel), None) is None:
                    panels.remove(panel)

                # calling ControlPanel.destroy()
                # here -  wx.Destroy is done below
                else:
                    log.debug('Panel closed: %s', type(panel).__name__)
                    panel.destroy()

        # Destroy all the panels
        for panel in panels:

            # Even when the user closes a pane,
            # AUI does not detach said pane -
            # we have to do it manually
            self.__auiMgr.DetachPane(panel)
            wx.CallAfter(panel.Destroy)

        # Update interaction profile. We do not
        # consider multiple tabbed controls here.
        # If the closed control is associated with
        # an interaction profile, if no other other
        # open panels rely on the same destroy the
        # profile and restore the default profile
        #
        # We assume that, if a panel which requires
        # a custom profile was open, that profile
        # was active.
        #
        # See WTF AUI comment above for reason for
        # len(panels) guard
        if len(panels) > 0:
            profileCls   = panels[0].profileCls()
            closeProfile = True
            if profileCls is not None:
                for ctype in self.__panels:
                    cprofileCls = ctype.profileCls()
                    if cprofileCls is not None and \
                       issubclass(cprofileCls, profileCls):
                        closeProfile = False
                if closeProfile:
                    log.debug('Panel %s uses a custom interaction profile %s - '
                              'deactivating it and restoring default profile',
                              type(panels[0]).__name__, profileCls.__name__)
                    self.__profileManager.deactivateProfile()

        # Update the view panel layout
        wx.CallAfter(self.__auiMgrUpdate)


    def __onPerspectiveChange(self, ev):
        """Called on ``EVT_AUI_PERSPECTIVE_CHANGED`` events. Re-emits the
        event via the :meth:`events` notifier, with topic ``'aui_perspective'``.
        This is performed for the benefit of non-wx entities which need to
        know about layout changes.
        """
        self.events.notify(topic='aui_perspective')


class MyAuiFloatingFrame(auifm.AuiFloatingFrame):
    """Here I am monkey patching the
    ``wx.agw.aui.framemanager.AuiFloatingFrame.__init__`` method.

    I am doing this because I have observed some strange behaviour when running
    a remote instance of this application over an SSH/X11 session, with the X11
    server (i.e. the local machine) running in OS X. When a combobox is embedded
    in a floating frame (either a pane or a toolbar), its dropdown list appears
    underneath the frame, meaning that the user is unable to actually select any
    items from the list!

    I have only seen this behaviour when using XQuartz on macOS.

    Ultimately, this appears to be caused by the ``wx.FRAME_TOOL_WINDOW``
    style, as passed to the ``wx.MiniFrame`` constructor (from which the
    ``AuiFloatingFrame`` class derives). Removing this style flag fixes the
    problem, so this is exactly what I'm doing. I haven't looked any deeper
    into the situation.


    This class also overrieds the ``SetPaneWindow`` method, because under gtk3,
    the maximum size if a frame musr be set.
    """

    def __init__(self, *args, **kwargs):
        """My new constructor, which makes sure that the ``FRAME_TOOL_WINDOW``
        style is not passed through to the ``AuiFloatingFrame`` constructor
        """

        if 'style' in kwargs:
            style = kwargs['style']

        # This is the default style, as defined
        # in the AuiFloatingFrame constructor
        else:
            style = (wx.FRAME_TOOL_WINDOW     |
                     wx.FRAME_FLOAT_ON_PARENT |
                     wx.FRAME_NO_TASKBAR      |
                     wx.CLIP_CHILDREN)

        if fwidgets.inSSHSession():
            style &= ~wx.FRAME_TOOL_WINDOW

        kwargs['style'] = style

        super().__init__(*args, **kwargs)


    def SetPaneWindow(self, pane):
        """Make sure that floated toolbars are sized correctly.
        """
        super().SetPaneWindow(pane)
        if isinstance(pane.window, ctrlpanel.ControlToolBar):
            size = self.GetBestSize()
            self.SetMaxSize(size)


def _AuiDockingGuide_init(self, *args, **kwargs):
    """I am also monkey-patching the
    ``wx.lib.agw.aui.AuiDockingGuide.__init__`` method, because in this
    instance, when running over SSH/X11, the ``wx.FRAME_TOOL_WINDOW`` style
    seems to result in the docking guide frames being given title bars, which
    is quite undesirable.

    I cannot patch the entire class in the aui package, because it is used
    as part of a class hierarchy. So I am just patching the method.
    """

    if 'style' in kwargs:
        style = kwargs['style']

    # This is the default style, as defined
    # in the AuiDockingGuide constructor
    else:
        style = (wx.FRAME_TOOL_WINDOW |
                 wx.FRAME_STAY_ON_TOP |
                 wx.FRAME_NO_TASKBAR  |
                 wx.NO_BORDER)

    if fwidgets.inSSHSession():
        style &= ~wx.FRAME_TOOL_WINDOW

    kwargs['style'] = style

    _AuiDockingGuide_real_init(self, *args, **kwargs)


aui  .AuiFloatingFrame       = MyAuiFloatingFrame
auifm.AuiFloatingFrame       = MyAuiFloatingFrame
_AuiDockingGuide_real_init   = aui.AuiDockingGuide.__init__
aui.AuiDockingGuide.__init__ = _AuiDockingGuide_init
