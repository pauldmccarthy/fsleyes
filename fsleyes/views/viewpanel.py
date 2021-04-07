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


import logging

import                                  wx
import wx.lib.agw.aui                as aui
import wx.lib.agw.aui.framemanager   as auifm

import fsl.utils.notifier            as notifier
import fsl.utils.deprecated          as deprecated
import fsleyes_widgets               as fwidgets

import fsleyes.panel                 as fslpanel
import fsleyes.toolbar               as fsltoolbar
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
    :meth:`getCurrentProfile` method. See the :mod:`.profiles` package for
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
        # associated with a control panel. If a
        # control+profile is open, and the user opens
        # another control+profile, the first one is
        # destroyed, and the new one created. A ref
        # to the active control is saved for this
        # purpose.This all happens in togglePanel.
        self.__activeControl  = None
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

        # Notifier instance for emitting events
        self.__events = notifier.Notifier()

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
        self.__auiMgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onPaneClose)

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


    def destroy(self):
        """Removes some property listeners, destroys all child panels,
        destroys the :class:`.ProfileManager`, and ``AuiManager``, and
        calls :meth:`.FSLeyesPanel.destroy`.
        """

        # Make sure that any control panels are correctly destroyed
        for panel in self.__panels.values():
            self.__auiMgr.DetachPane(panel)
            panel.destroy()

        # Clear ref to the events Notifier - it
        # will drop refs to any event handlers
        self.__events = None

        # Remove listeners from the overlay
        # list and display context
        lName = 'ViewPanel_{}'.format(self.name)

        self.overlayList.removeListener('overlays',        lName)
        self.displayCtx .removeListener('selectedOverlay', lName)

        # Disable the  ProfileManager
        self.__profileManager.destroy()

        # Un-initialise the AUI manager
        self.__auiMgr.Unbind(aui.EVT_AUI_PANE_CLOSE)
        self.__auiMgr.Update()
        self.__auiMgr.UnInit()

        # The AUI manager does not clear its
        # reference to this panel, so let's
        # do it here.
        self.__auiMgr._frame  = None
        self.__profileManager = None
        self.__auiMgr         = None
        self.__panels         = None
        self.__centrePanel    = None

        fslpanel.FSLeyesPanel.destroy(self)


    @property
    def events(self):
        """Return a reference to a :class:`.Notifier` instance which can be
        used to be notified when certain events occur. Currently the only
        event topic which occurs is ``'profile'``, when the current
        interaction profile changes.
        """
        return self.__events


    def initProfile(self, defaultProfile):
        """Must be called by subclasses, after they have initialised all
        of the attributes which may be needed by their associated
        :class:`.Profile` instances.

        :arg defaultProfile: Default profile type
        """
        self.__profileManager.activateProfile(defaultProfile)


    def getCurrentProfile(self):
        """Returns the :class:`.Profile` instance currently in use. """
        return self.__profileManager.getCurrentProfile()


    @property
    def centrePanel(self):
        """Returns the primary (centre) panel on this ``ViewPanel``.
        """
        return self.__centrePanel


    @deprecated.deprecated('0.16.0', '1.0.0', 'Use centrePanel instead')
    def getCentrePanel(self):
        """Returns the primary (centre) panel on this ``ViewPanel``.
        """
        return self.centrePanel


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


    @deprecated.deprecated('0.16.0', '1.0.0', 'Use centrePanel instead')
    def setCentrePanel(self, panel):
        """Set the primary centre panel for this ``ViewPanel``. This method
        is only intended to be called by sub-classes.
        """
        self.centrePanel = panel


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
                     ``floatPane``, ``profileCls``, ``floatOnly``,
                     ``floatPos``, ``closeable``, or ``location``, as
                     arguments with those names will get eaten by this method
                     before they can be passed to the constructor.
        """

        if len(kwargs) == 0:
            kwargs = panelType.defaultLayout()
            if kwargs is None:
                kwargs = {}

        location   = kwargs.pop('location',  None)
        floatPane  = kwargs.pop('floatPane', False)
        floatOnly  = kwargs.pop('floatOnly', False)
        closeable  = kwargs.pop('closeable', True)
        title      = kwargs.pop('title',     None)
        floatPos   = kwargs.pop('floatPos',  (0.5, 0.5))
        profileCls = panelType.profileCls()

        if title is None:
            title = strings.titles.get(panelType, type(panelType).__name__)

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
        # profile, create it first, as the panel.__init__ should
        # be allowed to assume that its profile is ready to go.
        if profileCls is not None:

            # Another control panel+custom profile is active.
            # We only allow one custom profile at a time, so
            # let's destroy the other one.
            if self.__activeControl is not None:
                self.__onPaneClose(None, self.__activeControl)
            self.__profileManager.activateProfile(profileCls)
            self.__events.notify(topic='profile')

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


    @deprecated.deprecated('0.16.0', '1.0.0', 'Use auiManager instead')
    def getAuiManager(self):
        """Returns the ``wx.lib.agw.aui.AuiManager`` object which manages the
        layout of this ``ViewPanel``.
        """
        return self.__auiMgr


    def getTools(self):
        """This method should be overridden by sub-classes (if necessary), and
        should return any ``action`` methods which should be added to the
        :class:`.FSLeyesFrame` *Tools* menu.
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
                    log.debug('Panel closed: {}'.format(type(panel).__name__))
                    panel.destroy()

            # This control is associated with an
            # interaction profile - destroy it,
            # and restore the default profile
            if panel is self.__activeControl:
                self.__activeControl = None
                self.__profileManager.deactivateProfile()
                self.__events.notify(topic='profile')

        # Destroy all the panels
        for panel in panels:

            # Even when the user closes a pane,
            # AUI does not detach said pane -
            # we have to do it manually
            self.__auiMgr.DetachPane(panel)
            wx.CallAfter(panel.Destroy)

        # Update the view panel layout
        wx.CallAfter(self.__auiMgrUpdate)


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
