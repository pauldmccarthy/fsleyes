#!/usr/bin/env python
#
# panel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLeyesPanel` class.


A :class:`FSLeyesPanel` object is a :class:`wx.Panel` which provides some sort
of view of a collection of overlay objects, contained within an
:class:`.OverlayList`. The :class:`FSLeyesPanel` is the base class for all GUI
panels in FSLeyes - see also the :class:`.ViewPanel` and :class:`.ControlPanel`
classes.


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

import wx

from   fsl.utils.platform import platform as fslplatform
import fsl.utils.deprecated               as deprecated
import fsleyes_props                      as props
import fsleyes_widgets.floatspin          as floatspin
import fsleyes_widgets.floatslider        as floatslider
import fsleyes_widgets.rangeslider        as rangeslider

from . import                                actions
from . import                                displaycontext


log = logging.getLogger(__name__)


class _FSLeyesPanel(actions.ActionProvider, props.SyncableHasProperties):
    """The ``_FSLeyesPanel`` is the base class for the :class:`.FSLeyesPanel`
    and the :class:`.FSLeyesToolBar`.


    A ``_FSLeyesPanel`` has the following methods and properties, available for
    use by subclasses:

    .. autosummary::
       :nosignatures:

       name
       frame
       overlayList
       displayCtx
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
        self.__destroyed   = False
        self.__navOrder    = None

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
        except Exception:
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


    @property
    def name(self):
        """Returns a unique name associated with this ``_FSLeyesPanel``. """
        return self.__name


    @property
    def frame(self):
        """Returns the :class:`.FSLeyesFrame` which created this
        ``_FSLeyesPanel``. May be ``None``, if this panel was not created
        by a ``FSLeyesFrame``.
        """
        return self.__frame


    @property
    def displayCtx(self):
        """Returns a reference to the :class:`.DisplayContext` that is
        associated with this ``_FSLeyesPanel``.
        """
        return self.__displayCtx


    @property
    def overlayList(self):
        """Returns a reference to the :class:`.OverlayList`. """
        return self.__overlayList


    @property
    @deprecated.deprecated('0.16.0', '1.0.0', 'Use overlayList instead')
    def _overlayList(self):
        return self.__overlayList


    @property
    @deprecated.deprecated('0.16.0', '1.0.0', 'Use displayCtx instead')
    def _displayCtx(self):
        return self.__displayCtx


    @property
    @deprecated.deprecated('0.16.0', '1.0.0', 'Use name instead')
    def _name(self):
        return self.__name


    @deprecated.deprecated('0.15.2', '1.0.0', 'Use name instead')
    def getName(self):
        """Returns a unique name associated with this ``_FSLeyesPanel``. """
        return self.__name


    @deprecated.deprecated('0.15.2', '1.0.0', 'Use frame instead')
    def getFrame(self):
        """Returns the :class:`.FSLeyesFrame` which created this
        ``_FSLeyesPanel``. May be ``None``, if this panel was not created
        by a ``FSLeyesFrame``.
        """
        return self.__frame


    @deprecated.deprecated('0.15.2', '1.0.0', 'Use displayCtx instead')
    def getDisplayContext(self):
        """Returns a reference to the :class:`.DisplayContext` that is
        associated with this ``_FSLeyesPanel``.
        """
        return self.__displayCtx


    @deprecated.deprecated('0.15.2', '1.0.0', 'Use overlayList instead')
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
        ``__overlayList`` and ``__displayCtx`` references.
        """
        actions.ActionProvider.destroy(self)
        self.__frame       = None
        self.__displayCtx  = None
        self.__overlayList = None
        self.__navOrder    = None
        self.__destroyed   = True

        self.__displayCtx  = None
        self.__overlayList = None


    def destroyed(self):
        """Returns ``True`` if a call to :meth:`destroy` has been made,
        ``False`` otherwise.
        """
        return self.__destroyed


    def __del__(self):
        """If the :meth:`destroy` method has not been called, a warning message
        is logged.
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
"""Under Python3/wxPython-Phoenix, we need to specify the meta-class as
``wx.siplib.wrappertype``. This is not necessary under Python2/wxPython.
"""

# wxPython/Phoenix
if fslplatform.wxFlavour == fslplatform.WX_PHOENIX:

    import wx.siplib as sip

    FSLeyesPanelMeta = sip.wrappertype
    FSLeyesPanelBase = wx.Panel

# Old wxPython
else:
    FSLeyesPanelMeta = type
    FSLeyesPanelBase = wx.PyPanel


class FSLeyesPanel(six.with_metaclass(FSLeyesPanelMeta,
                                      _FSLeyesPanel,
                                      FSLeyesPanelBase)):
    """The ``FSLeyesPanel`` is the base class for all view and control panels
    in *FSLeyes*. See the :mod:`fsleyes` documentation for more details.

    See also the :class:`.ViewPanel` and :class:`.ControlPanel` classes.
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
    """The ``FSLeyesSettingsPanel`` is deprecated - it has been replaced
    with the :class:`.controls.controlpanel.SettingsPanel`.
    """
    @deprecated.deprecated(
        '0.26.0', '1.0.0', 'Use controls.controlpanel.SettingsPanel instead')
    def __init__(self, parent, *args, **kwargs):
        FSLeyesPanel.__init__(self, parent, *args, **kwargs)

        from fsleyes.controls.controlpanel import SettingsPanel

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.__panel = SettingsPanel(self, *args, **kwargs)
        self.__sizer.Add(self.__panel, flag=wx.EXPAND, proportion=1)
        self.SetSizer(self.__sizer)
    def getWidgetList(self):
        return self.__panel.getWidgetList()
