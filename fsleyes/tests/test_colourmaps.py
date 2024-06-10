#!/usr/bin/env python

import os
import os.path as op
import random
import string
import itertools as it
import textwrap as tw
from unittest import mock

from contextlib import contextmanager

import pytest

import numpy as np

import fsl.utils.settings as fslsettings
from   fsl.utils.tempdir import tempdir
import fsleyes.colourmaps as fslcm

from fsleyes.tests import (mockSettingsDir,
                           mockSiteDir,
                           mockAssetDir,
                           clearCmapsDecorator)


############
# Management
############


@contextmanager
def mockCmaps():

    cmap = tw.dedent("""
    0.3 0.4 0.5
    0.6 0.7 0.8
    """).strip()

    lut = tw.dedent("""
    1 0.3 0.4 0.5 label 1
    2 0.6 0.7 0.8 label 2
    """).strip()

    with mockSettingsDir() as userDir, \
         mockAssetDir()    as assetDir, \
         mockSiteDir()     as siteDir:
        cmap1 = op.join(assetDir, 'colourmaps', 'cmap1.cmap')
        cmap2 = op.join(userDir,  'colourmaps', 'cmap2.cmap')
        cmap3 = op.join(siteDir,  'colourmaps', 'cmap3.cmap')
        lut1  = op.join(assetDir, 'luts',       'lut1.lut')
        lut2  = op.join(userDir,  'luts',       'lut2.lut')
        lut3  = op.join(siteDir,  'luts',       'lut3.lut')
        with open(cmap1, 'wt') as f: f.write(cmap)
        with open(cmap2, 'wt') as f: f.write(cmap)
        with open(cmap3, 'wt') as f: f.write(cmap)
        with open(lut1,  'wt') as f: f.write(lut)
        with open(lut2,  'wt') as f: f.write(lut)
        with open(lut3,  'wt') as f: f.write(lut)
        yield (assetDir, userDir, siteDir)


@clearCmapsDecorator
def test_scanDirs():
    with mockSettingsDir() as userDir, \
         mockAssetDir()    as assetDir, \
         mockSiteDir()     as siteDir:
        os.mkdir(op.join(assetDir, 'colourmaps', 'sub'))
        os.mkdir(op.join(assetDir, 'luts',       'sub'))

        # builtins
        bifiles = [op.join('luts',              'lut1_builtin.lut'),
                   op.join('luts',       'sub', 'lut2_builtin.lut'),
                   op.join('luts',              'lut3_builtin.txt'),
                   op.join('colourmaps',        'cmap1_builtin.cmap'),
                   op.join('colourmaps', 'sub', 'cmap2_builtin.cmap'),
                   op.join('colourmaps',        'cmap3_builtin.txt'),
                   ]

        # user added
        uafiles = [op.join('luts',       'lut1_added.lut'),
                   op.join('luts',       'lut2_added.lut'),
                   op.join('luts',       'lut3_added.txt'),
                   op.join('colourmaps', 'cmap1_added.cmap'),
                   op.join('colourmaps', 'cmap2_added.cmap'),
                   op.join('colourmaps', 'cmap3_added.txt'),
                   ]

        # site added
        safiles = [op.join('luts',       'lut1_site.lut'),
                   op.join('luts',       'lut2_site.lut'),
                   op.join('luts',       'lut3_site.txt'),
                   op.join('colourmaps', 'cmap1_site.cmap'),
                   op.join('colourmaps', 'cmap2_site.cmap'),
                   op.join('colourmaps', 'cmap3_site.txt'),
                   ]


        for f in bifiles:
            with open(op.join(assetDir, f), 'wt'):
                pass
        for f in uafiles:
            with open(op.join(userDir, f), 'wt'):
                pass
        for f in safiles:
            with open(op.join(siteDir, f), 'wt'):
                pass

        acmapdir = op.join(assetDir, 'colourmaps')
        scmapdir = op.join(siteDir,  'colourmaps')
        ucmapdir = op.join(userDir,  'colourmaps')
        alutdir  = op.join(assetDir, 'luts')
        slutdir  = op.join(siteDir,  'luts')
        ulutdir  = op.join(userDir,  'luts')

        assert fslcm.getCmapDirs() == [ucmapdir, scmapdir, acmapdir]
        assert fslcm.getLutDirs()  == [ulutdir,  slutdir,  alutdir]

        expcmaps = {
            'cmap1_builtin'     : op.join(acmapdir,        'cmap1_builtin.cmap'),
            'sub_cmap2_builtin' : op.join(acmapdir, 'sub', 'cmap2_builtin.cmap'),
            'cmap3_builtin'     : op.join(acmapdir,        'cmap3_builtin.txt'),
            'cmap1_added'       : op.join(ucmapdir,        'cmap1_added.cmap'),
            'cmap2_added'       : op.join(ucmapdir,        'cmap2_added.cmap'),
            'cmap3_added'       : op.join(ucmapdir,        'cmap3_added.txt'),
            'cmap1_site'        : op.join(scmapdir,        'cmap1_site.cmap'),
            'cmap2_site'        : op.join(scmapdir,        'cmap2_site.cmap'),
            'cmap3_site'        : op.join(scmapdir,        'cmap3_site.txt'),
        }
        expluts  = {
            'lut1_builtin'     : op.join(alutdir,        'lut1_builtin.lut'),
            'sub_lut2_builtin' : op.join(alutdir, 'sub', 'lut2_builtin.lut'),
            'lut3_builtin'     : op.join(alutdir,        'lut3_builtin.txt'),
            'lut1_added'       : op.join(ulutdir,        'lut1_added.lut'),
            'lut2_added'       : op.join(ulutdir,        'lut2_added.lut'),
            'lut3_added'       : op.join(ulutdir,        'lut3_added.txt'),
            'lut1_site'        : op.join(slutdir,        'lut1_site.lut'),
            'lut2_site'        : op.join(slutdir,        'lut2_site.lut'),
            'lut3_site'        : op.join(slutdir,        'lut3_site.txt'),
        }

        assert fslcm.scanColourMaps()   == expcmaps
        assert fslcm.scanLookupTables() == expluts


@clearCmapsDecorator
def test_init():

    with mockCmaps() as (assetDir, userDir, siteDir):
        fslcm.init()

        cmap1 = op.join(assetDir, 'colourmaps', 'cmap1.cmap')
        cmap2 = op.join(userDir,  'colourmaps', 'cmap2.cmap')
        cmap3 = op.join(siteDir,  'colourmaps', 'cmap3.cmap')
        lut1  = op.join(assetDir, 'luts',       'lut1.lut')
        lut2  = op.join(userDir,  'luts',       'lut2.lut')
        lut3  = op.join(siteDir,  'luts',       'lut3.lut')

        assert fslcm.getColourMaps() == ['cmap1', 'cmap3', 'cmap2']
        assert fslcm.getColourMapLabel( 'cmap1') == 'cmap1'
        assert fslcm.getColourMapLabel( 'cmap2') == 'cmap2'
        assert fslcm.getColourMapLabel( 'cmap3') == 'cmap3'
        assert fslcm.getColourMapFile(  'cmap1') == cmap1
        assert fslcm.getColourMapFile(  'cmap2') == cmap2
        assert fslcm.getColourMapFile(  'cmap3') == cmap3
        assert fslcm.getColourMapKey(cmap1)      == 'cmap1'
        assert fslcm.getColourMapKey(cmap2)      == 'cmap2'
        assert fslcm.getColourMapKey(cmap3)      == 'cmap3'
        assert fslcm.getLookupTableFile('lut1')  == lut1
        assert fslcm.getLookupTableFile('lut2')  == lut2
        assert fslcm.getLookupTableFile('lut3')  == lut3
        assert fslcm.getLookupTableKey(lut1)     == 'lut1'
        assert fslcm.getLookupTableKey(lut2)     == 'lut2'
        assert fslcm.getLookupTableKey(lut3)     == 'lut3'

        assert     fslcm.isColourMapInstalled(   'cmap1')
        assert     fslcm.isColourMapInstalled(   'cmap2')
        assert     fslcm.isColourMapInstalled(   'cmap3')
        assert     fslcm.isColourMapRegistered(  'cmap1')
        assert     fslcm.isColourMapRegistered(  'cmap2')
        assert     fslcm.isColourMapRegistered(  'cmap3')
        assert not fslcm.isColourMapRegistered(  'lut1')
        assert     fslcm.isColourMapRegistered(filename=cmap1)
        assert     fslcm.isColourMapRegistered(filename=cmap2)
        assert     fslcm.isColourMapRegistered(filename=cmap3)
        assert not fslcm.isColourMapRegistered(filename=lut1)
        assert     fslcm.isLookupTableInstalled( 'lut1')
        assert     fslcm.isLookupTableInstalled( 'lut2')
        assert     fslcm.isLookupTableInstalled( 'lut3')
        assert     fslcm.isLookupTableRegistered('lut1')
        assert     fslcm.isLookupTableRegistered('lut2')
        assert     fslcm.isLookupTableRegistered('lut3')
        assert not fslcm.isLookupTableRegistered('cmap1')
        assert     fslcm.isLookupTableRegistered(filename=lut1)
        assert     fslcm.isLookupTableRegistered(filename=lut2)
        assert     fslcm.isLookupTableRegistered(filename=lut3)
        assert not fslcm.isLookupTableRegistered(filename=cmap1)

        luts = fslcm.getLookupTables()
        assert len(luts)              == 3
        assert luts[0].key            == 'lut1'
        assert luts[1].key            == 'lut3'
        assert luts[2].key            == 'lut2'


@clearCmapsDecorator
def test_register():

    cmap = tw.dedent("""
    0 0 0
    0 0 1
    0 1 1
    1 1 1
    """).strip()

    lut = tw.dedent("""
    1 0 0 0 label 1
    2 0 0 1 label 2
    3 0 1 1 label 3
    4 1 1 1 label 4
    """).strip()

    with mockCmaps() as (assetDir, userDir, siteDir):
        fslcm.init()

        with open('cmap.txt', 'wt') as f: f.write(cmap)
        with open('lut.txt',  'wt') as f: f.write(lut)

        assert not fslcm.isColourMapRegistered('mycmap')
        fslcm.registerColourMap('cmap.txt', key='mycmap', name='My cmap')
        fslcm.getColourMap('mycmap')
        assert     fslcm.isColourMapRegistered('mycmap')
        assert not fslcm.isColourMapInstalled( 'mycmap')
        assert     fslcm.getColourMapLabel('mycmap') == 'My cmap'
        fslcm.installColourMap('mycmap')
        assert     fslcm.isColourMapInstalled( 'mycmap')

        assert not fslcm.isLookupTableRegistered('mylut')
        fslcm.registerLookupTable('lut.txt', key='mylut', name='My lut')
        assert     fslcm.isLookupTableRegistered('mylut')
        assert not fslcm.isLookupTableInstalled( 'mylut')
        assert     fslcm.getLookupTable('mylut').name == 'My lut'
        fslcm.installLookupTable('mylut')
        assert     fslcm.isLookupTableInstalled( 'mylut')



##########
# File I/O
##########


def test_fileType():

    cmap = tw.dedent("""
    0.5 0.7 0.1
    0.5 0.7 0.1
    """).strip()

    lut = tw.dedent("""
    1 0.5 0.7 0.1 label
    2 0.5 0.7 0.1 label
    """).strip()

    vest = tw.dedent("""
    %!VEST-LUT
    <-color{0.000000,0.000000,0.000000}->
    <-color{0.010000,0.010000,0.010000}->
    """).strip()

    bad =  tw.dedent("""
    this is not a colour map file
    """).strip()

    with tempdir():
        with open('cmap.txt', 'wt') as f: f.write(cmap)
        with open('lut.txt',  'wt') as f: f.write(lut)
        with open('vest.txt', 'wt') as f: f.write(vest)
        with open('bad.txt',  'wt') as f: f.write(bad)

        assert fslcm.fileType('cmap.txt') == 'cmap'
        assert fslcm.fileType('lut.txt')  == 'lut'
        assert fslcm.fileType('vest.txt') == 'vest'

        with pytest.raises(ValueError):
            fslcm.fileType('bad.txt')


def test_loadColourMapFile():

    cmap = tw.dedent("""
    0.0 0.5 1.0
    0.3 0.4 0.5
    0.5 0.6 0.7
    """).strip()

    vest = tw.dedent("""
    %!VEST-LUT
    <-color{0.0,0.5,1.0}->
    <-color{0.3,0.4,0.5}->
    <-color{0.5,0.6,0.7}->
    """).strip()

    exp    = np.array([[0.0, 0.5, 1.0],
                       [0.3, 0.4, 0.5],
                       [0.5, 0.6, 0.7]])
    explut = np.hstack((np.arange(1, 4).reshape(-1, 1), exp))

    with tempdir():
        with open('cmap.txt', 'wt') as f: f.write(cmap)
        with open('vest.txt', 'wt') as f: f.write(vest)

        gotcmap    = fslcm.loadColourMapFile('cmap.txt')
        gotvest    = fslcm.loadColourMapFile('vest.txt')
        gotcmaplut = fslcm.loadColourMapFile('cmap.txt', aslut=True)

        assert np.all(np.isclose(gotcmap,    exp))
        assert np.all(np.isclose(gotvest,    exp))
        assert np.all(np.isclose(gotcmaplut, explut))


def test_loadLookupTableFile():
    # Test file without names

    lut = tw.dedent("""
    1 0.0 0.5 1.0 label 1
    4 0.3 0.4 0.5 label 4
    7 0.5 0.6 0.7 label 7
    """).strip()

    lutnoname = tw.dedent("""
    1 0.0 0.5 1.0
    4 0.3 0.4 0.5
    7 0.5 0.6 0.7
    """).strip()

    lutcomments = tw.dedent("""
    # comments
    1 0.0 0.5 1.0 label 1
    # should be ignored
    4 0.3 0.4 0.5 label 4
    7 0.5 0.6 0.7 label 7
    """).strip()

    cmap = tw.dedent("""
    0.0 0.5 1.0
    0.3 0.4 0.5
    0.5 0.6 0.7
    """).strip()

    exp     = np.array([[1, 0.0, 0.5, 1.0],
                        [4, 0.3, 0.4, 0.5],
                        [7, 0.5, 0.6, 0.7]])
    expcmap = np.array([[1, 0.0, 0.5, 1.0],
                        [2, 0.3, 0.4, 0.5],
                        [3, 0.5, 0.6, 0.7]])

    with tempdir():
        with open('lut.txt',         'wt') as f: f.write(lut)
        with open('lutnoname.txt',   'wt') as f: f.write(lutnoname)
        with open('lutcomments.txt', 'wt') as f: f.write(lutcomments)
        with open('cmap.txt',        'wt') as f: f.write(cmap)

        gotlut         = fslcm.loadLookupTableFile('lut.txt')
        gotlutnoname   = fslcm.loadLookupTableFile('lutnoname.txt')
        gotlutcomments = fslcm.loadLookupTableFile('lutcomments.txt')
        gotcmap        = fslcm.loadLookupTableFile('cmap.txt')

        assert np.all(np.isclose(gotlut[        0], exp))
        assert np.all(np.isclose(gotlutnoname[  0], exp))
        assert np.all(np.isclose(gotlutcomments[0], exp))
        assert np.all(np.isclose(gotcmap[       0], expcmap))

        assert gotlut[        1] == ['label 1', 'label 4', 'label 7']
        assert gotlutnoname[  1] == ['1',       '4',       '7']
        assert gotlutcomments[1] == ['label 1', 'label 4', 'label 7']
        assert gotcmap[       1] == ['1',       '2',       '3']


###############
# Miscellaneous
###############


def test_briconToScaleOffset():
    assert fslcm.briconToScaleOffset(0.5,  0.5, 100) == (1,   0)
    assert fslcm.briconToScaleOffset(0.25, 0.5, 100) == (1, -50)
    assert fslcm.briconToScaleOffset(0.75, 0.5, 100) == (1,  50)


def test_briconToDisplayRange():

    tests = list(it.product(np.linspace(0, 1, 5),
                            np.linspace(0, 1, 5)))

    # bricon of 0.5/0.5 should result in a
    # display range equal to the data range
    assert fslcm.briconToDisplayRange((0, 100), 0.5, 0.5) == (0, 100)

    for inbri, incon in tests:
        dmin,   dmax   = fslcm.briconToDisplayRange((0, 100), inbri, incon)
        outbri, outcon = fslcm.displayRangeToBricon((0, 100), (dmin, dmax))
        assert np.all(np.isclose((inbri, incon), (outbri, outcon)))


def test_applyBricon():

    rgb  = np.random.random((10, 3))
    rgba = np.random.random((10, 4))

    # bricon of 0.5/0.5 should have no effect
    assert np.all(np.isclose(rgb,  fslcm.applyBricon(rgb,  0.5, 0.5)))
    assert np.all(np.isclose(rgba, fslcm.applyBricon(rgba, 0.5, 0.5)))

    # we should be able to pass in a single
    # colour
    onergb  = [0.3, 0.4, 0.5]
    onergba = [0.3, 0.4, 0.5, 0.6]
    assert np.all(np.isclose(onergb,  fslcm.applyBricon(onergb,  0.5, 0.5)))
    assert np.all(np.isclose(onergba, fslcm.applyBricon(onergba, 0.5, 0.5)))


def test_randomX():
    c1 = fslcm.randomColour()
    c2 = fslcm.randomBrightColour()
    c3 = fslcm.randomDarkColour()

    for c in [c1, c2, c3]:
        assert c.shape == (3,)
        assert np.all((c >= 0) & (c <= 1))


def test_complementaryColour():
    rgb  = [0.3, 0.4, 0.5]
    rgba = [0.3, 0.4, 0.5, 0.6]

    crgb  = fslcm.complementaryColour(rgb)
    crgba = fslcm.complementaryColour(rgba)

    assert len(crgb)  == 3
    assert len(crgba) == 4
    assert crgba[3]   == 0.6


def test_LookupTable():
    lut = tw.dedent("""
    1 0 0 0 Label 1
    2 0 0 1 Label 2
    3 0 1 1 Label 3
    4 1 1 1 Label 4
    """).strip()

    colours = [(0, 0, 0, 1),
               (0, 0, 1, 1),
               (0, 1, 1, 1),
               (1, 1, 1, 1)]


    with tempdir():
        with open('lut.txt', 'wt') as f:
            f.write(lut)

        lut = fslcm.LookupTable('mylut', 'My LUT', 'lut.txt')

        assert lut.key   == 'mylut'
        assert lut.name  == 'My LUT'
        assert str( lut) == 'My LUT'
        assert repr(lut) == 'My LUT'
        assert len(lut)  == 4
        for i in range(3):
            assert lut[i].value     == i + 1
            assert lut.index(i + 1) == i
        assert lut.max() == 4
        assert lut.saved

        for i in range(4):
            val  = i + 1
            lbl  = lut.get(val)
            name = 'Label {}'.format(val)
            assert lbl.value             == val
            assert lbl.name              == name
            assert lbl.internalName      == name.lower()
            assert tuple(lbl.colour)     == colours[i]
            assert lut.getByName(name)   == lbl
            assert list(lut.labels())[i] == lbl
            repr(lbl)
            hash(lbl)

        called = {}

        def removed(lt, top, args):
            called['removed'] = args

        def added(lt, top, args):
            called['added'] = args

        def saved(lt, top, args):
            called['saved'] = True

        def label(lt, top, args):
            called['label'] = args

        lut.register('l1', removed, topic='removed')
        lut.register('l2', added,   topic='added')
        lut.register('l3', saved,   topic='saved')
        lut.register('l4', label,   topic='label')

        lbl0      = list(lut.labels())[0]
        lbl0.name = 'My Label 1!'

        assert called['saved']
        assert called['label'] == (lbl0, 0)
        assert not lut.saved

        called.pop('saved')
        lut.save('newfile.lut')
        assert called['saved']
        assert lut.saved

        called.pop('saved')
        lut.delete(4)
        assert len(lut)  == 3
        assert lut.max() == 3
        assert not lut.saved
        assert called['saved']

        called.pop('saved')
        lut.save('newfile.lut')
        assert lut.saved
        lbl = lut.new('New big label')
        assert lbl.value == 4
        assert lut.max() == 4
        assert len(lut)  == 4
        assert not lut.saved
        assert called['added'] == (lbl, 3)

        called.pop('saved')
        lut.save('newfile.lut')
        assert lut.saved
        lbl = lut.insert(7, name='New huge label')
        assert lbl.value == 7
        assert lut.max() == 7
        assert len(lut)  == 5
        assert not lut.saved
        assert called['added'] == (lbl, 4)
