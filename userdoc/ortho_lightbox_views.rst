.. |command_key| unicode:: U+2318
.. |shift_key|   unicode:: U+21E7
.. |control_key| unicode:: U+2303
.. |alt_key|     unicode:: U+2325

.. |right_arrow| unicode:: U+21D2


.. _ortho_lightbox_views:

Orthographic/lightbox views
===========================


FSLeyes |version| has two primary views - the orthographic (*ortho*) view, and
the *lightbox* view.


.. _ortho_lightbox_views_ortho:

Ortho view
----------


.. image:: images/ortho_lightbox_views_ortho.png
   :width: 75%
   :align: center


The ortho view comprises three canvases, which display your overlays along
three orthogonal planes. For a NIFTI image which is oriented acording to the
MNI152 template, these canvases correspond to the sagittal, coronal, and axial
planes.


.. _ortho_lightbox_views_ortho_interaction:

Ortho view interaction
^^^^^^^^^^^^^^^^^^^^^^


You can interact with an ortho view in a number of ways:


 - Click, or click and drag, to change the current location.
 - Right click and drag to draw a zoom rectangle. When you release the mouse,
   the view will zoom in to that rectangle.

 - Hold down the |command_key| key (OSX) or |control_key| key (Linux), and
   use your mouse wheel to zoom in and out of a canvas. 
   
 - Hold down the |shift_key| key, and use your mouse wheel to change the
   current location along the depth axis for that canvas (i.e. to scroll
   through slices).

 - When a canvas is zoomed in, you can middle-click and drag, or hold down the
   |alt_key| key and drag with the left mouse button, to pan around.
   
 - Hold down the Shift key and the |command_key|/|control_key| key, then click
   and drag the mouse to adjust the brightness and contrast of the currently
   selected overlay. Moving the mouse vertically will adjust the contrast, and
   horizontally will adjust the brightness.

 - You can reset the view to its default zoom/pan settings by pressing
   |alt_key| + r, or selecting the *Settings* |right_arrow| *Ortho view 1*
   |right_arrow| *Reset display* menu item.


.. _ortho_lightbox_views_ortho_toolbar:

Ortho toolbar
^^^^^^^^^^^^^



.. _ortho_lightbox_views_lightbox:

Lightbox view
-------------


.. image:: images/ortho_lightbox_views_lightbox.png
   :width: 75%
   :align: center


.. _ortho_lightbox_views_ligthbox_interaction:

Lightbox view interaction
^^^^^^^^^^^^^^^^^^^^^^^^^


.. _ortho_lightbox_views_lightbox_toolbar:

Lightbox toolbar
^^^^^^^^^^^^^^^^


.. _ortho_lightbox_display_settings:
           
Ortho/lightbox display settings
-------------------------------
