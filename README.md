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


Take a look at the [Documentation for
developers](http://users.fmrib.ox.ac.uk/~paulmc/fsleyes/index.html) if you want
to program with *FSLeyes*.


Dependencies
------------


*FSLeyes* depends upon the following libraries:


| Library                                           | Version |
| ------------------------------------------------- | ------- |
| [props](https://git.fmrib.ox.ac.uk/paulmc/props/) | Latest  |
| [fslpy](https://git.fmrib.ox.ac.uk/paulmc/fslpy/) | Latest  |
| [PyOpenGL](http://pyopengl.sourceforge.net/)      | 3.1.0   |
| [numpy](http://www.numpy.org/)                    | 1.8.1   |
| [scipy](http://www.scipy.org/)                    | 0.14.0  |
| [matplotlib](http://matplotlib.org/)              | 1.4.3   |
| [nibabel](http://nipy.org/nibabel/)               | 1.3.0   |
| [Pillow](https://python-pillow.github.io/)        | 2.5.3   |
| [PyParsing](http://pyparsing.wikispaces.com/)     | 2.1.0   |
| [Jinja2](http://jinja.pocoo.org/)                 | 2.8     |
| [wxPython](http://wxpython.org/)                  | 3.0.2.0 |
| [OSMesa](http://mesa3d.org/)                      | 8.0.5   |
| [Sphinx](http://www.sphinx-doc.org/en/stable/)    | 1.3.5   |

 > Notes:
 >   - Sphinx is only needed for building the documentation.
 >
 >   - OSMesa is only needed for the off-screen `render` program.
 >
 >   - Pillow is only needed for saving screenshots in formats other than PNG.
 > 
 >   - If you are installing *FSLeyes* manually, don't worry too much about 
 >     having the exact version of each of the packages - just try with 
 >     the latest version, and roll-back if you have problems.


Being an OpenGL application, *FSLeyes* can only be used on computers
with graphics hardware that supports one of the following versions:

 - OpenGL 1.4, with the following extensions:
   - `ARB_vertex_program`
   - `ARB_fragment_program`
   - `EXT_framebuffer_object`

 - OpenGL 2.1, with the following extensions:
   - `EXT_framebuffer_object`
   - `ARB_instanced_arrays`
   - `ARB_draw_instanced`


Credits
-------


Some of the icons are derived from the Freeline icon set, by Enes Dal,
available at https://www.iconfinder.com/Enesdal, and released under the
Creative Commons (Attribution 3.0 Unported) license.
