.. |command_key| unicode:: U+2318
.. |shift_key|   unicode:: U+21E7
.. |control_key| unicode:: U+2303
.. |alt_key|     unicode:: U+2325
.. |up_key|      unicode:: U+2191
.. |down_key|    unicode:: U+2193
.. |left_key|    unicode:: U+2190
.. |right_key|   unicode:: U+2192





.. _keyboard_shortcuts:

Keyboard and mouse shortcuts
============================


.. contents::
   :local:
   :depth: 1


FSLeyes has a number of keyboard and mouse shortcuts and modifiers which can
make performing various tasks more convenient. This page contains a list of
all keyboard and mouse shortcuts available for use within FSLeyes.


Modifier keys
-------------


The following symbols and terms are used to represent various keyboard keys:

 - |shift_key|: Shift
 - |control_key|: Control
 - |command_key|: Command (on macOS; Control on other platforms)
 - |alt_key|: Option (on macOS; Alt on other platforms)
 - |up_key|: Up arrow key
 - |down_key|: Down arrow key
 - |left_key|: Left arrow key
 - |right_key|: Right arrow key
 - **Left mouse**: Left mouse button, typically a one-finger tap on a touchpad
 - **Right mouse**: Right mouse button, typically a two-finger tap on a
   touchpad
 - **Middle mouse**: Left mouse button, typically a three-finger tap on a
   touchpad
 - **Mouse wheel**: Mouse-wheel scrolling, typically a two-finger drag on a
   touchpad


General
-------


The following shortcuts are available throughout FSLeyes.


.. rst-class:: linewrap-table

=================================== =====================================
Shortcut                            Action
=================================== =====================================
|command_key| + ``q``               Exit FSLeyes
|command_key| + |shift_key| + ``/`` Open FSLeyes user documentation
|command_key| + |shift_key| + ``d`` Change to default view/control panel
                                    layout
|command_key| + ``1``               Open ortho view
|command_key| + ``2``               Open lightbox view
|command_key| + ``3``               Open time series view
|command_key| + ``4``               Open histogram view
|command_key| + ``5``               Open power spectrum view
|command_key| + ``6``               Open 3D view
|command_key| + ``7``               Open Python shell
|command_key| + ``w``               Close focused view
|command_key| + |alt_key| + ``x``   Remove all controls from focused view
|command_key| + ``o``               Load new overlay
|command_key| + ``d``               Load new overlay from directory
|command_key| + ``s``               Load new overlay from
                                    ``$FSLDIR/data/standard/``
|command_key| + |up_key|            Select next overlay in list (within
                                    the focused view)
|command_key| + |down_key|          Select previous overlay in list
                                    (within the focused view)
|command_key| + ``f``               Show/hide selected overlay (within
                                    the focused view)
|command_key| + |shift_key| + ``n`` Create new image
|command_key| + |shift_key| + ``c`` Copy selected image
|command_key| + |shift_key| + ``s`` Save selected image
|command_key| + |shift_key| + ``r`` Re-load selected overlay
|command_key| + |shift_key| + ``w`` Remove selected overlay
=================================== =====================================


Ortho, ligthbox, and 3D views
-----------------------------


The following shortcuts are available within ortho, lightbox, and 3D views.


.. rst-class:: linewrap-table

================================= =====================================
Shortcut                          Action
================================= =====================================
|command_key| + |alt_key| + ``1`` Open/close overlay list
|command_key| + |alt_key| + ``2`` Open/close location panel
|command_key| + |alt_key| + ``3`` Open/close overlay information
|command_key| + |alt_key| + ``4`` Open/close overlay display settings
|command_key| + |alt_key| + ``5`` Open/close view settings
|command_key| + |alt_key| + ``6`` Open/close FSL atlas panel
|command_key| + |alt_key| + ``7`` Open/close overlay display toolbar
|command_key| + |alt_key| + ``8`` Open/close ortho/lightbox/3D toolbar
|command_key| + |alt_key| + ``9`` Open/close file tree panel
|alt_key| + ``m``                 Start/stop movie mode
================================= =====================================


Some additional shortcuts are available within ortho views.


.. rst-class:: linewrap-table

================================= =====================================
Shortcut                          Action
================================= =====================================
|command_key| + |alt_key| + ``a`` Open/close annotations panel
|alt_key| + ``e``                 Toggle edit mode
|alt_key| + ``r``                 Reset zoom/pan
|alt_key| + ``c``                 Reset location to centre
|alt_key| + ``o``                 Reset location to world origin
|alt_key| + ``l``                 Show/hide orientation labels
|alt_key| + ``c``                 Show/hide location cursor
|alt_key| + ``x``                 Show/hide X (sagittal) canvas
|alt_key| + ``y``                 Show/hide Y (coronal) canvas
|alt_key| + ``z``                 Show/hide Z (axial) canvas
|alt_key| + ``i``                 Seed correlation on 4D image
|up_key|                          Move location up in focused canvas
|down_key|                        Move location down in focused canvas
|left_key|                        Move location left in focused canvas
|right_key|                       Move location right in focused canvas
``-`` / ``_``                     Previous slice in focused canvas
``+`` / ``=``                     Next slice in focused canvas
================================= =====================================


Plotting views
--------------


The following shortcuts and actions are available within time series,
histogram, and power spectrum views.


.. rst-class:: linewrap-table

======================================== =====================================
Shortcut                                 Action
======================================== =====================================
|command_key| + |alt_key| + ``1``        Open/close overlay list
|command_key| + |alt_key| + ``2``        Open/close plot list
|command_key| + |alt_key| + ``3``        Open/close time series/histogram/
                                         power spectrum toolbar
|command_key| + |alt_key| + ``4``        Open/close time series/histogram/
                                         power spectrum control panel
|command_key| + ``i``                    Import data from file
|command_key| + ``e``                    Save data to file
Left mouse click/drag                    Pan
Right mouse click/drag                   Zoom
|command_key| + left mouse click/drag    Adjust overlay range, when a :ref:`3D
                                         histogram overlay
                                         <plot_views_histogram_control>` is
                                         shown (histogram view only)
|command_key| + left mouse click/drag    Change volume (time series view only)
======================================== =====================================



Ortho, lightbox, and 3D view interaction
----------------------------------------


The following actions are available in the ortho view.


.. rst-class:: linewrap-table

======================================== =====================================
Shortcut                                 Action
======================================== =====================================
Left mouse click/drag                    Change location
Right mouse drag                         Zoom to rectangle
Middle mouse drag                        Pan
|command_key| + mouse wheel/scroll       Zoom
|alt_key| + mouse drag                   Pan
|shift_key| + mouse wheel/scroll         Change slice
|shift_key| + mouse click/drag           Select nearest vertex (when a
                                         :ref:`mesh overlay <overlays_mesh>`
                                         is selected
|command_key| + |shift_key| + mouse drag Adjust brightness/contrast
======================================== =====================================


The following actions are available in the lightbox view.


.. rst-class:: linewrap-table

======================================== =====================================
Shortcut                                 Action
======================================== =====================================
Left mouse click/drag                    Change location
|command_key| + mouse wheel/scroll       Zoom
======================================== =====================================


The following actions are available in the 3D view.


.. rst-class:: linewrap-table

======================================== =====================================
Shortcut                                 Action
======================================== =====================================
Left mouse click/drag                    Rotate scene
Moddle mouse click/drag                  Pan
|command_key| + mouse wheel/scroll       Zoom
|alt_key| + mouse click/drag             Pan
|shift_key| + mouse click/drag           Change location, or select nearest
                                         vertex, when a mesh overlay is
                                         selected
======================================== =====================================


Ortho edit mode
---------------


The following shortcuts and actions are available in ortho edit mode.

.. rst-class:: linewrap-table

======================================== =====================================
Shortcut                                 Action
======================================== =====================================
|command_key| + ``z``                    Undo last change
|command_key| + ``y``                    Redo last undone change
|command_key| + ``n``                    Create new mask
|command_key| + |shift_key| + ``a``      Clear selection (select mode only)
|command_key| + ``b``                    Fill selected voxels (select mode
                                         only)
|command_key| + ``e``                    Erase selected voxels (select mode
                                         only)
|command_key| + ``i``                    Invert selection (select mode only)
|command_key| + ``c``                    Copy/paste data across images (select
                                         mode only)
|command_key| + ``p``                    Copy/paste selection across  slices
                                         (select mode only)
======================================== =====================================


The following actions are available when using the pencil, eraser, bucket, or
select-by-intensity tools:


+-------------------------------------+---------------------------------------+
| Shortcut                            | Action                                |
+-------------------------------------+---------------------------------------+
| *All tools*                                                                 |
+-------------------------------------+---------------------------------------+
| |shift_key| + left mouse click/drag | Change location                       |
+-------------------------------------+---------------------------------------+
| |shift_key| + mouse wheel/scroll    | Change slice                          |
+-------------------------------------+---------------------------------------+
| |alt_key| + left mouse click/drag   | Pan                                   |
+-------------------------------------+---------------------------------------+
| |command_key| + mouse wheel/scroll  | Zoom                                  |
+-------------------------------------+---------------------------------------+
| Middle mouse click/drag             | Pan                                   |
+-------------------------------------+---------------------------------------+
| *Pencil tool*                                                               |
+-------------------------------------+---------------------------------------+
| Left mouse click/drag               | Draw/select voxels                    |
+-------------------------------------+---------------------------------------+
| Right mouse click/drag              | Erase/de-select voxels                |
+-------------------------------------+---------------------------------------+
| *Eraser tool*                                                               |
+-------------------------------------+---------------------------------------+
| Left mouse click/drag               | Erase/de-select voxels                |
+-------------------------------------+---------------------------------------+
| Right mouse click/drag              | Draw/select voxels                    |
+-------------------------------------+---------------------------------------+
| *Pencil and eraser tools*                                                   |
+-------------------------------------+---------------------------------------+
| |command_key| + |shift_key| + mouse | Change cursor size                    |
| wheel/scroll                        |                                       |
+-------------------------------------+---------------------------------------+
| *Select-by-intensity tool*                                                  |
+-------------------------------------+---------------------------------------+
| |command_key| + |shift_key| + mouse | Change intensity threshold            |
| wheel/scroll                        |                                       |
+-------------------------------------+---------------------------------------+
| |alt_key| + |shift_key| + mouse     | Change selection radius               |
| wheel/scroll                        |                                       |
+-------------------------------------+---------------------------------------+


The ortho crop tool
-------------------

The following actions are available when using the ortho crop tool.


.. rst-class:: linewrap-table

======================================== =====================================
Shortcut                                 Action
======================================== =====================================
Left mouse click/drag                    Adjust crop box
|shift_key| + left mouse click/drag      Change location
|shift_key| + left mouse click/drag      Change location
|alt_key| + left mouse click/drag        Pan
|command_key| + mouse wheel/scroll       Zoom
======================================== =====================================
