#!/usr/bin/env python
#
# The profiles module contains logic for mouse-keyboard interaction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`profiles` package contains logic for mouse/keyboard interaction
with :class:`.ViewPanel` panels.

This logic is encapsulated in two classes:

 - The :class:`Profile` class is intended to be subclassed. A :class:`Profile`
   instance contains the mouse/keyboard event handlers for a particular type
   of ``ViewPanel`` to allow the user to interact with the view in a
   particular way. For example, the :class:`.OrthoViewProfile` class allows
   the user to navigate through the display space in an :class:`.OrthoPanel`
   canvas, whereas the :class:`.OrthoEditProfile` class contains interaction
   logic for selecting and editing :class:`.Image` voxels in an ``OrthoPanel``.

 - The :class:`ProfileManager` class is used by ``ViewPanel`` instances to
   create and change the ``Profile`` instance currently in use.


The :mod:`.profilemap` module contains mappings between ``ViewPanel`` types,
and their corresponding ``Profile`` types.
"""

import logging
import inspect

import wx

import props

import fsl.fsleyes.actions as actions


log = logging.getLogger(__name__)


class ProfileManager(object):
    """Manages creation/registration/de-registration of :class:`Profile`
    instances for a :class:`.ViewPanel` instance.

    A :class:`ProfileManager` instance is created and used by every
    :class:`.ViewPanel` instance. The :mod:`.profilemap` module defines the
    :class:`Profile` types which should used for specific :class:`.ViewPanel`
    types.
    """


    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create a :class:`ProfileManager`.

        :arg viewPanel:   The :class:`.ViewPanel` instance which this
                          :class:`ProfileManager` is to manage.
        
        :arg overlayList: The :class:`.OverlayList` instance containing the
                          overlays that are being displayed.
        
        :arg displayCtx:  The :class:`.DisplayContext` instance which defines
                          how overlays are being displayed.
        """
        import profilemap
        
        self.__viewPanel      = viewPanel
        self.__viewCls        = viewPanel.__class__
        self.__overlayList    = overlayList
        self.__displayCtx     = displayCtx
        self.__currentProfile = None

        profileProp = viewPanel.getProp('profile')
        profilez    = profilemap.profiles.get(viewPanel.__class__, [])

        for profile in profilez:
            profileProp.addChoice(profile, instance=viewPanel)

        if len(profilez) > 0:
            viewPanel.profile = profilez[0]


    def destroy(self):
        """This method must be called by the owning :class:`.ViewPanel` when
        it is about to be destroyed (or when it no longer needs a
        ``ProfileManager``).

        This method destroys the current :class:`Profile` (if any), and
        clears some internal object references to avoid memory leaks.
        """
        if self.__currentProfile is not None:
            self.__currentProfile.deregister()
            self.__currentProfile.destroy()
            
        self.__currentProfile    = None
        self.__viewPanel         = None
        self.__overlayList       = None
        self.__overlaydisplayCtx = None


    def getCurrentProfile(self):
        """Returns the :class:`Profile` instance currently in use."""
        return self.__currentProfile

        
    def changeProfile(self, profile):
        """Deregisters the current :class:`Profile` instance (if necessary),
        and creates a new one corresponding to the named profile.
        """

        import profilemap

        profileCls = profilemap.profileHandlers[self.__viewCls, profile]

        # the current profile is the requested profile
        if (self.__currentProfile is not None) and \
           (self.__currentProfile.__class__ is profileCls):
            return

        if self.__currentProfile is not None:
            log.debug('Deregistering {} profile from {}'.format(
                self.__currentProfile.__class__.__name__,
                self.__viewCls.__name__))
            self.__currentProfile.deregister()
            self.__currentProfile.destroy()
            self.__currentProfile = None
               
        self.__currentProfile = profileCls(self.__viewPanel,
                                           self.__overlayList,
                                           self.__displayCtx)
        
        log.debug('Registering {} profile with {}'.format(
            self.__currentProfile.__class__.__name__,
            self.__viewCls.__name__))
        
        self.__currentProfile.register()


class Profile(props.SyncableHasProperties, actions.ActionProvider):
    """A :class:`Profile` class implements keyboard/mouse interaction behaviour
    for a :class:`.ViewPanel` instance.

    
    Subclasses should specify at least one *mode* of operation, which defines
    a sort of sub-profile. The current mode can be changed with the
    :attr:`mode` property.


    Subclasses must also override the :meth:`getEventTargets` method, to
    return the :mod:`wx` objects that are to be the targets for mouse/keyboard
    interaction.

    
    .. note:: The ``Profile`` class currently assumes that all objects returned
              by the :meth:`getEventTargets` method are :class:`.SliceCanvas`
              instances.

    
    In order to receive mouse or keyboard events, subclasses simply need to
    implement methods which handle the events of interest for the relevant
    mode, and name them appropriately. The name of a method handler must be 
    of the form::

    
        _[modeName]Mode[eventName]

    
    where ``modeName`` is an identifier for the profile mode (see the
    :meth:`__init__` method), and ``eventName`` is one of the following:
    
      - ``LeftMouseMove``
      - ``LeftMouseDown``
      - ``LeftMouseDrag``
      - ``LeftMouseUp``
      - ``RightMouseMove``
      - ``RightMouseDown``
      - ``RightMouseDrag``
      - ``RightMouseUp`` 
      - ``MiddleMouseMove``
      - ``MiddleMouseDown``
      - ``MiddleMouseDrag``
      - ``MiddleMouseUp``
      - ``MouseWheel``
      - ``MouseEnter``
      - ``MouseLeave`` 
      - ``Char``

    
    For example, if a particular profile has defined a mode called ``nav``,
    and is interested in left clicks, the profile class must provide a method
    called ``_navModeLeftMouseDown``. Then, whenever the profile is in the
    ``nav`` mode, this method will be called on left mouse clicks.

    
    The :mod:`.profilemap` module contains a ``tempModeMap`` which, for each
    profile and each mode, defines a keyboard modifier which may be used to
    temporarily redirect mouse/keyboard events to the handlers for a different
    mode. For example, if while in ``nav`` mode, you would like the user to be
    able to switch to ``zoom`` mode with the control key, you can add a
    temporary mode map in the ``tempModeMap``.


    The :mod:`.profilemap` module contains another dictionary, called the
    ``altHandlerMap``. This dictionary allows you to re-use event handlers
    that have been defined for one mode in another mode. For example, if you
    would like right clicks in ``zoom`` mode to behave like left clicks in
    ``nav`` mode, you can set up such a mapping using the
    ``altHandlerMap`` dictionary.

    
    As the ``Profile`` class derives from the :class:`.ActionProvider`
    class, ``Profile`` subclasses may define properties and actions for
    the user to configure the profile behaviour, and/or to perform any
    relevant actions.

    The following instance attributes are present on a ``Profile`` instance,
    intended to be accessed by sub-classes:

    ================ =======================================================
    ``_viewPanel``   The :class:`ViewPanel` which is using this ``Profile``.
    ``_overlayList`` A :class:`.OverlayList` instance.
    ``_displayCtx``  A :class:`.DisplayContext` instance.
    ``_name``        A unique name for this ``Profile`` instance.
    ================ =======================================================
    """


    mode = props.Choice()
    """The current profile mode - by default this is empty, but subclasses
    may specify the choice options in the :class:`__init__` method.
    """
    

    def __init__(self,
                 viewPanel,
                 overlayList,
                 displayCtx,
                 modes=None):
        """Create a ``Profile`` instance.

        :arg viewPanel:   The :class:`.ViewPanel` instance for which this
                          ``Profile`` instance defines mouse/keyboard
                          interaction behaviour.

        :arg overlayList: The :class:`.OverlayList` instance which contains
                          the list of overlays being displayed.

        :arg displayCtx:  The :class:`.DisplayContext` instance which defines
                          how the overlays are to be displayed.

        :arg modes:       A sequence of strings, containing the mode
                          identifiers for this profile. These are added as
                          options on the :attr:`mode` property.
        """

        actions.ActionProvider     .__init__(self)
        props.SyncableHasProperties.__init__(self)
        
        self._viewPanel   = viewPanel
        self._overlayList = overlayList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))

        # Maps which define temporarymodes/alternate
        # handlers when keyboard modifiers are used,
        # or when a handler for a particular event
        # is not defined
        self.__tempModeMap   = {}
        self.__altHandlerMap = {}
        
        # some attributes to keep track
        # of mouse event locations
        self.__lastMousePos  = None
        self.__lastCanvasPos = None
        self.__mouseDownPos  = None
        self.__canvasDownPos = None

        # Add all of the provided modes
        # as options to the mode property
 
        if modes is None:
            modes = []

        modeProp = self.getProp('mode')
        
        for mode in modes:
            modeProp.addChoice(mode, instance=self)

        if len(modes) > 0:
            self.mode = modes[0]

        # Configure temporary modes and alternate
        # event handlers - see the profilemap
        # module
        import profilemap
        
        for cls in inspect.getmro(self.__class__):
            
            tempModes   = profilemap.tempModeMap  .get(cls, {})
            altHandlers = profilemap.altHandlerMap.get(cls, {})

            for (mode, keymod), tempMode in tempModes.items():
                self.addTempMode(mode, keymod, tempMode)

            for (mode, handler), (altMode, altHandler) in altHandlers.items():
                self.addAltHandler(mode, handler, altMode, altHandler)
                
        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))

        
    def __del__(self):
        """Prints a log message. """
        if log:
            log.memory('{}.del ({})'.format(type(self).__name__, id(self)))

                
    def destroy(self):
        """This method must be called when this ``Profile`` is no longer
        needed - it is typically called by a :class:`ProfileManager`.

        Clears references to the display context, view panel, and overlay
        list, and calls :meth:`.ActionProvider.destroy`.
        """
        actions.ActionProvider.destroy(self)
        self._viewPanel   = None
        self._overlayList = None
        self._displayCtx  = None


    def getEventTargets(self):
        """Must be overridden by subclasses, to return a sequence of
        :mod:`wx` objects that are the targets of mouse/keyboard interaction.

        .. note:: It is currently assumed that all of the objects in the
                  sequence derive from the :class:`.SliceCanvas` class.
        """
        raise NotImplementedError('Profile subclasses must implement '
                                  'the getEventTargets method')


    def getMouseDownLocation(self):
        """If the mouse is currently down, returns a 2-tuple containing the
        x/y mouse coordinates, and the corresponding 3D display space
        coordinates, of the mouse down event. Otherwise, returns
        ``(None, None)``.
        """
        return self.__mouseDownPos, self.__canvasDownPos

    
    def getLastMouseLocation(self):
        """Returns a 2-tuple containing the most recent x/y mouse coordinates,
        and the corresponding 3D display space coordinates. 
        """
        return self.__lastMousePos, self.__lastCanvasPos


    def addTempMode(self, mode, modifier, tempMode):
        """Add a temporary mode to this ``Profile``, in addition to those
        defined in the :attr:`.profilemap.tempModeMap` dictionary.

        :arg mode:     The mode to change from.
        
        :arg modifier: A keyboard modifier which will temporarily
                       change the mode from ``mode`` to ``tempMode``.
        
        :arg tempMode: The temporary mode which the ``modifier`` key will
                       change into.
        """ 
        self.__tempModeMap[mode, modifier] = tempMode

        
    def addAltHandler(self, mode, event, altMode, altEvent):
        """Add an alternate handler to this ``Profile``, in addition to
        those already defined in the :attr:`.profilemap.altHandleMap`
        dictionary.

        :arg mode:     The source mode.
        
        :arg event:    Name of the event to handle (e.g. ``LeftMouseDown``).
        
        :arg altMode:  The mode for which the handler is defined.
        
        :arg altEvent: The event name for which the handler is defined.
        """
        self.__altHandlerMap[mode, event] = (altMode, altEvent)

    
    def register(self):
        """This method must be called to register this ``Profile``
        instance as the target for mouse/keyboard events. This method
        is called by the :class:`ProfileManager`.

        Subclasses may override this method to performa any initialisation,
        but must make sure to call this implementation. 
        """
        for t in self.getEventTargets():
            t.Bind(wx.EVT_LEFT_DOWN,    self.__onMouseDown)
            t.Bind(wx.EVT_MIDDLE_DOWN,  self.__onMouseDown)
            t.Bind(wx.EVT_RIGHT_DOWN,   self.__onMouseDown)
            t.Bind(wx.EVT_LEFT_UP,      self.__onMouseUp)
            t.Bind(wx.EVT_MIDDLE_UP,    self.__onMouseUp)
            t.Bind(wx.EVT_RIGHT_UP,     self.__onMouseUp)
            t.Bind(wx.EVT_MOTION,       self.__onMouseMove)
            t.Bind(wx.EVT_MOUSEWHEEL,   self.__onMouseWheel)
            t.Bind(wx.EVT_ENTER_WINDOW, self.__onMouseEnter)
            t.Bind(wx.EVT_LEAVE_WINDOW, self.__onMouseLeave)
            t.Bind(wx.EVT_CHAR,         self.__onChar)

    
    def deregister(self):
        """This method de-registers this :class:`Profile` instance from
        receiving mouse/keybouard events. This method is called by the
        :class:`ProfileManager`.
        
        Subclasses may override this method to performa any initialisation,
        but must make sure to call this implementation.
        """
        for t in self.getEventTargets():
            t.Unbind(wx.EVT_LEFT_DOWN)
            t.Unbind(wx.EVT_MIDDLE_DOWN)
            t.Unbind(wx.EVT_RIGHT_DOWN)
            t.Unbind(wx.EVT_LEFT_UP) 
            t.Unbind(wx.EVT_MIDDLE_UP)
            t.Unbind(wx.EVT_RIGHT_UP) 
            t.Unbind(wx.EVT_MOTION)
            t.Unbind(wx.EVT_MOUSEWHEEL)
            t.Unbind(wx.EVT_ENTER_WINDOW)
            t.Unbind(wx.EVT_LEAVE_WINDOW)
            t.Unbind(wx.EVT_CHAR)

    
    def __getTempMode(self, ev):
        """Checks the temporary mode map to see if a temporary mode should
        be applied. Returns the mode identifier, or ``None`` if no temporary
        mode is applicable.
        """

        mode  = self.mode
        alt   = ev.AltDown()        
        ctrl  = ev.ControlDown()
        shift = ev.ShiftDown()

        # Figure out the dictionary key to use,
        # based on the modifier keys that are down
        keys  = {
            (False, False, False) :  None,
            (False, False, True)  :  wx.WXK_SHIFT,
            (False, True,  False) :  wx.WXK_CONTROL,
            (False, True,  True)  : (wx.WXK_CONTROL, wx.WXK_SHIFT), 
            (True,  False, False) :  wx.WXK_ALT,
            (True,  False, True)  : (wx.WXK_ALT, wx.WXK_SHIFT),
            (True,  True,  False) : (wx.WXK_ALT, wx.WXK_CONTROL),
            (True,  True,  True)  : (wx.WXK_ALT, wx.WXK_CONTROL, wx.WXK_SHIFT)
        }

        return self.__tempModeMap.get((mode, keys[alt, ctrl, shift]), None)

    
    def __getMouseLocation(self, ev):
        """Returns two tuples; the first contains the x/y coordinates of the
        given :class:`wx.MouseEvent`, and the second contains the
        corresponding x/y/z display space coordinates.
        """

        mx, my    = ev.GetPositionTuple()
        canvas    = ev.GetEventObject()
        w, h      = canvas.GetClientSize()
        my        = h - my

        canvasPos = canvas.canvasToWorld(mx, my)
        
        return (mx, my), canvasPos
                                

    def __getMouseButton(self, ev):
        """Returns a string describing the mouse button associated with the
        given :class:`wx.MouseEvent`.
        """
        
        btn = ev.GetButton()
        if   btn == wx.MOUSE_BTN_LEFT:   return 'Left'
        elif btn == wx.MOUSE_BTN_RIGHT:  return 'Right'
        elif btn == wx.MOUSE_BTN_MIDDLE: return 'Middle'
        elif ev.LeftIsDown():            return 'Left'  
        elif ev.RightIsDown():           return 'Right' 
        elif ev.MiddleIsDown():          return 'Middle'
        else:                            return  None


    def __getHandler(self, ev, evType, mode=None):
        """Returns a reference to a method of this ``Profile`` instance
        (defined on the sub-class) which can handle the given
        :class:`wx.MouseEvent` or :class:`wx.KeyEvent` (the ``ev`` argument).

        The ``mode`` and ``evType`` arguments may be used to force the lookup
        of a handler for the specified mode (see the :attr:`mode` property)
        or event type.

        If a handler is not found, the :attr:`__altHandlerMap` map is checked
        to see if an alternate handler for the mode/event type has been
        specified.
        """

        tempMode = self.__getTempMode(ev)

        if mode is None:
            if tempMode is None: mode = self.mode
            else:                mode = tempMode

        # Search for a method which can
        # handle the specified mode/evtype
        if mode is not None:
            handlerName = '_{}Mode{}'.format(mode, evType)
        else:
            handlerName = '_{}{}'.format(evType[0].lower(),
                                         evType[1:])

        handler = getattr(self, handlerName, None)

        if handler is not None:
            log.debug('Handler found for mode {}, event {}'.format(mode,
                                                                   evType))
            return handler
        
        # No handler found - search 
        # the alternate handler map
        alt = self.__altHandlerMap.get((mode, evType), None)

        # An alternate handler has
        # been specified - look it up
        if alt is not None:
            altMode, altEvType = alt
            return self.__getHandler(ev, altEvType, altMode)

        return None

        
    def __onMouseWheel(self, ev):
        """Called when the mouse wheel is moved.

        Delegates to a mode specific handler if one is present.
        """

        handler = self.__getHandler(ev, 'MouseWheel')
        if handler is None:
            return

        mouseLoc, canvasLoc = self.__getMouseLocation(ev)
        canvas              = ev.GetEventObject()
        wheel               = ev.GetWheelRotation()

        log.debug('Mouse wheel event ({}) on canvas {}'.format(
            wheel, canvas.name))

        handler(ev, canvas, wheel, mouseLoc, canvasLoc)


    def __onMouseEnter(self, ev):
        """Called when the mouse enters a canvas target.

        Delegates to a mode specific handler if one is present.
        """

        handler = self.__getHandler(ev, 'MouseEnter')
        if handler is None:
            return

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        log.debug('Mouse enter event on canvas {}'.format(canvas.name))

        handler(ev, canvas, mouseLoc, canvasLoc)

        
    def __onMouseLeave(self, ev):
        """Called when the mouse leaves a canvas target.

        Delegates to a mode specific handler if one is present.
        """ 

        handler = self.__getHandler(ev, 'MouseLeave')
        if handler is None:
            return

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        log.debug('Mouse leave event on canvas {}'.format(canvas.name))

        handler(ev, canvas, mouseLoc, canvasLoc)        

        
    def __onMouseDown(self, ev):
        """Called when any mouse button is pushed.

        Delegates to a mode specific handler if one is present.
        """
        
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)
        canvas              = ev.GetEventObject()

        self.__mouseDownPos  = mouseLoc
        self.__canvasDownPos = canvasLoc

        if self.__lastMousePos  is None: self.__lastMousePos  = mouseLoc
        if self.__lastCanvasPos is None: self.__lastCanvasPos = canvasLoc

        handler = self.__getHandler(
            ev, '{}MouseDown'.format(self.__getMouseButton(ev)))
        if handler is None:
            return

        log.debug('Mouse down event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(ev, canvas, mouseLoc, canvasLoc)

        self.__lastMousePos  = mouseLoc
        self.__lastCanvasPos = canvasLoc        

    
    def __onMouseUp(self, ev):
        """Called when any mouse button is released.

        Delegates to a mode specific handler if one is present.
        """
        
        handler = self.__getHandler(
            ev, '{}MouseUp'.format(self.__getMouseButton(ev)))

        if handler is None:
            self.__mouseDownPos  = None
            self.__canvasDownPos = None
            return

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        log.debug('Mouse up event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(ev, canvas, mouseLoc, canvasLoc)
        self.__mouseDownPos  = None
        self.__canvasDownPos = None


    def __onMouseMove(self, ev):
        """Called on mouse motion. If a mouse button is down, delegates to
        :meth:`__onMouseDrag`.

        Otherwise, delegates to a mode specific handler if one is present.
        """

        if ev.Dragging():
            self.__onMouseDrag(ev)
            return

        handler = self.__getHandler(ev, 'MouseMove')

        if handler is None:
            return
        
        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        log.debug('Mouse move event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(ev, canvas, mouseLoc, canvasLoc)

        self.__lastMousePos  = mouseLoc
        self.__lastCanvasPos = canvasLoc        

    
    def __onMouseDrag(self, ev):
        """Called on mouse drags.
        
        Delegates to a mode specific handler if one is present.
        """
        ev.Skip()

        canvas              = ev.GetEventObject()
        mouseLoc, canvasLoc = self.__getMouseLocation(ev)

        handler = self.__getHandler(
            ev, '{}MouseDrag'.format(self.__getMouseButton(ev)))
        if handler is None:
            return 

        log.debug('Mouse drag event ({}, {}) on canvas {}'.format(
            mouseLoc, canvasLoc, canvas.name))

        handler(ev, canvas, mouseLoc, canvasLoc)

        self.__lastMousePos  = mouseLoc
        self.__lastCanvasPos = canvasLoc

        
    def __onChar(self, ev):
        """Called on keyboard key presses.

        Delegates to a mode specific handler if one is present.
        """

        handler = self.__getHandler(ev, 'Char')
        if handler is None:
            return 

        canvas = ev.GetEventObject()
        key    = ev.GetKeyCode()

        log.debug('Keyboard event ({}) on canvas {}'.format(key, canvas.name))

        handler(ev, canvas, key)
