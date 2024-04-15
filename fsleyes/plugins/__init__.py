#!/usr/bin/env python
#
# __init__.py - Accessing installed FSLeyes plugins.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package provides access to installed and built-in FSLeyes plugins.


FSLeyes uses a simple plugin architecture for loading custom views, controls,
tools, and layouts. Plugins can be installed from Python libraries (e.g. as
hosted on `PyPi <https://pypi.org/>`_), or installed directly from a ``.py``
file.


In both cases, FSLeyes uses `entry points
<https://packaging.python.org/specifications/entry-points/>`__
to locate the items provided by plugin library/files.


Things plugins can provide
--------------------------


FSLeyes plugins can provide custom *views*, *controls*, *tools*, and *layouts*:

 - A *view* is a top level panel, such as an :class:`.OrthoPanel`,
   :class:`.Scene3DPanel`, or :class:`.TimeSeriesPanel`. Views provided
   by plugins are added to the top level *Views* menu.

 - A *control* is a secondary panel, or toolbar, which is embedded within a
   view, such as an :class:`.OverlayListPanel`, :class:`.OrthoToolBar`, or
   :class:`.MelodicClassificationPanel`. Controls provided by plugins are
   added to the *Settings* menu for each active view.

 - A *tool* is an :class:`.Action` which is associated with a menu item under
   the top-level *Tools* menu, such as the :class:`.ApplyFlirtXfmAction`, the
   :class:`.CropImageAction`, and the :class:`.ResampleAction`.

 - A *layout* is a string which specifies the layout of the FSLeyes frame,
   comprising one or more view panels, and a set of control panels for each
   view. Refer to the :mod:`fsleyes.layouts` module for more details.


FSLeyes plugin sources
----------------------

FSLeyes plugins can be loaded from the following locations:

 - Built-in plugins from the :mod:`fsleyes.plugins` package.
 - Single-file plugins that have been loaded/installed by the user.
 - Plugins from third-party libraries that are installed into the running Python
   environment.

The default behaviour, when FSLeyes starts up, is to only expose plugins from
the first two locations - plugins from third party libraries are hidden by
default. However, third-party plugins are automatically made available when a
layout from the same library is loaded.

Third-party plugins can also be made visible by default if you start FSLeyes
with the ``--showAllPlugins`` command-line option.


Loading/installing FSLeyes plugins
----------------------------------


FSLeyes plugins are loaded into a running FSLeyes as follows:

 - Any Python libraries (e.g. installed from ``PyPi``) which are present the
   environment that FSLeyes is running in, and which provide any FSLeyes entry
   points, will automatically be detected by FSLeyes.

 - Plugin ``.py`` files, which contain view, control, tool, and/or layout
   definitions, can be passed directly to the :func:`loadPlugin` function.

 - Plugin ``.py`` files which are present in the FSLeyes settings directory,
   or which are found in the ``FSLEYES_PLUGIN_PATH`` environment variable, will
   be loaded by the :func:`initialise` function.

 - Built-in plugins located within the ``fsleyes.plugins`` package.


A plugin can be installed permanently into FSLeyes as follows:

 - Any Python libraries (e.g. installed from ``PyPi``) which are present the
   environment that FSLeyes is running in, and which provide any FSLeyes entry
   points, will automatically be detected by FSLeyes.

 - ``.py`` plugin files can be passed to the :func:`installPlugin`
   function. This file will be saved into the FSLeyes settings directory
   (e.g. ``~/.fsleyes/plugins/``).


Writing a FSLeyes plugin
------------------------


.. note:: A minimal example of a FSLeyes plugin library can be found in
          ``fsleyes/tests/testdata/fsleyes_plugin_example/``, and a range of
          built-in plugins can be found in ``fsleyes/plugins/``.


.. warning:: FSLeyes assumes that **all** views, controls, tools, and layouts
             have unique names.  So expect problems if, for example, you
             define your own FSLeyes control with a name that is already used
             by a built-in control, e.g. ``OverlayListPanel``.


A FSLeyes plugin is a Python library, or a ``.py`` file, which contains
definitions for custom views, controls, tools, and layouts.

 - Views must be sub-classes of the :class:`.ViewPanel` class.

 - Controls must be sub-classes of the :class:`.ControlPanel` or
   :class:`.ControlToolBar` classes.

 - Tools must be sub-classes of the :class:`.Action` class.

 - Layouts must be strings or tuples. For single-file plugins, layout variables
   must have a name that begins with ``FSLEYES_LAYOUT_``. If a layout is a
   string, it is given a name based on the name of the variable. If a layout
   is a tuple, the first value in the tuple is used as the name, and the second
   value is assumed to be the layout string.


To write a ``.py`` file which can be loaded as a FSLeyes plugin, simply define
your views, controls, tools, and layouts in the file. The file path can then be
passed to the :func:`loadPlugin` or :func:`installPlugin` function.


To release a FSLeyes plugin as a library, you need to organise your code
as a Python library. Minimally, this requires the following:

 - Arrange your ``.py`` file(s) into a Python package.

 - Expose your custom views, controls, tools, and layouts as `entry points
   <https://packaging.python.org/specifications/entry-points/>`_.


A minimal ``pyproject.toml`` file for a FSLeyes plugin might look like this::

    [build-system]
    requires      = ["setuptools"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "my-cool-fsleyes-plugin"

    # Views, controls, tools, and layouts
    # must be exposed as entry points
    # within groups called "fsleyes_views",
    # "fsleyes_controls", "fsleyes_tools"
    # and "fsleyes_layouts" respectively.

    [project.entry-points.fsleyes_views]
    "My cool view" = "myplugin:MyView"

    [project.entry-points.fsleyes_controls]
    "My cool control" = "myplugin:MyControl"

    [project.entry-points.fsleyes_tools]
    "My cool tool" = "myplugin.MyTool"

    [project.entry-points.fsleyes_layouts]
    "My cool layout" = "myplugin.MyLayout"


See the `Python Packaging guide
<https://packaging.python.org/tutorials/packaging-projects/>`_ for more
details on packaging Python libraries.


Module contents
---------------

As plugins provided by installed libraries are automatically taken care of by
``importlib``, most of the logic in this module is for managing single-file
FSLeyes plugins. When a plugin file is loaded, a custom
``importlib.metadata.Distribution`` instance is created and registered using a
custom ``importlib.abvc.MetaPathFinder`` instance. The plugin file is scanned
to identify the plugins that it provides, and these are exposed as entry
points of the distribution.


At present there are few examples available on how to accomplish the above,
but there are enough clues in the ``importlib.metadata`` documentation at:

https://docs.python.org/3/library/importlib.metadata.html#extending-the-search-algorithm.


The following functions can be used to load/install new plugins:

.. autosummary::
   :nosignatures:

   initialise
   loadPlugin
   installPlugin


The following functions can be used to access plugins:

.. autosummary::
   :nosignatures:

   listViews
   listControls
   listTools
   listLayouts
   lookupControl
   lookupTool
   layoutModule
   pluginTitle
"""


import functools           as ft
import os.path             as op
import                        os
import                        sys
import                        glob
import                        random
import                        string
import                        fnmatch
import                        pkgutil
import                        logging
import                        importlib
import importlib.util      as imputil
import importlib.metadata  as impmeta
import                        collections


from typing import Dict, Union, Type, Optional, Sequence
from types  import ModuleType

import fsl.utils.settings            as fslsettings
import fsleyes.actions               as actions
import fsleyes.strings               as strings
import fsleyes.views.viewpanel       as viewpanel
import fsleyes.views.canvaspanel     as canvaspanel
import fsleyes.controls.controlpanel as ctrlpanel


log = logging.getLogger(__name__)


View    = Type[viewpanel.ViewPanel]
Control = Union[Type[ctrlpanel.ControlMixin], Type[ctrlpanel.ControlToolBar]]
Tool    = Type[actions.Action]
Layout  = Union[str, tuple]
Plugin  = Union[View, Control, Tool, Layout]


SHOW_THIRD_PARTY_PLUGINS = set()
"""Global toggle which controls whether plugins provided by installed
third-party libraries are exposed by the :func:`listViews`,
:func:`listControls`, and :func:`listTools` functions.  Layouts provided
by plugins are always visible.

This field may either be a set containing the names of specific third-party
plugins to show, or a boolean which will toggle all third party plugins on or
off.
"""


def showThirdPartyPlugin(modname : str):
    """Show plugins from the given third party module. """
    global SHOW_THIRD_PARTY_PLUGINS
    if SHOW_THIRD_PARTY_PLUGINS is True:
        return
    if SHOW_THIRD_PARTY_PLUGINS is False:
        SHOW_THIRD_PARTY_PLUGINS = set()
    SHOW_THIRD_PARTY_PLUGINS.add(modname)


def shouldShowThirdPartyPlugin(modname : str) -> bool:
    """Return ``True`` if the given plugin should be visible, ``False``
    otherwise.
    """
    if SHOW_THIRD_PARTY_PLUGINS in (True, False):
        return SHOW_THIRD_PARTY_PLUGINS

    for pattern in SHOW_THIRD_PARTY_PLUGINS:
        if fnmatch.fnmatch(modname, f'{pattern}*'):
            return True
    return False


class FSLeyesPlugin(impmeta.Distribution):
    """Custom ``importlib.metadata.Distribution`` used to represent FSLeyes
    plugins that are loaded from a single file.

    A ``FSLeyesPlugin`` is created for each single-file FSLeyes plugin that
    is registered with the :meth:`FSLeyesPluginFinder.add_plugin` method.
    """

    def __init__(self, module : ModuleType, modname : str):
        """Create a ``FSLeyesPlugin`` from a single-file plugin file that
        has already been loaded as a module.

        :arg module:  The loaded module
        :arg modname: The module name
        """
        log.debug('New FSLeyesPlugin(%s)', modname)
        self.__module  = module
        self.__modname = modname


    @property
    def version(self) -> str:
        return '0.0.0'


    @property
    def name(self) -> str:
        return self.__modname


    def read_text(self, filename):
        return None


    def locate_file(self, path):
        raise NotImplementedError()


    @property
    @ft.lru_cache
    def entry_points(self) -> Sequence[impmeta.EntryPoint]:
        """Return a sequence of ``EntryPoint`` objects provided by the plugin.  The
        :meth:`FSLeyesPlugin.find_entry_points` function is used to scan the
        module for entry points.
        """

        modname = self.__modname
        alleps  = FSLeyesPlugin.find_entry_points(self.__module)
        epobjs  = []

        for group, eps in alleps.items():
            for name, plugin in eps.items():

                # layouts can be either strings with
                # variable name FSLEYES_LAYOUT_<label>
                # or tuples containing (label, layout)
                if isinstance(plugin, (tuple, str)):
                    if isinstance(plugin, tuple):
                        label  = plugin[0]
                        plugin = plugin[1]
                    else:
                        label = name[15:]

                # View/Control/Tool plugins can implement
                # a title() staticmethod to specify their
                # title/label
                else:
                    label = plugin.title()
                    # Look up label for built-in plugins
                    if label is None:
                        if group == 'fsleyes_tools':
                            label = strings.actions.get(name, name)
                        else:
                            label = strings.titles.get(name, name)

                epobjs.append(impmeta.EntryPoint(label,
                                                 f'{modname}:{name}',
                                                 group=group))
        return epobjs


    @staticmethod
    def find_entry_points(mod : ModuleType) -> Dict[str, Dict[str, Plugin]]:
        """Finds the FSLeyes entry points (views,
        controls, tools, or layouts) that are defined within the given module.

        :arg mod: The module to search
        :returns: A dictionary
        """

        entryPoints = collections.defaultdict(dict)

        for name in dir(mod):

            item  = getattr(mod, name)
            ptype = _pluginType(item)

            if not ptype:
                continue

            if ptype == 'layout':
                # Layouts from single-file plugins must have
                # a variable name starting with FSLEYES_LAYOUT_
                if not name.startswith('FSLEYES_LAYOUT_'):
                    continue

            bases = [viewpanel.ViewPanel,
                     canvaspanel.CanvasPanel,
                     ctrlpanel.ControlPanel,
                     ctrlpanel.ControlToolBar,
                     ctrlpanel.SettingsPanel,
                     actions.Action]

            # avoid base-classes
            if item in bases:
                continue

            # ignore imported classes - e.g. a module
            # might import an existing plugin like so,
            # for the sake of being sub-classed - in
            # this case, we only want to consider
            # MyView:
            #     from blah import SomeView:
            #     class MyView(SomeView):
            #         ..
            if ptype in ('view', 'control', 'tool'):
                if item.__module__ != mod.__name__:
                    continue

                # ignoreControl/ignoreTool may be overridden
                # to tell us to ignore this plugin
                if ptype == 'control'               and \
                   'ignoreControl' in item.__dict__ and \
                   item.ignoreControl():
                    continue
                if ptype == 'tool'               and \
                   'ignoreTool' in item.__dict__ and \
                   item.ignoreTool():
                    continue

            group = _pluginGroup(item)
            if group is not None:
                log.debug('Found %s entry point: %s', group, name)
                entryPoints[f'fsleyes_{group}'][name] = item

        return entryPoints


class FSLeyesPluginFinder(importlib.abc.MetaPathFinder):
    """Custom ``MetaPathFinder`` for single-file FSLeyes plugins.
    """

    @staticmethod
    def instance() -> 'FSLeyesPluginFinder':
        """Return a singleton ``FSLeyesPluginFinder`` instance. """

        instance = getattr(FSLeyesPluginFinder, '_instance', None)
        if instance is None:
            instance                      = FSLeyesPluginFinder()
            FSLeyesPluginFinder._instance = instance
            sys.meta_path.append(instance)
        return instance


    def __init__(self):
        """Don't create a ``FSLeyesPluginFinder``. Instead, access the
        singleton instance via the :meth:`instance` method.
        """
        self.__plugins = {}


    def add_plugin(self, module : ModuleType, modname : str):
        """Register a FSLeyes plugin module.

        :arg module:  The loaded module
        :arg modname: The module name
        """
        self.__plugins[modname] = FSLeyesPlugin(module, modname)


    def find_distributions(self, context=None):
        """Returns all registered :class:`FSLeyesPlugin` distributions. """
        return iter(self.__plugins.values())


    def find_spec(self, fullname, path, target=None):
        """May be called by importlib when attempting to import a module.
        Returns ``None``.
        """
        return None


def initialise():
    """Loads all plugins, including built-ins, plugin files in the FSLeyes
    settings directory, and those found on the ``FSLEYES_PLUGIN_PATH``
    environment variable.
    """

    _loadBuiltIns()

    # plugins in fsleyes settings dir
    pluginFiles = list(fslsettings.listFiles('plugins/*.py'))
    pluginFiles = [fslsettings.filePath(p) for p in pluginFiles]

    # plugins on path
    fpp = os.environ.get('FSLEYES_PLUGIN_PATH', None)
    if fpp is not None:
        for dirname in fpp.split(op.pathsep):
            pluginFiles.extend(glob.glob(op.join(dirname, '*.py')))

    for fname in pluginFiles:
        try:
            loadPlugin(fname)
        except Exception as e:
            log.warning('Failed to load plugin file %s: %s', fname, e)


def _pluginType(item) -> Union[str, bool]:
    """Return the plugin type of the given object - one of ``'view'``,
    ``'control'``, ``'tool'`` or ``'layout'``.
    """

    if isinstance(item, type):
        if   issubclass(item, ctrlpanel.ControlMixin): return 'control'
        elif issubclass(item, viewpanel.ViewPanel):    return 'view'
        elif issubclass(item, actions.Action):         return 'tool'
    elif isinstance(item, (str, tuple)):               return 'layout'

    return False


def _pluginGroup(plg : Plugin) -> Optional[str]:
    """Returns the type/group of the given plugin, one of ``'views'``,
    ``'controls'``, ``'tools'``, or ``'layouts'``.
    """
    ptype = _pluginType(plg)
    if   ptype == 'view':    return 'views'
    elif ptype == 'control': return 'controls'
    elif ptype == 'tool':    return 'tools'
    elif ptype == 'layout':  return 'layouts'
    return None


def _loadBuiltIns():
    """Called by :func:`initialise`. Loads all bulit-in plugins, from
    sub-modules of the ``fsleyes.plugins`` directory.
    """

    import fsleyes.plugins.views    as views
    import fsleyes.controls         as controls
    import fsleyes.plugins.controls as pcontrols
    import fsleyes.plugins.tools    as tools

    def load_all_submodules(mod):
        submods = pkgutil.iter_modules(mod.__path__, mod.__name__ + '.')
        for _, name, ispkg in submods:
            log.debug('Loading built-in plugin module %s', name)
            submod = importlib.import_module(name)
            FSLeyesPluginFinder.instance().add_plugin(submod, submod.__name__)
            if ispkg:
                load_all_submodules(submod)

    for mod in (views, controls, pcontrols, tools):
        load_all_submodules(mod)


def _listEntryPoints(
        group   : str,
        showAll : bool = False,
        load    : bool = True
) -> Dict[str, Plugin]:
    """Returns a dictionary containing ``{name : object}`` entry points for the
    given entry point group.

    https://docs.python.org/3/library/importlib.metadata.html#entry-points

    :arg group:   One of ``'fsleyes_views'``, ``'fsleyes_controls``,
                  ``'fsleyes_tools'``, or ``'fsleyes_layouts'``.

    :arg showAll: If ``True``, all plugins, including from installed
                  third-party packages will be included. Otherwise (the
                  default) plugins from third-party packages which are not in
                  :attr:`SHOW_THIRD_PARTY_PLUGINS` will be omitted.  :arg
                  load:

    :arg load:    If ``True`` (the default), the returned dictionary will
                  contain loaded entry point objects. If ``False``, the entry
                  points will not be loaded, and the returned dictionary will
                  instead contain ``importlib.metadata.EntryPoint`` objects.
    """

    items = {}
    eps   = impmeta.entry_points()

    # Python >=3.10 returns an EntryPoints
    # object, older versions return a dict.
    try:              eps = eps.select(group=group)
    except Exception: eps = eps.get(group, [])

    for ep in eps:
        # filter out third-party plugins by module path
        if not (showAll or ep.value.startswith('fsleyes.')):
            if not shouldShowThirdPartyPlugin(ep.value.split(':')[0]):
                log.debug('Filtering third party plugin: %s', ep.value)
                continue
        if ep.name in items:
            log.debug('Overriding entry point %s [%s] with entry point of '
                      'the same name from %s', ep.name, group, ep.value)

        try:
            if load: items[ep.name] = ep.load()
            else:    items[ep.name] = ep
        except Exception as e:
            log.warning('Could not load FSLeyes entry point %s ("%s"): %s',
                        ep.value, ep.name, e)
            continue

    return items


def listViews() -> Dict[str, View]:
    """Returns a dictionary of ``{name : ViewPanel}`` mappings containing
    the custom views provided by all installed FSLeyes plugins.
    """
    views = _listEntryPoints('fsleyes_views')
    for name, cls in list(views.items()):
        if not issubclass(cls, viewpanel.ViewPanel):
            log.debug('Ignoring fsleyes_views entry point '
                      '%s - not a ViewPanel', name)
            views.pop(name)
            continue
    return views


def listControls(viewType : Optional[View] = None) -> Dict[str, Control]:
    """Returns a dictionary of ``{name : ControlPanel}`` mappings containing
    the custom controls provided by all installed FSLeyes plugins.

    :arg viewType: Sub-class of :class:`.ViewPanel` - if provided, only
                   controls which are compatible with this view type are
                   returned (as determined by
                   :meth:`.ControlMixin.supportedViews.`).
    """
    ctrls = _listEntryPoints('fsleyes_controls')

    for name, cls in list(ctrls.items()):

        if not issubclass(cls, (ctrlpanel.ControlPanel,
                                ctrlpanel.ControlToolBar)):
            log.debug('Ignoring fsleyes_controls entry point %s - '
                      'not a ControlPanel/ToolBar', name)
            ctrls.pop(name)
            continue

        # views that this control supports - might be None,
        # in which case the control is assumed to support
        # all views.
        supported = cls.supportedViews()

        # does the control support sub-classes of the
        # views that it supports, or only the specific
        # view classes returned by supportedViews?
        subclassok = True
        if 'supportSubClasses' in cls.__dict__:
            subclassok = cls.supportSubClasses()

        if viewType  is not None and \
           supported is not None:
            if subclassok:
                if not issubclass(viewType, tuple(supported)):
                    ctrls.pop(name)
            elif viewType not in supported:
                ctrls.pop(name)
    return ctrls


def listTools(viewType : Optional[View] = None) -> Dict[str, Tool]:
    """Returns a dictionary of ``{name : Action}`` mappings containing
    the custom tools provided by all installed FSLeyes plugins.

    :arg viewType: Sub-class of :class:`.ViewPanel` - if provided, only
                   tools which are compatible with this view type are
                   returned (as determined by
                   :meth:`.Action.supportedViews.`).
    """
    tools = _listEntryPoints('fsleyes_tools')
    for name, cls in list(tools.items()):

        if not issubclass(cls, actions.Action):
            log.debug('Ignoring fsleyes_tools entry point '
                      '%s - not an Action', name)
            tools.pop(name)
            continue

        if viewType is not None:

            supported = cls.supportedViews()
            # If a viewType is provided, we don't
            # return view-independent views
            if (supported is None) or \
               (not issubclass(viewType, tuple(supported))):
                tools.pop(name)

    return tools


def listLayouts() -> Dict[str, Layout]:
    """Returns a dictionary of ``{name : str}`` mappings containing
    the custom layouts provided by all installed FSLeyes plugins.
    """

    layouts = _listEntryPoints('fsleyes_layouts', showAll=True)

    for name, layout in list(layouts.items()):

        if not isinstance(layout, (str, tuple)):
            log.debug('Ignoring fsleyes_layouts entry point '
                      '%s - not a string or tuple', name)
            layouts.pop(name)
            continue

        # layout plugins may be either layout strings,
        # or tuples containing (name, layout string)
        if isinstance(layout, tuple):
            layouts[name] = layout[1]

    return layouts


def _lookupPlugin(plgname : str, group : str) -> Optional[Plugin]:
    """Looks up the FSLeyes plugin with the given name. """
    entries = _listEntryPoints(f'fsleyes_{group}', True)
    for name, plugin in entries.items():
        if isinstance(plugin, (str, tuple)):
            if isinstance(plugin, tuple):
                if plugin[0] == plgname:
                    return plugin[1]
            elif name == plgname:
                return plugin
        elif plugin.__name__ == plgname:
            return plugin
    return None


def lookupControl(clsName : str) -> Control:
    """Looks up the FSLeyes control with the given class name. """
    return _lookupPlugin(clsName, 'controls')


def lookupTool(clsName : str) -> Tool:
    """Looks up the FSLeyes tool with the given class name. """
    return _lookupPlugin(clsName, 'tools')


def layoutModule(name : str) -> str:
    """Return the module that a given layout is defined iwthin. """
    layouts = _listEntryPoints('fsleyes_layouts', showAll=True, load=False)

    for ep in layouts.values():
        if ep.name == name:
            return ep.value.split(':')[0].split('.')[0]

    raise ValueError(f'Could not find layout with name {name}')


def pluginTitle(plugin : Plugin) -> Optional[str]:
    """Looks and returns up the title under which the given ``plugin`` is
    registered.
    """
    group   = _pluginGroup(plugin)
    entries = _listEntryPoints(f'fsleyes_{group}', True)
    for title, cls in entries.items():
        if cls is plugin:
            return title


def loadPlugin(filename : str):
    """Loads the given Python file as a FSLeyes plugin. """

    # Generate a unique module name for each file
    def genModuleName():
        salt    = ''.join(random.choices(string.ascii_letters, k=10))

        # We locate single-file modules within the
        # fsleyes.plugins package, so that the
        # _listEntryPoints function can filter them.
        modname = op.splitext(op.basename(filename))[0].strip('_')
        modname = f'fsleyes.plugins.{modname}_{salt}'
        return modname

    modname = genModuleName()
    while modname in sys.modules:
        modname = genModuleName()

    log.debug('Importing %s as %s', filename, modname)

    spec   = imputil.spec_from_file_location(modname, filename)
    module = imputil.module_from_spec(spec)
    spec.loader.exec_module(module)

    sys.modules[modname] = module

    FSLeyesPluginFinder.instance().add_plugin(module, modname)


def installPlugin(filename : str):
    """Copies the given Python file into the FSLeyes settings directory,
    within a sub-directory called ``plugins``. After the file has been
    copied, the path to the copy is passed to :func:`loadPlugin`.
    """

    basename = op.splitext(op.basename(filename))[0]
    dest     = f'plugins/{basename}.py'

    log.debug('Installing plugin %s', filename)

    with open(filename, 'rt')        as inf, \
         fslsettings.writeFile(dest) as outf:
        outf.write(inf.read())

    dest = fslsettings.filePath(dest)

    try:
        loadPlugin(dest)
    except Exception:
        fslsettings.deleteFile(dest)
        raise
