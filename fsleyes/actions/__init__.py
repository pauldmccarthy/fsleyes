#!/usr/bin/env python
#
# __init__.py - Superclasses for objects which perform 'actions'.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package provides a collection of actions, classes - the
:class:`~fsleyes.actions.base.Action` class and the :class:`.ActionProvider`
class, and the :func:`action` and :func:`toggleAction` decorators.


The :class:`.Action` class represents some sort of action which may be
performed, enabled and disabled, and may be bound to a GUI menu item or
button. The :class:`ActionProvider` class represents some entity which can
perform one or more actions.  As the :class:`.FSLeyesPanel` class derives from
:class:`ActionProvider` pretty much everything in FSLeyes is an
:class:`ActionProvider`.


Many of the modules in this package also contain standalone functions for doing
various things, such as the :func:`.screenshot.screenshot` function, and the
:func:`.loadoverlay.loadImage` function.


The :func:`action` and :func:`toggleAction` functions are intended to be used
as decorators upon the methods of a class which derives from
:class:`ActionProvider`. For example::

    >>> import fsleyes.actions as actions
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
      File "/.../fsleyes/actions/__init__.py", line 139, in __call__
        self.__name))
    fsleyes.actions.ActionDisabledError: Action doFirstThing is disabled


It is useful to know that each method on the ``t`` instance has actually been
replaced with an :class:`.Action` instance, which encapsulates the method.
Using this knowledge, you can access the ``Action`` instances directly::

    >>> t.doFirstThing.enabled = True
    >>> t.doFirstThing()
    First thing done


The :meth:`.Action.bindToWidget` method allows a widget to be bound to an
:class:`.Action`. For example::

    # We're assuming here that a wx.App, and
    # a parent window, has been created
    >>> button = wx.Button(parent, label='Do the first thing!')
    >>> t.doSecondThing.bindToWidget(parent, button, wx.EVT_BUTTON)


All bound widgets of an ``Action`` can be accessed through the
:meth:`.Action.getBoundWidgets` method, and can be unbound via the
:meth:`.Action.unbindAllWidgets` method.


This module also provides two classes which allow a widget to be automatically
created for, and bound to an ``Action`` or ``ToggleAction`` (through the
:mod:`props.build` package):

 .. autosummary::
    :nosignatures:

    ActionButton
    ToggleActionButton
"""


import logging
import types
import functools
from   collections import defaultdict

import fsleyes_props   as props
import fsleyes.strings as strings

from . import base
from . import togglecontrolpanel


Action                   = base.Action
ActionDisabledError      = base.ActionDisabledError
ToggleAction             = base.ToggleAction
ToggleControlPanelAction = togglecontrolpanel.ToggleControlPanelAction


log = logging.getLogger(__name__)


def action(*args, **kwargs):
    """A decorator which identifies a class method as an action. """
    return ActionFactory(Action, *args, **kwargs)


def toggleAction(*args, **kwargs):
    """A decorator which identifies a class method as a toggle action. """
    return ActionFactory(ToggleAction, *args, **kwargs)


def toggleControlAction(*args, **kwargs):
    """A decorator which identifies a class method as a
    :class:`.ToggleControlPanelAction`.
    """
    return ActionFactory(ToggleControlPanelAction, *args, **kwargs)


class ActionProvider:
    """The ``ActionProvider`` class is intended to be used as a base class for
    classes which contain actions. The :func:`action` and :func:`toggleAction`
    functions can be used as decorators on class methods, to denote them as
    actions.
    """

    def __init__(self, overlayList, displayCtx):
        """Create an ``ActionProvider``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        """
        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__actions     = {}


    def addAction(self, action, name=None):
        """Register an :class:`.Action` object with this ``ActionProvider``.

        Actions defined via the :func:`action` decorators are automatically
        registered - this method can be used to register an ``Action`` which
        was created separately.

        All registered ``Action`` instances of an ``ActionProvider`` are made
        available as attributes of the provider, with the
        :meth:`.Action.actionName` the attribute name.

        Once an ``Action`` is registered with an ``ActionProvider``, the
        provider effectively owns the ``Action`` and is responsible for its
        lifecycle. This means that when the ``ActionProvider`` is destroyed,
        it will call the :meth:`.Action.destroy` method of all registered
        ``Action`` instances.

        :arg action: An :class:`.Action` object
        :arg name:   The action name - used as the attribute name on this
                     ``ActionProvider``. Defaults to :meth:`.Action.actionName`
        """
        if name is None:
            name = action.actionName

        if name in self.__actions:
            raise ValueError(f'An action with name {name} is already '
                             f'registered with this {type(self).__name__}')


        log.debug('%s: registering action %s', type(self).__name__, name)

        self.__actions[name] = action
        action.provider      = self

        setattr(self, name, action)


    @property
    def overlayList(self):
        """Return a reference to the :class:`.OverlayList`. """
        return self.__overlayList


    @property
    def displayCtx(self):
        """Return a reference to the :class:`.DisplayContext`. """
        return self.__displayCtx


    def destroy(self):
        """Must be called when this ``ActionProvider`` is no longer needed.
        Calls the :meth:`Action.destroy` method of all ``Action`` instances
        owned by this ``ActionProvider``.
        """

        for name, act in self.__actions.items():
            if not act.destroyed:
                act.destroy()

        self.__overlayList = None
        self.__displayCtx  = None
        self.__actions     = None


    def getAction(self, name):
        """Return the :class:`Action` instance with the specified name. """

        # getattr in case this is a decorated ActionFactory
        # instance that hasn't yet been accesseed.
        getattr(self, name, None)
        return self.__actions[name]


    def hasAction(self, name):
        """Return ``True`` if this ``ActionProvider`` has an action with the
        given name, ``False`` otherwise
        """
        getattr(self, name, None)
        return name in self.__actions


    def enableAction(self, name, enable=True):
        """Enable/disable the named :class:`Action`. """
        getattr(self, name, None)
        self[name].enabled = enable


    def disableAction(self, name):
        """Disable the named :class:`Action`. """
        getattr(self, name, None)
        self.enableAction(name, False)


    def getActions(self):
        """Return a list containing the ``(name, Action)`` of all
        :class:`Action` instances in this ``ActionProvider``.

        Sub-classes may wish to override this method to enforce a specific
        ordering of their actions.

        .. note:: The list returned by this method may contain entries equal
                      to ``(None, None)``. This is used as a hint for the
                      :class:`.FSLeyesFrame`, which creates menu items, to
                      indicate that a separator should be inserted.
        """
        return list(self.__actions.items())


class ActionFactory:
    """The ``ActionFactory`` is used by the :func:`action`,
    :func:`toggleAction`, and :func:`toggleControlPanelAction` decorators.
    Its job is to create :class:`Action` instances for :class:`ActionProvider`
    instances.


    .. warning:: This class contains difficult-to-understand code. Read up
                 on decorators and descriptors before proceeding.


    .. note:: This class has no use outside of this module, except for use
              with custom :class:`.Action`/:class:`.ToggleAction` sub-classes
              and corresponding decorators (along the lines of :func:`.action`
              and :func:`.toggleAction`). A custom decorator simply needs
              to return ``ActionFactory(CustomActionClass, *args, **kwargs)``,
              where the ``*args`` and ``**kwargs`` are the arguments passed to
              the :class:`Action` sub-class.

              See the :func:`toggleControlAction` decorator for an example.


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
    instance for every ``MyThing`` instance, whilst still allowing the action
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


    The ``ActionFactory`` supports class-method decorators both with and
    without arguments. While neither the :class:`.Action`, nor the
    :class:`.ToggleAction` classes accept any optional arguments, this may be
    useful for custom sub-classes, i.e.::

        class MyThing(ActionProvider):

            @action
            def myAction(self):
                # do things here

            @customAction()
            def myAction2(self):
                # do things here

            @otherCustomAction(arg1=8)
            def myAction3(self):
                # do things here


    .. todo:: Merge/replace this class with the :class:`.memoize.Instanceify`
              decorator.
    """


    def __init__(self, actionType, *args, **kwargs):
        """Create an ``ActionFactory``.

        :arg actionType: The action type (e.g. :class:`Action` or
                         :class:`ToggleAction`).

        The remaining arguments may comprise a single callable object, (an
        ``@action`` style decorator was used) or a collection of arguments
        passed to the decorator (an ``@action(...)`` style decorator was
        used).
        """

        self.__actionType  = actionType
        self.__args        = args
        self.__kwargs      = kwargs
        self.__func        = None

        # A no-brackets style
        # decorator was used
        if len(kwargs) == 0 and \
           len(args)   == 1 and \
           isinstance(args[0], (types.FunctionType,
                                types.MethodType)):

            self.__func = args[0]
            self.__args = self.__args[1:]


    def __call__(self, func=None):
        """If this ``ActionFactory`` was instantiated through a brackets-style
        decorator (e.g. ``@action(arg1=1, arg2=2)``), this method is called
        immediately after :meth:`__init__`, with a reference to the decorated
        function. Otherwise, (an ``@action`` style decorator was used), this
        method should never be called.
        """

        if self.__func is not None:
            log.warning('ActionFactory.__call__ was called, but function is '
                        'alreday set (%s)! I\'m really confused.',
                        self.__func.__name__)

        self.__func = func
        return self


    def __get__(self, instance, cls):
        """When this ``ActionFactory`` is accessed through an instance,
        an :class:`Action` instance is created. This ``ActionFactory`` is
        then replaced by the ``Action`` instance.

        If this ``ActionFactory`` is accessed through a class, the
        encapsulated function is returned.
        """

        # Class-level access
        if instance is None:
            return self.__func

        else:
            # first argument will be the
            # instance (the "self" argument)
            func = functools.partial(self.__func, instance)
            func = functools.update_wrapper(func, self.__func)
            args = [instance.overlayList, instance.displayCtx]

            # ToggleControlPanelAction for a ViewPanel instance
            if self.__actionType is ToggleControlPanelAction:
                args.append(instance)

            # Create an Action for the ActionProvider
            # instance and register it with the provider
            log.debug('Creating @action %s.%s',
                      type(instance).__name__, func.__name__)
            action = self.__actionType(
                *args,
                *self.__args,
                func=func,
                name=func.__name__,
                **self.__kwargs)

            action = functools.update_wrapper(action, self.__func)
            instance.addAction(action)

            return action


class ActionButton(props.Button):
    """Extends the :class:`props.Button` class to encapsulate an
    :class:`Action` instance.

    Only actions which are defined using the :func:`action` or
    :func:`toggleAction` decorator are supported.
    """


    def __init__(self,
                 actionName,
                 classType=None,
                 actionArgs=None,
                 actionKwargs=None,
                 **kwargs):
        """Create an ``ActionButton``.

        :arg actionName: Name of the action

        :arg classType:  The type which defines the action.

        :arg kwargs:     Passed to the :class:`props.Button` constructor.
        """

        if actionArgs   is None: actionArgs   = []
        if actionKwargs is None: actionKwargs = {}

        self.__name         = actionName
        self.__actionArgs   = actionArgs
        self.__actionKwargs = actionKwargs

        text = kwargs.pop('text', None)

        if text is None:
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


    def __setup(self, instance, parent, widget):
        """Called when the button is created. Binds the button widget to the
        ``Action`` instance.
        """
        import wx
        instance.getAction(self.__name).bindToWidget(
            parent, wx.EVT_BUTTON, widget)


    def __onButton(self, instance, widget):
        """Called when the button is pushed. Runs the action."""
        instance.getAction(self.__name)(*self.__actionArgs,
                                        **self.__actionKwargs)


class ToggleActionButton(props.Toggle):
    """Extends the :class:`props.Toggle` class to encapsulate a
    :class:`ToggleAction` instance.

    Only actions which are defined using the :func:`action` or
    :func:`toggleAction` decorator are supported.
    """


    def __init__(self,
                 actionName,
                 icon,
                 actionArgs=None,
                 actionKwargs=None,
                 **kwargs):
        """Create a ``ToggleActionButton``.

        :arg actionName:   Name of the action

        :arg icon:         One or two icon file names to use on the button.

        :arg actionArgs:   Positional arguments to pass to the
                           :class:`.ToggleAction` when it is invoked.

        :arg actionKwargs: Keyword arguments to pass to the
                           :class:`.ToggleAction` when it is invoked.

        :arg kwargs:       Passed to the :class:`props.Toggle` constructor.
        """

        if actionArgs   is None: actionArgs   = []
        if actionKwargs is None: actionKwargs = {}

        self.__name         = actionName
        self.__actionArgs   = actionArgs
        self.__actionKwargs = actionKwargs

        props.Toggle.__init__(
            self,
            key=actionName,
            icon=icon,
            setup=self.__setup,
            callback=self.__onToggle,
            **kwargs)


    def __setup(self, instance, parent, widget):
        """Called when the toggle widget is created. Binds the widget to the
        ``ToggleAction`` instance.
        """
        import wx
        import fsleyes_widgets as fw

        if isinstance(widget, wx.CheckBox):
            ev = wx.EVT_BUTTON
        elif isinstance(widget, wx.ToggleButton):
            ev = wx.EVT_TOGGLEBUTTON
        elif isinstance(widget, fw.BitmapToggleButton):
            ev = fw.EVT_BITMAP_TOGGLE

        else:
            raise RuntimeError(f'Unknown widget {type(widget).__name__}')

        instance.getAction(self.__name).bindToWidget(parent, ev, widget)


    def __onToggle(self, instance, widget):
        """Called when the widget is toggled. Runs the action."""
        instance.getAction(self.__name)(*self.__actionArgs,
                                        **self.__actionKwargs)
