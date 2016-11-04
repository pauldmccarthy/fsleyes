.. _command_line:

Command line interface
======================


FSLeyes has a comprehensive command line interface. Nearly everything that you
can control through the :ref:`overlay display panel
<overlays_overlay_display_panel>`, and the :ref:`view settings panel
<ortho_lightbox_views_view_settings>` for orthographic/lightbox views, can be
set via the command line.

  
.. _command_line_overview:
  
Overview
--------


The FSLeyes command line interface follows this pattern:

::

  fsleyes [options] file [displayOpts] file [displayOpts] ...

where:

- ``options`` refers to options which relate to FSLeyes layout, behaviour,
  orthographic/lightbox configuration, etc.
  
- ``displayOpts`` refers to a group of options which are applied to the
  ``file`` that preceeds the group.


.. _command_line_help:

Help
----


To get a brief overview of the FSLeyes command line interface, which just
displays basic options::

  fsleyes --help
  fsleyes  -h


To get help on the full FSLeyes command line interface (warning: it is quite
long!)::

  fsleyes --fullhelp
  fsleyes  -fh

  
To print the version of FSLeyes you are using::

  fsleyes --version
  fsleyes  -V


Useful command line options
---------------------------


What follows is a short list highlighting some of the things that you can do
with the FSLeyes command line interface. For full details, refer to the
:ref:`command line help <command_line_help>`.

- :ref:`Auto display <command_line_auto_display>`
- :ref:`Add standard <command_line_add_standard>`
- :ref:`Perspectives <command_line_perspectives>`
- :ref:`Neurological orientation <command_line_neurological_orientation>`
- :ref:`Force-load images <command_line_force_load_images>`
- :ref:`Run script <command_line_run_script>`


.. _command_line_auto_display:

Auto-display
^^^^^^^^^^^^

::

  fsleyes --autoDisplay files ...
  fsleyes  -ad          files ...

  
The ``--autoDisplay`` option tells FSLeyes to automatically configure certain
display properties when you load an overlay. For example, if you start FSLeyes
with ``--autoDisplay``, and then load some Z-statistic images from a
:ref:`FEAT analysis <feat_mode>`, FSLeyes will set a colour map and threshold
value on the images.


As another example, loading a :ref:`MELODIC analysis <ic_classification>` with
``--autoDisplay`` enabled will cause FSLeyes to load a background image, and
to configure positive and negative colour maps on the ``melodic_IC`` image.


.. _command_line_add_standard:

Add standard
^^^^^^^^^^^^

::
   
  fsleyes --standard    files ...
  fsleyes --standard1mm files ...
  fsleyes  -std         files ...
  fsleyes  -std1mm      files ...


The ``--standard`` and ``--standard1mm`` options respectively tell FSLeyes to
load 2mm and 1mm versions of the MNI152 template. These options only work if
your command line environment has been correctly configured to use FSL
(e.g. the ``$FSLDIR`` environment variable is set).


.. _command_line_perspectives:

Perspectives
^^^^^^^^^^^^

::

   fsleyes --scene feat     files ...
   fsleyes --scene melodic  files ...
   fsleyes --scene default  files ...
   fsleyes --scene ortho    files ...
   fsleyes --scene ligthbox files ...
   fsleyes  -s     feat     files ...
   fsleyes  -s     melodic  files ...
   fsleyes  -s     default  files ...
   fsleyes  -s     ortho    files ...
   fsleyes  -s     ligthbox files ...
   

The ``--scene`` option allows you to tell FSLeyes to start up with a specific
:ref:`perspective <overview_layout_and_perspectives>`. If you have saved your
own custom perspective, you can also load it, by name, using the ``--scene``
option.


.. _command_line_neurological_orientation:

Neurological orientation
^^^^^^^^^^^^^^^^^^^^^^^^

::

   fsleyes --neuroOrientation files ...
   fsleyes  -no               files ...


By default, FSLeyes displays images in radiological orientation (i.e. with
subject right to the left of the display, and subject left to the right). You
can use the ``--neuroOrientation`` option to tell FSLeyes to use neurological
orientation instead.


.. _command_line_force_load_images:

Force-load images
^^^^^^^^^^^^^^^^^

::

   fsleyes --bigmem files ...
   fsleyes  -b      files ...


By default, FSLeyes keeps large compressed NIFTI files on disk, only
decompressing and loading data on-demand (i.e. when it needs to be viewed).
While this reduces the amount of RAM needed to view such images, it also slows
down the performance of changing volumes (e.g. via :ref:`movie mode
<ortho_lightbox_views_view_settings_movie_mode>`) and of viewing :ref:`time
series <plot_views_time_series_view>`.

If you are using a computer with a large amount of RAM, and you don't mind
loading the entire image into memory, you can use the ``--bigmem`` argument to
tell FSLeyes to do just that.


.. _command_line_run_script:

Run script
^^^^^^^^^^

::

   fsleyes --runscript script.py files ...
   fsleyes  -r         script.py files ...


FSLeyes has a programming API with which you can set up complex scenes. The
``--runscript`` option allows you to execute a script when FSLeyes starts.
These scripts have access to the same environment that is available in the
:ref:`Python shell <python_shell>`.

   
.. _command_line_offscreen_rendering:

Off-screen rendering
--------------------


FSLeyes is capable of generating screenshots from the command line. This is
useful, for example, if you need to generate a large number of PNG images for
quality control purposes. Simply build a FSLeyes command line which generates
the scene that you wish to view, and then tell FSLeyes to render the scene to
a file. FSLeyes should also work on systems which do not have a display
(e.g. cluster nodes), although in these environments FSLeyes assumes that
`MESA <http://mesa3d.org/>`_ is installed.


You can access the FSLeyes off-screen renderer by passing the word ``render``
as the **first** argument to FSLeyes::

  fsleyes render ...


You can access command line help in the same manner as :ref:`described above
<command_line_help>`::

  fsleyes render --help
  fsleyes render  -h
  fsleyes render --fullhelp
  fsleyes render  -fh 

  
Using the off-screen renderer is nearly identical to using the :ref:`standard
FSLeyes command line interface <command_line_overview>`, but you must also
specify an output file::

  fsleyes render [options] --outfile outfile file [displayOpts] ...
  fsleyes render [options]  -of      outfile file [displayOpts] ... 


You may also specify the size of the generated image, in pixels::

  fsleyes render [options] --outfile outfile --size 800 600 file [displayOpts] ...
  fsleyes render [options]  -of      outfile  -sz   800 600 file [displayOpts] ... 
  

When using the off-screen renderer, the ``--scene`` option, normally used to
:ref:`specify a perspective <command_line_perspectives>`, allows you to choose
between generating a screenshot with an :ref:`orthographic view
<ortho_lightbox_views_ortho>` or a :ref:`lightbox view
<ortho_lightbox_views_lightbox>`::

  fsleyes render --scene ortho    --outfile outfile file [displayOpts] ...
  fsleyes render --scene lightbox --outfile outfile file [displayOpts] ...
