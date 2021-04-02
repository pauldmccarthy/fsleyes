#!/usr/bin/env python
#
# saveannotationsaction.py - Load/save annotations displayed on an OrthoPanel
#                            to file
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LoadAnnotationsAction` and
:class:`SaveAnnotationsAction` classes, both FSLeyes actions which can be used
to save/load :mod:`.annotations` to/from a file.  This module is tightly
coupled to the implementations of the specific :class:`.AnnotationObject`
types that are supported:

 - :class:`.Point`
 - :class:`.Line`
 - :class:`.Arrow`
 - :class:`.Rect`
 - :class:`.Ellipse`
 - :class:`.TextAnnotation`


The ``SaveAnnotationsAction`` class is an action which is added to the
FSLeyes Tools menu, and which allows the user to save all annotations that
have been added to the canvases of an :class:`.OrthoPanel` to a file. This
file can then be loaded back in via the ``LoadAnnotationsAction``.


The logic for serialising and deserialising annotations to/from string
represantations is also implemented in this module.


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
import shlex
import logging

import wx

import fsleyes_widgets.utils.status as status
import fsl.utils.settings           as fslsettings
import fsleyes.views.orthopanel     as orthopanel
import fsleyes.actions              as actions
import fsleyes.strings              as strings
import fsleyes.gl.annotations       as annotations


log = logging.getLogger(__name__)


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
        errtitle = strings.titles[  self, 'saveFileError']
        errmsg   = strings.messages[self, 'saveFileError']
        with status.reportIfError(errtitle, errmsg, raiseError=False):
            with open(filePath, 'wt') as f:
                f.write(serialiseAnnotations(ortho))


class LoadAnnotationsAction(actions.Action):
    """The ``LoadAnnotationsAction`` allos the user to load annotations
    from a file into an :class:`.OrthoPanel`.
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
                                self.__loadAnnotations)
        self.__ortho = ortho


    def __loadAnnotations(self):
        """Show a dialog prompting the user for a file to load, then loads the
        annotations contained in the file and adds them to the
        :class:`OrthoPanel`.
        """

        ortho   = self.__ortho
        msg     = strings.messages[self, 'loadFile']
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg     = wx.FileDialog(wx.GetApp().GetTopWindow(),
                                message=msg,
                                defaultDir=fromDir,
                                style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        filePath = dlg.GetPath()
        errtitle = strings.titles[  self, 'loadFileError']
        errmsg   = strings.messages[self, 'loadFileError']
        with status.reportIfError(errtitle, errmsg, raiseError=False):
            with open(filePath, 'rt') as f:
                s = f.read().strip()
            deserialiseAnnotations(ortho, s)


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
            otype = type(obj).__name__
            serialised.append('{} {} {}'.format(
                canvas, otype, serialiseAnnotation(obj)))

    return '\n'.join(serialised)


def serialiseAnnotation(obj):
    """Convert the given :class:`.AnnotationObject` to a string representation.
    """

    # All properties on all annotation
    # types that are to be serialised
    keys = ['colour', 'lineWidth', 'alpha', 'honourZLimits', 'zmin', 'zmax',
            'filled', 'border', 'fontSize', 'text', 'x', 'y', 'w', 'h',
            'x1', 'y1', 'x2', 'y2']

    # Custom formatters for some properties
    def formatColour(colour):
        colour = [int(round(c * 255)) for c in colour[:3]]
        return '#{:02x}{:02x}{:02x}'.format(*colour)

    formatters = {
        'colour' : formatColour,
        'text'   : shlex.quote
    }

    kvpairs = []
    for key in keys:
        val = getattr(obj, key, None)
        if val is not None:
            val = formatters.get(key, str)(val)
            kvpairs.append('{}={}'.format(key, val))

    return ' '.join(kvpairs)


def deserialiseAnnotations(ortho, s):
    """Deserialise all of the annotation specifications in the string ``s``,
    and add them as :class:`.AnnotationObject` instances to the canvases
    of the given :class:`.OrthoPanel`.
    """

    annots  = {'X' : ortho.getXCanvas().getAnnotations(),
               'Y' : ortho.getYCanvas().getAnnotations(),
               'Z' : ortho.getZCanvas().getAnnotations()}

    for line in s.split('\n'):
        try:
            canvas, cls, kvpairs = deserialiseAnnotation(line)
            annot                = annots[canvas]
            obj                  = cls(annot, **kvpairs)
            annot.obj(obj, hold=True, fixed=False)
            pass
        except Exception as e:
            log.warning('Error parsing annotation (%s): %s ', e, line)


def deserialiseAnnotation(s):
    """Deserialises the annotation specification in the provided string.

    Returns a tuple containing:
      - The canvas identifier, one of ``'X'`` ``'Y'``, or ``'Z'``.
      - the :class:`.AnnotationObject` type
      - A dictionary of kwargs to use to create the ``AnnotationObject``.
    """

    # Parser functions for some property types
    # (default for unlisted properties is float)
    def tobool(v):
        return v.lower() in 'true'

    parsers = {
        'colour'        : str,
        'honourZLimits' : tobool,
        'filled'        : tobool,
        'border'        : tobool,
        'text'          : str,
    }

    canvas, otype, kvpairs = s.strip().split(maxsplit=2)

    canvas  = canvas.upper()
    cls     = getattr(annotations, otype)
    kvpairs = dict([kv.split('=') for kv in shlex.split(kvpairs)])

    if canvas not in 'XYZ':
        raise ValueError('Canvas is not one of X, Y, '
                         'or Z ({})'.format(canvas))

    for k, v in kvpairs.items():
        kvpairs[k] = parsers.get(k, float)(v)

    return canvas, cls, kvpairs
