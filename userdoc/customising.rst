.. _customising:

=====================
 Customising FSLeyes
=====================


This page contains details on customising various aspects of FSLeyes.


.. _customising_colour_maps:

Colour maps
===========

For :ref:`volume <overlays_volume>` overlays, the :ref:`overlay display panel
<overlays_overlay_display_panel>` has a **Load colour map** button which
allows you to load new colour maps into FSLeyes.


Clicking on this button will bring up a file selection dialog, allowing you to
choose a file which contains a custom colour map. FSLeyes understands colour
map files with a name that ends in ``.cmap``, and which contain a list of RGB
colours, one per line, with each colour specified by three space-separated
floating point values in the range ``0.0 - 1.0``, with each value
corresponding to the R, G, and B colour channels respectively. For example::


  1.000000 0.260217 0.000000
  0.000000 0.687239 1.000000
  0.738949 0.000000 1.000000


When you apply a colour map to an image, FSLeyes will map the image display
range to the colours in the colour map - the low display range value will map
to the first colour in the colour map (i.e. the first colour in the file), and
the high display range to the last colour (the last colour in the file). The
**Interpolate colour maps** setting for :ref:`volume <overlays_volume>` allows
you to define a continuous colour map by only specifying a few colours. For
example, you could define the greyscale colour map with just two colours::

  
  0.0 0.0 0.0
  1.0 1.0 1.0


When the **Interpolate colour maps** setting is enabled, FSLeyes will
interpolate between these colours.
 

When you load a custom colour map, FSLeyes will ask you if you would like to
install it permanently [*]_. If you choose to do so, FSLeyes will copy the
colour map file into the FSLeyes ``assets`` directory, renaming the file so it
ends with ``.cmap``. Under OSX, this directory is located in::

  FSLeyes.app/Contents/Resources/assets/colourmaps/


And under Linux, it  is located in::

  FSLeyes/share/FSLeyes/assets/colourmaps/


You can also customise colour map display names and order. Inside the
``colourmaps/`` directoy you will find a file called ``order.txt``. This file
defines the order in which colour maps are displayed in the FSLeyes interface,
and also contains the display name for each colour map; it contains a list of
colour map file names (without the ``.cmap`` suffix), and corresponding
display names for each::

  
  greyscale        Greyscale
  red-yellow       Red-Yellow
  blue-lightblue   Blue-Light blue
  red              Red
  ...

  
Any colour maps which exist in the ``colourmaps/`` directory, but are not
listed in ``order.txt`` will still be available in the FSLeyes interface, but
will be added after all of the colour maps listed in ``order.txt``.


.. warning:: When creating your own ``.cmap`` file, make sure that there are
             no spaces in the file name. This also applies to ``.lut`` files
             (covered :ref:`below <customising_lookup_tables>`).

   
.. [*] To permanently install a colour map (and to edit existing colour maps),
       you will need permission to write to the FSLeyes installation
       directory.


.. _customising_lookup_tables: 

Lookup tables
=============


FSLeyes manages lookup tables for :ref:`overlays_label` overlays in a very
similar manner as for :ref:`colour maps <customising_colour_maps>`. The
:ref:`lookup table panel <overlays_the_lookup_table_panel>` allows you to
create your own lookup tables, and load a lookup table from a file.
A FSLeyes lookup table file has a name that ends in ``.lut``, and defines a
lookup table which may be used to display images wherein each voxel has a
discrete integer label.  The lookup table file defines a name and a colour for
each of the possible voxel values in such an image.


Each line in a ``.lut`` file must specify the label value, RGB colour, and
associated name.  The first column (where columns are space-separated) defines
the label value, the second to fourth columns specify the RGB values, and all
remaining columns give the label name. For example::

  
        1  0.00000 0.93333 0.00000 Frontal Pole
        2  0.62745 0.32157 0.17647 Insular Cortex
        3  1.00000 0.85490 0.72549 Superior Frontal Gyrus


.. important:: The labels specified in a ``.lut`` file must be specified
               in ascending order.


Under OSX, FSLeyes stores its lookup table files in::

  FSLeyes.app/Contents/Resources/assets/luts/


Under Linux, the lookup tables can be found in::

  FSLeyes/share/FSLeyes/assets/luts/


In the same manner as for :ref:`colour maps <customising_colour_maps>` the
``luts/`` director contains a file called ``order.txt``, which allows you to
cusomise the display name and order of LUTs as shown in the FSLeyes interface.

               
.. _customising_atlases:

Atlases
=======


The :ref:`atlas management <atlases_atlas_management>` panel allows you to
load custom atlases into FSLeyes. FSL |fsl_version| and FSLeyes |version|
supports atlases which are described by an ``xml`` file that adheres to the
`FSL atlas XML file format
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Atlases-Reference>`_.


FSLeyes |version| understands two types of atlases [*]_:


 - A *label* (or *summary*) atlas is a 3D NIFTI image which contains different
   discrete integer values for each region defined in the atlas.

   
 - A *probabilistic* atlas is a 4D NIFTI image, where each volume contains a
   probability map for one region in the atlas.  This probabilistic image may
   also be accompanied by a corresponding label image.

   
Multiple versions of these images, at different resolutions, may exist
(e.g. 1mm and 2mm versions of the same image may be present).


If you have an atlas image which you would like to use in FSLeyes, you must
write an ``xml`` file which describes the atlas, contains paths to the atlas
image(s), and contains a description of every region in the atlas.


The best way to create one of these files is to look at the atlas files that
exist in ``$FSLDIR/data/atlases``. Create a copy of one of these files -
select one which describes an atlas that is similar to your own atlas
(i.e. probabilistic or label) - and then modify the atlas name, file paths,
and label descriptions to suit your atlas.  Your ``xml`` atlas file should end
up looking something like the following:


.. code-block:: xml

   <atlas>

     <!-- The header defines the atlas name, type, 
          and paths to the atlas image files. -->
     <header>

       <!-- Human-readable atlas name -->
       <name>Harvard-Oxford Cortical Structural Atlas</name>

       <!-- Abbreviated atlas name -->
       <shortname>HOCPA</shortname>

       <!-- Atlas type - "Probabilistic" or "Label" -->
       <type>Probabilistic</type>

       <!-- Paths (defined relative to the location 
            of this XML file) to the atlas images.
            Multiple <images> elements may be present
            - one for each resolution in which the
            atlas is available. -->
       <images>

         <!-- If the atlas type is "Probabilistic", the
              <imagefile> must be a path to a 4D image
              which contains one volume per region.
              Otherwise, if the atlas type is "Label",
              the <imagefile> must be a path to 3D
              label image. -->
         <imagefile>/HarvardOxford/HarvardOxford-cort-prob-2mm</imagefile>

         <!-- If the atlas type is "Probabilistic", the
              <summaryimagefile> must be a path to a 3D
              label image which 'summarises' the
              probabilistic image. If the atlas type is
              "Label", the <summaryimagefile> is identical
              to the <imagefile>. -->
         <summaryimagefile>/HarvardOxford/HarvardOxford-cort-maxprob-thr25-2mm</summaryimagefile>
       </images>

       <!-- A 1mm version of the same atlas images. -->
       <images>
         <imagefile>/HarvardOxford/HarvardOxford-cort-prob-1mm</imagefile>
         <summaryimagefile>/HarvardOxford/HarvardOxford-cort-maxprob-thr25-1mm</summaryimagefile>
       </images>
     </header>

     <!-- The <data> element contains descriptions
          of all regions in the atlas. -->
     <data>

       <!-- Every region in the atlas has a <label> element which defines:

            - The "index" of the label in the 4D probabilistic
              image, if the atlas type is "Probabilistic". The
              index also defines the region label value, for
              "Label" atlases, and for 3D summary files - add
              1 to the index to get the label value.

            - The "x", "y", and "z" coordinates of a pre-
              calculated "centre-of-gravity" for this region.
              These are specified as voxel coordinates,
              relative to the *first* image in the <images>
              list, above.

            - The name of the region. -->
       
       <label index="0" x="48" y="94" z="35">Frontal Pole</label>
       <label index="1" x="25" y="70" z="32">Insular Cortex</label>
       <label index="2" x="33" y="73" z="63">Superior Frontal Gyrus</label>

       <!-- ... -->

       <label index="45" x="74" y="53" z="40">Planum Temporale</label>
       <label index="46" x="44" y="21" z="42">Supracalcarine Cortex</label>
       <label index="47" x="37" y="15" z="34">Occipital Pole</label> 
     </data>
   </atlas>

   
.. [*] Future releases of FSL and FSLeyes will support different types of
       atlases (e.g. longitudinal, surface-based, etc.).
