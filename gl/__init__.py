#!/usr/bin/env python
#
# __init__.py - The fsl.fsleyes.gl package contains OpenGL data and
# rendering stuff for fsleyes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""OpenGL data and rendering stuff for fsleyes.

This package contains the OpenGL rendering code used by FSLEyes. It contains a
number of modules which contain logic that is independent of the available
OpenGL version (e.g. the :class:`.SliceCanvas` class), and also contains a
number of sub-packages (currently two) which contain OpenGL-version-dependent
modules that are used by the version independent ones.

The available OpenGL API version can only be determined once an OpenGL context
has been created, and a display is available for rendering. Therefore, the
package-level :func:`bootstrap` function is called by the version-independent
module classes as needed, to dynamically determine which version-dependent
modules should be loaded.  Users of this package should not need to worry
about any of this - just instantiate the GUI classes provided by the
version-independent modules (e.g. the :class:`.LightBoxCanvas` class) as you
would any other :mod:`wx` widget.

Two methods of OpenGL usage are supported:

  - On-screen display of a scene using a :class:`wx.glcanvas.GLCanvas` canvas.

  - Off-screen renering of a scene using OSMesa.

Two super classes are provided for each of these cases:

 - The :class:`WXGLCanvasTarget` class for on-screen rendering using
   :mod:`wx`.

 - The :class:`OSMesaCanvasTarget` class for off-screen rendering using
   OSMesa.

After the :func:`boostrap` function has been called, the following
package-level attributes will be available:

 - ``GL_VERSION``:         A string containing the target OpenGL version, in 
                           the format ``major.minor``, e.g. ``2.1``.

 - ``glvolume_funcs``:     The version-specific module containing functions for
                           rendering :class:`.GLVolume` instances.

 - ``glrgbvector_funcs``:  The version-specific module containing functions for
                           rendering :class:`.GLRGBVector` instances.

 - ``gllinevector_funcs``: The version-specific module containing functions for
                           rendering :class:`.GLLineVector` instances.

 - ``glmodel_funcs``:      The version-specific module containing functions for
                           rendering :class:`.GLModel` instances. 
"""

import logging 
import os


log = logging.getLogger(__name__)


# When running under X, indirect rendering fails for
# unknown reasons, so I'm forcing direct rendering.
# If direct rendering is not available, I don't know
# what to do.
os.environ.pop('LIBGL_ALWAYS_INDIRECT', None)


import OpenGL


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


# Using PyOpenGL 3.1 (and OSX Mavericks 10.9.4 on a MacbookPro11,3), the
# OpenGL.contextdata.setValue method throws 'unhashable type' TypeErrors
# unless we set STORE_POINTERS to False. I don't know why.
if os.environ.get('PYOPENGL_PLATFORM', None) == 'osmesa':
    OpenGL.STORE_POINTERS = False


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
    the :mod:`~fsl.fsleyes.gl` package.  The version-independent modules may
    then simply access these version-dependent modules through this module.

    :arg glVersion: A tuple containing the desired (major, minor) OpenGL API
                    version to use. If ``None``, the best possible API version
                    will be used.
    """

    import sys
    import OpenGL.GL         as gl
    import OpenGL.extensions as glexts
    import gl14
    import gl21

    thismod = sys.modules[__name__]

    if hasattr(thismod, '_bootstrapped'):
        return 

    if glVersion is None:
        glVer        = gl.glGetString(gl.GL_VERSION).split()[0]
        major, minor = map(int, glVer.split('.'))
    else:
        major, minor = glVersion

    glpkg = None

    if   major >= 2 and minor >= 1:
        verstr = '2.1'
        glpkg  = gl21
    elif major >= 1 and minor >= 4:
        verstr = '1.4'
        glpkg  = gl14
    else: raise RuntimeError('OpenGL 1.4 or newer is required')

    # The gl21 implementation depends on a
    # few extensions - if they're not present,
    # fall back to the gl14 implementation
    if glpkg == gl21:


        # List any GL21 extensions here
        exts = ['GL_EXT_framebuffer_object']
        
        if not all(map(glexts.hasExtension, exts)):
            log.debug('One of these OpenGL extensions is '
                      'not available: [{}]. Falling back '
                      'to an older OpenGL implementation.'
                      .format(', '.join(exts))) 
            verstr = '1.4'
            glpkg = gl14

    # If using GL14, and the ARB_vertex_program
    # and ARB_fragment_program extensions are
    # not present, we're screwed.
    if glpkg == gl14:
        
        exts = ['GL_EXT_framebuffer_object',
                'GL_ARB_vertex_program',
                'GL_ARB_fragment_program']
        
        if not all(map(glexts.hasExtension, exts)):
            raise RuntimeError('One of these OpenGL extensions is '
                               'not available: [{}]. This software '
                               'cannot run on the available graphics '
                               'hardware.'.format(', '.join(exts)))

        # Spline interpolation is not currently
        # available in the GL14 implementation
        import fsl.fsleyes.displaycontext as dc
        dc.VolumeOpts   .interpolation.removeChoice('spline')
        dc.RGBVectorOpts.interpolation.removeChoice('spline')
        

    renderer = gl.glGetString(gl.GL_RENDERER)
    log.debug('Using OpenGL {} implementation with renderer {}'.format(
        verstr, renderer))

    # If we're using a software based renderer,
    # reduce the default performance settings
    # 
    # There doesn't seem to be any quantitative
    # method for determining whether we are using
    # software-based rendering, so a hack is
    # necessary. 
    if 'software' in renderer.lower():
        
        log.debug('Software-based rendering detected - '
                  'lowering default performance settings.')

        import fsl.fsleyes.displaycontext as dc

        dc.SceneOpts.performance.setConstraint(None, 'default', 2)

        # And disable some fancy options - spline
        # may have been disabled above, so absorb
        # the ValueError if it occurs

        # TODO Remove this code duplication
        try:
            dc.VolumeOpts   .interpolation.removeChoice('spline')
            dc.RGBVectorOpts.interpolation.removeChoice('spline')
            
        except ValueError: pass

    thismod.GL_VERSION         = verstr
    thismod.glvolume_funcs     = glpkg.glvolume_funcs
    thismod.glrgbvector_funcs  = glpkg.glrgbvector_funcs
    thismod.gllinevector_funcs = glpkg.gllinevector_funcs
    thismod.glmodel_funcs      = glpkg.glmodel_funcs
    thismod.gllabel_funcs      = glpkg.gllabel_funcs
    thismod._bootstrapped      = True


def getWXGLContext(parent=None):
    """Create and return a GL context object for rendering to a
    :class:`wx.glcanvas.GLCanvas` canvas.

    If a context object has already been created, it is returned.
    Otherwise, one is created and returned. In the latter case,
    the ``parent`` parameter must be a visible :mod:`wx` object.

    In either case, this function returns two values:
    
      - A :class:`wx.glcanvas.GLContext` instance
    
      - If a context instance has previously been created, the second
        return value is ``None``. Other a dummy
        :class:`wx.glcanvas.GLCanvas` instance is returned. This canvas
        should be destroyed by the caller when it is safe to do so. This
        seems to primarily be a problem under Linux/GTK - it does not
        seem to be possible to destroy the dummy canvas immediately after
        creating the context. So the calling code needs to destroy it
        at some point in the future (possibly after another, real
        GLCanvas has been created, and set as the context target).
    """

    import sys
    import wx
    import wx.glcanvas as wxgl

    thismod = sys.modules[__name__]

    # A context has already been created
    if hasattr(thismod, '_wxGLContext'):
        return thismod._wxGLContext, None

    if parent is None or not parent.IsShown():
        raise RuntimeError('A visible WX object is required '
                           'to create a GL context')

    # We can't create a wx GLContext without
    # a wx GLCanvas. But we can create a
    # dummy one, and destroy it after the
    # context has been created. Destroying
    # the canvas is the responsibility of the
    # calling code.

    # There's something wrong with wxPython's
    # GLCanvas (on OSX at least) - the pixel
    # format attributes have to be set on the
    # *first* GLCanvas that is created -
    # setting them on subsequent canvases will
    # have no effect. But if you set them on
    # the first canvas, all canvases that are
    # subsequently created will inherit the
    # same properties.
    attribs = [wxgl.WX_GL_RGBA,
               wxgl.WX_GL_DOUBLEBUFFER,
               wxgl.WX_GL_STENCIL_SIZE, 4,
               wxgl.WX_GL_DEPTH_SIZE,   8,
               0,
               0] 

    canvas = wxgl.GLCanvas(parent, attribList=attribs)
    canvas.SetSize((0, 0))

    # The canvas must be visible before we are
    # able to set it as the target of the GL context
    canvas.Show(True)
    canvas.Refresh()
    canvas.Update()
    wx.Yield()

    thismod._wxGLContext = wxgl.GLContext(canvas)
    thismod._wxGLContext.SetCurrent(canvas)

    return thismod._wxGLContext, canvas

    
def getOSMesaContext():
    """Create and return a GL context object for off-screen rendering using
    OSMesa.
    """

    import sys    
    import OpenGL.GL              as gl
    import OpenGL.raw.osmesa.mesa as osmesa
    import OpenGL.arrays          as glarrays

    thismod = sys.modules[__name__]
    
    if not hasattr(thismod, '_osmesaGLContext'):

        # We follow the same process as for the
        # wx.glcanvas.GLContext, described above 
        dummy = glarrays.GLubyteArray.zeros((640, 480, 43))
        thismod._osmesaGLContext = osmesa.OSMesaCreateContextExt(
            gl.GL_RGBA, 8, 4, 0, None)
        osmesa.OSMesaMakeCurrent(thismod._osmesaGLContext,
                                 dummy,
                                 gl.GL_UNSIGNED_BYTE,
                                 640,
                                 480) 

    return thismod._osmesaGLContext 


class OSMesaCanvasTarget(object):
    """Superclass for canvas objects which support off-screen rendering using
    OSMesa.
    """
    
    def __init__(self, width, height, bgColour=(0, 0, 0, 255)):
        """Creates an off-screen buffer to be used as the render target.

        :arg width:    Width in pixels
        :arg height:   Height in pixels
        :arg bgColour: Background colour as an RGBA tuple
                       (e.g. (255, 255, 255, 255))
        """
        import OpenGL.arrays as glarrays 
        self._width    = width
        self._height   = height 
        self._bgColour = bgColour 
        self._buffer   = glarrays.GLubyteArray.zeros((height, width, 4))

        
    def _getSize(self):
        """Returns a tuple containing the canvas width and height."""
        return self._width, self._height

        
    def _setGLContext(self):
        import OpenGL.GL              as gl
        import OpenGL.raw.osmesa.mesa as osmesa
        """Configures the GL context to render to this canvas. """
        osmesa.OSMesaMakeCurrent(getOSMesaContext(),
                                 self._buffer,
                                 gl.GL_UNSIGNED_BYTE,
                                 self._width,
                                 self._height)
        return True

        
    def _refresh(self, *a):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass

        
    def _postDraw(self):
        """Does nothing, see :method:`_refresh`."""
        pass


    def _draw(self, *a):
        """Must be provided by subclasses."""
        raise NotImplementedError()


    def draw(self):
        """Calls the :meth:`_draw` method, which must be provided by
        subclasses.
        """

        import OpenGL.GL as gl
        
        self._initGL()
        self._setGLContext()
        gl.glClearColor(*self._bgColour)
        self._draw()

        
    def getBitmap(self):
        """Return a (width*height*4) shaped numpy array containing the
        rendered scene as an RGBA bitmap. The bitmap will be full of
        zeros if the scene has not been drawn (via a call to
        :meth:`draw`).
        """
        import OpenGL.GL        as gl
        import numpy            as np

        self._setGLContext()
        
        bmp = gl.glReadPixels(
            0, 0,
            self._width, self._height,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE)
        
        bmp = np.fromstring(bmp, dtype=np.uint8)
        bmp = bmp.reshape((self._height, self._width, 4))
        bmp = np.flipud(bmp)

        return bmp


    def saveToFile(self, filename):
        """Saves the contents of this canvas as an image, to the specified
        file.
        """
        import matplotlib.image as mplimg
        mplimg.imsave(filename, self.getBitmap()) 


class WXGLCanvasTarget(object):
    """Superclass for :class:`wx.glcanvas.GLCanvas` objects objects.

    It is assumed that subclasses of this superclass are also subclasses of
    :class:`wx.glcanvas.GLCanvas`
    """


    def __init__(self):
        """Binds :attr:`wx.EVT_PAINT` events to the :meth:`_mainDraw` method.
        """

        import wx

        self._glReady = False
        self.Bind(wx.EVT_PAINT, self._mainDraw)
    

    def _initGL(self):
        """Must be implemented by subclasses.

        This method should perform any OpenGL data initialisation required for
        rendering.
        """
        raise NotImplementedError()


    def _draw(self, *a):
        """Must be implemented by subclasses.

        This method should implement the OpenGL drawing logic.
        """
        raise NotImplementedError()
 
        
    def _mainDraw(self, *a):
        """Called on :attr:`wx.EVT_PAINT` events.

        This method calls :meth:`_initGL` if it has not already been called.
        Otherwise, it calls the subclass :meth:`_draw` method.
        """

        import wx

        def doInit(*a):
            self._initGL()
            self._glReady = True
            self._draw()

        if not self._glReady:
            wx.CallAfter(doInit)
            return

        self._draw()

        
    def _getSize(self):
        """Returns the current canvas size. """
        return self.GetClientSize().Get()

        
    def _setGLContext(self):
        """Configures the GL context for drawing to this canvas.

        This method should be called before any OpenGL operations related to
        this canvas take place (e.g. texture/data creation, drawing, etc).
        """
        if not self.IsShownOnScreen(): return False

        log.debug('Setting context target to {} ({})'.format(
            type(self).__name__, id(self)))
        
        getWXGLContext()[0].SetCurrent(self)
        return True

        
    def _refresh(self, *a):
        """Triggers a redraw via the :meth:`_draw` method."""
        self.Refresh()

        
    def _postDraw(self):
        """Called after the scene has been rendered. Swaps the front/back
        buffers. 
        """
        self.SwapBuffers()

        
    def getBitmap(self):
        """Return a (width*height*4) shaped numpy array containing the
        rendered scene as an RGBA bitmap. 
        """
        import OpenGL.GL        as gl
        import numpy            as np

        self._setGLContext()

        width, height = self._getSize()

        # Make sure we're reading
        # from the front buffer
        gl.glReadBuffer(gl.GL_FRONT_LEFT)
        
        bmp = gl.glReadPixels(
            0, 0,
            width, height,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE)
        
        bmp = np.fromstring(bmp, dtype=np.uint8)
        bmp = bmp.reshape((height, width, 4))
        bmp = np.flipud(bmp)

        return bmp        
