FSLeyes
=======

.. image:: https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/badges/master/build.svg
   :target: https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/commits/master/

.. image:: https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/badges/master/coverage.svg
   :target: https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/commits/master/

.. image:: https://img.shields.io/pypi/v/fsleyes.svg
   :target: https://pypi.python.org/pypi/fsleyes/)


*FSLeyes* is the `FSL <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki>`_ image viewer.


Dependencies
------------


All of the dependencies of FSLeyes are listed in
`requirements.txt <requirements.txt>`_.


Being an OpenGL application, FSLeyes can only be used on computers with
graphics hardware (or a software GL renderer) that supports one of the
following versions:


- OpenGL 1.4, with the following extensions:

  - ``ARB_vertex_program``
  - ``ARB_fragment_program``
  - ``EXT_framebuffer_object``
  - ``GL_ARB_texture_non_power_of_two``

- OpenGL 2.1, with the following extensions:

  - ``EXT_framebuffer_object``
  - ``ARB_instanced_arrays``
  - ``ARB_draw_instanced``


FSLeyes also requires the presence of GLUT, or FreeGLUT.


Documentation
-------------


The FSLeyes user and API documentation is written in ReStructuredText, and can
be built using `sphinx <http://www.sphinx-doc.org/>`_::

    python setup.py userdoc
    python setup.py apidoc

The documentation will be generated and saved in ``userdoc/html/`` and
``apidoc/html/``.


Credits
-------


Some of the FSLeyes icons are derived from the Freeline icon set, by Enes Dal,
available at https://www.iconfinder.com/Enesdal, and released under the
Creative Commons (Attribution 3.0 Unported) license.


The file `fsleyes.gl.trimesh <fsleyes/gl/trimesh.py>`_ module includes code
from Michael Dawson-Haggerty's `trimesh <https://github.com/mikedh/trimesh>`_
project, which is released under the MIT license.


The volumetric spline interpolation routine uses code from:

Daniel Ruijters and Philippe Thévenaz,
GPU Prefilter for Accurate Cubic B-Spline Interpolation,
The Computer Journal, vol. 55, no. 1, pp. 15-20, January 2012.
http://dannyruijters.nl/docs/cudaPrefilter3.pdf
