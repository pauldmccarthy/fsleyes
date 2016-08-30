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
              # object such as a wx.Frame or wx.Panel
              orthoPanel  = op.OrthoPanel(parent, overlayList, displayCtx)
"""


import logging

import six

import                   wx
import wx.lib.agw.aui as wxaui

import                        props
import pwidgets.widgetlist as widgetlist

from fsl.utils.platform import platform as fslplatform
from .                  import             actions
from .                  import             displaycontext


log = logging.getLogger(__name__)


class _FSLeyesPanel(actions.ActionProvider, props.SyncableHasProperties):
    """The ``_FSLeyesPanel`` is the base class for the :class:`.FSLeyesPanel`
    and the :class:`.FSLeyesToolBar`.

    
    A ``_FSLeyesPanel`` has the following attributes, intended to be used by
    subclasses:
    
      - :attr:`_overlayList`: A reference to the :class:`.OverlayList`
        instance which contains the images to be displayed.
    
      - :attr:`_displayCtx`: A reference to the :class:`.DisplayContext`
        instance, which contains display related properties about the
        :attr:`_overlayList`.
    
      - :attr:`_name`: A unique name for this :class:`_FSLeyesPanel`.


    .. note:: When a ``_FSLeyesPanel`` is no longer required, the
              :meth:`destroy` method **must** be called!
    """ 

    
    def __init__(self, overlayList, displayCtx):
        """Create a :class:`_FSLeyesPanel`.

        :arg overlayList: A :class:`.OverlayList` instance.
        
        :arg displayCtx:  A :class:`.DisplayContext` instance.
        """
        
        actions.ActionProvider     .__init__(self)
        props.SyncableHasProperties.__init__(self)

        if not isinstance(displayCtx, displaycontext.DisplayContext):
            raise TypeError(
                'displayCtx must be a '
                '{} instance'.format( displaycontext.DisplayContext.__name__))

        self._overlayList = overlayList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self))
        
        self.__destroyed  = False


    def getDisplayContext(self):
        """Returns a reference to the :class:`.DisplayContext` that is
        associated with this ``_FSLeyesPanel``.
        """
        return self._displayCtx

    
    def getOverlayList(self):
        """Returns a reference to the :class:`.OverlayList`. """
        return self._overlayList

        
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
        self._displayCtx  = None
        self._overlayList = None
        self.__destroyed  = True

        
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
``props.SyncablePropertyOwner``. This is not necessary under Python2/wxPython.
"""

# wxPython/Phoenix
if fslplatform.wxFlavour == fslplatform.WX_PHOENIX:

    import wx.siplib as sip

    class PhoenixMeta(props.SyncablePropertyOwner, sip.wrappertype):
        pass

    FSLeyesPanelMeta = PhoenixMeta
    FSLeyesPanelBase = wx.Panel

# Old wxPython
else:
    FSLeyesPanelMeta = props.SyncablePropertyOwner
    FSLeyesPanelBase = wx.PyPanel


class FSLeyesPanel(six.with_metaclass(FSLeyesPanelMeta,
                                      _FSLeyesPanel,
                                      FSLeyesPanelBase)):
    """The ``FSLeyesPanel`` is the base class for all view and control panels in
    *FSLeyes*. See the :mod:`fsleyes` documentation for more details.
    """
    
    def __init__(self, parent, overlayList, displayCtx):
        FSLeyesPanelBase.__init__(self, parent)
        _FSLeyesPanel.__init__(self, overlayList, displayCtx)


class FSLeyesSettingsPanel(FSLeyesPanel):
    """The ``FSLeyesSettingsPanel`` is a convenience class for *FSLeyes*
    control panels which use a :class:`pwidgets.WidgetList` to display a
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
        """Returns the :class:`pwidgets.WidgetList` which should be used by
        sub-classes to display content to the user.
        """
        return self.__widgets


    def __widgetListChange(self, ev):
        """Called whenever the widget list contents change. If this panel
        is floating, its parent is autmatically resized.
        """
        if isinstance(self.GetTopLevelParent(), wxaui.AuiFloatingFrame):
            self.SetBestSize(self.__widgets.GetBestSize())
            self.GetTopLevelParent().Fit()
