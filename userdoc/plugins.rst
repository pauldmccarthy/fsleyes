.. |right_arrow| unicode:: U+21D2


.. _fsleyes_plugins:

FSLeyes plugins
===============


FSLeyes |version| has a simple plugin architecture, allowing you to write and
install custom views, controls, tools, and layouts.


For users
---------

FSLeyes plugins come in two forms:

 - Python libraries (e.g. as hosted on `PyPi - the Python Package Index
   <https://pypi.org/>`_)
 - Standalone Python ``.py`` files


``.py`` plugin files
^^^^^^^^^^^^^^^^^^^^


If you wish to use a FSLeyes plugin which comes as a ``.py`` file, you can
simply use the *File* |right_arrow| *Load plugin* menu item. The panels and
tools that the plugin provides will be made available in the *View*,
*Settings* and *Tools* menus.


Plugin libraries
^^^^^^^^^^^^^^^^


If you wish to use FSLeyes plugin which has been published on PyPi, you will
need to install the plugin into the Python environment that FSLeyes is running
in. You may wish to ask your local system adminsistrator or Python expert to
help you with this.


For developers
--------------


.. note:: The FSLeyes API documentation can be found at |fsleyes_apidoc_url|


For both types of plugin (Python libraries and ``.py`` files), FSLeyes uses
Python `entry points
<https://packaging.python.org/specifications/entry-points/>`__ to
locate the items provided by plugin libraries/files.


Things plugins can provide
^^^^^^^^^^^^^^^^^^^^^^^^^^


FSLeyes plugins can provide custom *views*, *controls*, *tools*, and *layouts*:

 - A *view* is a top level panel, such as an
   :class:`~fsleyes.views.orthopanel.OrthoPanel`,
   :class:`~fsleyes.views.scene3dpanel.Scene3DPanel`, or
   :class:`~fsleyes.views.timeseriespanel.TimeSeriesPanel`. Views provided by
   plugins are added to the top level *Views* menu.

 - A *control* is a secondary panel, or toolbar, which is embedded within a
   view, such as an
   :class:`~fsleyes.controls.overlaylistpanel.OverlayListPanel`,
   :class:`~fsleyes.controls.orthotoolbar.OrthoToolBar`, or
   :class:`~fsleyes.plugins.controls.melodicclassificationpanel.melodicclassificationpanel.MelodicClassificationPanel`. Controls
   provided by plugins are added to the *Settings* menu for each active view.

 - A *tool* is an :class:`~fsleyes.actions.base.Action` which is associated
   with a menu item under the top-level *Tools* menu, such as the
   :class:`~fsleyes.plugins.tools.applyflirtxfm.ApplyFlirtXfmAction` and the
   :class:`~fsleyes.plugins.tools.resample.ResampleAction`.

 - A *layout* is a string which specifies the layout of the FSLeyes frame,
   comprising one or more view panels, and a set of control panels for each
   view. Refer to the page on :ref:`customising FSLeyes
   <customising_layouts>`, and the :mod:`fsleyes.layouts` module for more
   details.


FSLeyes plugin sources
^^^^^^^^^^^^^^^^^^^^^^

FSLeyes plugins can be loaded from the following locations:

 - Built-in plugins from the :mod:`fsleyes.plugins` package.
 - Single-file plugins that have been loaded/installed by the user.
 - Plugins from third-party libraries that have been installed into the
   running Python environment.

The default behaviour, when FSLeyes starts up, is to only expose plugins from
the first two locations - plugins from third party libraries are hidden by
default. However, third-party plugins are automatically made available when a
layout from the same library is loaded.

Third-party plugins can also be made visible by default if you start FSLeyes
with the ``--showAllPlugins`` command-line option. You can permanently apply
this option by adding it to your :ref:`default command-line arguments
<command_line_default_arguments>`.


Loading/installing FSLeyes plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


FSLeyes plugins are loaded into a running FSLeyes as follows:

 - Any Python libraries (e.g. installed from ``PyPi``) which are present the
   environment that FSLeyes is running in, and which provide any FSLeyes entry
   points, will automatically be detected by FSLeyes.

 - Plugin ``.py`` files can be loaded via the *File* |right_arrow| *Load
   plugin* menu item.

 - Plugin ``.py`` files which are present in the FSLeyes settings directory,
   or which are found in the ``FSLEYES_PLUGIN_PATH`` environment variable, will
   be loaded when FSLeyes starts.


A plugin can be installed permanently into FSLeyes as follows:

 - Any Python libraries (e.g. installed from ``PyPi``) which are present the
   environment that FSLeyes is running in, and which provide any FSLeyes entry
   points, will automatically be detected by FSLeyes.

 - When you load a plugin ``.py`` file via the *File* |right_arrow| *Load
   plugin* menu item, FSLeyes will ask you if you would like to install the
   plugin permanently. If you choose *Yes*, the plugin file will be saved into
   the FSLeyes settings directory (e.g. ``~/.fsleyes/plugins/`` on macOS).


Writing a FSLeyes plugin
^^^^^^^^^^^^^^^^^^^^^^^^


.. note:: A minimal example of a FSLeyes plugin library can be found in the
          |fsleyes_repository|_, in the
          ``fsleyes/tests/testdata/fsleyes_plugin_example/`` directory, and a
          range of built-in plugins can be found in ``fsleyes/plugins/``.


.. warning:: FSLeyes assumes that all views, controls, tools, and layouts have
             unique class names.  So expect problems if, for example, you
             define your own FSLeyes control with the name
             :class:`~fsleyes.controls.overlaylistpanel.OverlayListPanel`.


A FSLeyes plugin is a Python library, or a ``.py`` file, which contains
definitions for custom views, controls, tools, and layouts.

 - Views must be sub-classes of the :class:`.ViewPanel` class.

 - Controls must be sub-classes of the :class:`.ControlPanel` or
   :class:`.ControlToolBar` classes.

 - Tools must be sub-classes of the :class:`.Action` class.

 - Layouts must be strings conforming to the FSLeyes layout specification (see
   the :mod:`fsleyes.layouts` module).


To write a ``.py`` file which can be loaded as a FSLeyes plugin, simply define
your views, controls, and tools as Python classes in the file, and define
layouts as module-level string values with a name beginning with
``FSLEYES_LAYOUT_``. The file path can then be loaded via the *File*
|right_arrow| *Load plugin* menu item.


To release a FSLeyes plugin as a library, you need to organise your code
as a Python library. Minimally, this requires the following:

 - Arrange your ``.py`` file(s) into a Python package.

 - Expose your custom views, controls, tools, and layouts as `entry points
   <https://packaging.python.org/specifications/entry-points/>`__.


A minimal ``pyproject.toml`` file for a FSLeyes plugin might look like this:


.. sidebar:: FSLeyes plugin library naming conventions

             Versions of FSLeyes older than 1.8.0 will only recognise plugin
             libraries with a name beginning with ``fsleyes-plugin-``. As of
             FSLeyes 1.8.0, this restriction no longer exists - you can
             give your library any name you wish. All you need to do is expose
             the relevant entry points.

::

    [build-system]
    requires      = ["setuptools"]
    build-backend = "setuptools.build_meta"

    [project]
    name    = "my-cool-fsleyes-plugin"
    version = "1.0.0"

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

    [project.entry-points.fsleyes_layouts]
    "My cool layout" = "myplugin.MyLayout"


See the `Python Packaging guide
<https://packaging.python.org/tutorials/packaging-projects/>`_ for more
details on packaging Python libraries.


Customising control panels
^^^^^^^^^^^^^^^^^^^^^^^^^^


If you are writing a custom control panel which is designed to only work with
a specific view (e.g. an ortho view), you can override the
:mod:`.ControlMixin.supportedViews` static method to limit the views that your
control supports.


Furthermore, if you want to customise how your custom control is displayed
(e.g. on the bottom, left, right, or top, or as a separate floating panel),
you can override the :mod:`.ControlMixin.defaultLayout` static method to
return default layout options that will be passed to the
:meth:`.ViewPanel.togglePanel` method when your control panel is opened.


If you would like to add custom mouse/keyboard interaction in conjunction with
your control panel, you can do so by writing a custom :class:`.Profile` class,
and overriding the :class:`.ControlMixin.profileCls` method. See the
:class:`.CropImageAction` and :class:`.AnnotationPanel` for examples of
custom interaction profiles.
