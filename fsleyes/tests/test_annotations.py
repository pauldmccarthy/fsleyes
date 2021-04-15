#!/usr/bin/env python
#
# test_annotations.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from fsleyes.tests import run_cli_tests


def test_point():
    def hook(overlayList, displayCtx, sceneOpts, canvases):
        xannot = canvases[0].getAnnotations()
        yannot = canvases[1].getAnnotations()
        zannot = canvases[2].getAnnotations()
        p1 = xannot.point(12, 15, colour='#ff0000', lineWidth=3)
        yannot.point(20, 16, colour='#00ff00', lineWidth=5)
        zannot.point(13, 15, colour='#0000ff', lineWidth=8, alpha=50)
        assert     p1.hit(12, 15)
        assert not p1.hit(14, 17)
        p1.move(2, 2)

    run_cli_tests('test_annotations_point', '3d', hook=hook)


def test_line():
    def hook(overlayList, displayCtx, sceneOpts, canvases):
        xannot = canvases[0].getAnnotations()
        yannot = canvases[1].getAnnotations()
        zannot = canvases[2].getAnnotations()
        l1 = xannot.line(12, 12, 15, 15, colour='#ff0000', lineWidth=3)
        yannot.line(13, 12, 20, 16, colour='#00ff00', lineWidth=5)
        zannot.line(20, 10, 13, 15, colour='#0000ff', lineWidth=8, alpha=50)

        assert     l1.hit(12, 12)
        assert not l1.hit(11, 11)
        l1.move(1, -1)

    run_cli_tests('test_annotations_line', '3d', hook=hook)


def test_arrow():
    def hook(overlayList, displayCtx, sceneOpts, canvases):
        xannot = canvases[0].getAnnotations()
        yannot = canvases[1].getAnnotations()
        zannot = canvases[2].getAnnotations()
        a1 = xannot.arrow(12, 12, 15, 15, colour='#ff0000', lineWidth=3)
        yannot.arrow(13, 12, 20, 16, colour='#00ff00', lineWidth=5)
        zannot.arrow(20, 10, 13, 15, colour='#0000ff', lineWidth=8, alpha=50)

        assert     a1.hit(12, 12)
        assert not a1.hit(11, 11)
        a1.move(1, -1)

    run_cli_tests('test_annotations_arrow', '3d', hook=hook)


def test_rect():
    def hook(overlayList, displayCtx, sceneOpts, canvases):
        xannot = canvases[0].getAnnotations()
        yannot = canvases[1].getAnnotations()
        zannot = canvases[2].getAnnotations()
        r1 = xannot.rect(12, 12, 15, 15,
                         colour='#ff0000',
                         lineWidth=3,
                         filled=False)
        yannot.rect(13, 12, 20, 16,
                    colour='#00ff00',
                    lineWidth=5,
                    border=False,
                    alpha=50)
        zannot.rect(20, 10, 13, 15,
                    colour='#0000ff',
                    lineWidth=8,
                    alpha=50)

        assert     r1.hit(13, 13)
        assert not r1.hit(11, 11)
        r1.move(1, -1)

    run_cli_tests('test_annotations_rect', '3d', hook=hook)



def test_ellipse():
    def hook(overlayList, displayCtx, sceneOpts, canvases):
        xannot = canvases[0].getAnnotations()
        yannot = canvases[1].getAnnotations()
        zannot = canvases[2].getAnnotations()
        e1 = xannot.ellipse(12, 12, 3, 4,
                            colour='#ff0000',
                            lineWidth=3,
                            filled=False)
        yannot.ellipse(13, 12, 4, 3,
                       colour='#00ff00',
                       lineWidth=5,
                       border=False,
                       alpha=50)
        zannot.ellipse(20, 10, 5, 2,
                       colour='#0000ff',
                       lineWidth=8,
                       alpha=50)

        assert     e1.hit(13, 13)
        assert not e1.hit(15.5, 14.5)
        e1.move(1, 3)

    run_cli_tests('test_annotations_ellipse', '3d', hook=hook)


def test_text():
    def hook(overlayList, displayCtx, sceneOpts, canvases):
        xannot = canvases[0].getAnnotations()
        yannot = canvases[1].getAnnotations()
        zannot = canvases[2].getAnnotations()
        t1 = xannot.text('text1', 12, 12,
                         coordinates='display',
                         colour='#ff0000',
                         fontSize=48)
        yannot.text('text2', 0.5, 0.75,
                    coordinates='proportions',
                    halign='centre',
                    colour='#00ff00')
        zannot.text('text3',
                    12, 12,
                    colour='#0000ff',
                    coordinates='display',
                    fontSize=12,
                    alpha=50)
        zannot.text('text4',
                    20, 150,
                    colour='#0000ff',
                    coordinates='pixels',
                    alpha=50)
        # Can't perform hit test, as the text annotation
        # only updates the position on the underlying
        # gl.text.Text object at draw time

    run_cli_tests('test_annotations_text', '3d', hook=hook)
