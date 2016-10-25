.. _display_space:

The display space
=================


.. note:: This is an advanced topic and can safely be skipped over, unless you
          are having problems with images not being overlaid on top of each
          other, or if you are particularly curious.

          
FSLeyes assumes that all of the overlays you load are defined in the same
space. If this assumption holds, FSLeyes will align all of your overlays on
the display, even if they have different resolution or orientation. 


For NIFTI images, FSLeyes accomplishes this by using the transformation
matrices (the ``qform`` and/or ``sform`` fields) defined in the NIFTI file
header. These transformation matrices are used to convert voxel, or data,
coordinates into display, or "world", coordinates.  For VTK models, FSLeyes
uses the the transformation matrix of that model's reference image to position
the VTK model in the display coordinate system.


By default, FSLeyes displays all overlays in terms of a single overlay, which
is typically the first one that you load. If this overlay is a NIFTI image, it
will be displayed in *scaled voxels*, where the three display axes correspond
to the image data axes (i.e. how the image data is stored in the image file)
[*]_, 


All other overlays are transformed into the scaled voxel space of the
reference overlay so they will be aligned on the screen.


.. [*] If your reference image is stored in the same manner as the MNI152
       standard space image (e.g. if you have run the `fslreorient2std` tool
       on it), the three display space axes will correpond to the sagittal,
       coronal, and axial axes, respectively.
