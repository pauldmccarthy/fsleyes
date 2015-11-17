#!/usr/bin/env python
#
# panel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FSLEyesPanel` class.


A :class:`FSLEyesPanel` object is a :class:`wx.PyPanel` which provides some
sort of view of a collection of overlay objects, contained within an
:class:`.OverlayList`. 


``FSLEyesPanel`` instances are also :class:`.ActionProvider` instances - any
actions which are specified during construction may (or may not ) be exposed
to the user. Furthermore, any display configuration options which should be
made available available to the user can be added as :class:`.PropertyBase`
attributes of the :class:`FSLEyesPanel` subclass.


.. note:: ``FSLEyesPanel`` instances are usually displayed within a
          :class:`.FSLEyesFrame`, but they can  be used on their own
          as well. You will need to create, or need references to,
          an :class:`.OverlayList` and a :class:`.DisplayContext`.
          For example::

              import fsl.fsleyes.overlay          as ovl
              import fsl.fsleyes.displaycontext   as dc
              import fsl.fsleyes.views.orthopanel as op

              overlayList = ovl.OverlayList()
              displayCtx  = dc.DisplayContext(overlayList)

              # the parent argument is some wx parent
              # object such as a wx.Frame or wx.Panel
              orthoPanel  = op.OrthoPanel(parent, overlayList, displayCtx)
"""


import logging

import wx

import props

import actions
import displaycontext


log = logging.getLogger(__name__)


class _FSLEyesPanel(actions.ActionProvider, props.SyncableHasProperties):
    """The ``_FSLEyesPanel`` is the base class for the :class:`.FSLEyesPanel`
    and the :class:`.FSLEyesToolBar`.

    
    A ``_FSLEyesPanel`` has the following attributes, intended to be used by
    subclasses:
    
      - :attr:`_overlayList`: A reference to the :class:`.OverlayList`
        instance which contains the images to be displayed.
    
      - :attr:`_displayCtx`: A reference to the :class:`.DisplayContext`
        instance, which contains display related properties about the
        :attr:`_overlayList`.
    
      - :attr:`_name`: A unique name for this :class:`_FSLEyesPanel`.


    .. note:: When a ``_FSLEyesPanel`` is no longer required, the
              :meth:`destroy` method **must** be called!
    """ 

    
    def __init__(self, overlayList, displayCtx):
        """Create a :class:`ViewPanel`.

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

        
    def destroy(self):
        """This method must be called by whatever is managing this 
        ``_FSLEyesPanel`` when it is to be closed/destroyed.

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

    
    def __del__(self):
        """If the :meth:`destroy` method has not been called, a warning message
        logged.
        """
        if not self.__destroyed:
            log.warning('The {}.destroy() method has not been called '
                        '- unless the application is shutting down, '
                        'this is probably a bug!'.format(type(self).__name__))


class FSLEyesPanel(_FSLEyesPanel, wx.PyPanel):
    """The ``FSLEyesPanel`` is the base class for all view and control panels in
    *FSLeyes*. See the :mod:`~fsl.fsleyes` documentation for more details.
    """
    
    def __init__(self, parent, overlayList, displayCtx):
        wx.PyPanel.__init__(self, parent)
        _FSLEyesPanel.__init__(self, overlayList, displayCtx)
