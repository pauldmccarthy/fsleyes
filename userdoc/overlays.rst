.. |right_arrow| unicode:: U+21D2


.. _overlays:

Overlays
========


FSLeyes refers to the files that you load as *overlays*. FSLeyes |version| is
capable of loading the following types of data:

 - NIFTI image files (``.nii``, ``.nii.gz``).

 - `FEAT <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FEAT>`_ analysis directories
   (``.feat``).

 - `MELODIC <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/MELODIC>`_ analysis
   directories (``.melodic``).

 - `dtifit <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#DTIFIT>`_
   output directories. 
   
 - VTK files (``.vtk``) which are in a format similar to that produced by the
   `FIRST <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST>`_ sub-cortical
   segmentation tool.


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


Overlay types
-------------


NIFTI images can be displayed in a variety of different ways, depending on the
nature of the image, and on how you want to display it. The way in which an
overlay is displayed is called the *overlay type*.


When you select an overlay, or change the type of an overlay, the contents of
the :ref:`overlay toolbar <ortho_lightbox_controls_overlay_toolbar>` will
change to display commonly used settings for that overlay. All display
settings for the currently selected overlay are available in the :ref:`overlay
display panel <ortho_lightbox_controls_overlay_display_panel>`.


Volume
^^^^^^


This is the default (and most conventional) display type for NIFTI
images. Image intensity values are coloured according to a colour map. Many
settings are available to control how an image is displayed.


.. container:: image-strip

  .. image:: images/overlays_volume1.png
     :width: 25%

  .. image:: images/overlays_volume2.png
     :width: 25% 

  .. image:: images/overlays_volume3.png
     :width: 25% 
 

Label
^^^^^


This type is useful for viewing NIFTI images which contain discrete integer
values (*labels*), such as atlases and (sub-)cortical segmentation summary
images. Each label is displayed in a different colour, and the regions can
either be shown filled, or with the outline only.  Label colours can be
customised using the :ref:`lookup table panel
<ortho_lightbox_controls_lookup_table_panel>`.


.. container:: image-strip
   
   .. image:: images/overlays_label1.png
      :width: 25%

   .. image:: images/overlays_label2.png
      :width: 25% 


Mask
^^^^


This type is useful if you want to display an image as a binary mask. You can
display any NIFTI image as a mask - not just binary images. The
minimum/maximum thresholds used to define the voxels which are included in the
mask can be adjusted, as can the mask colour.



.. container:: image-strip
   
   .. image:: images/overlays_mask1.png
      :width: 25%

   .. image:: images/overlays_mask2.png
      :width: 25%

   .. image:: images/overlays_mask3.png
      :width: 25% 


Vector
^^^^^^


4D NIFTI images which contain exactly three 3D volumes may be interpreted as a
*vector* image where, at each voxel, the three volumes contain X, Y and Z
coordinates specifying the magnitude and direction of a vector at that voxel.
For example, the `dtifit
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#DTIFIT>`_ tool outputs
diffusion tensor eigenvectors, and the `bedpostx
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#BEDPOSTX>`_ tool outputs
mean principal diffusion directions, as vector images.


A vector image can be displayed in one of two ways - as a *RGB* vector, or as
a *line* vector. In a RGB vector image, each voxel is coloured according to
the magnitude of the X, Y, and Z vector components. The default colours are
(respectively) red green and blue, but these can be customised or disabled. If
you have another image in the same space (e.g. a FA or MD map), you can
modulate the brightness of the vector colours in each voxel according to the
values in the other image:


.. container:: image-strip

  .. image:: images/overlays_rgbvector1.png
     :width: 25%

  .. image:: images/overlays_rgbvector2.png
     :width: 25%

  .. image:: images/overlays_rgbvector3.png
     :width: 25%


In a line vector image, the vector at each voxel is displayed as a line, and
usually coloured in the same manner as for a RGB vector. Line width and
lengths can be scaled by a constant factor, and the vector values can be
displayed with their individual magnitudes, or all scaled to unit length:


.. container:: image-strip

  .. image:: images/overlays_linevector1.png
     :width: 25%

  .. image:: images/overlays_linevector2.png
     :width: 25%

  .. image:: images/overlays_linevector3.png
     :width: 25% 


Tensor
^^^^^^


Spherical harmonic
^^^^^^^^^^^^^^^^^^


The display space
-----------------


Coordinate systems
------------------

