.. |FSL| replace:: FSL
.. _FSL: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/

.. |FSLView| replace:: FSLView
.. _FSLView: http://fsl.fmrib.ox.ac.uk/fsl/fslview/

.. |FLIRT| replace:: FLIRT
.. _FLIRT: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/

.. |FIRST| replace:: FIRST
.. _FIRST: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST/

.. |FDT| replace:: FDT
.. _FDT: http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FDT/

.. |nifti| replace:: NIFTI
.. _nifti: https://nifti.nimh.nih.gov/nifti-1

.. |nibabel| replace:: ``nibabel``
.. _nibabel: http://nipy.org/nibabel/


.. _display_space:

The display space
=================


This page contains an overview of the coordinate systems used in |nifti|_
images and in FSLeyes, and aims to clarify [*]_ some terms which you may have
come across in the FSLeyes documentation and source code.  This is an advanced
topic and can safely be skipped over, unless you are having problems with
images not being overlaid on top of each other, or if you are particularly
curious.


.. note:: If you are reading this page simply to learn how to make a specific
          image orthogonal to the display, all you need to do is select that
          image as the **Display space**, in the :ref:`view settings panel
          <ortho_lightbox_views_view_settings>`.


.. [*] While I am genuinely trying to clarify things on this page, there is a
       very good chance that I will just cause more confusion. Sorry about
       that.


Overview
--------


FSLeyes assumes that all of the overlays you load are defined in the same
space. If this assumption holds, FSLeyes will align all of your overlays in
the display, even if they have different resolution or orientation.


For NIFTI images, FSLeyes accomplishes this by using the transformation
matrices (the ``sform`` and/or ``qform`` fields) defined in the NIFTI file
header. These transformation matrices are used to convert voxel, or data,
coordinates into display, or "world", coordinates.  For other overlay types
(e.g. GIFTI and VTK meshes), FSLeyes uses the the transformation matrix of
that model's reference image to position the mesh in the display coordinate
system.


FSLeyes allows you to choose between displaying your overlays in terms of one
:ref:`reference image <display_space_reference_image_space>`, or displaying
all overlays in :ref:`world space <display_space_world_space>`. This setting
is called the *display space*, and you can change it independently for each
open view via the :ref:`view settings panel
<ortho_lightbox_views_view_settings>`.


.. _display_space_display_coordinate_system:

The FSLeyes display coordinate system
-------------------------------------


Regardless of whether you are displaying your images in *reference image
space* or in *world space*, FSLeyes refers to the space in which all of your
overlays are displayed as the *display coordinate system*. The display
coordinate system is the space in which images are shown on your computer
screen - in an :ref:`ortho view <ortho_lightbox_views_ortho>`, the three
canvases respectively display a slice through the X, Y, and Z planes of the
display coordinate system.


There is no explicit anatomical orientation in the display coordinate system -
this will depend on the value of the display space setting, and on the images
that you are viewing.


.. _display_space_reference_image_space:

Reference image space
^^^^^^^^^^^^^^^^^^^^^


By default, FSLeyes displays all overlays in terms of a single image, which is
typically the first one that you load; this image is referred to as the
*reference image*.


The reference image is displayed in *scaled voxels*.  *Scaled voxels* refers
to a coordinate system whereby the image voxel coordinate system is made
orthogonal to the display coordinate system, and the the X, Y,
and Z voxel coordinates are respectively scaled by the voxel size
along each dimension.  The size of one voxel along each voxel dimension is
stored in the NIFTI header; these sizes are often referred to as the image
*pixdims* and, for brain images, are typically specified in millimetres.


When FSLeyes displays your overlays in terms of a reference image, the display
coordinate system is changed so that it corresponds to the scaled voxel
coordinate system of that reference image; i.e. the image voxel coordinate
system is made orthogonal to the display coordinate system, and made to share
the same origin.  All other overlays are transformed into the scaled voxel
coordinate system of the reference overlay [*]_.


In FSLeyes, the scaled voxel coordinate system for an image also includes an
implicit flip along the X voxel dimension (which generally corresponds to the
left-right axis), **if** the image :ref:`data storage order
<display_space_data_storage_order>` appears to be neurological (see
:ref:`below <display_space_radiological_vs_neurological>` for more
details). This X axis flip is very important, because many |FSL|_ tools use
this scaled voxel coordinate system. For instance, this is the coordinate
system used by |FSLView|_, by |FLIRT|_, and in the VTK sub-cortical
segmentation model files output by |FIRST|_.


Furthermore, the vectors in eigenvector images images output by the |FDT|_
``dtifit`` tool are oriented according to this space, so if the input data is
in neurological orientation, these vectors need to be inverted along the X
axis (see the section on :ref:`line vector orientation
<troubleshooting_vector_orientation>` in the troubleshooting page for more
information).


.. [*] If your reference image is stored in the same manner as the MNI152
       standard space image (e.g. if you have run the `fslreorient2std` tool
       on it), the three axes of the display coordinate system will correpond
       to the sagittal, coronal, and axial axes, respectively.


.. _display_space_world_space:

World space
^^^^^^^^^^^


As an alternate to displaying all of your overlays in terms of a
:ref:`reference image <display_space_reference_image_space>`, you may choose
to display all of your images in the *world coordinate system*.  In this
scenario, the :ref:`display coordinate system
<display_space_display_coordinate_system>` is set to the :ref:`world
coordinate system <display_space_world_coordinate_system>` of the images you
are viewing.


.. _display_space_nifti_image_orientation:

NIFTI image orientation
-----------------------


Every NIFTI image is associated with two coordinate systems - the :ref:`voxel
coordinate system <display_space_voxel_coordinate_system>`, and the
:ref:`world coordinate system <display_space_voxel_coordinate_system>`.


.. _display_space_voxel_coordinate_system:

Voxel coordinate system
^^^^^^^^^^^^^^^^^^^^^^^


The voxel coordinate system of a NIFTI image defines how the voxel intensities
of that image were acquired, and how they are stored and accessed in the image
data.  For example, if you load the MNI152 2mm template (which has dimensions
:math:`[d_x=91, d_y=109, d_z=91]\ `):


 - Coordinates :math:`[x=0, y=0, z=0]\ ` would refer to the first voxel stored
   in the file.

 - Coordinates :math:`[x=16, y=20, z=8]\ ` would refer to the 81189th voxel
   (see the section on :ref:`data storage order
   <display_space_data_storage_order>`):

   .. math::

      16 + (20\times 91) + (8\times 91\times 109) = 81188


 - Coordinates :math:`[x=90, y=108, z=90]\ ` would refer to the 902629th voxel
   (the last voxel in the file):

   .. math::

      90 + (108\times 91) + (90\times 91\times 109) = 902628


The |nifti|_ specification does not impose any requirements upon the
anatomical orientation of the voxel coordinate system. However, in a research
environment, it is relatively common to see NIFTI images for which:

- The voxel X axis corresponds to the left-right axis
- The voxel Y axis corresponds to the posterior-anterior axis
- The voxel Z axis corresponds to the inferior-superior axis


.. _display_space_world_coordinate_system:

World coordinate system
^^^^^^^^^^^^^^^^^^^^^^^


The |nifti|_ specification allows you to store two affine transformation
matrices in the header of a NIFTI image. These matrices, referred to as the
``qform`` and ``sform``, are intended to be used for encoding a transformation
from voxel coordinates into some other coordinate system [*]_. The ``sform``
and ``qform`` are respectively intended to be used for encoding a
transformation from voxel coordinates into:


- The coordinate system of a standard template such as MNI152 or Talairach
  space.
- The coordinate system of the MRI scanner in which the image was acquired.


The |nifti|_ header also stores a code for both the ``sform`` and ``qform``
which specifies the target space of the transformation.


In FSLeyes, the target space of this transformation (i.e. the space into
which voxel coordinates are transformed) is referred to as the *world
coordinate system* of that image.  FSLeyes follows the same process as
``nibabel`` in choosing which voxel to world transformation matrix should be
used for an image (see
http://nipy.org/nibabel/nifti_images.html#the-nifti-affines):


  1. If the ``sform`` code is not ``NIFTI_XFORM_UNKNOWN``, use the
     sform matrix; else

  2. If the ``qform`` code is not ``NIFTI_XFORM_UNKNOWN``, use the qform
     matrix; else

  3. Use the *fall-back* matrix.


The *fall-back* matrix is a simple scaling matrix in which the size of a voxel
along each dimension is scaled by the ``pixdim`` fields in the |nifti|_
header.  The fall-back matrix used by FSLeyes differs to that used by
``nibabel``. In ``nibabel``, the origin (world coordinates (0, 0, 0)) is set
to the centre of the image. In FSLeyes, we set the world coordinate orign to
be the corner of the image, i.e. the corner of voxel (0, 0, 0).


The |nifti|_ specification requires that the world coordiate system of all
images are (approximately) oriented such that:

- The X axis increases from left ro right
- The Y axis increases from posterior to anterior
- The Z axis increases from inferior to superior

This is referred to as a RAS coordinate system (i.e. with the X, Y, and Z
coordinates increasing in the **R**\ ight, **A**\ nterior, **S**\ uperior
directions respectively)


 .. [*] For the purposes of these voxel to world coordinate transformations,
        voxel coordinates refer to the **centre** of the voxel.


.. _display_space_radiological_vs_neurological:

Radiological vs neurological
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These terms are an endless source of confusion in neuro-image analysis. They
refer to the left-right orientation of an image, and are used in at least
three scenarios:


- **Voxel storage order**: The image :ref:`voxel coordinate system
  <display_space_voxel_coordinate_system>` - how the image voxel intensities
  are stored on disk, e.g.. does the voxel X axis increase from left to right
  (neurological), or right to left (radioological)? [*]_


- **Image world coordinate system** The image :ref:`world coordinate system
  <display_space_world_coordinate_system>` - how the image is oriented in
  world coordinates (i.e. the image voxel coordinates, transformed via the
  image ``qform``/ ``sform`` transformation matrix). For all NIFTI images,
  this coordinate system is required to be neurological (RAS, as described
  :ref:`above <display_space_world_coordinate_system>`) [*]_.


- **Display orientation** How the image is displayed, i.e. is the subject's
  left shown to the left of the display (neurological), or to the right of the
  display (radiological)?  FSLeyes defaults to displaying images
  radiologically, but this can be changed via the :ref:`view settings panel
  <ortho_lightbox_views_view_settings>`.


.. [*] The voxel X axis may not even correspond to the anatomical left-right
       axis - recall the section on the :ref:`NIFTI voxel coordinate system
       <display_space_voxel_coordinate_system>`.

.. [*] But what makes things really confusing is the fact that the MNI152
       standard brain image (and thus all images stored with the same voxel
       orientation) has a *radiological* (LAS) voxel storage order!


.. _display_space_data_storage_order:

Data storage order
^^^^^^^^^^^^^^^^^^

The voxel intensities in a 3D NIFTI image are stored as a big one-dimensional
list of numbers. Without the dimension and orientation information in the
NIFTI file header, we would not be able to determine where those numbers
should be located in the brain.


All 3D NIFTI images are stored such that the X dimension is the *fastest
changing*, and the Z dimension the *slowest changing*. For example, if we have
an image with dimensions :math:`[d_x=3, d_y=2, d_z=2]\ `, the image data, as
stored on disk, would correspond to voxel coordinates like so (the index
:math:`i` refers to the location, in the file, of the intensity for each
voxel) [*]_:


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


And for completeness, the inverse calculation is also straightforward:

.. math::

   x &=               \big(i \mod (d_x \times d_y)\big) \mod d_x      \\
   y &= \Bigl\lfloor \frac{i \mod (d_x \times d_y)}{d_x} \Bigr\rfloor \\
   z &= \Bigl\lfloor \frac{i}     {d_x \times d_y}       \Bigr\rfloor \\



.. [*] In |FSL|_, C, Python, and |nibabel|_, voxel coordinates and indices
       begin from 0.  However, if you were to load a NIFTI image into MATLAB,
       the voxel coordinates and indices would begin from 1.


ANALYZE images
--------------


FSLeyes can load and display ANALYZE images (see the `SPM99 ANALYZE format
specification
<http://www.fil.ion.ucl.ac.uk/spm/software/spm99/#AzeFmt>`_). For these
images, FSLeyes uses a scaling matrix using the ``pixdim`` fields, with an
additional translation defined by the contents of the ``origin`` field . The
creation of this matrix is handled by ``nibabel`` (see
http://nipy.org/nibabel/reference/nibabel.analyze.html).

FSLeyes (and ``nibabel``) requires that all ANALYZE images have a voxel
coordinate system where:

 - The X axis increases from right to left
 - The Y axis increases from posterior to anterior
 - The Z axis increases from inferior to superior

In order to force the world coordinate system of ANALYZE images to be in RAS
orientation (and thus compliant with the `NIFTI specification
<display_space_world_coordinate_system>`_), negative ``pixdim`` values are
ignored by FSLeyes, and a left-right flip (on the X axis) is encoded into the
transformation.
