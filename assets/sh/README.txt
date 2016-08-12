This directory contains pre-calculated information which is used to render
fibre orientation distributions (FODs), described by spherical harmonic
functions.


vert*.txt
---------


These files contain the vertices of a tessellated sphere at a range of
different qualities. The spheres are based on an icosahedron (12 vertices
comprising 20 equilateral triangles), which are repeatedly tessellated to
improve their resolution. The files are named according to following
convention:

  vert_[iterations].txt


where "iterations" is the number of times the sphere was tessellated.


face*.txt
---------


Vertex indices defining the faces (triangles) of the tessellated spheres. The
vertices of each face have the same unwinding order (meaning that back-face
culling is possible when displaying using OpenGL). These files follow the same
naming convention as the vertex files.


*coef*.txt
----------

These files contain pre-calculated spherical harmonic coefficient tables, for
calculating the radii of the vertices on a sphere at a given display
resolution (number of vertices), and given maximum SH function order. The file
names follow the convention:


  [shType]_coef_[resolution]_[maxSHOrder].txt


where:

  - shType:     either "sym" or "asym". "sym" files contain coefficients for
                SH functions of even order only, and "asym" files contain
                coefficients for both even and odd order.

  - resolution: Display resolution (see the "vert" and "face" file descriptions
                above).

  - maxSHOrder: Maximum SH function order used to generate the coefficients.


Thanks to Matteo Bastiani (FMRIB Centre, Oxford, UK) for help in creating
these files.
