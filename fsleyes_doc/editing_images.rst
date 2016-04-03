.. |command_key| unicode:: U+2318
.. |shift_key|   unicode:: U+21E7
.. |control_key| unicode:: U+2303
.. |alt_key|     unicode:: U+2325 
.. |right_arrow| unicode:: U+21D2


.. _editing-images:


Editing NIFTI images
====================


The ortho view has an *edit mode* which allows you to edit the values of NIFTI
overlays.


.. _editing-images-edit-toolbar:


Create a copy!
--------------


If you are worried about destroying your data, you may wish to create a copy
of your image, and edit that copy - you can do this via the *File*
|right_arrow| *Copy overlay* menu option.


The edit toolbar
----------------


.. TODO:: Image of edit toolbar goes here.


Open the edit toolbar (via the *Settings* |right_arrow| *Ortho view*
|right_arrow| *Edit toolbar* menu option), and click on the pencil button to
enter edit mode.

Modifying the data in an image is a two-stage process:

 1. Select the voxels you wish to change.
 
 2. Change the value of the selected voxels.


Selecting voxels
----------------


Voxels can be selected by right-clicking and dragging, or by holding down the
|command_key|/|control_key| and |shift_key| keys and left-clicking and
dragging.

Voxels can be de-selected by holding down the |command_key|/|control_key| and
|shift_key| keys, and right-clicking and dragging.

The selection size can be adjusted via the Selection size field in the edit
toolbar, or by holding down the |command_key|/|control_key| and |shift_key|
keys and spinning the mouse wheel.

By default, the selection block is a 2-dimensional rectangle in the current
slice, but it can be made into a 3-dimensional cube by toggling the 2D/3D
button on the edit toolbar.


Select-by-value
---------------


.. image:: images/editing_images_select_by_value_button.png
   :align: left

As an alternate to manually drawing the selection, voxels can be selected by
value. Select-by-value mode is enabled via the select-by-value button on the
edit toolbar.


In select-by-value mode, clicking on a voxel (the *seed*) will result in all
voxels that have a value similar to that voxel being selected.  The threshold
by which voxels are considered to be similar can be changed via the edit
toolbar, or by spinning the mouse wheel.


When in select-by-value mode, the search region can be restricted in the
following ways:


.. image:: images/editing_images_2D_button.png
   :align: left
           
The region can be limited to the current slice, or the entire volume, via the
2D/3D buttons.

   
.. image:: images/editing_images_select_radius_button.png
   :align: left
              
The region be limited to a radius by pushing the radius button.  The radius
can be changed on the edit toolbar, or by holding down the |alt_key| and
|shift_key| keys, and spinning the mouse wheel.

   
.. image:: images/editing_images_local_search_button.png
   :align: left
              
The search can be restricted to adjacent voxels by pushing the local search
button.  When local search is enabled, voxels which are not adjacent to an
already-selected voxel are excluded from the search.


Changing voxel values
---------------------


Once you are happy with your selection you can change the value of the
selected voxels in one of the following ways:

.. image:: images/editing_images_bucket_fill_button.png
   :align: left
              
The values of all selected voxels can be replaced with the current fill value,
by clicking the bucket-fill button:


.. image:: images/editing_images_erase_button.png
   :align: left
              
The values of all selected voxels can be erased (replaced with 0) by clicking
the erase button:

              
The current fill value can be modified via the Fill value field on the edit
toolbar.


Creating masks/ROIs
-------------------


Once you have made a selection, you can copy that selection into a new overlay,
with the *Create mask* and *Create ROI* buttons. Both buttons will create a new
image which has the same dimensions as the image being edited.



.. image:: images/editing_images_create_roi_button.png
   :align: left

The *Create ROI* button will create a new image, and will copy the values of
all selected voxels over from the image being edited. All other voxels in the
new image will be set to 0.



.. image:: images/editing_images_create_mask_button.png
   :align: left

The *Create Mask* button will create a new image, and will set the value of
all selected voxels to 1, and the value of all other voxels to 0.

   

Saving your changes
-------------------


When you have made changes to an image, or created a mask/ROI image, don't
forget to save them via the *File* |right_arrow| *Save overlay* menu item, or
the floppy disk button on the :ref:`controls-overlay-list`.
