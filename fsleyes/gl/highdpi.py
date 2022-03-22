#!/usr/bin/env python
#
# highdpi.py - Functions for enabling retina / high DPI rendering on OpenGL
# canvases.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for enabling retina / high DPI rendering on
OpenGL canvases. It is used by the :class:`.WXGLCanvasTarget` class.

Two functions are defined:

  - :func:`needsToggling` returns ``True`` or ``False``, indicating whether
    a call to :func:`toggle` is necessary.

  - :func:`toggle` enables / disables high DPI rendering for a specific
    :class:`.WXGLCanvasTarget`.

On macOS with wxPython < 4.1.0, retina support for OpenGL canvases must be
programmatically enabled. In all other configurations, :func:`needsToggling`
will return False, and :func:`toggle` will do nothing.
"""


import              ctypes
import functools as ft
import              platform


@ft.lru_cache()
def _objc_runtime():
    """Create and return a wrapper around the objective-c runtime, with
    only the bits that we need.
    """

    objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library('objc'))
    _    = ctypes.cdll.LoadLibrary(ctypes.util.find_library('Foundation'))

    # Get the class of an object
    objc.object_getClass.argtypes = [ctypes.c_void_p]
    objc.object_getClass.restype  =  ctypes.c_void_p

    # Get a method associated with an instance
    objc.class_getInstanceMethod.restype  =  ctypes.c_void_p
    objc.class_getInstanceMethod.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    # Register a method given its name
    objc.sel_registerName.restype  =  ctypes.c_void_p
    objc.sel_registerName.restype  =  ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]

    # Send a message (a.k.a. call a method) on an object
    objc.objc_msgSend.restype  =  ctypes.c_void_p
    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

    return objc


@ft.lru_cache()
def needsToggling():
    """Return ``True`` if high-DPI scaling can be toggled, ``False``
    otherwise.

    Under GTK, high DPI support is not possible with wxPython < 4.0.7, as
    ``wx.Window.GetContentScaleFactor`` always returns 1. Under GTK and
    from wxPython 4.0.7 onwards, GL canvases are scaled automatically. This
    function therefore returns ``False`` in both of these cases.

    Under macOS and wxpython < 4.1.0, high DPI must be explicitly requested
    for GL canvases via a Cocoa API call. This can be done via the
    :meth:`toggle` function.

    Under macOS and with wxpython >= 4.1.0, GL canvases are scaled
    automatically, so in this case this function will return ``False``.
    """

    import wx

    if platform.system() != 'Darwin':
        return False

    wxver = getattr(wx, '__version__', '1.0.0')
    wxver = [int(v) for v in wxver.split('.')[:3]]

    return wxver < [4, 1, 0]


def toggle(canvas, enable=True):
    """Enables/disables high-DPI/retina resolution rendering on the given
    ``wx.glcanvas.GLCanvas`` object.
    """
    if not needsToggling():
        return

    objc     = _objc_runtime()
    hd       = canvas.GetHandle()
    selector = objc.sel_registerName(b'setWantsBestResolutionOpenGLSurface:')
    objc.objc_msgSend(hd, selector, ctypes.c_bool(enable))
