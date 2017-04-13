#!/usr/bin/env python
#
# setup.py - setuptools configuration for installing FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Setup script for FSLeyes.

The following commands are available:

 - sdist            - Build a source distribution
 - userdoc          - Build the user documentation
 - apidoc           - Build the source documentation
 - build_standalone - Build a standalone version of FSLeyes ising py2app (OSX)
                      or pyinstaller (Linux).

============
Py2App notes
============

I am currently using py2app 0.12 for OSX builds. There are a couple of issues
with this version of py2app which we need to work around:

https://bitbucket.org/ronaldoussoren/py2app/issues/222/argv-emulation-only-works-when-redirect):
https://bitbucket.org/ronaldoussoren/py2app/issues/140/app-starts-minimized


The following patch must be applied to the py2app source::

    --- orig/py2app/apptemplate/src/main.c	2017-02-22 10:32:57.000000000 +0000
    +++ patch/py2app/apptemplate/src/main.c	2017-04-04 15:52:20.000000000 +0100
    @@ -1147,7 +1147,6 @@
        do_asl_log_descriptor(cl, msg, 4 /* ASL_LEVEL_NOTICE */, 2, 2 /* ASL_LOG_DESCRIPTOR_WRITE */);
     }

    -#ifndef PY2APP_SECONDARY
     static int
     have_psn_arg(int argc, char* const * argv)
     {
    @@ -1162,7 +1161,6 @@
        }
        return 0;
     }
    -#endif /* !PY2APP_SECONDARY */


     int
    @@ -1170,7 +1168,6 @@
     {
         int rval;

    -#ifndef PY2APP_SECONDARY
         /* Running as a GUI app started by launch
          * services, try to redirect stdout/stderr
          * to ASL.
    @@ -1217,9 +1214,10 @@
            bname++;
             }

    +#ifndef PY2APP_SECONDARY
             setup_asl(bname);
    -    }
     #endif /* !PY2APP_SECONDARY */
    +  }

         if (bind_CoreFoundation()) {
             fprintf(stderr, "CoreFoundation not found or functions missing\n");
    --- orig/py2app/bootstrap/argv_emulation.py	2017-02-22 10:32:57.000000000 +0000
    +++ patch/py2app/bootstrap/argv_emulation.py	2017-04-04 17:16:54.000000000 +0100
    @@ -88,7 +88,7 @@

         return carbon

    -def _run_argvemulator(timeout = 60):
    +def _run_argvemulator(timeout = 5):

         # Configure ctypes
         carbon = _ctypes_setup()
    @@ -113,6 +113,7 @@
         FALSE               = b'\0'
         TRUE                = b'\1'
         eventLoopTimedOutErr = -9875
    +    eventParameterNotFoundErr = -9870

         kEventClassAppleEvent, = struct.unpack('>i', b'eppc')
         kEventAppleEvent = 1
    @@ -242,7 +243,7 @@
             event = ctypes.c_void_p()

             sts = carbon.ReceiveNextEvent(1, ctypes.byref(eventType),
    -                start + timeout[0] - now, TRUE, ctypes.byref(event))
    +                start + timeout[0] - now, FALSE, ctypes.byref(event))

             if sts == eventLoopTimedOutErr:
                 break
    @@ -252,10 +253,17 @@
                 break

             sts = carbon.AEProcessEvent(event)
    -        if sts != 0:
    +
    +        # No events
    +        if sts == eventParameterNotFoundErr:
    +            break
    +
    +        elif sts != 0:
                 print("argvemulator warning: processing events failed")
                 break

    +        now = time.time()
    +

         carbon.AERemoveEventHandler(kCoreEventClass, kAEOpenApplication,
                 open_app_handler, FALSE)


Then the py2app bootloader needs to be recompiled::

    cd py2app/apptemplate/
    python setup.py
"""


from __future__ import print_function

import               platform
import               pkgutil
import               os
import               sys
import               shutil
import               fnmatch
import itertools  as it
import subprocess as sp
import os.path    as op

from setuptools import setup
from setuptools import find_packages
from setuptools import Command


# "darwin" or "linux"
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


class build_standalone(Command):
    description = 'Build a standalone FSLeyes application ' \
                  'using py2app or pyinstaller.'
    user_options = [
        ('version=',        'v', 'FSLeyes version'),
        ('props-version=',  'p', 'props version'),
        ('fslpy-version=',  'f', 'fslpy version'),
        ('skip-patch-code', 'c', 'Skip code patch step'),
        ('skip-build',      'b', 'Skip build'),
        ('enable-logging',  'l', 'Enable logging'),
    ]

    boolean_options = [
        'skip-patch-code',
        'enable-logging'
    ]
 
    def initialize_options(self):
        self.version         = None
        self.props_version   = None
        self.fslpy_version   = None
        self.skip_patch_code = False
        self.skip_build      = False
        self.enable_logging  = False

    def finalize_options(self):
        pass

    def run(self):

        if op.exists(op.join(basedir, 'build')):
            shutil.rmtree(op.join(basedir, 'build'))
        
        # Check out props/fslpy
        checkout = self.distribution.get_command_obj('checkout_subprojects')
        checkout.props_version = self.props_version
        checkout.fslpy_version = self.fslpy_version

        self.run_command('checkout_subprojects')

        # Make a copy of the fsleyes source,
        # because patch_code makes changes to
        # it, and we restore these changes
        # after the build
        shutil.copytree(op.join(basedir, 'fsleyes'),
                        op.join(basedir, 'build', 'fsleyes.backup'))

        sys.path.insert(0, basedir)
        sys.path.insert(0, op.join(basedir, 'build', 'fslpy'))
        sys.path.insert(0, op.join(basedir, 'build', 'props'))

        try:

            # Patch code (remove log calls, and set
            # up fsleyes logging/GL initialisation)
            if not self.skip_patch_code:

                pc                = self.distribution.get_command_obj('patch_code')
                pc.enable_logging = self.enable_logging
                pc.version        = self.version

                self.run_command('patch_code')

            # Build user documentation
            self.run_command('userdoc')

            # run py2app or pyinstaller
            if not self.skip_build:
                if platform == 'darwin': self.run_command('py2app')
                else:                    self.run_command('pyinstaller')

            # create a zip file
            archivefile = op.join(basedir, 'dist', 'FSLeyes-{}'.format(
                get_fsleyes_version()))

            distdir = op.join(basedir, 'dist')

            if platform == 'darwin': archivedir = 'FSLeyes.app'
            else:                    archivedir = 'FSLeyes'

            print('Creating {}.zip...'.format(archivefile))
            shutil.make_archive(archivefile,
                                'zip',
                                root_dir=distdir,
                                base_dir=archivedir)

        finally:
            shutil.rmtree(op.join(basedir, 'fsleyes'))
            shutil.move(  op.join(basedir, 'build', 'fsleyes.backup'),
                          op.join(basedir, 'fsleyes'))
        

class checkout_subprojects(Command):
    description = 'Checks out the props and fslpy '\
                  'projects into [fsleyesdir]/build/'
    
    user_options = [
        ('props-version=',  'p', 'props version (default: master; set '
                                 'to \'local\' to use from PYTHONPATH)'),
        ('fslpy-version=',  'f', 'fslpy version (default: master; set '
                                 'to \'local\' to use from PYTHONPATH)'),
    ]

    def initialize_options(self):
        self.props_version = None
        self.fslpy_version = None

    def finalize_options(self):
        if self.props_version is None:
            self.props_version = 'master'
            
        if self.fslpy_version is None:
            self.fslpy_version = 'master'

    def run(self):

        builddir  = op.join(basedir,  'build')
        propsdest = op.join(builddir, 'props')
        fslpydest = op.join(builddir, 'fslpy')

        if not op.exists(builddir):  os.makedirs(builddir)
        if     op.exists(propsdest): shutil.rmtree(propsdest)
        if     op.exists(fslpydest): shutil.rmtree(fslpydest)

        if self.props_version == 'local':
            
            print('Copying props [local] to {}'.format(propsdest))
            propsdir = pkgutil.get_loader('props').filename
            propsdir = op.abspath(op.join(propsdir, '..'))
            shutil.copytree(propsdir, propsdest)
            sys.path_importer_cache.pop(propsdir)
            
        else:
            print('Checking out props [{}] to {}'.format(
                self.props_version, propsdest)) 
            checkout('props', self.props_version, propsdest)

        if self.fslpy_version == 'local':
            
            print('Copying fslpy [local] to {}'.format(fslpydest)) 
            fslpydir = pkgutil.get_loader('fsl').filename
            fslpydir = op.abspath(op.join(fslpydir, '..'))
            shutil.copytree(fslpydir, fslpydest)
            sys.path_importer_cache.pop(fslpydir)
            
        else:
            print('Checking out fslpy [{}] to {}'.format(
                self.fslpy_version, fslpydest)) 
            checkout('fslpy', self.fslpy_version, fslpydest)
            

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

        env   = dict(os.environ)
        ppath = [
            op.join(pkgutil.get_loader('fsleyes').filename, '..'),
            op.join(pkgutil.get_loader('fsl')    .filename, '..'),
            op.join(pkgutil.get_loader('props')  .filename, '..')]
        
        env['PYTHONPATH'] = op.pathsep.join(ppath)

        print('Building documentation [{}]'.format(destdir))

        sphinx = sp.check_output(['which', 'sphinx-build']).strip()

        # Framwork python needs to be used on osx
        if platform == 'darwin':
            sp_call(['pythonw', sphinx, docdir, destdir], env=env)
        else:
            sp_call(['python',  sphinx, docdir, destdir], env=env)


class userdoc(docbuilder):
    description = """Builds the FSLeyes user documentation. """
    docdir      = op.join(basedir, 'userdoc')

    
class apidoc(docbuilder):
    description = """Builds the FSLeyes API documentation. """
    docdir      = op.join(basedir, 'apidoc')


class patch_code(Command):

    description  = 'Patches the FSLeyes source code in preparation ' \
                   'for building a standalone distribution'
    
    user_options = [
        ('enable-logging', 'l', 'Enable logging'),
        ('version=',       'v', 'FSLeyes version number (overwrites '
                                 'that listed in source code)'),
    ]

    boolean_options = ['enable-logging']

    def initialize_options(self):
        self.enable_logging = False
        self.version        = None

    def finalize_options(self):
        if self.version is None:
            self.version = get_fsleyes_version()

    def run(self):

        propsdir   = op.join(pkgutil.get_loader('props')  .filename)
        fslpydir   = op.join(pkgutil.get_loader('fsl')    .filename)
        fsleyesdir = op.join(pkgutil.get_loader('fsleyes').filename)

        def patch_file(filename, linepatch):

            old = filename
            new = '{}.patch'.format(filename)

            with open(old, 'rt') as inf, \
                 open(new, 'wt') as outf:

                for line in inf:
                    outf.write(linepatch(line))

            os.rename(new, old) 

        def patch_version():

            filename   = op.join(fsleyesdir, 'version.py')
            version    = get_fsleyes_version()
            gitVersion = get_git_version()

            def linepatch(line):
                if line.startswith('__version__'):
                    line = '__version__ = \'{}\'\n'.format(version)
                elif line.startswith('__vcs_version__'):
                    line = '__vcs_version__ = \'{}\'\n'.format(gitVersion)
                return line

            print('Patching FSLeyes version [{} / {}]: {}'.format(
                version, gitVersion, filename))
            
            patch_file(filename, linepatch)

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

            propsfiles   = list_all_files(propsdir)
            fslpyfiles   = list_all_files(fslpydir)
            fsleyesfiles = list_all_files(fsleyesdir)

            print('Removing logging: {}'.format(propsdir))
            print('Removing logging: {}'.format(fslpydir))
            print('Removing logging: {}'.format(fsleyesdir))

            for filename in it.chain(propsfiles, fslpyfiles, fsleyesfiles):
                if not filename.endswith('.py'):
                    continue

                logstrip = op.join(basedir, 'assets', 'build', 'logstrip.py')

                sp_call(['python', logstrip, '-f', '-M', 'INFO', filename],
                        quiet=True)

        def enable_logging():

            def linepatch(line):
                if line.startswith('disableLogging'):
                    line = 'disableLogging = False\n'
                return line
                
            filename = op.join(fsleyesdir, '__init__.py')

            print('Enabling logging: {}'.format(filename))

            patch_file(filename, linepatch)

        patch_version()
        patch_gl()
        if self.enable_logging: enable_logging()
        else:                   remove_logging()


class py2app(orig_py2app):
    description = 'Builds a standalone FSLeyes OSX application using py2app'

    def finalize_options(self):

        entrypt     = op.join(basedir, 'fsleyes', '__main__.py')
        assetdir    = op.join(basedir, 'assets')
        iconfile    = op.join(assetdir, 'icons', 'app_icon', 'fsleyes.icns')
        dociconfile = op.join(assetdir, 'icons', 'app_icon', 'fsleyes_doc.icns')
        plist       = op.join(assetdir, 'build', 'Info.plist')
        assets      = build_asset_list()

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

        version    = get_fsleyes_version()
        gitVersion = get_git_version()
        copyright  = get_fsleyes_copyright()

        contentsdir = op.join(basedir, 'dist', 'FSLeyes.app', 'Contents')
        plist       = op.join(contentsdir, 'Info.plist')
        resourcedir = op.join(contentsdir, 'Resources')

        # py2app (and pyinstaller) seem to
        # get the wrong version of libpng,
        # which causes render to segfault
        pildir = pkgutil.get_loader('PIL').filename
        dylib  = op.join(pildir, '.dylibs', 'libpng16.16.dylib')
        if op.exists(dylib):
            shutil.copy(dylib, op.join(contentsdir, 'Frameworks'))

        # copy the application document iconset
        shutil.copy(self.dociconfile, resourcedir)

        # Patch Info.plist
        commands = [
            ['delete', 'PythonInfoDict'],
            ['write',  'CFBundleShortVersionString', version],
            ['write',  'CFBundleVersion',            gitVersion],
            ['write',  'NSHumanReadableCopyright',   copyright],
        ]

        for c in commands:
            sp_call(['defaults'] + [c[0]] + [plist] + c[1:])


class pyinstaller(Command):
    description  = 'Builds a standalone FSLeyes Linux ' \
                   'application using pyinstaller'
    user_options = []

    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):

        builddir = op.join(basedir, 'build')
        distdir  = op.join(basedir, 'dist')
        assetdir = op.join(basedir, 'dist', 'FSLeyes', 'share', 'FSLeyes')
        iconfile = op.join(assetdir, 'icons', 'app_icon', 'fsleyes.ico')
        assets   = build_asset_list()
        entrypt  = op.join(basedir, 'fsleyes', '__main__.py')
        
        hidden = [
            'scipy.special._ufuncs_cxx',
            'scipy.linalg.cython_blas',
            'scipy.linalg.cython_lapack',
            'scipy.integrate',
            'OpenGL.platform.osmesa',
            'OpenGL_accelerate'
        ]

        excludes = [
            'matplotlib.backends.backend_agg',
            'matplotlib.backends.backend_pdf',
            'matplotlib.backends.backend_pgf',
            'matplotlib.backends.backend_ps',
            'matplotlib.backends.backend_svg',
            'matplotlib.backends.backend_template',
            'IPython',
        ]
        
        cmd = [
            'pyinstaller',
            '--name=FSLeyes',
            '--icon={}'.format(iconfile),
            '--windowed',
            '--workpath={}'.format(builddir),
            '--distpath={}'.format(distdir),
            entrypt,
        ]

        env   = dict(os.environ)
        ppath = [
            op.join(pkgutil.get_loader('fsleyes').filename, '..'),
            op.join(pkgutil.get_loader('fsl')    .filename, '..'),
            op.join(pkgutil.get_loader('props')  .filename, '..')]
        
        env['PYTHONPATH'] = op.pathsep.join(ppath) 

        sp_call(cmd, env=env)

        # Move the spec file into the build directory
        shutil.move(op.join(basedir, 'FSLeyes.spec'), builddir)
        
        # Make the executable lowercase
        try:
            os.rename(op.join(distdir, 'FSLeyes', 'FSLeyes'),
                      op.join(distdir, 'FSLeyes', 'fsleyes'))

        # Case insensitive file system?
        except:
            pass

        # Copy assets
        os.makedirs(assetdir)
        for dirname, files in assets:

            dirname = op.join(assetdir, dirname)

            if not op.exists(dirname):
                os.makedirs(dirname)

            for src in files:
                shutil.copy(src, dirname)


def sp_call(command, *args, **kwargs):
    """Prints the given command, then calls ``subprocess.call``. """

    if not kwargs.pop('quiet', False):
        print(' '.join(command))
        
    return sp.call(command, *args, **kwargs)


def sp_check_output(command, *args, **kwargs):
    """Prints the given command, then calls ``subprocess.check_output``. """
    print(' '.join(command))
    return sp.check_output(command, *args, **kwargs)


def checkout(project, rev, todir):
    """Checks out the given project from the FMRIB gitlab repository. """

    project_repos = {
        'fsleyes'      : 'git@git.fmrib.ox.ac.uk:paulmc/fsleyes.git',
        'fslpy'        : 'git@git.fmrib.ox.ac.uk:paulmc/fslpy.git',
        'props'        : 'git@git.fmrib.ox.ac.uk:paulmc/props.git',
        'indexed_gzip' : 'git@github.com:pauldmccarthy/indexed_gzip.git',
    } 

    repo    = project_repos[project]

    if op.exists(todir):
        shutil.rmtree(todir)

    os.mkdir(todir)

    commands = [
        'git init .',
        'git pull {} {}'.format(repo, rev)
    ]

    # indexed_gzip needs to be compiled
    if project == 'indexed_gzip':
        commands.append('python setup.py  build_ext --inplace')

    for cmd in commands:
        if sp_call(cmd.split(), cwd=todir):
            raise RuntimeError('Command failed: "{}"'.format(cmd))


def list_all_files(in_dir):
    """List all files ``in_dir``. """
    
    for dirname, dirs, files in os.walk(in_dir):
        for filename in files:
            yield op.join(dirname, filename) 


def build_asset_list():
    """Build a list of all the FSLeyes non-source-code files that should
    be included in a distribution built by py2app.
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
    
    return resources.items()


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


def get_git_version():
    """Returns a string containing the git hashes of fsleyes, fslpy, and
    props.

    Warning: This will fix the paths to the props/fslpy packages, so make
             sure the PYTHONPATH/sys.path is set before calling this function.
    """
    propsdir   = pkgutil.get_loader('props')  .filename
    fslpydir   = pkgutil.get_loader('fsl')    .filename
    fsleyesdir = pkgutil.get_loader('fsleyes').filename

    cmd = 'git rev-parse HEAD'.split()

    propshash   = sp_check_output(cmd, cwd=propsdir)  .strip()
    fslpyhash   = sp_check_output(cmd, cwd=fslpydir)  .strip()
    fsleyeshash = sp_check_output(cmd, cwd=fsleyesdir).strip()
    hashes      = [fsleyeshash, fslpyhash, propshash]
    
    return '.'.join([h[:7] for h in hashes])


def get_fsleyes_copyright():
    """Returns the FSLeyes copyright text. """
    with open(op.join(basedir, 'COPYRIGHT')) as f:
        return f.read().strip()


def get_fsleyes_deps():
    """Returns two lists containing the FSLeyes dependencies:
        - Packages to be installed via pip
        - Packages to be installed from git repositories
    """

    # The dependency list is stored in requirements.txt
    with open(op.join(basedir, 'requirements.txt'), 'rt') as f:
        install_requires = f.readlines()
        
    dependency_links = [i.strip() for i in install_requires
                        if     i.startswith('git')]
    install_requires = [i.strip() for i in install_requires
                        if not i.startswith('git')]

    return install_requires, dependency_links


def main():

    version   = get_fsleyes_version()
    packages  = find_packages(
        exclude=('userdoc', 'apidoc', 'assets', 'build', 'dist'))

    with open(op.join(basedir, 'README.md'), 'rt') as f:
        readme = f.read()

    deps             = get_fsleyes_deps()
    install_requires = deps[0]
    dependency_links = deps[1]
    
    if platform == 'darwin': setup_requires = ['py2app']
    else:                    setup_requires = ['pyinstaller']

    setup(

        name='fsleyes',
        version=version,
        description='FSLeyes, the FSL image viewer',
        long_description=readme,
        url='https://git.fmrib.ox.ac.uk/paulmc/fsleyes',
        author='Paul McCarthy',
        author_email='pauldmccarthy@gmail.com',
        license='Apache License Version 2.0',

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
            'patch_code'           : patch_code,
            'build_standalone'     : build_standalone,
            'checkout_subprojects' : checkout_subprojects,
            'py2app'               : py2app,
            'pyinstaller'          : pyinstaller,
            'userdoc'              : userdoc,
            'apidoc'               : apidoc,
        },

        setup_requires=setup_requires,
    )


if __name__ == '__main__':
    main()
