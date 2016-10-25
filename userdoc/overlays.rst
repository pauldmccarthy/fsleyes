.. |right_arrow| unicode:: U+21D2


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
overlay is displayed is called the *overlay type* or the *display type*.


When you select an overlay, or change the type of an overlay, the contents of
the :ref:`overlay toolbar <todo>` will
change to show commonly used display settings for that overlay. All display
settings for the currently selected overlay are available in the :ref:`overlay
display panel <todo>`.


Volume
^^^^^^


This is the default (and most conventional) display type for NIFTI
images. Image intensity values are coloured according to a colour map. Many
settings are available to control how an image is displayed - these are
accessed through the :ref:`overlay display panel
<todo>`.


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
either be shown filled, or with just the outline.  Label colours can be
customised, and invidiual labels toggled on and off, using the :ref:`lookup
table panel <todo>`.


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
*vector* image where, at each voxel, the three volumes respectively contain X,
Y and Z coordinates specifying the magnitude and direction of a vector at that
voxel.  For example, the `dtifit
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#DTIFIT>`_ tool outputs
diffusion tensor eigenvectors, and the `bedpostx
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#BEDPOSTX>`_ tool outputs
mean principal diffusion directions, as vector images.


A vector image can be displayed in one of two ways - as a *RGB* vector, or as
a *line* vector. In a RGB vector image, each voxel is coloured according to
the magnitude of the X, Y, and Z vector components. The default colours are
(respectively) red green and blue, but these can be customised or individually
disabled. If you have another image in the same space (e.g. a FA or MD map),
you can modulate the brightness of the vector colours in each voxel according
to the values in the other image.


.. container:: image-strip

  .. image:: images/overlays_rgbvector1.png
     :width: 25%

  .. image:: images/overlays_rgbvector2.png
     :width: 25%

  .. image:: images/overlays_rgbvector3.png
     :width: 25%


In a line vector image, the vector at each voxel is displayed as a line, and
usually coloured in the same manner as for a RGB vector. Line width and length
can be scaled by a constant factor, and the vector values can be displayed
with varying lengths (according to their individual magnitudes), or all scaled
to have the same length.


.. container:: image-strip

  .. image:: images/overlays_linevector1.png
     :width: 25%

  .. image:: images/overlays_linevector2.png
     :width: 25%

  .. image:: images/overlays_linevector3.png
     :width: 25% 


Tensor
^^^^^^


Directories which contain `dtifit
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/UserGuide#DTIFIT>`_ output, and
images which contain exactly 6 volumes can be displayed as *tensors*, where
the diffusion magnitude, anisotropy, and orientation within each voxel is
modelled with a tensor matrix, which can be visualised as an ellipsoid. Most
of the display settings which can be applied to vector images are also
applicable to tensor overlays.


.. container:: image-strip

  .. image:: images/overlays_tensor1.png
     :width: 25%

  .. image:: images/overlays_tensor2.png
     :width: 25%

  .. image:: images/overlays_tensor3.png
     :width: 25% 


Spherical harmonic
^^^^^^^^^^^^^^^^^^


Images which appear to contain [*]_ spherical harmonic (SH) coefficients for
spherical deconvolution-based diffusion modelling techniques [*]_ can be
displayed as spherical harmonic functions. Many of the display properties
which can be applied to vector images can also be applied to SH images. The
fibre orientation distributions (FODs) within each voxel can be coloured
according to their orientation, or to the magnitude of their radius.


.. note:: The lighting model used for SH overlays in FSLeyes |version| is
          broken, as I haven't figured out a way to implement lighting on FODs
          in an efficient manner.


.. container:: image-strip

  .. image:: images/overlays_sh1.png
     :width: 25%

  .. image:: images/overlays_sh2.png
     :width: 25%

  .. image:: images/overlays_sh3.png
     :width: 25%


.. [*] 4D images which contain 1, 6, 15, 28, 45, 66, 91, 120, or 153 volumes
       can be displayed as symmetric SH functions (i.e. the file contains
       coefficients for even spherical functions only). 4D images which
       contain 1, 9, 25, 49, 81, 121, 169, 225, or 289 volumes can be
       displayed as asymmetric SH functions (i.e. the file contains
       coefficients for both odd and even spherical functions).


.. [*] Spherical Deconvolution (SD) and Constrained Spherical Deconvolution
       (CSD) methods use spherical harmonic functions to represent the fibre
       orientation distribution (FOD), based on diffusion imaging data, within
       each voxel. For more details. refer to:
       
       J.-Donald Tournier, Chun-Hung Yeh, Fernando Calamante, Kuan-Hung Cho,
       Alan Connelly, Ching-Po Lin, `Resolving crossing fibres using
       constrained spherical deconvolution: Validation using
       diffusion-weighted imaging phantom data`, NeuroImage, Volume 42, Issue
       2, 15 August 2008, Pages 617-625, ISSN 1053-8119,
       http://dx.doi.org/10.1016/j.neuroimage.2008.05.002.


VTK model
^^^^^^^^^


FSLeyes is able to display `VTK legacy files
<http://www.vtk.org/wp-content/uploads/2015/04/file-formats.pdf>`_ which
specify a triangle mesh in the ``POLYDATA`` data format [*]_. Files of this
type are generated by the `FIRST
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST>`_ sub-cortical segmentation
tool, to represent sub-cortical structures.  VTK models can be shown either
filled, or with just the outline.


FSLeyes cannot automatically determine the coordinate system that is used in a
VTK model file. For this reason, in order to ensure that a model is displayed
in the correct space, you must associate a *reference image* with each VTK
model. For example, if you have performed sub-cortical segmentation on a T1
image with FIRST, you would associate that T1 image with the resulting VTK
model files [*]_.


.. container:: image-strip

  .. image:: images/overlays_vtkmodel1.png
     :width: 25%

  .. image:: images/overlays_vtkmodel2.png
     :width: 25%


.. [*] Future versions of FSLeyes will include support for more VTK data
       formats.


.. [*] Future versions of FSLeyes will attempt to automatically determine the
       reference image for VTK models when you load in the file(s).
   

The display space
-----------------


FSLeyes works under the assumption that all of the overlays you load are
defined in the same space. For example, if you load a T1 image and a T2*
image, FSLeyes will attempt to overlay them on top of one another, even if
they have different resolution or orientation. By default, FSLeyes will
display all overlays in terms of a single reference overlay, typically the
first one that you load; all other overlays are transformed into the space of
this reference overlay. You can change the reference overlay via the
:ref:`display settings panel <todo>`.


.. container:: image-strip
               
  .. image:: images/overlays_display_space1.png
     :width: 25%
             
  .. image:: images/overlays_display_space2.png
     :width: 25% 


If you are having trouble with mis-aligned images, or are interested in how
FSLeyes works, refer to the page on :ref:`the display space <display_space>`.
