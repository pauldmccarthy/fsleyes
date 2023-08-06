#!/usr/bin/env python
#
# __init__.py - Accessing installed FSLeyes plugins.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package provides access to installed and built-in FSLeyes plugins.


FSLeyes uses a simple plugin architecture for loading custom views, controls,
and tools. Plugins can be installed from Python libraries (e.g. as hosted on
`PyPi <https://pypi.org/>`_), or installed directly from a ``.py`` file.


In both cases, FSLeyes uses `entry points
<https://packaging.python.org/specifications/entry-points/>`__
to locate the items provided by plugin library/files.


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

 - A *tool* is an :class:`.Action` which is associated with a menu item under
   the top-level *Tools* menu, such as the :class:`.ApplyFlirtXfmAction`, the
   :class:`.CropImageAction`, and the :class:`.ResampleAction`.


Loading/installing FSLeyes plugins
----------------------------------


FSLeyes plugins are loaded into a running FSLeyes as follows:

 - Any Python libraries (e.g. installed from ``PyPi``) which are present the
   environment that FSLeyes is running in, and which provide any FSLeyes entry
   points, will automatically be detected by FSLeyes.

 - Plugin ``.py`` files, which contain view, control, and/or tool definitions,
   can be passed directly to the :func:`loadPlugin` function.

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


.. warning:: FSLeyes assumes that all views, controls, and tools have unique
             class names.  So expect problems if, for example, you define your
             own FSLeyes control with the name ``OverlayListPanel``.


A FSLeyes plugin is a Python library, or a ``.py`` file, which contains
definitions for custom views, controls, and tools.

 - Views must be sub-classes of the :class:`.ViewPanel` class.

 - Controls must be sub-classes of the :class:`.ControlPanel` or
   :class:`.ControlToolBar` classes.

 - Tools must be sub-classes of the :class:`.Action` class.


To write a ``.py`` file which can be loaded as a FSLeyes plugin, simply
define your views, controls, and tools in the file. The file path can then
be passed to the :func:`loadPlugin` or :func:`installPlugin` function.


To release a FSLeyes plugin as a library, you need to organise your code
as a Python library. Minimally, this requires the following:

 - Arrange your ``.py`` file(s) into a Python package.

 - Expose your custom views, controls, and tools as `entry points
   <https://packaging.python.org/specifications/entry-points/>`_.


A minimal ``pyproject.toml`` file for a FSLeyes plugin might look like this::

    [build-system]
    requires      = ["setuptools"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "my-cool-fsleyes-plugin"

    # Views, controls, and tools must be exposed
    # as entry points within groups called
    # "fsleyes_views", "fsleyes_controls" and
    # "fsleyes_tools" respectively.

    [project.entry-points.fsleyes_views]
    "My cool view" = "myplugin:MyView"

    [project.entry-points.fsleyes_controls]
    "My cool control" = "myplugin:MyControl"

    [project.entry-points.fsleyes_tools]
    "My cool tool" = "myplugin.MyTool"


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
   lookupView
   lookupControl
   lookupTool
   pluginTitle
"""


import os.path             as op
import                        os
import                        sys
import                        glob
import                        pkgutil
import                        logging
import                        importlib
import importlib.util      as imputil
import importlib.metadata  as impmeta
import                        collections

from typing import Dict, Union, Type, Optional, Iterator
from types  import ModuleType

import fsl.utils.settings            as fslsettings
import fsleyes.actions               as actions
import fsleyes.strings               as strings
import fsleyes.views.viewpanel       as viewpanel
import fsleyes.views.canvaspanel     as canvaspanel
import fsleyes.controls.controlpanel as ctrlpanel


log = logging.getLogger(__name__)

View    = Type[viewpanel.ViewPanel]
Control = Type[ctrlpanel.ControlPanel]
Tool    = Type[actions.Action]
Plugin  = Union[View, Control, Tool]


def class_defines_method(cls : Type, methname : str) -> bool:
    """Check to see whether ``methname`` is implemented on ``cls``, and not
    on a base-class.

    :meth:`.Action.ignoreTool`, :meth:`.ControlMixin.ignoreControl`, and
    :meth:`.ControlMixin.supportSubClasses` need to be implemented on the
    specific class - inherited base class implementations are not considered.
    """
    return methname in cls.__dict__


class FSLeyesPlugin(impmeta.Distribution):
    """Custom ``importlib.metadata.Distribution`` used to represent FSLeyes
    plugins that are loaded from a single file.

    A ``FSLeyesPlugin`` is created for each single-file FSLeyes plugin that
    is registered with the :meth:`FSLeyesPluginFinder.add_plugin` method.
    """

    def __init__(self,
                 module  : ModuleType,
                 modname : str,
                 builtin : bool):
        """Create a ``FSLeyesPlugin`` from a single-file plugin file that
        has already been loaded as a module.

        :arg module:  The loaded module
        :arg modname: The module name
        :arg builtin: Whether or not this is a built-in FSLeyes plugin, from
                      the :mod:`fsleyes.plugins` module.
        """
        self.__module  = module
        self.__modname = modname
        self.__builtin = builtin


    @property
    def version(self) -> str:
        return '0.0.0'


    @property
    def name(self) -> str:
        return self.__modname


    @property
    def entry_points(self) -> Iterator[impmeta.EntryPoint]:
        """Return a sequence of ``EntryPoint`` objects provided by the plugin.  The
        :meth:`FSLeyesPlugin.find_entry_points` function is used to scan the
        module for entry points.
        """

        modname = self.__modname
        alleps  = FSLeyesPlugin.find_entry_points(
            self.__module, not self.__builtin)

        for group, eps in alleps.items():
            for name, cls in eps.items():

                label = cls.title()
                # Look up label for built-in plugins
                if label is None:
                    if group == 'fsleyes_tools':
                        label = strings.actions.get(name, name)
                    else:
                        label = strings.titles.get(name, name)

                yield impmeta.EntryPoint(label,
                                         f'{modname}:{name}',
                                         group=group)


    @staticmethod
    def find_entry_points(
            mod            : ModuleType,
            ignoreBuiltins : bool
    ) -> Dict[str, Dict[str, Plugin]]:
        """Finds the FSLeyes entry points (views,
        controls, or tools) that are defined within the given module.

        :arg mod:            The module to search
        :arg ignoreBuiltins: If ``True``, all, views, controls and tools which
                             are built into FSLeyes will be ignored. The
                             :class:`.ViewPanel`, :class:`.ControlPanel`,
                             :class:`.ControlToolBar` and :class:`.Action` base
                             classes are always ignored.

        :returns:            A dictionary
        """

        entryPoints = collections.defaultdict(dict)

        for name in dir(mod):

            item = getattr(mod, name)

            if not isinstance(item, type):
                continue

            bases = [viewpanel.ViewPanel,
                     canvaspanel.CanvasPanel,
                     ctrlpanel.ControlPanel,
                     ctrlpanel.ControlToolBar,
                     ctrlpanel.SettingsPanel,
                     actions.Action]

            # avoid base-classes and built-ins
            if item in bases:
                continue
            if ignoreBuiltins and str(item.__module__).startswith('fsleyes.'):
                continue

            # ignoreControl/ignoreTool may be overridden
            # to tell us to ignore this plugin
            if issubclass(item, ctrlpanel.ControlMixin)    and \
               class_defines_method(item, 'ignoreControl') and \
               item.ignoreControl():
                continue
            if issubclass(item, actions.Action)         and \
               class_defines_method(item, 'ignoreTool') and \
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
            instance = FSLeyesPluginFinder()
            sys.meta_path.append(instance)

        return instance


    def __init__(self):
        """Don't create a ``FSLeyesPluginFinder``. Instead, access the
        singleton instance via the :meth:`instance` method.
        """
        FSLeyesPluginFinder._instance = self
        self.__plugins = {}


    def add_plugin(self, module : ModuleType, modname : str, builtin : bool):
        """Register a FSLeyes plugin module.

        :arg module:  The loaded module
        :arg modname: The module name
        :arg builtin: Whether or not this is a built-in FSLeyes plugin, from
                      the :mod:`fsleyes.plugins` module.
        """
        self.__plugins[modname] = FSLeyesPlugin(module, modname, builtin)


    def find_distributions(self, context=None):
        """Returns all registered :class:`FSLeyesPlugin` distributions. """
        return self.__plugins.values()


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


def _pluginGroup(cls : Plugin) -> Optional[str]:
    """Returns the type/group of the given plugin, one of ``'views'``,
    ``'controls'``, or ``'tools'``.
    """
    if   issubclass(cls, viewpanel.ViewPanel):      return 'views'
    elif issubclass(cls, ctrlpanel.ControlPanel):   return 'controls'
    elif issubclass(cls, ctrlpanel.ControlToolBar): return 'controls'
    elif issubclass(cls, actions.Action):           return 'tools'
    return None


def _loadBuiltIns():
    """Called by :func:`initialise`. Loads all bulit-in plugins, from
    sub-modules of the ``fsleyes.plugins`` directory.
    """

    import fsleyes.plugins.views    as views
    import fsleyes.controls         as controls
    import fsleyes.plugins.controls as pcontrols
    import fsleyes.plugins.tools    as tools

    for mod in (views, controls, pcontrols, tools):
        submods = pkgutil.iter_modules(mod.__path__, mod.__name__ + '.')
        for _, name, _ in submods:
            log.debug('Loading built-in plugin module %s', name)
            submod = importlib.import_module(name)
            FSLeyesPluginFinder.instance().add_plugin(
                submod, submod.__name__, True)


def _listEntryPoints(group : str) -> Dict[str, Plugin]:
    """Returns a dictionary containing ``{name : type}`` entry points for the
    given entry point group.

    https://docs.python.org/3/library/importlib.metadata.html#entry-points
    """
    items = collections.OrderedDict()

    eps = impmeta.entry_points()

    # Python >=3.10 returns an EntryPoints
    # object, older versions return a dict.
    try:              eps = eps.select(group=group)
    except Exception: eps = eps[group]

    for ep in eps:
        if ep.name in items:
            log.debug('Overriding entry point %s [%s] with entry '
                      'point of the same name from', ep.name, group)
        items[ep.name] = ep.load()
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
        if class_defines_method(cls, 'supportSubClasses'):
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

        supported = cls.supportedViews()

        if viewType is not None:
            # If a viewType is provided, we don't
            # return view-independent views
            if (supported is None) or \
               (not issubclass(viewType, tuple(supported))):
                tools.pop(name)

    return tools


def _lookupPlugin(clsname : str, group : str) -> Optional[Plugin]:
    """Looks up the FSLeyes plugin with the given class name. """
    entries = _listEntryPoints(f'fsleyes_{group}')
    for cls in entries.values():
        if cls.__name__ == clsname:
            return cls
    return None


def lookupView(clsName : str) -> View:
    """Looks up the FSLeyes view with the given class name. """
    return _lookupPlugin(clsName, 'views')


def lookupControl(clsName : str) -> Control:
    """Looks up the FSLeyes control with the given class name. """
    return _lookupPlugin(clsName, 'controls')


def lookupTool(clsName : str) -> Tool:
    """Looks up the FSLeyes tool with the given class name. """
    return _lookupPlugin(clsName, 'tools')


def pluginTitle(plugin : Plugin) -> Optional[str]:
    """Looks and returns up the title under which the given ``plugin`` is
    registered.
    """
    group   = _pluginGroup(plugin)
    entries = _listEntryPoints(f'fsleyes_{group}')
    for title, cls in entries.items():
        if cls is plugin:
            return title


def loadPlugin(filename : str):
    """Loads the given Python file as a FSLeyes plugin. """

    modname = op.splitext(op.basename(filename))[0].strip('_')
    modname = f'fsleyes_plugin_{modname}'

    log.debug('Importing %s as %s', filename, modname)

    spec   = imputil.spec_from_file_location(modname, filename)
    module = imputil.module_from_spec(spec)
    spec.loader.exec_module(module)

    sys.modules[modname] = module

    FSLeyesPluginFinder.instance().add_plugin(module, modname, False)


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
