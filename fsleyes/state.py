#!/usr/bin/env python
#
# state.py - Functions for saving/restoring the state of *FSLeyes*.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides two functions, :func:`save` and :func:`restore`.
These functions may be used to save/restore the state of *FSLeyes*.

 .. note:: :func:`restore` is currently not implemented.
"""

import                  importlib
from collections import OrderedDict

import fsleyes_props as props

from .           import perspectives


def save(frame):
    """Creates and returns a dictionary containing the current state of the
    given :class:`.FSLeyesFrame`, the :class:`.OverlayList` and
    :class:`.DisplayContext` associated with it, and the :class:`.ViewPanel`
    instances being displayed.
    """

    overlayList = frame.getOverlayList()
    displayCtx  = frame.getDisplayContext()
    viewPanels  = frame.getViewPanels()

    layout   = perspectives.serialisePerspective(frame)
    overlays = [(type(o).__name__, o.dataSource) for o in overlayList]

    overlays = []

    for i, ovl in enumerate(overlayList):
        overlays.append(OrderedDict([
            ('type',   '{}.{}'.format(ovl.__module__, type(ovl).__name__)),
            ('name',   ovl.name),
            ('source', ovl.dataSource)]))

    state                   = OrderedDict()
    state['Layout']         = layout
    state['Overlays']       = overlays
    state['DisplayContext'] = _displayContextState(overlayList, displayCtx)

    vpStates = {}

    for vp in viewPanels:

        # Accessing the undocumented
        # AuiPaneInfo.name attribute
        vpName       = frame.getViewPanelInfo(vp).name
        vpDisplayCtx = vp.getDisplayContext()

        vpStates[vpName] = OrderedDict([
            ('View',           _viewPanelState(vp)),
            ('DisplayContext', _displayContextState(overlayList,
                                                    vpDisplayCtx))])

    state['ViewPanels'] = vpStates

    return state


def _displayContextState(overlayList, displayCtx):
    """Creates and returns a hierarchical dictionary containing
    the state of the given :class:`.DisplayContext` and the
    :class:`.Display`/:class:`.DisplayOpts` instances which it
    is managing.
    """

    state     = OrderedDict()
    overlays  = []
    propNames = displayCtx.getAllProperties()[0]

    for overlay in overlayList:

        display = displayCtx.getDisplay(overlay)
        opts    = displayCtx.getOpts(   overlay)

        overlays.append(OrderedDict([
            ('Display',     _displayState(    display)),
            ('DisplayOpts', _displayOptsState(opts))]))

    for propName in propNames:
        state[propName] = props.serialise(displayCtx, propName)

    state['Overlays'] = overlays

    return state


def _displayState(display):
    """Creates and returns a dictionary containing the state of the given
    :class:`.Display` instance.
    """

    state     = OrderedDict()
    propNames = display.getAllProperties()[0]

    for propName in propNames:
        state[propName] = props.serialise(display, propName)

    return state


def _displayOptsState(opts):
    """Creates and returns a dictionary containing the state of the given
    :class:`.DisplayOpts` instance.
    """

    state     = OrderedDict()
    propNames = opts.getAllProperties()[0]

    state['type'] = type(opts).__name__

    for propName in propNames:
        state[propName] = props.serialise(opts, propName)

    return state


def _viewPanelState(viewPanel):
    """Creates and returns a dictionary containing the state of the given
    :class:`.ViewPanel`.
    """

    import fsleyes.views.canvaspanel as canvaspanel

    state     = OrderedDict()
    propNames = viewPanel.getAllProperties()[0]

    state['type'] = type(viewPanel).__name__

    for propName in propNames:
        state[propName] = props.serialise(viewPanel, propName)

    if isinstance(viewPanel, canvaspanel.CanvasPanel):

        sceneOptsState = OrderedDict()
        sceneOpts      = viewPanel.getSceneOptions()
        propNames      = sceneOpts.getAllProperties()[0]

        sceneOptsState['type'] = type(sceneOpts).__name__

        for propName in propNames:
            sceneOptsState[propName] = props.serialise(sceneOpts, propName)

        state['SceneOpts'] = sceneOptsState

    return state


def restore(frame, state):
    """Applies a state, previously saved via :func:`save`, to the given
    :class:`.FSLeyesFrame`.

    .. note:: Not implemented.
    """

    return

    overlayList     = frame.getOverlayList()
    displayCtx      = frame.getDisplayContext()
    layout          = state['Layout']
    overlays        = state['Overlays']
    displayCtxState = state['DisplayContext']
    vpStates        = state['ViewPanels']

    # First, remove all view panels and then
    # clear the overlay list. We do it in this
    # order to avoid any unncessary processing
    # by existing view panel DisplayContexts.
    frame.removeAllViewPanels()
    overlayList[:] = []

    # Populate the overlay list and configure
    # the master display context
    overlayObjs = []
    for ovl in overlays:
        klass      = ovl['type']
        name       = ovl['name']
        dataSource = ovl['source']

        # We can't restore in-memory overlays
        if dataSource is None or dataSource.lower() == 'none':
            continue

        # Split the (fully-qualified)
        # class name into the containing
        # module and the class name.
        klass  = klass.split('.')
        module = '.'.join(klass[:-1])
        klass  = klass[-1]

        # Import the module, and
        # look up the class object
        module = importlib.import_module(module)
        klass  = getattr(module, klass)

        # Create the overlay object
        ovl      = klass(dataSource)
        ovl.name = name
        overlayObjs.append(ovl)

    # Restore the master display contxt
    _restoreDisplayContext(displayCtx, overlayList, displayCtxState)

    # Apply the frame perspective
    perspectives.applyPerspective(frame, None, layout)

    # Restore view panel settings
    viewPanels = frame.getViewPanels()
    for vp, vpState in zip(viewPanels, vpStates):
        _restoreViewPanel(vp, overlayList, vpState)


def _restoreViewPanel(viewPanel, overlayList, state):

    displayCtx     = viewPanel.getDisplayContext()
    sceneOpts      = viewPanel.getSceneOptions()
    vpState        = state['View']
    dcState        = state['DisplayContext']
    vpType         = vpState.pop('type')
    sceneOptsState = vpState.pop('SceneOpts')

    _restoreDisplayContext(displayCtx, overlayList, dcState)
    _applyProps(viewPanel, vpState)
    _applyProps(sceneOpts, sceneOptsState)


def _restoreDisplayContext(displayCtx, overlayList, state):

    # Configure selected properties
    # of the master display context
    dcProps = ['selectedOverlay',
               'location',
               # 'overlayOrder',
               'syncOverlayDisplay',
               'displaySpace',
               'autoDisplay']

    _applyProps(displayCtx, state, dcProps)

    for overlay, ovlState in zip(overlayList, state['Overlays']):
        displayState = ovlState['Display']
        optsState    = ovlState['DisplayOpts']

        display = displayCtx.getDisplay(overlay)
        _applyProps(display, displayState)

        # TODO: This will almost certainly fail
        #       for non-trivial properties (e.g.
        #       VolumeOpts.clipImage)
        opts = displayCtx.getOpts(overlay)
        _applyProps(opts, optsState)


def _applyProps(target, values, propNames=None):

    if propNames is None:
        propNames = values.keys()

    for propName in propNames:

        val = values[propName]
        val = props.deserialise(target, propName, val)

        setattr(target, propName, val)
