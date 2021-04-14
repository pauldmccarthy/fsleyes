#!/usr/bin/env python
#
# annotationpanel.py - The AnnotationPanel
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains the :class:`AnnotationPanel` class, a FSLeyes control
panel which allows the user to annotate the canvases of an
:class:`.OrthoPanel`.
"""


import copy

import wx

import fsleyes_widgets.elistbox                      as elb
import fsleyes_props                                 as props
import fsleyes_widgets.widgetlist                    as widgetlist
import fsleyes_widgets.bitmapradio                   as bmpradio
import fsleyes.strings                               as strings
import fsleyes.icons                                 as fslicons
import fsleyes.views.orthopanel                      as orthopanel
import fsleyes.controls.controlpanel                 as ctrlpanel
import fsleyes.plugins.profiles.orthoannotateprofile as annotprofile
import fsleyes.gl.annotations                        as annotations


class AnnotationPanel(ctrlpanel.ControlPanel):
    """The ``AnnotationPanel`` contains controls allowing the user to add
    annotations to the canvases in an :class:`.OrthoPanel`. The user is able
    to add points, lines, rectangles, ellipses, and text to any canvas, and
    can adjust the properties (e.g. colour, thickness) of each annotation.

    When a user selects an annotation to add, the
    :class:`.OrthoAnnotateProfile` is enabled on the ``OrthoPanel``, which
    provides user interaction.
    """


    # These properties are used to synchronise property
    # values between the ortho edit profile, and newly
    # added or selected annotation objects
    colour        = copy.copy(annotprofile.OrthoAnnotateProfile.colour)
    fontSize      = copy.copy(annotprofile.OrthoAnnotateProfile.fontSize)
    lineWidth     = copy.copy(annotprofile.OrthoAnnotateProfile.lineWidth)
    filled        = copy.copy(annotprofile.OrthoAnnotateProfile.filled)
    border        = copy.copy(annotprofile.OrthoAnnotateProfile.border)
    honourZLimits = copy.copy(annotprofile.OrthoAnnotateProfile.honourZLimits)
    alpha         = copy.copy(annotprofile.OrthoAnnotateProfile.alpha)


    # Just used as a convenience
    DISPLAY_PROPERTIES = ['colour', 'fontSize', 'lineWidth', 'filled',
                          'border', 'honourZLimits', 'alpha']


    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``CropImagePanel`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        return [orthopanel.OrthoPanel]


    @staticmethod
    def profileCls():
        """Returns the :class:`.OrthoAnnotateProfile` class, which needs to be
        activated in conjunction with the ``AnnotationPanel``.
        """
        return annotprofile.OrthoAnnotateProfile


    @staticmethod
    def defaultLayout():
        """Returns a dictionary containing layout settings to be passed to
        :class:`.ViewPanel.togglePanel`.
        """
        return {'location' : wx.LEFT}


    def __init__(self, parent, overlayList, displayCtx, ortho):
        """Create an ``AnnotationPanel``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg ortho:       The :class:`.OrthoPanel` instance.
        """
        ctrlpanel.ControlPanel.__init__(
            self, parent, overlayList, displayCtx, ortho)
        self.__ortho = ortho

        self.__buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__mainSizer   = wx.BoxSizer(wx.VERTICAL)

        # Listbox containing all annotations
        # that have been added to all canvases,
        # sorted by creation time
        self.__annotList   = elb.EditableListBox(
            self, style=(elb.ELB_NO_ADD | elb.ELB_REVERSE))

        # Stores a reference to the most recently
        # selected annotation object, as we need
        # to bind/unbind property listeners on it
        self.__selected = None

        # Widgets that can be used to set display
        # properties for newly added annotations,
        # and for the existing currently selected
        # annotation in the listbox
        self.__widgets       = widgetlist.WidgetList(self, minHeight=24)
        self.__colour        = props.makeWidget(self.__widgets, self, 'colour')
        self.__filled        = props.makeWidget(self.__widgets, self, 'filled')
        self.__border        = props.makeWidget(self.__widgets, self, 'border')
        self.__honourZLimits = props.makeWidget(self.__widgets, self,
                                                'honourZLimits')
        self.__fontSize      = props.makeWidget(self.__widgets, self,
                                                'fontSize', slider=False)
        self.__lineWidth     = props.makeWidget(self.__widgets, self,
                                                'lineWidth', slider=False)
        self.__alpha         = props.makeWidget(self.__widgets, self,
                                                'alpha', spin=False)

        self.__widgets.AddWidget(self.__colour,
                                 strings.labels[self, 'colour'])
        self.__widgets.AddWidget(self.__alpha,
                                 strings.labels[self, 'alpha'])
        self.__widgets.AddWidget(self.__fontSize,
                                 strings.labels[self, 'fontSize'])
        self.__widgets.AddWidget(self.__lineWidth,
                                 strings.labels[self, 'lineWidth'])
        self.__widgets.AddWidget(self.__filled,
                                 strings.labels[self, 'filled'])
        self.__widgets.AddWidget(self.__border,
                                 strings.labels[self, 'border'])
        self.__widgets.AddWidget(self.__honourZLimits,
                                 strings.labels[self, 'honourZLimits'])

        # Radio box buttons allowing the user to
        # select an annotation type to draw
        self.__annotOptions = bmpradio.BitmapRadioBox(
            self, style=bmpradio.BMPRADIO_ALLOW_DESELECTED)

        icons = {
            'text'    : [fslicons.loadBitmap('textAnnotationHighlight24'),
                         fslicons.loadBitmap('textAnnotation24')],
            'rect'    : [fslicons.loadBitmap('rectAnnotationHighlight24'),
                         fslicons.loadBitmap('rectAnnotation24')],
            'line'    : [fslicons.loadBitmap('lineAnnotationHighlight24'),
                         fslicons.loadBitmap('lineAnnotation24')],
            'arrow'   : [fslicons.loadBitmap('arrowAnnotationHighlight24'),
                         fslicons.loadBitmap('arrowAnnotation24')],
            'point'   : [fslicons.loadBitmap('pointAnnotationHighlight24'),
                         fslicons.loadBitmap('pointAnnotation24')],
            'ellipse' : [fslicons.loadBitmap('ellipseAnnotationHighlight24'),
                         fslicons.loadBitmap('ellipseAnnotation24')],
        }

        for option, icons in icons.items():
            self.__annotOptions.AddChoice(*icons, clientData=option)

        self.__mainSizer.Add(self.__annotList,    flag=wx.EXPAND, proportion=1)
        self.__mainSizer.Add(self.__widgets,      flag=wx.EXPAND)
        self.__mainSizer.Add(self.__annotOptions, flag=wx.EXPAND)

        self.SetSizer(self.__mainSizer)

        self.__annotOptions.Bind(bmpradio.EVT_BITMAP_RADIO_EVENT,
                                 self.__onAnnotOption)

        self.__annotList.Bind(elb.EVT_ELB_REMOVE_EVENT,
                              self.__annotListItemRemoved)
        self.__annotList.Bind(elb.EVT_ELB_MOVE_EVENT,
                              self.__annotListItemMoved)
        self.__annotList.Bind(elb.EVT_ELB_SELECT_EVENT,
                              self.__annotListItemSelected)

        for propName in self.DISPLAY_PROPERTIES:
            self.addListener(propName, self.name,
                             self.__displayPropertyChanged)

        for canvas in ortho.getGLCanvases():
            canvas.getAnnotations().addListener(
                'annotations', self.name, self.__annotationsChanged)

        # populate annotations listbox
        self.__annotationsChanged()


    def destroy(self):
        """Must be called when this ``AnnoationPanel`` is no longer needed.
        Removes property listeners and clears references.
        """
        super().destroy()
        for canvas in self.__ortho.getGLCanvases():
            canvas.getAnnotations().removeListener('annotations', self.name)
        self.__annotListItemSelected()
        self.__ortho = None


    def __annotationsChanged(self, *a):
        """Called when the :attr:`.Annotations.annotations` list of any
        :class:`.SliceCanvas` changes. Makes sure that the contents of the
        annotations list box is up to date, and selects the most recently
        added annotation.
        """

        alist     = self.__annotList
        allAnnots = []

        for canvas in self.__ortho.getGLCanvases():
            allAnnots.extend(canvas.getAnnotations().annotations)

        alist.Clear()

        for obj in allAnnots:
            canvas = 'XYZ'[obj.annot.canvas.opts.zax]
            if isinstance(obj, annotations.TextAnnotation):
                name = obj.text
            else:
                name = strings.labels[self, obj]
            alist.Append('[{}] {}'.format(canvas, name), obj)

        # select the most recently added annotation,
        # and bind it to the display settings widgets
        if len(allAnnots) > 0:
            alist.SetSelection(len(allAnnots) - 1)
            self.__annotListItemSelected(obj=allAnnots[-1])


    def __displayPropertyChanged(self, *a):
        """Called when any display property changes. Refreshes all canvases.
        """
        if self.__selected is not None:
            self.__ortho.Refresh()


    def __annotListItemRemoved(self, ev):
        """Called when an item is removed from the annotations list box.
        Removes it from the corresponding :attr:`.Annotations.annotations`
        list.
        """
        obj   = ev.data
        annot = obj.annot
        with props.suppress(annot, 'annotations'):
            annot.dequeue(obj, hold=True, fixed=False)
        self.__annotListItemSelected()
        obj.annot.canvas.Refresh()


    def __annotListItemMoved(self, ev):
        """Called when an item is moved in the annotations list box.  Syncs
        the new item order on the corresponding
        :attr:`.Annotations.annotations` list.
        """
        alist   = self.__annotList
        obj     = ev.data
        annot   = obj.annot
        allobjs = [o for o in alist.GetData() if o.annot is annot]

        with props.suppress(annot, 'annotations'):
            annot.annotations[:] = list(allobjs)
        annot.canvas.Refresh()


    def __annotListItemSelected(self, ev=None, obj=None):
        """Called when an item is selected in the annotations listbox, or
        programmatically at various times. If the properties of an
        :class:`.AnnotationObject` are bound to the display settings widgets,
        they are unbound. If an annotation has been selected in the annotations
        list box, the display settings widgets are bound to its properties.
        """

        if ev is not None:
            obj = ev.data

        prev            = self.__selected
        self.__selected = obj

        for propName in self.DISPLAY_PROPERTIES:
            if prev is not None and hasattr(prev, propName):
                self.unbindProps(propName, prev)
            if obj is not None and hasattr(obj, propName):
                self.bindProps(propName, obj)


    def __onAnnotOption(self, ev):
        """Called when the user selects an annnotation type to draw. Changes
        the :class:`.OrthoAnnotateProfile` mode.
        """
        self.__annotList.ClearSelection()
        self.__annotListItemSelected()

        profile = self.__ortho.currentProfile

        if ev.value:
            profile.mode = ev.clientData
            for propName in self.DISPLAY_PROPERTIES:
                profile.bindProps(propName, self)
        else:
            profile.mode = 'nav'
