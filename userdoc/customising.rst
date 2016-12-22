.. _customising:

=====================
 Customising FSLeyes
=====================


.. todo:: This page has not yet been written.


Various elements of FSLeyes can be customised


Colour maps

Remember that you need write permission to /assets/ to install colour
maps/luts

Luts

Perspectives


.. _customising_custom_atlases:


Custom atlases
==============


The :ref:`atlas management <atlases_atlas_management>` panel allows you to
load custom atlases into FSLeyes. FSLeyes |version| supports atlases which are
described by an ``xml`` file that adheres to the `FSL atlas XML file format
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Atlases-Reference>`_ [*]_.


FSLeyes can understand two types of atlases:


 - A *label* (or "summary") atlas is a 3D NIFTI image which contains different
   discrete integer values for each region defined in the atlas.

   
 - A *probabilistic* atlas is a 4D NIFTI image, where each volume contains a
   probability map for one region in the atlas.  This probabilistic image may
   also be accompanied by a corresponding label image.

   
Multiple versions of these images, at different resolutions, may exist
(e.g. 1mm and 2mm versions of the same image may be present).


If you have an atlas image which you would like to use in FSLeyes, you must
write an ``xml`` file which describes the atlas. This file describes the
atlas, contains paths to the atlas image(s), and contains a description of
every region in the atlas.


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

   
.. [*] The ``xml`` atlas specification format is due to be replaced in a
       future release of FSL.
