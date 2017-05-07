#!/usr/bin/env python
#
# panel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLeyesPanel` and
:class:`FSLeyesSettingsPanel` classes.


A :class:`FSLeyesPanel` object is a :class:`wx.PyPanel` which provides some
sort of view of a collection of overlay objects, contained within an
:class:`.OverlayList`.  The :class:`FSLeyesSettingsPanel` is a convenience
class for certain *FSLeyes* control panels (see the ::mod:`fsleyes`
documentation).


``FSLeyesPanel`` instances are also :class:`.ActionProvider` instances - any
actions which are specified in the class definitions may (or may not) be
exposed to the user. Furthermore, any display configuration options which
should be made available available to the user can be added as
:class:`.PropertyBase` attributes of the :class:`FSLeyesPanel` subclass.


.. note:: ``FSLeyesPanel`` instances are usually displayed within a
          :class:`.FSLeyesFrame`, but they can  be used on their own
          as well. You will need to create, or need references to,
          an :class:`.OverlayList` and a :class:`.DisplayContext`.
          For example::

              import fsleyes.overlay          as ovl
              import fsleyes.displaycontext   as dc
              import fsleyes.views.orthopanel as op

              overlayList = ovl.OverlayList()
              displayCtx  = dc.DisplayContext(overlayList)

              # the parent argument is some wx parent
              # object such as a wx.Frame or wx.Panel.
              # Pass in None as the FSLeyesFrame
              orthoPanel  = op.OrthoPanel(parent,
                                          overlayList,
                                          displayCtx,
                                          None)
"""


import logging

import six

import                   wx
import wx.lib.agw.aui as wxaui

from   fsl.utils.platform import platform as fslplatform
import fsleyes_props                      as props
import fsleyes_widgets.widgetlist         as widgetlist
import fsleyes_widgets.floatspin          as floatspin
import fsleyes_widgets.floatslider        as floatslider
import fsleyes_widgets.rangeslider        as rangeslider

from . import                                actions
from . import                                displaycontext


log = logging.getLogger(__name__)


class _FSLeyesPanel(actions.ActionProvider, props.SyncableHasProperties):
    """The ``_FSLeyesPanel`` is the base class for the :class:`.FSLeyesPanel`
    and the :class:`.FSLeyesToolBar`.


    A ``_FSLeyesPanel`` has the following methods, available for use by
    subclasses:

    .. autosummary::
       :nosignatures:

       getName
       getFrame
       getOverlayList
       getDisplayContext
       setNavOrder
       destroy
       destroyed


    .. note:: When a ``_FSLeyesPanel`` is no longer required, the
              :meth:`destroy` method **must** be called!
    """


    def __init__(self, overlayList, displayCtx, frame, kbFocus=False):
        """Create a :class:`_FSLeyesPanel`.

        :arg overlayList: A :class:`.OverlayList` instance.

        :arg displayCtx:  A :class:`.DisplayContext` instance.

        :arg frame:       The :class:`.FSLeyesFrame` that created this
                          ``_FSLeyesPanel``. May be ``None``.

        :arg kbFocus:     If ``True``, a keyboard event handler is configured
                          to intercept ``Tab`` and ``Shift+Tab`` keyboard
                          events, to shift focus between a set of child
                          widgets. The child widgets to be included in the
                          navigation can be specified with the
                          :meth:`setNavOrder` method.
        """

        actions.ActionProvider     .__init__(self)
        props.SyncableHasProperties.__init__(self)

        if not isinstance(displayCtx, displaycontext.DisplayContext):
            raise TypeError(
                'displayCtx must be a '
                '{} instance'.format( displaycontext.DisplayContext.__name__))

        self.__overlayList = overlayList
        self.__displayCtx  = displayCtx
        self.__frame       = frame
        self.__name        = '{}_{}'.format(self.__class__.__name__, id(self))

        # TODO Remove these attributes. Access
        #      should be through the methods.
        self._overlayList = self.__overlayList
        self._displayCtx  = self.__displayCtx
        self._name        = self.__name

        self.__destroyed  = False
        self.__navOrder   = None

        if kbFocus:
            self.Bind(wx.EVT_CHAR_HOOK, self.__onCharHook)


    def setNavOrder(self, children):
        """Set the keyboard (tab, shift+tab) navigation order to the
        given list of controls, assumed to be children of this
        ``_FSLeyesPanel``.
        """

        nav = []

        allChildren = []
        for c in children:
            if type(c) == wx.Panel: allChildren.extend(c.GetChildren())
            else:                   allChildren.append(c)

        children = allChildren

        log.debug('Updating nav order for {}'.format(type(self).__name__))
        for i, w in enumerate(children):

            log.debug('{} nav {:2d}: {}'.format(
                type(self).__name__,
                i,
                type(w).__name__))

            # Special cases for some of our custom controls
            if isinstance(w, floatspin.FloatSpinCtrl):
                nav.append(w.textCtrl)
            elif isinstance(w, floatslider.SliderSpinPanel):
                nav.append(w.spinCtrl.textCtrl)
            elif isinstance(w, rangeslider.RangePanel):

                low  = w.lowWidget
                high = w.highWidget

                if isinstance(low, floatspin.FloatSpinCtrl):
                    low = low.textCtrl
                if isinstance(high, floatspin.FloatSpinCtrl):
                    high = high.textCtrl

                nav.extend([low, high])

            elif isinstance(w, rangeslider.RangeSliderSpinPanel):
                nav.extend([w.lowSpin.textCtrl, w.highSpin.textCtrl])
            else:
                nav.append(w)

        self.__navOrder = nav


    def __onCharHook(self, ev):
        """Called on ``EVT_CHAR_HOOK`` events. Intercepts tab key presses,
        to force an explicit keyboard navigation ordering.
        """

        if self.__navOrder is None or ev.GetKeyCode() != wx.WXK_TAB:
            ev.Skip()
            return

        # Get the widget that has focus
        try:
            focusIdx = self.__navOrder.index(wx.Window.FindFocus())

            log.debug('{} focus nav event ({:2d} [{}] is focused)'.format(
                type(self).__name__,
                focusIdx,
                type(wx.Window.FindFocus()).__name__))

        # Some other widget that we
        # don't care about has focus.
        except:
            ev.Skip()
            return

        if ev.ShiftDown(): offset = -1
        else:              offset =  1

        # Get the next widget in
        # the tab traversal order
        nextIdx = (focusIdx + offset) % len(self.__navOrder)

        # Search for the next enabled widget
        while not (self.__navOrder[nextIdx].IsEnabled() and
                   self.__navOrder[nextIdx].IsShownOnScreen()):

            if nextIdx == focusIdx:
                break

            nextIdx = (nextIdx + offset) % len(self.__navOrder)

        toFocus = self.__navOrder[nextIdx]

        log.debug('{}: moving focus to {:2d} [{}]'.format(
            type(self).__name__,
            nextIdx,
            type(toFocus).__name__))

        toFocus.SetFocus()

        # If the next widget to receive
        # focus is a TextCtrl, select
        # all of its text
        if isinstance(toFocus, wx.TextCtrl):
            toFocus.SelectAll()


    def getName(self):
        """Returns a unique name associated with this ``_FSLeyesPanel``. """
        return self.__name


    def getFrame(self):
        """Returns the :class:`.FSLeyesFrame` which created this
        ``_FSLeyesPanel``. May be ``None``, if this panel was not created
        by a ``FSLeyesFrame``.
        """
        return self.__frame


    def getDisplayContext(self):
        """Returns a reference to the :class:`.DisplayContext` that is
        associated with this ``_FSLeyesPanel``.
        """
        return self.__displayCtx


    def getOverlayList(self):
        """Returns a reference to the :class:`.OverlayList`. """
        return self.__overlayList


    def destroy(self):
        """This method must be called by whatever is managing this
        ``_FSLeyesPanel`` when it is to be closed/destroyed.

        It seems to be impossible to define a single handler (on either the
        :attr:`wx.EVT_CLOSE` and/or :attr:`wx.EVT_WINDOW_DESTROY` events)
        which handles both cases where the window is destroyed (in the process
        of destroying a parent window), and where the window is explicitly
        closed by the user (e.g. when embedded as a page in a Notebook).

        This issue is probably caused by my use of the AUI framework for
        layout management, as the AUI manager/notebook classes do not seem to
        call close/destroy in all cases. Everything that I've tried, which
        relies upon ``EVT_CLOSE``/``EVT_WINDOW_DESTROY`` events, inevitably
        results in the event handlers not being called, or in segmentation
        faults (presumably due to double-frees at the C++ level).

        Subclasses which need to perform any cleaning up when they are closed
        may override this method, and should be able to assume that it will be
        called. So this method *must* be called by managing code when a panel
        is deleted.

        Overriding subclass implementations must call this base class
        method, otherwise memory leaks will probably occur, and warnings will
        probably be output to the log (see :meth:`__del__`). This
        implememtation should be called **after** the subclass has performed
        its own clean-up, as this method expliciltly clears the
        ``_overlayList`` and ``_displayCtx`` references.
        """
        actions.ActionProvider.destroy(self)
        self.__frame       = None
        self.__displayCtx  = None
        self.__overlayList = None
        self.__navOrder    = None
        self.__destroyed   = True

        self._displayCtx   = None
        self._overlayList  = None


    def destroyed(self):
        """Returns ``True`` if a call to :meth:`destroy` has been made,
        ``False`` otherwise.
        """
        return self.__destroyed


    def __del__(self):
        """If the :meth:`destroy` method has not been called, a warning message
        logged.
        """
        if not self.__destroyed:
            log.warning('The {}.destroy() method has not been called '
                        '- unless the application is shutting down, '
                        'this is probably a bug!'.format(type(self).__name__))


FSLeyesPanelBase = None
"""Under Python2/wxPython, we need to derive from ``wx.PyPanel``. But
under Python3/wxPython-Phoenix, we need to derive from ``wx.Panel``.
"""


FSLeyesPanelMeta = None
"""Under Python3/wxPython-Phoenix, we need to specify a custom meta-class
which derives from ``wx.siplib.wrappertype``, and the
``props.PropertyOwner``. This is not necessary under Python2/wxPython.
"""

# wxPython/Phoenix
if fslplatform.wxFlavour == fslplatform.WX_PHOENIX:

    import wx.siplib as sip

    class PhoenixMeta(props.PropertyOwner, sip.wrappertype):
        pass

    FSLeyesPanelMeta = PhoenixMeta
    FSLeyesPanelBase = wx.Panel

# Old wxPython
else:
    FSLeyesPanelMeta = props.PropertyOwner
    FSLeyesPanelBase = wx.PyPanel


class FSLeyesPanel(six.with_metaclass(FSLeyesPanelMeta,
                                      _FSLeyesPanel,
                                      FSLeyesPanelBase)):
    """The ``FSLeyesPanel`` is the base class for all view and control panels
    in *FSLeyes*. See the :mod:`fsleyes` documentation for more details.
    """

    def __init__(self,
                 parent,
                 overlayList,
                 displayCtx,
                 frame,
                 *args,
                 **kwargs):

        # Slightly ugly way of supporting the _FSLeyesPanel
        # kbFocus argument. In order to catch keyboard events,
        # we need the WANTS_CHARS style. So we peek in
        # kwargs to see if it is present. If it is, we add
        # WANTS_CHARS to the style flag.
        kbFocus = kwargs.pop('kbFocus', False)
        if kbFocus:

            # The wx.Panel style defaults to TAB_TRAVERSAL
            style = kwargs.get('style', wx.TAB_TRAVERSAL)
            kwargs['style'] = style | wx.WANTS_CHARS

        FSLeyesPanelBase.__init__(self, parent, *args, **kwargs)
        _FSLeyesPanel.__init__(self, overlayList, displayCtx, frame, kbFocus)


class FSLeyesSettingsPanel(FSLeyesPanel):
    """The ``FSLeyesSettingsPanel`` is a convenience class for *FSLeyes*
    control panels which use a :class:`fsleyes_widgets.WidgetList` to display a
    collection of controls for the user.  When displayed as a dialog/floating
    frame, the ``FSLeyesSettingsPanel`` will automatically resize itself to
    fit its contents. See the :class:`.CanvasSettingsPanel` for an example.
    """


    def __init__(self, *args, **kwargs):
        """Create an ``FSLeyesSettingsPanel``.  All arguments are passed to
        the :meth:`FSLeyesPanel.__init__` method.
        """

        FSLeyesPanel.__init__(self, *args, **kwargs)

        self.__widgets = widgetlist.WidgetList(self)
        self.__sizer   = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__widgets, flag=wx.EXPAND, proportion=1)

        self.SetMinSize((80, 80))

        self.__widgets.Bind(widgetlist.EVT_WL_CHANGE_EVENT,
                            self.__widgetListChange)


    def getWidgetList(self):
        """Returns the :class:`fsleyes_widgets.WidgetList` which should be used
        by sub-classes to display content to the user.
        """
        return self.__widgets


    def __widgetListChange(self, ev):
        """Called whenever the widget list contents change. If this panel
        is floating, its parent is autmatically resized.
        """
        if isinstance(self.GetTopLevelParent(), wxaui.AuiFloatingFrame):
            self.SetInitialSize(self.__widgets.GetBestSize())
            self.GetTopLevelParent().Fit()
