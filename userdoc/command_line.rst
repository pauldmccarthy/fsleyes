.. _command_line:

Command line interface
======================


FSLeyes has a comprehensive command line interface. Nearly everything that you
can control through the :ref:`overlay display panel
<overlays_overlay_display_panel>`, and the :ref:`view settings panel
<ortho_lightbox_views_view_settings>` for orthographic/lightbox/3D views, can
be set via the command line.


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


What follows is a short list highlighting some of the features in FSLeyes that
you can access through the command line interface. For full details, refer to
the :ref:`command line help <command_line_help>`.

- :ref:`Auto display <command_line_auto_display>`
- :ref:`Add standard <command_line_add_standard>`
- :ref:`Layouts <command_line_layouts>`
- :ref:`Font size <command_line_font_size>`
- :ref:`Neurological orientation <command_line_neurological_orientation>`
- :ref:`Force-load images <command_line_force_load_images>`
- :ref:`Run script <command_line_run_script>`
- :ref:`One FSLeyes instance <command_line_one_instance>`


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


.. _command_line_layouts:

Layouts
^^^^^^^

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
:ref:`layout <overview_layouts>`. If you have saved your
own custom layout, you can also load it, by name, using the ``--scene``
option.



.. _command_line_font_size:

Font size
^^^^^^^^^


You can set the font used throughout the FSLeyes interface via the
``--fontSize`` argument::

    fsleyes --fontSize  6 files ...
    fsleyes  -fs       14 files ...



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


FSLeyes has a programming interface which you can use to programmatically set
up complex scenes. The ``--runscript`` option allows you to execute a Python
script when FSLeyes starts, which can load overlays and configure their
display properties, and set up the FSLeyes interface.  These scripts have
access to the same environment that is available via the :ref:`FSLeyes-Jupyter
notebook <fsleyes_notebook>`.


.. _command_line_one_instance:

One FSLeyes instance
^^^^^^^^^^^^^^^^^^^^


By default, when you call ``fsleyes`` on the command line, a new FSLeyes
instance will be opened. If you would prefer to have just one instance of
FSLeyes open, you can use the ``--cliserver`` option::

    fsleyes --cliserver ...
    fsleyes  -cs        ...


The first time you call ``fsleyes`` in this way, the FSLeyes application will
open as normal. Then, on subsequent calls, all of the arguments that you
specify on the command-line will be passed to that first instance. Note that
only *overlay* arguments will be applied on subsequent calls - all arguments
pertaining to the FSLeyes layout or displayed scene will be ignored.


If you would like FSLeyes to behave this way permanently, add an alias to
your shell startup file (e.g. ``~/.bash_profile`` if you are using macOS)::

    alias fsleyes="fsleyes --cliserver"


.. _command_line_generating_arguments:

Generating command line arguments
---------------------------------


The :ref:`orthographic, ligthtbox <ortho_lightbox_views>` and :ref:`3D
<3d_view>` views have the ability to generate a command line which describes
the currently displayed scene. This is available in the *View* sub-menu for
each of these views, as the *Show command line for scene* option.  These views
also have a *Apply command line arguments* option, which allows you to paste
in a previosuly generated command line.


.. _command_line_examples:

Examples
--------


Volume overlays
^^^^^^^^^^^^^^^

Set up display/clipping/colourmap/interpolation on an image, and centre
display at a specific voxel::


  fsleyes -sortho -std1mm -vl 33 20 31 \
    zstat1.nii.gz -dr 2.5 3.5 -cr 2.5 3.5 -cm hot -in spline


Set up positive/negative colour map on a PE image::


  fsleyes -std1mm pe1 -un -cm red-yellow \
    -nc blue-lightblue -dr 10 60 -in spline


Vector overlays
^^^^^^^^^^^^^^^


Display ``dtifit`` output as an RGB vector::

  fsleyes dti_FA dti_V1 -ot rgbvector

Display ``bedpostx`` two-fibre output as line vectors::

  fsleyes mean_f1samples dyads1 -ot linevector dyads2_thr0.05 -ot linevector


Display ``dtifit`` output as a tensor (not possible in a SSH/X11 session).
You can specify the ``dtifit`` output directory::

  fsleyes dtifit/dti_FA dtifit/

Or the 6-volume image containing the unique elements of the tensor matrix::

  fsleyes dtifit/dti_FA dtifit/dti_tensor.nii.gz -ot tensor


Display spherical harmonic coefficients (not possible in a SSH/X11 session)::

  fsleyes asym_fods.nii.gz -ot sh


Melodic mode
^^^^^^^^^^^^

Specify the path to your filtered_func_data.ica directory::

  fsleyes -s melodic path/to/analysis.ica/filtered_func_data.ica

Or the path to your melodic_IC file::

  fsleyes -s melodic path/to/analysis.ica/filtered_func_data.ica/melodic_IC

Use the ``-ad`` flag (``--autoDisplay``) to automatically set up colour maps::

  fsleyes -ad -s melodic path/to/analysis.ica/filtered_func_data.ica/melodic_IC


Lightbox view
^^^^^^^^^^^^^

Set Z axis, number of rows, and number of columns::

  fsleyes -slightbox -zx Z -nr 10 -nc 10 -std1mm

Set slice spacing (mm)::

  fsleyes -slightbox -zx Z -ss 10 -std1mm

Set slice range (mm, starting from 0)::

  fsleyes -slightbox -zx Z -ss 5 -zr  0  91 -std1mm
  fsleyes -slightbox -zx Z -ss 5 -zr 91 182 -std1mm
  fsleyes -slightbox -zx Z -ss 5 -zr 45 136 -std1mm


.. _command_line_offscreen_rendering:

Off-screen rendering
--------------------


FSLeyes is capable of generating screenshots from the command line. This is
useful, for example, if you need to generate a large number of PNG images for
quality control purposes. Simply build a FSLeyes command line which generates
the scene that you wish to view, and then tell FSLeyes to render the scene to
a file.


You can access the FSLeyes off-screen renderer by passing the word ``render``
as the **first** argument to FSLeyes::

  fsleyes render ...


The ``fsleyes render`` command will also work on systems which do not have a
display (e.g. cluster nodes), as long as the `osmesa
<https://docs.mesa3d.org/osmesa.html>`_ library is available. In order to use
``osmesa``, you need to set the ``PYOPENGL_PLATFORM="osmesa"`` environment
variable.


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
:ref:`specify a layout <command_line_layouts>`, allows you to choose
between generating a screenshot with an :ref:`orthographic
<ortho_lightbox_views_ortho>`, :ref:`lightbox
<ortho_lightbox_views_lightbox>`, or :ref:`3D <3d_view>` view::

  fsleyes render --scene ortho    --outfile outfile file [displayOpts] ...
  fsleyes render --scene lightbox --outfile outfile file [displayOpts] ...
  fsleyes render --scene 3d       --outfile outfile file [displayOpts] ...
