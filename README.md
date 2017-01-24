FSLeyes
=======


This is the home of *FSLeyes*, the
 [FSL](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/) image viewer. 


Documentation
-------------


Check out the [Installation
instructions](https://git.fmrib.ox.ac.uk/paulmc/fsleyes/wikis/home) for
details on installing FSLeyes.


The [Documentation for
users](http://users.fmrib.ox.ac.uk/~paulmc/fsleyes_userdoc/index.html)
provides a comprehensive overview of how to use *FSLeyes*.


Take a look at the `fsleyes`, `fslpy` and `props` API documentation if you
want to program with *FSLeyes*.

 - [FSLeyes](http://users.fmrib.ox.ac.uk/~paulmc/fsleyes_apidoc/index.html)
 - [fslpy](http://users.fmrib.ox.ac.uk/~paulmc/fslpy/index.html)
 - [props](http://users.fmrib.ox.ac.uk/~paulmc/props/index.html) 


Dependencies
------------


*FSLeyes* depends on [wxPython 3.0.2.0](http://wxpython.org/), and
the libraries listed in [requirements.txt](requirements.txt).


Being an OpenGL application, *FSLeyes* can only be used on computers with
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

*FSLeyes* also requires the presence of GLUT, or FreeGLUT.


Credits
-------


Some of the icons are derived from the Freeline icon set, by Enes Dal,
available at https://www.iconfinder.com/Enesdal, and released under the
Creative Commons (Attribution 3.0 Unported) license.
