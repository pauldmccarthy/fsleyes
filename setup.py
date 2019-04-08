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
import               contextlib
import               platform
import os.path    as op
from io import       open

from setuptools import setup
from setuptools import find_packages
from setuptools import Command

from distutils.command.build import build


# The directory in which this
# setup.py file is contained.
basedir = op.dirname(op.abspath(__file__))


# Expected to be "darwin" or "linux"
platform = platform.system().lower()


@contextlib.contextmanager
def templinks(targets, dests):
    """Used by the ``custom_build`` class to create temporary symlinks to
    non-python files, so they get included in built-distributions.
    """
    try:
        for target, dest in zip(targets, dests):
            if not op.exists(dest):
                if hasattr(os, 'symlink'):
                    os.symlink(target, dest)
                elif op.isfile(target):
                    shutil.copy(target, dest)
                elif op.isdir(target):
                    shutil.copytree(target, dest)

        yield

    finally:
        for dest in dests:
            if op.exists(dest):
                if hasattr(os, 'symlink'):
                    os.remove(dest)
                elif op.isfile(dest):
                    os.remove(dest)
                elif op.isdir(dest):
                    shutil.rmtree(dest)


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

        import sphinx.cmd.build as sphinx_build

        try:
            import unittest.mock as mock
        except ImportError:
            import mock

        # Sigh. Why can't I mock a package?
        mockobj       = mock.MagicMock()
        mockedModules = open(op.join(docdir, 'mock_modules.txt')).readlines()
        mockedClasses = open(op.join(docdir, 'mock_classes.txt')).readlines()
        mockedModules = {m.strip() : mockobj for m in mockedModules}
        mockedClasses = {l.strip() : None    for l in mockedClasses}

        # a different mock class for each mocked class
        for clsname in mockedClasses.keys():
            class MockClass(object):
                def __init__(self, *args, **kwargs):
                    pass
            mockedClasses[clsname] = MockClass

        class MockType(type):
            pass

        patches = [mock.patch.dict('sys.modules', **mockedModules)]    + \
                  [mock.patch('wx.lib.newevent.NewEvent',
                              return_value=(mockobj, mockobj))]        + \
                  [mock.patch(n, c) for n, c in mockedClasses.items()] + \
                  [mock.patch('fsleyes_props.PropertyOwner', MockType)]

        [p.start() for p in patches]
        sphinx_build.main([docdir, destdir])
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
        #
        # I can't believe that this is so difficult to
        # accomplish.
        targets = ['assets', op.join('userdoc', 'html')]
        dests   = ['assets', 'userdoc']
        targets = [op.join(basedir, t)            for t in targets]
        dests   = [op.join(basedir, 'fsleyes', d) for d in dests]

        with templinks(targets, dests):
            build.run(self)


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
    """Returns a dict specifying the extra and platform-specific FSLeyes
    dependencies.
    """
    with open(op.join(basedir, 'requirements-extra.txt'), 'rt') as f:
        extras_require = [r.strip() for r in f.readlines()]

    with open(op.join(basedir, 'requirements-notebook.txt'), 'rt') as f:
        nb_require = [r.strip() for r in f.readlines()]

    platform_requires = []
    platform_file = op.join(basedir, 'requirements-{}.txt'.format(platform))

    if op.exists(platform_file):
        with open(platform_file, 'rt') as f:
            platform_requires = [r.strip() for r in f.readlines()]

    return {'extras' : extras_require + nb_require + platform_requires}


def get_fsleyes_dev_deps():
    """Returns a dict specifying the FSLeyes development dependencies."""
    with open(op.join(basedir, 'requirements-dev.txt'), 'rt') as f:
        setup_requires = f.readlines()
    return [i.strip() for i in setup_requires]


def main():

    packages         = find_packages(exclude=('tests', ))
    version          = get_fsleyes_version()
    readme           = get_fsleyes_readme()
    install_requires = get_fsleyes_deps()
    extras_require   = get_fsleyes_extra_deps()

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

        # This is needed to ensure that non-python
        # files are included in built distributions
        include_package_data=True,

        test_suite='tests',

        cmdclass={
            'build'   : custom_build,
            'userdoc' : userdoc,
            'apidoc'  : apidoc,
        },

        entry_points={
            'console_scripts' : [
                'render  = fsleyes.render:main',
            ],
            'gui_scripts' : [
                'fsleyes = fsleyes.main:main',
            ]
        }
    )


if __name__ == '__main__':
    main()
