.. |right_arrow| unicode:: U+21D2
.. |information| unicode:: U+2139


.. _overlays:

Overlays
========


FSLeyes refers to the files that you load as *overlays*. FSLeyes |version| is
capable of loading the following types of data:

 - `NIFTI <https://nifti.nimh.nih.gov/>`_ image files (``.nii``, ``.nii.gz``).

 - `FEAT <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FEAT>`_ analysis directories
   (``.feat``).

 - `MELODIC <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/MELODIC>`_ analysis
   directories (``.melodic``).

 - `dtifit <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#DTIFIT>`_
   output directories. 
   
 - `VTK legacy files
   <http://www.vtk.org/wp-content/uploads/2015/04/file-formats.pdf>`_
   (``.vtk``) which are in a format similar to that produced by the `FIRST
   <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST>`_ sub-cortical segmentation
   tool.


NIFTI images can be displayed in a variety of different ways, depending on the
nature of the image data, and on how you want to display it. The way in which
an overlay is displayed is called the *overlay type* or the *display type*.
The most conventionaal overlay/display type for a NIFTI image is the
:ref:`volume <overlays_volume>`; the other types are described :ref:`below
<overlays_overlay_type>`.
   

.. _overlays_loading_an_overlay:

Loading an overlay
------------------


You can load an overlay by doing one of the following:

1. The *File* |right_arrow| *Add overlay from file* menu option allows you to
   choose a file to load (e.g. a ``.nii``, ``.nii.gz``, or ``.vtk`` file).

2. The *File* |right_arrow| *Add overlay from directory* menu option allows
   you to choose a directory to load (e.g. a ``.feat``, ``.ica``, or ``dtifit``
   directory).

3. The *File* |right_arrow| *Add standard* menu option allows you to choose a
   file from the ``$FSLDIR/data/standard/`` directory to load [*]_.

4. The + button on the overlay list allows you to choose a file to load.


.. [*] The *File* |right_arrow| *Add standard* menu option will be disabled
       if your FSL environment is not configured correctly.


.. _overlays_overlay_display_settings:

Overlay display settings
------------------------


When you select an overlay, or change the type of an overlay, the contents of
the :ref:`overlay display toolbar <overlays_overlay_display_toolbar>` will
change to show commonly used display settings for that overlay. All display
settings for the currently selected overlay are available in the :ref:`overlay
display panel <overlays_overlay_display_panel>`.


.. _overlays_overlay_display_toolbar:

The overlay display toolbar
---------------------------


The overlay display toolbar allows you to adjust basic display settings for
the currently selected overlay. Some settings are available for all overlay
types, whereas other settings will change depending on the type of the
selected overlay.


.. image:: images/overlays_overlay_toolbar.png
   :width: 80%
   :align: center

1. **Overlay display panel** Clicking on the gear button will open the
   :ref:`overlay display panel <overlays_overlay_display_panel>`.

2. **Overlay information** Clicking on the information button will open the
   :ref:`overlay information panel <overlays_overlay_information_panel>`.
   
3. **Overlay name** You can change the overlay name, as shown in the
   :ref:`overlay list panel <ortho_lightbox_views_overlay_list>` here.

4. **Overlay type** You can change the overlay type here.
   
5. **Opacity** This slider allows you to adjust the overlay
   opacity/transparency.
   
6. **Brightness/contrast** These sliders allow you to adjust the overlay
   brightness and contrast.
   
7. **Type-specific settings** The remaining controls will change depending on
   the type of the overlay. For :ref:`volume <overlays_volume>` overlays, as
   shown in the example above, display range and colour map controls are
   provided.

   
.. _overlays_overlay_display_panel:

The overlay display panel
-------------------------


The :ref:`overlay toolbar <overlays_overlay_display_toolbar>` allows you to
adjust basic display settings for the currently selected overlay. Many more
settings are available in the overlay display panel (accessed via the gear
button on the overlay toolbar):


.. image:: images/overlays_overlay_display_panel.png
   :width: 50%
   :align: center


The *General display settings* section at the top contains settings common to
all overlay types. The bottom section (*Volume settings* in this example)
contain settings which are specific to the type of the currently selected
overlay. The settings available for each overlay type are covered :ref:`below
<overlays_overlay_type>`.


.. _overlays_overlay_information_panel:

The overlay information panel
-----------------------------


Clicking the |information| button on the overlay toolbar brings up the overlay
information panel:


.. image:: images/overlays_overlay_display_panel.png
   :width: 50%
   :align: center


This panel contains basic information about the currently selected overlay,
such as its dimensions, file name, and transformation/orientation information.


.. _overlays_overlay_type:

Overlay types
-------------


.. _overlays_volume:

Volume
^^^^^^


.. container:: image-strip

  .. image:: images/overlays_volume1.png
     :width: 25%

  .. image:: images/overlays_volume2.png
     :width: 25% 

  .. image:: images/overlays_volume3.png
     :width: 25% 


This is the default (and most conventional) display type for NIFTI
images. Image intensity values are coloured according to a colour map. 
 

.. _overlays_label:

Label
^^^^^


.. container:: image-strip
   
   .. image:: images/overlays_label1.png
      :width: 25%

   .. image:: images/overlays_label2.png
      :width: 25% 


This type is useful for viewing NIFTI images which contain discrete integer
values (*labels*), such as atlases and (sub-)cortical segmentation summary
images. 


.. _overlays_mask:

Mask
^^^^


.. container:: image-strip
   
   .. image:: images/overlays_mask1.png
      :width: 25%

   .. image:: images/overlays_mask2.png
      :width: 25%

   .. image:: images/overlays_mask3.png
      :width: 25% 


This type is useful if you want to display an image as a binary mask. You can
display any NIFTI image as a mask - not just binary images. 


.. _overlays_vector:

Vector
^^^^^^


.. container:: image-strip

  .. image:: images/overlays_rgbvector1.png
     :width: 25%

  .. image:: images/overlays_rgbvector2.png
     :width: 25%

  .. image:: images/overlays_rgbvector3.png
     :width: 25%


.. container:: image-strip

  .. image:: images/overlays_linevector1.png
     :width: 25%

  .. image:: images/overlays_linevector2.png
     :width: 25%

  .. image:: images/overlays_linevector3.png
     :width: 25% 


4D NIFTI images which contain exactly three 3D volumes may be interpreted as a
*vector* image where, at each voxel, the three volumes respectively contain X,
Y and Z coordinates specifying the magnitude and direction of a vector at that
voxel.  A vector image can be displayed in one of two ways - as a *RGB*
vector, or as a *line* vector.


.. _overlays_tensor:

Tensor
^^^^^^


.. container:: image-strip

  .. image:: images/overlays_tensor1.png
     :width: 25%

  .. image:: images/overlays_tensor2.png
     :width: 25%

  .. image:: images/overlays_tensor3.png
     :width: 25%


Directories which contain `dtifit
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#DTIFIT>`_ output, and
images which contain exactly 6 volumes can be displayed as *tensors*, where
the diffusion magnitude, anisotropy, and orientation within each voxel is
modelled with a tensor matrix, which can be visualised as an ellipsoid.


.. _overlays_diffusion_sh:

Diffusion SH
^^^^^^^^^^^^


.. container:: image-strip

  .. image:: images/overlays_sh1.png
     :width: 25%

  .. image:: images/overlays_sh2.png
     :width: 25%

  .. image:: images/overlays_sh3.png
     :width: 25%


Images which appear to contain spherical harmonic (SH) coefficients for
spherical deconvolution-based diffusion modelling techniques can be displayed
as spherical harmonic functions.


.. _overlays_vtk_model:

VTK model
^^^^^^^^^


.. container:: image-strip

  .. image:: images/overlays_vtkmodel1.png
     :width: 25%

  .. image:: images/overlays_vtkmodel2.png
     :width: 25%


FSLeyes is able to display `VTK legacy files
<http://www.vtk.org/wp-content/uploads/2015/04/file-formats.pdf>`_ which
specify a triangle mesh in the ``POLYDATA`` data format [*]_. Files of this
type are generated by the `FIRST
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST>`_ sub-cortical segmentation
tool, to represent sub-cortical structures.

             
.. [*] Future versions of FSLeyes will include support for more VTK data
       formats.

.. For example, the `dtifit
.. <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#DTIFIT>`_ tool outputs
.. diffusion tensor eigenvectors, and the `bedpostx
.. <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#BEDPOSTX>`_ tool outputs
.. mean principal diffusion directions, as vector images.  

.. In a RGB vector image, each voxel is coloured according to
.. the magnitude of the X, Y, and Z vector components. The default colours are
.. (respectively) red green and blue, but these can be customised or individually
.. disabled. If you have another image in the same space (e.g. a FA or MD map),
.. you can modulate the brightness of the vector colours in each voxel according
.. to the values in the other image.

.. In a line vector image, the vector at each voxel is displayed as a line, and
.. usually coloured in the same manner as for a RGB vector. Line width and length
.. can be scaled by a constant factor, and the vector values can be displayed
.. with varying lengths (according to their individual magnitudes), or all scaled
.. to have the same length.



.. Images which appear to contain [*]_ spherical harmonic (SH) coefficients for
.. spherical deconvolution-based diffusion modelling techniques [*]_ can be
.. displayed as spherical harmonic functions. Many of the display properties
.. which can be applied to vector images can also be applied to SH images. The
.. fibre orientation distributions (FODs) within each voxel can be coloured
.. according to their orientation, or to the magnitude of their radius.


.. .. [*] 4D images which contain 1, 6, 15, 28, 45, 66, 91, 120, or 153 volumes
..        can be displayed as symmetric SH functions (i.e. the file contains
..        coefficients for even spherical functions only). 4D images which
..        contain 1, 9, 25, 49, 81, 121, 169, 225, or 289 volumes can be
..        displayed as asymmetric SH functions (i.e. the file contains
..        coefficients for both odd and even spherical functions).
..
.. .. [*] Spherical Deconvolution (SD) and Constrained Spherical Deconvolution
..        (CSD) methods use spherical harmonic functions to represent the fibre
..        orientation distribution (FOD), based on diffusion imaging data, within
..        each voxel. For more details. refer to:
..
..        J.-Donald Tournier, Chun-Hung Yeh, Fernando Calamante, Kuan-Hung Cho,
..        Alan Connelly, Ching-Po Lin, `Resolving crossing fibres using
..        constrained spherical deconvolution: Validation using
..        diffusion-weighted imaging phantom data`, NeuroImage, Volume 42, Issue
..        2, 15 August 2008, Pages 617-625, ISSN 1053-8119,
..        http://dx.doi.org/10.1016/j.neuroimage.2008.05.002.


.. FSLeyes cannot automatically determine the coordinate system that is used in a
.. VTK model file. For this reason, in order to ensure that a model is displayed
.. in the correct space, you must associate a *reference image* with each VTK
.. model. For example, if you have performed sub-cortical segmentation on a T1
.. image with FIRST, you would associate that T1 image with the resulting VTK
.. model files [*]_.
..
.. .. [*] Future versions of FSLeyes will attempt to automatically determine the
..        reference image for VTK models when you load in the file(s).
