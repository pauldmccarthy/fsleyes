#!/usr/bin/env python
#
# profilemap.py - CanvasPanel -> Profile mappings.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module is used by the :class:`.Profile` and :class:`.ProfileManager`
classes.

It defines a few dictionaries which define the profile type to use for each
:class:`.CanvasPanel` type, temporary mouse/keyboard interaction modes, and
alternate mode handlers for the profiles contained in the profiles package.
"""

import logging

from collections import OrderedDict

import wx

from fsl.fsleyes.views.orthopanel             import OrthoPanel
from fsl.fsleyes.views.lightboxpanel          import LightBoxPanel

from fsl.fsleyes.profiles.orthoviewprofile    import OrthoViewProfile
from fsl.fsleyes.profiles.orthoeditprofile    import OrthoEditProfile
from fsl.fsleyes.profiles.lightboxviewprofile import LightBoxViewProfile


log = logging.getLogger(__name__)


profiles  = {
    OrthoPanel    : ['view', 'edit'],
    LightBoxPanel : ['view']
}
"""This dictionary is used by the :class:`.ProfileManager` to figure out which
profiles are available for each :class:`.CanvasPanel`.
"""


profileHandlers = {
    (OrthoPanel,    'view') : OrthoViewProfile,
    (OrthoPanel,    'edit') : OrthoEditProfile,
    (LightBoxPanel, 'view') : LightBoxViewProfile
}
"""This dictionary is used by the :class:`.ProfileManager` class to figure out
which :class:`.Profile` instance to create for a given :class:`.CanvasPanel`
instance and profile identifier.
"""


# For multi-key combinations, the modifier key
# IDs must be provided as a tuple, in alphabetical
# order. For example, to specify shift+ctrl, the
# tuple must be (wx.WXK_CTRL, wx.WXK_SHIFT)
tempModeMap = {

    # Command/CTRL puts the user in zoom mode,
    # and ALT puts the user in pan mode
    OrthoViewProfile : OrderedDict((
        (('nav',  wx.WXK_CONTROL), 'zoom'),
        (('pan',  wx.WXK_CONTROL), 'zoom'),
        (('nav',  wx.WXK_ALT),     'pan'),
        (('zoom', wx.WXK_ALT),     'pan'))),

    # OrthoEditProfile inherits all of the
    # settings for OrthoViewProfile above,
    # and adds new settings for the edit
    # modes (sel, desel, and selint)
    OrthoEditProfile : OrderedDict((

        # CTRL+Shift puts the user in
        # deselect mode (or select
        # mode if in deselect mode)
        (('sel',    (wx.WXK_CONTROL, wx.WXK_SHIFT)), 'desel'),
        (('selint', (wx.WXK_CONTROL, wx.WXK_SHIFT)), 'desel'),
        (('desel',  (wx.WXK_CONTROL, wx.WXK_SHIFT)), 'sel'),

        # ALT puts the user in pan mode,
        (('sel',    wx.WXK_ALT),     'pan'),
        (('selint', wx.WXK_ALT),     'pan'),
        (('desel',  wx.WXK_ALT),     'pan'),

        # Shift puts the user in navigate mode,
        (('sel',    wx.WXK_SHIFT),   'nav'),
        (('desel',  wx.WXK_SHIFT),   'nav'),
        (('selint', wx.WXK_SHIFT),   'nav'),

        # Command/CTRL puts the user in zoom mode,
        (('sel',    wx.WXK_CONTROL), 'zoom'),
        (('desel',  wx.WXK_CONTROL), 'zoom'),
        (('selint', wx.WXK_CONTROL), 'zoom'))),

    LightBoxViewProfile : OrderedDict((
        (('view', wx.WXK_CONTROL), 'zoom'), ))
}


altHandlerMap = {

    OrthoViewProfile : OrderedDict((
        
        # in navigate mode, the left mouse button
        # navigates, the right mouse button draws
        # a zoom rectangle, and the middle button
        # pans 
        (('nav',  'LeftMouseDown'),   ('nav',  'LeftMouseDrag')),
        (('nav',  'MiddleMouseDown'), ('pan',  'LeftMouseDown')),
        (('nav',  'MiddleMouseDrag'), ('pan',  'LeftMouseDrag')),
        (('nav',  'RightMouseDown'),  ('zoom', 'LeftMouseDown')),
        (('nav',  'RightMouseDrag'),  ('zoom', 'LeftMouseDrag')),
        (('nav',  'RightMouseUp'),    ('zoom', 'LeftMouseUp')),

        # In pan mode, the left mouse button pans,
        # and right mouse button navigates
        (('pan',  'LeftMouseDown'),   ('pan',  'LeftMouseDrag')),
        (('pan',  'RightMouseDown'),  ('nav',  'LeftMouseDown')),
        (('pan',  'RightMouseDrag'),  ('nav',  'LeftMouseDrag')),

        # In zoom mode, the left mouse button
        # draws a zoom rectangle, the right mouse
        # button navigates, and the middle mouse
        # button pans 
        (('zoom', 'LeftMouseDown'),   ('zoom', 'LeftMouseDrag')),
        (('zoom', 'RightMouseDown'),  ('nav',  'LeftMouseDown')),
        (('zoom', 'RightMouseDrag'),  ('nav',  'LeftMouseDrag')),
        (('zoom', 'MiddleMouseDrag'), ('pan',  'LeftMouseDrag')))),

    OrthoEditProfile : OrderedDict((

        # In select and select-by-intensity 
        # mode, the right mouse button deselects
        (('sel',    'RightMouseDown'),  ('desel',  'LeftMouseDown')),
        (('sel',    'RightMouseDrag'),  ('desel',  'LeftMouseDrag')),
        (('sel',    'RightMouseUp'),    ('desel',  'LeftMouseUp')),
        (('selint', 'RightMouseDown'),  ('desel',  'LeftMouseDown')),
        (('selint', 'RightMouseDrag'),  ('desel',  'LeftMouseDrag')),
        (('selint', 'RightMouseUp'),    ('desel',  'LeftMouseUp')), 

        # In select/deselect/selint
        # mode, the middle mouse buyton pans
        (('sel',    'MiddleMouseDown'), ('pan',    'LeftMouseDown')),
        (('sel',    'MiddleMouseDrag'), ('pan',    'LeftMouseDrag')),
        (('desel',  'MiddleMouseDrag'), ('pan',    'LeftMouseDrag')),
        (('selint', 'MiddleMouseDown'), ('pan',    'LeftMouseDown')),
        (('selint', 'MiddleMouseDrag'), ('pan',    'LeftMouseDrag')),

        # The selection cursor is shown in deselect
        # mode the same as for select mode
        (('desel',  'MouseMove'),       ('sel',    'MouseMove')),


        # Keyboard navigation works in the select
        # modes in the same way that it works
        # in navigate mode (as defined in the
        # OrthoViewProfile)
        (('sel',    'Char'), ('nav', 'Char')),
        (('desel',  'Char'), ('nav', 'Char')),
        (('selint', 'Char'), ('nav', 'Char')),
    )),


    LightBoxViewProfile : OrderedDict((
        (('view', 'LeftMouseDown'), ('view', 'LeftMouseDrag')), ))
}
