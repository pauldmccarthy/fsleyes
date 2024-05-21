#!/usr/bin/env python


import                   importlib
import importlib.util as imputil
import                   os
import                   random
import                   sys
import                   string
import textwrap       as tw
from   unittest   import mock

from   fsl.utils.tempdir    import tempdir
import fsleyes.utils            as utils
import fsleyes.utils.lazyimport as lazyimport

from fsleyes.tests import touch


def test_validMapKey():
    for i in range(100):
        instr = random.choice(string.ascii_letters) + \
            ''.join([random.choice(string.printable) for i in range(50)])
        key   = utils.makeValidMapKey(instr)
        assert utils.isValidMapKey(key)


def test_lazyimport():

    testpkg_name = ''.join(random.choices(string.ascii_letters, k=10))
    testpkg_file = f'{testpkg_name}/__init__.py'
    moda_name    = f'{testpkg_name}.modulea'
    modb_name    = f'{testpkg_name}.moduleb'
    moda_file    = f'{testpkg_name}/modulea.py'
    modb_file    = f'{testpkg_name}/moduleb.py'

    moda_contents = tw.dedent("""
    from fsleyes.utils.lazyimport import lazyimport
    sys = lazyimport('sys')
    """).strip()

    modb_contents = tw.dedent(f"""
    from fsleyes.utils.lazyimport import lazyimport
    sys = lazyimport('sys', '{testpkg_name}.moduleb.sys')
    """).strip()

    with tempdir():

        os.mkdir(testpkg_name)
        touch(testpkg_file)

        with open(moda_file, 'wt') as f: f.write(moda_contents)
        with open(modb_file, 'wt') as f: f.write(modb_contents)

        testpkg_spec = imputil.spec_from_file_location(testpkg_name, testpkg_file)
        moda_spec    = imputil.spec_from_file_location(moda_name, moda_file)
        modb_spec    = imputil.spec_from_file_location(modb_name, modb_file)
        testpkg      = imputil.module_from_spec(testpkg_spec)
        moda         = imputil.module_from_spec(moda_spec)
        modb         = imputil.module_from_spec(modb_spec)

        testpkg_spec.loader.exec_module(testpkg)
        moda_spec   .loader.exec_module(moda)
        modb_spec   .loader.exec_module(modb)

        sys.modules[testpkg_name] = testpkg
        sys.modules[moda_name]    = moda
        sys.modules[modb_name]    = modb

        try:
            assert isinstance(moda.sys, lazyimport.LazyImporter)
            assert isinstance(modb.sys, lazyimport.LazyImporter)

            assert not moda.sys.hasBeenImported
            assert not modb.sys.hasBeenImported

            moda.sys.version
            modb.sys.version

            assert isinstance(moda.sys, lazyimport.LazyImporter)
            assert moda.sys.hasBeenImported

            # reference should have been
            # replaced with the imported module
            assert modb.sys is sys

        finally:
            sys.modules.pop(testpkg_name)
            sys.modules.pop(moda_name)
            sys.modules.pop(modb_name)
