#!/usr/bin/env python
#
# setup.py - setuptools configuration for installing FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import            os
import os.path as op

from setuptools               import setup
from setuptools               import find_packages
from setuptools.command.sdist import sdist


class fsl_sdist(sdist):
    """Custom sdist command which inserts the LICENSE text at the
    beginning of every source file.
    """

    
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
        licence = ['# {}'.format(l) for l in licence]

        with open(filename, 'rt') as f:
            lines = f.read().split('\n')

        # Remove any existing hashbang line
        if len(lines) > 0 and lines[0].startswith('#!'):
            lines = lines[1:]

        # Insert the fsl hashbang and the licence
        lines = ['#!/usr/bin/env fslpython'] + ['#'] + licence + lines
        lines = ['{}\n'.format(l) for l in lines]

        with open(filename, 'wt') as f:
            f.writelines(lines)
            
            
    def __patch_prog_file(self, filename, licence):

        licence = licence.split('\n')
        licence = ['# {}'.format(l) for l in licence]

        with open(filename, 'rt') as f:
            lines = f.read().split('\n')

        # ARB vertex/fragment programs 
        # have a hashbang-like thing as 
        # their first line.
        if len(lines) > 0 and lines[0].startswith('!!'):
            lines = [lines[0]] + licence + lines[1:]
        else:
            lines = licence + lines
            
        lines = ['{}\n'.format(l) for l in lines]

        with open(filename, 'wt') as f:
            f.writelines(lines)


    def __patch_glsl_file(self, filename, licence):

        licence = licence.split('\n')
        licence = ['/*'] + [' * {}'.format(l) for l in licence] + [' */']

        with open(filename, 'rt') as f:
            lines = f.read().split('\n')

        lines = licence + lines
        lines = ['{}\n'.format(l) for l in lines]

        with open(filename, 'wt') as f:
            f.writelines(lines)        
        

# The directory in which this setup.py file is contained.
basedir = op.dirname(__file__)


# Figure out the current fsleyes version, as defined in fsleyes/version.py. We
# don't want to import the fsleyes package,  as this may cause build problems.
# So we manually parse the contents of fsl/version.py to extract the
# version number.
version = {}
with open(op.join(basedir, "fsleyes", "version.py")) as f:
    for line in f:
        if line.startswith('__version__'):
            exec(line, version)
            break


install_requires = open(op.join(basedir, 'requirements.txt'), 'rt').readlines()
dependency_links = [i for i in install_requires if     i.startswith('git')]
install_requires = [i for i in install_requires if not i.startswith('git')]

setup(

    name='fsleyes',

    version=version.get('__version__'),

    description='FSLeyes, the FSL image viewer',

    url='https://git.fmrib.ox.ac.uk/paulmc/fsleyes',

    author='Paul McCarthy',

    author_email='pauldmccarthy@gmail.com',

    license='FMRIB',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Free for non-commercial use',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules'],

    packages=find_packages(exclude=('doc')),

    install_requires=install_requires,
    dependency_links=dependency_links,

    cmdclass={'fsl_sdist' : fsl_sdist},

    entry_points={
        'console_scripts' : [
            'render = fsleyes.render:main'
        ],
        'gui_scripts' : [
            'FSLeyes = fsleyes.main:main'
        ]
    }
)
