#!/usr/bin/env python
#
# perspectives.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import fsl.utils.settings   as fslsettings
import fsl.fsleyes.views    as views
import fsl.fsleyes.controls as controls


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
    
    return perspectives



def loadPerspective(frame, name):
    log.debug('Loading perspective {}'.format(name))

    persp = fslsettings.read('fsleyes.perspectives.{}'.format(name), None)


def savePerspective(frame, name):
    
    log.debug('Saving current perspective with name {}'.format(name))
    persp = serialisePerspective(frame)
    fslsettings.write('fsleyes.perspectives.{}'.format(name), persp)


    
def serialisePerspective(frame):
    log.debug('Serialising current perspective')

    auiMgr     = frame.getAuiManager()
    viewPanels = frame.getViewPanels()

    frameLayout = auiMgr.SavePerspective()

    # The different sections of the string
    # returned by SavePerspective are
    # separated with a '|' character.
    lines = frameLayout.split('|')
    lines = [l.strip() for l in lines]
    lines = [l for l in lines if l != '']

    # Even though the layout for each view
    # panel is included in the perspective
    # string, we are going to remove them,
    # and patch them back in, in the loop
    # below. This is so we can match view
    # panel layouts with their child control
    # panel layouts, and be sure that each 
    # view panel is paired to the correct
    # set of control panels.
    lines = [l for l in lines if l.find('name=') == -1]

    for vp in viewPanels:

        # Get the layout for this view panel
        # (which we just removed, above)
        vpLayout = auiMgr.SavePaneInfo(frame.getViewPanelInfo(vp))

        # Each ViewPanel is itself managed by
        # an AuiManager, which manages the layout
        # of the control panels that have been
        # added to the ViewPanel. Here, we get
        # the layout for this view panel.
        vpAuiMgr      = vp.getAuiManager()
        vpInnerLayout = vpAuiMgr.SavePerspective()

        # After the Frame-level layout for a view
        # panel, we add in the ViewPanel-level
        # layout for the control panels within
        # that view panel.
        lines.append(vpLayout)
        lines.append(vpInnerLayout)

    # Both the frame-level, and the viewpanel-level
    # layouts use '|' characters to separate their
    # sections. To avoid confusing the two, we're
    # replacing the pipes in the frame-level layout 
    # with newlines.
    layout = '\n'.join(lines)

    return layout


def deserialisePerspective(persp):
    """
    """
    # Returns:
    #  - Layout string for Frame
    #  - List of ViewPanels
    # 
    #  - For each ViewPanel:
    #     - Layout string for ViewPanel
    #     - List of ControlPanels

    lines = persp.split('\n')
