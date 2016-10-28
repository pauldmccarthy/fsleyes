.. _plot_views:

Plotting views
==============


.. image:: images/plot_views_time_series_example.png
   :width: 90%
   :align: center


FSLeyes |version| provides three plotting views:

- The :ref:`Time series <plot_views_time_series_view>` view plots voxel
  intensities from 4D NIFTI images. 

- The :ref:`Power spectra <plot_views_power_spectra_view>` view is similar to
  the time series view, but it plots time courses transformed into the
  frequency domain.

- The :ref:`Histogram <plot_views_histogram_view>` plots a histogram of the
  intensities of all voxels in a 3D NIFTI image (or one 3D volume of a 4D
  image).


All of these views have a similar interface, described :ref:`below
<plot_views_plotting_view_controls>`. Plotting views can plot data from
:ref:`multiple overlays <plot_views_overlay_list>` and :ref:`multiple voxels
<plot_views_plot_list>`, and you can also :ref:`import and export plotting
data <plot_views_importing_exporting_data>`.


.. _plot_views_time_series_view:

Time series view
----------------


The time series view plots voxel intensities from 4D NIFTI images. It is also
capable of displaying various :ref:`FEAT analysis <feat_mode>` outputs, and
:ref:`MELODIC component time courses <ic_classification>` - refer to those
pages for more details.


When you are viewing a 4D NIFTI image in an :ref:`orthographic or ligthbox
view <ortho_lightbox_views>`, the time series view will update as you change
the cursor location, to show the time course from the voxel (or voxels, if you
have more than one 4D image loaded) at the current location.


The plot control panel (described :ref:`below
<plot_views_plot_control_panel>`) contains some settings specific to time
series plots:


.. image:: images/plot_views_time_series_control.png
   :width: 50%
   :align: center


.. sidebar:: Percent-signal changed

             TODO describe method used
             

- **Plotting mode** This setting allows you to scale or normalise the time
  series which are displayed. You can plot the "raw" data, demean it,
  normalise it to the range ``[-1, 1]``, or scale it to
  percent-signal-changed (suitable for FMRI BOLD data).
  
- **Use pixdims** This setting is enabled by default. When enabled, the
  ``pixdim`` field of the time dimension in the NIFTI header is used to scale
  the time series data along the X axis. Effectively, this means that the X
  axis will show seconds. When disabled, the X axis corresponds to the volume
  index in the 4D image.
  
- **Plot component time courses for Melodic images**


.. _plot_views_power_spectra_view:

Power spectra view
------------------


.. side bar somewhere on how the power spectra transformation works



.. _plot_views_histogram_view:

Histogram view
--------------



.. _plot_views_plotting_view_controls:

Plotting view controls
----------------------


Controls common to all views blah-di-blah.


.. _plot_views_overlay_list:

The overlay list
^^^^^^^^^^^^^^^^

The overlay list available on plotting views is similar to the :ref:`one
available in orthographic/lightbox views <ortho_lightbox_views_overlay_list>`,
but provides less functionality:

- a
- b


.. _plot_views_plot_toolbar:

The plot toolbar
^^^^^^^^^^^^^^^^


.. _plot_views_plot_control_panel:

The plot control panel
^^^^^^^^^^^^^^^^^^^^^^


.. _plot_views_plot_list:

The plot list
^^^^^^^^^^^^^


.. _plot_views_importing_exporting_data:

Importing/exporting data
------------------------
