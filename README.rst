FSLeyes
=======

.. image:: https://img.shields.io/pypi/v/fsleyes.svg
   :target: https://pypi.python.org/pypi/fsleyes/

.. image:: https://anaconda.org/conda-forge/fsleyes/badges/version.svg
   :target: https://anaconda.org/conda-forge/fsleyes

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.1470761.svg
   :target: https://doi.org/10.5281/zenodo.1470761

.. image:: https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/badges/master/coverage.svg
   :target: https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/commits/master/


`FSLeyes <https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes>`_ is the `FSL
<http://fsl.fmrib.ox.ac.uk/fsl/fslwiki>`_ image viewer.


Installation
------------


FSLeyes is a GUI application written in Python, and built on `wxPython
<https://www.wxpython.org>`_. FSLeyes requires OpenGL for visualisation.


In the majority of cases, you should be able to follow the installation
instructions outlined at the FSLeyes home page:

https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSLeyes.


Dependencies
------------


All of the core dependencies of FSLeyes are listed in `requirements.txt
<requirements.txt>`_.


Some extra dependencies, which provide additional functionality, are listed in
`requirements-extra.txt <requirements-extra.txt>`_ and
`requirements-notebook.txt <requirements-notebook.txt>`_.


Dependencies for running tests and building the documentation are listed
in `requirements-dev.txt <requirements-dev.txt>`_.


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


Documentation
-------------

The FSLeyes user and API documentation are hosted at:

 - https://open.win.ox.ac.uk/pages/fsl/fsleyes/fsleyes/userdoc/
 - https://open.win.ox.ac.uk/pages/fsl/fsleyes/fsleyes/apidoc/


The FSLeyes user and API documentation is written in ReStructuredText, and can
be built using `sphinx <http://www.sphinx-doc.org/>`_::

    pip install -r requirements-dev.txt
    python setup.py userdoc
    python setup.py apidoc

The documentation will be generated and saved in ``userdoc/html/`` and
``apidoc/html/``.


Credits
-------


Some of the FSLeyes icons are derived from the Freeline icon set, by Enes Dal,
available at https://www.iconfinder.com/Enesdal, and released under the
Creative Commons (Attribution 3.0 Unported) license.

The volumetric spline interpolation routine uses code from:

Daniel Ruijters and Philippe Thévenaz,
GPU Prefilter for Accurate Cubic B-Spline Interpolation,
The Computer Journal, vol. 55, no. 1, pp. 15-20, January 2012.
http://dannyruijters.nl/docs/cudaPrefilter3.pdf

The GLSL parser is based on code by Nicolas P . Rougier, available at
https://github.com/rougier/glsl-parser, and released under the BSD license.

DICOM to NIFTI conversion is performed with Chris Rorden's dcm2niix
(https://github.com/rordenlab/dcm2niix).

The *brain_colours* colour maps were produced and provided by Cyril Pernet
(https://doi.org/10.1111/ejn.14430).
