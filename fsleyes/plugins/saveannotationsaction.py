#!/usr/bin/env python
#
# saveannotationsaction.py - Save annotations displayed on an OrthoPanel
#                            to file
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`SaveAnnotationsActions` class, a FSLeyes
action which can be used to save :mod:`.annotations` to a file.  This module
is tightly coupled to the implementations of the specific
:class:`.AnnotationObject` types that are supported:

 - :class:`.Point`
 - :class:`.Line`
 - :class:`.Arrow`
 - :class:`.Rect`
 - :class:`.Ellipse`
 - :class:`.TextAnnotation`


The ``SaveAnnotationsAction`` class is an action which is added to the
FSLeyes Tools menu, and which allows the user to save all annotations that
have been added to the canvases of an :class:`.OrthoPanel` to a file. This
file can then be loaded back in via the :class:`.LoadAnnotationsAction`.


The logic for serialising annotations to file is implemented in this module,
and for de-serialising annotations from file in the
:mod:`.loadannotationsaction` module.


A FSLeyes annotations file is a plain text file where each line contains
a description of one :class:`.AnnotationObject`. An example of a FSLeyes
annotation file is::

    X Line lineWidth=4 colour=#0090a0 alpha=100 honourZLimits=False zmin=89.0  zmax=90.0  x1=48.7 y1=117.4 x2=39.1 y2=65.5
    Y Rect lineWidth=4 colour=#ff0800 alpha=100 honourZLimits=False zmin=107.0 zmax=108.0 filled=False border=True x=43.3 y=108.1 w=71.5 h=-62.7
    Y TextAnnotation lineWidth=5 colour=#e383ff alpha=100 honourZLimits=False zmin=107.0 zmax=108.0 text='' fontSize=20 x=10.9 y=154.2


Each line has the form::

    <canvas> <type> key=value [key=value ...]

where:

 - ``<canvas>`` is one of ``X``, ``Y`` or ``Z``, indicating the ortho canvas
   that the annotation is drawn on

 - ``<type>`` is the annotation type, one of ``Point``, ``Line``, ``Arrow``,
   ``Rect``, ``Ellipse`` or ``TextAnnotation``.

 - ``key=value`` contains the name and value of one property of the annotation.

The following key-value pairs are set for all annotation types:

 - ``colour``        - Annotation colour, as string of the form ``#RRGGBB``
 - ``lineWidth``     - Line width in pixels
 - ``alpha``         - Transparency, between 0 and 10
 - ``honourZLimits`` - ``True`` or ``False``, whether ``zmin`` and ``zmax``
                       should be applied
 - ``zmin``          - Minimum depth value, as a floating point number
 - ``zmax``          - Maximum depth value, as a floating point number

The following additional key-value pairs are set for specific annotation
types.  All coordinates and lengths are relative to the display coordinate
system.

 - ``Point``
   - ``x`` X coordinate
   - ``y`` Y coordinate

 - ``Line`` and ``Arrow``
   - ``x1`` X coordinate of first point
   - ``y1`` Y coordinate of first point
   - ``x2`` X coordinate of second point
   - ``y2`` Y coordinate of second point

 - ``Rect`` and ``Ellipse``
   - ``filled`` ``True`` or ``False``, whether the rectangle/ellipse is
     filled
   - ``border`` ``True`` or ``False``, whether the rectangle/ellipse is
     drawn with a border
   - ``x`` X coordinate of one corner of the rectangle, or the ellipse centre
   - ``y`` Y coordinate of one corner of the rectangle, or the ellipse centre
   - ``w`` Rectangle width, relative to ``x``, or horizontal radius of elliipse
   - ``h`` Rectangle height, relative to ``y``, or vertical radius of elliipse

 - ``TextAnnotation``
   - ``text`` Displayed text, quoted with ``shlex.quote``
   - ``fontSize`` Font size in points (relative to the canvas scaling that
     was in place at the time that the text was created)
   - ``x`` Bottom left X coordinate of text
   - ``y`` Bottom left Y coordinate of text
"""


import os
import sys
import shlex

import wx

import fsl.utils.settings       as fslsettings
import fsleyes.views.orthopanel as orthopanel
import fsleyes.actions          as actions
import fsleyes.strings          as strings


class SaveAnnotationsAction(actions.Action):
    """The ``SaveAnnotationsAction`` allos the user to save annotations
    that have been added to an :class:`.OrthoPanel` to a file.
    """


    @staticmethod
    def supportedViews():
        """This action is only intended to work with :class:`.OrthoPanel`
        views.
        """
        return [orthopanel.OrthoPanel]


    def __init__(self, overlayList, displayCtx, ortho):
        """Create a ``SaveAnnotationsAction``.

        :arg overlayList: The :class:`.OverlayList`
        :arg displayCtx:  The :class:`.DisplayContext`
        :arg ortho:       The :class:`.OrthoPanel`.
        """
        actions.Action.__init__(self, overlayList, displayCtx,
                                self.__saveAnnotations)
        self.__ortho = ortho


    def __saveAnnotations(self):
        """Show a dialog prompting the user for a file to save to,
        then serialises all annotations, and saves them to that file.
        """

        ortho   = self.__ortho
        msg     = strings.messages[self, 'saveFile']
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.FileDialog(wx.GetApp().GetTopWindow(),
                                message=msg,
                                defaultDir=fromDir,
                                defaultFile='annotations.txt',
                                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()

        with open(filePath, 'wt') as f:
            f.write(serialiseAnnotations(ortho))


def serialiseAnnotations(ortho):
    """Serialise all of the annotations for each canvas of the given
    :class:`.OrthoPanel` to a string representation.
    """

    serialised = []
    allAnnots  = {'X' : ortho.getXCanvas().getAnnotations(),
                  'Y' : ortho.getYCanvas().getAnnotations(),
                  'Z' : ortho.getZCanvas().getAnnotations()}

    for canvas, annots in allAnnots.items():
        for obj in annots.annotations:
            serialised.append('{} {}'.format(canvas, serialiseAnnotation(obj)))

    return '\n'.join(serialised)


def serialiseAnnotation(obj):
    """Convert the given :class:`.AnnotationObject` to a string representation.
    """

    mod    = sys.modules[__name__]
    otype  = type(obj).__name__
    sfunc  = getattr(mod, '_serialise{}'.format(otype))
    colour = [int(round(c * 255)) for c in obj.colour[:3]]

    properties = {
        'lineWidth'     : str(obj.lineWidth),
        'colour'        : '#{:02x}{:02x}{:02x}'.format(*colour),
        'alpha'         : str(obj.alpha),
        'honourZLimits' : str(obj.honourZLimits),
        'zmin'          : str(obj.zmin),
        'zmax'          : str(obj.zmax),
    }

    s = ' '.join([
        otype,
        ' '.join(['{}={}'.format(k, v) for k, v in properties.items()]),
        sfunc(obj)])

    return s


def _serialisePoint(point):
    """Convert the given :class:`.Point` to a string representation. """
    return 'x={} y={}'.format(*point.xy)


def _serialiseLine(line):
    """Convert the given :class:`.Line` to a string representation. """
    return 'x1={} y1={} x2={} y2={}'.format(*line.xy1, *line.xy2)


def _serialiseArrow(arrow):
    """Convert the given :class:`.Arrow` to a string representation. """
    return _serialiseLine(arrow)


def _serialiseRect(rect):
    """Convert the given :class:`.Rect` to a string representation. """
    return 'filled={} border={} x={} y={} w={} h={}'.format(
        rect.filled, rect.border, *rect.xy, rect.w, rect.h)


def _serialiseEllipse(ellipse):
    """Convert the given :class:`.Ellipse` to a string representation. """
    return _serialiseRect(ellipse)


def _serialiseTextAnnotation(text):
    """Convert the given :class:`.TextAnnotation` to a string representation.
    """
    return 'text={} fontSize={} x={} y={}'.format(
        shlex.quote(text.text), text.fontSize, *text.pos)
