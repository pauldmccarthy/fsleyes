#!/usr/bin/env python
#
# test_saveannotations.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsleyes.gl.annotations                as annotations
import fsleyes.plugins.tools.saveannotations as saveannotations
from .. import run_render_test


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
