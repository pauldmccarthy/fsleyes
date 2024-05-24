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

import re
import logging
import contextlib

import numpy                as np


from fsl.utils               import memoize
from fsleyes.gl.shaders.arbp import parse
from fsleyes.utils           import lazyimport


log = logging.getLogger(__name__)


gl      = lazyimport('OpenGL.GL',                      f'{__name__}.gl')
arbfp   = lazyimport('OpenGL.GL.ARB.fragment_program', f'{__name__}.arbfp')
arbvp   = lazyimport('OpenGL.GL.ARB.vertex_program',   f'{__name__}.arbvp')
gltypes = lazyimport('OpenGL.raw.GL._types',           f'{__name__}.gltypes')


class ARBPShader:
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
       loaded
       destroy
       setConstant
       recompile
       setVertParam
       setFragParam
       set
       setAtt
       setIndices
       draw

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

        program = ARBPShader(vertSrc, fragSrc, textures)

        # Load the program
        program.load()

        # Set some parameters
        program.set('transform', np.eye(4))
        program.set('clipping',  [0, 1, 0, 0])

        # Create and set vertex attributes
        vertices, normals = createVertices()

        program.setAtt('vertex', vertices)
        program.setAtt('normal', normals)

        # Draw the scene
        program.draw(gl.GL_TRIANGLES, vertices.shape[0])

        # Clear the GL state
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


    def __init__(self,
                 vertSrc,
                 fragSrc,
                 textureMap=None,
                 constants=None,
                 clean=True,
                 includePath=None):
        """Create an ``ARBPShader``.

        :arg vertSrc:     Vertex program source.

        :arg fragSrc:     Fragment program source.

        :arg textureMap:  A dictionary of ``{name : int}`` mappings, specifying
                          the texture unit assignments.

        :arg constants:   A dictionary of ``{name : values}`` mappings,
                          specifying any constant parameters required by the
                          programs. It is assumed that constant parameters are
                          shared by the vertex and fragment programs.

        :arg clean:       If ``True`` (the default), the vertex and fragment
                          program source is 'cleaned' before compilation - all
                          comments, empty lines, and unncessary spaces are
                          removed before compilation.

        :arg includePath: Path to a directory which contains any additional
                          files that may be included in the given source
                          files. Defaults to
                          :func:`fsleyes.gl.shaders.getShaderDir`.
        """

        if includePath is None:
            from fsleyes.gl.shaders import getShaderDir
            includePath = getShaderDir()

        decs = parse.parseARBP(vertSrc, fragSrc)

        vParams      = decs['vertParam']
        fParams      = decs['fragParam']
        constantDecs = decs['constant']

        if constants is None: constants      = {}
        if len(vParams) > 0:  vParams, vLens = zip(*vParams)
        else:                 vParams, vLens = [], []
        if len(fParams) > 0:  fParams, fLens = zip(*fParams)
        else:                 fParams, fLens = [], []

        vLens = {name : length for name, length in zip(vParams, vLens)}
        fLens = {name : length for name, length in zip(fParams, fLens)}

        self.vertexSource    = vertSrc
        self.fragmentSource  = fragSrc
        self.includePath     = includePath
        self.vertexProgram   = None
        self.fragmentProgram = None
        self.clean           = clean
        self.includePath     = includePath
        self.vertParams      = vParams
        self.vertParamLens   = vLens
        self.fragParams      = fParams
        self.fragParamLens   = fLens
        self.textures        = decs['texture']
        self.attrs           = decs['attr']
        self.constants       = constantDecs
        self.constantVals    = dict(constants)

        # See the setAtt method for
        # information about this dict
        self.attCache   = {}
        self.attsLoaded = False

        # The setIndices method caches an
        # index array which will then be
        # passed to glDrawElements in the
        # draw method
        self.indices = None

        poses = self.__generatePositions(textureMap)
        vpPoses, fpPoses, texPoses, attrPoses = poses

        self.vertParamPositions = vpPoses
        self.fragParamPositions = fpPoses
        self.texturePositions   = texPoses
        self.attrPositions      = attrPoses

        self.recompile()

        log.debug('{}.init({})'.format(type(self).__name__, id(self)))


    def __del__(self):
        """Prints a log message. """
        if log:
            log.debug('{}.del({})'.format(type(self).__name__, id(self)))


    def destroy(self):
        """Deletes all GL resources managed by this ``ARBPShader``. """

        if self.vertexProgram is not None:
            arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
        if self.fragmentProgram is not None:
            arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

        self.vertexProgram   = None
        self.fragmentProgram = None


    def recompile(self):
        """(Re-)generates the vertex and fragment program source code, and
        recompiles the programs.
        """

        # As we are compiling new
        # vertex/fragment programs,
        # we need to invalidate any
        # cached parameter values.
        # Constants are ok.
        self.setVertParam.invalidate()
        self.setFragParam.invalidate()

        vertSrc, fragSrc = parse.fillARBP(self.vertexSource,
                                          self.fragmentSource,
                                          self.vertParamPositions,
                                          self.vertParamLens,
                                          self.fragParamPositions,
                                          self.fragParamLens,
                                          self.constantVals,
                                          self.texturePositions,
                                          self.attrPositions,
                                          self.includePath)

        # Compile the new version, but
        # only discard the old version
        # if compilation succeeds
        vp, fp = self.__compile(vertSrc, fragSrc)

        self.destroy()
        self.vertexProgram   = vp
        self.fragmentProgram = fp


    def load(self):
        """Loads the shader program. """
        gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB)
        gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                               self.vertexProgram)
        arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                               self.fragmentProgram)


    def unload(self):
        """Unloads the shader program. """
        gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
        gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)


    @contextlib.contextmanager
    def loaded(self):
        """Context manager which calls :meth:`load`, yields, then
        calls :meth:`unload`.
        """
        self.load()
        try:
            yield
        finally:
            self.unload()


    def loadAtts(self):
        """Enables texture coordinates for all shader program attributes.
        This is called automatically by :meth:`draw`, so there is no need
        to call it explicitly.

        All attributes must be set before they are loaded.
        """
        if self.attsLoaded:
            return

        # In some scenarios, GL_VERTEX_ARRAY
        # must be enabled even if it is not
        # used (e.g. on macOS).
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        for attr in self.attrs:
            texUnit     = self.__getAttrTexUnit(attr)
            value, size = self.attCache[attr]
            gl.glClientActiveTexture(texUnit)
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
            gl.glTexCoordPointer(size, gl.GL_FLOAT, 0, value)
        self.attsLoaded = True


    def unloadAtts(self):
        """Disables texture coordinates on all texture units.
        This is called automatically by :meth:`draw`, so there is no need
        to call it explicitly.
        """
        for attr in self.attrs:
            texUnit = self.__getAttrTexUnit(attr)
            gl.glClientActiveTexture(texUnit)
            gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        self.attsLoaded = False


    @contextlib.contextmanager
    def loadedAtts(self):
        """Context manager which calls :meth:`loadAtts`, yields, then
        calls :meth:`unloadAtts`.
        This is called automatically by :meth:`draw`, so there is no need
        to call it explicitly.
        """
        self.loadAtts()
        try:
            yield
        finally:
            self.unloadAtts()


    def set(self, name, value):
        """Set the value of the specified parameter on the vertex program
        and/or the fragment program.
        """
        if name in self.vertParamPositions: self.setVertParam(name, value)
        if name in self.fragParamPositions: self.setFragParam(name, value)


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
        value = self.__normaliseParam(value)
        nrows = len(value) // 4

        log.debug('Setting vertex parameter %s = %s', name, value)

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
        value = self.__normaliseParam(value)
        nrows = len(value) // 4

        log.debug('Setting fragment parameter %s = %s', name, value)

        for i in range(nrows):
            row = value[i * 4: i * 4 + 4]
            arbfp.glProgramLocalParameter4fARB(
                arbfp.GL_FRAGMENT_PROGRAM_ARB, pos + i,
                row[0], row[1], row[2], row[3])


    @memoize.Instanceify(memoize.skipUnchanged)
    def setConstant(self, name, value):
        """Updates the value of a constant parameter used by the program.

        The :meth:`recompile` method must be called after changing a constant
        value.
        """
        if name not in self.constants:
            raise ValueError('Unknown constant: {}'.format(name))

        log.debug('Setting vertex constant %s = %s', name, value)

        self.constantVals[name] = value


    def setAtt(self, name, value):
        """Sets the value of the specified vertex attribute. Each vertex
        attribute is mapped to a texture coordinate. It is assumed that
        the given value is a ``numpy`` array of shape ``(n, l)``, where
        ``n`` is the number of vertices being drawn, and ``l`` is the
        number of components in each vertex attribute coordinate. If
        ``value`` is 1D, it is reshaped to ``(N, 1)``.
        """

        if len(value.shape) == 1:
            value = value.reshape(-1, 1)

        texUnit = self.__getAttrTexUnit(name)
        value   = np.array(value, dtype=np.float32, copy=False)
        size    = value.shape[1]

        log.debug('Setting vertex attribute %s [%s] = [%s * %s]',
                  name, texUnit, value.shape[0], size)

        # The array is passed to glTexCoordPointer in
        # loadAtts.  With GL14, we don't have vertex
        # buffers, so we have to pass all vertex data
        # on every single draw.
        self.attCache[name] = value.ravel('C'), size


    def setIndices(self, indices):
        """Stores a set of vertex indices to be used in calls to :meth:`draw`.
        """
        if indices is not None:
            indices = np.asarray(indices.ravel('C'), dtype=np.uint32)
        self.indices = indices


    def draw(self, prim, *args):
        """Submits a GL draw call for the specified primitive type.
        If vertex indices have been provided via the :meth:`setIndices` method,
        ``glDrawElements`` is used, and all other arguments are ignored.
        Otherwise, ``glDrawArrays`` is used, and is passed all other arguments.
        """
        with self.loadedAtts():
            if self.indices is not None:
                indices  = self.indices
                nindices = indices.size
                gl.glDrawElements(prim, nindices, gl.GL_UNSIGNED_INT, indices)
            else:
                gl.glDrawArrays(prim, *args)


    def __normaliseParam(self, value):
        """Used by :meth:`setVertParam` and :meth:`setFragParam`. Ensures that
        all vertex/fragment program parameters are vectors of length 4, or
        matrices of size ``(n, 4)``.
        """

        # scalar
        if np.isscalar(value):
            value = [value]

        value = np.array(value, copy=False)

        # vector
        if len(value.shape) == 1:

            # if < 4 values, pad it to 4. If > 4
            # values, an error will be raised below
            if value.shape[0] < 4:
                value = list(value) + [0] * (4 - len(value))

        # matrix
        elif value.shape[1] != 4:
            padding = np.zeros((value.shape[0], 1))
            value   = np.hstack((value, padding))

        value = np.array(value, dtype=np.float32, copy=False)

        if value.ndim > 2 or value.size < 4 or value.size % 4 != 0:
            raise ValueError('Invalid arbp parameter: {}'.format(value))

        return value.ravel('C')


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


    def __cleanSource(self, src):
        """Strips out comments and blank lines from the given string, unless
        ``clean is False`` (as passed into :meth:`__init__`).
        """

        if not self.clean:
            return src

        # strip out comments and blank lines
        lines = src.split('\n')
        lines = [l.strip() for l in lines]
        lines = [l         for l in lines if l    != '']
        lines = [l         for l in lines if l[0] != '#']
        src  = '\n'.join(lines)

        # Squeeze duplicate spaces
        src = re.sub(' +', ' ', src)

        return src


    def __compile(self, vertSrc, fragSrc):
        """Called by :meth:`__init__`. Compiles the vertex and fragment
        programs and returns references to the compiled programs.

        """

        gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB)
        gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        # Clear out unnecessary stuff from
        # the source, and make sure it is
        # plain ASCII - not unicode.
        vertSrc = self.__cleanSource(vertSrc)
        fragSrc = self.__cleanSource(fragSrc)
        vertSrc = vertSrc.encode('ascii')
        fragSrc = fragSrc.encode('ascii')

        fragProg = arbfp.glGenProgramsARB(1)
        vertProg = arbvp.glGenProgramsARB(1)

        # vertex program
        try:
            arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB, vertProg)
            arbvp.glProgramStringARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                                     arbvp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                     len(vertSrc),
                                     vertSrc)

        except Exception:

            position = gl.glGetIntegerv(arbvp.GL_PROGRAM_ERROR_POSITION_ARB)
            message  = gl.glGetString(  arbvp.GL_PROGRAM_ERROR_STRING_ARB)
            message  = message.decode('ascii')

            raise RuntimeError('Error compiling vertex program ({}): '
                               '{}\n{}'.format(position, message, vertSrc))

        # fragment program
        try:
            arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                   fragProg)

            arbfp.glProgramStringARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                     arbfp.GL_PROGRAM_FORMAT_ASCII_ARB,
                                     len(fragSrc),
                                     fragSrc)
        except Exception:
            position = gl.glGetIntegerv(arbfp.GL_PROGRAM_ERROR_POSITION_ARB)
            message  = gl.glGetString(  arbfp.GL_PROGRAM_ERROR_STRING_ARB)
            message  = message.decode('ascii')

            raise RuntimeError('Error compiling fragment program ({}): '
                               '{}\n{}'.format(position, message, fragSrc))

        gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
        gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

        return vertProg, fragProg
