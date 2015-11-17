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
button. The :class:`ActionProvider` class represents some entity which can
perform one or more actions.  As the :class:`.FSLEyesPanel` class derives from
:class:`ActionProvider` pretty much everything in FSLEyes is an
:classf:`ActionProvider`. 


The :func:`action` and :func:`toggleAction` functions are intended to be used
as decorators upon the methods of a class which derives from
:class:`ActionProvider`. For example::

    >>> import fsl.fsleyes.actions as actions
    >>> class Thing(actions.ActionProvider):
            @actions.action
            def doFirstThing(self):
                print 'First thing done'
            @actions.action
            def doSecondThing(self):
                print 'Second thing done'
            @actions.toggleAction
            def toggleOtherThing(self):
                print 'Other thing toggled'


In this example, when an instance of ``Thing`` is defined, each of the methods
that are defined as actions will be available through the methods defined in
the :class:`ActionProvder`. For example::

    >>> t = Thing()
    >>> print t.getActions()
    [('doFirstThing', Action(doFirstThing)),
     ('doSecondThing', Action(doSecondThing)),
     ('toggleOtherThing', ToggleAction(toggleOtherThing))]


You can enable/disable actions through the :meth:`ActionProvider.enableAction`
and :meth:`ActionProvider.disableAction` methods::

    >>> t.disableAction('doFirstThing')
    >>> t.doFirstThing()
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/.../fsl/fsleyes/actions/__init__.py", line 139, in __call__
        self.__name))
    fsl.fsleyes.actions.ActionDisabledError: Action doFirstThing is disabled


It is useful to know that each method on the ``t`` instance has actually been
replaced with an :class:`Action` instance, which encapsulates the method. Using
this knowledge, you can access the ``Action`` instances directly::

    >>> t.doFirstThing.enabled = True
    >>> t.doFirstThing()
    First thing done


The :meth:`Action.bindToWidget` method allows a widget to be bound to an
:class:`Action`. For example::

    # We're assuming here that a wx.App, and
    # a parent window, has been created
    >>> button = wx.Button(parent, label='Do the first thing!')
    >>> t.doSecondThing.bindToWidget(parent, button, wx.EVT_BUTTON)


All bound widgets of an ``Action`` can be accessed through the
:meth:`Action.getBoundWidgets` method, and can be unbound via the
:meth:`Action.unbindAllWidgets` method.


Some 'global' actions are also provided in this package:

 .. autosummary::

    ~fsl.fsleyes.actions.copyoverlay
    ~fsl.fsleyes.actions.loadcolourmap
    ~fsl.fsleyes.actions.openfile
    ~fsl.fsleyes.actions.openstandard
    ~fsl.fsleyes.actions.saveoverlay

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
    """Represents an action of some sort. 
    """
    
    
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

        result = Action.__call__(self, *args, **kwargs)
            
        self.toggled = not self.toggled
            
        return result


    def bindToWidget(self, parent, evType, widget):
        """Bind this ``ToggleAction`` to a widget. If the widget is a
        ``wx.MenuItem``, its ``Check`` is called whenever the :attr:`toggled`
        state changes.
        """

        import wx
        
        Action.bindToWidget(self, parent, evType, widget)

        if isinstance(widget, wx.MenuItem):
            widget.Check(self.toggled)

        
    def __toggledChanged(self, *a):
        """Internal method called when :attr:`toggled` changes. Updates the
        state of any bound widgets.
        """
        
        import wx
        
        for widget in self.getBoundWidgets():

            if isinstance(widget, wx.MenuItem):
                widget.Check(self.toggled)


class ActionProvider(object):
    """The ``ActionProvider`` class is intended to be used as a base class for
    classes which contain actions. The :func:`action` and :func:`toggleAction`
    functions can be used as decorators on class methods, to denote them as
    actions.
    """

    def destroy(self):
        """Must be called when this ``ActionProvider`` is no longer needed.
        Calls the :meth:`Action.destroy` method of all ``Action`` instances.
        """
        for name, action in self.getActions():
            action.destroy()


    def getAction(self, name):
        """Return the :class:`Action` instance with the specified name. """
        return getattr(self, name)


    def enableAction(self, name, enable=True):
        """Enable/disable the named :class:`Action`. """
        self.getAction(name).enabled = enable

        
    def disableAction(self, name):
        """Disable the named :class:`Action`. """
        self.enableAction(name, False)

    
    def getActions(self):
        """Return a list containing the ``(name, Action)`` of all
        :class:`Action` instances in this ``ActionProvider``.
        
        Sub-classes may wish to override this method to enforce a specific
        ordering of their actions.
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
    """Exception raised when an attempt is made to call a disabled
    :class:`Action`.
    """
    pass


class ActionFactory(object):
    """The ``ActionFactory`` is used by the :func:`action` and
    :func:`toggleAction` decorators. Its job is to create :class:`Action`
    instances for :class:`ActionProvider` instances. This class has no use
    outside of this module. 

    
    *Boring technical details*

    
    Consider the following class::

        class MyThing(ActionProvider):

            @action
            def myAction(self):
                # do things here

                
    The ``MyClass.myAction`` method has been marked as an action, using the
    :func:`action` decorator. However, the :func:`action` decorator cannot
    create an :class:`Action` instance at the point of class definition,
    because this would lead to a single ``Action`` instance being shared by
    multiple ``MyThing`` instances.  We need to be able to create an ``Action``
    instance for every ``MyThing`` instance, will still allowing the action
    decorator to be used on class methods.


    So when the :func:`action` or :func:`toggleAction` is used in a class
    definition, an ``ActionFactory`` is created, and used as the decorator
    of the unbound class method.

    
    Later on, when the ``ActionFactory`` detects that it being is accessed
    through an instance of the class (a ``MyThing`` instance in the example
    above), it creates an :class:`Action` instance, and then replaces itself
    with this ``Action`` instance - the ``Action`` instance becomes the
    decorator of the bound method. This is possible because the
    ``ActionFactory`` is a descriptor - it uses the :meth:`__get__` method
    so it can differentiate between class-level and instance-level accesses
    of the decorated method.
    """

    
    def __init__(self, func, actionType):
        """Create an ``ActionFactory``.

        :arg func:       The encapsulated method.
        :arg actionType: The action type (e.g. :class:`Action` or
                         :class:`ToggleAction`).
        """
        self.__func        = func
        self.__actionType  = actionType

    
    def __get__(self, instance, cls):
        """When this ``ActionFactory`` is accessed through an instance,
        a :class:`Action` instance is created. This ``ActionFactory`` is
        then replaced by the ``Action`` instance.

        If this ``ActionFactory`` is accessed through a class, the
        encapsulated function is returned.
        """

        # Class-level access
        if instance is None:
            return self.__func
        
        else:
            
            # Create an Action for the instance,
            # and replace this ActionFactory
            # with the Action on the instance.
            action = self.__actionType(self.__func, instance)
            setattr(instance, self.__func.__name__, action)
            return action
