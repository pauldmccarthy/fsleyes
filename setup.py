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
"""


from __future__ import print_function

import               os
import               shutil
import               fnmatch
import               logging
import itertools  as it
import os.path    as op

from collections import defaultdict
from io          import open

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
        mockedModules = open(op.join(docdir, 'mock_modules.txt')).readlines()
        mockedClasses = open(op.join(docdir, 'mock_classes.txt')).readlines()
        mockedModules = {m.strip() : mockobj for m in mockedModules}
        mockedClasses = [l.strip() for l in mockedClasses]

        class MockClass(object):
            def __init__(self, *args, **kwargs):
                pass

        class MockType(type):
            pass

        patches = [mock.patch.dict('sys.modules', **mockedModules)] + \
                  [mock.patch('wx.lib.newevent.NewEvent',
                              return_value=(mockobj, mockobj))]     + \
                  [mock.patch(c, MockClass) for c in mockedClasses]    + \
                  [mock.patch('fsleyes_props.PropertyOwner', MockType)]

        [p.start() for p in patches]
        sphinx.build_main(['sphinx-build', docdir, destdir])
        [p.stop() for p in patches]


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
    with open(op.join(basedir, 'requirements.txt'), 'rt') as f:
        install_requires = f.readlines()
    return [i.strip() for i in install_requires]


def get_fsleyes_extra_deps():
    """Returns a dict specifying the extra FSLeyes dependencies."""
    with open(op.join(basedir, 'requirements-extra.txt'), 'rt') as f:
        extras_require = f.readlines()
    return {'extras' : [r.strip() for r in extras_require]}


def get_fsleyes_dev_deps():
    """Returns a dict specifying the FSLeyes development dependencies."""
    with open(op.join(basedir, 'requirements-dev.txt'), 'rt') as f:
        setup_requires = f.readlines()
    return [i.strip() for i in setup_requires]


def main():

    packages  = find_packages(
        exclude=('userdoc', 'apidoc', 'assets', 'build', 'dist'))

    version          = get_fsleyes_version()
    readme           = get_fsleyes_readme()
    install_requires = get_fsleyes_deps()
    extras_require   = get_fsleyes_extra_deps()
    setup_requires   = get_fsleyes_dev_deps()
    tests_require    = setup_requires
    assets           = build_asset_list(True)

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
        extras_require=extras_require,
        setup_requires=setup_requires,
        tests_require=tests_require,

        include_package_data=True,
        package_data=assets,
        test_suite='tests',

        cmdclass={
            'build'   : custom_build,
            'userdoc' : userdoc,
            'apidoc'  : apidoc,
        },

        entry_points={
            'console_scripts' : [
                'fsleyes = fsleyes.main:main',
                'render  = fsleyes.render:main',
            ]
        }
    )


if __name__ == '__main__':
    logging.basicConfig()

    def dummy_log(*args, **kwargs):
        pass

    # some things are awfully loud, and
    # distutils does its own logging.
    import distutils.log as dul
    dul._global_log._log = dummy_log

    logging.getLogger('py2app')    .setLevel(logging.CRITICAL)
    logging.getLogger('distutils') .setLevel(logging.CRITICAL)
    logging.getLogger('setuptools').setLevel(logging.CRITICAL)

    main()
