#!/usr/bin/env python
#
# filter.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Filter` class, which provides an interface
to loading and running simple filter shader programs, which require a
:class:`.Texture2D` as their input.
"""


import collections


import OpenGL.GL                          as gl

from   fsl.utils.platform import platform as fslplatform
import fsleyes.gl.shaders                 as shaders


GL14_CONSTANTS = collections.defaultdict(dict, {
    'smooth' : ['kernSize']
})
"""This dictionary contains the names of any constant parameters that are
required by GL14 filter implementations. It is used by the :meth:`Filter.set`
method.

The :meth:`Filter.set` method allows both uniform and constant paramters to be
updated, but when a constant parameter is updated, the shader needs to be
recompiled.
"""


class Filter(object):
    """A ``Filter`` object encapsulates a shader program which applies some
    sort of image filter to a :class:`.Texture2D`.

    All filters use the same vertex shader, which is called
    ``filter_vert.glsl`` or ``filter_vert.prog``.

    Filter fragment shaders are assumed to have the name
    ``filter_[name]_frag.glsl`` or ``filter_[name]_frag.prog``, where
    ``[name]`` is the name of the filter that can be passed to
    :meth:`__init__`.

    Filter fragment shaders must define the following varyings/uniforms/
    attributes:

      - ``texture``      - the 2D texture which contains the filter input
      - ``fragTexCoord`` - The texture coordinate, as passed through from the
                           vertex shader.

    Other settable filter parameters must be declared as uniforms, and can be
    set via the :meth:`set` method.
    """


    def __init__(self, filterName, texture):
        """Create a ``Filter``.

        :arg filterName: Name of the filter to create.

        :arg texture:    Number of the texture unit that the filter input
                         texture will be bound to. This must be specified
                         when the shader program is compiled, to support
                         OpenGL 1.4.
        """

        basename        = filterName
        filterName      = 'filter_{}'.format(filterName)
        vertSrc         = shaders.getVertexShader( 'filter')
        fragSrc         = shaders.getFragmentShader(filterName)
        self.__texture  = texture
        self.__basename = basename

        if float(fslplatform.glVersion) >= 2.1:
            self.__shader = shaders.GLSLShader(vertSrc, fragSrc)
        else:
            constants = {n : 1 for n in GL14_CONSTANTS[basename]}
            self.__shader = shaders.ARBPShader(
                vertSrc,
                fragSrc,
                shaders.getShaderDir(),
                {'texture' : texture},
                constants=constants)


    def destroy(self):
        """Must be called when this ``Filter`` is no longer needed. Destroys
        the shader program.
        """
        self.__shader.destroy()
        self.__shader = None


    def set(self, **kwargs):
        """Set filter parameters. This method must be called before
        :meth:`apply` or :meth:`osApply` can be called, even if no parameters
        need to be set.

        The filter parameters vary depending on the specific filter that is
        used.
        """

        shader   = self.__shader
        texture  = self.__texture
        basename = self.__basename

        shader.load()

        kwargs        = dict(kwargs)
        glver         = float(fslplatform.glVersion)
        needRecompile = False

        if glver >= 2.1:
            kwargs['texture'] = texture

        for name, value in kwargs.items():
            if glver >= 2.1:
                shader.set(name, value)
            else:
                if name in GL14_CONSTANTS[basename]:
                    needRecompile = (needRecompile or
                                     shader.setConstant(name, value))
                else:
                    shader.setFragParam(name, value)

        if needRecompile:
            shader.recompile()

        shader.unload()


    def apply(self,
              source,
              zpos,
              xmin,
              xmax,
              ymin,
              ymax,
              xax,
              yax,
              xform=None,
              **kwargs):
        """Apply the filter to the given ``source`` texture, and render the
        results according to the given bounds.

        :arg source:      :class:`.Texture2D` instance to apply the filter to
        :arg zpos:        Position along the Z axis, in the display coordinate
                          system.
        :arg xmin:        Minimum X axis coordinate.
        :arg xmax:        Maximum X axis coordinate.
        :arg ymin:        Minimum Y axis coordinate.
        :arg ymax:        Maximum Y axis coordinate.
        :arg xax:         Display space axis which maps to the horizontal
                          screen axis.
        :arg yax:         Display space axis which maps to the vertical screen
                          axis.
        :arg xform:       Transformation matrix to appply to vertices.

        All other keyword arguments are passed through to the
        :meth:`.Texture2D.draw` method of the ``source`` texture.
        """

        shader    = self.__shader
        vertices  = source.generateVertices(
            zpos, xmin, xmax, ymin, ymax, xax, yax, xform)
        texCoords = source.generateTextureCoords()

        shader.load()
        shader.loadAtts()
        shader.setAtt('texCoord', texCoords)

        if float(fslplatform.glVersion) >= 2.1:
            shader.setAtt('vertex', vertices)
            source.draw(**kwargs)
        else:
            source.draw(vertices=vertices, **kwargs)

        shader.unloadAtts()
        shader.unload()


    def osApply(self, source, dest, clearDest=True, **kwargs):
        """Apply the filter to the given ``source`` texture, rendering
        the results to the given ``dest`` texture.

        This method can be used for ping-ponging, by using two
        :class:`.RenderTexture` objects, and swapping the ``source`` and
        ``dest`` parameters on each iteration.

        :arg source:    :class:`.Texture2D` instance to apply the filter to
        :arg dest:      :class:`.RenderTexture` instance to render the result
                        to
        :arg clearDest: If ``True`` (the default), the ``dest`` texture is
                        cleared before the draw.

        All other arguments are passed to the :meth:`apply` method.
        """

        with dest.bound(0, 1, (0, 0, 0), (1, 1, 1)):
            if clearDest:
                gl.glClear(gl.GL_COLOR_BUFFER_BIT |
                           gl.GL_DEPTH_BUFFER_BIT |
                           gl.GL_STENCIL_BUFFER_BIT)
            self.apply(source, 0.5, 0, 1, 0, 1, 0, 1, **kwargs)
