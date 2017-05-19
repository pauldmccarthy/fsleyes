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

import                   wx
import wx.lib.agw.aui as aui

import fsl.data.image         as fslimage
import fsleyes_props          as props

import fsleyes.panel          as fslpanel
import fsleyes.toolbar        as fsltoolbar
import fsleyes.profiles       as profiles
import fsleyes.displaycontext as fsldisplay
import fsleyes.strings        as strings
import fsleyes.actions        as actions



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
    via the :meth:`setCentrePanel` method, and secondary panels can be
    added/removed to/from with the :meth:`togglePanel` method. The current
    state of a secondary panel (i.e. whether one is open or not) can be
    queried with the :meth:`isPanelOpen` method, and existing secondary panels
    can be accessed via the :meth:`getPanel` method.  Secondary panels must be
    derived from either the :class:`.FSLeyesPanel` or :class:`.FSLeyesToolBar`
    base-classes.


    **Profiles**


    Some ``ViewPanel`` classes have relatively complex mouse and keyboard
    interaction behaviour (e.g. the :class:`.OrthoPanel` and
    :class:`.LightBoxPanel`). The logic defines this interaction is provided
    by a :class:`.Profile` instance, and is managed by a
    :class:`.ProfileManager`.  Some ``ViewPanel`` classes have multiple
    interaction profiles - for example, the :class:`.OrthoPanel` has a
    ``view`` profile, and an ``edit`` profile. The current interaction
    profile can be changed with the :attr:`profile` property, and can be
    accessed with the :meth:`getCurrentProfile` method. See the
    :mod:`.profiles` package for more information on interaction profiles.


    **Programming interface**


    The following methods are available on a ``Viewpanel`` for programmatically
    controlling its display and layout:


    .. autosummary::
       :nosignatures:

       togglePanel
       isPanelOpen
       getPanel
       getPanels
       removeAllPanels
       getPanelInfo
       getAuiManager
    """


    profile = props.Choice()
    """The current interaction profile for this ``ViewPanel``. """


    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``ViewPanel``. All arguments are passed through to the
        :class:`.FSLeyesPanel` constructor.
        """

        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, frame)

        self.__profileManager = profiles.ProfileManager(
            self, overlayList, displayCtx)

        # The centrePanel attribute stores a reference
        # to the main (centre) panel on this ViewPanel.
        # It is set by sub-class implementations via
        # the setCentrePanel method.
        #
        # The panels dictionary stores a collection
        # of {type : instance} mappings of active
        # FSLeyes control panels that are contained
        # in this view panel.
        self.__centrePanel = None
        self.__panels      = {}

        # See note in FSLeyesFrame about
        # the user of aero docking guides.
        self.__auiMgr = aui.AuiManager(
            self,
            agwFlags=(aui.AUI_MGR_RECTANGLE_HINT          |
                      aui.AUI_MGR_NO_VENETIAN_BLINDS_FADE |
                      aui.AUI_MGR_ALLOW_FLOATING          |
                      aui.AUI_MGR_AERO_DOCKING_GUIDES     |
                      aui.AUI_MGR_LIVE_RESIZE))

        self.__auiMgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onPaneClose)

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'ViewPanel_{}'.format(self._name)

        self.addListener('profile', lName, self.__profileChanged)

        overlayList.addListener('overlays',
                                lName,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                lName,
                                self.__selectedOverlayChanged)

        self.__selectedOverlay = None
        self.__selectedOverlayChanged()

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
        for panelType, panel in self.__panels.items():
            panel.destroy()

        # Remove listeners from the overlay
        # list and display context
        lName = 'ViewPanel_{}'.format(self._name)

        self             .removeListener('profile',         lName)
        self._overlayList.removeListener('overlays',        lName)
        self._displayCtx .removeListener('selectedOverlay', lName)

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

        fslpanel.FSLeyesPanel.destroy(self)


    def initProfile(self):
        """Must be called by subclasses, after they have initialised all
        of the attributes which may be needed by their associated
        :class:`.Profile` instances.
        """
        self.__profileChanged()


    def getCurrentProfile(self):
        """Returns the :class:`.Profile` instance currently in use. """
        return self.__profileManager.getCurrentProfile()


    def setCentrePanel(self, panel):
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
        """Add/remove the secondary panel of the specified type to/from this
        ``ViewPanel``.

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

        :arg kwargs:    All keyword arguments, apart from ``floatPane`` and
                        ``location``, are passed to the ``panelType``
                        constructor.

        .. note::       The ``panelType`` type must be a sub-class of
                        :class:`.FSLeyesPanel` or :class:`.FSLeyesToolBar`,
                        which can be created like so::

                            panel = panelType(parent,
                                              overlayList,
                                              displayCtx,
                                              frame,
                                              *args,
                                              **kwargs)

        .. warning::    Do not define a control (a.k.a. secondary) panel
                        constructor to accept arguments with the names
                        ``floatPane``, ``floatOnly``, ``floatPos``,
                        ``closeable``, or ``location``, as arguments with
                        those names will get eaten by this method before they
                        can be passed to the constructor.
        """

        location  = kwargs.pop('location',  None)
        floatPane = kwargs.pop('floatPane', False)
        floatOnly = kwargs.pop('floatOnly', False)
        closeable = kwargs.pop('closeable', True)
        floatPos  = kwargs.pop('floatPos',  (0.5, 0.5))

        if location not in (None, wx.TOP, wx.BOTTOM, wx.LEFT, wx.RIGHT):
            raise ValueError('Invalid value for location')

        window = self.__panels.get(panelType, None)

        # The panel is already open - close it
        if window is not None:
            self.__onPaneClose(None, window)
            return

        # Otherwise, create a new panel of the specified type.
        # The PaneInfo Name is the control panel class name -
        # this is used for saving and restoring perspectives.
        paneInfo  = aui.AuiPaneInfo().Name(panelType.__name__)
        window    = panelType(self,
                              self.getOverlayList(),
                              self.getDisplayContext(),
                              self.getFrame(),
                              *args,
                              **kwargs)
        isToolbar = isinstance(window, fsltoolbar.FSLeyesToolBar)

        if isToolbar:

            # ToolbarPane sets the panel layer to 10
            paneInfo.ToolbarPane()

            if window.GetOrient() == wx.VERTICAL:
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
                if isinstance(p, fsltoolbar.FSLeyesToolBar):
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
            window.Bind(fsltoolbar.EVT_TOOLBAR_EVENT, self.__auiMgrUpdate)

        paneInfo.Caption(strings.titles[window])

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

            paneInfo.Direction(location)

        # Or, for floating panes, centre the
        # floating pane on this ViewPanel
        else:

            selfPos    = self.GetScreenPosition().Get()
            selfSize   = self.GetSize().Get()
            selfCentre = (selfPos[0] + selfSize[0] * floatPos[0],
                          selfPos[1] + selfSize[1] * floatPos[1])

            paneSize = window.GetBestSize().Get()
            panePos  = (selfCentre[0] - paneSize[0] * 0.5,
                        selfCentre[1] - paneSize[1] * 0.5)

            paneInfo.Float()                 \
                    .Dockable(not floatOnly) \
                    .CloseButton(closeable)  \
                    .FloatingPosition(panePos)


        self.__auiMgr.AddPane(window, paneInfo)
        self.__panels[panelType] = window
        self.__auiMgrUpdate()


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

        for panelType, instance in list(self.__panels.items()):
            self.togglePanel(panelType)


    def getCentrePanel(self):
        """Returns the primary (centre) panel on this ``ViewPanel``.
        """
        return self.__centrePanel


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


    def getAuiManager(self):
        """Returns the ``wx.lib.agw.aui.AuiManager`` object which manages the
        layout of this ``ViewPanel``.
        """
        return self.__auiMgr


    def __selectedOverlayChanged(self, *a):
        """Called when the :class:`.OverlayList` or
        :attr:`.DisplayContext.selectedOverlay` changes.

        This method is slightly hard-coded and hacky. For the time being,
        profiles called ``edit`` profiles are only supported for ``volume``
        overlay types. This method checks the type of the selected overlay,
        and disables the ``edit`` profile option (if it is an option), so the
        user can only choose an ``edit`` profile on ``volume`` overlay types.
        """

        lName   = 'ViewPanel_{}'.format(self._name)
        overlay = self._displayCtx.getSelectedOverlay()

        if self.__selectedOverlay not in (None, overlay):
            try:
                d = self._displayCtx.getDisplay(self.__selectedOverlay)

                d.removeListener('overlayType', lName)

            # The overlay has been removed
            except fsldisplay.InvalidOverlayError:
                pass

        self.__selectedOverlay = overlay

        if overlay is None:
            return

        # If the overlay is of a compatible type,
        # register for overlay type changes, as
        # these will affect the profile property
        if isinstance(overlay, fslimage.Image):
            display = self._displayCtx.getDisplay(overlay)
            display.addListener('overlayType',
                                lName,
                                self.__configureProfile,
                                overwrite=True)

        self.__configureProfile()


    def __configureProfile(self, *a):
        """Called by the :meth:`__selectedOverlayChanged` method. Implements
        the hacky logic described in the documentation for that method.
        """

        overlay     = self.__selectedOverlay
        display     = self._displayCtx.getDisplay(overlay)
        profileProp = self.getProp('profile')

        # edit profile is not an option -
        # nothing to be done
        if 'edit' not in profileProp.getChoices(self):
            return

        if not isinstance(overlay, fslimage.Image) or \
           display.overlayType not in ('volume', 'label', 'mask'):

            # change profile if needed,
            if self.profile == 'edit':
                self.profile = 'view'

            # and disable edit profile
            log.debug('{}: disabling edit profile for '
                      'selected overlay {}'.format(
                          type(self).__name__, overlay))
            profileProp.disableChoice('edit', self)

        # Otherwise make sure edit
        # is enabled for volume images
        else:
            log.debug('{}: Enabling edit profile for '
                      'selected overlay {}'.format(
                          type(self).__name__, overlay))
            profileProp.enableChoice('edit', self)


    def __profileChanged(self, *a):
        """Called when the current :attr:`profile` property changes. Tells the
        :class:`.ProfileManager` about the change.

        The ``ProfileManager`` will create a new :class:`.Profile` instance of
        the appropriate type.
        """

        self.__profileManager.changeProfile(self.profile)


    def __auiMgrUpdate(self, *a):
        """Called whenever a panel is added/removed to/from this ``ViewPanel``.

        Calls the ``Update`` method on the ``AuiManager`` instance that is
        managing this panel.
        """

        # When a panel is added/removed from the AuiManager,
        # the position of floating panels seems to get reset
        # to their original position, when they were created.
        # Here, we explicitly set the position of each
        # floating frame, so the AuiManager doesn't move our
        # windows about the place.
        #
        # We also explicitly tell the AuiManager what the
        # current minimum and best sizes are for every panel
        for panel in self.__panels.values():

            if isinstance(panel, fsltoolbar.FSLeyesToolBar):
                continue

            paneInfo = self.__auiMgr.GetPane(panel)
            parent   = panel.GetParent()
            minSize  = panel.GetMinSize().Get()

            # If the panel is floating, use its
            # current size as its 'best' size,
            # as otherwise it will immediately
            # resize the panel to its best size
            if paneInfo.IsFloating():
                bestSize = panel.GetSize().Get()

                # Unless it's current size is less
                # than its minimum size (which probably
                # means that it has just been added)
                if bestSize[0] < minSize[0] or \
                   bestSize[1] < minSize[1]:
                    bestSize = panel.GetBestSize().Get()

            else:
                bestSize = panel.GetBestSize().Get()

            # See comments in __init__ about
            # this silly 'float offset' thing
            floatSize = (bestSize[0] + self.__floatOffset[0],
                         bestSize[1] + self.__floatOffset[1])

            log.debug('New size for panel {} - min: {}, '
                      'best: {}, float: {}'.format(
                          type(panel).__name__, minSize, bestSize, floatSize))

            paneInfo.MinSize(     minSize)  \
                    .BestSize(    bestSize) \
                    .FloatingSize(floatSize)

            # Re-position floating panes, otherwise
            # the AuiManager will reset their position
            if paneInfo.IsFloating() and \
               isinstance(parent, aui.AuiFloatingFrame):
                paneInfo.FloatingPosition(parent.GetScreenPosition())

        self.__auiMgr.Update()


    def __onPaneClose(self, ev=None, panel=None):
        """Called when the user closes a control (a.k.a. secondary) panel.
        Calls the
        :class:`.FSLeyesPanel.destroy`/:class:`.FSLeyesToolBar.destroy`
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

            if isinstance(panel, (fslpanel  .FSLeyesPanel,
                                  fsltoolbar.FSLeyesToolBar)):

                # WTF AUI. Sometimes this method gets called
                # twice for a panel, the second time with a
                # reference to a wx._wxpyDeadObject; in such
                # situations, the Destroy method call below
                # would result in an exception being raised.
                if self.__panels.pop(type(panel), None) is None:
                    panels.remove(panel)

                # calling fslpanel.FSLeyesPanel.destroy()
                # here -  wx.Destroy is done below
                else:
                    log.debug('Panel closed: {}'.format(type(panel).__name__))
                    panel.destroy()

        # Destroy all the panels
        for panel in panels:

            # Even when the user closes a pane,
            # AUI does not detach said pane -
            # we have to do it manually
            self.__auiMgr.DetachPane(panel)
            wx.CallAfter(panel.Destroy)

        # Update the view panel layout
        wx.CallAfter(self.__auiMgrUpdate)


#
# Here I am monkey patching the
# wx.agw.aui.framemanager.AuiFloatingFrame.__init__ method.
#
#
# I am doing this because I have observed some strange behaviour when running
# a remote instance of this application over an SSH/X11 session, with the X11
# server (i.e. the local machine) running in OS X. When a combobox is embedded
# in a floating frame (either a pane or a toolbar), its dropdown list appears
# underneath the frame, meaning that the user is unable to actually select any
# items from the list!
#
# I have only seen this behaviour when using XQuartz 2.7.6, running under OSX
# 10.9 Mavericks.
#
# Ultimately, this appears to be caused by the wx.FRAME_TOOL_WINDOW style, as
# passed to the wx.MiniFrame constructor (from which the AuiFloatingFrame
# class derives). Removing this style flag fixes the problem, so this is
# exactly what I'm doing. I haven't looked any deeper into the situation.
#


# My new constructor, which makes sure that
# the FRAME_TOOL_WINDOW style is not passed
# through to the AuiFloatingFrame constructor
def AuiFloatingFrame__init__(*args, **kwargs):

    if 'style' in kwargs:
        style = kwargs['style']

    # This is the default style, as defined
    # in the AuiFloatingFrame constructor
    else:
        style = (wx.FRAME_TOOL_WINDOW     |
                 wx.FRAME_FLOAT_ON_PARENT |
                 wx.FRAME_NO_TASKBAR      |
                 wx.CLIP_CHILDREN)

    style &= ~wx.FRAME_TOOL_WINDOW

    kwargs['style'] = style

    return AuiFloatingFrame__real__init__(*args, **kwargs)

# Store a reference to the real constructor, and
# Patch my constructor in to the class definition.
AuiFloatingFrame__real__init__ = aui.AuiFloatingFrame.__init__
aui.AuiFloatingFrame.__init__  = AuiFloatingFrame__init__

# I am also monkey-patching the wx.lib.agw.aui.AuiDockingGuide.__init__ method,
# because in this instance, when running over SSH/X11, the wx.FRAME_TOOL_WINDOW
# style seems to result in the docking guide frames being given title bars,
# which is quite undesirable.
def AuiDockingGuide__init__(*args, **kwargs):

    if 'style' in kwargs:
        style = kwargs['style']

    # This is the default style, as defined
    # in the AuiDockingGuide constructor
    else:
        style = (wx.FRAME_TOOL_WINDOW |
                 wx.FRAME_STAY_ON_TOP |
                 wx.FRAME_NO_TASKBAR  |
                 wx.NO_BORDER)

    style &= ~wx.FRAME_TOOL_WINDOW

    kwargs['style'] = style

    return AuiDockingGuide__real__init__(*args, **kwargs)


AuiDockingGuide__real__init__ = aui.AuiDockingGuide.__init__
aui.AuiDockingGuide.__init__  = AuiDockingGuide__init__
