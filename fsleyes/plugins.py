#!/usr/bin/env python
#
# plugins.py - Accessing installed FSLeyes plugins.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides access to installed FSLeyes plugins. FSLeyes uses
``setuptools`` `entry points
<https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points>`_
to provide a simple plugin architecture for loading custom views, controls,
and tools.

Things plugins can provide
--------------------------

FSLeyes plugins can provide custom *views*, *controls* and *tools*:

 - A *view* is a top level panel, such as an :class:`.OrthoPanel`,
   :class:`.Scene3DPanel`, or :class:`.TimeSeriesPanel`. Views provided
   by plugins are added to the top level *Views* menu.

 - A *control* is a secondary panel, or toolbar, which is embedded within a
   view, such as an :class:`.OverlayListPanel`, :class:`.OrthoToolBar`, or
   :class:`.MelodicClassificationPanel`. Controls provided by plugins are
   added to the *Settings* menu for each active view.

 - A *tool* is an :class:`.Action` which is associated with a menu item
   under the top-level *Tools* menu, such as the :class:`.ApplyFlirtXfmAction`
   and the :class:`.ResampleAction`.


Writing your own FSLeyes plugin
-------------------------------

TODO
"""


import logging
import collections
import pkg_resources

import fsleyes.actions.base          as base
import fsleyes.views.viewpanel       as viewpanel
import fsleyes.controls.controlpanel as ctrlpanel


log = logging.getLogger(__name__)


def listPlugins():
    """Returns a list containing the names of all installed FSLeyes plugins.
    """
    plugins = []
    for dist in pkg_resources.working_set:
        if dist.project_name.startswith('fsleyes-plugin'):
            plugins.append(dist.project_name)
    return list(sorted(plugins))


def _listEntryPoints(group):
    """Returns a dictionary containing ``{name : type}`` entry points for the
    given entry point group.

    https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points
    """
    items = collections.OrderedDict()
    for plugin in listPlugins():
        for name, ep in pkg_resources.get_entry_map(plugin, group).items():
            items[name] = ep.load()
        return items


def listViews():
    """Returns a dictionary of ``{name : ViewPanel}`` mappings containing
    the custom views provided by all installed FSLeyes plugins.
    """
    views = _listEntryPoints('fsleyes_views')
    for name, cls in list(views.items()):
        if not issubclass(cls, viewpanel.ViewPanel):
            log.debug('Ignoring fsleyes_views entry point '
                      '{} - not a ViewPanel'.format(name))
            views.pop(name)
            continue
    return views


def listControls():
    """Returns a dictionary of ``{name : ControlPanel}`` mappings containing
    the custom controls provided by all installed FSLeyes plugins.
    """
    ctrls = _listEntryPoints('fsleyes_controls')
    for name, cls in list(ctrls.items()):
        if not issubclass(cls, (ctrlpanel.ControlPanel,
                                ctrlpanel.ControlToolBar)):
            log.debug('Ignoring fsleyes_controls entry point {} - '
                      'not a ControlPanel/ToolBar'.format(name))
            ctrls.pop(name)
            continue
    return ctrls


def listTools():
    """Returns a dictionary of ``{name : Action}`` mappings containing
    the custom tools provided by all installed FSLeyes plugins.
    """
    tools = _listEntryPoints('fsleyes_tools')
    for name, cls in list(tools.items()):
        if not issubclass(cls, base.Action):
            log.debug('Ignoring fsleyes_tools entry point '
                      '{} - not an Action'.format(name))
            tools.pop(name)
            continue
    return tools
