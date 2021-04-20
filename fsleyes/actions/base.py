#!/usr/bin/env python
#
# base.py - The Action and ToggleAction classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Action`, :class:`NeedOverlayAction`, and
:class:`ToggleAction` classes.  See the :mod:`.actions` package documentation
for more details.
"""


import logging

import fsl.data.image  as fslimage
import fsleyes_props   as props
import fsleyes_widgets as fwidgets


log = logging.getLogger(__name__)


class ActionDisabledError(Exception):
    """Exception raised when an attempt is made to call a disabled
    :class:`Action`.
    """


class BoundWidget(object):
    """Container class used by :class:`Action` instances to store references
    to widgets that are currently bound to them.
    """


    def __init__(self, parent, evType, widget):
        import wx
        self.parent = parent
        self.evType = evType
        self.widget = widget

        # Under OSX, if a wx.Menu is destroyed,
        # and then the GetMenu method of a
        # contained wx.MenuItem is called, a
        # segfault will occur. So let's get a
        # reference now.
        if isinstance(widget, wx.MenuItem):
            self.menu = widget.GetMenu()
        else:
            self.menu = None


    def isAlive(self):
        """Returns ``True`` if the widget contained by this ``BoundWidget`` is
        still alive, ``False`` otherwise.
        """

        import wx

        if not fwidgets.isalive(self.parent):
            return False

        if isinstance(self.widget, wx.MenuItem):
            return fwidgets.isalive(self.menu)

        else:
            return fwidgets.isalive(self.widget)


class Action(props.HasProperties):
    """Represents an action of some sort. """


    enabled = props.Boolean(default=True)
    """Controls whether the action is currently enabled or disabled.
    When this property is ``False`` calls to the action will
    result in a :exc:`ActionDisabledError`.
    """


    @staticmethod
    def title():
        """May be overridden by sub-classes. Returns a title to be used
        in menus.
        """
        return None


    @staticmethod
    def supportedViews():
        """May be overridden to declare that this Action should be associated
        with a specific :class:`.ViewPanel`. If overridden, must return a
        list containing all of the supported ``ViewPanel`` types.
        """
        return None


    @staticmethod
    def ignoreTool():
        """Used by the FSLeyes :mod:`.plugins` module for actions which are
        loaded as plugins. Can be used to tell the ``plugins`` module that
        a particular ``Action`` should not be added as an option to the
        FSLeyes Tools menu.

        Note that this method must be implemented on the class that is to
        be ignored - inherited implementations from base classes are not
        considered.
        """
        return False


    def __init__(self,
                 overlayList,
                 displayCtx,
                 func,
                 name=None):
        """Create an ``Action``.

        :arg overlayList: The :class:`.OverlayList`.

        :arg displayCtx:  The :class:`.DisplayContext` associated with this
                          ``Action``; note that this is not necessarily the
                          master :class:`.DisplayContext`.

        :arg func:        The action function.

        :arg name:        Action name. Defaults to ``func.__name__``.

        .. note:: If an ``Action`` encapsulates a method of an
                  :class:`.ActionProvider` instance, it is assumed that the
                  ``name`` is the name of the method on the instance.
        """

        if name is None:
            name = func.__name__

        self.__overlayList  = overlayList
        self.__displayCtx   = displayCtx
        self.__func         = func
        self.__name         = '{}_{}'.format(type(self).__name__, id(self))
        self.__actionName   = name
        self.__destroyed    = False
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


    @property
    def actionName(self):
        """Returns the name of this ``Action``, often the method name of the
        :class:`.ActionProvider` that implements the action. Not to be
        confused with :meth:`name`.
        """
        return self.__actionName


    @property
    def name(self):
        """Not to be confused with :meth:`actionName`.
        Returns a unique name for a specific ``Action`` instance, which
        can be used (e.g.) for registering property listeners.
        """
        return self.__name


    @property
    def overlayList(self):
        """Return a reference to the :class:`.OverlayList`. """
        return self.__overlayList


    @property
    def displayCtx(self):
        """Return a reference to the :class:`.DisplayContext`. """
        return self.__displayCtx


    def __call__(self, *args, **kwargs):
        """Calls this action. An :exc:`ActionDisabledError` will be raised
        if :attr:`enabled` is ``False``.
        """

        if not self.enabled:
            raise ActionDisabledError('Action {} is disabled'.format(
                self.__name))

        log.debug('Action %s called', self.__name)

        return self.__func(*args, **kwargs)


    @property
    def destroyed(self):
        """Returns ``True`` if :meth:`destroy` has been called, ``False``
        otherwise.
        """
        return self.__destroyed


    def destroy(self):
        """Must be called when this ``Action`` is no longer needed. """
        self.unbindAllWidgets()
        self.__destroyed   = True
        self.__overlayList = None
        self.__displayCtx  = None
        self.__func        = None


    def bindToWidget(self, parent, evType, widget, wrapper=None):
        """Binds this action to the given :mod:`wx` widget.

        :arg parent:  The :mod:`wx` object on which the event should be bound.
        :arg evType:  The :mod:`wx` event type.
        :arg widget:  The :mod:`wx` widget.
        :arg wrapper: Optional custom wrapper function used to execute the
                      action.
        """

        if wrapper is None:
            def wrapper(ev):
                self()

        parent.Bind(evType, wrapper, widget)
        widget.Enable(self.enabled)
        self.__boundWidgets.append(BoundWidget(parent, evType, widget))


    def unbindWidget(self, widget):
        """Unbinds the given widget from this ``Action``. """

        # Figure out the index into __boundWidgets,
        # as we need this to pass to __unbindWidget,
        # which does the real work.
        index = -1

        for i, bw in enumerate(self.__boundWidgets):
            if bw.widget == widget:
                index = i
                break

        if index == -1:
            raise ValueError('Widget {} [{}] is not bound'
                             .format(type(widget).__name__, id(widget)))

        self.__unbindWidget(    index)
        self.__boundWidgets.pop(index)


    def __unbindWidget(self, index):
        """Unbinds the widget at the specified index into the
        ``__boundWidgets`` list. Does not remove it from the list.
        """

        bw = self.__boundWidgets[index]

        # Only attempt to unbind if the parent
        # and widget have not been destroyed
        if bw.isAlive():
            bw.parent.Unbind(bw.evType, source=bw.widget)


    def unbindAllWidgets(self):
        """Unbinds all widgets which have been bound via :meth:`bindToWidget`.
        """

        for i in range(len(self.__boundWidgets)):
            self.__unbindWidget(i)

        self.__boundWidgets = []


    def getBoundWidgets(self):
        """Returns a list of :class:`BoundWidget` instances, containing all
        widgets which have been bound to this ``Action``.
        """
        return list(self.__boundWidgets)


    def __enabledChanged(self, *args):
        """Internal method which is called when the :attr:`enabled` property
        changes. Enables/disables any bound widgets.
        """

        for bw in self.__boundWidgets:

            # The widget may have been destroyed,
            # so check before trying to access it
            if bw.isAlive(): bw.widget.Enable(self.enabled)
            else:            self.unbindWidget(bw.widget)


class ToggleAction(Action):
    """A ``ToggleAction`` an ``Action`` which is intended to encapsulate
    actions that toggle some sort of state. For example, a ``ToggleAction``
    could be used to encapsulate an action which opens and/or closes a dialog
    window.
    """


    toggled = props.Boolean(default=False)
    """Boolean which tracks the current state of the ``ToggleAction``. """


    def __init__(self, *args, **kwargs):
        """Create a ``ToggleAction``.

        :arg autoToggle: Must be specified as a keyword argument. If ``True``
                         (the default), the state of ``toggled`` is inverted
                         every time this action is called. Otherwise, the
                         state of ``toggled``, and of all bound widgets/menu
                         items, needs to be changed manually.

        All other arguments are passed to :meth:`Action.__init__`.
        """

        autoToggle = kwargs.pop('autoToggle', True)

        Action.__init__(self, *args, **kwargs)

        self.__autoToggle = autoToggle

        self.addListener('toggled',
                         'ToggleAction_{}_internal'.format(id(self)),
                         self.__toggledChanged)


    def __call__(self, *args, **kwargs):
        """Call this ``ToggleAction``. The value of the :attr:`toggled` property
        is flipped.
        """

        # Copy the toggled value before running
        # the action, in case it gets inadvertently
        # changed
        toggled = self.toggled
        result  = Action.__call__(self, *args, **kwargs)

        # Update self.toggled to align
        # it with the widget state.
        if self.__autoToggle:
            self.toggled = not toggled

        # Or update the widget state to
        # align it with self.toggled
        else:
            self.__toggledChanged()

        return result


    def bindToWidget(self, parent, evType, widget, wrapper=None):
        """Bind this ``ToggleAction`` to a widget. If the widget is a
        ``wx.MenuItem``, its ``Check`` is called whenever the :attr:`toggled`
        state changes.
        """

        Action.bindToWidget(self, parent, evType, widget, wrapper)
        self.__setState(widget)


    def __setState(self, widget):
        """Sets the toggled state of the given widget to the current value of
        :attr:`toggled`.
        """

        import wx
        import fsleyes_widgets.bitmaptoggle as bmptoggle

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

        for bw in list(self.getBoundWidgets()):

            # An error will be raised if a widget
            # has been destroyed, so we'll unbind
            # any widgets which no longer exist.
            try:

                if not bw.isAlive():
                    raise Exception()

                self.__setState(bw.widget)

            except Exception:
                self.unbindWidget(bw.widget)


class NeedOverlayAction(Action):
    """The ``NeedOverlayAction`` is a convenience base class for actions
    which can only be executed when an overlay of a specific type is selected.
    It enables/disables itself based on the type of the currently selected
    overlay.
    """


    def __init__(self,
                 overlayList,
                 displayCtx,
                 func=None,
                 overlayType=fslimage.Image):
        """Create a ``NeedOverlayAction``.

        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg func:        The action function
        :arg overlayType: The required overlay type (defaults to :class:`.Image`)
        """
        Action.__init__(self, overlayList, displayCtx, func)

        self.__overlayType = overlayType
        self.__name        = 'NeedOverlayAction_{}_{}'.format(
            type(self).__name__, id(self))

        displayCtx .addListener('selectedOverlay',
                                self.__name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.__name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()


    def destroy(self):
        """Removes listeners from the :class:`.DisplayContext` and
        :class:`.OverlayList`, and calls :meth:`.Action.destroy`.
        """
        self.displayCtx .removeListener('selectedOverlay', self.__name)
        self.overlayList.removeListener('overlays',        self.__name)
        Action.destroy(self)


    def __selectedOverlayChanged(self, *a):
        """Called when the selected overlay, or overlay list, changes.

        Enables/disables this action depending on the nature of the selected
        overlay.
        """
        ovl          = self.displayCtx.getSelectedOverlay()
        ovlType      = self.__overlayType
        self.enabled = (ovl is not None) and isinstance(ovl, ovlType)
