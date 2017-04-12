FSLeyes
=======


*FSLeyes* is the [FSL](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/) image viewer.


Dependencies
------------


All of the dependencies of FSLeyes are listed in
[requirements.txt](requirements.txt).


Being an OpenGL application, FSLeyes can only be used on computers with
graphics hardware (or a software GL renderer) that supports one of the
following versions:


 - OpenGL 1.4, with the following extensions:
   - `ARB_vertex_program`
   - `ARB_fragment_program`
   - `EXT_framebuffer_object`
   - `GL_ARB_texture_non_power_of_two`

 - OpenGL 2.1, with the following extensions:
   - `EXT_framebuffer_object`
   - `ARB_instanced_arrays`
   - `ARB_draw_instanced`


FSLeyes also requires the presence of GLUT, or FreeGLUT.


Documentation
-------------


The FSLeyes user and API documentation is written in ReStructuredText, and
can be built using [sphinx](http://www.sphinx-doc.org/). Install `sphinx`
and `sphinx-rtd-theme`, and then run:

    python setup.py userdoc
    python setup.py apidoc

The documentation will be generated and saved in `userdoc/html/` and
`apidoc/html/`.


Buildling
---------


You can build standalone versions of FSLeyes for OSX and Linux.  For OSX,
install `py2app>=0.12`. For Linux, install `pyinstaller>=3.2.0`. Then, on
either platform, run the following:

    python setup.py build_standalone


Credits
-------


Some of the FSLeyes icons are derived from the Freeline icon set, by Enes Dal,
available at https://www.iconfinder.com/Enesdal, and released under the
Creative Commons (Attribution 3.0 Unported) license.


The file [fsleyes.gl.trimesh](fsleyes/gl/trimesh.py) module includes code from
Michael Dawson-Haggerty's [trimesh](https://github.com/mikedh/trimesh)
project, which is released under the MIT license.
