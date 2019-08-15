.. |right_arrow| unicode:: U+21D2


.. _file_tree:


File tree
=========


The *File tree* control panel allows you to use FSLeyes to browse image data
in *structured directories*. You can add a file tree panel to the ortho,
lightbox, or 3D views via the *Settings* |right_arrow| *view* |right_arrow|
*File tree* menu option.


FSLeyes has built-in support for a selection of structured data directories,
including:

 - `Human Connectome Project <http://www.humanconnectomeproject.org/>`_ data
 - Raw `BIDS <https://bids.neuroimaging.io/>`_ data
 - `Freesurfer <http://www.freesurfer.net/>`_ data

It is also possible to :ref:`define your own file tree
<file_tree_define_your_own>`, for working with your own directory structures.


Opening a data directory
------------------------


.. image:: images/filetree_toprow.png
   :width: 60%
   :align: center


.. image:: images/filetree_filetypes_and_variables.png
   :width: 25%
   :align: left


The file tree panel has a row along its top containing a drop-down box and
some buttons. When you want to open a directory, the first step is to select
the data directory type from the dropdown box. Or, if you have a custom tree
file, you can select it via the *Load tree file* button.


Once you have selected a tree, click on the *Load directory* button to select
your data directory. The left side of the file tree panel will be then be
populated with lists of all the file types and variables present in the
directory. Here we are looking at some data from the Human Connectome Project.


Configuring the file list
-------------------------


The next step is to choose which file types you want to display - you can do
this by selecting them from the file type list on the left. As soon as you
select some file types, a list of files will appear on the right side of the
file tree panel.



Saving notes
------------




.. _file_tree_define_your_own:

Defining your own file tree
---------------------------

Say you have some imaging data for a group of subjects, which you have
organised nicely like so::

  subj-01/
    ses-1/
      T1w.nii.gz
      T2w.nii.gz
      L.white.gii
      R.white.gii
      L.mid.gii
      R.mid.gii
      L.pial.gii
      R.pial.gii
    ses-2/
      T1w.nii.gz
      T2w.nii.gz
      L.white.gii
      R.white.gii
      L.mid.gii
      R.mid.gii
      L.pial.gii
      R.pial.gii
  subj-02/
    ses-1/
      T1w.nii.gz
      T2w.nii.gz
      L.white.gii
      R.white.gii
      L.mid.gii
      R.mid.gii
      L.pial.gii
      R.pial.gii
    ses-2/
      T1w.nii.gz
      T2w.nii.gz
      L.white.gii
      R.white.gii
      L.mid.gii
      R.mid.gii
      L.pial.gii
      R.pial.gii
  ...

To load this directory into the file tree panel, you need to create a
``.tree`` file which describes the structure of the directory. It defines all
of the *variables* which are implicitly present in the structure (e.g. subject
ID), and all of the *file types* which are present (e.g. ``T1w``, ``T2w``,
etc)::

  subj-{subject}
    ses-{session}
      T1w.nii.gz (T1w)
      T2w.nii.gz (T2w)
      {hemi}.{surf}.gii (surface)


In this example, we have three file types - the ``T1w`` image, the ``T2w``
image, and the cortical ``surface`` files. We also have four variables - the
``subject``, the ``session``, the surface type (``surf``), and the hemisphere
(``hemi``).


See the ``fsl.utils.filetree`` module in the |fslpy_doc| documentation for
more details on defining your own file trees.
