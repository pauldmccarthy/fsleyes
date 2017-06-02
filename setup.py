#!/usr/bin/env python
#
# setup.py - setuptools configuration for installing FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Setup script for FSLeyes. """


from __future__ import print_function

import               os
import               shutil
import               fnmatch
import itertools  as it
import os.path    as op

from setuptools import setup
from setuptools import find_packages
from setuptools import Command

from distutils.command.build import build


# The directory in which this
# setup.py file is contained.
basedir = op.dirname(op.abspath(__file__))


class docbuilder(Command):
    """Base class for the userdoc and apidoc commands. """

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):

        docdir  = self.docdir
        destdir = op.join(docdir, 'html')

        if op.exists(destdir):
            shutil.rmtree(destdir)

        import sphinx

        try:
            import unittest.mock as mock
        except:
            import mock

        # Sigh. Why can't I mock a package?
        mockobj       = mock.MagicMock()
        mockedModules = [
            'OpenGL',
            'OpenGL.GL',
            'OpenGL.GL.ARB',
            'OpenGL.GL.ARB.draw_instanced',
            'OpenGL.GL.ARB.fragment_program',
            'OpenGL.GL.ARB.instanced_arrays',
            'OpenGL.GL.ARB.texture_float',
            'OpenGL.GL.ARB.vertex_program',
            'OpenGL.GL.EXT',
            'OpenGL.GL.EXT.framebuffer_object',
            'OpenGL.GLUT',
            'OpenGL.extensions',
            'OpenGL.raw',
            'OpenGL.raw.GL',
            'OpenGL.raw.GL._types',
            'fsl',
            'fsl.data',
            'fsl.data.atlases',
            'fsl.data.constants',
            'fsl.data.dtifit',
            'fsl.data.featanalysis',
            'fsl.data.featimage',
            'fsl.data.fixlabels',
            'fsl.data.gifti',
            'fsl.data.image',
            'fsl.data.imagewrapper',
            'fsl.data.melodicimage',
            'fsl.data.mesh',
            'fsl.data.vest',
            'fsl.data.volumelabels',
            'fsl.utils',
            'fsl.utils.async',
            'fsl.utils.cache',
            'fsl.utils.callfsl',
            'fsl.utils.memoize',
            'fsl.utils.notifier',
            'fsl.utils.platform',
            'fsl.utils.settings',
            'fsl.utils.transform',
            'fsleyes_props',
            'fsleyes_widgets',
            'fsleyes_widgets.bitmaptoggle',
            'fsleyes_widgets.dialog',
            'fsleyes_widgets.elistbox',
            'fsleyes_widgets.floatslider',
            'fsleyes_widgets.floatspin',
            'fsleyes_widgets.imagepanel',
            'fsleyes_widgets.notebook',
            'fsleyes_widgets.numberdialog',
            'fsleyes_widgets.placeholder_textctrl',
            'fsleyes_widgets.rangeslider',
            'fsleyes_widgets.texttag',
            'fsleyes_widgets.utils',
            'fsleyes_widgets.utils.colourbarbitmap',
            'fsleyes_widgets.utils.layout',
            'fsleyes_widgets.utils.status',
            'fsleyes_widgets.utils.typedict',
            'fsleyes_widgets.widgetgrid',
            'fsleyes_widgets.widgetlist',
            'matplotlib',
            'matplotlib.backend_bases',
            'matplotlib.backends',
            'matplotlib.backends.backend_wx',
            'matplotlib.backends.backend_wxagg',
            'matplotlib.image',
            'matplotlib.patches',
            'matplotlib.pyplot',
            'numpy',
            'numpy.fft',
            'numpy.linalg',
            'pyparsing',
            'scipy',
            'scipy.interpolate',
            'scipy.ndimage',
            'scipy.ndimage.measurements',
            'scipy.spatial',
            'scipy.spatial.distance',
            'wx',
            'wx.glcanvas',
            'wx.html',
            'wx.lib',
            'wx.lib.agw',
            'wx.lib.agw.aui',
            'wx.lib.newevent',
            'wx.py',
            'wx.py.interpreter',
            'wx.py.shell',
        ]

        mockedModules = {m : mockobj for m in mockedModules}

        # Various classes and types have
        # to be mocked, otherwise we get
        # all sorts of errors in cases
        # of inheritance and monkey
        # patching.
        class MockClass(object):
            def __init__(self, *args, **kwargs):
                pass

        class MockType(type):
            pass

        with mock.patch.dict('sys.modules', **mockedModules), \
             mock.patch('fsl.utils.notifier.Notifier',         MockClass), \
             mock.patch('fsleyes_props.HasProperties',         MockClass), \
             mock.patch('fsleyes_props.SyncableHasProperties', MockClass), \
             mock.patch('fsleyes_props.PropertyOwner',         MockType),  \
             mock.patch('fsleyes_props.Toggle',                MockClass), \
             mock.patch('fsleyes_props.Button',                MockClass), \
             mock.patch('wx.Panel',                            MockClass), \
             mock.patch('wx.glcanvas.GLCanvas',                MockClass), \
             mock.patch('wx.PyPanel',                          MockClass), \
             mock.patch('wx.lib.agw.aui.AuiFloatingFrame',     MockClass), \
             mock.patch('wx.lib.agw.aui.AuiDockingGuide',      MockClass), \
             mock.patch('wx.lib.newevent.NewEvent',    return_value=(0, 0)):
                sphinx.main(['sphinx-build', docdir, destdir])



class userdoc(docbuilder):
    description = 'Builds the FSLeyes user documentation. '
    docdir      = op.join(basedir, 'userdoc')


class apidoc(docbuilder):
    description = 'Builds the FSLeyes API documentation. '
    docdir      = op.join(basedir, 'apidoc')


class custom_build(build):
    description = 'Custom build command. Also builds the '\
                  'user documentation.'

    def run(self):
        self.run_command('userdoc')
        build.run(self)


def list_all_files(in_dir):
    """List all files ``in_dir``. """

    for dirname, dirs, files in os.walk(in_dir):
        for filename in files:
            yield op.join(dirname, filename)


def build_asset_list():
    """Build a list of all the FSLeyes non-source-code files that should
    be included in a distribution.
    """

    assetdir = op.join(basedir, 'assets')
    docdir   = op.join(basedir, 'userdoc', 'html')

    excludePatterns = [
        op.join(assetdir, 'icons', 'app_icon', '*'),
        op.join(assetdir, 'icons', 'splash', 'sources', '*'),
        op.join(assetdir, 'icons', 'sources', '*'),
        op.join(assetdir, 'build', '*'),
        op.join('*', '.DS_Store'),
    ]

    # A dict containing { dest_directory : [files_to_put_in_dest_directory] }
    resources = {}

    docfiles   = list_all_files(docdir)
    assetfiles = list_all_files(assetdir)

    for filename in it.chain(docfiles, assetfiles):

        dirname = op.dirname(filename)
        destdir = op.join(op.relpath(dirname, basedir))
        exclude = any([fnmatch.fnmatch(filename, p) for p in excludePatterns])

        if not exclude:

            flist = resources.get(destdir, [])
            flist.append(filename)
            resources[destdir] = flist

    return list(resources.items())


def get_fsleyes_version():
    """Returns the current FSLeyes version number. """

    # Figure out the current fsleyes version, as defined
    # in fsleyes/version.py. We don't want to import the
    # fsleyes package, as this may cause build problems.
    # So we manually parse the contents of fsl/version.py
    # to extract the version number.
    version = {}
    with open(op.join(basedir, "fsleyes", "version.py")) as f:
        for line in f:
            if line.startswith('__version__'):
                exec(line, version)
                break

    return version.get('__version__')


def get_fsleyes_copyright():
    """Returns the FSLeyes copyright text. """
    with open(op.join(basedir, 'COPYRIGHT')) as f:
        return f.read().strip()


def get_fsleyes_readme():
    """Returns the FSLeyes README text. """
    with open(op.join(basedir, 'README.md'), 'rt') as f:
        return f.read().strip()


def get_fsleyes_deps():
    """Returns a list containing the FSLeyes dependencies. """

    # The dependency list is stored in requirements.txt
    with open(op.join(basedir, 'requirements.txt'), 'rt') as f:
        install_requires = f.readlines()

    return [i.strip() for i in install_requires]


def main():

    packages  = find_packages(
        exclude=('userdoc', 'apidoc', 'assets', 'build', 'dist'))

    version          = get_fsleyes_version()
    readme           = get_fsleyes_readme()
    install_requires = get_fsleyes_deps()
    setup_requires   = ['sphinx', 'sphinx-rtd-theme', 'mock']

    setup(

        name='fsleyes',
        version=version,
        description='FSLeyes, the FSL image viewer',
        long_description=readme,
        url='https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes',
        author='Paul McCarthy',
        author_email='pauldmccarthy@gmail.com',
        license='Apache License Version 2.0',

        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Scientific/Engineering :: Visualization'],

        packages=packages,
        install_requires=install_requires,
        setup_requires=setup_requires,
        include_package_data=True,

        cmdclass={
            'build'   : custom_build,
            'userdoc' : userdoc,
            'apidoc'  : apidoc,
        },
    )


if __name__ == '__main__':
    main()
