.. _display_space:

The display space
=================


.. note:: This is an advanced topic and can safely be skipped over, unless you
          are having problems with images not being overlaid on top of each
          other, or if you are particularly curious.


Overview
--------

          
FSLeyes assumes that all of the overlays you load are defined in the same
space. If this assumption holds, FSLeyes will align all of your overlays on
the display, even if they have different resolution or orientation. 


For NIFTI images, FSLeyes accomplishes this by using the transformation
matrices (the ``qform`` and/or ``sform`` fields) defined in the NIFTI file
header. These transformation matrices are used to convert voxel, or data,
coordinates into display, or "world", coordinates.  For VTK models, FSLeyes
uses the the transformation matrix of that model's reference image to position
the VTK model in the display coordinate system.


FSLeyes allows you to choose between displaying your overlays in terms of one
:ref:`reference image <display_space_reference_image_space>`, or displaying
all overlays in :ref:`world space <display_space_world_space>`.


This page contains ...


.. _display_space_nifti_image_orientation: 

NIFTI image orientation
-----------------------


Two coordinate systems - voxel / world


.. _display_space_data_storage_order: 

Data storage order
^^^^^^^^^^^^^^^^^^

The voxel intensities in a 3D NIFTI image are stored as a big one-dimensional
list of numbers. Without the dimension and orientation information in the
NIFTI file header, we would not be able to determine where those numbers
should be located in the brain.


All 3D NIFTI images, are stored such that the :math:`x` dimension is the
*fastest changing*, and the :math:`z` dimension the *slowest changing*. For
example, if we have an image with dimensions :math:`[d_x=3, d_y=2, d_z=2]\ `,
the image data, as stored on disk, would correspond to voxel coordinates like
so (the index :math:`i` refers to the location, in the file, of the intensity
for each voxel) [*]_:

             
=========  =========  =========  ========= 
:math:`i`  :math:`x`  :math:`y`  :math:`z`
=========  =========  =========  ========= 
0          0          0          0
1          1          0          0
2          2          0          0
3          0          1          0
4          1          1          0
5          2          1          0
6          0          0          1
7          1          0          1
8          2          0          1
9          0          1          1
10         1          1          1
11         2          1          1
=========  =========  =========  ========= 


It is easy to calculate the index :math:`i` of a voxel from its coordinates:

.. math::
   
   i = x + (y\times d_x) + (z\times d_x\times d_y)



.. [*] In `FSL <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_, in C and Python,
       and hence with ``nibabel``, voxel coordinates and indices begin from 0.
       However, if you were to load a NIFTI image into MATLAB, the voxel
       coordinates and indices would begin from 1.

   
.. _display_space_voxel_coordinate_system:

Voxel coordinate system
^^^^^^^^^^^^^^^^^^^^^^^
            

.. |nibabel| replace:: ``nibabel``
.. _nibabel: http://nipy.org/nibabel/


The voxel coordinate system of a NIFTI image defines how the voxel intensities
of that image were acquired, and how they are stored and accessed in the image
file.  For example, if you load the MNI152 2mm template (which has dimensions
:math:`[d_x=91, d_y=109, d_z=91]\ `):


 - Coordinates :math:`[x=0, y=0, z=0]\ ` would refer to the first voxel stored
   in the file.

 - Coordinates :math:`[x=16, y=20, z=8]\ ` would refer to the 81189th voxel
   (see :ref:`above <display_space_data_storage_order>`):

   .. math::

      16 + (20\times 91) + (8\times 91\times 109) = 81188


 - Coordinates :math:`[x=90, y=108, z=90]\ ` would refer to the 902629th voxel
   (the last voxel in the file):

   .. math::

      90 + (108\times 91) + (90\times 91\times 109) = 902628


.. _display_space_world_coordinate_system:

World coordinate system
^^^^^^^^^^^^^^^^^^^^^^^


The NIFTI specification allows you to store two affine transformation matrices
in the header of a NIFTI image. These matrices, referred to as the ``qform``
and ``sform``, are intended to be used for encoding a transformation from
voxel coordinates into some other coordinate system. The ``qform`` and ``sform``
are commonly used to encode a transformation from voxel coordinates into:


- The coordinate system of a standard template such as MNI152 or Talairach
  space.
- The coordinate system of the MRI scanner in which the image the image was
  acquired.


While, in theory, you can store two independent transformations in a NIFTI
image header, FSL generally sets both the ``qform`` and ``sform`` to the same
transformation.  In FSLeyes, the target space of this transformation (i.e.
the space into which voxel coordinates are transformed) is referred to as the
*world coordinate system* of that image. Critically, FSLeyes assumes that
every image you load shares the same world coordinate system.


.. _display_space_radiological_vs_neurological:

Radiological vs neurological
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These terms are an endless source of confusion in neuro-image analysis. They
are used to refer to the orientation of an image in three scenarios:

- **Voxel storage order**: How the image voxel intensities are stored on disk,
  e.g.. does the voxel X axis increase from left to right, or right to left?

  

The `NIFTI specification <https://nifti.nimh.nih.gov/nifti-1>`_ does not
impose any requirements upon the anatomical orientation of the voxel
coordinate system. However, it is relatively common to see NIFTI images for
which:

- The voxel X axis corresponds to the left-right axis
- The voxel Y axis corresponds to the posterior-anterior axis 
- The voxel Z axis corresponds to the inferior-superior axis


  
- **Image world coordinate system** How the 

- **Display orientation** How the image is displayed, i.e. is the subject's
  left shown to the left of the display, or to the right of the display?


             Three different meanings:
              - Voxel storage order
              - World coordinate system orientation
              - Display orientation

             First two - radiological -> RAS



.. _display_space_scaled_voxel_coordinate_system: 
  
Scaled voxel coordinate system
------------------------------


*Scaled voxels* refers to a coordinate system whereby the :math:`x`,
:math:`y`, and :math:`z` voxel coordinates of an image are respectively scaled
by the voxel size along each dimension. The size of one voxel along each voxel
dimension is stored in the NIFTI header; these sizes are often referred to as
the image *pixdims* and, for brain images, are typically specified in
millimetres.


In FSLeyes, the scaled voxel coordinate system for an image also includes an
implicit flip along the X voxel dimension (which generally corresponds to the
left-right axis), **if** the image data storage order appears to be
neurological (see :ref:`below <display_space_radiological_vs_neurological>`
for more details). This X axis flip is very important, because many `FSL
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_ tools use this scaled voxel
coordinate system. For instance, this is the coordinate system used by
`FSLView <http://fsl.fmrib.ox.ac.uk/fsl/fslview/>`_, by `FLIRT
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT>`_, and in the VTK sub-cortical
segmentation model files output by `FIRST
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST>`_.


Furthermore, the vectors in eigenvector images images output by the `FDT
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/>`_ ``dtifit`` tool are oriented
according to this space, so if the input data is in neurological orientation,
these vectors need to be inverted along the x axis.


When FSLeyes displays the loaded overlays in terms of a :ref:`reference image
<display_space_reference_image_space>`, the display coordinate system is
changed so that it corresponds to the scaled voxel coordinate system of the
reference image.



.. _display_space_display_coordinate_system:

Display coordinate system
-------------------------


.. _display_space_reference_image_space:

Reference image space
---------------------


FSLeyes has two main display modes - *reference image* space, and *world*
space (described :ref:`below <display_space_world_space>`). You can change the
display space via the :ref:`view settings panel
<ortho_lightbox_views_view_settings>`.


By default, FSLeyes displays all overlays in terms of a single overlay, which
is typically the first one that you load. If this overlay is a NIFTI image, it
will be displayed in *scaled voxels*, where the three display axes correspond
to the image data axes (i.e. the order in which the voxel intensities are is
stored in the image file).



i.e.  the image voxel coordinate system is orthogonal to the display
coordinate system, and they share the same origin [*]_.  All other overlays
are transformed into the scaled voxel space of the reference overlay so they
will be aligned on the screen.




.. [*] If your reference image is stored in the same manner as the MNI152
       standard space image (e.g. if you have run the `fslreorient2std` tool
       on it), the three display space axes will correpond to the sagittal,
       coronal, and axial axes, respectively.


.. _display_space_world_space: 

World space
-----------
