#!/usr/bin/env python
#
# program.py - The ARBPShader class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ARBPShader` class, which encapsulates
an OpenGL shader program written according to the ``ARB_vertex_program``
and ``ARB_fragment_program`` extensions.
"""


from __future__ import division

import logging

import numpy                          as np

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.memoize              as memoize
from . import                            parse


log = logging.getLogger(__name__)


class ARBPShader(object):
    """The ``ARBPShader`` class encapsulates an OpenGL shader program
    written according to the ``ARB_vertex_program`` and
    ``ARB_fragment_program`` extensions. It parses and compiles vertex
    and fragment program code, and provides methods to load/unload
    the program, and to set vertex/fragment program parameters and vertex
    attributes.


    The ``ARBPShader`` class assumes that vertex/fragment program source
    has been written to work with the functions defined in the
    :mod:`.arbp.parse` module, which allows programs to be written so that
    parameter, vertex attribute and texture locations do not have to be hard
    coded in the source.  Texture locations may be specified in
    :meth:`__init__`, and parameter/vertex attribute locations are
    automatically assigned by the ``ARBPShader``.


    The following methods are available on an ``ARBPShader`` instance:

    .. autosummary::
       :nosignatures:

       load
       unload
       destroy
       setVertParam
       setFragParam
       setAttr

    Typcical usage of an ``ARBPShader`` will look something like the
    following::

        vertSrc = 'vertex shader source'
        fragSrc = 'vertex shader source'

        # You must specify the texture unit
        # assignments at creation time.
        textures = {
            'colourMapTexture' : 0,
            'dataTexture'      : 1
        }

        program = GLSLShader(vertSrc, fragSrc, textures)

        # Load the program, and
        # enable program attributes
        # (texture coordinates)
        program.load()
        progra.loadAtts()

        # Set some parameters
        program.setVertParam('transform', np.eye(4))
        program.setFragParam('clipping',  [0, 1, 0, 0])

        # Create and set vertex attributes
        vertices, normals = createVertices()

        program.setAttr('normals', normals)

        # Draw the scene
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(vertices))

        # Clear the GL state
        program.unloadAtts()
        program.unload()

        # Delete the program when
        # it is no longer needed
        program.destroy()


    .. warning:: The ``ARBPShader`` uses texture coordinates to pass vertex
                 attributes to the shader programs. Therefore, if you are using
                 an ``ARBPShader`` you cannot directly use texture coordinates.


    See also the :class:`.GLSLShader`, which provides similar functionality for
    GLSL shader programs.
    """

    def __init__(self, vertSrc, fragSrc, textureMap=None):
        """Create an ``ARBPShader``.

        :arg vertSrc:    Vertex program source.

        :arg fragSrc:    Fragment program source.

        :arg textureMap: A dictionary of ``{name : int}`` mappings, specifying
                         the texture unit assignments.
        """

        decs = parse.parseARBP(vertSrc, fragSrc)

        vParams = decs['vertParam']
        fParams = decs['fragParam']

        if len(vParams) > 0: vParams, vLens = zip(*vParams)
        else:                vParams, vLens = [], []
        if len(fParams) > 0: fParams, fLens = zip(*fParams)
        else:                fParams, fLens = [], []

        vLens = {name : length for name, length in zip(vParams, vLens)}
        fLens = {name : length for name, length in zip(fParams, fLens)}

        self.vertParams    = vParams
        self.vertParamLens = vLens
        self.fragParams    = fParams
        self.fragParamLens = fLens
        self.textures      = decs['texture']
        self.attrs         = decs['attr']

        poses = self.__generatePositions(textureMap)
        vpPoses, fpPoses, texPoses, attrPoses = poses

        self.vertParamPositions = vpPoses
        self.fragParamPositions = fpPoses
        self.texturePositions   = texPoses
        self.attrPositions      = attrPoses

        vertSrc, fragSrc = parse.fillARBP(vertSrc,
                                          fragSrc,
                                          self.vertParamPositions,
                                          self.vertParamLens,
                                          self.fragParamPositions,
                                          self.fragParamLens,
                                          self.texturePositions,
                                          self.attrPositions)

        vp, fp = self.__compile(vertSrc, fragSrc)

        self.vertexProgram   = vp
        self.fragmentProgram = fp

        log.memory('{}.init({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message. """
        if log:
            log.memory('{}.del({})'.format(type(self).__name__, id(self)))


    def destroy(self):
        """Deletes all GL resources managed by this ``ARBPShader``. """
        arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))


    def load(self):
        """Loads the shader program. """
        gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB)
        gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                               self.vertexProgram)
        arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                               self.fragmentProgram)

    def loadAtts(self):
        """Enables texture coordinates for all shader program attributes. """
        for attr in self.attrs:
            texUnit = self.__getAttrTexUnit(attr)

            gl.glClientActiveTexture(texUnit)
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)


    def unload(self):
        """Unloads the shader program. """
        gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
        gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)


    def unloadAtts(self):
        """Disables texture coordinates on all texture units. """
        for attr in self.attrs:
            texUnit = self.__getAttrTexUnit(attr)

            gl.glClientActiveTexture(texUnit)
            gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)


    @memoize.Instanceify(memoize.skipUnchanged)
    def setVertParam(self, name, value):
        """Sets the value of the specified vertex program parameter.

        .. note:: It is assumed that the value is either a sequence of length
                  4 (for vector parameters), or a ``numpy`` array of shape
                  ``(n, 4)`` (for matrix parameters).

        .. note:: This method is decorated by the
                  :func:`.memoize.skipUnchanged` decorator, which returns
                  ``True`` if the value was changed, and ``False`` otherwise.
        """

        pos   = self.vertParamPositions[name]
        value = np.array(value, dtype=np.float32).ravel('F')
        nrows = len(value) // 4

        log.debug('Setting vertex parameter {} = {}'.format(name, value))

        for i in range(nrows):
            row = value[i * 4: i * 4 + 4]
            arbvp.glProgramLocalParameter4fARB(
                arbvp.GL_VERTEX_PROGRAM_ARB, pos + i,
                row[0], row[1], row[2], row[3])


    @memoize.Instanceify(memoize.skipUnchanged)
    def setFragParam(self, name, value):
        """Sets the value of the specified vertex program parameter. See
        :meth:`setVertParam` for infomration about possible values.

        .. note:: This method is decorated by the
                  :func:`.memoize.skipUnchanged` decorator, which returns
                  ``True`` if the value was changed, and ``False`` otherwise.
        """
        pos   = self.fragParamPositions[name]
        value = np.array(value, dtype=np.float32).ravel('F')
        nrows = len(value) // 4

        log.debug('Setting fragment parameter {} = {}'.format(name, value))

        for i in range(nrows):
            row = value[i * 4: i * 4 + 4]
            arbfp.glProgramLocalParameter4fARB(
                arbfp.GL_FRAGMENT_PROGRAM_ARB, pos + i,
                row[0], row[1], row[2], row[3])


    def setAttr(self, name, value):
        """Sets the value of the specified vertex attribute. Each vertex
        attribute is mapped to a texture coordinate. It is assumed that
        the given value is a ``numpy`` array of shape ``(n, l)``, where
        ``n`` is the number of vertices being drawn, and ``l`` is the
        number of components in each vertex attribute coordinate.
        """
        texUnit = self.__getAttrTexUnit(name)
        size    = value.shape[1]
        value   = np.array(value, dtype=np.float32)

        log.debug('Setting vertex attribute {} = [{} * {}]'.format(
            name, value.shape[0], size))

        value = value.ravel('C')

        gl.glClientActiveTexture(texUnit)
        gl.glTexCoordPointer(size, gl.GL_FLOAT, 0, value)


    def __getAttrTexUnit(self, attr):
        """Returns the texture unit identifier which corresponds to the named
        vertex attribute.
        """

        pos     = self.attrPositions[attr]
        texUnit = 'GL_TEXTURE{}'.format(pos)
        texUnit = getattr(gl, texUnit)

        return texUnit


    def __generatePositions(self, textureMap=None):
        """Called by :meth:`__init__`. Generates positions for vertex/fragment
        program parameters and vertex attributes.

        The lengths of each vertex/fragment parameter are known (see
        :mod:`.arbp.parse`), so these parameters are set up to be sequentially
        stored in the program parameter memory.

        Vertex attributes are passed to the vertex program as texture
        coordinates.

        If texture units were not specified in ``__init__``, texture units are
        also automatically assigned to each texture used in the fragment
        program.
        """

        vpPoses   = {}
        fpPoses   = {}
        texPoses  = {}
        attrPoses = {}

        # Vertex parameters
        pos = 0
        for name in self.vertParams:
            vpPoses[name]  = pos
            pos           += self.vertParamLens[name]

        # Fragment parameters
        pos = 0
        for name in self.fragParams:
            fpPoses[name]  = pos
            pos           += self.fragParamLens[name]

        # Vertex attributes
        for i, name in enumerate(self.attrs):
            attrPoses[name]  = i

        # Texture positions. If the caller did
        # not provide a texture map in __init__,
        # we'll generate some positions.
        if textureMap is None:

            names    = self.textures
            poses    = list(range(len(names)))
            texPoses = {n : p for n, p in zip(names, poses)}
        else:
            texPoses = dict(textureMap)

        return vpPoses, fpPoses, texPoses, attrPoses


    def __compile(self, vertSrc, fragSrc):
        """Called by :meth:`__init__`. Compiles the vertex and fragment
        programs and returns references to the compiled programs.

        """

        gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB)
        gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        fragProg = arbfp.glGenProgramsARB(1)
        vertProg = arbvp.glGenProgramsARB(1)

        # Make sure the source is plain
        # ASCII - not unicode
        vertSrc = vertSrc.encode('ascii')
        fragSrc = fragSrc.encode('ascii')

        # vertex program
        try:
            arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB, vertProg)
            arbvp.glProgramStringARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                                     arbvp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                     len(vertSrc),
                                     vertSrc)

        except:

            position = gl.glGetIntegerv(arbvp.GL_PROGRAM_ERROR_POSITION_ARB)
            message  = gl.glGetString(  arbvp.GL_PROGRAM_ERROR_STRING_ARB)
            message  = message.decode('ascii')

            raise RuntimeError('Error compiling vertex program '
                               '({}): {}'.format(position, message))

        # fragment program
        try:
            arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                   fragProg)

            arbfp.glProgramStringARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                     arbfp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                     len(fragSrc),
                                     fragSrc)
        except:
            position = gl.glGetIntegerv(arbfp.GL_PROGRAM_ERROR_POSITION_ARB)
            message  = gl.glGetString(  arbfp.GL_PROGRAM_ERROR_STRING_ARB)
            message  = message.decode('ascii')

            raise RuntimeError('Error compiling fragment program '
                               '({}): {}'.format(position, message))

        gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
        gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        return vertProg, fragProg
