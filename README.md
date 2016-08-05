FSLeyes
=======


This is the home of *FSLeyes*, the
 [FSL](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/) image viewer. 


Documentation
-------------


Check out the [Installation
instructions](https://git.fmrib.ox.ac.uk/paulmc/fsleyes/wikis/home) for
details on getting started.


The [Documentation for users](http://users.fmrib.ox.ac.uk/~paulmc/fsleyes/index.html)
provides a comprehensive overview of how to use *FSLeyes*.


Take a look at the `fsleyes`, `fslpy` and `props` API documentation if you
want to program with *FSLeyes*.

 - [FSLeyes](http://users.fmrib.ox.ac.uk/~paulmc/fsleyes_apidoc/index.html)
 - [fslpy](http://users.fmrib.ox.ac.uk/~paulmc/fslpy/index.html)
 - [props](http://users.fmrib.ox.ac.uk/~paulmc/props/index.html) 


Dependencies
------------


*FSLeyes* depends upon the following libraries:


| Library                                                        | Version |
| -------------------------------------------------------------- | ------- |
| [fslpy](https://git.fmrib.ox.ac.uk/paulmc/fslpy/)              | Latest  |
| [indexed_gzip](https://github.com/pauldmccarthy/indexed_gzip/) | Latest  |
| [Jinja2](http://jinja.pocoo.org/)                              | 2.8     |
| [matplotlib](http://matplotlib.org/)                           | 1.5.1   |
| [nibabel](http://nipy.org/nibabel/)                            | 2.0.2   |
| [numpy](http://www.numpy.org/)                                 | 1.11.1  |
| [Pillow](https://python-pillow.github.io/)                     | 3.2.0   |
| [props](https://git.fmrib.ox.ac.uk/paulmc/props/)              | Latest  |
| [PyOpenGL](http://pyopengl.sourceforge.net/)                   | 3.1.0   |
| [PyOpenGL-accelerate](http://pyopengl.sourceforge.net/)        | 3.1.0   |
| [PyParsing](http://pyparsing.wikispaces.com/)                  | 2.1.1   |
| [scipy](http://www.scipy.org/)                                 | 0.17.0  |
| [six](https://pythonhosted.org/six/)                           | 1.10.0  |
| [Sphinx](http://www.sphinx-doc.org/en/stable/)                 | 1.4.1   |
| [Sphinx RTD theme](https://github.com/snide/sphinx_rtd_theme)  | 0.1.9   | 
| [wxPython](http://wxpython.org/)                               | 3.0.2.0 |


Being an OpenGL application, *FSLeyes* can only be used on computers
with graphics hardware that supports one of the following versions:

 - OpenGL 1.4, with the following extensions:
   - `ARB_vertex_program`
   - `ARB_fragment_program`
   - `EXT_framebuffer_object`
   - `GL_ARB_texture_non_power_of_two`

 - OpenGL 2.1, with the following extensions:
   - `EXT_framebuffer_object`
   - `ARB_instanced_arrays`
   - `ARB_draw_instanced`


Credits
-------


Some of the icons are derived from the Freeline icon set, by Enes Dal,
available at https://www.iconfinder.com/Enesdal, and released under the
Creative Commons (Attribution 3.0 Unported) license.
