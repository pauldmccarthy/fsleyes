This document contains the ``fsleyes`` release history in reverse
chronological order.


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
