#!/usr/bin/env python
#
# test_query.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import glob
import shutil
import os.path as op
import contextlib
import textwrap as tw
import itertools as it

import pytest

import fsleyes.plugins.controls.filetreepanel.query as ftquery

from fsleyes.tests import testdir as _testdir


# all test are skipped if file_tree is not installed
file_tree = pytest.importorskip('file_tree')
xr        = pytest.importorskip('xarray')


_test_tree = """
subj-{participant}
  [ses-{session}]
    T1w.nii.gz (T1w)
    T2w.nii.gz (T2w)
    {hemi}.{surf}.gii (surface)
scalar_file.txt (scalar)
""".strip()

_subjs = ['01', '02', '03']
_sess  = ['1', '2']
_hemis = ['L', 'R']
_surfs = ['midthickness', 'pial', 'white']


@contextlib.contextmanager
def _test_data():

    files = ['scalar_file.txt']

    for subj, ses in it.product(_subjs, _sess):
        sesdir = op.join('subj-{}'.format(subj), 'ses-{}'.format(ses))
        files.append(op.join(sesdir, 'T1w.nii.gz'))
        files.append(op.join(sesdir, 'T2w.nii.gz'))

        for hemi, surf in it.product(_hemis, _surfs):
            files.append(op.join(sesdir, '{}.{}.gii'.format(hemi, surf)))

    with _testdir(files):
        with open('_test_tree.tree', 'wt') as f:
            f.write(_test_tree)
        yield


def _expected_matches(template, tree, **kwargs):

    matches = []
    subjs   = kwargs.get('participant', _subjs)
    sess    = kwargs.get('session',     _sess)
    surfs   = kwargs.get('surf',        _surfs)
    hemis   = kwargs.get('hemi',        _hemis)

    if template == 'scalar':
        matches.append(ftquery.Match('scalar_file.txt',
                                     template,
                                     {}))

    for subj, ses in it.product(subjs, sess):

        sesdir = op.join('subj-{}'.format(subj), 'ses-{}'.format(ses))

        if template in ('T1w', 'T2w'):
            f = op.join(sesdir, '{}.nii.gz'.format(template))
            matches.append(ftquery.Match(f,
                                         template,
                                         {'participant' : subj,
                                          'session'     : ses}))

        elif template == 'surface':
            for hemi, surf in it.product(hemis, surfs):
                f = op.join(sesdir, '{}.{}.gii'.format(hemi, surf))
                matches.append(ftquery.Match(f,
                                             template,
                                             {'participant' : subj,
                                              'session'     : ses,
                                              'hemi'        : hemi,
                                              'surf'        : surf}))

    return matches


def _run_and_check_query(query, template, **vars):

    gotmatches = query.query(      template, **vars)
    expmatches = _expected_matches(
        template, query.tree, **{k : [v] for k, v in vars.items()})

    assert len(gotmatches) == len(expmatches)
    for got, exp in zip(sorted(gotmatches), sorted(expmatches)):
        assert got == exp


def test_query_properties():
    with _test_data():

        tree  = file_tree.FileTree.read('_test_tree.tree', '.')
        query = ftquery.FileTreeQuery(tree)

        assert sorted(query.axes('scalar'))  == []
        assert sorted(query.axes('T1w'))     == ['participant', 'session']
        assert sorted(query.axes('T2w'))     == ['participant', 'session']
        assert sorted(query.axes('surface')) == ['hemi',
                                                 'participant',
                                                 'session',
                                                 'surf']
        assert sorted(query.templates)       == ['T1w', 'T2w', 'scalar', 'surface']

        assert query.variables('scalar') == {}
        assert query.variables('T1w') == {
            'participant' : ['01', '02', '03'],
            'session'     : ['1', '2']}
        assert query.variables('T2w') == {
            'participant' : ['01', '02', '03'],
            'session'     : ['1', '2']}
        assert query.variables('surface') == {
            'participant' : ['01', '02', '03'],
            'session'     : ['1', '2'],
            'surf'        : ['midthickness', 'pial', 'white'],
            'hemi'        : ['L', 'R']}
        assert query.variables() == {
            'participant' : ['01', '02', '03'],
            'session'     : ['1', '2'],
            'surf'        : ['midthickness', 'pial', 'white'],
            'hemi'        : ['L', 'R']}


def test_query():
    with _test_data():
        tree  = file_tree.FileTree.read('_test_tree.tree', '.')
        query = ftquery.FileTreeQuery(tree)

    _run_and_check_query(query, 'scalar')
    _run_and_check_query(query, 'T1w')
    _run_and_check_query(query, 'T1w', participant='01')
    _run_and_check_query(query, 'T1w', session='2')
    _run_and_check_query(query, 'T1w', participant='02', session='1')
    _run_and_check_query(query, 'T2w')
    _run_and_check_query(query, 'T2w', participant='01')
    _run_and_check_query(query, 'T2w', session='2')
    _run_and_check_query(query, 'T2w', participant='02', session='1')
    _run_and_check_query(query, 'surface')
    _run_and_check_query(query, 'surface', hemi='L')
    _run_and_check_query(query, 'surface', surf='midthickness')
    _run_and_check_query(query, 'surface', hemi='R', surf='pial')
    _run_and_check_query(query, 'surface', participant='03', surf='pial')
    _run_and_check_query(query, 'surface', participant='03', sssion='2')


def test_query_optional_var_folder():
    with _test_data():

        # make subj-01 have no session sub-directories
        for f in glob.glob(op.join('subj-01', 'ses-1', '*')):
            shutil.move(f, 'subj-01')
        shutil.rmtree(op.join('subj-01', 'ses-1'))
        shutil.rmtree(op.join('subj-01', 'ses-2'))

        tree  = file_tree.FileTree.read('_test_tree.tree', '.')
        query = ftquery.FileTreeQuery(tree)

        # None gets converted to a string,
        # then sorted with the rest of the
        # values. So in this case it will
        # come last.
        assert query.variables()['session'] == ['1', '2', None]

        m = query.query('T1w', participant='01')
        assert len(m) == 1
        assert m[0].filename == op.join('subj-01', 'T1w.nii.gz')


def test_query_optional_var_filename():

    treefile = tw.dedent("""
    sub-{subject}
        img[-{modality}].nii.gz (image)
    """).strip()

    files = [
        op.join('sub-01', 'img.nii.gz'),
        op.join('sub-02', 'img-t1.nii.gz'),
        op.join('sub-02', 'img-t2.nii.gz'),
        op.join('sub-03', 'img-t1.nii.gz'),
        op.join('sub-04', 'img.nii.gz')]

    with _testdir(files):
        with open('_test_tree.tree', 'wt') as f:
            f.write(treefile)

        tree  = file_tree.FileTree.read('_test_tree.tree', '.')
        query = ftquery.FileTreeQuery(tree)

        qvars = query.variables()

        assert sorted(qvars.keys()) == ['modality', 'subject']
        assert qvars['subject']  == ['01', '02', '03', '04']
        assert qvars['modality'] == [None, 't1', 't2']

        got = query.query('image', modality=None)
        assert [m.filename for m in sorted(got)] == [
            op.join('sub-01', 'img.nii.gz'),
            op.join('sub-04', 'img.nii.gz')]

        got = query.query('image', modality='t1')
        assert [m.filename for m in sorted(got)] == [
            op.join('sub-02', 'img-t1.nii.gz'),
            op.join('sub-03', 'img-t1.nii.gz')]

        got = query.query('image', modality='t2')
        assert len(got) == 1
        assert got[0].filename == op.join('sub-02', 'img-t2.nii.gz')


def test_query_missing_files():
    with _test_data():

        os.remove(op.join('subj-01', 'ses-1', 'T1w.nii.gz'))
        os.remove(op.join('subj-02', 'ses-2', 'T2w.nii.gz'))
        os.remove(op.join('subj-03', 'ses-1', 'L.white.gii'))
        os.remove(op.join('subj-03', 'ses-1', 'L.midthickness.gii'))
        os.remove(op.join('subj-03', 'ses-1', 'L.pial.gii'))

        tree  = file_tree.FileTree.read('_test_tree.tree', '.')
        query = ftquery.FileTreeQuery(tree)

        got = query.query('T1w', session='1')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-02', 'ses-1', 'T1w.nii.gz'),
            op.join('subj-03', 'ses-1', 'T1w.nii.gz')]

        got = query.query('T2w', session='2')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'ses-2', 'T2w.nii.gz'),
            op.join('subj-03', 'ses-2', 'T2w.nii.gz')]

        got = query.query('surface', session='1', hemi='L')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'ses-1', 'L.midthickness.gii'),
            op.join('subj-01', 'ses-1', 'L.pial.gii'),
            op.join('subj-01', 'ses-1', 'L.white.gii'),
            op.join('subj-02', 'ses-1', 'L.midthickness.gii'),
            op.join('subj-02', 'ses-1', 'L.pial.gii'),
            op.join('subj-02', 'ses-1', 'L.white.gii')]


def test_query_subtree():
    tree1 = tw.dedent("""
    subj-{participant}
        T1w.nii.gz (T1w)
        surf
            ->surface (surfdir)
    """)
    tree2 = tw.dedent("""
    {hemi}.{surf}.gii (surface)
    """)

    files = [
        op.join('subj-01', 'T1w.nii.gz'),
        op.join('subj-01', 'surf', 'L.pial.gii'),
        op.join('subj-01', 'surf', 'R.pial.gii'),
        op.join('subj-01', 'surf', 'L.white.gii'),
        op.join('subj-01', 'surf', 'R.white.gii'),
        op.join('subj-02', 'T1w.nii.gz'),
        op.join('subj-02', 'surf', 'L.pial.gii'),
        op.join('subj-02', 'surf', 'R.pial.gii'),
        op.join('subj-02', 'surf', 'L.white.gii'),
        op.join('subj-02', 'surf', 'R.white.gii'),
        op.join('subj-03', 'T1w.nii.gz'),
        op.join('subj-03', 'surf', 'L.pial.gii'),
        op.join('subj-03', 'surf', 'R.pial.gii'),
        op.join('subj-03', 'surf', 'L.white.gii'),
        op.join('subj-03', 'surf', 'R.white.gii')]

    with _testdir(files):
        with open('tree1.tree',   'wt') as f: f.write(tree1)
        with open('surface.tree', 'wt') as f: f.write(tree2)

        tree  = file_tree.FileTree.read('tree1.tree', '.')
        query = ftquery.FileTreeQuery(tree)

        assert sorted(query.templates) == ['T1w', 'surfdir/surface']

        qvars = query.variables()
        assert sorted(qvars.keys()) == ['hemi', 'participant', 'surf']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']
        assert qvars['surf']        == ['pial', 'white']

        qvars = query.variables('T1w')
        assert sorted(qvars.keys()) == ['participant']
        assert qvars['participant'] == ['01', '02', '03']

        qvars = query.variables('surfdir/surface')
        assert sorted(qvars.keys()) == ['hemi', 'participant', 'surf']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']
        assert qvars['surf']        == ['pial', 'white']

        got = query.query('T1w')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz'),
            op.join('subj-02', 'T1w.nii.gz'),
            op.join('subj-03', 'T1w.nii.gz')]

        got = query.query('T1w', participant='01')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz')]

        got = query.query('surfdir/surface')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'surf', 'L.pial.gii'),
            op.join('subj-01', 'surf', 'L.white.gii'),
            op.join('subj-01', 'surf', 'R.pial.gii'),
            op.join('subj-01', 'surf', 'R.white.gii'),
            op.join('subj-02', 'surf', 'L.pial.gii'),
            op.join('subj-02', 'surf', 'L.white.gii'),
            op.join('subj-02', 'surf', 'R.pial.gii'),
            op.join('subj-02', 'surf', 'R.white.gii'),
            op.join('subj-03', 'surf', 'L.pial.gii'),
            op.join('subj-03', 'surf', 'L.white.gii'),
            op.join('subj-03', 'surf', 'R.pial.gii'),
            op.join('subj-03', 'surf', 'R.white.gii')]

        got = query.query('surfdir/surface', hemi='L')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'surf', 'L.pial.gii'),
            op.join('subj-01', 'surf', 'L.white.gii'),
            op.join('subj-02', 'surf', 'L.pial.gii'),
            op.join('subj-02', 'surf', 'L.white.gii'),
            op.join('subj-03', 'surf', 'L.pial.gii'),
            op.join('subj-03', 'surf', 'L.white.gii')]

        got = query.query('surfdir/surface', surf='white')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'surf', 'L.white.gii'),
            op.join('subj-01', 'surf', 'R.white.gii'),
            op.join('subj-02', 'surf', 'L.white.gii'),
            op.join('subj-02', 'surf', 'R.white.gii'),
            op.join('subj-03', 'surf', 'L.white.gii'),
            op.join('subj-03', 'surf', 'R.white.gii')]


def test_query_variable_partial_set():
    tree1 = tw.dedent("""
    subj-{participant}
        T1w.nii.gz (T1w)
        native
            ->surface space=native (surf_native)
        standard
            ->surface (surf_standard)
    """)
    tree2 = tw.dedent("""
    {hemi}.{space}.gii (surface)
    """)

    files = [
        op.join('subj-01', 'T1w.nii.gz'),
        op.join('subj-01', 'native', 'L.native.gii'),
        op.join('subj-01', 'native', 'R.native.gii'),
        op.join('subj-01', 'standard',    'L.mni.gii'),
        op.join('subj-01', 'standard',    'R.mni.gii'),
        op.join('subj-01', 'standard',    'L.freesurfer.gii'),
        op.join('subj-01', 'standard',    'R.freesurfer.gii'),
        op.join('subj-02', 'T1w.nii.gz'),
        op.join('subj-02', 'native', 'L.native.gii'),
        op.join('subj-02', 'native', 'R.native.gii'),
        op.join('subj-02', 'standard',    'L.mni.gii'),
        op.join('subj-02', 'standard',    'R.mni.gii'),
        op.join('subj-02', 'standard',    'L.freesurfer.gii'),
        op.join('subj-02', 'standard',    'R.freesurfer.gii'),
        op.join('subj-03', 'T1w.nii.gz'),
        op.join('subj-03', 'native', 'L.native.gii'),
        op.join('subj-03', 'native', 'R.native.gii'),
        op.join('subj-03', 'standard',    'L.mni.gii'),
        op.join('subj-03', 'standard',    'R.mni.gii')]

    with _testdir(files):
        with open('tree1.tree',   'wt') as f: f.write(tree1)
        with open('surface.tree', 'wt') as f: f.write(tree2)

        tree  = file_tree.FileTree.read('tree1.tree', '.')
        query = ftquery.FileTreeQuery(tree)

        assert sorted(query.templates) == ['T1w',
                                           'surf_native/surface',
                                           'surf_standard/surface']

        qvars = query.variables()
        assert sorted(qvars.keys()) == ['hemi', 'participant', 'space']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']
        assert qvars['space']       == ['freesurfer', 'mni']

        qvars = query.variables('T1w')
        assert sorted(qvars.keys()) == ['participant']
        assert qvars['participant'] == ['01', '02', '03']

        qvars = query.variables('surf_native/surface')
        assert sorted(qvars.keys()) == ['hemi', 'participant']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']

        qvars = query.variables('surf_standard/surface')
        assert sorted(qvars.keys()) == ['hemi', 'participant', 'space']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']
        assert qvars['space']       == ['freesurfer', 'mni']

        got = query.query('T1w')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz'),
            op.join('subj-02', 'T1w.nii.gz'),
            op.join('subj-03', 'T1w.nii.gz')]

        got = query.query('T1w', participant='01')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz')]

        got = query.query('surf_native/surface')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'native', 'L.native.gii'),
            op.join('subj-01', 'native', 'R.native.gii'),
            op.join('subj-02', 'native', 'L.native.gii'),
            op.join('subj-02', 'native', 'R.native.gii'),
            op.join('subj-03', 'native', 'L.native.gii'),
            op.join('subj-03', 'native', 'R.native.gii')]

        got = query.query('surf_native/surface', hemi='L')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'native', 'L.native.gii'),
            op.join('subj-02', 'native', 'L.native.gii'),
            op.join('subj-03', 'native', 'L.native.gii')]

        got = query.query('surf_standard/surface', hemi='L')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'standard', 'L.freesurfer.gii'),
            op.join('subj-01', 'standard', 'L.mni.gii'),
            op.join('subj-02', 'standard', 'L.freesurfer.gii'),
            op.join('subj-02', 'standard', 'L.mni.gii'),
            # subj03/standard/L.freesurfer.gii was skipped when creating files
            op.join('subj-03', 'standard', 'L.mni.gii')]


def test_query_multi_subtree():
    tree1 = tw.dedent("""
    subj-{participant}
        T1w.nii.gz (T1w)
        native
            ->surface space=native (surf_native)
        mni
            ->surface space=mni (surf_mni)
    """)
    tree2 = tw.dedent("""
    {hemi}.{space}.gii (surface)
    """)

    files = [
        op.join('subj-01', 'T1w.nii.gz'),
        op.join('subj-01', 'native', 'L.native.gii'),
        op.join('subj-01', 'native', 'R.native.gii'),
        op.join('subj-01', 'mni',    'L.mni.gii'),
        op.join('subj-01', 'mni',    'R.mni.gii'),
        op.join('subj-02', 'T1w.nii.gz'),
        op.join('subj-02', 'native', 'L.native.gii'),
        op.join('subj-02', 'native', 'R.native.gii'),
        op.join('subj-02', 'mni',    'L.mni.gii'),
        op.join('subj-02', 'mni',    'R.mni.gii'),
        op.join('subj-03', 'T1w.nii.gz'),
        op.join('subj-03', 'native', 'L.native.gii'),
        op.join('subj-03', 'native', 'R.native.gii'),
        op.join('subj-03', 'mni',    'L.mni.gii'),
        op.join('subj-03', 'mni',    'R.mni.gii')]

    with _testdir(files):
        with open('tree1.tree',   'wt') as f: f.write(tree1)
        with open('surface.tree', 'wt') as f: f.write(tree2)

        tree  = file_tree.FileTree.read('tree1.tree', '.')
        query = ftquery.FileTreeQuery(tree)

        assert sorted(query.templates) == ['T1w',
                                           'surf_mni/surface',
                                           'surf_native/surface']

        qvars = query.variables()
        assert sorted(qvars.keys()) == ['hemi', 'participant']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']

        qvars = query.variables('T1w')
        assert sorted(qvars.keys()) == ['participant']
        assert qvars['participant'] == ['01', '02', '03']

        qvars = query.variables('surf_mni/surface')
        assert sorted(qvars.keys()) == ['hemi', 'participant']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']

        qvars = query.variables('surf_native/surface')
        assert sorted(qvars.keys()) == ['hemi', 'participant']
        assert qvars['hemi']        == ['L', 'R']
        assert qvars['participant'] == ['01', '02', '03']

        got = query.query('T1w')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz'),
            op.join('subj-02', 'T1w.nii.gz'),
            op.join('subj-03', 'T1w.nii.gz')]

        got = query.query('T1w', participant='01')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'T1w.nii.gz')]

        got = query.query('surf_mni/surface')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'mni', 'L.mni.gii'),
            op.join('subj-01', 'mni', 'R.mni.gii'),
            op.join('subj-02', 'mni', 'L.mni.gii'),
            op.join('subj-02', 'mni', 'R.mni.gii'),
            op.join('subj-03', 'mni', 'L.mni.gii'),
            op.join('subj-03', 'mni', 'R.mni.gii')]

        got = query.query('surf_native/surface', hemi='L')
        assert [m.filename for m in sorted(got)] == [
            op.join('subj-01', 'native', 'L.native.gii'),
            op.join('subj-02', 'native', 'L.native.gii'),
            op.join('subj-03', 'native', 'L.native.gii')]


def test_scan():

    with _test_data():
        tree      = file_tree.FileTree.read('_test_tree.tree', '.')
        gotarrays = ftquery.scan(tree)
        query     = ftquery.FileTreeQuery(tree)

    exparrays = {
        'T1w' : xr.DataArray(object(),
            dims=['participant', 'session'],
            coords={'participant' : _subjs, 'session' : _sess}),

        'T2w' : xr.DataArray(object(),
            dims=['participant', 'session'],
            coords={'participant' : _subjs, 'session' : _sess}),

        'surface' : xr.DataArray(object(),
            dims=['participant', 'session', 'surf', 'hemi'],
            coords={'participant' : _subjs,
                    'session'     : _sess,
                    'surf'        : _surfs,
                    'hemi'        : _hemis}),
        'scalar'  : xr.DataArray('scalar_file.txt'),
    }

    for subj, ses in it.product(_subjs, _sess):

        sesdir = op.join('subj-{}'.format(subj), 'ses-{}'.format(ses))
        t1wf   = op.join(sesdir, 'T1w.nii.gz')
        t2wf   = op.join(sesdir, 'T2w.nii.gz')
        exparrays['T1w'].loc[subj, ses] = t1wf
        exparrays['T2w'].loc[subj, ses] = t2wf

        for hemi, surf in it.product(_hemis, _surfs):
            surff = op.join(sesdir, '{}.{}.gii'.format(hemi, surf))

            exparrays['surface'].loc[subj, ses, surf, hemi] = surff

    assert len(gotarrays) == len(exparrays)
    for template in gotarrays.keys():
        got = gotarrays[template]
        exp = exparrays[template]

        # scalar
        if exp.shape == ():
            assert exp == got
            assert exp == query.matcharray(template)
        else:
            assert (exp == got).all()
            assert (exp == query.matcharray(template)).all()
