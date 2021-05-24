#!/usr/bin/env python
#
# __init__.py - OpenGL data and rendering for FSLeyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains the OpenGL data and rendering stuff for *FSLeyes*.
On-screen and off-screen rendering is supported, and two OpenGL versions (1.4
and 2.1) are supported.  The contents of this package can be broadly
categorised into the following:

 - *Canvases*: A canvas is a thing that can be drawn on.

 - *Objects*:  An object is a thing which can be drawn on a canvas.


-----------
Quick start
-----------

::

    import fsleyes.gl                 as fslgl
    import fsleyes.gl.wxglslicecanvas as slicecanvas

    # This function will be called when
    # the GL context is ready to be used.
    def ready():

        # The fsleyes.gl package needs to do
        # some initialisation that can only
        # be performed once a GL context has
        # been created.
        fslgl.bootstrap()

        # Once a GL context has been created,
        # you can do stuff! The SliceCanvas
        # will take care of creating and
        # managing GLObjects for each overlay
        # in the overlay list.
        canvas = slicecanvas.WXGLSliceCanvas(parent, overlayList, displayCtx)

    # Create a GL context, and tell it to
    # call our function when it is ready.
    fslgl.getGLContext(ready=ready)

    # ...

    # When you're finished, call the shutdown
    # function to clear the context (only
    # necessary for on-screen rendering)
    fslgl.shutdown()


--------
Canvases
--------


A *canvas* is the destination for an OpenGL scene render. The following
canvases are defined in the ``gl`` package:

.. autosummary::
   :nosignatures:

   ~fsleyes.gl.slicecanvas.SliceCanvas
   ~fsleyes.gl.lightboxcanvas.LightBoxCanvas
   ~fsleyes.gl.scene3dcanvas.Scene3DCanvas
   ~fsleyes.gl.colourbarcanvas.ColourBarCanvas


These classes are not intended to be used directly. This is because the ``gl``
package has been written to support two primary use-cases:

  - *On-screen* display of a scene using a :class:`wx.glcanvas.GLCanvas`
    canvas.

  - *Off-screen* rendering of a scene to a file.


Because of this, the canvas classes listed above are not dependent upon the
OpenGL environment in which they are used (i.e. on-screen or off-screen).
Instead, two base classes are provided for each of the use-cases:


.. autosummary::
   :nosignatures:

   WXGLCanvasTarget
   OffScreenCanvasTarget


And the following sub-classes are defined, providing use-case specific
implementations for each of the available canvases:

.. autosummary::
   :nosignatures:

   ~fsleyes.gl.wxglslicecanvas.WXGLSliceCanvas
   ~fsleyes.gl.wxgllightboxcanvas.WXGLLightBoxCanvas
   ~fsleyes.gl.wxglscene3dcanvas.WXGLScene3DCanvas
   ~fsleyes.gl.wxglcolourbarcanvas.WXGLColourBarCanvas
   ~fsleyes.gl.offscreenslicecanvas.OffScreenSliceCanvas
   ~fsleyes.gl.offscreenlightboxcanvas.OffScreenLightBoxCanvas
   ~fsleyes.gl.offscreenscene3dcanvas.OffScreenScene3DCanvas
   ~fsleyes.gl.offscreencolourbarcanvas.OffScreenColourBarCanvas


The classes listed above are the ones which are intended to be instantiated
and used by application code.


--------------
``gl`` objects
--------------


With the exception of the :class:`.ColourBarCanvas`, everything that is drawn
on a canvas derives from the :class:`.GLObject` base class. A ``GLObject``
manages the underlying data structures, GL resources (e.g. shaders and
textures), and rendering routines required to draw an object, in 2D or 3D, to a
canvas.  The following ``GLObject`` sub-classes correspond to each of the
possible types (the :attr:`.Display.overlayType` property) that an overlay can
be displayed as:

.. autosummary::

   ~fsleyes.gl.glvolume.GLVolume
   ~fsleyes.gl.glrgbvolume.GLRGBVolume
   ~fsleyes.gl.glcomplex.GLComplex
   ~fsleyes.gl.glmask.GLMask
   ~fsleyes.gl.gllabel.GLLabel
   ~fsleyes.gl.gllinevector.GLLineVector
   ~fsleyes.gl.glrgbvector.GLRGBVector
   ~fsleyes.gl.glmesh.GLMesh
   ~fsleyes.gl.glmip.GLMIP
   ~fsleyes.gl.gltensor.GLTensor
   ~fsleyes.gl.glsh.GLSH


These objects are created and destroyed automatically by the canvas classes
instances, so application code does not need to worry about them too much.


===========
Annotations
===========


Canvases can be *annotated* in a few ways, by use of the :class:`.Annotations`
class. An ``Annotations`` object allows lines, rectangles, and other simple
shapes to be rendered on top of the ``GLObject`` renderings which represent
the overlays in the :class:`.OverlayList`.  The ``Annotations`` object for a
canvas instance can be accessed through its ``getAnnotations`` method.


---------------------------------
OpenGL versions and bootstrapping
---------------------------------


*FSLeyes* needs to be able to run in restricted environments, such as within a
VNC session, and over SSH. In such environments the available OpenGL version
could be quite old, so the ``gl`` package has been written to support an
environment as old as OpenGL 1.4.


The available OpenGL API version can only be determined once an OpenGL context
has been created, and a display is available for rendering. The package-level
:func:`getGLContext` function allows a context to be created.


The data structures and rendering logic for some ``GLObject`` classes differs
depending on the OpenGL version that is available. Therefore, the code for
these ``GLObject`` classes may be duplicated, with one version for OpenGL 1.4,
and another version for OpenGL 2.1.  The ``GLObject`` code which targets a
specific OpenGL version lives within either the :mod:`.gl14` or :mod:`.gl21`
sub-packages.


Because of this, the package-level :func:`bootstrap` function must be called
before any ``GLObject`` instances are created, but *after* a GL context has
been created.
"""


import os
import sys
import logging
import platform

import fsl.utils.idle                     as idle
import fsl.version                        as fslversion
from   fsl.utils.platform import platform as fslplatform
import fsleyes_widgets                    as fwidgets


log = logging.getLogger(__name__)


import OpenGL  # noqa


# Make PyOpenGL throw an error, instead of implicitly
# converting, if we pass incorrect types to OpenGL functions.
OpenGL.ERROR_ON_COPY = True


# These flags should be set to True
# for development, False for production
OpenGL.ERROR_CHECKING = True
OpenGL.ERROR_LOGGING  = True


# If FULL_LOGGING is enabled,
# every GL call will be logged.
# OpenGL.FULL_LOGGING   = True


GL_VERSION = None
"""Set in :func:`bootstrap`. String containing the available "major.minor"
OpenGL version.
"""


GL_COMPATIBILITY = None
"""Set in :func:`bootstrap`. String containing the target "major.minor"
OpenGL compatibility version ("1.4" or "2.1").
"""


GL_RENDERER = None
"""Set in :func:`bootstrap`. Contains a description of the OpenGL renderer in
 use.
"""


def _selectPyOpenGLPlatform():
    """Pyopengl sometimes doesn't select a suitable platform, so in some
    circumstances we need to force things (but not if ``PYOPENGL_PLATFORM``
    is already set in the environment).
    """
    if 'PYOPENGL_PLATFORM' in os.environ:
        return

    # If no display, osmesa on all platforms
    if not fwidgets.canHaveGui():
        os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

    # GTK3 versions of wxpython 4.1.1 and newer
    # default to using EGL for GL initialisation,
    # but pyopengl defaults to glx.
    elif fslplatform.os.lower() == 'linux':
        wxver  = fwidgets.wxVersion()
        wxplat = fwidgets.wxPlatform()

        if wxver is not None                               and \
           fslversion.compareVersions(wxver, '4.1.1') >= 0 and \
           wxplat == fwidgets.WX_GTK3:
            os.environ['PYOPENGL_PLATFORM'] = 'egl'


_selectPyOpenGLPlatform()


def glIsSoftwareRenderer():
    """Returns ``True`` if the OpenGL renderer appears to be software based,
    ``False`` otherwise, or ``None`` :func:`bootstrap` has not been called yet.

    .. note:: This check is based on heuristics, ans is not guaranteed to
              be correct.
    """
    if GL_RENDERER is None:
        return None

    # There doesn't seem to be any quantitative
    # method for determining whether we are using
    # software-based rendering, so a hack is
    # necessary.
    renderer = GL_RENDERER.lower()

    # "software" / "chromium" -> software renderer
    # But SVGA3D/llvmpipe are super fast, so if
    # we're using either of them, pretend that
    # we're on hardware
    sw     = any(('software' in renderer, 'chromium' in renderer))
    fastsw = any(('llvmpipe' in renderer, 'svga3d'   in renderer))

    return sw and (not fastsw)


def bootstrap(glVersion=None):
    """Imports modules appropriate to the specified OpenGL version.

    The available OpenGL API version can only be queried once an OpenGL
    context is created, and a canvas is available to draw on. This makes
    things a bit complicated, because it means that we are only able to
    choose how to draw things when we actually need to draw them.


    This function should be called after an OpenGL context has been created,
    and a canvas is available for drawing, but before any attempt to draw
    anything.  It will figure out which version-dependent package needs to be
    loaded, and will attach all of the modules contained in said package to
    the :mod:`~fsleyes.gl` package.  The version-independent modules may
    then simply access these version-dependent modules through this module.


    After the :func:`boostrap` function has been called, the following
    package-level attributes will be available on the ``gl`` package:


    ====================== ====================================================
    ``GL_COMPATIBILITY``   A string containing the target OpenGL version, in
                           the format ``major.minor``, e.g. ``2.1``.

    ``GL_VERSION``         A string containing the available OpenGL version.

    ``GL_RENDERER``        A string containing the name of the OpenGL renderer.

    ``glvolume_funcs``     The version-specific module containing functions for
                           rendering :class:`.GLVolume` instances.

    ``glrgbvolume_funcs``  The version-specific module containing functions for
                           rendering :class:`.GLRGBVolume` instances.

    ``glrgbvector_funcs``  The version-specific module containing functions for
                           rendering :class:`.GLRGBVector` instances.

    ``gllinevector_funcs`` The version-specific module containing functions for
                           rendering :class:`.GLLineVector` instances.

    ``glmesh_funcs``       The version-specific module containing functions for
                           rendering :class:`.GLMesh` instances.

    ``glmask_funcs``       The version-specific module containing functions for
                           rendering :class:`.GLMask` instances.

    ``gllabel_funcs``      The version-specific module containing functions for
                           rendering :class:`.GLLabel` instances.

    ``gltensor_funcs``     The version-specific module containing functions for
                           rendering :class:`.GLTensor` instances.

    ``glsh_funcs``         The version-specific module containing functions for
                           rendering :class:`.GLSH` instances.

    ``glmip_funcs``        The version-specific module containing functions for
                           rendering :class:`.GLMIP` instances.
    ====================== ====================================================


    :arg glVersion: A tuple containing the desired (major, minor) OpenGL API
                    version to use. If ``None``, the best possible API
                    version will be used.
    """

    import OpenGL.GL         as gl
    import OpenGL.extensions as glexts
    from . import               gl14
    from . import               gl21

    thismod = sys.modules[__name__]

    if hasattr(thismod, '_bootstrapped'):
        return

    if glVersion is None:
        glver = gl.glGetString(gl.GL_VERSION).decode('latin1').split()[0]
        major, minor = [int(v) for v in glver.split('.')][:2]
    else:
        major, minor = glVersion

    # glVersion contains the actual GL version
    # verstr contains the target compatibility
    # GL version
    glVersion = major + minor / 10.0
    glpkg     = None
    if glVersion >= 2.1:
        verstr = '2.1'
        glpkg  = gl21
    elif glVersion >= 1.4:
        verstr = '1.4'
        glpkg  = gl14
    else: raise RuntimeError('OpenGL 1.4 or newer is required '
                             '(detected version: {:0.1f})'.format(glVersion))

    # The gl21 implementation depends on a
    # few extensions - if they're not present,
    # fall back to the gl14 implementation
    if glpkg == gl21:

        # List any GL21 extensions here
        exts = ['GL_EXT_framebuffer_object',
                'GL_ARB_instanced_arrays',
                'GL_ARB_draw_instanced']

        if not all(map(glexts.hasExtension, exts)):
            log.warning('One of these OpenGL extensions is '
                        'not available: [{}]. Falling back '
                        'to an older OpenGL implementation.'
                        .format(', '.join(exts)))
            verstr = '1.4'
            glpkg  = gl14

    # If using GL14, and the ARB_vertex_program
    # and ARB_fragment_program extensions are
    # not present, we're screwed.
    if glpkg == gl14:

        exts = ['GL_EXT_framebuffer_object',
                'GL_ARB_vertex_program',
                'GL_ARB_fragment_program',
                'GL_ARB_texture_non_power_of_two']

        if not all(map(glexts.hasExtension, exts)):
            raise RuntimeError('One of these OpenGL extensions is '
                               'not available: [{}]. This software '
                               'cannot run on the available graphics '
                               'hardware.'.format(', '.join(exts)))

        # Tensor/SH/MIP overlays are not available in GL14
        import fsleyes.displaycontext as dc
        dc.ALL_OVERLAY_TYPES            .remove('tensor')
        dc.ALL_OVERLAY_TYPES            .remove('sh')
        dc.ALL_OVERLAY_TYPES            .remove('mip')
        dc.OVERLAY_TYPES['DTIFitTensor'].remove('tensor')
        dc.OVERLAY_TYPES['Image']       .remove('sh')
        dc.OVERLAY_TYPES['Image']       .remove('tensor')
        dc.OVERLAY_TYPES['Image']       .remove('mip')

    renderer = gl.glGetString(gl.GL_RENDERER).decode('latin1')
    log.debug('Using OpenGL {} implementation with renderer {}'.format(
        verstr, renderer))

    thismod.GL_VERSION         = str(glVersion)
    thismod.GL_COMPATIBILITY   = verstr
    thismod.GL_RENDERER        = renderer
    thismod.glvolume_funcs     = glpkg.glvolume_funcs
    thismod.glrgbvolume_funcs  = glpkg.glrgbvolume_funcs
    thismod.glrgbvector_funcs  = glpkg.glrgbvector_funcs
    thismod.gllinevector_funcs = glpkg.gllinevector_funcs
    thismod.glmask_funcs       = glpkg.glmask_funcs
    thismod.glmesh_funcs       = glpkg.glmesh_funcs
    thismod.gllabel_funcs      = glpkg.gllabel_funcs
    thismod.gltensor_funcs     = glpkg.gltensor_funcs
    thismod.glsh_funcs         = glpkg.glsh_funcs
    thismod.glmip_funcs        = glpkg.glmip_funcs
    thismod._bootstrapped      = True

    # If we're using a software based renderer,
    # reduce the default performance settings
    if glIsSoftwareRenderer():

        log.debug('Software-based rendering detected - '
                  'lowering default performance settings.')

        import fsleyes.displaycontext as dc
        dc.SceneOpts.performance.setAttribute(None, 'default', 1)


def getGLContext(**kwargs):
    """Create and return a GL context object for on- or off-screen OpenGL
    rendering.

    If a context object has already been created, it is returned.
    Otherwise, one is created and returned.

    See the :class:`GLContext` class for details on the arguments.

    .. warning:: Use the ``ready`` argument to
                 :meth:`GLContext.__init__`, and don't call :func:`bootstrap`
                 until it has been called!
    """

    thismod = sys.modules[__name__]

    # A context has already been created
    if hasattr(thismod, '_glContext'):

        # If a callback was provided,
        # make sure it gets called.
        callback = kwargs.pop('ready', None)
        if callback is not None:
            idle.idle(callback)

        return thismod._glContext

    thismod._glContext = GLContext(**kwargs)

    return thismod._glContext


def shutdown():
    """Must be called when the GL rendering context is no longer needed.
    Destroys the context object, and resources associated with it.

    Does not need to be called for off-screen rendering.
    """

    thismod = sys.modules[__name__]
    context = getattr(thismod, '_glContext', None)
    if context is not None:
        context.destroy()
        delattr(thismod, '_glContext')


class GLContext:
    """The ``GLContext`` class manages the creation of, and access to, an
    OpenGL context. This class abstracts away the differences between
    creation of on-screen and off-screen rendering contexts.
    It contains two methods:

      - :meth:`setTarget`, which may be used to set a
        :class:`.WXGLCanvasTarget` or an :class:`OffScreenCanvasTarget` as the
        GL rendering target.
      - :meth:`destroy`, which must be called when the context is no longer
        needed.


    On-screen rendering is performed via the ``wx.GLCanvas.GLContext``
    context, whereas off-screen rendering is performed  via
    ``OpenGL.raw.osmesa.mesa`` (OSMesa is assumed to be available).


    If it is possible to do so, a ``wx.glcanvas.GLContext`` will be created,
    even if an off-screen context has been requested. This is because
    using the native graphics card is nearly always preferable to using
    OSMesa.


    *Creating an on-screen GL context*


    A ``wx.glcanvas.GLContext`` may only be created once a
    ``wx.glcanvas.GLCanvas`` has been created, and is visible on screen.  The
    ``GLContext`` class therefore creates a dummy ``wx.Frame`` and
    ``GLCanvas``, and displays it, before creating the ``wx`` GL context.


    A reference to this dummy ``wx.Frame`` is retained, because destroying it
    can result in ``GLXBadCurrentWindow`` errors when running on
    macOS+XQuartz. The frame is destroyed on calls to the ``GLContext.destroy``
    method.


    Because ``wx`` contexts may be used even when an off-screen rendering
    context has been requested, the ``GLContext`` class has the ability to
    create and run a temporary ``wx.App``, on which the canvas and context
    creation process is executed. This horrible ability is necessary, because
    a ``wx.GLContext`` must be created on a ``wx`` application loop. We cannot
    otherwise guarantee that the ``wx.GLCanvas`` will be visible before the
    ``wx.GLContext`` is created.


    The above issue has the effect that the real underlying ``wx.GLContext``
    may only be created after the ``GLContext.__init__`` method has returned.
    Therefore, you must use the ``ready`` callback function if you are
    creating a ``wx`` GL context - this function will be called when the
    ``GLContext`` is ready to be used.


    You can get away without using the ``ready`` callback in the following
    situations:

      - When you are 100% sure that you will be using OSMesa.

      - When there is not (and never will be) a ``wx.MainLoop`` running, and
        you pass in ``createApp=True``.
    """

    def __init__(self,
                 offscreen=False,
                 other=None,
                 target=None,
                 createApp=False,
                 ready=None,
                 raiseErrors=False):
        """Create a ``GLContext``.

        :arg offscreen:   On-screen or off-screen context?

        :arg other:       Another ``GLContext`` instance with which GL state
                          should be shared.

        :arg target:      If ``other`` is not ``None``, this must be a
                          reference to a ``WXGLCanvasTarget``, the rendering
                          target for the new context.

        :arg createApp:   If ``True``, and if possible, this ``GLContext`` will
                          create and run a ``wx.App`` so that it can create a
                          ``wx.glcanvas.GLContext``.

        :arg ready:       Function which will be called when the context has
                          been created and is ready to use.

        :are raiseErrors: Defaults to ``False``. If ``True``, and if the
                          ``ready`` function raises an error, that error is not
                          caught.
        """

        def defaultReady():
            pass

        if ready is None:
            ready = defaultReady

        self.__offscreen = offscreen
        self.__ownApp    = False
        self.__context   = None
        self.__canvas    = None
        self.__parent    = None
        self.__buffer    = None
        self.__app       = None

        osmesa     = os.environ.get('PYOPENGL_PLATFORM', None) == 'osmesa'
        canHaveGui = fwidgets.canHaveGui()
        haveGui    = fwidgets.haveGui()

        # On-screen contexts *must* be
        # created via a wx event loop
        if (not offscreen) and not (haveGui or createApp):
            raise ValueError('On-screen GL contexts must be '
                             'created on the wx.MainLoop')

        # For off-screen, only use OSMesa
        # if we have no cnoice, or if
        # dictated by PYOPENGL_PLATFORM.
        # Otherewise we use wx if possible.
        if offscreen and (osmesa or (not canHaveGui)):
            self.__createOSMesaContext()
            ready()
            return

        self.__ownApp = (not haveGui) and createApp

        # A context already exists - we don't
        # need to create a GL canvas to create
        # another one.
        if other is not None:
            self.__createWXGLContext(other=other.__context, target=target)
            ready()
            return

        # Create a wx.App if we've been
        # given permission to do so
        # (via the createApp argument)
        if self.__ownApp:
            log.debug('Creating temporary wx.App')

            import fsleyes.main as fm
            self.__app = fm.FSLeyesApp()

        # Create a parent for the GL
        # canvas, and the canvas itself
        self.__createWXGLParent()
        self.__createWXGLCanvas()

        # This function creates the context
        # and does some clean-up afterwards.
        # It gets scheduled on the wx idle
        # loop.
        def create():

            app = self.__app

            self.__createWXGLContext()

            # If we've created and started
            # our own loop, kill it
            if self.__ownApp:
                log.debug('Exiting temporary wx.MainLoop')
                app.ExitMainLoop()

            if ready is not None:

                try:
                    ready()

                except Exception as e:
                    log.warning('GLContext callback function raised '
                                '{}: {}'.format(type(e).__name__,
                                                str(e)),
                                                exc_info=True)
                    if raiseErrors:
                        raise e

            # We keep the parent around, because
            # destroying it can cause GLXBadCurrentWindow
            # errors when running on macOS+XQuartz. It is
            # destroyed when the GLContext.destroy() method
            # is called.
            self.__parent.Hide()

        # If we've created our own wx.App, run its
        # main loop - we need to run the loop
        # in order to display the GL canvas and
        # context. But we can kill the loop as soon
        # as this is done (in the create function
        # above).  If an existing wx.App is running,
        # we just schedule the context creation
        # routine on it.
        idle.idle(create, alwaysQueue=True)

        if self.__ownApp:
            log.debug('Starting temporary wx.MainLoop')
            self.__app.MainLoop()


    def destroy(self):
        """Called by the module-level :func:`shutdown` function. If this is an
        on-screen context, the dummy canvas and frame that were created at
        initialisation are destroyed.
        """

        # We need to destroy the OSMesa context,
        # otherwise it will stay in memory
        if self.__buffer is not None:
            import OpenGL.raw.osmesa.mesa as osmesa
            osmesa.OSMesaDestroyContext(self.__context)

        # Clear refs to wx frame/canvas
        # before destroying the wx.App,
        # as problems can otherwise occur
        app            = self.__app
        self.__app     = None
        self.__context = None
        self.__buffer  = None
        self.__parent  = None
        self.__canvas  = None

        if app is not None:
            app.Destroy()


    def setTarget(self, target=None):
        """Set the given ``WXGLCanvasTarget`` or ``OffScreenCanvasTarget`` as
        the target for GL rendering with this context.

        If ``target`` is None, and this is an on-screen rendering context,
        the dummy ``wx.glcanvas.GLCanvas`` that was used to create this
        ``GLContext`` is set as the rendering target.
        """
        # not necessary for offscreen rendering
        if self.__offscreen:
            return True

        # destroy() has been called
        if self.__context is None:
            return False

        if target is None and self.__canvas is not None:
            return self.__context.SetCurrent(self.__canvas)

        else:
            import wx.glcanvas as wxgl
            if isinstance(target, wxgl.GLCanvas):
                return self.__context.SetCurrent(target)


    def __createWXGLParent(self):
        """Create a dummy ``wx.Frame`` to be used as the parent for the
        dummy ``wx.glcanvas.GLCanvas``.
        """

        import wx

        # Override ShouldPreventAppExit, meaning
        # that the wx.App.MainLoop will exit even
        # if a DummyFrame still exists. The wx
        # equivalent of marking a thread as a
        # daemon.
        class DummyFrame(wx.Frame):
            def ShouldPreventAppExit(self):
                return False

        log.debug('Creating dummy wx.Frame for GL context creation')

        self.__parent = DummyFrame(None, style=0)
        self.__parent.SetSize((0, 0))
        self.__parent.Show(True)


    def __createWXGLCanvas(self):
        """Create a dummy ``wx.glcanvas.GLCanvas`` instance which is to
        be used to create a context. Assigns the canvas to an attributed
        called ``__canvas``.
        """

        import wx.glcanvas as wxgl

        log.debug('Creating temporary wx.GLCanvas')

        # There's something wrong with wxPython's
        # GLCanvas (on OSX at least) - the pixel
        # format attributes have to be set on the
        # *first* GLCanvas that is created -
        # setting them on subsequent canvases will
        # have no effect. But if you set them on
        # the first canvas, all canvases that are
        # subsequently created will inherit the
        # same properties.
        attrs = WXGLCanvasTarget.displayAttribues()

        # GLCanvas initialisation with an attribute
        # list fails when running in a nomachine-like
        # remote desktop session. No idea why.
        try:
            self.__canvas = wxgl.GLCanvas(self.__parent, **attrs)
            self.__canvas.SetSize((0, 0))

        # Creating without attribute list works ok
        # though. This does mean that we don't have
        # control over depth/stencil buffer sizes,
        # under these remote desktop environments.
        except Exception:
            self.__canvas = wxgl.GLCanvas(self.__parent)
            self.__canvas.SetSize((0, 0))

        self.__canvas.Show(True)


    def __createWXGLContext(self, other=None, target=None):
        """Creates a ``wx.glcanvas.GLContext`` object, assigning it to
        an attribute called ``__context``. Assumes that a
        ``wx.glcanvas.GLCanvas`` has already been created.

        :arg other:  Another `wx.glcanvas.GLContext`` instance with which
                     the new context should share GL state.

        :arg target: If ``other`` is not ``None``, this must be a
                     ``wx.glcanvas.GLCanvas``, the rendering target for the
                     new context.

        .. warning:: This method *must* be called via the ``wx.MainLoop``.
        """

        import                wx
        import wx.glcanvas as wxgl

        # Versions of wxwidgets 3.1 and newer (approximately
        # corresponding to wxpython 4.1 and newer) allow
        # us to select a GL compatibility profile (required,
        # because we rely on GL 1.4/2.1).
        #
        # This only seems to work with wayland/EGL builds of
        # wxPython. We assume that gtk3+wxpython>=4.1.1
        # supports requesting a compatibility profile,
        # but don't bother for gtk2+older wxpython
        wxver  = fwidgets.wxVersion()
        wxplat = fwidgets.wxPlatform()
        if wxver is not None                               and \
           fslversion.compareVersions(wxver, '4.1.1') >= 0 and \
           wxplat in (fwidgets.WX_MAC_COCOA, fwidgets.WX_GTK3):
            attrs = wxgl.GLContextAttrs()
            attrs.CompatibilityProfile()
            attrs.EndList()
            kwargs = {'ctxAttrs' : attrs}
        else:
            kwargs = {}

        log.debug('Creating wx.GLContext')

        if other is not None:
            self.__context = wxgl.GLContext(target, other=other, **kwargs)

        else:
            self.__context = wxgl.GLContext(self.__canvas, **kwargs)

            # We can't set the context target
            # until the dummy canvas is
            # physically shown on the screen.
            while not self.__canvas.IsShownOnScreen():
                wx.GetApp().Yield()

            self.__context.SetCurrent(self.__canvas)


    def __createOSMesaContext(self):
        """Creates an OSMesa context, assigning it to an attribute called
        ``__context``.
        """

        import OpenGL.GL              as gl
        import OpenGL.raw.osmesa.mesa as osmesa
        import OpenGL.arrays          as glarrays

        log.debug('Creating gl.OSMesaContext')

        # We have to create a dummy buffer
        # for the off-screen context.
        buffer  = glarrays.GLubyteArray.zeros((640, 480, 4))
        context = osmesa.OSMesaCreateContextExt(
            gl.GL_RGBA, 8, 4, 0, None)
        osmesa.OSMesaMakeCurrent(context,
                                 buffer,
                                 gl.GL_UNSIGNED_BYTE,
                                 640,
                                 480)

        self.__buffer  = buffer
        self.__context = context


class OffScreenCanvasTarget:
    """Base class for canvas objects which support off-screen rendering. """

    def __init__(self, width, height):
        """Create an ``OffScreenCanvasTarget``. A :class:`.RenderTexture` is
        created, to be used as the rendering target.

        :arg width:    Width in pixels
        :arg height:   Height in pixels
        """

        from fsleyes.gl.textures import RenderTexture

        self.__width  = width
        self.__height = height
        self.__target = RenderTexture(
            '{}({})_RenderTexture'.format(
                type(self).__name__,
                id(self)))


    def _setGLContext(self):
        """Configures the GL context to render to this canvas. """
        return getGLContext().setTarget(self)


    def _draw(self, *a):
        """Must be provided by subclasses."""
        raise NotImplementedError()


    def getAnnotations(self):
        """Must be provided by subclasses."""
        raise NotImplementedError()


    def canvasToWorld(self, xpos, ypos):
        """Convert X/Y pixel coordinates into a location in the display
        coordinate system. Must be provided by subclasses.
        """
        raise NotImplementedError()


    def worldToCanvas(self, pos):
        """Convert a location in the display coordinate system into X/Y pixel
        coordinates. Must be provided by subclasses.
        """
        raise NotImplementedError()


    def GetSize(self):
        """Returns a tuple containing the canvas width and height."""
        return self.__width, self.__height


    def GetScaledSize(self):
        """Returns a tuple containing the canvas width and height."""
        return self.GetSize()


    def Refresh(self, *a):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass


    def FreezeDraw(self):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass


    def ThawDraw(self):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass

    def FreezeSwapBuffers(self):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass


    def ThawSwapBuffers(self):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass


    def EnableHighDPI(self):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass


    def draw(self):
        """Calls the :meth:`_draw` method, which must be provided by
        subclasses.
        """

        self._setGLContext()
        self._initGL()
        self.__target.shape = self.__width, self.__height

        with self.__target.target():
            self._draw()


    def getBitmap(self):
        """Return a (height*width*4) shaped numpy array containing the
        rendered scene as an RGBA bitmap. The bitmap will be full of
        zeros if the scene has not been drawn (via a call to
        :meth:`draw`).
        """

        self._setGLContext()
        return self.__target.getBitmap()


    def saveToFile(self, filename):
        """Saves the contents of this canvas as an image, to the specified
        file.
        """
        import matplotlib.image as mplimg
        mplimg.imsave(filename, self.getBitmap())


class WXGLCanvasTarget:
    """Base class for :class:`wx.glcanvas.GLCanvas` objects.

    It is assumed that subclasses of this base class are also subclasses of
    :class:`wx.glcanvas.GLCanvas`. Sub-classes must override the following
    methods:

    .. autosummary::
       :nosignatures:

       _initGL
       _draw

    And must also ensure that the :meth:`destroy` method is called when
    the class is being destroyed.
    """


    @staticmethod
    def canToggleHighDPI():
        """Return ``True`` if high-DPI scaling can be toggled, ``False``
        otherwise.

        Under GTK, high DPI support is not possible with wxPython < 4.0.7, as
        ``wx.Window.GetContentScaleFactor`` always returns 1. Under GTK and
        from wxPython 4.0.7 onwards, GL canvases are scaled automatically.

        Under macOS and wxpython < 4.1.0, high DPI must be explicitly requested
        for GL canvases via a Cocoa API call. This can be done via the
        :meth:`EnableHighDPI` method.

        Under macOS and with wxpython >= 4.1.0, GL canvases are scaled
        automatically.
        """

        import wx

        if platform.system() != 'Darwin':
            return False

        wxver = getattr(wx, '__version__', '1.0.0')
        wxver = [int(v) for v in wxver.split('.')[:3]]

        return wxver < [4, 1, 0]


    @staticmethod
    def displayAttribues():
        """Used within ``__init__`` methods of ``WXGLCanvasTarget``
        sub-classes.

        Return a dict to be passed as keyword arguments to the
        ``wx.glcanvas.GLCanvas.__init__`` method, defining display attributes.
        The ``GLCanvas`` interface changed between wxWidgets 3.0.x and 3.1.x
        (roughly corresponding to wxPython 4.0.x and 4.1.x) - this method
        checks the wxPython version and returns a suitable set of arguments.
        """

        import wx
        import wx.glcanvas as wxgl

        # the format of wx.__version__ is not
        # consistent (e.g. "4.0.7.post2", "4.1.0", etc)
        try:
            version = '.'.join(wx.__version__.split('.')[:3])
        except Exception:
            version = '4.0.0'

        # Use new API for 4.1.0 and newer
        if fslversion.compareVersions(version, '4.1.0') >= 0:
            attrs = wxgl.GLAttributes()
            attrs.MinRGBA(8, 8, 8, 8) \
                 .DoubleBuffer()      \
                 .Depth(24)           \
                 .Stencil(4)          \
                 .EndList()
            kwargs = {'dispAttrs' : attrs}

        else:
            attrs = [wxgl.WX_GL_RGBA,
                     wxgl.WX_GL_DOUBLEBUFFER,
                     wxgl.WX_GL_STENCIL_SIZE, 4,
                     wxgl.WX_GL_DEPTH_SIZE,   24,
                     0,
                     0]
            kwargs = {'attribList' : attrs}
        return kwargs


    def __init__(self):
        """Create a ``WXGLCanvasTarget``. """

        import wx

        context = getGLContext()

        # If we are on OSX, and using the Apple Software
        # Renderer (e.g. in a virtual machine), then it
        # seems that we have to have a separate context
        # for each display. If we don't, then strange
        # refresh problems will occur.
        if platform.system() == 'Darwin' and \
           'software' in GL_RENDERER.lower():

            log.debug('Creating separate GL context for '
                      'WXGLCanvasTarget {}'.format(id(self)))

            context = GLContext(other=context, target=self)

        self.__glReady           = False
        self.__freezeDraw        = False
        self.__freezeSwapBuffers = False
        self.__context           = context

        if WXGLCanvasTarget.canToggleHighDPI():
            self.__dpiscale = 1.0
        else:
            self.__dpiscale = self.GetContentScaleFactor()

        self.Bind(wx.EVT_PAINT,            self.__onPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.__onEraseBackground)


    def destroy(self):
        """Must be called when this WXGLCanvasTarget is no longer in use.
        Clears the GL rendering context target.
        """
        self.__context.setTarget(None)
        self.__context = None


    @property
    def destroyed(self):
        """Returns ``True`` if :meth:`destroy` has been called, ``False``
        otherwise.
        """
        return self.__context is None


    def __onEraseBackground(self, ev):
        """Called on ``wx.EVT_ERASE_BACKGROUND`` events. Does nothing. """
        pass


    def __onPaint(self, ev):
        """Called on ``wx.EVT_PAINT`` events. Schedules :meth:`Refresh`
        to be called on the idle loop.
        """

        def doRefresh():
            if fwidgets.isalive(self):
                self.Refresh()

        # GL canvases do need to be refreshed
        # on EVT_PAINT events. If they are not,
        # the canvas will be corrupted.
        if not self.__freezeDraw:
            idle.idle(doRefresh)


    def _initGL(self):
        """This method should perform any OpenGL data initialisation required
        for rendering. Must be implemented by subclasses.
        """
        raise NotImplementedError()


    def getAnnotations(self):
        """Must be provided by subclasses."""
        raise NotImplementedError()


    def canvasToWorld(self, xpos, ypos):
        """Convert X/Y pixel coordinates into a location in the display
        coordinate system. Must be provided by subclasses.
        """
        raise NotImplementedError()


    def worldToCanvas(self, pos):
        """Convert a location in the display coordinate system into X/Y pixel
        coordinates. Must be provided by subclasses.
        """
        raise NotImplementedError()


    def _draw(self, *a):
        """This method should implement the OpenGL drawing logic - it must be
        implemented by subclasses.

        .. note:: When runing with an on-screen display, this method should
                  never be called directly - call the :meth:`Refresh` method
                  instead.
        """
        raise NotImplementedError()


    def __realDraw(self, *a):
        """Called when the canvas needs to be refreshed.

        This method calls :meth:`_initGL` if it has not already been called.
        Otherwise, it calls the subclass :meth:`_draw` method.
        """

        # The only purpose of __realDraw is to
        # make sure that _initGL has been called
        # before the first call to _draw.  So
        # after initGL has been called, we replace
        # this method (__realDraw) and _draw
        # with drawWrapper. This wrapper calls
        # the original _draw method (provided by
        # subclasses), and manages GL flushing
        # and front/back buffer swaps. It also
        # honours FreezeDraw and FreezeSwapBuffers.
        subClassDraw = self._draw

        import OpenGL.GL as gl

        def drawWrapper(*a, **kwa):

            if self.destroyed:
                return

            if not self.__freezeDraw:
                subClassDraw(*a, **kwa)

            if not self.__freezeSwapBuffers:

                # If a draw didn't occur above,
                # this canvas may not have been
                # set as the target for the GL
                # context.
                if not self.__freezeDraw:
                    self._setGLContext()
                self.SwapBuffers()

            # If not swapping the front/back
            # buffers immediately after a draw,
            # make sure we flush all recent GL
            # operations, otherwise we may lose
            # them.
            elif not self.__freezeDraw:
                gl.glFlush()

        def doInit(*a):

            import wx

            try:
                self.__glReady = True
                self._initGL()

                self.__realDraw = drawWrapper
                self.__draw     = drawWrapper
                self._draw()

            # Just in case this canvas
            # was destroyed before it
            # had a chance to be drawn
            # on - wxpython raises a
            # RuntimeError on attempts
            # to use deleted wx objects
            except RuntimeError:
                pass

        if not self.__glReady:
            import wx
            wx.CallAfter(doInit)


    def _setGLContext(self):
        """Configures the GL context for drawing to this canvas.

        This method should be called before any OpenGL operations related to
        this canvas take place (e.g. texture/data creation, drawing, etc).
        """
        if not (fwidgets.isalive(self) and self.IsShownOnScreen()):
            return False

        log.debug('Setting context target to {} ({})'.format(
            type(self).__name__, id(self)))

        return self.__context.setTarget(self)


    def GetSize(self):
        """Returns the current canvas size. """
        return self.GetClientSize().Get()


    def GetContentScaleFactor(self):
        """Overrides ``wx.Window.GetContentScaleFactor``.

        Calls the base class implementation, except where wxpython 3.0.2.0 is
        being used, as the method does not exist in that version. In this
        case, 1.0 is returned.
        """
        try:
            return float(super().GetContentScaleFactor())
        except AttributeError:
            return 1.0


    def GetScale(self):
        """Returns the current DPI scaling factor. """

        scale = self.GetContentScaleFactor()

        # Reset scaling factor in case the canvas
        # window has moved between displays with
        # different scaling factors
        if scale == 1 and self.__dpiscale != 1:
            self.EnableHighDPI(False)

        return self.__dpiscale


    def GetScaledSize(self):
        """Returns the current canvas size, scaled by the current DPI scaling
        factor.
        """
        w, h = self.GetSize()
        s    = self.GetScale()

        return int(round(w * s)), int(round(h * s))


    def Refresh(self, *a):
        """Triggers a redraw via the :meth:`_draw` method. """
        self.__realDraw()


    def FreezeDraw(self):
        """*Freezes* updates to the canvas. See :meth:`ThawDraw`. """
        self.__freezeDraw = True


    def ThawDraw(self):
        """Unfreezes canvas updates. See :meth:`FreezeDraw`. """
        self.__freezeDraw = False


    def FreezeSwapBuffers(self):
        """*Freezes* canvas fron/back buffer swaps, but not canvas drawing.
        See :meth:`ThawSwapBuffers`.
        """
        self.__freezeSwapBuffers = True


    def ThawSwapBuffers(self):
        """Unfreezes canvas fron/back buffer swaps. See
        :meth:`FreezeSwapBuffers`.
        """
        self.__freezeSwapBuffers = False


    def SwapBuffers(self):
        """Overrides ``wx.GLCanvas.SwapBuffers``. Calls that method, but
        only if ``FreezeSwapBuffers`` is not active.
        """
        if not self.__freezeSwapBuffers:
            if self._setGLContext():
                super(WXGLCanvasTarget, self).SwapBuffers()


    def EnableHighDPI(self, enable=True):
        """Attempts to enable/disable high-resolution rendering.
        """

        # We don't necessarily need to
        # enable high-DPI support - see
        # __init__.
        if not WXGLCanvasTarget.canToggleHighDPI():
            return

        if not self._setGLContext():
            return

        self.__dpiscale = 1.0

        # If the display can't scale,
        # (scale == 1) there's no point
        # in enabling it.
        scale  = self.GetContentScaleFactor()
        enable = enable and scale > 1

        # on macOS, we have to set
        # scaling on the GL canvas
        try:
            import objc
            nsview = objc.objc_object(c_void_p=self.GetHandle())
            nsview.setWantsBestResolutionOpenGLSurface_(enable)

        # objc library not present
        except ImportError:
            return

        if enable: self.__dpiscale = scale
        else:      self.__dpiscale = 1.0


    def getBitmap(self):
        """Return a (width*height*4) shaped numpy array containing the
        rendered scene as an RGBA bitmap.
        """
        import OpenGL.GL as gl
        import numpy     as np

        self._setGLContext()

        width, height = self.GetScaledSize()

        # Make sure we're reading
        # from the front buffer
        gl.glReadBuffer(gl.GL_FRONT_LEFT)

        bmp = gl.glReadPixels(
            0, 0,
            width, height,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE)

        bmp = np.frombuffer(bmp, dtype=np.uint8)
        bmp = bmp.reshape((height, width, 4))
        bmp = np.flipud(bmp)

        return bmp
