.. |right_arrow| unicode:: U+21D2


.. _fsleyes_notebook:

FSLeyes and Jupyter Notebook
============================


FSLeyes is written primarily in the `Python <https://www.python.org>`_
programming language.  Much of the internal state of FSLeyes can be queried
and modified through a programming interface, which may be accessed through a
Jupyter Notebook. You can start a Jupyter Notebook server which may be used to
interact with FSLeyes via the *File* |right_arrow| *Open notebooks* menu item.

.. image:: images/fsleyes_notebook.png
   :width: 50%
   :align: center


FSLeyes also has an integrated Python shell which offers the same programming
interface. This can be accessed via the *Views* |right_arrow| *Python shell*
menu item

.. image:: images/python_shell.png
   :width: 50%
   :align: center


This page contains a very brief overview of the FSLeyes programming
interface. Refer to the :ref:`links below <fsleyes_api_further_reading>` for
more comprehensive documentation.


.. [*] See also the ``--runscript`` :ref:`command line option
       <command_line_run_script>`.


.. warning:: The FSLeyes programming API is subject to change without warning!


Help
----

Use the built-in ``help`` function to get help on anything in the
notebook/shell environment, whether it is a module, function, class, or
object::

  >>> help(load)
  Help on function load in module fsleyes.actions.runscript:

  load(filename)
      Load the specified file into FSLeyes.


Overlays
--------


The ``overlayList`` is a list which contains all of the overlays that have
been loaded into FSLeyes::


  >>> overlayList
  >>> [Image(MNI152_T1_1mm, /.../MNI152_T1_1mm.nii.gz),
       Image(MNI152_T1_2mm, /.../MNI152_T1_2mm.nii.gz)]


You can load overlays into FSLeyes simply by inserting them into this
list. Or, you can use the built-in ``load`` function::

  >>> load('path/to/my_image.nii.gz')


You can remove an overlay in the same way that you would remove an item from a
python ``list``::

  >>> del overlayList[0]
  >>> overlayList
  >>> [Image(MNI152_T1_2mm, /.../MNI152_T1_2mm.nii.gz)]


.. note:: As an alternative to the ``load`` function, ytou can also manually
          create overlays, and then add them to the ``overlayList``. For
          example::

              image = Image('path/to/my_image.nii.gz')
              overlayList.append(image)


FSL tools
---------


If you have FSL installed, you can call some FSL tools [*]_ through Python
functions, e.g.::

  >>> struc = load('/path/to/my/T1.nii.gz')
  >>> bet(struc, LOAD)

The special ``LOAD`` symbol will cause the result to be loaded into FSLeyes.

.. [*] The FSL wrapper functions are provided by the |fslpy_doc| library -
       check out the ``fsl.wrappers`` package documentation to see what is
       available.


Display settings
----------------


You can use the ``displayCtx`` to access the display settings for an
overlay. Display settings for an overlay are divided between two objects:

 - A ``Display`` object, which contains general display settings
 - A ``DisplayOpts`` object, which contains display settings specific to the
   overlay type


You can access these objects like so::

  >>> overlay = overlayList[0]
  >>> display = displayCtx.getDisplay(overlay)
  >>> opts    = displayCtx.getOpts(   overlay)


Adjusting the overlay display settings is easy::

  >>> display.brightness = 75
  >>> opts.cmap          = 'hot'


You can get help on the ``Display`` and ``DisplayOpts`` instances via the
``help`` function::

  >>> help(display)
  Help on Display in module fsleyes.displaycontext.display object:

  class Display(props.syncable.SyncableHasProperties)
   |  The ``Display`` class contains display settings which are common to
   |  all overlay types.
   |
   |  A ``Display`` instance is also responsible for managing a single
   |  :class:`DisplayOpts` instance, which contains overlay type specific
   |  display options. Whenever the :attr:`overlayType` property of a
   |  ``Display`` instance changes, the old ``DisplayOpts`` instance (if any)
   |  is destroyed, and a new one, of the correct type, created.
  .
  .
  .


FSLeyes interface
-----------------

You can programmatically modify the FSLeyes interface and layout through the
notebook/shell. The FSLeyes interface is contained within a single object, the
``FSLeyesFrame``. This is available in the environment as the ``frame``.


You can add and remove :ref:`views <overview_views_and_controls>` to and from
the ``frame``::

  >>> frame.addViewPanel(views.OrthoPanel)
  >>> frame.viewPanels
  [<fsleyes.views.shellpanel.ShellPanel; proxy of <Swig Object of type 'wxPyPanel *' at 0x11b4b4c90> >,
   <fsleyes.views.orthopanel.OrthoPanel; proxy of <Swig Object of type 'wxPyPanel *' at 0x11593dba0> >]

  >>> ortho = frame.viewPanels[1]
  >>> frame.removeViewPanel(ortho)


You can also access the view settings for a specific view::

  >>> frame.addViewPanel(views.OrthoPanel)
  >>> frame.viewPanels
  [<fsleyes.views.shellpanel.ShellPanel; proxy of <Swig Object of type 'wxPyPanel *' at 0x11b4b4c90> >,
   <fsleyes.views.orthopanel.OrthoPanel; proxy of <Swig Object of type 'wxPyPanel *' at 0x11593dba0> >]

  >>> ortho                = frame.viewPanels[1]
  >>> orthoOpts            = ortho.getSceneOptions()
  >>> orthoOpts.layout     = 'grid'
  >>> orthoOpts.showLabels = False


.. _fsleyes_api_further_reading:

Further reading
---------------


For more information on the FSLeyes programming interface, refer to:

- |fsleyes_apidoc|_ developer documentation
- |fslpy_doc|_ developer documentation
- |props_doc|_ developer documentation
- |widgets_doc|_ developer documentation
