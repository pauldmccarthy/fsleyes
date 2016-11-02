.. |right_arrow|   unicode:: U+21D2
.. |right_arrow_2| unicode:: U+2192

.. _feat_mode:

Viewing FEAT analyses
=====================


FSLeyes has some features which can help you to view and explore the results
of your `FEAT <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FEAT>`_ analyses.


.. _feat_mode_loading_a_feat_analysis:

Loading a FEAT analysis
-----------------------


.. sidebar:: What does a FEAT analysis directory look like?

             FSLeyes detects FEAT directories based on the following rules.
             If any of these rules are not met, FSLeyes will not recognise
             your data as a FEAT analysis:

             - The directory name must end in ``.feat``
             - The directory must contain the following files:
               
              - ``filtered_func_data``: a NIFTI image containing the
                pre-processed input data (the file extension does not
                matter)
              - ``design.fsf``: FEAT configuration file
              - ``design.mat``: FEAT design matrix file
              - ``design.con``: FEAT contrast vector file
             

You can load a FEAT analysis in a few different ways [*]_:

- From the :ref:`command line <command_line>` - you can specify either a
  ``.feat`` directory::

      fsleyes path/to/my_analysis.feat

  Or the ``filtered_func_data`` image::
    
      fsleyes path/to/my_analysis.feat/filtered_func_data

- Via *File* |right_arrow| *Add overlay from directory* - select your
  ``.feat`` analysis directory.

- Via *File* |right_arrow| *Add overlay from file* - select the
  ``filtered_func_data`` image located in your ``.feat`` analysis directory.


In fact, you can load any NIFTI image contained within a ``.feat`` analysis
directory - FSLeyes will automatically detect that the image is part of a FEAT
analysis. However, the ``filtered_func_data`` image must be loaded in order to
view :ref:`time series and model fits
<feat_mode_viewing_model_fits_in_the_time_series_panel>`.


.. [*] FSLeyes |version| does not contain any special functionality for
       higher-level FEAT analyses (``.gfeat`` directories). But you can load
       and view the individual ``cope*.feat`` directories contained within a
       ``.gfeat`` directory. Future versions of FSLeyes will add
       functionality for working with group analyses.


.. _feat_mode_the_feat_perspective:

The FEAT perspective
--------------------


The FEAT perspective arranges the FSLeyes interface for viewing FEAT analyses.


.. image:: images/feat_mode_feat_perspective.png
   :width: 75%
   :align: center


The FEAT perspective simply adds a :ref:`cluster panel
<feat_mode_viewing_clusters_the_cluster_panel>`, and a :ref:`time series panel
<feat_mode_viewing_model_fits_in_the_time_series_panel>` to the :ref:`default
perspective <overview_default_perspective>`.


You can activate the FEAT perspective via the *View* |right_arrow|
*Perspectives* |right_arrow| *FEAT mode* menu item. Or you can tell FSLeyes to
start up with the FEAT perspective via the :ref:`command line <command_line>`
(the ``-s`` flag is short for ``--scene``)::
   
    fsleyes -s feat path/to/my_analysis.feat


.. _feat_mode_viewing_clusters_the_cluster_panel:
   
Viewing clusters (the cluster panel)
------------------------------------


If you have used `cluster thresholding
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FEAT/UserGuide>`_ in your FEAT
analysis, the cluster panel allows you to browse the clusters that were found
in each contrast of your analysis.


.. image:: images/feat_mode_cluster_panel.png
   :width: 80%
   :align: center


The controls at the top of the cluster panel allow you to:

- Change the contrast for which you are viewing cluster results.

- Load the Z statistic image for the current contrast. The image is displayed
  as a :ref:`volume overlay <overlays_volume>`.

- Load a cluster mask image for the current contrast. The image is displayed
  as a :ref:`label overlay <overlays_label>`, highlighting the clusters that
  were deemed significant for this contrast.


.. |cluster_link| replace:: FSL ``cluster`` tool
.. _cluster_link: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Cluster


The table in the cluster panel lists all of the clusters that were found to be
significant for the current contrast. The information shown in this table is
similar to that which can be generated with the |cluster_link|_.  The
|right_arrow_2| buttons embedded in the table allow you to move the display to
the following locations for a given cluster:


 - The location of the maximum Z value in the cluster
 - The location of the clutser's centre of gravity
 - The location of the maximum COPE value in the cluster


.. _feat_mode_viewing_model_fits_in_the_time_series_panel:

Viewing model fits in the time series panel
-------------------------------------------


The :ref:`time series view <plot_views_time_series_view>` contains
functionality specific to FEAT analyses. When the selected overlay is from a
FEAT analysis (and the ``filtered_func_data`` image from that analysis is
loaded), the time series view will plot the time series for the current voxel,
and will also plot the full GLM model fit for that voxel. You can also plot
several other types of data from a FEAT analysis, including explanatory
variables (EVs), parameter estimates (PEs) and contrasts of parameter
estimates (COPEs).


When an image from a FEAT analysis is selected, the :ref:`plot control panel
<plot_views_customising_the_plot_the_plot_control_panel>` adds a group of
settings allowing you to control what is plotted:


.. image:: images/feat_mode_time_series_feat_settings.png
   :width: 60%
   :align: center


- **Plot data** This setting is selected by default. When selected, the input
  data for the current voxel is plotted.
  
- **Plot full model fit** This setting is selected by default. When selected,
  the full model fit at the current voxel is plotted.
  
- **Plot residuals** When selected, the residuals of the full model fit (the
  noise) at the current voxel is plotted.
  
- **Plot partial model fit against** This setting allows you to plot a partial
  model fit against any of the PEs or COPEs in the analysis.
  
- **Plot EV** A checkbox is added for each EV in your design, allowing you to
  plot them alongside the data.
   
- **Plot PE fit** A checkbox is added for each PE in the analysis, allowing
  you to plot any of them at the current voxel.
  
- **Plot COPE fit** A checkbox is added for each COPE in the analysis,
  allowing you to plot any of them at the current voxel.
  
