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
import fsleyes.actions                               as actions
import fsleyes.strings                               as strings
import fsleyes.icons                                 as fslicons
import fsleyes.tooltips                              as tooltips
import fsleyes.views.orthopanel                      as orthopanel
import fsleyes.controls.controlpanel                 as ctrlpanel
import fsleyes.plugins.profiles.orthoannotateprofile as annotprofile
import fsleyes.plugins.tools.saveannotations         as saveannotations
import fsleyes.gl.annotations                        as annotations


class AnnotationPanel(ctrlpanel.ControlPanel):
    """The ``AnnotationPanel`` contains controls allowing the user to add
    annotations to the canvases in an :class:`.OrthoPanel`. The user is able
    to add points, lines, rectangles, ellipses, and text to any canvas, and
    can adjust the properties (e.g. colour, thickness) of each annotation.

    When a user selects an annotation to add, the
    :class:`.OrthoAnnotateProfile` is enabled on the ``OrthoPanel``, which
    provides user interaction.

    The :class:`.SaveAnnotationsAction` and :class:`.LoadAnnotationsAction`
    actions, for saving/loading annotations to/from files, are bound to
    buttons in the ``AnnotationPanel``.
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

        # load/save actions are bound to buttons below
        self.loadAnnotations = saveannotations.LoadAnnotationsAction(
            overlayList, displayCtx, ortho)
        self.saveAnnotations = saveannotations.SaveAnnotationsAction(
            overlayList, displayCtx, ortho)

        # The interface comprises a list of annotations,
        # a set of controls below the list, a column of
        # buttons down the side, and a row of buttons
        # along the bottom
        self.__mainSizer       = wx.BoxSizer(wx.VERTICAL)
        self.__listSizer       = wx.BoxSizer(wx.HORIZONTAL)
        self.__sideButtonSizer = wx.BoxSizer(wx.VERTICAL)

        # Listbox containing all annotations that
        # have been added to all canvases, sorted
        # by creation time. We add our own buttons
        # to remove/reorder anontations below
        self.__annotList = elb.EditableListBox(
            self, style=(elb.ELB_NO_ADD    |
                         elb.ELB_NO_REMOVE |
                         elb.ELB_NO_MOVE   |
                         elb.ELB_REVERSE))

        # Buttons running down the side of the list,
        # for loading/saving annotations, and for
        # removing/reordering annotations from/within
        # the list
        loadSpec = actions.ActionButton(
            'loadAnnotations',
            icon=fslicons.findImageFile('folder16'),
            tooltip=tooltips.actions[self, 'saveAnnotations'])
        saveSpec = actions.ActionButton(
            'saveAnnotations',
            icon=fslicons.findImageFile('floppydisk16'),
            tooltip=tooltips.actions[self, 'loadAnnotations'])

        self.__loadButton   = props.buildGUI(self, self, loadSpec)
        self.__saveButton   = props.buildGUI(self, self, saveSpec)
        self.__upButton     = wx.Button(self, style=wx.BU_EXACTFIT)
        self.__downButton   = wx.Button(self, style=wx.BU_EXACTFIT)
        self.__removeButton = wx.Button(self, style=wx.BU_EXACTFIT)

        upicon     = wx.Bitmap(fslicons.findImageFile('up16'))
        downicon   = wx.Bitmap(fslicons.findImageFile('down16'))
        removeicon = wx.Bitmap(fslicons.findImageFile('remove16'))

        self.__upButton    .SetBitmapLabel(upicon)
        self.__downButton  .SetBitmapLabel(downicon)
        self.__removeButton.SetBitmapLabel(removeicon)

        self.__sideButtonSizer.Add(self.__loadButton)
        self.__sideButtonSizer.Add(self.__saveButton)
        self.__sideButtonSizer.Add(self.__upButton)
        self.__sideButtonSizer.Add(self.__downButton)
        self.__sideButtonSizer.Add(self.__removeButton)
        self.__sideButtonSizer.Add((1, 1), proportion=1)

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

        self.__listSizer.Add(self.__sideButtonSizer)
        self.__listSizer.Add(self.__annotList, flag=wx.EXPAND, proportion=1)

        self.__mainSizer.Add(self.__listSizer,    flag=wx.EXPAND, proportion=1)
        self.__mainSizer.Add(self.__widgets,      flag=wx.EXPAND)
        self.__mainSizer.Add(self.__annotOptions, flag=wx.EXPAND)

        self.SetSizer(self.__mainSizer)

        self.__upButton    .Bind(wx.EVT_BUTTON, self.__onMoveUp)
        self.__downButton  .Bind(wx.EVT_BUTTON, self.__onMoveDown)
        self.__removeButton.Bind(wx.EVT_BUTTON, self.__onRemove)

        self.__annotOptions.Bind(bmpradio.EVT_BITMAP_RADIO_EVENT,
                                 self.__onAnnotOption)

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

        # This is a little awkward. Each XYZ canvas has its own
        # separate list of annotation objects, but we display
        # all objects in a single list, and the user is able to
        # arbitrarily re-order the objects, independently of
        # which canvas they are from (even though reordering
        # two objects from different canvases has no effect on
        # how they are drawn).
        #
        # The __onMove method keeps the ordering of the GUI list
        # and canvas lists in sync. But this method (which is
        # typically called when new annotations are added) just
        # clears and re-creates the GUI list from the canvas
        # lists. This keeps the code simple, but does mean that
        # new annotations will appear after the last annotation
        # *from the same canvas*, meaning that they may appear
        # in the middle of the GUI list.
        alist     = self.__annotList
        allAnnots = []
        for canvas in self.__ortho.getGLCanvases():
            allAnnots.extend(canvas.getAnnotations().annotations)

        listAnnots = alist.GetData()
        alist.Clear()

        for obj in allAnnots:
            canvas = 'XYZ'[obj.annot.canvas.opts.zax]
            if isinstance(obj, annotations.TextAnnotation):
                name = obj.text
            else:
                name = strings.labels[self, obj]
            alist.Append('[{}] {}'.format(canvas, name), obj)

        # select the most recently added annotation
        # (we just take the first one which was not
        # originally in the GUI list) and bind it
        # to the display settings widgets
        for i, obj in enumerate(allAnnots):
            if obj not in listAnnots:
                alist.SetSelection(i)
                self.__annotListItemSelected(obj=obj)
                break


    def __displayPropertyChanged(self, *a):
        """Called when any display property changes. Refreshes all canvases.
        """
        if self.__selected is not None:
            self.__ortho.Refresh()


    def __onRemove(self, ev):
        """Called when the "remove item" button is pushed.  Removes the
        item from the list box widget, and from the corresponding
        :attr:`.Annotations.annotations` list.
        """

        idx = self.__annotList.GetSelection()
        if idx == wx.NOT_FOUND:
            return

        obj   = self.__annotList.GetItemData(idx)
        annot = obj.annot

        self.__annotList.Delete(idx)

        with props.suppress(annot, 'annotations'):
            annot.dequeue(obj, hold=True, fixed=False)

        obj.annot.canvas.Refresh()

        if self.__annotList.GetCount() > 0:
            self.__annotListItemSelected(idx - 1)


    def __onMoveUp(self, ev):
        """Called when the "move item up" button is pushed. """
        self.__onMove(-1)


    def __onMoveDown(self, ev):
        """Called when the "move item down" button is pushed. """
        self.__onMove(1)


    def __onMove(self, offset):
        """Called when one of the move buttons is pushed. Moves the item in the
        list box, then syncs the new item order on the corresponding
        :attr:`.Annotations.annotations` list.
        """
        alist = self.__annotList
        idx   = alist.GetSelection()

        if idx == wx.NOT_FOUND:
            return

        obj   = alist.GetItemData(idx)
        annot = obj.annot

        alist.MoveItem(offset)

        # Sync the order of the canvas annotations
        # list with the new order in the GUI list
        with props.suppress(annot, 'annotations'):
            allobjs = [o for o in alist.GetData() if o.annot is annot]
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
