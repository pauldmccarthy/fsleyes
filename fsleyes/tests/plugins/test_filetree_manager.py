#!/usr/bin/env python


import os
import shutil
import os.path as op
import itertools as it
import textwrap as tw
from contextlib import contextmanager
from collections import OrderedDict

import pytest

from   fsl.utils.tempdir import tempdir
from   fsl.data.image    import Image
from   fsl.data.gifti    import GiftiMesh

import fsleyes.plugins.controls.filetreepanel.query   as ftquery
import fsleyes.plugins.controls.filetreepanel.manager as ftman

from fsleyes.tests import run_with_fsleyes, run_with_orthopanel, yieldUntil


file_tree = pytest.importorskip('file_tree')


datadir = op.join(op.dirname(__file__), '..', 'testdata')


treespec = tw.dedent("""
subj-{subject}
  ses-{session}
    T1w.nii.gz (T1w)
    T2w.nii.gz (T2w)
    {hemi}.{surf}.gii (surface)
""").strip()

ftypes = ['T1w', 'T2w', 'surface']
subjs  = ['01', '02', '03']
sess   = ['1', '2']
hemis  =  ['L', 'R']
surfs  = ['pial', 'mid', 'white']


@contextmanager
def _query(specs=None, files=None, realdata=False):

    if specs is None:
        specs = {'tree' : treespec}

    root = list(specs.keys())[0]
    volfile  = op.join(datadir, '3d.nii.gz')
    meshfile = op.join(datadir, 'gifti', 'white.surf.gii')

    with tempdir():
        for name, spec in specs.items():
            with open('{}.tree'.format(name), 'wt') as f:
                f.write(spec)

        if files is None:
            files = []
            for subj, ses in it.product(subjs, sess):
                sesdir = op.join('subj-{}'.format(subj), 'ses-{}'.format(ses))
                files.append(op.join(sesdir, 'T1w.nii.gz'))
                files.append(op.join(sesdir, 'T2w.nii.gz'))
                for hemi, surf in it.product(hemis, surfs):
                    fname = '{}.{}.gii'.format(hemi, surf)
                    files.append(op.join(sesdir, fname))

        for file in files:
            dirname = op.split(file)[0]
            os.makedirs(dirname, exist_ok=True)

            if realdata:
                if   file.endswith('.gii'):    src = meshfile
                elif file.endswith('.nii.gz'): src = volfile
                shutil.copy(src, file)
            else:
                with open(file, 'wt') as f:
                    pass

        tree  = file_tree.FileTree.read('{}.tree'.format(root), '.')
        query = ftquery.FileTreeQuery(tree)
        yield query


def test_prepareVaryings():
    with _query() as query:
        assert (ftman.prepareVaryings(query, ['T1w'], {'subject' : '01'}) ==
                {'subject' : ['01']})
        assert (ftman.prepareVaryings(query, ['T1w'], {'subject' : '*'}) ==
                {'subject' : ['01', '02', '03']})
        assert (ftman.prepareVaryings(query, ['T1w', 'T2w'], {'subject' : '*'}) ==
                {'subject' : ['01', '02', '03']})
        assert (ftman.prepareVaryings(query, ['T1w', 'T2w'], {'hemi' : 'L'}) == {})
        assert (ftman.prepareVaryings(query, ['T1w', 'T2w'], {'hemi' : '*'}) == {})
        assert (ftman.prepareVaryings(query,
                                      ['surface', 'T2w'],
                                      {'subject' : '01', 'hemi' : '*'}) ==
                {'subject' : ['01'], 'hemi' : ['L', 'R']})
        assert (ftman.prepareVaryings(query,
                                      ['surface', 'T2w'],
                                      {'subject' : '*', 'hemi' : '*'}) ==
                {'subject' : ['01', '02', '03'], 'hemi' : ['L', 'R']})


def test_prepareFixed():
    with _query() as query:
        assert (ftman.prepareFixed(query, ['T1w'], ['session']) ==
                {'T1w' : {'session' : ['1', '2']}})
        assert (ftman.prepareFixed(query, ['T1w', 'T2w'], ['session']) ==
                {'T1w' : {'session' : ['1', '2']},
                 'T2w' : {'session' : ['1', '2']}})
        assert (ftman.prepareFixed(query, ['surface'], []) ==
                {'surface' : {}})
        assert (ftman.prepareFixed(query, ['surface'], ['hemi']) ==
                {'surface' : {'hemi' : ['L', 'R']}})
        assert (ftman.prepareFixed(query, ['T1w', 'surface'], ['hemi']) ==
                {'T1w' : {},
                 'surface' : {'hemi' : ['L', 'R']}})


def test_genColumns():
    varcols, fixedcols = ftman.genColumns(['T1w'],
                                          {'subject' : ['01']},
                                          {'T1w' : {}})
    assert varcols == []
    assert fixedcols == [('T1w', {})]

    varcols, fixedcols = ftman.genColumns(['T1w'],
                                          {'subject' : ['01', '02', '03']},
                                          {'T1w' : {}})
    assert varcols == ['subject']
    assert fixedcols == [('T1w', {})]

    varcols, fixedcols = ftman.genColumns(['T1w', 'T2w'],
                                          {'subject' : ['01', '02', '03']},
                                          OrderedDict([('T1w', {'session' : ['1', '2']}),
                                                       ('T2w', {})]))
    assert varcols == ['subject']
    assert fixedcols == [('T1w', {'session' : '1'}),
                         ('T1w', {'session' : '2'}),
                         ('T2w', {})]

    varcols, fixedcols = ftman.genColumns(['T1w', 'surface'],
                                          OrderedDict([('subject', ['01', '02', '03']),
                                                       ('session', ['1', '2'])]),
                                          OrderedDict([('T1w',     {}),
                                                       ('surface', OrderedDict([('hemi', ['L', 'R']),
                                                                                ('surf', ['pial', 'mid', 'white'])]))]))
    assert sorted(varcols) == ['session', 'subject']
    assert fixedcols == [('T1w',     {}),
                         ('surface', {'hemi' : 'L', 'surf' : 'pial'}),
                         ('surface', {'hemi' : 'L', 'surf' : 'mid'}),
                         ('surface', {'hemi' : 'L', 'surf' : 'white'}),
                         ('surface', {'hemi' : 'R', 'surf' : 'pial'}),
                         ('surface', {'hemi' : 'R', 'surf' : 'mid'}),
                         ('surface', {'hemi' : 'R', 'surf' : 'white'})]

    varcols, fixedcols = ftman.genColumns(['T1w', 'surface'],
                                          OrderedDict([('subject', ['01', '02', '03']),
                                                       ('session', ['1', '2']),
                                                       ('surf'   , ['pial', 'mid', 'white'])]),
                                          OrderedDict([('T1w',     {}),
                                                       ('surface', {'hemi' : ['L', 'R']})]))
    assert sorted(varcols) == ['session', 'subject', 'surf']
    assert fixedcols == [('T1w',     {}),
                         ('surface', {'hemi' : 'L'}),
                         ('surface', {'hemi' : 'R'})]



def test_genFileGroups():
    # varyings, fixed, expgroups
    tests = [
        (OrderedDict([('subject', ['01', '02', '03']),
                      ('session', ['1', '2'])]),
         [('T1w', {}),
          ('T2w', {})],
         [ftman.FileGroup({'subject' : '01', 'session' : '1'}, [{}, {}], ['T1w', 'T2w'], ['subj-01/ses-1/T1w.nii.gz', 'subj-01/ses-1/T2w.nii.gz']),
          ftman.FileGroup({'subject' : '01', 'session' : '2'}, [{}, {}], ['T1w', 'T2w'], ['subj-01/ses-2/T1w.nii.gz', 'subj-01/ses-2/T2w.nii.gz']),
          ftman.FileGroup({'subject' : '02', 'session' : '1'}, [{}, {}], ['T1w', 'T2w'], ['subj-02/ses-1/T1w.nii.gz', 'subj-02/ses-1/T2w.nii.gz']),
          ftman.FileGroup({'subject' : '02', 'session' : '2'}, [{}, {}], ['T1w', 'T2w'], ['subj-02/ses-2/T1w.nii.gz', 'subj-02/ses-2/T2w.nii.gz']),
          ftman.FileGroup({'subject' : '03', 'session' : '1'}, [{}, {}], ['T1w', 'T2w'], ['subj-03/ses-1/T1w.nii.gz', 'subj-03/ses-1/T2w.nii.gz']),
          ftman.FileGroup({'subject' : '03', 'session' : '2'}, [{}, {}], ['T1w', 'T2w'], ['subj-03/ses-2/T1w.nii.gz', 'subj-03/ses-2/T2w.nii.gz'])]),
        ({'subject' : ['01', '02', '03']},
         [('T1w', {'session' : '1'}),
          ('T1w', {'session' : '2'})],
         [ftman.FileGroup({'subject' : '01'}, [{'session' : '1'}, {'session' : '2'}], ['T1w', 'T1w'], ['subj-01/ses-1/T1w.nii.gz', 'subj-01/ses-2/T1w.nii.gz']),
          ftman.FileGroup({'subject' : '02'}, [{'session' : '1'}, {'session' : '2'}], ['T1w', 'T1w'], ['subj-02/ses-1/T1w.nii.gz', 'subj-02/ses-2/T1w.nii.gz']),
          ftman.FileGroup({'subject' : '03'}, [{'session' : '1'}, {'session' : '2'}], ['T1w', 'T1w'], ['subj-03/ses-1/T1w.nii.gz', 'subj-03/ses-2/T1w.nii.gz'])]),
        (OrderedDict([('subject', ['01', '02', '03']),
                      ('session', ['1']),
                      ('surf',    ['pial', 'mid', 'white'])]),
         [('T1w',     {}),
          ('surface', {'hemi' : 'L'}),
          ('surface', {'hemi' : 'R'})],
         [ftman.FileGroup({'subject' : '01', 'session' : '1', 'surf' : 'pial'},  [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-01/ses-1/T1w.nii.gz', 'subj-01/ses-1/L.pial.gii',  'subj-01/ses-1/R.pial.gii']),
          ftman.FileGroup({'subject' : '01', 'session' : '1', 'surf' : 'mid'},   [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-01/ses-1/T1w.nii.gz', 'subj-01/ses-1/L.mid.gii',   'subj-01/ses-1/R.mid.gii']),
          ftman.FileGroup({'subject' : '01', 'session' : '1', 'surf' : 'white'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-01/ses-1/T1w.nii.gz', 'subj-01/ses-1/L.white.gii', 'subj-01/ses-1/R.white.gii']),
          ftman.FileGroup({'subject' : '02', 'session' : '1', 'surf' : 'pial'},  [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-02/ses-1/T1w.nii.gz', 'subj-02/ses-1/L.pial.gii',  'subj-02/ses-1/R.pial.gii']),
          ftman.FileGroup({'subject' : '02', 'session' : '1', 'surf' : 'mid'},   [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-02/ses-1/T1w.nii.gz', 'subj-02/ses-1/L.mid.gii',   'subj-02/ses-1/R.mid.gii']),
          ftman.FileGroup({'subject' : '02', 'session' : '1', 'surf' : 'white'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-02/ses-1/T1w.nii.gz', 'subj-02/ses-1/L.white.gii', 'subj-02/ses-1/R.white.gii']),
          ftman.FileGroup({'subject' : '03', 'session' : '1', 'surf' : 'pial'},  [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-03/ses-1/T1w.nii.gz', 'subj-03/ses-1/L.pial.gii',  'subj-03/ses-1/R.pial.gii']),
          ftman.FileGroup({'subject' : '03', 'session' : '1', 'surf' : 'mid'},   [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-03/ses-1/T1w.nii.gz', 'subj-03/ses-1/L.mid.gii',   'subj-03/ses-1/R.mid.gii']),
          ftman.FileGroup({'subject' : '03', 'session' : '1', 'surf' : 'white'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-03/ses-1/T1w.nii.gz', 'subj-03/ses-1/L.white.gii', 'subj-03/ses-1/R.white.gii'])]),
    ]

    with _query() as query:
        for varyings, fixed, expgroups in tests:
            gotgroups = ftman.genFileGroups(query, varyings, fixed)
            assert expgroups == gotgroups


def test_filterFileGroups():

    base = tw.dedent("""
    subj-{subject}
      T1w.nii.gz (T1w)
      surf
        ->sub (surf)
    """).strip()

    sub = tw.dedent("""
    {hemi}.{boundary}.gii (surface)
    """).strip()

    files = [
        op.join('subj-01', 'T1w.nii.gz'),
        op.join('subj-01', 'surf', 'L.white.gii'),
        op.join('subj-01', 'surf', 'R.white.gii'),
        op.join('subj-01', 'surf', 'L.pial.gii'),
        op.join('subj-01', 'surf', 'R.pial.gii'),
        #op.join('subj-02', 'T1w.nii.gz'),
        op.join('subj-02', 'surf', 'L.white.gii'),
        op.join('subj-02', 'surf', 'R.white.gii'),
        op.join('subj-02', 'surf', 'L.pial.gii'),
        op.join('subj-02', 'surf', 'R.pial.gii'),
        op.join('subj-03', 'T1w.nii.gz'),
        op.join('subj-03', 'surf', 'L.white.gii'),
        op.join('subj-03', 'surf', 'R.white.gii'),
        #op.join('subj-03', 'surf', 'L.pial.gii'),
        #op.join('subj-03', 'surf', 'R.pial.gii'),
    ]

    # (invars, infixed, expgroups, expcols)
    tests = [

        # subj02 row should be filtered
        ({'subject' : ['01', '02', '03']},
         [('T1w', {})],
         [ftman.FileGroup({'subject' : '01'}, [{}], ['T1w'], ['subj-01/T1w.nii.gz']),
          # ftman.FileGroup({'subject' : '02'}, [{}], ['T1w'], ['subj-02/T1w.nii.gz']),
          ftman.FileGroup({'subject' : '03'}, [{}], ['T1w'], ['subj-03/T1w.nii.gz'])],
         None),

        # sub3/pial should be filtered
        ({'subject'  : ['01', '02', '03'],
          'boundary' : ['pial', 'white']},
         [('T1w',          {}),
          ('surf/surface', {'hemi' : 'L'}),
          ('surf/surface', {'hemi' : 'R'})],
         [ftman.FileGroup({'subject' : '01', 'boundary' : 'pial'},  [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surf/surface', 'surf/surface'], ['subj-01/T1w.nii.gz', 'subj-01/surf/L.pial.gii',  'subj-01/surf/R.pial.gii']),
          ftman.FileGroup({'subject' : '01', 'boundary' : 'white'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surf/surface', 'surf/surface'], ['subj-01/T1w.nii.gz', 'subj-01/surf/L.white.gii', 'subj-01/surf/R.white.gii']),
          ftman.FileGroup({'subject' : '02', 'boundary' : 'pial'},  [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surf/surface', 'surf/surface'], [None,                 'subj-02/surf/L.pial.gii',  'subj-02/surf/R.pial.gii']),
          ftman.FileGroup({'subject' : '02', 'boundary' : 'white'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surf/surface', 'surf/surface'], [None,                 'subj-02/surf/L.white.gii', 'subj-02/surf/R.white.gii']),
          # ftman.FileGroup({'subject' : '03', 'boundary' : 'pial'},  [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surf/surface', 'surf/surface'], ['subj-03/T1w.nii.gz', None,                        None]),
          ftman.FileGroup({'subject' : '03', 'boundary' : 'white'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surf/surface', 'surf/surface'], ['subj-03/T1w.nii.gz', 'subj-03/surf/L.white.gii', 'subj-03/surf/R.white.gii'])],
         None),


        # pial col should be filtered
        ({'subject' : ['03'],
          'hemi'    : ['L', 'R']},
         [('T1w',          {}),
          ('surf/surface', {'boundary' : 'white'}),
          ('surf/surface', {'boundary' : 'pial'})],
         [ftman.FileGroup({'subject' : '03', 'hemi' : 'L'}, [{}, {'boundary' : 'white'}], ['T1w', 'surf/surface'], ['subj-03/T1w.nii.gz', 'subj-03/surf/L.white.gii']),
          ftman.FileGroup({'subject' : '03', 'hemi' : 'R'}, [{}, {'boundary' : 'white'}], ['T1w', 'surf/surface'], ['subj-03/T1w.nii.gz', 'subj-03/surf/R.white.gii'])],
         [('T1w',          {}),
          ('surf/surface', {'boundary' : 'white'})],
        ),
    ]
    with _query(OrderedDict([('base', base), ('sub', sub)]), files) as query:

        for invars, infixed, expgroups, expcols in tests:
            if expcols is None:
                expcols = infixed

            ingroups = ftman.genFileGroups(query, invars, infixed)
            gotgroups, gotcols = ftman.filterFileGroups(ingroups, infixed)

            assert gotgroups == expgroups
            assert gotcols   == expcols


def test_FileTreeManager():
    run_with_fsleyes(_test_FileTreeManager)

def _test_FileTreeManager(frame, overlayList, displayCtx):

    with _query() as query:
        mgr = ftman.FileTreeManager(overlayList, displayCtx, query)

        mgr.update(['T1w'], {'subject' : '01', 'session' : '*'}, [])
        assert mgr.ftypes     == ['T1w']
        assert mgr.varyings   == {'subject' : ['01'], 'session' : ['1', '2']}
        assert mgr.fixed      == {'T1w' : {}}
        assert mgr.varcols    == ['session']
        assert mgr.fixedcols  == [('T1w', {})]
        assert mgr.filegroups == [ftman.FileGroup({'subject' : '01', 'session' : '1'}, [{}], ['T1w'], ['subj-01/ses-1/T1w.nii.gz']),
                                  ftman.FileGroup({'subject' : '01', 'session' : '2'}, [{}], ['T1w'], ['subj-01/ses-2/T1w.nii.gz'])]

        mgr.update(['T1w', 'surface'], {'subject' : '*', 'session' : '*', 'surf' : 'pial'}, ['hemi'])
        assert mgr.ftypes     == ['T1w', 'surface']
        assert mgr.varyings   == {'subject' : ['01', '02', '03'], 'session' : ['1', '2'], 'surf' : ['pial']}
        assert mgr.fixed      == {'T1w' : {}, 'surface' : {'hemi' : ['L', 'R']}}
        assert mgr.varcols    == ['session', 'subject']
        assert mgr.fixedcols  == [('T1w', {}), ('surface', {'hemi' : 'L'}), ('surface', {'hemi' : 'R'})]
        assert mgr.filegroups == [
            ftman.FileGroup({'subject' : '01', 'session' : '1', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-01/ses-1/T1w.nii.gz', 'subj-01/ses-1/L.pial.gii', 'subj-01/ses-1/R.pial.gii']),
            ftman.FileGroup({'subject' : '02', 'session' : '1', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-02/ses-1/T1w.nii.gz', 'subj-02/ses-1/L.pial.gii', 'subj-02/ses-1/R.pial.gii']),
            ftman.FileGroup({'subject' : '03', 'session' : '1', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-03/ses-1/T1w.nii.gz', 'subj-03/ses-1/L.pial.gii', 'subj-03/ses-1/R.pial.gii']),
            ftman.FileGroup({'subject' : '01', 'session' : '2', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-01/ses-2/T1w.nii.gz', 'subj-01/ses-2/L.pial.gii', 'subj-01/ses-2/R.pial.gii']),
            ftman.FileGroup({'subject' : '02', 'session' : '2', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-02/ses-2/T1w.nii.gz', 'subj-02/ses-2/L.pial.gii', 'subj-02/ses-2/R.pial.gii']),
            ftman.FileGroup({'subject' : '03', 'session' : '2', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-03/ses-2/T1w.nii.gz', 'subj-03/ses-2/L.pial.gii', 'subj-03/ses-2/R.pial.gii']),
        ]

        mgr.reorder(['subject', 'session'])
        assert mgr.varcols    == ['subject', 'session']
        assert mgr.filegroups == [
            ftman.FileGroup({'subject' : '01', 'session' : '1', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-01/ses-1/T1w.nii.gz', 'subj-01/ses-1/L.pial.gii', 'subj-01/ses-1/R.pial.gii']),
            ftman.FileGroup({'subject' : '01', 'session' : '2', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-01/ses-2/T1w.nii.gz', 'subj-01/ses-2/L.pial.gii', 'subj-01/ses-2/R.pial.gii']),
            ftman.FileGroup({'subject' : '02', 'session' : '1', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-02/ses-1/T1w.nii.gz', 'subj-02/ses-1/L.pial.gii', 'subj-02/ses-1/R.pial.gii']),
            ftman.FileGroup({'subject' : '02', 'session' : '2', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-02/ses-2/T1w.nii.gz', 'subj-02/ses-2/L.pial.gii', 'subj-02/ses-2/R.pial.gii']),
            ftman.FileGroup({'subject' : '03', 'session' : '1', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-03/ses-1/T1w.nii.gz', 'subj-03/ses-1/L.pial.gii', 'subj-03/ses-1/R.pial.gii']),
            ftman.FileGroup({'subject' : '03', 'session' : '2', 'surf' : 'pial'}, [{}, {'hemi' : 'L'}, {'hemi' : 'R'}], ['T1w', 'surface', 'surface'], ['subj-03/ses-2/T1w.nii.gz', 'subj-03/ses-2/L.pial.gii', 'subj-03/ses-2/R.pial.gii']),
        ]

        mgr.destroy()
        assert mgr.query is None


def test_getProperties():
    run_with_fsleyes(_test_getProperties)

def _test_getProperties(frame, overlayList, displayCtx):
    vol1 = Image(op.join(datadir, '3d.nii.gz'), name='vol1')
    vol2 = Image(op.join(datadir, '3d.nii.gz'), name='vol2')
    mesh = GiftiMesh(op.join(datadir, 'gifti', 'white.surf.gii'))

    overlayList.extend([vol1, vol2, mesh])

    displayCtx.getDisplay(vol1).alpha     = 97
    displayCtx.getOpts(   vol1).clipImage = vol2

    vprops = ftman.getProperties(vol1, displayCtx)
    assert vprops['alpha']         == 97
    assert vprops['interpolation'] == 'none'
    assert 'transform' not in vprops
    ci = vprops['clipImage']
    assert isinstance(ci, ftman.ToReplace) and ci.value == 'vol2'

    vprops = ftman.getProperties(vol2, displayCtx)
    assert vprops['alpha']         == 100
    assert vprops['interpolation'] == 'none'
    assert 'transform' not in vprops
    assert 'clipImage' not in vprops

    displayCtx.getDisplay(mesh).alpha = 43

    mprops = ftman.getProperties(mesh, displayCtx)
    assert mprops['alpha'] == 43
    assert 'refImage' not in mprops

    displayCtx.getOpts(mesh).refImage = vol1
    mprops = ftman.getProperties(mesh, displayCtx)
    assert mprops['alpha'] == 43
    ri = mprops['refImage']
    assert isinstance(ri, ftman.ToReplace) and ri.value == 'vol1'


def test_OverlayManager():
    run_with_orthopanel(_test_OverlayManager)

def _test_OverlayManager(panel, overlayList, displayCtx):

    volfile  = op.join(datadir, '3d.nii.gz')
    meshfile = op.join(datadir, 'gifti', 'white.surf.gii')

    with _query(realdata=True) as query:
        mgr = ftman.FileTreeManager(overlayList, displayCtx, query)

        called = [False]
        def callback():
            called[0] = True
        def beenCalled():
            return called[0]

        mgr.update(['T1w', 'T2w'], {'subject' : '*', 'session' : '*'}, [])

        mgr.show(mgr.filegroups[0], callback)

        yieldUntil(beenCalled)

        assert len(overlayList) == 2
        if 'T1' in overlayList[0].name: t1, t2 = overlayList
        else:                           t2, t1 = overlayList
        overlayList[:] = [t1, t2]

        assert op.abspath(t1.dataSource) == op.abspath('subj-01/ses-1/T1w.nii.gz')
        assert op.abspath(t2.dataSource) == op.abspath('subj-01/ses-1/T2w.nii.gz')

        displayCtx.getOpts(   t1).cmap       = 'red-yellow'
        displayCtx.getDisplay(t2).brightness = 75
        displayCtx.getOpts(   t1).clipImage  = t2

        called[0] = False
        mgr.show(mgr.filegroups[1], callback)

        yieldUntil(beenCalled)

        assert len(overlayList) == 2
        t1, t2 = overlayList

        # subject should default to fastest-changing
        assert op.abspath(t1.dataSource) == op.abspath('subj-02/ses-1/T1w.nii.gz')
        assert op.abspath(t2.dataSource) == op.abspath('subj-02/ses-1/T2w.nii.gz')

        assert displayCtx.getOpts(   t1).cmap.name  == 'red-yellow'
        assert displayCtx.getDisplay(t2).brightness == 75
        assert displayCtx.getOpts(   t1).clipImage  is t2

        called[0] = False
        mgr.update(['T1w', 'surface'], {'subject' : '*', 'session' : '1', 'surf' : 'white'}, ['hemi'])
        mgr.show(mgr.filegroups[0], callback)
        yieldUntil(beenCalled)

        assert len(overlayList) == 3
        if   'T1'   in overlayList[0].name: t1, sl, sr = overlayList
        elif 'T1'   in overlayList[1].name: sl, t1, sr = overlayList
        elif 'T1'   in overlayList[2].name: sl, sr, t1 = overlayList
        if 'hemi=L' in sr.name:             sl, sr     = sr, sl
        overlayList[:] = [t1, sl, sr]

        assert op.abspath(t1.dataSource) == op.abspath('subj-01/ses-1/T1w.nii.gz')
        assert op.abspath(sl.dataSource) == op.abspath('subj-01/ses-1/L.white.gii')
        assert op.abspath(sr.dataSource) == op.abspath('subj-01/ses-1/R.white.gii')

        displayCtx.getOpts(t1).cmap     = 'blue-lightblue'
        displayCtx.getOpts(sl).refImage = t1
        displayCtx.getOpts(sl).outline  = True
        displayCtx.getOpts(sr).colour   = (0.5,0.6,0.7)

        called[0] = False
        mgr.show(mgr.filegroups[1], callback)
        yieldUntil(beenCalled)

        t1, sl, sr = overlayList

        assert op.abspath(t1.dataSource) == op.abspath('subj-02/ses-1/T1w.nii.gz')
        assert op.abspath(sl.dataSource) == op.abspath('subj-02/ses-1/L.white.gii')
        assert op.abspath(sr.dataSource) == op.abspath('subj-02/ses-1/R.white.gii')

        assert displayCtx.getOpts(t1).cmap.name == 'blue-lightblue'
        assert displayCtx.getOpts(sl).refImage  is t1
        assert displayCtx.getOpts(sl).outline   is True
        assert displayCtx.getOpts(sr).colour    == (0.5, 0.6, 0.7, 1.0)
