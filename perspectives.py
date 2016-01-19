#!/usr/bin/env python
#
# perspectives.py - The perspectives API.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions for managing *perspectives* - stored view
and control panel layouts for *FSLeyes*. Perspectives are persisted using the
:mod:`.settings` module. A few perspectives are also *built in*, and are
defined in the :attr:`BUILT_IN_PERSPECTIVES` dictionary.


The ``perspectives`` module provides the following functions. These are
intended for use by the :class:`.FSLEyesFrame`, but can be used in other ways
too:


.. autosummary::
   :nosignatures:

   getAllPerspectives
   loadPerspective
   applyPerspective
   savePerspective
   removePerspective
   serialisePerspective
   deserialisePerspective


A perspective defines a layout for a :class:`.FSLEyesFrame`. It specifies the
type and layout of one or more *views* (defined in the :mod:`.views` module)
and, within each view, the type and layout of one or more *controls* (defined
in the :mod:`.controls` module). See the :mod:`.fsleyes` documentation for an
overview of views and controls.


All of this information is stored as a string - see the
:func:`serialisePerspective` function for details on its storage format.
"""


import logging
import textwrap
import collections

import fsl.utils.settings   as fslsettings
import fsl.utils.status     as status
import fsl.data.strings     as strings


log = logging.getLogger(__name__)


def getAllPerspectives():
    """Returns a list containing the names of all saved perspectives. """
    
    # A list of all saved perspective names
    # is saved as a comma-separated string
    perspectives = fslsettings.read('fsleyes.perspectives', '')
    perspectives = perspectives.split(',')
    perspectives = [p.strip() for p in perspectives]
    perspectives = [p         for p in perspectives if p != '']

    uniq = []
    for p in perspectives:
        if p not in uniq:
            uniq.append(p)
    
    return uniq


def loadPerspective(frame, name, **kwargs):
    """Load the named perspective, and apply it to the given
    :class:`.FSLEyesFrame`. The ``kwargs`` are passed through to the
    :func:`applyPerspective` function.
    """

    if name in BUILT_IN_PERSPECTIVES.keys():
        
        log.debug('Loading built-in perspective {}'.format(name))
        persp = BUILT_IN_PERSPECTIVES[name]
        
    else:
        log.debug('Loading saved perspective {}'.format(name))
        persp = fslsettings.read('fsleyes.perspectives.{}'.format(name), None)

    if persp is None:
        raise ValueError('No perspective named "{}" exists'.format(name))

    log.debug('Serialised perspective:\n{}'.format(persp))
    applyPerspective(frame, name, persp, **kwargs)


def applyPerspective(frame, name, perspective, message=None):
    """Applies the given serialised perspective string to the given
    :class:`.FSLEyesFrame`.

    :arg frame:       The :class:`.FSLEyesFrame` instance.
    :arg name:        The perspective name.
    :arg perspective: The serialised perspective string.
    :arg message:     A message to display (using the :mod:`.status` module).
    """

    import fsl.fsleyes.views as views
              
    persp         = deserialisePerspective(perspective)
    frameChildren = persp[0]
    frameLayout   = persp[1]
    vpChildrens   = persp[2]
    vpLayouts     = persp[3]
    vpPanelProps  = persp[4]
    vpSceneProps  = persp[5]

    # Show a message while re-configuring the frame
    if message is None:
        message = strings.messages[
            'perspectives.applyingPerspective'].format(
                strings.perspectives.get(name, name))
            
    status.update(message)

    # Clear all existing view
    # panels from the frame
    for vp in frame.getViewPanels():
        frame.removeViewPanel(vp)

    # Add all of the view panels
    # specified in the perspective
    for vp in frameChildren:
        log.debug('Adding view panel {} to frame'.format(vp.__name__))
        frame.addViewPanel(vp)

    # Apply the layout to those view panels
    frame.getAuiManager().LoadPerspective(frameLayout)

    # For each view panel, add all of the
    # control panels, and lay them out
    viewPanels = frame.getViewPanels()
    for i in range(len(viewPanels)):

        vp         = viewPanels[  i]
        children   = vpChildrens[ i]
        layout     = vpLayouts[   i]
        panelProps = vpPanelProps[i]
        sceneProps = vpSceneProps[i]
        
        for child in children:
            log.debug('Adding control panel {} to {}'.format(
                child.__name__, type(vp).__name__))
            _addControlPanel(vp, child)
            
        vp.getAuiManager().LoadPerspective(layout)

        # Apply saved property values
        # to the view panel.
        for name, val in panelProps.items():
            log.debug('Setting {}.{} = {}'.format(
                type(vp).__name__, name, val))
            vp.deserialise(name, val)

        # And, if it is a CanvasPanel,
        # to its SceneOpts instance.
        if isinstance(vp, views.CanvasPanel):
            opts = vp.getSceneOptions()
            for name, val in sceneProps.items():
                log.debug('Setting {}.{} = {}'.format(
                    type(opts).__name__, name, val))
                opts.deserialise(name, val)

            
def savePerspective(frame, name):
    """Serialises the layout of the given :class:`.FSLEyesFrame` and saves
    it as a perspective with the given name.
    """

    if name in BUILT_IN_PERSPECTIVES.keys():
        raise ValueError('A built-in perspective named "{}" '
                         'already exists'.format(name))
    
    log.debug('Saving current perspective with name {}'.format(name))
    
    persp = serialisePerspective(frame)
    fslsettings.write('fsleyes.perspectives.{}'.format(name), persp)

    _addToPerspectivesList(name)

    log.debug('Serialised perspective:\n{}'.format(persp))

    
def removePerspective(name):
    """Deletes the named perspective. """
    
    log.debug('Deleting perspective with name {}'.format(name))
    fslsettings.delete('fsleyes.perspectives.{}'.format(name))
    _removeFromPerspectivesList(name)

    
def serialisePerspective(frame):
    """Serialises the layout of the given :class:`.FSLEyesFrame`, and returns
    it as a string.
    
    .. note:: This function was written against wx.lib.agw.aui.AuiManager as
              it exists in wxPython 3.0.2.0.
    
     *FSLeyes* uses a hierarchy of ``wx.lib.agw.aui.AuiManager`` instances for
     its layout - the :class:`.FSLEyesFrame` uses an ``AuiManager`` to lay out
     :class:`.ViewPanel` instances, and each of these ``ViewPanels`` use their
     own ``AuiManager`` to lay out control panels.

     The layout for a single ``AuiManager`` can be serialised to a string via
     the ``AuiManager.SavePerspective`` and ``AuiManager.SavePaneInfo``
     methods. One of these strings consists of:
    
       - A name.
    
       - A set of key-value set of key-value pairs defining the top level
         panel layout.
    
       - A set of key-value pairs for each pane, defining its layout. the
         ``AuiManager.SavePaneInfo`` method returns this for a single pane.
     
     These are all encoded in a single string, with the above components
     separated with '|' characters, and the pane-level key-value pairs
     separated with a ';' character. For example:
    
     layoutName|key1=value1|name=Pane1;caption=Pane 1|\
     name=Pane2;caption=Pane 2|doc_size(5,0,0)=22|
    
     This function queries each of the AuiManagers, and extracts the following:
     
        - A layout string for the :class:`.FSLEyesFrame`.
    
        - A string containing a comma-separated list of :class:`.ViewPanel`
          class names, in the same order as they are specified in the frame
          layout string.
    
        - For each ``ViewPanel``:
    
           - A layout string for the ``ViewPanel``
    
           - A string containing a comma-separated list of control panel class
             names, in the same order as specified in the ``ViewPanel`` layout
             string.

    Each of these pieces of information are then concatenated into a single
    newline separated string.
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
    # The FSLEyesFrame gives each of its view panels a
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
    # view panel names given by the FSLEyesFrame must
    # match the names that are specified in the layout
    # perspective string.
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
    # We start with the FSLEyesFrame layout.
    auiMgr     = frame.getAuiManager()
    viewPanels = frame.getViewPanels()

    # Generate the frame layout string, and a
    # list of the children of the frame
    frameLayout   = patchLayoutString(auiMgr, viewPanels, True)
    frameChildren = [type(vp).__name__ for vp in viewPanels]
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
        vpAuiMgr    = vp.getAuiManager()
        ctrlPanels  = vp.getPanels()
        centrePanel = vp.getCentrePanel()

        # As above for the frame, generate a layout
        # string and a list of control panels - the
        # children of the view panel.
        vpLayout    = patchLayoutString(vpAuiMgr, [centrePanel] + ctrlPanels)
        vpChildren  = [type(cp).__name__ for cp in ctrlPanels]
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
    perspective = [frameChildren, frameLayout]
    for vpConfig, vpLayout in zip(vpConfigs, vpLayouts):
        perspective.append(vpConfig)
        perspective.append(vpLayout)

    # And we're done!
    return '\n'.join(perspective)


def deserialisePerspective(persp):
    """Deserialises a perspective string which was created by the
    :func:`serialisePerspective` string.

    :returns: A tuple containing the following:

                - A list of :class:`.ViewPanel` class types - the
                  children of the :class:`.FSLEyesFrame`.
    
                - An ``aui`` layout string for the :class:`.FSLEyesFrame`
   
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
                  ``ViewPanel``. If the ``ViewPanel`` is not a
                  :class:`.CanvasPanel`, the dictionary will be empty.
    """

    import fsl.fsleyes.views    as views
    import fsl.fsleyes.controls as controls
    
    lines = persp.split('\n')
    lines = [l.strip() for l in lines]
    lines = [l         for l in lines if l != '']

    frameChildren = lines[0]
    frameLayout   = lines[1]

    # The children strings are comma-separated
    # class names. The frame children are ViewPanels,
    # which are all defined in the fsl.fsleyes.views
    # package.
    frameChildren = frameChildren.split(',')
    frameChildren = [fc.strip() for fc in frameChildren]
    frameChildren = [fc         for fc in frameChildren if fc != '']
    frameChildren = [getattr(views, fc) for fc in frameChildren]

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
    # should be defined in the fsl.fsleyes.controls package.
    for i in range(len(vpChildren)):

        children      = vpChildren[i].split(',')
        children      = [vpc.strip() for vpc in children]
        children      = [vpc         for vpc in children if vpc != '']
        children      = [getattr(controls, vpc) for vpc in children]
        vpChildren[i] = children

    # The panel props and scene props strings are
    # comma-separated lists of 'prop=value' pairs.
    # We'll turn them into a dict for convenience.
    for i in range(len(vpPanelProps)):
        props           = vpPanelProps[i].split(',')
        props           = [p for p in props if p != '']
        props           = [p.split('=') for p in props]
        vpPanelProps[i] = dict(props)

    for i in range(len(vpSceneProps)):
        props           = vpSceneProps[i].split(',')
        props           = [p for p in props if p != '']
        props           = [p.split('=') for p in props]
        vpSceneProps[i] = dict(props)
        

    return (frameChildren,
            frameLayout,
            vpChildren,
            vpLayouts,
            vpPanelProps,
            vpSceneProps)


def _addToPerspectivesList(persp):
    """Adds the given perspective name to the list of saved perspectives. """
    perspectives = getAllPerspectives()

    if persp not in perspectives:
        perspectives.append(persp)

    perspectives = ','.join(perspectives)

    log.debug('Updating stored perspective list: {}'.format(perspectives))
    fslsettings.write('fsleyes.perspectives', perspectives)


def _removeFromPerspectivesList(persp):
    """Removes the given perspective name from the list of saved perspectives.
    """
    
    perspectives = getAllPerspectives()

    try:               perspectives.remove(persp)
    except ValueError: return

    perspectives = ','.join(perspectives)

    log.debug('Updating stored perspective list: {}'.format(perspectives))
    fslsettings.write('fsleyes.perspectives', perspectives) 


def _addControlPanel(viewPanel, panelType):
    """Adds a control panel to the given :class:`.ViewPanel`.

    :arg viewPanel: A :class:`.ViewPanel` instance.
    :arg panelType: A control panel type.
    """
    import fsl.fsleyes.controls as controls

    args = {
        controls.CanvasSettingsPanel       : {'canvasPanel' : viewPanel},
        controls.HistogramControlPanel     : {'plotPanel'   : viewPanel},
        controls.LightBoxToolBar           : {'lb'          : viewPanel},
        controls.OrthoEditToolBar          : {'ortho'       : viewPanel},
        controls.OrthoToolBar              : {'ortho'       : viewPanel},
        controls.OverlayDisplayToolBar     : {'viewPanel'   : viewPanel},
        controls.PlotListPanel             : {'plotPanel'   : viewPanel},
        controls.PowerSpectrumControlPanel : {'plotPanel'   : viewPanel},
        controls.ShellPanel                : {'canvasPanel' : viewPanel},
        controls.TimeSeriesControlPanel    : {'plotPanel'   : viewPanel},
    }

    args = args.get(panelType, {})

    viewPanel.togglePanel(panelType, **args)


def _getPanelProps(panel):
    """
    """

    import fsl.fsleyes.views as views

    if not isinstance(panel, views.CanvasPanel):
        return {}, {}

    panelType = type(panel).__name__
    opts      = panel.getSceneOptions()
    
    panelProps, sceneProps = VIEWPANEL_PROPS[panelType]

    panelProps = {name : panel.serialise(name) for name in panelProps}
    sceneProps = {name : opts .serialise(name) for name in sceneProps}

    return panelProps, sceneProps
    

VIEWPANEL_PROPS = {
    'OrthoPanel'    : [['syncLocation',  'syncOverlayOrder',  'syncOverlayDisplay'],
                       ['showCursor',    'bgColour',          'cursorColour',
                        'showColourBar', 'colourBarLocation', 'showXCanvas',
                        'showYCanvas',   'showZCanvas',       'showLabels',
                        'layout']
                       ],
    'LightBoxPanel' : [['syncLocation',  'syncOverlayOrder',  'syncOverlayDisplay'],
                       ['showCursor',    'bgColour',          'cursorColour',
                        'showColourBar', 'colourBarLocation', 'zax',
                        'showGridLines', 'highlightSlice']]}

    
BUILT_IN_PERSPECTIVES = collections.OrderedDict((
    ('default',
     textwrap.dedent("""
                     OrthoPanel
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     OverlayDisplayToolBar,OrthoToolBar,LocationPanel,OverlayListPanel;syncLocation=True,syncOverlayOrder=True,syncOverlayDisplay=True;layout=grid,showLabels=True,bgColour=#000000ff,showCursor=True,showZCanvas=True,cursorColour=#00ff00ff,showColourBar=False,showYCanvas=True,showXCanvas=True,colourBarLocation=top
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=855;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=748;besth=34;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=440;besth=111;minw=440;minh=109;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=440;floath=127;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=204;besth=80;minw=197;minh=80;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=204;floath=96;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=130|dock_size(1,10,0)=36|dock_size(1,11,0)=51|
                     """)),

    ('melodic',
     textwrap.dedent("""
                     LightBoxPanel,TimeSeriesPanel,PowerSpectrumPanel
                     layout2|name=LightBoxPanel 1;caption=Lightbox View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=853;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesPanel 2;caption=Time series 2;state=67377148;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=472;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=PowerSpectrumPanel 3;caption=Power spectra 3;state=67377148;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=-1;besth=472;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=195|
                     OverlayListPanel,OverlayDisplayToolBar,LocationPanel,LightBoxToolBar,MelodicClassificationPanel;;
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=204;besth=80;minw=197;minh=80;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=204;floath=96;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=810;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=440;besth=111;minw=440;minh=109;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=440;floath=127;notebookid=-1;transparent=255|name=LightBoxToolBar;caption=Lightbox view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=753;besth=43;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=MelodicClassificationPanel;caption=Melodic IC classification;state=67373052;dir=2;layer=0;row=0;pos=0;prop=100000;bestw=400;besth=100;minw=400;minh=100;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=400;floath=116;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=130|dock_size(1,10,0)=45|dock_size(1,11,0)=51|dock_size(2,0,0)=402|
                     ;;
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|
                     ;;
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|'
                     """)),

    ('feat',
     textwrap.dedent("""
                     OrthoPanel,TimeSeriesPanel,
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=853;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesPanel 2;caption=Time series 2;state=67377148;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=472;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=261|
                     OverlayDisplayToolBar,LocationPanel,AtlasPanel,OverlayListPanel,OrthoToolBar,ClusterPanel;;
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=860;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=2;row=0;pos=1;prop=98544;bestw=440;besth=109;minw=440;minh=109;maxw=-1;maxh=-1;floatx=2730;floaty=1104;floatw=440;floath=125;notebookid=-1;transparent=255|name=AtlasPanel;caption=Atlases;state=67373052;dir=2;layer=1;row=0;pos=0;prop=98904;bestw=318;besth=84;minw=318;minh=84;maxw=-1;maxh=-1;floatx=1091;floaty=143;floatw=318;floath=100;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=2;row=0;pos=0;prop=87792;bestw=197;besth=80;minw=197;minh=80;maxw=-1;maxh=-1;floatx=2608;floaty=1116;floatw=197;floath=96;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=1;pos=0;prop=100000;bestw=815;besth=34;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=2072;floaty=80;floatw=824;floath=50;notebookid=-1;transparent=255|name=ClusterPanel;caption=Cluster browser;state=67373052;dir=2;layer=1;row=0;pos=1;prop=114760;bestw=390;besth=96;minw=390;minh=96;maxw=-1;maxh=-1;floatx=3516;floaty=636;floatw=390;floath=112;notebookid=-1;transparent=255|dock_size(5,0,0)=10|dock_size(2,1,0)=566|dock_size(1,10,0)=51|dock_size(1,10,1)=36|dock_size(3,2,0)=130|
                     ;;
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|
                     """)),

    ('ortho',
     textwrap.dedent("""
                     OrthoPanel
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     ;syncLocation=True,syncOverlayOrder=True,syncOverlayDisplay=True;layout=horizontal,showLabels=True,bgColour=#000000ff,showCursor=True,showZCanvas=True,cursorColour=#00ff00ff,showColourBar=False,showYCanvas=True,showXCanvas=True,colourBarLocation=top
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     """)),
    ('lightbox',
     textwrap.dedent("""
                     LightBoxPanel
                     layout2|name=LightBoxPanel 1;caption=Lightbox View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     ;syncLocation=True,syncOverlayOrder=True,syncOverlayDisplay=True;bgColour=#000000ff,showCursor=True,cursorColour=#00ff00ff,highlightSlice=False,zax=0,showColourBar=False,showGridLines=False,colourBarLocation=top
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=10|
                     """))))
