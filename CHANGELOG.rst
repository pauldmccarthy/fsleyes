.. |right_arrow| unicode:: U+21D2


This document contains the ``fsleyes`` release history in reverse
chronological order.


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
