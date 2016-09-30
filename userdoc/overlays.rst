.. |right_arrow| unicode:: U+21D2


.. _overlays:

Overlays
========


FSLeyes refers to the files that you load as *overlays*. FSLeyes |version| is
capable of displaying the following file types:

 - NIFTI images (``.nii``, ``.nii.gz``).
   
 - VTK images (``.vtk``) which are in a format similar to that produced by the
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
   file from the ``$FSLDIR/data/standard/`` directory to load.

4. The + button on the overlay list allows you to choose a file to load.


.. note:: The *File* |right_arrow| *Add standard* menu option will be disabled
          if your FSL environment is not configured correctly.


The overlay menu
----------------


The *Overlay* menu contains optinos for chacn



The display space
-----------------


Coordinate systems
------------------

