#!/usr/bin/env python
#
# test_saveannotations.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

from unittest import mock

import pytest

import fsl.utils.tempdir as tempdir
import fsl.data.image    as fslimage

import fsleyes.gl.annotations                   as annotations
import fsleyes.plugins.controls.annotationpanel as annotationpanel
import fsleyes.plugins.tools.saveannotations    as saveannotations
from fsleyes.tests import (run_render_test,
                           run_with_orthopanel,
                           realYield,
                           MockFileDialog)


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_serialise_deserialise():
    objs = [
        annotations.Point(         None, 1, 2,       zmin=0, zmax=10),
        annotations.Line(          None, 1, 2, 3, 4, colour=(0, 1, 0)),
        annotations.Arrow(         None, 1, 2, 3, 4, honourZLimits=True),
        annotations.Rect(          None, 1, 2, 3, 4, alpha=25, border=False),
        annotations.Ellipse(       None, 1, 2, 3, 4, filled=False),
        annotations.TextAnnotation(None, r'some text" \n ', 1, 2,
                                   colour='#00ff00', fontSize=24)
    ]

    exp = [
        'X Point colour=#a00000 lineWidth=1 alpha=100.0 honourZLimits=False '
        'zmin=0.0 zmax=10.0 x=1 y=2',
        'X Line colour=#00ff00 lineWidth=1 alpha=100.0 honourZLimits=False '
        'zmin=0.0 zmax=0.0 x1=1 y1=2 x2=3 y2=4',
        'X Arrow colour=#a00000 lineWidth=1 alpha=100.0 honourZLimits=True '
        'zmin=0.0 zmax=0.0 x1=1 y1=2 x2=3 y2=4',
        'X Rect colour=#a00000 lineWidth=1 alpha=25.0 honourZLimits=False '
        'zmin=0.0 zmax=0.0 filled=True border=False x=1 y=2 w=3 h=4',
        'X Ellipse colour=#a00000 lineWidth=1 alpha=100.0 honourZLimits=False '
        'zmin=0.0 zmax=0.0 filled=False border=True x=1 y=2 w=3 h=4',
        'X TextAnnotation colour=#00ff00 lineWidth=1 alpha=100.0 '
        'honourZLimits=False zmin=0.0 zmax=0.0 fontSize=24 '
        'coordinates=proportions text=\'some text" \\n \' x=1 y=2',
    ]

    annots       = {'X' : None, 'Y' : None, 'Z' : None}
    deserialised = []
    for o, e in zip(objs, exp):
        got = saveannotations.serialiseAnnotation(o, 'X')
        assert e == got
        des, c = saveannotations.deserialiseAnnotation(got, annots)
        assert c == 'X'
        deserialised.append(des)

    point, line, arrow, rect, ellipse, text = deserialised

    assert (point.x    == 1 and
            point.y    == 2 and
            point.zmin == 0 and
            point.zmax == 10)
    assert (line.x1     == 1 and
            line.y1     == 2 and
            line.x2     == 3 and
            line.y2     == 4 and
            line.colour == (0, 1, 0, 1))
    assert (arrow.x1 == 1 and
            arrow.y1 == 2 and
            arrow.x2 == 3 and
            arrow.y2 == 4 and
            arrow.honourZLimits)
    assert (rect.x     == 1  and
            rect.y     == 2  and
            rect.w     == 3  and
            rect.h     == 4  and
            rect.alpha == 25 and
            not rect.border)
    assert (ellipse.x     == 1  and
            ellipse.y     == 2  and
            ellipse.w     == 3  and
            ellipse.h     == 4  and
            not ellipse.filled)
    assert (text.text   == 'some text" \\n ' and
            text.x        == 1  and
            text.y        == 2  and
            text.fontSize == 24 and
            text.colour   == (0, 1, 0, 1))




# used by test_[save|load]Annotations
ANNOTS = """
X Rect colour=#ff0000 lineWidth=1 alpha=25.0 honourZLimits=False zmin=0.0 zmax=0.0 filled=True border=True x=10 y=10 w=14 h=14
Y Arrow colour=#00ff00 lineWidth=3 alpha=100.0 honourZLimits=False zmin=0.0 zmax=0.0 x1=14 y1=14 x2=10 y2=7
Z TextAnnotation colour=#0000ff lineWidth=1 alpha=100.0 honourZLimits=False zmin=0.0 zmax=0.0 fontSize=30 coordinates=proportions text=text1 x=5 y=5
""".strip()


def test_saveAnnotations():
    run_with_orthopanel(_test_saveAnnotations)

def _test_saveAnnotations(panel, overlayList, displayCtx):
    overlayList.append(fslimage.Image(op.join(datadir, '3d')))
    panel.togglePanel(annotationpanel.AnnotationPanel)
    realYield()

    xannot = panel.getXCanvas().getAnnotations()
    yannot = panel.getYCanvas().getAnnotations()
    zannot = panel.getZCanvas().getAnnotations()

    xannot.rect( 10, 10, 14, 14, colour='#ff0000', alpha=25,
                 hold=True, fixed=False)
    yannot.arrow(14, 14, 10, 7, colour='#00ff00', lineWidth=3,
                 hold=True, fixed=False)
    zannot.text( 'text1', 5, 5, colour='#0000ff', fontSize=30,
                 hold=True, fixed=False)
    realYield()

    with tempdir.tempdir(), MockFileDialog() as dlg:
        dlg.GetPath_retval = 'annotations.txt'

        saveannotations.SaveAnnotationsAction(overlayList,
                                              displayCtx,
                                              panel)()

        with open('annotations.txt', 'rt') as f:
            got = f.read()

    assert ANNOTS.strip() == got.strip()


def test_loadAnnotations():
    run_with_orthopanel(_test_loadAnnotations)

def _test_loadAnnotations(panel, overlayList, displayCtx):
    overlayList.append(fslimage.Image(op.join(datadir, '3d')))
    panel.togglePanel(annotationpanel.AnnotationPanel)
    realYield()

    with tempdir.tempdir(), MockFileDialog() as dlg:

        with open('annotations.txt', 'wt') as f:
            f.write(ANNOTS)

        dlg.GetPath_retval = 'annotations.txt'
        saveannotations.LoadAnnotationsAction(overlayList,
                                              displayCtx,
                                              panel)()
    realYield()

    xannot = panel.getXCanvas().getAnnotations()
    yannot = panel.getYCanvas().getAnnotations()
    zannot = panel.getZCanvas().getAnnotations()

    assert len(xannot.annotations) == 1
    assert len(yannot.annotations) == 1
    assert len(zannot.annotations) == 1

    x = xannot.annotations[0]
    y = yannot.annotations[0]
    z = zannot.annotations[0]

    assert isinstance(x, annotations.Rect)
    assert isinstance(y, annotations.Arrow)
    assert isinstance(z, annotations.TextAnnotation)


    assert (x.x      == 10 and
            x.y      == 10 and
            x.w      == 14 and
            x.h      == 14 and
            x.alpha  == 25 and
            x.colour == (1, 0, 0, 1))

    assert (y.x1        == 14 and
            y.y1        == 14 and
            y.x2        == 10 and
            y.y2        == 7  and
            y.lineWidth == 3  and
            y.colour    == (0, 1, 0, 1))

    assert (z.x         == 5       and
            z.y         == 5       and
            z.fontSize  == 30      and
            z.text      == 'text1' and
            z.colour    == (0, 0, 1, 1))


    xannot.rect( 10, 10, 14, 14, colour='#ff0000', alpha=25,
                 hold=True, fixed=False)
    yannot.arrow(14, 14, 10, 7, colour='#00ff00', lineWidth=3,
                 hold=True, fixed=False)
    zannot.text( 'text1', 5, 5, colour='#0000ff', fontSize=30,
                 hold=True, fixed=False)

    realYield()
