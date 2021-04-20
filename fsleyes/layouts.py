#!/usr/bin/env python
#
# layout.py - The layout API (previously called "perspectives").
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions for managing *layouts* - stored view and
control panel layouts for *FSLeyes*. Layouts may be persisted using the
:mod:`.settings` module. A few layouts are also *built in*, and are
defined in the :attr:`BUILT_IN_LAYOUTS` dictionary.


.. note:: Prior to FSLeyes 0.24.0, *layouts* were called *perspectives*.


The ``layouts`` module provides the following functions. These are intended
for use by the :class:`.FSLeyesFrame`, but can be used in other ways too:


.. autosummary::
   :nosignatures:

   getAllLayouts
   loadLayout
   applyLayout
   saveLayout
   removeLayout
   serialiseLayout
   deserialiseLayout


A layout defines a layout for a :class:`.FSLeyesFrame`. It specifies the
type and layout of one or more *views* (defined in the :mod:`.views` module)
and, within each view, the type and layout of one or more *controls* (defined
in the :mod:`.controls` module). See the :mod:`fsleyes` documentation for
an overview of views and controls.


All of this information is stored as a string - see the
:func:`serialiseLayout` function for details on its storage format.
"""


import functools as ft
import              logging
import              pkgutil
import              textwrap
import              importlib
import              collections

import fsl.utils.settings            as fslsettings
import fsleyes_widgets.utils.status  as status
import fsleyes.strings               as strings
import fsleyes.plugins               as plugins
import fsleyes.controls              as controls
import fsleyes.views                 as views
import fsleyes.views.viewpanel       as viewpanel
import fsleyes.views.canvaspanel     as canvaspanel
import fsleyes.views.plotpanel       as plotpanel
import fsleyes.controls.controlpanel as controlpanel


log = logging.getLogger(__name__)


def getAllLayouts():
    """Returns a list containing the names of all saved layouts. The
    returned list does not include built-in layouts - these are
    accessible in the :attr:`BUILT_IN_LAYOUTS` dictionary.
    """

    layouts = fslsettings.read('fsleyes.layouts',      []) + \
              fslsettings.read('fsleyes.perspectives', [])

    uniq = []
    for l in layouts:
        if l not in uniq:
            uniq.append(l)

    return uniq


def loadLayout(frame, name, **kwargs):
    """Load the named layout, and apply it to the given
    :class:`.FSLeyesFrame`. The ``kwargs`` are passed through to the
    :func:`applyLayout` function.
    """

    if name in BUILT_IN_LAYOUTS.keys():

        log.debug('Loading built-in layout {}'.format(name))
        layout = BUILT_IN_LAYOUTS[name]

    else:
        log.debug('Loading saved layout {}'.format(name))
        layout = fslsettings.read('fsleyes.layouts.{}'.format(name), None)
        if layout is None:
            fslsettings.read('fsleyes.perspectives.{}'.format(name), None)

    if layout is None:
        raise ValueError('No layout named "{}" exists'.format(name))

    log.debug('Applying layout:\n{}'.format(layout))
    applyLayout(frame, name, layout, **kwargs)


def applyLayout(frame, name, layout, message=None):
    """Applies the given serialised layout string to the given
    :class:`.FSLeyesFrame`.

    :arg frame:   The :class:`.FSLeyesFrame` instance.
    :arg name:    The layout name.
    :arg layout:  The serialised layout string.
    :arg message: A message to display (using the :mod:`.status` module).
    """

    import fsleyes.views.canvaspanel as canvaspanel

    layout        = deserialiseLayout(layout)
    frameChildren = layout[0]
    frameLayout   = layout[1]
    vpChildrens   = layout[2]
    vpLayouts     = layout[3]
    vpPanelProps  = layout[4]
    vpSceneProps  = layout[5]

    # Show a message while re-configuring the frame
    if message is None:
        message = strings.messages[
            'layout.applyingLayout'].format(
                strings.layouts.get(name, name))

    status.update(message)

    # Clear all existing view
    # panels from the frame
    frame.removeAllViewPanels()

    # Add all of the view panels
    # specified in the layout
    for vp in frameChildren:
        log.debug('Adding view panel {} to frame'.format(vp.__name__))
        frame.addViewPanel(vp, defaultLayout=False)

    # Apply the layout to those view panels
    frame.auiManager.LoadPerspective(frameLayout)

    # For each view panel, add all of the
    # control panels, and lay them out
    viewPanels = frame.viewPanels
    for i in range(len(viewPanels)):

        vp         = viewPanels[  i]
        children   = vpChildrens[ i]
        vpLayout   = vpLayouts[   i]
        panelProps = vpPanelProps[i]
        sceneProps = vpSceneProps[i]

        for child in children:
            log.debug('Adding control panel {} to {}'.format(
                child.__name__, type(vp).__name__))
            _addControlPanel(vp, child)

        vp.auiManager.LoadPerspective(vpLayout)

        # Apply saved property values
        # to the view panel.
        for name, val in panelProps.items():
            log.debug('Setting {}.{} = {}'.format(
                type(vp).__name__, name, val))
            vp.deserialise(name, val)

        # And to its SceneOpts instance if
        # it is a CanvasPanel, or its
        # PlotCanvas if it is a PlotPanel
        if   isinstance(vp, canvaspanel.CanvasPanel): aux = vp.sceneOpts
        elif isinstance(vp, plotpanel.PlotPanel):     aux = vp.canvas

        for name, val in sceneProps.items():
            log.debug('Setting {}.{} = {}'.format(
                type(aux).__name__, name, val))
            aux.deserialise(name, val)


def saveLayout(frame, name):
    """Serialises the layout of the given :class:`.FSLeyesFrame` and saves
    it as a layout with the given name.
    """

    if name in BUILT_IN_LAYOUTS.keys():
        raise ValueError('A built-in layout named "{}" '
                         'already exists'.format(name))

    log.debug('Saving current layout with name {}'.format(name))

    layout = serialiseLayout(frame)
    fslsettings.write('fsleyes.layouts.{}'.format(name), layout)

    _addToLayoutList(name)

    log.debug('Serialised layout:\n{}'.format(layout))


def removeLayout(name):
    """Deletes the named layout. """

    log.debug('Deleting layout with name {}'.format(name))
    fslsettings.delete('fsleyes.layouts.{}'     .format(name))
    fslsettings.delete('fsleyes.perspectives.{}'.format(name))
    _removeFromLayoutList(name)


def serialiseLayout(frame):
    """Serialises the layout of the given :class:`.FSLeyesFrame`, and returns
    it as a string.

    .. note:: This function was written against wx.lib.agw.aui.AuiManager as
              it exists in wxPython 3.0.2.0.

     *FSLeyes* uses a hierarchy of ``wx.lib.agw.aui.AuiManager`` instances for
     its layout - the :class:`.FSLeyesFrame` uses an ``AuiManager`` to lay out
     :class:`.ViewPanel` instances, and each of these ``ViewPanels`` use their
     own ``AuiManager`` to lay out control panels.

     The layout for a single ``AuiManager`` can be serialised to a string via
     the ``AuiManager.SavePerspective`` and ``AuiManager.SavePaneInfo``
     methods. One of these strings consists of:

       - A name, `'layout1'` or `'layout2'`, specifying the AUI version
         (this will always be at least `'layout2'` for *FSLeyes*).

       - A set of key-value set of key-value pairs defining the top level
         panel layout.

       - A set of key-value pairs for each pane, defining its layout. the
         ``AuiManager.SavePaneInfo`` method returns this for a single pane.

     These are all encoded in a single string, with the above components
     separated with '|' characters, and the pane-level key-value pairs
     separated with a ';' character. For example:

     layout2|key1=value1|name=Pane1;caption=Pane 1|\
     name=Pane2;caption=Pane 2|doc_size(5,0,0)=22|

     This function queries each of the AuiManagers, and extracts the following:

        1. A layout string for the :class:`.FSLeyesFrame`.

        2. A string containing a comma-separated list of :class:`.ViewPanel`
           class names, in the same order as they are specified in the frame
           layout string.

        3.  For each ``ViewPanel``:

             - A layout string for the ``ViewPanel``

             - A string containing a comma-separated list of control panel
               class names, in the same order as specified in the
               ``ViewPanel`` layout string.

    Each of these pieces of information are then concatenated into a single
    newline separated string.

    In FSLeyes 0.35.0, the list of ``ViewPanel`` and ``ControlPanel`` class
    names was changed from containing just the class names
    (e.g. ``'OrthoPanel'``) to containing the fully resolved class paths
    (e.g. ``'fsleyes.views.orthopanel.OrthoPanel'``). The
    :func:`deserialiseLayout` function is compatible with both formats.
    """

    # We'll start by defining this silly function, which
    # takes an ``AuiManager`` layout string, and a list
    # of the children which are being managed by the
    # AuiManager, and makes sure that the order of the
    # child pane layout specifications in the string is
    # the same as the order of the children in the list.
    #
    # If the 'rename' argument is True, this function
    # performs an additional step.
    #
    # The FSLeyesFrame gives each of its view panels a
    # unique name of the form "ClassName index", where
    # the 'index' is a sequentially increasing identifier
    # number (so that multiple views of the same type can
    # be differentiated). If the 'rename' argument to
    # this function is True, these names are adjusted so
    # that they begin at 1 and increase sequentially. This
    # is done by the patchPanelName function, defined
    # below.
    #
    # This name adjustment is required to handle
    # situations where the indices of existing view panels
    # are not sequential, as when a layout is applied, the
    # view panel names given by the FSLeyesFrame must
    # match the names that are specified in the layout
    # string.
    #
    # In addition to patching the name of each panel,
    # the 'rename' argument will also cause the panel
    # caption (its display title) to be adjusted so that
    # it is in line with the name.
    def patchLayoutString(auiMgr, panels, rename=False):

        layoutStr = auiMgr.SavePerspective()

        # The different sections of the string
        # returned by SavePerspective are
        # separated with a '|' character.
        sections = layoutStr.split('|')
        sections = [s.strip() for s in sections]
        sections = [s for s in sections if s != '']

        # Here, we identify sections which specify
        # the layout of a child pane, remove them,
        # and patch them back in, in the order that
        # the child panels are specified in the list.
        pi = 0
        for si, s in enumerate(sections):
            if s.find('name=') > -1:
                panel        = panels[pi]
                panelInfo    = auiMgr.GetPane(panel)
                panelLayout  = auiMgr.SavePaneInfo(panelInfo)
                pi          += 1
                sections[si] = panelLayout

                if rename:
                    sections[si] = patchPanelName(sections[si], pi)

        # Now the panel layouts in our layout string
        # are in the same order as our list of view
        # panels - we can re-join the layout string
        # sections, and we're done.
        return '|'.join(sections) + '|'

    # The purpose of this function is described above.
    def patchPanelName(layoutString, index):
        # In each AUI layout section, 'key=value'
        # pairs are separated with a semi-colon
        kvps = layoutString.split(';')

        # And each 'key=value' pair is separated
        # with an equals character
        kvps = [kvp.split('=') for kvp in kvps]
        kvps = collections.OrderedDict(kvps)

        # We need to update the indices contained
        # in the 'name' and 'caption' values
        name    = kvps['name']
        caption = kvps['caption']

        # Strip off the old index
        name    = ' '.join(name   .split()[:-1])
        caption = ' '.join(caption.split()[:-1])

        # Patch in the new index
        name    = '{} {}'.format(name,    index)
        caption = '{} {}'.format(caption, index)

        kvps['name']    = name
        kvps['caption'] = caption

        # Reconstruct the layout string
        kvps = ['='.join((k, v)) for k, v in kvps.items()]
        kvps = ';'.join(kvps)

        return kvps

    # Now we can start extracting the layout information.
    # We start with the FSLeyesFrame layout.
    auiMgr     = frame.auiManager
    viewPanels = frame.viewPanels

    # Generate the frame layout string, and a
    # list of the children of the frame
    frameLayout   = patchLayoutString(auiMgr, viewPanels, True)
    frameChildren = ['.'.join((type(vp).__module__, type(vp).__qualname__))
                     for vp in viewPanels]
    frameChildren = ','.join(frameChildren)

    # We are going to build a list of layout strings,
    # one for each ViewPanel, and a corresponding list
    # of control panels displayed on each ViewPanel.
    vpLayouts = []
    vpConfigs = []

    for vp in viewPanels:

        # Get the auiManager and layout for this view panel.
        # This is a little bit complicated, as ViewPanels
        # differentiate between the main 'centre' panel, and
        # all other secondary (control) panels. The layout
        # string needs to contain layout information for
        # all of these panels, but we only care about the
        # control panels.
        vpAuiMgr    = vp.auiManager
        ctrlPanels  = vp.getPanels()
        centrePanel = vp.centrePanel

        # As above for the frame, generate a layout
        # string and a list of control panels - the
        # children of the view panel.
        vpLayout    = patchLayoutString(vpAuiMgr, [centrePanel] + ctrlPanels)
        vpChildren  = ['.'.join((type(cp).__module__, type(cp).__qualname__))
                       for cp in ctrlPanels]
        vpChildren  = ','.join(vpChildren)

        # Get the panel and scene settings
        panelProps, sceneProps = _getPanelProps(vp)

        # And turn them into comma-separated key-value pairs.
        panelProps = ['{}={}'.format(k, v) for k, v in panelProps.items()]
        sceneProps = ['{}={}'.format(k, v) for k, v in sceneProps.items()]

        panelProps = ','.join(panelProps)
        sceneProps = ','.join(sceneProps)

        # Build the config string - the children,
        # the panel settings and the scene settings.
        vpConfig = ';'.join([vpChildren, panelProps, sceneProps])

        vpLayouts.append(vpLayout)
        vpConfigs.append(vpConfig)

    # We serialise all of these pieces of information
    # as a single newline-separated string.
    layout = [frameChildren, frameLayout]
    for vpConfig, vpLayout in zip(vpConfigs, vpLayouts):
        layout.append(vpConfig)
        layout.append(vpLayout)

    # And we're done!
    return '\n'.join(layout)


def deserialiseLayout(layout):
    """Deserialises a layout string which was created by the
    :func:`serialiseLayout` string.

    :returns: A tuple containing the following:

                - A list of :class:`.ViewPanel` class types - the
                  children of the :class:`.FSLeyesFrame`.

                - An ``aui`` layout string for the :class:`.FSLeyesFrame`

                - A list of lists, one for each ``ViewPanel``, with each
                  list containing a collection of control panel class
                  types - the children of the corresponding ``ViewPanel``.

                - A list of strings, one ``aui`` layout string for each
                  ``ViewPanel``.

                - A list of dictionaries, one for each ``ViewPanel``,
                  containing property ``{name : value}`` pairs to be
                  applied to the ``ViewPanel``.

                - A list of dictionaries, one for each ``ViewPanel``,
                  containing property ``{name : value}`` pairs to be applied
                  to the :class:`.SceneOpts` instance associated with the
                  ``ViewPanel``, if it is a :class:`.CanvasPanel`, or the
                  :class:`.PlotCanvas` instance associated with the
                  ``ViewPanel``, if it is a :class:`.PlotPanel`.
    """

    # Versions of FSLeyes prior to 1.0.0 would just
    # save the view/control class name. This was
    # changed in 1.0.0 so that the full path to the
    # class is saved. This function aims to be
    # compatible with both formats - given a class
    # name, or a fully resolved class name, it will
    # return the corresponding type object.
    def findViewOrControl(panelname, paneltype):

        # new format
        if '.' in panelname:
            mod, cls = panelname.rsplit('.', maxsplit=1)
            mod      = importlib.import_module(mod)
            return getattr(mod, cls)

        # make a list of all candidate types,
        # then search through them for a match
        panels = []

        # builtins
        if paneltype == 'control':
            basemod  = controls
            basetype = (controlpanel.ControlPanel,
                        controlpanel.ControlToolBar)
        else:
            basemod  = views
            basetype = viewpanel.ViewPanel

        mods = pkgutil.iter_modules(basemod.__path__, basemod.__name__ + '.')
        for _, mod, _  in mods:
            mod = importlib.import_module(mod)
            for att in dir(mod):
                att = getattr(mod, att)
                if isinstance(att, type) and issubclass(att, basetype):
                    panels.append(att)

        # plugins
        if paneltype == 'control':
            panels.extend(plugins.listControls().values())
        else:
            panels.extend(plugins.listViews().values())

        for panel in panels:
            if panel.__name__ == panelname:
                return panel

        raise ValueError('Unknown FSLeyes panel type: {}'.format(panelname))

    findView    = ft.partial(findViewOrControl, paneltype='view')
    findControl = ft.partial(findViewOrControl, paneltype='control')

    lines = layout.split('\n')
    lines = [line.strip() for line in lines]
    lines = [line         for line in lines if line != '']

    frameChildren = lines[0]
    frameLayout   = lines[1]

    # The children strings are comma-separated
    # class names. The frame children are ViewPanels,
    # which are all defined in the fsleyes.views
    # package.
    frameChildren = frameChildren.split(',')
    frameChildren = [fc.strip()   for fc in frameChildren]
    frameChildren = [fc           for fc in frameChildren if fc != '']
    frameChildren = [findView(fc) for fc in frameChildren]

    # Collate the children/layouts for each view panel
    vpChildren   = []
    vpLayouts    = []
    vpPanelProps = []
    vpSceneProps = []

    for i in range(len(frameChildren)):

        linei = (i * 2) + 2

        config = lines[linei]
        layout = lines[linei + 1]

        children, panelProps, sceneProps = config.split(';')

        vpChildren   .append(children)
        vpLayouts    .append(layout)
        vpPanelProps .append(panelProps)
        vpSceneProps .append(sceneProps)

    # The ViewPanel children string is a comma-separated
    # list of control panel class names. All control panels
    # should be defined in the fsleyes.controls package.
    for i in range(len(vpChildren)):

        children      = vpChildren[i].split(',')
        children      = [vpc.strip()      for vpc in children]
        children      = [vpc              for vpc in children if vpc != '']
        children      = [findControl(vpc) for vpc in children]
        vpChildren[i] = children

    # The panel props and scene props strings are
    # comma-separated lists of 'prop=value' pairs.
    # We'll turn them into a dict for convenience.
    for i in range(len(vpPanelProps)):
        props           = vpPanelProps[i].split(',')
        props           = [p for p in props if p != '']
        props           = [p.split('=') for p in props]
        vpPanelProps[i] = collections.OrderedDict(props)

    for i in range(len(vpSceneProps)):
        props           = vpSceneProps[i].split(',')
        props           = [p for p in props if p != '']
        props           = [p.split('=') for p in props]
        vpSceneProps[i] = collections.OrderedDict(props)

    return (frameChildren,
            frameLayout,
            vpChildren,
            vpLayouts,
            vpPanelProps,
            vpSceneProps)


def _addToLayoutList(layout):
    """Adds the given layout name to the list of saved layouts. """

    layout  = layout.strip()
    layouts = getAllLayouts()

    if layout not in layouts:
        layouts.append(layout)

    log.debug('Updating stored layout list: {}'.format(layout))
    fslsettings.write('fsleyes.layouts', layouts)


def _removeFromLayoutList(layout):
    """Removes the given layout name from the list of saved layouts.
    """

    layouts = getAllLayouts()

    try:               layouts.remove(layout)
    except ValueError: return

    log.debug('Updating stored layout list: {}'.format(layouts))
    fslsettings.write('fsleyes.layouts', layouts)


def _addControlPanel(viewPanel, panelType):
    """Adds a control panel to the given :class:`.ViewPanel`.

    :arg viewPanel: A :class:`.ViewPanel` instance.
    :arg panelType: A control panel type.
    """
    viewPanel.togglePanel(panelType)


def _getPanelProps(panel):
    """Creates and returns two dictionaries, containing properties of the given
    :class:`.ViewPanel` (and its associated :class:`.SceneOpts` instance, if
    it is a :class:`.CanvasPanel`, or :class:`.PlotCanvas`, if it is a
    :class:`.PlotPanel`), which are to be saved as part of a seriaised
    *FSLeyes* layout. The properties to be saved are listed in the
    :data:`VIEWPANEL_PROPS` dictionary.
    """

    if not isinstance(panel, (canvaspanel.CanvasPanel, plotpanel.PlotPanel)):
        return {}, {}

    panelType              = type(panel).__name__
    panelProps, sceneProps = VIEWPANEL_PROPS[panelType]

    if isinstance(panel, canvaspanel.CanvasPanel):
        aux = panel.sceneOpts
    elif isinstance(panel, plotpanel.PlotPanel):
        aux = panel.canvas

    panelProps = {name : panel.serialise(name) for name in panelProps}
    sceneProps = {name : aux  .serialise(name) for name in sceneProps}

    return panelProps, sceneProps


VIEWPANEL_PROPS = {
    'OrthoPanel'         : [['syncLocation',
                             'syncOverlayOrder',
                             'syncOverlayDisplay',
                             'syncOverlayVolume',
                             'movieRate',
                             'movieAxis'],
                            ['showCursor',
                             'bgColour',
                             'fgColour',
                             'cursorColour',
                             'cursorGap',
                             'showColourBar',
                             'colourBarLocation',
                             'colourBarLabelSide',
                             'showXCanvas',
                             'showYCanvas',
                             'showZCanvas',
                             'showLabels',
                             'labelSize',
                             'layout',
                             'xzoom',
                             'yzoom',
                             'zzoom',
                             'highDpi']],
    'LightBoxPanel'      : [['syncLocation',
                             'syncOverlayOrder',
                             'syncOverlayDisplay',
                             'syncOverlayVolume',
                             'movieRate',
                             'movieAxis'],
                            ['showCursor',
                             'bgColour',
                             'fgColour',
                             'cursorColour',
                             'showColourBar',
                             'colourBarLocation',
                             'colourBarLabelSide',
                             'zax',
                             'showGridLines',
                             'highlightSlice',
                             'highDpi']],
    'Scene3DPanel'       : [['syncLocation',
                             'syncOverlayOrder',
                             'syncOverlayDisplay',
                             'syncOverlayVolume'],
                            ['showCursor',
                             'bgColour',
                             'fgColour',
                             'cursorColour',
                             'showColourBar',
                             'colourBarLocation',
                             'colourBarLabelSide',
                             'occlusion',
                             'light',
                             'lightPos',
                             'offset',
                             'rotation',
                             'showLegend']],
    'TimeSeriesPanel'    : [['usePixdim',
                             'plotMode',
                             'plotMelodicICs'],
                            ['legend',
                             'xAutoScale',
                             'yAutoScale',
                             'xLogScale',
                             'yLogScale',
                             'ticks',
                             'grid',
                             'gridColour',
                             'bgColour',
                             'smooth']],
    'HistogramPanel'     : [['histType',
                             'plotType'],
                            ['legend',
                             'xAutoScale',
                             'yAutoScale',
                             'xLogScale',
                             'yLogScale',
                             'ticks',
                             'grid',
                             'gridColour',
                             'bgColour',
                             'smooth']],
    'PowerSpectrumPanel' : [['plotMelodicICs',
                             'plotFrequencies'],
                            ['legend',
                             'xAutoScale',
                             'yAutoScale',
                             'xLogScale',
                             'yLogScale',
                             'ticks',
                             'grid',
                             'gridColour',
                             'bgColour',
                             'smooth']]}


# The order in which properties are defined in
# a layout is the order in which they will
# be applied. This is important to remember when
# considering properties that have side effects
# (e.g. setting SceneOpts.bgColour will clobber
# SceneOpts.fgColour).
BUILT_IN_LAYOUTS = collections.OrderedDict((
    ('default',
     textwrap.dedent("""
                     fsleyes.views.orthopanel.OrthoPanel
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     fsleyes.controls.orthotoolbar.OrthoToolBar,fsleyes.controls.overlaydisplaytoolbar.OverlayDisplayToolBar,fsleyes.controls.overlaylistpanel.OverlayListPanel,fsleyes.controls.locationpanel.LocationPanel;syncOverlayOrder=True,syncLocation=True,syncOverlayDisplay=True,movieRate=400;colourBarLocation=top,showCursor=True,bgColour=#000000ff,layout=horizontal,colourBarLabelSide=top-left,cursorGap=False,fgColour=#ffffffff,cursorColour=#00ff00ff,showXCanvas=True,showYCanvas=True,showColourBar=False,showZCanvas=True,showLabels=True
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=-1;besth=-1;minw=1;minh=1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=176|dock_size(1,10,0)=49|dock_size(1,11,0)=67|
                     """)),  # noqa

    ('melodic',
     textwrap.dedent("""
                     fsleyes.views.lightboxpanel.LightBoxPanel,fsleyes.views.timeseriespanel.TimeSeriesPanel,fsleyes.views.powerspectrumpanel.PowerSpectrumPanel
                     layout2|name=LightBoxPanel 1;caption=Lightbox View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesPanel 2;caption=Time series 2;state=67377148;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=PowerSpectrumPanel 3;caption=Power spectra 3;state=67377148;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=224|
                     fsleyes.controls.locationpanel.LocationPanel,fsleyes.controls.overlaylistpanel.OverlayListPanel,fsleyes.plugins.controls.melodicclassificationpanel.MelodicClassificationPanel,fsleyes.controls.lightboxtoolbar.LightBoxToolBar,fsleyes.controls.overlaydisplaytoolbar.OverlayDisplayToolBar;syncLocation=True,syncOverlayOrder=True,movieRate=750,syncOverlayDisplay=True;bgColour=#000000ff,fgColour=#ffffffff,showCursor=True,cursorColour=#00ff00ff,highlightSlice=False,zax=2,showColourBar=False,showGridLines=False,colourBarLocation=top
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MelodicClassificationPanel;caption=Melodic IC classification;state=67373052;dir=2;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LightBoxToolBar;caption=Lightbox view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=130|dock_size(1,10,0)=45|dock_size(1,11,0)=51|dock_size(2,0,0)=402|
                     TimeSeriesToolBar;;
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesToolBar;caption=Time series toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|dock_size(1,10,0)=36|
                     PowerSpectrumToolBar;;
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=PowerSpectrumToolBar;caption=Plot toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|dock_size(1,10,0)=36|
                     """)),  # noqa

    ('feat',
     textwrap.dedent("""
                     fsleyes.views.orthopanel.OrthoPanel,fsleyes.views.timeseriespanel.TimeSeriesPanel
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesPanel 2;caption=Time series 2;state=67377148;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=282|
                     fsleyes.controls.overlaylistpanel.OverlayListPanel,fsleyes.controls.overlaydisplaytoolbar.OverlayDisplayToolBar,fsleyes.controls.orthotoolbar.OrthoToolBar,fsleyes.controls.locationpanel.LocationPanel,fsleyes.plugins.controls.clusterpanel.ClusterPanel;syncLocation=True,syncOverlayOrder=True,movieRate=750,syncOverlayDisplay=True;layout=horizontal,showLabels=True,bgColour=#000000ff,fgColour=#ffffffff,showCursor=True,showZCanvas=True,cursorColour=#00ff00ff,showColourBar=False,showYCanvas=True,showXCanvas=True,colourBarLocation=top
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=2;row=0;pos=0;prop=87792;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=1;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=2;row=0;pos=1;prop=98544;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=ClusterPanel;caption=Cluster browser;state=67373052;dir=2;layer=1;row=0;pos=0;prop=114760;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=10|dock_size(2,1,0)=566|dock_size(1,10,0)=51|dock_size(1,10,1)=36|dock_size(3,2,0)=130|
                     OverlayListPanel,TimeSeriesToolBar;;
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=4;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesToolBar;caption=Time series toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|dock_size(1,10,0)=36|dock_size(4,0,0)=206|
                     """)),  # noqa

    ('ortho',
     textwrap.dedent("""
                     fsleyes.views.orthopanel.OrthoPanel
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     ;syncLocation=True,syncOverlayOrder=True,syncOverlayDisplay=True;layout=horizontal,showLabels=True,bgColour=#000000ff,fgColour=#ffffffff,showCursor=True,showZCanvas=True,cursorColour=#00ff00ff,showColourBar=False,showYCanvas=True,showXCanvas=True,colourBarLocation=top
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     """)),  # noqa
    ('3d',
     textwrap.dedent("""
                     fsleyes.views.scene3dpanel.Scene3DPanel
                     layout2|name=Scene3DPanel 1;caption=3D View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=24|
                     ;syncOverlayOrder=True,syncOverlayDisplay=True,syncLocation=True;showColourBar=False,showLegend=True,cursorColour=#00ff00ff,colourBarLocation=top,showCursor=True,colourBarLabelSide=top-left,bgColour=#9999c0ff,fgColour=#00ff00ff
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     """)),  # noqa

    ('lightbox',
     textwrap.dedent("""
                     fsleyes.views.lightboxpanel.LightBoxPanel
                     layout2|name=LightBoxPanel 1;caption=Lightbox View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     ;syncLocation=True,syncOverlayOrder=True,syncOverlayDisplay=True;bgColour=#000000ff,fgColour=#ffffffff,showCursor=True,cursorColour=#00ff00ff,highlightSlice=False,zax=2,showColourBar=False,showGridLines=False,colourBarLocation=top
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=10|
                     """))))  # noqa
