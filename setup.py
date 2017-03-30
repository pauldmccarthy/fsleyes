#!/usr/bin/env python
#
# setup.py - setuptools configuration for installing FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from __future__ import print_function

import               platform
import               os
import               shutil
import               fnmatch
import subprocess as sp
import os.path    as op

from setuptools               import setup
from setuptools               import find_packages
from setuptools               import Command
from setuptools.command.sdist import sdist


# "darwin" or "linux"
platform = platform.system().lower()


# The directory in which this
# setup.py file is contained.
basedir = op.dirname(op.abspath(__file__))


if platform == 'darwin':
    from py2app.build_app import py2app
else:
    py2app = object


orig_sdist  = sdist
orig_py2app = py2app


class sdist(orig_sdist):
    """Custom sdist command which inserts the LICENSE text at the
    beginning of every source file.
    """

    
    description = """Builds a FSLeyes source distribution. """

    
    def make_distribution(self):

        # Force distutils.command.sdist to copy
        # files instead of hardlinking them. This
        # hack is performed by setuptools >= 24.3.0,
        # but is not done by earlier versions. 
        link = getattr(os, 'link', None)
        try:
            del(os.link)
        except:
            pass
        
        sdist.make_distribution(self)

        if link is not None:
            os.link = link

            
    def make_release_tree(self, base_dir, files):

        # Make the release tree
        sdist.make_release_tree(self, base_dir, files)

        licence = op.abspath('LICENSE')

        if not op.exists(licence):
            return

        with open(licence, 'rt') as f:
            licence = f.read()

        patchfuncs = {

            '.py'   : self.__patch_py_file,
            '.prog' : self.__patch_prog_file,
            '.glsl' : self.__patch_glsl_file,
 
        }

        # Walk through the release 
        # tree, and patch the license 
        # into every relevant file.
        for root, dirs, files in os.walk(base_dir):
            for filename in files:

                filename  = op.join(root, filename)
                ext       = op.splitext(filename)[1]
                patchfunc = patchfuncs.get(ext)

                if patchfunc is not None:
                    patchfunc(filename, licence)


    def __patch_py_file(self, filename, licence):

        licence = licence.split('\n')
        licence = ['# {0}'.format(l) for l in licence]

        with open(filename, 'rt') as f:
            lines = f.read().split('\n')

        # Remove any existing hashbang line
        if len(lines) > 0 and lines[0].startswith('#!'):
            lines = lines[1:]

        # Insert the fsl hashbang and the licence
        lines = ['#!/usr/bin/env fslpython'] + ['#'] + licence + lines
        lines = ['{0}\n'.format(l) for l in lines]

        with open(filename, 'wt') as f:
            f.writelines(lines)
            
            
    def __patch_prog_file(self, filename, licence):

        licence = licence.split('\n')
        licence = ['# {0}'.format(l) for l in licence]

        with open(filename, 'rt') as f:
            lines = f.read().split('\n')

        # ARB vertex/fragment programs 
        # have a hashbang-like thing as 
        # their first line.
        if len(lines) > 0 and lines[0].startswith('!!'):
            lines = [lines[0]] + licence + lines[1:]
        else:
            lines = licence + lines
            
        lines = ['{0}\n'.format(l) for l in lines]

        with open(filename, 'wt') as f:
            f.writelines(lines)


    def __patch_glsl_file(self, filename, licence):

        licence = licence.split('\n')
        licence = ['/*'] + [' * {0}'.format(l) for l in licence] + [' */']

        with open(filename, 'rt') as f:
            lines = f.read().split('\n')

        lines = licence + lines
        lines = ['{0}\n'.format(l) for l in lines]

        with open(filename, 'wt') as f:
            f.writelines(lines)


class patch_code(Command):

    description  = 'Patches the FSLeyes source code in preparation ' \
                   'for building a standalone distribution'
    
    user_options = []

    def initialize_options(self): pass
    def finalize_options(  self): pass
    def run(self):
        pass 


class py2app(orig_py2app):

    description = 'Builds a standalone FSLeyes OSX application using py2app'

    def finalize_options(self):

        assetdir = op.join(basedir, 'assets')
        iconfile = op.join(assetdir, 'icons', 'app_icon', 'fsleyes.icns')
        plist    = op.join(assetdir, 'buildinfo', 'Info.plist')
        assets   = build_asset_list(basedir)

        self.argv_emulation      = True
        self.iconfile            = iconfile
        self.plist               = plist
        self.resources           = assets
        self.packages            = ['OpenGL_accelerate']
        self.matplotlib_backends = ['wx_agg']
        self.excludes            = ['IPython', 'ipykernel', 'Cython']

        orig_py2app.finalize_options(self)


    def run(self):

        self.run_command('patch_code')
        self.run_command('userdoc')
        orig_py2app.run(self)

        version, gitVersion = get_fsleyes_version(basedir)
        copyright           = get_fsleyes_copyright(basedir)

        plist = op.join(
            basedir, 'dist', 'FSLeyes.app', 'Contents', 'Info.plist')
        
        commands = [
            ['delete', 'PythonInfoDict'],
            ['write',  'CFBundleShortVersionString', version],
            ['write',  'CFBundleVersion',            gitVersion],
            ['write',  'NSHumanReadableCopyright',   copyright],
        ]

        for c in commands:
            sp.call(['defaults'] + [c[0]] + [plist] + c[1:])


class pyinstaller(Command):

    description  = 'Builds a standalone FSLeyes Linux ' \
                   'application using pyinstaller'
    user_options = []

    def initialize_options(self): pass
    def finalize_options(  self): pass
    def run(self):
        pass


class docbuilder(Command):
    """Base class for the userdoc and apidoc commands. """
    
    user_options = []
    
    def initialize_options(self): pass
    def finalize_options(  self): pass 
    def run(self):

        docdir  = self.docdir
        destdir = op.join(docdir, 'html')

        if op.exists(destdir):
            shutil.rmtree(destdir)

        env               = dict(os.environ)
        ppath             = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = op.pathsep.join((ppath, basedir))

        sp.call(['sphinx-build', docdir, destdir], env=env)


class userdoc(docbuilder):
    description = """Builds the FSLeyes user documentation. """
    docdir      = op.join(basedir, 'userdoc')

    
class apidoc(docbuilder):
    description = """Builds the FSLeyes API documentation. """
    docdir      = op.join(basedir, 'apidoc')


def list_all_files(in_dir):
    """List all files ``in_dir``.
    """
    
    for dirname, dirs, files in os.walk(in_dir):
        for filename in files:
            yield op.join(dirname, filename) 


def build_asset_list(basedir):
    """Build a list of all the FSLeyes non-source-code files that should
    be included in a distribution built by py2app.
    """

    basedir  = op.abspath(basedir)
    assetdir = op.join(basedir, 'assets')
    docdir   = op.join(basedir, 'userdoc', 'html')
    
    excludePatterns = [
        op.join(assetdir, 'icons', 'app_icon', '*'),
        op.join(assetdir, 'icons', 'splash', 'sources', '*'),
        op.join(assetdir, 'icons', 'sources', '*'),
        op.join(assetdir, 'buildinfo', '*'),
        op.join('*', '.DS_Store'),
    ]

    # A dict containing { dest_directory : [files_to_put_in_dest_directory] }
    resources = {}

    # resources['assets']  = []
    resources['userdoc'] = list(list_all_files(docdir))

    for filename in list_all_files(assetdir):

        dirname = op.dirname(filename)
        destdir = op.join(op.relpath(dirname, basedir))
        exclude = any([fnmatch.fnmatch(filename, p) for p in excludePatterns])

        if not exclude:
            
            flist = resources.get(destdir, [])
            flist.append(filename)
            resources[destdir] = flist
    
    return resources.items()


def get_fsleyes_version(basedir):

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
            elif line.startswith('__vcs_version__'):
                exec(line, version)

    return version.get('__version__'), version.get('__vcs_version__')


def get_fsleyes_copyright(basedir):
    with open(op.join(basedir, 'COPYRIGHT')) as f:
        return f.read().strip()


def get_fsleyes_deps(basedir):

    # The dependency list is stored in requirements.txt
    with open(op.join(basedir, 'requirements.txt'), 'rt') as f:
        install_requires = f.readlines()
        
    dependency_links = [i for i in install_requires if     i.startswith('git')]
    install_requires = [i for i in install_requires if not i.startswith('git')]

    return install_requires, dependency_links


def main():

    version   = get_fsleyes_version(basedir)[0]
    copyright = get_fsleyes_copyright(basedir)
    packages  = find_packages(exclude=('userdoc', 'apidoc', 'assets'))

    deps             = get_fsleyes_deps(basedir)
    install_requires = deps[0]
    dependency_links = deps[1]
    
    if platform == 'darwin': setup_requires = ['py2app']
    else:                    setup_requires = []

    setup(

        name='fsleyes',
        version=version,
        description='FSLeyes, the FSL image viewer',
        url='https://git.fmrib.ox.ac.uk/paulmc/fsleyes',
        author='Paul McCarthy',
        author_email='pauldmccarthy@gmail.com',
        license='Apache License Version 2.0',
        copyright=copyright,

        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 2.7',
            # 'Programming Language :: Python :: 3.5',
            'Topic :: Software Development :: Libraries :: Python Modules'],

        packages=packages,
        install_requires=install_requires,
        dependency_links=dependency_links,

        cmdclass={
            'sdist'       : sdist,
            'patch_code'  : patch_code,
            'py2app'      : py2app,
            'pyinstaller' : pyinstaller,
            'userdoc'     : userdoc,
            'apidoc'      : apidoc,
        },

        app=['fsleyes/__main__.py'],
        setup_requires=setup_requires,
    )


if __name__ == '__main__':
    main()
