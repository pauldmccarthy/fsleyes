#!/usr/bin/env python
#
# setup.py - setuptools configuration for installing FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Setup script for FSLeyes.

The following custom commands are available:

 - ``sdist``            - Build source distribution
 - ``bdist_wheel``      - Build universal wheel (if wheel is installed)
 - ``userdoc``          - Build the user documentation
 - ``apidoc``           - Build the source documentation
 - ``build_standalone`` - Build a standalone version of FSLeyes ising py2app
                          (macOS) or pyinstaller (Linux).


For the ``build_standalone`` command, you must install all of the FSLeyes
dependencies prior to calling ``setup.py``.


For standalone Linux builds, you must install pyinstaller prior to calling
``setup..py``. Version 3.2.1 is known to work.


For standalone macOS builds, you must install py2app 0.12 prior to calling
``setup.py``, and patch and recompile it as described below.


.. warning:: The ``build_standalone`` will modify the ``fsleyes``, ``fslpy``,
             ``fsleyes-props`` and ``fsleyes-widgets`` (stripping log
             statements) unless you use either the ``--enable-logging`` or
             ``--skip-patch-code`` options.


============
Py2App notes
============


I am currently using py2app 0.12 for macOS builds. There are a couple of
issues with this version of py2app which we need to work around:

https://bitbucket.org/ronaldoussoren/py2app/issues/222/argv-emulation-only-works-when-redirect):

https://bitbucket.org/ronaldoussoren/py2app/issues/140/app-starts-minimized


The patch found in ``assets/build/py2app.patch`` must be applied to the py2app
source, and the py2app bootloader needs to be recompiled::

    cd path/to/py2app/
    patch -p2 < path/to/fsleyes/assets/build/py2app.patch
    cd apptemplate/
    python setup.py
"""


from __future__ import print_function

import               os
import               sys
import               glob
import               shutil
import               pkgutil
import               fnmatch
import               platform
import               logging
import subprocess as sp
import itertools  as it
import os.path    as op

from collections import defaultdict
from io          import open

from setuptools import setup
from setuptools import find_packages
from setuptools import Command

from distutils.command.build import build


# Expected to be "darwin" or "linux"
platform = platform.system().lower()


# The directory in which this
# setup.py file is contained.
basedir = op.dirname(op.abspath(__file__))


try:
    from py2app.build_app import py2app as orig_py2app

# A dummy orig_py2app class, so my
# py2app class definition won't
# break if py2app is not present
except:
    class orig_py2app(Command):
        user_options = []

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            pass


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
            'fsl.version',
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
    description = 'Custom build command which builds the '\
                  'user documentation.'

    def run(self):

        self.run_command('userdoc')

        # In its source form, the FSLeyes asset files
        # and documentation live outside the FSLeyes
        # package directroy hierarchy. But setuptools
        # does not like this arrangement. So here I am
        # linking the assets and userdocs into the
        # fsleyes package directory, to trick setuptools
        # into including them in bdists and installations.
        linkins = ['assets', 'userdoc']

        for l in linkins:

            target = op.join(basedir, l)
            link   = op.join(basedir, 'fsleyes', l)

            if not op.exists(link):
                os.symlink(target, link)

        build.run(self)


class build_standalone(Command):
    description = 'Build a standalone FSLeyes application ' \
                  'using py2app or pyinstaller.'
    user_options = [
        ('skip-patch-code', 'c', 'Skip code patch step'),
        ('skip-build',      'b', 'Skip build'),
        ('enable-logging',  'l', 'Enable logging'),
    ]

    boolean_options = [
        'skip-patch-code',
        'skip-build',
        'enable-logging'
    ]

    def initialize_options(self):
        self.skip_patch_code = False
        self.skip_build      = False
        self.enable_logging  = False

    def finalize_options(self):
        pass

    def run(self):

        # Build user documentation
        self.run_command('userdoc')

        # Patch code (disable GL debug, remove logging, etc)
        if not self.skip_patch_code:
            self.patch_code(self.enable_logging)

        # run py2app or pyinstaller
        if not self.skip_build:
            if platform == 'darwin': self.run_command('py2app')
            else:                    self.run_command('pyinstaller')

        # create a zip file
        distdir     = op.join(basedir, 'dist')
        archivefile = op.join(distdir,
                              'FSLeyes-{}'.format(get_fsleyes_version()))

        if platform == 'darwin': archivedir = 'FSLeyes.app'
        else:                    archivedir = 'FSLeyes'

        print('Creating {}.zip...'.format(archivefile))
        shutil.make_archive(archivefile,
                            'zip',
                            root_dir=distdir,
                            base_dir=archivedir)


    def patch_code(self, enableLogging):

        propsdir   = op.join(package_path('fsleyes_props'),
                             'fsleyes_props')
        widgetsdir = op.join(package_path('fsleyes_widgets'),
                             'fsleyes_widgets')
        fslpydir   = op.join(package_path('fsl'),
                             'fsl')
        fsleyesdir = op.join(package_path('fsleyes'),
                             'fsleyes')

        def patch_file(filename, linepatch):

            old = filename
            new = '{}.patch'.format(filename)

            with open(old, 'rt') as inf, \
                 open(new, 'wt') as outf:

                for line in inf:
                    outf.write(linepatch(line))

            os.rename(new, old)

        def patch_gl():

            def linepatch(line):
                if line.startswith('OpenGL.ERROR_CHECKING'):
                    line = 'OpenGL.ERROR_CHECKING = False\n'
                elif line.startswith('OpenGL.ERROR_LOGGING'):
                    line = 'OpenGL.ERROR_LOGGING = False\n'
                return line

            filename = op.join(fsleyesdir, 'gl', '__init__.py')

            print('Setting up OpenGL initialisation: {}'.format(filename))

            patch_file(filename, linepatch)

        def remove_logging():

            logstripdir = op.join(basedir, 'assets', 'build')
            sys.path.append(logstripdir)
            import logstrip

            logging.getLogger('logstrip').setLevel(logging.CRITICAL)

            propsfiles   = list_all_files(propsdir)
            widgetsfiles = list_all_files(widgetsdir)
            fslpyfiles   = list_all_files(fslpydir)
            fsleyesfiles = list_all_files(fsleyesdir)

            print('Removing logging: {}'.format(propsdir))
            print('Removing logging: {}'.format(widgetsdir))
            print('Removing logging: {}'.format(fslpydir))
            print('Removing logging: {}'.format(fsleyesdir))

            for filename in it.chain(
                    propsfiles, widgetsfiles, fslpyfiles, fsleyesfiles):
                if not filename.endswith('.py'):
                    continue
                logstrip.main(['-f', '-M', 'INFO', filename])

        def enable_logging():

            def linepatch(line):
                if line.startswith('disableLogging'):
                    line = 'disableLogging = False\n'
                return line

            filename = op.join(fsleyesdir, '__init__.py')

            print('Enabling logging: {}'.format(filename))

            patch_file(filename, linepatch)

        patch_gl()
        if self.enable_logging: enable_logging()
        else:                   remove_logging()


class py2app(orig_py2app):
    description = 'Builds a standalone FSLeyes OSX application using '\
                  'py2app. Not intended to be called directly.'

    def finalize_options(self):

        entrypt     = op.join(basedir, 'fsleyes', '__main__.py')
        assetdir    = op.join(basedir, 'assets')
        iconfile    = op.join(assetdir, 'icons', 'app_icon', 'fsleyes.icns')
        dociconfile = op.join(assetdir, 'icons', 'app_icon',
                              'fsleyes_doc.icns')
        plist       = op.join(assetdir, 'build', 'Info.plist')
        assets      = build_asset_list(False)

        self.quiet               = True
        self.argv_emulation      = True
        self.no_chdir            = True
        self.optimize            = True
        self.app                 = [entrypt]
        self.iconfile            = iconfile
        self.dociconfile         = dociconfile
        self.plist               = plist
        self.resources           = assets
        self.packages            = ['OpenGL_accelerate']
        self.matplotlib_backends = ['wx_agg']
        self.excludes            = ['IPython', 'ipykernel', 'Cython']

        orig_py2app.finalize_options(self)


    def run(self):

        orig_py2app.run(self)

        version     = get_fsleyes_version()
        copyright   = get_fsleyes_copyright()

        distdir     = op.join(basedir, 'dist')
        contentsdir = op.join(distdir, 'FSLeyes.app', 'Contents')
        plist       = op.join(contentsdir, 'Info.plist')
        resourcedir = op.join(contentsdir, 'Resources')

        # py2app (and pyinstaller) seem to
        # get the wrong version of libpng,
        # which causes render to segfault
        pildir = package_path('PIL')
        dylib  = op.join(pildir, '.dylibs', 'libpng16.16.dylib')
        if op.exists(dylib):
            shutil.copy(dylib, op.join(contentsdir, 'Frameworks'))

        # copy the application document iconset
        shutil.copy(self.dociconfile, resourcedir)

        # Patch Info.plist
        commands = [
            ['delete', 'PythonInfoDict'],
            ['write',  'CFBundleShortVersionString', version],
            ['write',  'CFBundleVersion',            version],
            ['write',  'NSHumanReadableCopyright',   copyright],
        ]

        for c in commands:
            sp.call(['defaults'] + [c[0]] + [plist] + c[1:])

        # The defaults command screws with Info.plist
        # so make sure it has rw-r--r-- permissions
        sp.call(['chmod', '644', plist])


class pyinstaller(Command):
    description  = 'Builds a standalone FSLeyes Linux ' \
                   'application using pyinstaller. Not intended to be '\
                   'called directly.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):

        builddir = op.join(basedir, 'build')
        distdir  = op.join(basedir, 'dist')
        assetdir = op.join(distdir, 'FSLeyes', 'share', 'FSLeyes')
        iconfile = op.join(assetdir, 'icons', 'app_icon', 'fsleyes.ico')
        assets   = build_asset_list(False)
        entrypt  = op.join(basedir, 'fsleyes', '__main__.py')

        hidden = [
            'scipy.special._ufuncs_cxx',
            'scipy.linalg.cython_blas',
            'scipy.linalg.cython_lapack',
            'scipy.integrate',
            'OpenGL_accelerate',
            'OpenGL.platform.osmesa',
            'OpenGL.GLUT'
        ]

        excludes = [
            'IPython',
            'jinja2.asyncfilters',
            'jinja2.asyncsupport',
        ]

        extrabins = ['glut', 'OSMesa', 'xcb', 'SDL-1.2']
        extrabins = [find_library(b)  for b in extrabins]
        extrabins = ['{}:.'.format(b) for b in extrabins]

        cmd = [
            'pyinstaller',
            '--name=FSLeyes',
            '--icon={}'.format(iconfile),
            '--windowed',
            '--workpath={}'.format(builddir),
            '--distpath={}'.format(distdir)
        ]

        for h in hidden:    cmd += ['--hidden-import',  h]
        for e in excludes:  cmd += ['--exclude-module', e]
        for e in extrabins: cmd += ['--add-binary',     e]

        cmd += [entrypt]

        sp.call(cmd)

        # Move the spec file into the build directory
        shutil.move(op.join(basedir, 'FSLeyes.spec'), builddir)

        # Make the executable lowercase
        try:
            os.rename(op.join(distdir, 'FSLeyes', 'FSLeyes'),
                      op.join(distdir, 'FSLeyes', 'fsleyes'))

        # Case insensitive file system?
        except:
            pass

        # Something is wrong with the way
        # that PyOpenGL tries to find
        # the libglut library. If we make
        # a symlink, called 'glut', to the
        # .so file, things work fine.
        libglut = glob.glob(op.join(distdir, 'FSLeyes', 'libglut*'))
        if len(libglut) != 1:
            raise RuntimeError('Cannot identify libglut')

        os.symlink(libglut[0], op.join(distdir, 'FSLeyes', 'glut'))

        # Copy assets
        os.makedirs(assetdir)
        for dirname, files in assets:

            dirname = op.join(assetdir, dirname)

            if not op.exists(dirname):
                os.makedirs(dirname)

            for src in files:
                shutil.copy(src, dirname)


def find_library(name):
    """Returns the path o the given shared library. """

    import ctypes.util as cutil

    path = cutil.find_library(name)

    if path is None:
        raise RuntimeError('Library {} not found'.format(name))

    # Under mac, find_library
    # returns the full path
    if platform == 'darwin':
        return path

    print('Searching for: {}'.format(path))

    # Under linux, find_library
    # just returns a file name.
    # Let's look for it in some
    # likely locations.
    searchDirs = ['/lib64/',
                  '/lib/',
                  '/usr/lib64/',
                  '/usr/lib/',
                  '/usr/lib/x86_64-linux-gnu']
    for sd in searchDirs:
        searchPath = op.join(sd, path)
        if op.exists(searchPath):
            return searchPath

    raise RuntimeError('Could not find location for library {}'.format(name))


def package_path(pkg):
    """Returns the directory path to the given python package. """
    fname   = pkgutil.get_loader(pkg).get_filename()
    dirname = op.dirname(fname)
    dirname = op.abspath(op.join(dirname, '..'))
    return dirname


def list_all_files(in_dir):
    """List all files ``in_dir``. """

    for dirname, dirs, files in os.walk(in_dir):
        for filename in files:
            yield op.join(dirname, filename)


def build_asset_list(flat):
    """Build and return a list of all the FSLeyes non-source-code files that
    should be included in a distribution. The file paths are made relative
    to the FSLeyes base directory.

    :arg flat: If ``True``, a list is returned. Othewrise, a list of the form::

                   [ (dest_directory, [files_to_put_in_dest_directory]),
                     ...
                   ]

               is returned.
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

    flist      = defaultdict(list)
    docfiles   = list_all_files(docdir)
    assetfiles = list_all_files(assetdir)

    for filename in it.chain(docfiles, assetfiles):

        exclude = any([fnmatch.fnmatch(filename, p) for p in excludePatterns])

        if not exclude:
            destdir = op.relpath(op.dirname(filename), basedir)
            flist[destdir].append(filename)

    if flat:
        return list(it.chain(*[flist[k] for k in flist.keys()]))
    else:
        return list(flist.items())


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
    with open(op.join(basedir, 'README.rst'), 'rt', encoding='utf-8') as f:
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
    assets           = build_asset_list(True)
    setup_requires   = ['sphinx', 'sphinx-rtd-theme', 'mock']

    # When building/installing, all asset files
    # are placed within the fsleyes package
    # directory. Some related ugliness is present
    # in the custom_build command.
    assets = {'fsleyes' : assets}

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
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Scientific/Engineering :: Visualization'],

        packages=packages,
        install_requires=install_requires,
        setup_requires=setup_requires,
        include_package_data=True,
        package_data=assets,

        cmdclass={
            'build'            : custom_build,
            'userdoc'          : userdoc,
            'apidoc'           : apidoc,
            'py2app'           : py2app,
            'pyinstaller'      : pyinstaller,
            'build_standalone' : build_standalone,
        },

        entry_points={
            'console_scripts' : [
                'fsleyes = fsleyes.main:main',
            ]
        }
    )


if __name__ == '__main__':

    logging.basicConfig()
    main()
