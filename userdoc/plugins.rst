.. |right_arrow| unicode:: U+21D2


.. _fsleyes_plugins:

FSLeyes plugins
===============


FSLeyes |version| has a simple plugin architecture, allowing you to write and
install custom views, controls, and tools.


.. note:: The FSLeyes plugin architecture is new to FSLeyes 0.26.0 - as of the
          release of this version there are no FSLeyes plugins in existence,
          so don't bother searching for any just yet.


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
tools that the plugin provides will then be available in the *View*,
*Settings* and *Tools* menus.


Plugin libraries
^^^^^^^^^^^^^^^^


If you wish to use FSLeyes plugin which has been published on PyPi, you will
need to install the plugin into the Python environment that FSLeyes is running
in. You may wish to ask your local system adminsistrator or Python expert to
help you with this.



Finding plugins
^^^^^^^^^^^^^^^


Head to the `PyPi <https://pypi.org/>`_, and search for ``'fsleyes-plugin'``.


For developers
--------------


.. note:: The FSLeyes API documentation can be found at |fsleyes_apidoc_url|


For both types of plugin (Python libraries and ``.py`` files),, FSLeyes uses
``setuptools`` `entry points
<https://setuptools.readthedocs.io/en/latest/pkg_resources.html#entry-points>`__
to locate the items provided by plugin library/files.


Things plugins can provide
^^^^^^^^^^^^^^^^^^^^^^^^^^


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


Loading/installing FSLeyes plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


FSLeyes plugins are loaded into a running FSLeyes as follows:

 - Any Python libraries (e.g. installed from ``PyPi``) which are present the
   environment that FSLeyes is running in, and which have a name beginning
   with ``fsleyes-plugin-`` will automatically be detected by FSLeyes.

 - Plugin ``.py`` files, which contain view, control, and/or tool definitions,
   can be passed directly to the :func:`loadPlugin` function.

 - Plugin ``.py`` files which are present in the FSLeyes settings directory,
   or which are found in the ``FSLEYES_PLUGIN_PATH`` environment variable, will
   be loaded by the :func:`initialise` function.


A plugin can be installed permanently into FSLeyes as follows:


 - Any Python libraries (e.g. installed from ``PyPi``) which are present the
   environment that FSLeyes is running in, and which have a name beginning
   with ``fsleyes-plugin-`` will automatically be detected by FSLeyes.

 - ``.py`` plugin files can be passed to the :func:`installPlugin`
   function. This file will be saved into the FSLeyes settings directory
   (e.g. ``~/.fsleyes/plugins/``).


Writing a FSLeyes plugin
^^^^^^^^^^^^^^^^^^^^^^^^


.. note:: A minimal example of a FSLeyes plugin library can be found in
          ``tests/testdata/fsleyes_plugin_example/``.


A FSLeyes plugin is a Python library, or a ``.py`` file, which contains
definitions for custom views, controls, and tools.

 - Views must be sub-classes of the :class:`.ViewPanel` class.

 - Controls must be sub-classes of the :class:`.ControlPanel` class.

 - Tools must be sub-classes of the :class:`.Action` class.


.. sidebar:: Customising control panels

             If you are writing a custom control panel which is designed to
             only work with a specific view (e.g. an ortho view), you can
             override the :mod:`.ControlMixin.supportedViews` static method to
             limit the views that your control supports.

             Furthermore, if you want to customise how your custom control is
             displayed (e.g. on the bottom, left, right, or top, or as a
             separate floating panel), you can override the
             :mod:`.ControlMixin.defaultLayout` static method to return
             default layout options that will be passed to the
             :meth:`.ViewPanel.togglePanel` method when your control panel
             is opened.


To write a ``.py`` file which can be loaded as a FSLeyes plugin, simply
define your views, controls, and tools in the file. The file path can then
be passed to the :func:`loadPlugin` or :func:`installPlugin` function.


To release a FSLeyes plugin as a library, you need to organise your code
as a Python library. Minimally, this requires the following:

 - Arrange your ``.py`` file(s) into a Python package.

 - Write a ``setup.py`` file.

 - Give your library a name (the ``name`` argument to the ``setup``
   function) which begins with ``'fsleyes-plugin-``.

 - Expose your custom views, controls, and tools as `entry points
   <https://packaging.python.org/specifications/entry-points/>`__ (the
   ``entry_points`` argument to the ``setup`` function).

A minimal ``setup.py`` file for a FSLeyes plugin might look like this::

    import setuptools

    setup(
        # the name must begin with "fsleyes-plugin-"
        name='fsleyes-plugin-my-cool-plugin',

        # Views, controls, and tools must be exposed
        # as entry points within groups called
        # "fsleyes_views", "fsleyes_controls" and
        # "fsleyes_tools" respectively.
        entry_points={
            'fsleyes_views' : [
                'My cool view = myplugin:MyView'
            ]
            'fsleyes_controls' : [
                'My cool control = myplugin:MyControl'
            ]
            'fsleyes_tools' : [
                'My cool tool = myplugin:MyTool'
            ]
        }
    )

See the `Python Packaging guide
<https://packaging.python.org/tutorials/packaging-projects/>`_ for more
details on writing a ``setup.py`` file.
