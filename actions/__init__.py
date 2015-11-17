#!/usr/bin/env python
#
# __init__.py - Superclasses for objects which perform 'actions'.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package provides a collection of actions, two package-level
classes - the :class:`Action` class and the :class:`ActionProvider` class,
and the :func:`action` and :func:`toggleAction` decorators.


The :class:`Action` class represents some sort of action which may be
performed, enabled and disabled, and may be bound to a GUI menu item or
button.


Some 'global' actions are also provided in this package:

 .. autosummary::

    ~fsl.fsleyes.actions.copyoverlay
    ~fsl.fsleyes.actions.loadcolourmap
    ~fsl.fsleyes.actions.openfile
    ~fsl.fsleyes.actions.openstandard
    ~fsl.fsleyes.actions.saveoverlay


The :class:`ActionProvider` class represents some entity which can perform
one or more actions.  As the :class:`.FSLEyesPanel` class derives from
:class:`ActionProvider` pretty much everything in FSLEyes is an
:class:`ActionProvider`.
"""


import logging
import inspect

import props

import fsl.data.strings as strings


log = logging.getLogger(__name__)


def action(func):
    """A decorator which identifies a class method as an action. """
    return ActionFactory(func, Action)


def toggleAction(func):
    """A decorator which identifies a class method as a toggle action. """
    return ActionFactory(func, ToggleAction) 


class Action(props.HasProperties):
    """
    """
    
    
    enabled = props.Boolean(default=True)
    """Controls whether the action is currently enabled or disabled.
    When this property is ``False`` calls to the action will
    result in a :exc:`ActionDisabledError`.
    """

    
    def __init__(self, func, instance=None):
        """Create an ``Action``.
        
        :arg func: The action function.
        """
        self.__instance     = instance
        self.__func         = func
        self.__name         = func.__name__ 
        self.__boundWidgets = []

        self.addListener('enabled',
                         'Action_{}_internal'.format(id(self)),
                         self.__enabledChanged)


    
    def __call__(self, *args, **kwargs):

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
        """
        """
        return [w for _, _, w in self.__boundWidgets]


    def __enabledChanged(self, *args):
        """Internal method which is called when the :attr:`enabled` property
        changes. Enables/disables any bound widgets.
        """

        for _, _, widget in self.__boundWidgets:
            widget.Enable(self.enabled)

    
class ToggleAction(Action):


    toggled = props.Boolean(default=False)


    def __init__(self, func, instance=None):
        
        Action.__init__(self, func, instance)
        
        self.addListener('toggled',
                         'ToggleAction_{}_internal'.format(id(self)),
                         self.__toggledChanged)

        
    def __call__(self, *args, **kwargs):
        """
        """

        result = Action.__call__(self, *args, **kwargs)
            
        self.toggled = not self.toggled
            
        return result


    def bindToWidget(self, parent, evType, widget):

        import wx
        
        Action.bindToWidget(self, parent, evType, widget)

        if isinstance(widget, wx.MenuItem):
            widget.Check(self.toggled)

        
    def __toggledChanged(self, *a):
        
        import wx
        
        for widget in self.getBoundWidgets():

            if isinstance(widget, wx.MenuItem):
                widget.Check(self.toggled)


class ActionProvider(object):


    def destroy(self):
        for name, action in self.getActions():
            action.destroy()


    def getAction(self, name):
        return getattr(self, name)


    def enableAction(self, name, enable=True):
        self.getAction(name).enable = enable

        
    def disableAction(self, name):
        self.enableAction(name, False)

    
    def getActions(self):
        """
        Sub-classes may override this method to enforce a specific ordering
        of their actions.
        """
    
        acts = []
        
        for name, attr in inspect.getmembers(self):
            if isinstance(attr, Action):
                acts.append((name, attr))
                
        return acts


class ActionButton(props.Button):
    """Extends the :class:`props.Button` class to encapsulate an
    :class:`Action` instance.
    """
    
    def __init__(self, actionName, classType=None, **kwargs):
        """Create an ``ActionButton``.

        :arg actionName: Name of the action

        :arg classType:  The type which defines the action.

        :arg kwargs:     Passed to the :class:`props.Button` constructor.
        """

        self.__name = actionName

        if classType is not None:
            text = strings.actions.get((classType, actionName), actionName)
        else:
            text = actionName

        props.Button.__init__(
            self,
            actionName,
            text=text,
            callback=self.__onButton,
            setup=self.__setup,
            **kwargs)


    def __setup(self, instance, parent, widget, *a):
        """Called when the button is created. Binds the button widget to the
        ``Action`` instance.
        """
        import wx
        instance.getAction(self.__name).bindToWidget(
            parent, wx.EVT_BUTTON, widget)

        
    def __onButton(self, instance, *a):
        """Called when the button is pushed. Runs the action."""
        instance.getAction(self.__name)()


class ActionDisabledError(Exception):
    pass


class ActionFactory(object):

    
    def __init__(self, func, actionType):
        self.__func       = func
        self.__actionType = actionType

    
    def __get__(self, instance, cls):

        # Class-level access
        if instance is None:
            return self.__func
        
        else:
            
            # Create an Action for the instance,
            # and replace replace this ActionFactory
            # with the Action on the instance.
            action = self.__actionType(self.__func, instance)
            setattr(instance, self.__func.__name__, action)
            
            return action
