#!/usr/bin/env python
#
# action.py - The Action and ToggleAction classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Action` and :class:`ToggleAction` classes.
See the :mod:`.actions` package documentation for more details.
"""

import logging

import props


log = logging.getLogger(__name__)


class ActionDisabledError(Exception):
    """Exception raised when an attempt is made to call a disabled
    :class:`Action`.
    """
    pass


class Action(props.HasProperties):
    """Represents an action of some sort. """
    
    
    enabled = props.Boolean(default=True)
    """Controls whether the action is currently enabled or disabled.
    When this property is ``False`` calls to the action will
    result in a :exc:`ActionDisabledError`.
    """

    
    def __init__(self, func, instance=None):
        """Create an ``Action``.
        
        :arg func:     The action function.

        :arg instance: Object associated with the function, if this ``Action``
                       is encapsulating an instance method.
        """
        self.__instance     = instance
        self.__func         = func
        self.__name         = func.__name__ 
        self.__boundWidgets = []

        self.addListener('enabled',
                         'Action_{}_internal'.format(id(self)),
                         self.__enabledChanged)

        
    def __str__(self):
        """Returns a string representation of this ``Action``. """
        return '{}({})'.format(type(self).__name__, self.__name)

    
    def __repr__(self):
        """Returns a string representation of this ``Action``. """
        return self.__str__()

    
    def __call__(self, *args, **kwargs):
        """Calls this action. An :exc:`ActionDisabledError` will be raised
        if :attr:`enabled` is ``False``.
        """

        if not self.enabled:
            raise ActionDisabledError('Action {} is disabled'.format(
                self.__name))

        log.debug('Action {}.{} called'.format(
            type(self.__instance).__name__,
            self.__name))

        if self.__instance is not None:
            args = [self.__instance] + list(args)
            
        return self.__func(*args, **kwargs)

    
    def destroy(self):
        """Must be called when this ``Action`` is no longer needed. """
        self.unbindAllWidgets()
        self.__func     = None
        self.__instance = None

        
    def bindToWidget(self, parent, evType, widget):
        """Binds this action to the given :mod:`wx` widget.

        :arg parent: The :mod:`wx` object on which the event should be bound.
        :arg evType: The :mod:`wx` event type.
        :arg widget: The :mod:`wx` widget.
        """

        def wrappedAction(ev):
            self()
            
        parent.Bind(evType, wrappedAction, widget)
        widget.Enable(self.enabled)
        self.__boundWidgets.append((parent, evType, widget))


    def unbindAllWidgets(self):
        """Unbinds all widgets which have been bound via :meth:`bindToWidget`.
        """

        import wx
        
        for parent, evType, widget in self.__boundWidgets:

            # Only attempt to unbind if the parent
            # and widget have not been destroyed
            try:
                parent.Unbind(evType, source=widget)
            except wx.PyDeadObjectError:
                pass
            
        self.__boundWidgets = []

        
    def getBoundWidgets(self):
        """Returns a list containing all widgets which have been bound to
        this ``Action``.
        """
        return [w for _, _, w in self.__boundWidgets]


    def __enabledChanged(self, *args):
        """Internal method which is called when the :attr:`enabled` property
        changes. Enables/disables any bound widgets.
        """

        for _, _, widget in self.__boundWidgets:
            widget.Enable(self.enabled)

    
class ToggleAction(Action):
    """A ``ToggleAction`` an ``Action`` which is intended to encapsulate
    actions that toggle some sort of state. For example, a ``ToggleAction``
    could be used to encapsulate an action which opens and/or closes a dialog
    window.
    """


    toggled = props.Boolean(default=False)
    """Boolean which tracks the current state of the ``ToggleAction``. """


    def __init__(self, *args, **kwargs):
        """Create a ``ToggleAction``. All arguments are passed to
        :meth:`Action.__init__`.
        """
        
        Action.__init__(self, *args, **kwargs)
        
        self.addListener('toggled',
                         'ToggleAction_{}_internal'.format(id(self)),
                         self.__toggledChanged)

        
    def __call__(self, *args, **kwargs):
        """Call this ``ToggleAction`. The value of the :attr:`toggled` property
        is flipped.
        """

        # Copy the toggled value before running
        # the action, in case it gets inadvertently
        # changed
        toggled      = self.toggled
        result       = Action.__call__(self, *args, **kwargs)
        self.toggled = not toggled
            
        return result


    def bindToWidget(self, parent, evType, widget):
        """Bind this ``ToggleAction`` to a widget. If the widget is a
        ``wx.MenuItem``, its ``Check`` is called whenever the :attr:`toggled`
        state changes.
        """

        import wx
        import pwidgets.bitmaptoggle as bmptoggle
        
        Action.bindToWidget(self, parent, evType, widget)

        if isinstance(widget, wx.MenuItem):
            widget.Check(self.toggled)
        elif isinstance(widget, (wx.CheckBox,
                                 wx.ToggleButton,
                                 bmptoggle.BitmapToggleButton)):
            widget.SetValue(self.toggled)

        
    def __toggledChanged(self, *a):
        """Internal method called when :attr:`toggled` changes. Updates the
        state of any bound widgets.
        """
        
        import wx
        import pwidgets.bitmaptoggle as bmptoggle
        
        for widget in self.getBoundWidgets():

            if isinstance(widget, wx.MenuItem):
                widget.Check(self.toggled)
                
            elif isinstance(widget, (wx.CheckBox,
                                     wx.ToggleButton,
                                     bmptoggle.BitmapToggleButton)):
                widget.SetValue(self.toggled)
