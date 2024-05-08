.. |right_arrow|  unicode:: U+21D2
.. |command_key|  unicode:: U+2318
.. |shift_key|    unicode:: U+21E7
.. |control_key|  unicode:: U+2303
.. |eye_icon|     image::   images/eye_icon.png
.. |chain_icon|   image::   images/chainlink_icon.png
.. |spanner_icon| image::   images/spanner_icon.png


This document contains the ``fsleyes`` release history in reverse
chronological order.


1.12.0 (Wednesday 8th May 2024)
-------------------------------


Added
^^^^^


* New ``--autoName`` / ``-an`` command-line option, which causes overlays that
  would otherwise have the same name to be automatically renamed (!434).


Fixed
^^^^^


* Updated the *Show command-line for scene* menu item to support the
  ``--asVoxels`` flag for lightbox views (!435).


1.11.0 (Monday 22nd April 2024)
-------------------------------


Added
^^^^^


* New *Choose lightbox slices* option, available under the *Tools* menu, which
  allows lightbox slices to be specified via voxel coordinates instead of
  proportions (!432).
* New ``--asVoxels`` command-line option for use with lightbox views, which
  causes the ``--zrange`` and ``--sliceSpacing`` options to be interpreted
  as voxel coordinates instead of proportions (!432).


Changed
^^^^^^^


* FSLeyes will now attempt to automatically set ``$FSLDIR`` if it is not set
  (e.g. when started from a desktop launcher) (!428).


Fixed
^^^^^


* Voxels with high values are no longer clipped when loading a probabilistic
  atlas overlay from the atlas panel (!431).
* Fixed an issue with argument parsing under Python 3.12 (!432).


1.10.4 (Monday 25th March 2024)
-------------------------------


Fixed
^^^^^


* Added a work-around to avoid send2trash-related crashes on old versions of
  macOS (!426, see https://github.com/arsenetar/send2trash/issues/83).


1.10.3 (Thursday 29th February 2024)
------------------------------------


Added
^^^^^


* New ``-u`` / ``--ungroupOverlays`` command-line option, which causes all
  overlays to be unlinked by default (via the overlay list chain-link
  |chain_icon| button). This has the effect that properties such as
  interpolation, which are normally linked across all overlays, can be set
  independently for each overlay (!422).


Changed
^^^^^^^


* Some additional display properties are now linked by default across
  overlays, including mesh outline and outline width and line vector width and
  L/R orientation flip. These properties can be unlinked for a specific overlay
  via the overlay list chain-link |chain_icon| button (!424).


Fixed
^^^^^


* Fixed an issue with overlay depth-sorting in the 3D view (!422).
* Fixed an issue in the lightbox view when displaying label and mask overlays and
  overlapping lightbox slices (!424).


1.10.2 (Thursdy 18th January 2024)
----------------------------------


Fixed
^^^^^

* Fixed a bug which made edit mode inaccessible when more than one view was
  open (!418).
* Fixed a bug affecting the lookup table panel, and *Load colour map* option
  (!419).
* Fixed a mask overlay bug where, when specifying both `--alpha` and
  `--maskColour` would cause the `--alpha` value to be ignored (!419).


1.10.1 (Thursday 16th November 2023)
------------------------------------


Changed
^^^^^^^


* Adjust initialisation logic to prevent FSLeyes from crashing due to a
  corrupt third-party plugin (!416).


1.10.0 (Tuesday 14th November 2023)
-----------------------------------


Changed
^^^^^^^


* FSLeyes colour map and lookup table files can now be stored in a site-specific
  configuration directory, which can be set by a ``$FSLEYES_SITE_CONFIG_DIR``
  environment variable, by
  Rob Reid (@captainnova) (!412, `GitHub PR
  <https://github.com/pauldmccarthy/fsleyes/pull/121>`__).
* FSLeyes layouts can now be stored as plain-text files, in the FSLeyes settings
  directory, or in ``$FSLEYES_SITE_CONFIG_DIR`` (!412).
* Changed the behaviour of the *Modulate alpha by intensity* setting for mesh
  overlays. Now, if the *Hide clipped areas* setting is enabled, the mesh
  transparency is modulated by intensity. But the *Hide clipped areas* setting
  is disabled, the mesh data colour is blended with its background colour
  (!411).


Fixed
^^^^^

* Fixed an issue with mesh depth ordering in the 3D view, when running FSLeyes
  in legacy environments (!411).


1.9.0 (Monday 25th September 2023)
----------------------------------


Added
^^^^^


* New keyboard shortcut (|control_key| + |shift_key| + ``f``) to toggle
  visibility of all overlays except for the first/bottom one, by
  Christopher G. Schwarz (@CGSchwarzMayo) (!406, `GitHub PR
  <https://github.com/pauldmccarthy/fsleyes/pull/118>`__).
* New *FSLView mode* for the *Display space* setting, which emulates the
  behaviour of FSLView, by Christopher G. Schwarz (@CGSchwarzMayo) (!407,
  `GitHub PR <https://github.com/pauldmccarthy/fsleyes/pull/117>`_).
* New ``--hideOrientationWarnings`` command-line option, which hides the
  location panel warning regarding different orientations / fields-of-view, by
  Christopher G. Schwarz (@CGSchwarzMayo) (!407, `GitHub PR
  <https://github.com/pauldmccarthy/fsleyes/pull/117>`__).


Changed
^^^^^^^


* FSLeyes now attempts to detect FreeSurfer-generated GIfTI surfaces, and will
  set the coordinate space accordingly (!407).


Fixed
^^^^^


* Fixed an issue with colour maps caused by changes in matplotlib 3.8 (!409).


1.8.3 (Thursday 31st August 2023)
---------------------------------


Added
^^^^^


* New ``--cmapCycle`` command-line option, which automatically assigns a
  different colour map to each ``volume`` overlay (!402).


Fixed
^^^^^


* Fixed an issue with overlays being interleaved when overlapping slices in
  the lightbox view (!403).
* Fixed some bugs in edit mode - crashes could occur when drawing/selecting
  voxels in highly anisotropic images, and the cursor size could vary for
  images with floating point imprecision in their pixdims (!404).


1.8.2 (Tuesday 22nd August 2023)
--------------------------------


Fixed
^^^^^


* Fixed an issue with loading built-in plugins - the atlas panel (amongst
  others) was not being loaded (!400).


1.8.1 (Thursday 17th August 2023)
---------------------------------


Fixed
^^^^^


* Filtered some irrelevant warning messages from underlying libraries (!395).


1.8.0 (Wednesday 16th August 2023)
----------------------------------


Added
^^^^^


* New features in the lightbox view, allowing slices to be overlapping, and
  the order in which slices are displayed to be reversed. These features are
  available on the command-line via the ``--sliceOverlap`` and
  ``--reverseSlices`` flags (!379).
* FSLeyes plugin libraries can now provide custom layouts (!386).


Changed
^^^^^^^


* The _Nudge_ panel now applies scaling parameters such that the
  centre-of-volume or the current cursor location are preserved. The previous
  behaviour was such that location (0, 0, 0) was preserved by the scaling
  parameters (!378).
* The FEAT cluster panel now remembers which contrast for a FEAT analysis was
  selected when switching between different analyses (!380).
* Updated the FSLeyes plugin architecture to use ``importlib`` instead of the
  deprecated ``pkg_resources``. FSLeyes plugin libraries no longer need to have
  a name beginning with ``fsleyes-plugin`` (!385).
* FSLeyes plugins provided by third-party libraries are now hidden by default,
  but are shown when a custom layout defined in the library is applied.  All
  plugins can be shown via the ``--showAllPlugins`` command-line option (which
  can be saved as a :ref:`default argument <command_line_default_arguments>`
  to be permanently applied) (!386).


Fixed
^^^^^


* Updates to the Jupyter Notebook integration to work with Notebook 7.x (!383).
* Fixed a transparency issue in the ortho panel (!384).


1.7.0 (Tuesday 13th June 2023)
------------------------------


Added
^^^^^

* New *colour range* option (available via the ``--colourRange`` command-line
  option) which can be used on vector overlays when colouring them by a
  secondary image, to specify the mapping between the voxel intensities and
  the colour map (!371).
* New *Show slice location* option, allowing the location of each slice to be
  displayed in the lightbox view (!375).


Changed
^^^^^^^


* Changed the ``--initialDisplayRange`` command-line option to have the same
  behaviour as the ``--displayRange`` option - by default, the values will
  now be interpreted as raw intensities. Values can be specified as percentiles
  by appending a ``%`` to the high value (!366).
* Colour map and lookup table files may now have a ``.txt`` suffix instead of
  ``.cmap`` / ``.lut`` (!368).
* Colour map interpolation will now be applied to the colour bar shown in the
  ortho/lightbox/3D views (!368).
* Changed the behaviour of the *Clip by* and *Modulate by* settings for volume
  overlays - when clipping/modulating by a secondary image, and a negative
  colour map is in use, the *absolute* values of the secondary image are now
  used for clipping/modulation (!370).
* Changes to the mechanism used to save screenshots/movies, which should make
  the process more robust (!371).


Fixed
^^^^^


* Fixed some issues with parsing command line arguments for RGB vector and
  complex images (!363, !364).
* Fixed an issue with plotting the MELODIC power spectrum for data with an
  odd number of timepoints (!365).
* Fixed an issue when passing a colour map file path to the ``--negativeCmap``
  option (!368).
* Fixed an issue related to loading NIfTI ``qform`` matrices which arose
  with ``nibabel >= 5.1.0`` (!369).
* Fixed an edit mode issue where a drawn line would have gaps in it (!369).
* Some minor fixes which allow the overlay type of a NIfTI image to be changed
  whilst it is being edited (!369).
* Fixed a small issue with ``volume`` overlays sometimes not being refreshed
  (!372).


1.6.1 (Thursday 23rd February 2023)
-----------------------------------


Changed
^^^^^^^


* Internal changes to avoid having to overwrite built-in ``matplotlib``
  colour maps (!360).


1.6.0 (Tuesday 20th February 2023)
----------------------------------


Added
^^^^^


* Added an *outline* button to the overlay display toolbar for mask overlays
  (!342).
* New ``--no3DInterp`` / ``-ni`` option, which prevents interpolation from
  being enabled for volume overlays when a 3D view is opened (!344).
* FSLeyes will now read "default" command-line arguments from a file called
  ``default_arguments.txt``, stored in the FSLeyes settings directory (!347).
* New ``--numSlices`` command-line option for use with lightbox views, which
  is an inverted alias for the ``--sliceSpacing`` option (!350).


Changed
^^^^^^^


* DICOM directories are now only scanned once, instead of each time they are
  opened via the *Add from DICOM* menu option (!345).
* The ``--useNegativeCmap`` / ``-un`` option is now automatically enabled when
  ``--negativeCmap`` / ``-nc`` is specified (!350).



Fixed
^^^^^


* Fixed some issues related to shutting down FSLeyes cleanly, which could
  occasionally result in segmentation faults (!340).
* Fixed an issue with tractogram overlays not being drawn in some
  circumstances (!341).
* Fixed an issue with loading mesh vertex data (!343).
* Fixed an issue with loading annotations when using ``fsleyes render`` (!346).


1.5.0 (Wednesday 31st August 2022)
----------------------------------


Added
^^^^^


* ``ViewPanel`` plugin classes can now implement the
  :meth:`~.ViewPanel.defaultLocation` static method to specify an initial
  location and size within the FSLeyes frame (!334).
* New built-in ``defaultlb`` and ``default3d`` layouts, which respectively open
  a lightbox or 3D view with standard toolbars and control panels.
* New ``--noBrowser`` / ``-nbb`` command-line option, which starts a Jupyter
  kernel without opening the Notebooks home page; this can be used when you
  wish to attach a terminal IPython instance to FSLeyes, instead of a Jupyter
  notebook (!334).


Changed
^^^^^^^


* Redesigned the lightbox view to simplify behaviour and interaction (!334).
* Restored low-performance settings for the ortho and lightbox views (!333).
* The time series, power spectra and histogram panels now default to
  displaying data series from all compatible overlays, instead of just the
  currently selected overlay (!334).


Fixed
^^^^^


* Fixed several issues related to mesh rendering in the lightbox view (!333).
* Fixed an issue with the location cursor (and other annotations) not being
  displayed when running FSLeyes in OpenGL 1.4 compatibility mode on macOS (!334).
* Fixed a memory leak triggered by the file tree panel (!334).


Removed
^^^^^^^


* Removed the ``--highDpi`` command-line and interface option - as of wxPython
  4.1.0, high DPI scaling should be taken care of automatically (!338).


1.4.6 (Tuesday 14th June 2022)
------------------------------


Fixed
^^^^^


* Fixed an issue with mesh outlines not appearing in the orthographic view
  (!331).


1.4.5 (Friday 20th May 2022)
----------------------------


Fixed
^^^^^


* Added support for the ``NIFTI_TEMPLATE_XFORM_OTHER`` code (!329).


1.4.4 (Tuesday 17th May 2022)
-----------------------------


Fixed
^^^^^


* Fixed an issue with removing items from the annotation panel (!327).
* Fixed an issue with toggling ortho view canvases in VNC/SSH sessions (!327).


1.4.3 (Tuesday 17th May 2022)
-----------------------------


Fixed
^^^^^


* Changed GL initialisation logic so that it is compatible with newer GTK2/GLX
  versions of wxPython (!324).


1.4.2 (Friday 13th May 2022)
----------------------------


Fixed
^^^^^


* Make sure atlas images (selected through the atlas panel) are loaded into
  RAM. This used to be the case, but default behaviour was changed recently in
  the ``fsl.data.image`` and ``fsl.data.atlases`` modules (!322).



1.4.1 (Tuesday 3rd May 2022)
----------------------------


Fixed
^^^^^


* Fixed an issue with 2D tractogram display on macOS (!318).


1.4.0 (Monday 2nd May 2022)
---------------------------


Added
^^^^^


* FSLeyes is now able to visualise TrackVis ``.trk`` and Mrtrix3 ``.tck``
  tractogram files, containing tractography streamlines (!307, !312).
* New *Invert modulata alpha* display setting (available via the
  ``--inverModulateAlpha`` command-line option), which can be used to
  make regions with high intensity more transparent (!311).
* New ``--index`` command-line option for ``volume`` overlays, allowing
  the indices for all non-spatial dimensions to be specified (!304).
* New option to display the coordinates for the current location on the
  canvases of an ortho view (available on the command-line via
  ``--showLocation``) (!314).
* New option to control the location cursor width on ortho/lightbox views
  (available on the command-line via ``--cursorWidth``) (!314).


Changed
^^^^^^^


* Improvements to overlay blending, and default volume quality settings, in
  the 3D view (!309).


Fixed
^^^^^


* Fixed an issue with loading FIRST subcortical segmentation VTK meshes (!306).
* Fixed an issue with the ``--updatecheck`` commmand line argument (!306).
* Fixed some bugs in the *File tree panel* (!315).


Removed
^^^^^^^


* The ``--occlusion`` command-line option has been rendered obsolete by the
  improved 3D overlay blending, and so has been removed (along with the
  corresponding option in the 3D view settings panel).


1.3.3 (Thursday 23rd December 2021)
-----------------------------------


Fixed
^^^^^


* Fixed an issue with black screenshot images in some environments (e.g.
  SSH sessions in mobaxterm) (!301).
* Removed ``pyobj-core`` and ``pyobjc-framework-cocoa`` from the list
  of dependencies (!302).


1.3.2 (Thursday 9th December 2021)
----------------------------------


Fixed
^^^^^

* Fixed an issue with line vector display when running FSLeyes in an
  environment which doesn't support floating point textures (!299).


1.3.1  (Thursday 2nd December 2021)
-----------------------------------


Fixed
^^^^^

* Updated Jupyter notebook integration to work with newer versions of
  ``ipykernel`` (!297).
* Various small tweaks for Python 3.10 compatibility (!297).


1.3.0 (Monday 18th October 2021)
--------------------------------


Added
^^^^^


* The 3D view now allows the display location to be set to the corresponding
  location under the mouse on a volume overlay, by shift+clicking (!290).
* The display range for a ``volume`` overlay can now be adjusted interactively
  by |command_key| + |shift_key| + right clicking (|control_key| + |shift_key|
  on Linux) and dragging to select a region - the display range will be set to
  the minimum/maximum voxel intensities within that region (!293).


Changed
^^^^^^^


* The *Sample along line* tool now supports 2D and multi-channel (e.g. RGB)
  images (currently plotting the mean intensity across channels for the
  latter).
* Small improvementsto the *File* |right_arrow| *Add from XNAT* dialog (!291).


Fixed
^^^^^


* The **Display space** |right_arrow| *Scaled voxel coordinates* setting no
  longer applies a L/R flip for images with neurological data storage order
  (!289).
* The high clipping range is no longer set when loading a Melodic image
  with the ``--autoDisplay`` / ``-ad`` option.(!293).


1.2.0 (Monday 13th September 2021)
----------------------------------


Added
^^^^^


* The **Display space** setting can now be set to *Scaled voxel coordinates*
  on ortho and lightbox views. This causes all images to be displayed in
  scaled voxels, with the origin for each image set to the centre of voxel
  ``(0, 0, 0)`` (!286).


Changed
^^^^^^^


* The *scale vectors to unit length* option for line vector overlays now
  scales the vector colouring, in addition to lengths (!285).


Fixed
^^^^^


* Fixed an issue on macOS / Big Sur whereby an image specified on the
  command-line could be loaded twice (!285).
* Fixed some rendering issues for images stored as type ``NIFTI_TYPE_RGB24``
  (!285).


1.1.0 (Friday 6th August 2021)
------------------------------


Added
^^^^^


* New ``--interpolation`` option for ``mesh`` overlays, which allows
  nearest-neighbour or linear interpolation to be selected when colouring
  meshes with vertex data. This replaces the ``--flatShading`` option (!278).


Changed
^^^^^^^


* The Location panel now displays the region label associated with the current
  vertex for mesh overlays which are being coloured with a lookup table (!278).


Fixed
^^^^^


* Fixed a bug which was preventing the same colour map or lookup table file to
  be specified more than once on the command line (!278).
* Fixed the *Check for updates* menu item - it now queries ``conda-forge`` for
  the latest available FSLeyes version (!279).
* Fixed a bug which had broken volume navigation in the time series view
  (!283).


Deprecated
^^^^^^^^^^


* The ``--flatShading`` option for ``mesh`` overlays is equivalent to using
  ``--interpolation nearest`` (!278).


1.0.15 (Thursday 22nd July 2021)
--------------------------------


Fixed
^^^^^


* Fixed a subtle bug affecting ``fsleyes render``, where taking a screenshot
  of a large 4D image could result in an infinite loop or segmentation fault
  (!275).


1.0.14 (Friday 16th July 2021)
------------------------------


Fixed
^^^^^


* Fixed an issue with image copying, which could cause pixdims to be changed
  slightly (!270).
* The x-axis of the power spectrum view can can now show frequencies of ICA
  power spectra for for MELODIC overlays (!271).


1.0.13 (Tuesday 6th July 2021)
------------------------------


Fixed
^^^^^


* Fixed a circular import issue, affecting programmatic use of FSLeyes (!268).


1.0.12 (Monday 28th June 2021)
------------------------------


Fixed
^^^^^


* Fixed an issue with Jupyter Notebook integration on macOS (!266).


1.0.11 (Monday 14th June 2021)
------------------------------


Fixed
^^^^^


* Fixed a compatibility issue with NoMachine/x2go-like remote environments
  (!264).


1.0.10 (Wednesday 2nd June 2021)
--------------------------------


Fixed
^^^^^


* Fixed an issue with removing data series from plot views (!262).


1.0.9 (Wednesday 2nd June 2021)
-------------------------------


Fixed
^^^^^


* Fixed an issue with opening the overlay display panel in 3D views (!260).


1.0.8 (Wednesday 26th May 2021)
-------------------------------


Changed
^^^^^^^


* Gamma correction is no longer disabled when log scaling is active (!256).


Fixed
^^^^^


* Fixed a problem with API documentation generation (!256, !258).


1.0.7 (Monday 24th May 2021)
----------------------------


Added
^^^^^


* New *logarithmic scaling* option (``--logScale`` on the command-line) for
  volume overlays, which causes voxel intensities to be mapped to the colour
  map logarithmically, rather than linearly (!254).


1.0.6 (Monday 24th May 2021)
----------------------------


Changed
^^^^^^^


* Overlay display options which refer to other overlays (e.g. *Clip by*) now
  use the display name of the other overlay, rather than their file base name
  (!251).
* Restored compatibiilty with wxPython 4.0.* (!250).


Fixed
^^^^^


* Fixed a bug related to positioning of line vectors, tensors and FODs for
  images with non-isotropic voxels (!250).


1.0.5 (Thursday 6th May 2021)
-----------------------------


Fixed
^^^^^

* Fixed some issues with shutting down cleanly (!248).
* Fixed a bug when saving a layout with plugin-provided view panels (!248).


1.0.4 (Tuesday 4th May 2021)
----------------------------


Changed
^^^^^^^


* Improved ortho edit mode performance on large images (!246).
* Suppressed some warning messages (!246).


Fixed
^^^^^


* Fixed an issue with the :attr:`.PlotCanvas.limits` becoming out of sync with
  the ``matplotlib.Axes`` limits (!246).
* The ``file-tree`` library is now optional (!246).


1.0.3 (Friday 23rd April 2021)
------------------------------


Fixed
^^^^^


* Fixed an issue with the management of built-in asset files (e.g. icons,
  colour maps, etc). Asset files are now located inside the ``fsleyes``
  package directory (!244).


1.0.2 (Thursday 22nd April 2021)
--------------------------------


Fixed
^^^^^


* Fixed some issues with FSLeyes plugin management (!242).
* Fixed some issues with GL initialisations on GTK2 versions of ``wxpython``
  (!242).
* New ``--annotations`` command-line option, allowing annotations to be
  loaded from a file into an ortho view (!242).


1.0.1 (Tuesday 20th April 2021)
-------------------------------


Fixed
^^^^^


* Fixed compatibility issues with recent versions of matplotlib (!240).


1.0.0 (Monday 19th April 2021)
------------------------------


Added
^^^^^


* The lighting effect in the 3D view is now applied to ``volume`` overlays
  (OpenGL 2.1 or newer only) (!222).
* New ``--lightDistance`` option (for 3D view), allowing the distance of the
  light source from the centre of the display bounding box to be set (!222).
* New ``--noBlendByIntensity`` option, for ``volume`` overlays in the 3D view,
  allowing the modulation of samples by voxel intensity to be disabled (!222).
* New ``-ixh``, ``-ixv``, ``-iyh``, ``-iyv``, ``-izh``, and ``-izv`` options,
  allowing ortho canvases to be inverted vertically or horizontally (!225).
* New ``--modulateMode`` option for ``rgbvector``, ``linevector``, ``tensor``
  and ``sh`` overlays, allowing modulation to be applied to either brightness
  or transparency (!231).
* New option to copy/paste 2D selections between slices when editing a NIFTI
  image (!232).
* New *annotation* panel, allowing simple shapes and text to be overlaid on
  the canvases of an ortho view. Annotations can be saved to/loaded from file,
  via new options in the *Tools* menu (!233).
* New *Sample along line* tool, allowing data from an image to be sampled
  along a line and plotted (!235).


Changed
^^^^^^^


* Text labels drawn on GL canvases are now created using ``matplotilb`` rather
  than [Free]GLUT (!221).
* Removed dependence on [Free]GLUT - this means that ``fsleyes render`` can
  now be used on headless systems without using ``xvfb-run``, as long as
  `OSMesa <https://docs.mesa3d.org/osmesa.html>`_ is installed (!221).
* The ``--lightPos`` command-line option (for the 3D view) has been changed to
  expect three rotation values (in degrees), which specify the position of the
  light source with respect to the centre of the display bounding box. This
  can be combined with the new ``--lightDistance`` option to specify the
  position of the light source (!222).
* FSLeyes no longer ignores the ``LIBGL_ALWAYS_INDIRECT`` environment
  variable (!222).
* FSLeyes attempts to determine a suitable value for ``PYOPENGL_PLATFORM``
  if it is not already set (!222).
* FSLeyes should now work with both Wayland/EGL and X11/GLX builds of wxPython
  on Linux (!222).
* The normalisation method used in the power spectrum panel has been adjusted
  so that, instead of the data being normalised to unit variance before the
  fourier transform, the fourier-transformed data itself is normalised to the
  range [-1, 1] (!224).
* The *Show command line for scene* option will display a warning if any
  overlays are not saved (!226).
* The :class:`.FileTreePanel` has been updated to work with the
  new `file-tree <https://pypi.org/project/file-tree/>`_ library (!230).
* Change to the interface for copying/pasting data between images - there is
  now a single button for copying, pasting, and clearing the clipboard (!232).
* :class:`.annotations.TextAnnotation` objects can now be positioned in the
  display coordinate system, in addition to being positioned at pixel locations
  on a canvas (!232).
* Changes to the FSLeyes plugin system to ease the development of FSLeyes
  controls that use custom interaction profiles, and to improve switching
  between different interaction proflies (!234).
* The FSLeyes plugin system now supports tools which are bound to a specific
  view panel (!234).
* Many built-in FSLeyes control panels and tools have been migrated into the
  FSLeyes plugin system so that they are dynamically loaded as plugins, rather
  than being hard-coded (!234).
* It is now possible to save and re-load view/control panel layouts with
  plugin-provided views and control panels (!234).


Fixed
^^^^^


* Various fixes and improvements to the lighting effect on ``mesh`` overlays
  in the 3D view (!222).
* When opening a ``melodic_IC.nii.gz`` file with the
  ``--autoDisplay'`/``-ad``, option, the ``melodic_IC`` file is now selected
  by default, instead of the ``mean`` underlay (!219).
* Fixed a bug in image texture preparation for complex data types, when
  running in a limited GL environment (e.g. VNC) (!220).
* Compatibility fixes for newer versions of Jupyter `notebook` (!227).
* Fixed a problem with macOS desktop integration - it should now be possible
  to open a file with FSLeyes as the default application, and to drag a file
  onto the FSLeyes.app icon (!228).
* Improved stability when running under macOS+XQuartz (!229).
* Fixed an issue with screenshots generated by ``fsleyes render`` containing
  transparent pixels (!233).
* Fixed a collision between the ``-mc`` and ``-a`` command-line options for
  mesh overlays (!233).


0.34.2 (Tuesday 14th July 2020)
-------------------------------


Fixed
^^^^^


* Added support for high-DPI scaling under macOS with wxPython >= 4.1.0 (!217).


0.34.1 (Monday 13th July 2020)
------------------------------


Fixed
^^^^^


* Fixed an issue with Jupyter Notebook integration on conda+macOS installations
  (!215).
* Fixed an issue with the high-DPI option not appearing in the view settings panel
  under macOS (!215).


0.34.0 (Wednesday 8th July 2020)
--------------------------------


Added
^^^^^


* New option under the *Tools* menu which allows data from an image overlay to
  be projected onto a surface overlay (!213).
* New *Flat shading* display option when viewing surfaces in 3D (!213).


Changed
^^^^^^^


* Tweaked GL initialisation to avoid errors when running via XQuartz (!211).
* Minor adjustment to Jupyter Notebook integration (!213).
* NaN values in mesh overlay vertex data are now handled in the same manner as
  clipped values - previously they would be displayed in the low colour from the
  selected colour map (!213).


0.33.2 (Tuesday 23rd June 2020)
-------------------------------


Added
^^^^^


* Added some more line styles to the plotting panels (!206).
* Added a new "accessible" lookup table, courtesy of Paul Tol
  (https://personal.sron.nl/~pault/) (!206).


Changed
^^^^^^^


* Increased the default plotting line width (!206).
* The default plot colours are now from a pre-generated accessible palette,
  rather than being randomly generated (!206).
* The default plot line style is also rotated, in addition the plot colour
  (!206).
* Adjusted the histogram panel so that, when plotting a probability histogram,
  the values are normalised by bin-width (!203).
* A minor adjustment to the default font, to improve readability on some
  platforms (!202).


Fixed
^^^^^


* Fixed an issue with FSLeyes not shutting down cleanly (!204).


0.33.1 (Monday 8th June 2020)
-----------------------------


Changed
^^^^^^^

* Changed the :func:`.embed` function so that a parent ``wx`` object is
  not required.


0.33.0 (Tuesday 26th May 2020)
------------------------------


Added
^^^^^


* New *modulate alpha* option for volume and mesh overlays, which causes
  opacity to be modulated by voxel/vertex intensity (!193).


Changed
^^^^^^^


* The minimum supported Python version is now 3.7, due to reliance upon
  a recent version of `fslpy` (!190).
* The :func:`.embed` function accepts a ``mkFrame`` argument, allowing
  it to be called without creating a :class:`.FSLeyesFrame` (!195).
* A warning is now displayed in the location panel when images with different
  orientations, resolutions and/or fields-of-view are being displayed (!198).


Fixed
^^^^^


* Fixed a bug in the *Export data series* action, which was causing
  a crash on macOS (!190).
* Importing modules from the current directory in the Notebook/shell
  environments is now possible within standalone versions of FSLeyes (!189).
* Fixed a small bug in the :func:`.embed` function (!189).
* Fixed a bug in the *Add from XNAT* action (!192).
* Adjusted the Jupyter Notebook integration so it does not rely on the
  existence of a command called ``jupyter-notebook`` (!191).
* Fixed a couple of bugs in the RGB vector overlay code (!194).
* Fixed a bug in ortho edit mode (!196).


0.32.3 (Monday 2nd March 2020)
------------------------------


Fixed
^^^^^


* Fixed a bug which occurred when using 3D mode on platforms with
  limited OpenGL capabilities.
* Fixed some minor issues in the file tree panel.


0.32.2 (Friday 21st February 2020)
----------------------------------


Fixed
^^^^^


* The animated GIF changes in 0.32.1 broke movie mode.


0.32.1 (Thursday 20th February 2020)
------------------------------------


Changed
^^^^^^^


* Any mesh overlay can now be displayed in the Freesurfer mesh coordinate
  system - not just Freesurfer meshes.
* Internal changes to avoid using the deprecated
  ``nibabel.dataobj_images.DataobjImage.get_data`` method.


Fixed
^^^^^


* Fixed a bug which caused mesh display to be corrupted when changing rows in
  the file tree panel.
* Added support for high-DPI displays on platforms other than macOS.
* Fixed a bug in animated GIF generation.
* Fixed a bug which occurred when editing 4D images.


0.32.0 (Thursday 7th November 2019)
-----------------------------------


Added
^^^^^


* New ``--notebookFile`` command-line option, which starts the Jupyter notebook
  server, and opens a specified notebook file.
* New option to change the location of the *Notes* column in the file treee
  panel.
* New ``--unitLength`` option for the *RGB vector* overlay type, which scales
  the vector data to unit length.
* Metadata from JSON sidecar files (e.g. in BIDS data sets) is now displayed
  in the overlay information panel.


Changed
^^^^^^^


* The :func:`.main.embed` function has been changed so that it now works in a
  synchronous manner, rather than using an asynchronous callback function.
* The Jupyter notebook server is now configured so that its root directory
  is the current working directory.
* Small valued regions are no longer shown in the atlas information panel.
  They are thresholded according to the ``lower`` threshold in the
  :class:`.AtlasDescription`.


Fixed
^^^^^


* Fixed a bug in :class:`.MeshOpts` bounds calculation.
* Fixed a bug in Jupyter notebook integration, where an error in the notebook
  would stop the kernel from executing any more commands.
* The *Robust FOV* and load/export affine transformation options now work
  with in-memory images.


0.31.2 (Tuesday October 22nd 2019)
----------------------------------


Changed
^^^^^^^


* FSLeyes is now more lenient towards NIfTI images with extreme qform affines.
* Various changes to improve GTK3 compatibility.
* Various changes to reduce warnings and unnecessary output messages.


Fixed
^^^^^


* Image texture data is now prepared off the main thread; this was the
  behaviour before version 0.30.0, but was accidentally disabled for that
  release.


0.31.1 (Tuesday October 8th 2019)
---------------------------------


Fixed
^^^^^


* Fixed a bug in edit mode where the image texture would not get updated
  correctly in restricted environments (e.g. VNC) with certain image data
  types.


0.31.0 (Thursday September 10th 2019)
-------------------------------------


Added
^^^^^


* New *File tree* control panel, for viewing data contained in structured
  directories.
* New ``complex`` overlay type, for displaying images with a complex data type.
* Support in plot panels for complex images - data from the real, imaginary,
  magnitude, and/or phase components can be plotted.
* New plot panel options to invert axes, and to apply scale/offsets.
* New power spectrum panel options to apply phase correction to complex image
  data.
* The atlas panel has basic support for more general "Statistic" atlas types.
* New *File* |right_arrow| *New image* menu option, a shortcut to create a
  new empty image.


Changed
^^^^^^^


* Images with a complex data type are no longer split into separate real and
  imaginary ``volume`` overlays - they are loaded as a single image, and
  displayed as ``complex`` overlays.
* The *Overlay* |right_arrow| *Copy* menu option now supports complex and
  RGB(A) images.
* The plugin interface for tools has changed slightly - tools provided by
  FSLeyes plugins are now passed references to the :class:`.OverlayList`, the
  :class:`.DisplayContext`, and to the main :class:`.FSLeyesFrame`, to their
  ``__init__`` method.


Fixed
^^^^^


* Fixed a bug in the :class:`.OverlayGroup` where old display settings were
  mistakenly being applied to newly added overlays.
* Fixed a number of minor bugs in the plot panel logic.


0.30.1 (Wednesday 7th August 2019)
----------------------------------


Changed
^^^^^^^

* The *Crop* tool can now be used to expand the field-of-view of an image,
  in addition to cropping an image.
* The label overlay ``--lut`` command-line option will accepts colour map
  files.


Fixed
^^^^^


* Added support for editing 2D images.
* Fixed a bug in the mesh vertex picking logic which would occur when multiple
  views were open.


0.30.0 (Thursday 27th June 2019)
--------------------------------


Added
^^^^^


* The volume overlay type now has support for NIfTI images of type ``RGB24``
  and ``RGBA32``, via a new *Channel* setting.
* New *RGB(A)* overlay type, for displaying the above image types.
* FSLeyes can now load bitmap images (e.g. ``.jpg``, ``.png``, etc.).  When a
  bitmap file is loaded it is internally converted into a 2D NIfTI image.
* New alternative main function :func:`fsleyes.filtermain.main`, which filters
  out useless warnings that originate from underlying libraries (e.g. ``wx``,
  GTK, Cocoa, etc).
* New ``--cliserver`` option, allowing command-line arguments to be passed
  to a single FSLeyes instance.


Changed
^^^^^^^


* The :mod:`fsleyes.gl.textures` package has been cleaned up and refactored
  without any attempt to preserve backwards compatibility. Much of the texture
  data handling code is now shared by the :class:`.Texture2D` and
  :class:`.Texture3D` classes.
* The :class:`.NiftiOpts` class has been moved into a separate module.
* 2D NIfTI images are now displayed with a 2D texture - this means that
  the maximum dimension size for 2D images is now 16384 on typical
  hardware.
* The *Freesurfer coordinates* coordinate space option is no longer available
  on non-freesurfer mesh overlays.


0.29.0 (Sunday May 12th 2019)
-----------------------------


Added
^^^^^


* The *Tools* |right_arrow| *Resample image* option now allows an
  image to be resampled to the space of another image.
* New ``-stdb`` and ``-std1mmb``  command-line options for loading
  brain-extracted versions of the MNI152 templtes.


Fixed
^^^^^


* Fixed an issue where images with unconventional voxel storage orders were
  being transformed into the display coordinate system in a slightly
  inaccurate manner.
* FIxed an issue with orthographic edit mode being incorrectly disabled when
  the selected overlay is changed.


0.28.3 (Sunday April 14th 2019)
-------------------------------


Fixed
^^^^^


* More PyOpenGL / read-only ``numpy`` array workarounds.


0.28.2 (Sunday April 14th 2019)
-------------------------------


Changed
^^^^^^^

* The update check option does not verify SSL certificates when downloading
  the latest version string.


Fixed
^^^^^


* Fixed an issue with the MIP overlay on macOS.
* Workarounds for the inability of PyOpenGL to accept read-only ``numpy``
  arrays.
* Minimum required ``fslpy`` version is now 2.1, so that "compressed"
  voxelwise EVs (suh as those generated by `PNM
  <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/PNM>`_) are supported.


0.28.1 (Monday April 8th 2019)
------------------------------


Fixed
^^^^^


* Fixed a bug in drag-and-drop functionality.


0.28.0 (Friday April 5th 2019)
------------------------------


Added
^^^^^


* Added metadata to allow better integration with Linux desktop environments,
  by Ankur Sinha (@sanjayankur31, [GitHub
  PR](https://github.com/pauldmccarthy/fsleyes/pull/13)).
* Added ability to drag-and-drop files onto the FSLeyes window to open them, by
  Taylor Hanayik (!99, !100).
* The ``--vertexSet`` and ``--vertexData`` command-line options now cause the
  last vertex set/data to be selected, and also support GIFTI surface files
  which contain multiple vertex sets and vertex data.
* New :meth:`.ControlMixin.defaultLayout` method, which can be overridden by
  control panels (including plugins) to customise the default panel
  positioning/layout.


Changed
^^^^^^^


* FSLeyes no longer depends on the ``deprecation`` library.


Fixed
^^^^^


* Jupyter Notebook integration has been updated to work with newer versions
  of the ``ipykernel`` library.
* Fixed bug with initial directory shown in open file dialogs.
* Fixed a bug which would sometimes cause 4D image data display to be
  corrupted on macOS.
* Fixed a bug which was preventing image textures from being updated when
  non-3D data regions were changed.


Deprecated
^^^^^^^^^^


* The :func:`fsleyes.overlay.guessDataSourceType` function has been deprecated,
  as it has been replaced by the :func:`fsl.data.utils.guessType` function.


0.27.3 (Friday February 8th 2019)
---------------------------------


Fixed
^^^^^


* Fixed initialisation bug on platforms with a non-English language.


0.27.2 (Friday February 8th 2019)
---------------------------------


Changed
^^^^^^^


* Small display range values are forced to 0 on the colour bar.


0.27.1 (Friday January 18th 2019)
---------------------------------


Fixed
^^^^^


* Updated the ``render`` command so it incoporates the recent enhancments to
  colour bar display.


0.27.0 (Monday December 3rd 2018)
---------------------------------


Added
^^^^^


* Complex image types are now supported - the real and imaginary components
  are loaded as separate overlays.
* New *Set $FSLDIR* menu option, for updating the FSL installation directory.


Changed
^^^^^^^


* FSLeyes is no longer tested against Python 2, or wxPython 3.
* The *Tools* |right_arrow| *Resample image* menu option now supports images
  with more than three dimensions.
* Increased range of colour bar tick labels.
* When the negative colour map is enabled, and the display range minimum is
  0.0, only a single central tick label is displayed on the colour bar.


Fixed
^^^^^


* FSLeyes should fail more gracefully when unrecognised files/directories are
  specified on the command line.
* Fixed a bug in the ``--fullhelp``/``-fh`` command line option.


0.26.6 (Monday November 26th 2018)
----------------------------------


Fixed
^^^^^


* Fixed an issue with Zenodo DOI registration.



0.26.5 (Monday November 26th 2018)
----------------------------------


Added
^^^^^

* New option to change the colour bar width/height - this is available in the
  ortho/lightbox/3D settings panel (the |spanner_icon| button).
* The *Label size* option now adjusts the colour bar font size, in addition to
  the orientation label font size.


Fixed
^^^^^


* Fixed a bug in the time series panel when viewing a FEAT analysis with voxelwise
  confound EVs.
* Fixed a bug in the FEAT cluster panel when viewing a FEAT analysis which had
  not used cluster-based thresholding.



0.26.4 (Tuesday October 23rd 2018)
----------------------------------


Changed
^^^^^^^


* Renamed the *File* |right_arrow| *Add atlas* menu item to *Import new atlas*.


Removed
^^^^^^^


* Test data is not included in the FSLeyes source distribution, as it is too
  large for PyPi.


0.26.3 (Tuesday October 23rd 2018)
----------------------------------


Fixed
^^^^^


* Fixed a bug in edit mode where the selection overlay would sometimes
  not be displayed.
* Fixed a bug in the :class:`.DiagnosticReportAction` (the *FSLeyes*
  |right_arrow| *Diagnostic Report* menu item).


0.26.2 (Friday October 5th 2018)
--------------------------------


Changed
^^^^^^^


* Development (test and documentation dependencies) are no longer listed
  in ``setup.py`` - they now need to be installed manually.
* Removed conda build infrastructure.


0.26.1 (Sunday September 16th 2018)
-----------------------------------


Changed
^^^^^^^


* Reduced user documentation image sizes.


0.26.0 (Sunday September 16th 2018)
-----------------------------------


Added
^^^^^

* New :mod:`.plugins` architecture, for adding custom panels and tools to
  FSLeyes.
* The ``render`` tool has a new ``--crop`` option, to auto-crop screenshots.
* The :attr:`.VolumeOpts.overrideDataRange` is now automatically enabled for
  images with an extreme data range, on platforms that do not support floating
  point textures.
* New ``brain_colour`` colour maps provided by `MRICron
  <https://www.nitrc.org/projects/mricron>`_ and `Cyril Pernet
  <https://github.com/CPernet/brain_colours>`_.


Changed
^^^^^^^


* User-added and built-in colour map/lookup table names and display order can
  now be customised by adding a file called ``order.txt`` to the FSLeyes user
  configuration directory.


Fixed
^^^^^


* Updated user documentation.
* Fixed a bug in the :class:`.HistogramSeries` class.
* Fixed a bug in the :class:`.ImportDataSeriesAction` class.
* Fixed a bug in the :class:`.AddMaskDataSeriesAction` class.
* Fixed a bug in the :class:`.AddROIHistogramAction` class.
* :mod:`.gl` initialisation can now handle non-ASCII OpenGL renderer strings.


0.25.0 (Tuesday August 28th 2018)
---------------------------------


Added
^^^^^


* New MIP overlay type, for displaying 2D maximum intensity projections (not
  available over SSH/X11).
* A new movie mode option to change the canvas refresh regime between
  synchronised and unsynchronised, as the default synchronised regime does
  not work in some environments/platforms.
* New :func:`fsleyes.main.embed` function, allowing a FSLeyes frame to be
  opened from within an existing application.


0.24.6 (Monday August 6th 2018)
-------------------------------


Fixed
^^^^^


* Fixed a small bug in detection of image/analysis types from command line
  arguments.
* Fixed deprecation warning suppression in standalone versions of FSLeyes.


0.24.5 (Wednesday August 1st 2018)
----------------------------------


Added
^^^^^


* New command line flag  ``--notebook``/``-nb``, which starts the Jupyter
  notebook server automatically.


Changed
^^^^^^^


* Overlays loaded from ``fslpy`` wrapper functions are now named accordingly.


Fixed
^^^^^


* Fixed a memory leak in the :mod:`fsleyes.displaycontext.group` module.
* Suppresed some deprecation warnings when running frozen versions of FSLeyes.


0.24.4 (Thursday July 19th 2018)
--------------------------------


Fixed
^^^^^


* Fixed an error caused when loading a Melodic IC label file containing
  unrecognised labels.


Changed
^^^^^^^


* ``fslpy`` wrapper functions now return a value (e.g. if output files are
  marked for loading) when called from a Jupyter notebook or the FSLeyes
  python shell.
* The ``appnope`` library is only a dependency on macOS.



0.24.3 (Monday June 11th 2018)
------------------------------


Fixed
^^^^^


* Further fixes to Jupyter notebook server and kernel management for
  running within frozen versions of FSLeyes.
* Fixed a sizing issue in the FSLeyes about dialog.



0.24.2 (Friday June 8th 2018)
-----------------------------


Changed
^^^^^^^


* Changed the Jupyter notebook server management so it can be easily
  run within a frozen version of FSLeyes.


0.24.1 (Wednesday June 6th 2018)
--------------------------------


Changed
^^^^^^^


* Reduced the size of the PyPi source distribution files.



0.24.0 (Tuesday June 5th 2018)
------------------------------


Added
^^^^^


* Integration with `Jupyter Notebook <https://jupyter.org/>`_ is now
  available via the *File* |right_arrow| *Open notebooks* menu option.
* Support for high-resolution (e.g. retina) displays under macOS.
* ``fslpy`` FSL wrapper functions are now available in the Python shell
  and Jupyter notebooks.
* A colour bar preview is now shown in the overlay display panel.


Changed
^^^^^^^


* The *gamma* display setting now accepts values between -1 and +1.
* Minor improvements to 3D volumetric raycasting.
* The :mod:`fsleyes.perspectives` module  has been renamed to
  :mod:`fsleyes.layouts`. All associated functions and classes have been
  renamed accordingly.
* The :mod:`fsleyes.state` module has been re-written - the :func:`.getState`
  and :func:`.setState` functions can be used to save/restore the full
  FSLeyes state (layout and overlays).


Deprecated
^^^^^^^^^^


* The :mod:`fsleyes.perspectives`, :mod:`fsleyes.actions.clearperspective`,
  :mod:`fsleyes.actions.loadperspective`, and
  :mod:`fsleyes.actions.saveperspective` modules.
* The :mod:`fsleyes.views.shellpanel` has been deprecated in favour of
  using Jupyter notebooks.


Fixed
^^^^^


* Regression in handling 3D textures from on-disk image files.


0.23.0 (Friday May 4th 2018)
----------------------------


Added
^^^^^


* The *Nudge* tool now allows users to change the centre of rotation.
* New *gamma correction* display setting for volume and mesh overlays.
* New *smoothing* display setting for 3D volume rendering.
* New *normalise* display setting for SH FODs, to normalise individual
  FODs to voxel size.
* New *fill* tool in orthographic edit mode, which allows a bounded region to
  be filled or selected.


Changed
^^^^^^^


* Plot view interaction changed - left click to pan, right click to zoom, and
  hold down |control_key| (|command_key| under macOS) and click for secondary
  behaviour (e.g. changing the current volume on a time series panel).
* In edit mode, when a new image is created, it is now selected.


Fixed
^^^^^


* Freesurfer surface files could not be selectd in macOS open file dialogs.
* Freesurfer surfaces were causing an error in overlay information panel.
* Fixed issue where edit mode selection overlay could become out of date when
  display space was changed.
* Show/hide button in a plot view's overlay list no longer toggles overlay
  visibility on other (e.g. ortho) views.
* Selecting an item in a plot view's overlay list no longer shows/hides
  its data plot - the |eye_icon| button needs to be clicked.


Removed
^^^^^^^


* Removed all code and resources related to standalone versions of FSLeyes -
  this is now managed in a `separate project
  <https://git.fmrib.ox.ac.uk/fsl/fsleyes/build/>`_.


0.22.6 (Wednesday April 18th 2018)
----------------------------------


* Fixed more `libspatialindex` issues with macOS standalone builds.


0.22.5 (Tuesday April 17th 2018)
--------------------------------


Fixed
^^^^^


* Fixed an issue with macOS standalone builds (problems with
  `libspatialindex`).


0.22.4 (Thursday March 29th 2018)
---------------------------------


Fixed
^^^^^


* Fixed a couple of bugs in FOD rendering.


0.22.3 (Tuesday March 19th 2018)
--------------------------------


Added
^^^^^


* A new option for the :attr:`.MeshOpts.coordSpace` property - this fixes an
  issue with display alignemnt of freesurfer surfaces.


Deprecated
^^^^^^^^^^


* :meth:`.MeshOpts.getCoordSpaceTransform` - the
  :meth:`.MeshOpts.getTransform` should be used instead.


0.22.2 (Sunday March 18th 2018)
-------------------------------


Fixed
^^^^^


* Fixed an error with the *Override data range* not being applied correctly.


0.22.1 (Thursday March 15th 2018)
---------------------------------


Fixed
^^^^^


* Fixed an error which was being raised on attempts to add ("hold") a data
  series to a plot.



0.22.0 (Tuesday March 13th 2018)
--------------------------------


Added
^^^^^


* New Freesurfer lookup table (``freesurfercolorlut.lut``, provided by Vincent
  Koppelmans) to replace the incomplete ``mgh-cma-freesurfer.lut`` lookup
  table.
* FSLeyes can now load and save non-FLIRT affine transformation files.
* Infrastructure for buildling FSLeyes ``conda`` packages.
* Ortho view keyboard navigation shortcuts now work in edit mode.


Changed
^^^^^^^


* The x-axis in a time series view now defaults to showing volumes, rather
  than being scaled by time. This can be toggled via the *Use pixdims* option
  in the time series control panel.
* MGH images should no longer be displayed as unsaved. When an MGH image
  is copied/edited and saved, it will be saved as a NIfTI image.
* Labels in FSLeyes ``.lut`` files no longer need to be in ascending order.
* The FSLeyes settings directory should now be compatible across Python 2
  and 3.
* An error message is now displayed on attempts to load an invalid lookup
  table file.
* Adjustments to standalone Linux builds, hopefully fixing ``libxcb`` related
  compatibility issues.


Fixed
^^^^^


* FSLeyes should now run on macOS systems which have FreeGLUT installed.
* Fixed a bug where viewing outlines of mask or label overlays would cause
  a ``GLXBadRenderRequest`` error.
* Fixed a bug where mask overlays were not shown in a lightbox view over a
  SSH/X11 connection.
* Fixed a problem with colour maps/luts not being listed in command line help.
* Fixed a bug with the location panel *History* tab when running under
  Python 2.


Deprecated
^^^^^^^^^^


* :class:`fsleyes.overlay.PropCache` - an equivalent class is now available
  in |props_doc|.



0.21.1 (Monday February 5th 2018)
---------------------------------


* Adjustments to standalone linux builds, hopefully fixing the ``module 'wx'
  has no attribute '__version__'`` issue.


0.21.0 (Tuesday January 30th 2018)
----------------------------------


* FSLeyes is now able to load Freesurfer surface files, and ``mgh`` / ``mgz``
  images.
* The vertices of a 3D mesh (VTK, GIFTI, or Freesurfer file) can now be
  selected in both 3D and ortho views by holding down the shift key. If data
  is associated with the mesh vertices, it will be shown in the location
  panel, the time series panel, and the power spectrum panel. This feature is
  dependent on the presence of the `Trimesh
  <https://github.com/mikedh/trimesh/>`_ library, a new optional dependency.
* Mesh vertex data is now shown on the histogram panel.
* It is now possible to associate multiple vertex files with mesh overlays.
  For Freesurfer/GIFTI surfaces, if other vertex files are found (e.g. pial,
  white matter, inflated), they will be added as options.
* Docked FSLeyes control panels can now be minimised by dragging the dock
  separator.
* The 3D view now has a toolbar, and standard panels when it is opened.
* The ``--version``, ``--help`` and ``--fullhelp`` command line arguments
  can now be used on systems which do not have a display, and without Xvfb.
* Initial display range for all ``volume`` overlays can now be set as a
  percentile, via the global ``--initialDisplayRange`` command line argument.
* A small bugfix to 2D mesh outline drawing with weird reference image
  orientations.
* Default 3D volume settings have been increased when running in an SSH/X11
  environment.
* Fixed some bugs with mask outline view.


0.20.1 (Friday January 11th 2018)
---------------------------------


* Fixed an issue with ``label`` overlays - the outline and width settings
  defaulted to being synchronised across images.
* FSLeyes dependencies are now separated into core, optional and development
  dependencies.
* Adjustments to standalone build environment.


0.20.0 (Wednesday January 10th 2018)
------------------------------------


* The location panel now has a *history* section, which contains a list of
  previously visited locations.
* Volume display range can now be specified as a percentile on the command
  line
* Colour maps and lookup table files can now be specified on the command line.
* The ``--vertexData`` command line argument, for mesh overlays, can be
  specified multiple times. All vertex data files will be pre-loaded, and the
  first one will be selected.
* New options on mask overlays to display the mask outline, and to apply
  interpolation on the display.
* The threshold range for mask overlays is now **exclusive** - now, only
  values which are within the threshold limits are displayed.  Previously,
  values which were within or equal to the limits were displayed.
* :class:`.Profile` instances can now notify arbitrary listeners of mouse and
  keyboard events, instead of only notifying via sub-class methods.


0.19.1 (Wednesday January 3rd 2018)
-----------------------------------


* Small fix related to per-view selected overlays.
* Adjustments to per-view volume linking.


0.19.0 (Wednesday January 3rd 2018)
-----------------------------------


* Volumetric DICOM data series can now be loaded into FSLeyes, via
  the *File* |right_arrow| *Add from DICOM* menu option. The
  DICOM to NIFTI conversion is performed using Chris Rorden's
  `dcm2niix <https://github.com/rordenlab/dcm2niix/>`_ tool.
* The selected overlay can now be different in different FSLeyes views.
* Volume/timepoint properties can now be linked across views independently of
  other display properties. This is accessible via a new setting *Link overlay
  volume settings* in the view settings panel.
* All new overlays are now linked by default. This is so that the volumes
  for 4D images will be synchronised by default.
* Ortho edit mode has a new *Invert selection* option.
* Bug fix in time series and histogram panels regarding non-Image overlays
  (e.g. surfaces).
* Work around in screenshot logic for a bug in matplotlib (see
  https://github.com/matplotlib/matplotlib/pull/10084).


0.18.2 (Thursday December 7th 2017)
-----------------------------------


* Fixed another bug drawing ``label`` overlays - were not being drawn
  correctly when both image and LUT had low number of labels.


0.18.1 (Wednesday December 6th 2017)
------------------------------------


* Fixed bug in ``render`` (introduced by new ``--selectedOverlay`` command
  line option)


0.18.0 (Wednesday December 6th 2017)
------------------------------------


* Fixed issue linking to the ``freeglut`` library on linux builds.
* Fixed bug drawing ``label`` overlays on lightbox views - outlines
  were not being drawn.
* A couple of wxPython 3.0.2.0 compatibility bug-fixes.
* Fixed bug in :class:`.ResampleAction` - was crashing on 4D images.
* Fixed bug in :class:`.ColourBarCanvas` - was trying to draw before
  colour bar texture had been created.
* The :func:`~fsleyes.actions.screenshot.screenshot` function is
  now available in the shell environment (in the :class:`.ShellPanel`,
  and in scripts executed by the :class:`.RunScriptAction`).
* New command line option ``--selectedOverlay`` to specify the
  selected overlay.
* The :class:`.TimeSeriesPanel` honours the NIFTI ``toffset`` field.
* New histogram option :attr:`.HistogramPanel.plotType`, to choose
  between plotting bin edges or bin centres.
* The :attr:`.HistogramSeries.nbins` property now has a maximum
  value of 1000, and will also accept larger values.
* The :class:`.SliceCanvas` no longer resets the pan/zoom settings
  when an overlay is added/removed.
* The `xnat <https://bitbucket.org/bigr_erasmusmc/xnatpy>`_ and
  `wxnatpy <https://github.com/pauldmccarthy/wxnatpy>`_ dependencies
  are now optional - the *Load overlay from XNAT* option will be disabled
  if these dependenceies are not present.
* New option to generate animated GIFs (see the :class:`.MovieGifAction`).
  The :func:`.movieGif` function is available in the shell environment.
* Plot panels no longer draw tick lines when ticks are disabled.


0.17.2 (Wednesday November 15th 2017)
-------------------------------------


* Fixed API documentation generation


0.17.1 (Monday Novermber 13th 2017)
-----------------------------------


* Fixed screenhot bug (related to :meth:`.CanvasPanel.colourBarCanvas`
  property).


0.17.0 (Sunday November 12th 2017)
----------------------------------


* Adjustments to the use of ``GL_LUMINANCE`` textures - they are now
  only used as a fallback if there are are absolutely no other options,
  as they do not display correctly on some more recent GL drivers.
* Improved the version update notification dialog.
* Fixed use of the ``help`` function in the python shell.
* The :attr:`.Volume3DOpts.dithering` property, and the ``--dithering``
  command line option are now deprecated - a suitable dithering level
  is now automatically determined.
* Removed some XNAT account credentials which were accidentally hard-coded.



0.16.0 (Tuesday October 31st 2017)
----------------------------------


* Removed the ``--skipupdatecheck`` command line option - the default
  behaviour is now *not* to check for updates on startup. This can be
  enabled via the new ``--updatecheck`` option.
* Added the ability to load images from an XNAT server.
* Application font size can now be set via the ``--fontSize`` command line
  option.
* 3D volume clipping planes can now be applied as the intersection (default),
  union or complement of all active clipping planes.
* Bugfix in CLI generation - ``--overrideDataRange`` option does not get
  generated if data range override is disabled.
* Display space warning popups/changes are no longer used - instead, a little
  warning message is shown alongside a button that allows the user to change the
  display space manually.


0.15.2 (Friday November 24th 2017)
----------------------------------


* A couple of wxPython 3.0.2.0 compatibility bug-fixes (backported from
  0.18.0).


0.15.1 (Saturday October 7th 2017)
----------------------------------


* Crop image dialog now has ability to load/save crop parameters
* New 'resample' tool, allowing an image to be resampled to another
  resolution.


0.15.0 (Thursday September 21st 2017)
-------------------------------------


* Removed ``NiftiOpts.customXform`` property. Volume overlays can
  now be aligned to a reference image by setting the ``transform``
  property to ``'reference'``. Volume to reference transformation
  is now handled by individual ``NiftiOpts`` instances, rather than
  centrally by the ``DisplayContext``.
* Fix to canvas screenshot save - was always saving to current working
  directory.
* Nudge panel now displays a warning if the display space is set
  such that transform changes would not be seen.
* Various bug fixes to command line generation - ``--orientFlip``,
  ``--fgColour``, ``--displaySpace``, and overlay order.
* Fix to pyinstaller/CentOS7 build.
* Fix to image display on some VM environments - images were displayed
  at low contrast due to use of luminance texture.



0.14.2 (Wednesday September 13th 2017)
--------------------------------------


* Bugfix to vector image handling, caused by 4D addition in 0.14.1
* Improvements to performance of histogram panel



0.14.1 (Monday September 11th 2017)
-----------------------------------


* Support for images with more than 4 dimensions.
* Overlay display panel has a 'dimension' spin control for images,
  allowing the volume value to control different dimensions.


0.14.0 (Thursday August 24th 2017)
----------------------------------


* Display space is no longer a global setting, but can be changed
  independently on different views.
* 3D view always displays in world coordinate system
* Added command line interface for 3D view and overlay settings
* Changes to command line for setting ortho centr
* VEST lookup table files are no longer normalised when loaded
* Canvases now have a foreground colour option, which controls text,
  cursor, etc.



0.13.1 (Monday August 14th 2017)
--------------------------------


* Movie mode working in 3D
* Histogram view has ability to calculate histogram from an ROI
* Fixes to handling of GL canvas/colour bar background colour
* Screenshots can now be generated from a script/shell
* Line vector width is now floating point rather than integer


0.13.0 (Thursday August 10th 2017
---------------------------------


* New 3D view, with volume ray-casting and mesh visualisation
* OpenGL 1.4 ARB shader program parser now allows sub-routines with
  arbitrarily named parameters
* Overlay display panel code refactored to make it easier to customise


0.12.4 (Friday July 14th 2017)
------------------------------


* New 'Tools' menu, intended for things which don't fit anywhere else.
* Apply/save FLIRT transform, and seed correlation menu options moved to
  new Tools menu.
* Time series view has a feature to generate mean time series from a mask
* New HSV colour map
* Order of paths in 'recent paths' menu inverted.
* Fix an issue with py2app command line handling under python 3


0.12.3 (Monday June 12th 2017)
------------------------------


* Fixes to macOS build


0.12.2 (Monday June 12th 2017)
------------------------------


* Voxels with a value of NaN are now clipped for volume overlays
* Bug fixes to melodic classification panel


0.12.1 (Sunday June 11th 2017)
------------------------------


* Bug fix to histogram auto-bin option for images with no data range
* Allow Unicode characters in GLSL shader files
* Changes to FSLeyes build process


0.12.0 (Sunday June 4th 2017)
-----------------------------


* Fixed screenshot under Python 3
* Changes to FSLeyes assets directory (icons, data files, etc)
* Changes to FSLeyes build process


0.11.0 (Saturday May 27th 2017)
-------------------------------


* Re-added 'Reset display range' button to toolbar for volume overlays
* Lightbox panel now defaults to Z axis
* Fixed icon button centering under OSX
* Fixes to execution and screenshot generation to work around issues
  in remote (vnc/x2go) execution environments.
* FSLeyes settings are now stored in user's home directory on all
  platforms.
* Fixes to off-screen orthographic and lightbox rendering
* Fixes to ortho edit mode 'target image' option
* Many python 2/3, and wxPython 3/4 compatibility fixes


0.10.1 (Thursday April 20th 2017)
---------------------------------


* First public release as part of FSL 5.0.10
* Melodic classificaiton panel can now be used with any 4D image,
  not just ``melodic_IC`` images.
* Bug fix to edit mode - was broken for 4D images
* Volume clipping range can now be specified as a percentile on the command
  line
