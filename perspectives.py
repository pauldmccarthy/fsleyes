#!/usr/bin/env python
#
# perspectives.py - The perspectives API.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions for managing *perspectives*, view and
control panel layouts for *FSLeyes*.

.. autosummary::
   :nosignatures:

   getAllPerspectives
   loadPerspective
   applyPerspective
   savePerspective
   removePerspective
   serialisePerspective
   deserialisePerspective
"""


import logging
import textwrap
import collections

import fsl.utils.settings   as fslsettings
import fsl.utils.dialog     as fsldlg
import fsl.data.strings     as strings


log = logging.getLogger(__name__)


def getAllPerspectives():
    """
    """
    
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
    """
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


def applyPerspective(frame, name, perspective, showMessage=True, message=None):
    """
    """
              
    persp = deserialisePerspective(perspective)
    frameChildren, frameLayout, vpChildrens, vpLayouts = persp

    # Show a message while re-configuring the frame

    if showMessage:
        if message is None:
            message = strings.messages[
                'perspectives.applyingPerspective'].format(
                    strings.perspectives.get(name, name))
            
        dlg = fsldlg.SimpleMessageDialog(frame, message)
        dlg.Show()

    # Clear all existing view
    # panels from the frame
    for vp in frame.getViewPanels():
        frame.removeViewPanel(vp)

    # Add all of the view panels
    # specified in the perspective
    for vp in frameChildren:
        frame.addViewPanel(vp)

    # Apply the layout to those view panels
    frame.getAuiManager().LoadPerspective(frameLayout)

    # For each view panel, add all of the
    # control panels, and lay them out
    viewPanels = frame.getViewPanels()
    for vp, vpChildren, vpLayout in zip(viewPanels, vpChildrens, vpLayouts):
        
        for child in vpChildren:
            _addControlPanel(vp, child)
            
        vp.getAuiManager().LoadPerspective(vpLayout)

    if showMessage:
        dlg.Close()
        dlg.Destroy()

            
def savePerspective(frame, name):
    """
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
    """
    """
    log.debug('Deleting perspective with name {}'.format(name))

    fslsettings.delete('fsleyes.perspectives.{}'.format(name))
    _removeFromPerspectivesList(name)

    
def serialisePerspective(frame):
    """
    """

    # Written against wx.lib.agw.aui.AuiManager as it
    # exists in wxPython 3.0.2.0.
    #
    # FSLEyes uses a hierarchy of AuiManager instances
    # for its layout - the FSLEyesFrame uses an AuiManager
    # to lay out ViewPanel instances, and each of these
    # ViewPanels use their own AuiManager to lay out
    # control panels. The layout for a single AuiManager
    # can be serialised to a string via the
    # AuiManager.SavePerspective and AuiManager.SavePaneInfo
    # methods.
    #
    # An Aui perspective string consists of:
    #   - A name.
    #
    #   - A set of key-value set of key-value pairs defining
    #     the top level panel layout.
    #
    #   - A set of key-value pairs for each pane,
    #     defining its layout. the AuiManager.SavePaneInfo
    #     method returns this for a single pane.
    # 
    # These are all encoded in a single string, with
    # the above components separated with '|'
    # characters, and the pane-level key-value pairs
    # separated with a ';' character. For example:
    #
    # layoutName|key1=value1|name=Pane1;caption=Pane 1|\
    # name=Pane2;caption=Pane 2|doc_size(5,0,0)=22|
    #
    # The following code is going to query each of the
    # AuiManagers, and extract the following:
    # 
    #    - A layout string for the FSLEyesFrame
    #
    #    - A string containing a comma-separated list of
    #      ViewPanels (class names, in the same order as
    #      they are specified in the frame layout string)
    #
    #    - For each ViewPanel:
    #
    #       - A layout string for the ViewPanel
    #       - A string containing a comma-separated list
    #         of ControlPanels (class names, in the same
    #         order as specified in the ViewPanel layout
    #         string)
    #
    # 
    # We'll start by defining this silly function, which
    # takes an ``AuiManager`` layout string, and a list
    # of the children which are being managed by the
    # AuiManager, and makes sure that the order of the
    # child pane layout specifications in the string is
    # the same as the order of the children in the list.
    def patchLayoutString(auiMgr, panels):

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

        # Now the panel layouts in our layout string
        # are in the same order as our list of view
        # panels - we can re-join the layout string
        # sections, and we're done.
        return '|'.join(sections) + '|'

    # Now we can start extracting the layout information.
    # We start with the FSLEyesFrame layout.
    auiMgr     = frame.getAuiManager()
    viewPanels = frame.getViewPanels()

    # Generate the frame layout string, and a
    # list of the children of the frame
    frameLayout   = patchLayoutString(auiMgr, viewPanels)
    frameChildren = [type(vp).__name__ for vp in viewPanels]
    frameChildren = ','.join(frameChildren) + ','

    # We are going to build a list of layout strings,
    # one for each ViewPanel, and a corresponding list
    # of control panels displayed on each ViewPanel.
    vpLayouts   = [] 
    vpChildrens = []

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

        # The process is now identical to that used
        # for the frame layout and children, above.
        vpLayout    = patchLayoutString(vpAuiMgr, [centrePanel] + ctrlPanels)
        vpChildren  = [type(cp).__name__ for cp in ctrlPanels]
        vpChildren  = ','.join(vpChildren) + ','

        vpLayouts  .append(vpLayout)
        vpChildrens.append(vpChildren)

    # We serialise all of these pieces of information
    # as a single newline-separated string.
    perspective = [frameChildren, frameLayout]
    for vpChildren, vpLayout in zip(vpChildrens, vpLayouts):
        perspective.append(vpChildren)
        perspective.append(vpLayout)

    # And we're done!
    return '\n'.join(perspective)


def deserialisePerspective(persp):
    """
    """

    import fsl.fsleyes.views    as views
    import fsl.fsleyes.controls as controls
    
    # This function deserialises a string which was
    # generated by the serialisePerspective function.
    # It returns:
    # 
    #  - A list of ViewPanel class types - the
    #    children of the FSLEyesFrame.
    # 
    #  - A layout string for the FSLEyesFrame.
    # 
    #  - A list of lists, each inner list containing
    #    a collection of ControlPanel class types -
    #    the children of the corresponding ViewPanel.
    # 
    #  - A list of layout strings, one for each
    #    ViewPanel.
    
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
    vpChildren = []
    vpLayouts  = []
    for i in range(2, len(frameChildren) + 2, 2):
        vpChildren.append(lines[i]) 
        vpLayouts .append(lines[i + 1])

    # And the ViewPanel children are control panels,
    # all defined in the fsl.fsleyes.controls package.
    for i in range(len(vpChildren)):

        vpChildren[i] = vpChildren[i].split(',')
        vpChildren[i] = [vpc.strip() for vpc in vpChildren[i]]
        vpChildren[i] = [vpc         for vpc in vpChildren[i] if vpc != ''] 
        vpChildren[i] = [getattr(controls, vpc) for vpc in vpChildren[i]]

    return frameChildren, frameLayout, vpChildren, vpLayouts


def _addToPerspectivesList(persp):
    """
    """
    perspectives = getAllPerspectives()

    if persp not in perspectives:
        perspectives.append(persp)

    perspectives = ','.join(perspectives)

    log.debug('Updating stored perspective list: {}'.format(perspectives))
    fslsettings.write('fsleyes.perspectives', perspectives)


def _removeFromPerspectivesList(persp):
    """
    """
    
    perspectives = getAllPerspectives()

    try:               perspectives.remove(persp)
    except ValueError: return

    perspectives = ','.join(perspectives)

    log.debug('Updating stored perspective list: {}'.format(perspectives))
    fslsettings.write('fsleyes.perspectives', perspectives) 


def _addControlPanel(viewPanel, panelType):
    """
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

    
BUILT_IN_PERSPECTIVES = collections.OrderedDict((
    ('default',
     textwrap.dedent("""
                     OrthoPanel,
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67376064;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|
                     LocationPanel,OverlayListPanel,OverlayDisplayToolBar,OrthoToolBar,
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=440;besth=109;minw=440;minh=109;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=440;floath=125;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=197;besth=80;minw=197;minh=80;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=197;floath=96;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=860;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=755;besth=34;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=130|dock_size(1,10,0)=36|dock_size(1,11,0)=51|
                     """)),

    ('melodic',
     textwrap.dedent("""
                     LightBoxPanel,TimeSeriesPanel,PowerSpectrumPanel,
                     layout2|name=LightBoxPanel 1;caption=Lightbox View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=853;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesPanel 2;caption=Time series 2;state=67377148;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=472;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=PowerSpectrumPanel 3;caption=Power spectra 3;state=67377148;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=-1;besth=472;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=493|
                     OverlayListPanel,LightBoxToolBar,OverlayDisplayToolBar,LocationPanel,MelodicClassificationPanel,LookupTablePanel,
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=197;besth=80;minw=197;minh=80;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=197;floath=96;notebookid=-1;transparent=255|name=LightBoxToolBar;caption=Lightbox view toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=757;besth=43;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=11;row=0;pos=0;prop=100000;bestw=860;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=0;row=0;pos=1;prop=100000;bestw=440;besth=109;minw=440;minh=109;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=440;floath=125;notebookid=-1;transparent=255|name=MelodicClassificationPanel;caption=Melodic IC classification;state=67373052;dir=2;layer=0;row=0;pos=1;prop=100000;bestw=400;besth=100;minw=400;minh=100;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=400;floath=116;notebookid=-1;transparent=255|name=LookupTablePanel;caption=Lookup tables;state=67373052;dir=2;layer=0;row=0;pos=0;prop=100000;bestw=358;besth=140;minw=358;minh=140;maxw=-1;maxh=-1;floatx=3614;floaty=658;floatw=358;floath=156;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=130|dock_size(1,10,0)=45|dock_size(1,11,0)=10|dock_size(2,0,0)=402|
                     ,
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|
                     ,
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|
                     """)),

    ('feat',
     textwrap.dedent("""
                     OrthoPanel,TimeSeriesPanel,
                     layout2|name=OrthoPanel 1;caption=Ortho View 1;state=67377088;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=853;besth=-1;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=TimeSeriesPanel 2;caption=Time series 2;state=67377148;dir=3;layer=0;row=0;pos=0;prop=100000;bestw=-1;besth=472;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=22|dock_size(3,0,0)=261|
                     OverlayDisplayToolBar,LocationPanel,AtlasPanel,OverlayListPanel,OrthoToolBar,ClusterPanel,
                     layout2|name=Panel;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=20;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=OverlayDisplayToolBar;caption=Display toolbar;state=67382012;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=860;besth=49;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=LocationPanel;caption=Location;state=67373052;dir=3;layer=2;row=0;pos=1;prop=98544;bestw=440;besth=109;minw=440;minh=109;maxw=-1;maxh=-1;floatx=2730;floaty=1104;floatw=440;floath=125;notebookid=-1;transparent=255|name=AtlasPanel;caption=Atlases;state=67373052;dir=2;layer=1;row=0;pos=0;prop=98904;bestw=318;besth=84;minw=318;minh=84;maxw=-1;maxh=-1;floatx=1091;floaty=143;floatw=318;floath=100;notebookid=-1;transparent=255|name=OverlayListPanel;caption=Overlay list;state=67373052;dir=3;layer=2;row=0;pos=0;prop=87792;bestw=197;besth=80;minw=197;minh=80;maxw=-1;maxh=-1;floatx=2608;floaty=1116;floatw=197;floath=96;notebookid=-1;transparent=255|name=OrthoToolBar;caption=Ortho view toolbar;state=67382012;dir=1;layer=10;row=1;pos=0;prop=100000;bestw=815;besth=34;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=2072;floaty=80;floatw=824;floath=50;notebookid=-1;transparent=255|name=ClusterPanel;caption=Cluster browser;state=67373052;dir=2;layer=1;row=0;pos=1;prop=114760;bestw=390;besth=96;minw=390;minh=96;maxw=-1;maxh=-1;floatx=3516;floaty=636;floatw=390;floath=112;notebookid=-1;transparent=255|dock_size(5,0,0)=10|dock_size(2,1,0)=566|dock_size(1,10,0)=51|dock_size(1,10,1)=36|dock_size(3,2,0)=130|
                     ,
                     layout2|name=FigureCanvasWxAgg;caption=;state=768;dir=5;layer=0;row=0;pos=0;prop=100000;bestw=640;besth=480;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|dock_size(5,0,0)=642|
                     """))))
