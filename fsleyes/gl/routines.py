#!/usr/bin/env python
#
# routines.py - A collection of disparate utility functions related to OpenGL.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a collection of miscellaneous OpenGL and geometric
routines.
"""


from __future__ import division

import                logging
import                contextlib
import                collections
import itertools   as it

import OpenGL.GL   as gl
import OpenGL.GLUT as glut
import numpy       as np

import fsl.utils.transform as transform


log = logging.getLogger(__name__)


def clear(bgColour):
    """Clears the current frame buffer, and does some standard setup
    operations.
    """

    # set the background colour
    gl.glClearColor(*bgColour)

    # clear the buffer
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # enable transparency
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)


@contextlib.contextmanager
def enabled(capabilities, enable=True):
    """This function can be used as a context manager to temporarily
    enable/disable one or more GL capabilities (i.e. something that you pass
    to ``glEnable`` and ``glDisable``, or ``glEnableClientState`` and
    ``glDisableClientState``), for a piece of code, and restore their previous
    state afterwards.

    :arg capabilities: One or more OpenGL capabilities to be
                       temporarily enabled/disabled, e.g. ``GL_BLEND``,
                       ``GL_TEXTURE_2D``, etc.

    :arg enable:       Whether the capabilities are to be enabled (the
                       default) or disabled.
    """

    # Capabilities which are used via
    # glEnableClientState/glDisableClientState,
    # rather than glEnable/glDisable
    clientCapabilities = [
        gl.GL_VERTEX_ARRAY,
        gl.GL_NORMAL_ARRAY,
        gl.GL_COLOR_ARRAY,
        gl.GL_SECONDARY_COLOR_ARRAY,
        gl.GL_EDGE_FLAG_ARRAY,
        gl.GL_INDEX_ARRAY,
        gl.GL_FOG_COORD_ARRAY,
        gl.GL_TEXTURE_COORD_ARRAY]

    if not isinstance(capabilities, collections.Sequence):
        capabilities = [capabilities]

    # Build lists of pre/post-yield
    # functions, one pre and post
    # for each capability, being
    # one of:
    #
    #   - glEnable
    #   - glDisable
    #   - glEnableClientState
    #   - glDisableClientState
    #   - noop (if the capability's
    #     current state is already
    #     in the requested state)

    def noop(*a):
        pass

    pres  = []
    posts = []

    for c in capabilities:

        if bool(gl.glIsEnabled(c)) == enable:
            pre  = noop
            post = noop
        else:
            if c in clientCapabilities:
                pre  = gl.glEnableClientState
                post = gl.glDisableClientState
            else:
                pre  = gl.glEnable
                post = gl.glDisable

        if not enable:
            pre, post = post, pre

        pres .append(pre)
        posts.append(post)

    [p(c) for p, c in zip(pres,  capabilities)]
    yield
    [p(c) for p, c in zip(posts, capabilities)]


@contextlib.contextmanager
def disabled(capabilities):
    """Can be used as a context manager to temporarily disable the
    given GL capabilities - see :func:`enabled`.
    """
    with enabled(capabilities, False):
        yield


def show2D(xax, yax, width, height, lo, hi, flipx=False, flipy=False):
    """Configures the OpenGL viewport for 2D othorgraphic display.

    :arg xax:    Index (into ``lo`` and ``hi``) of the axis which
                 corresponds to the horizontal screen axis.
    :arg yax:    Index (into ``lo`` and ``hi``) of the axis which
                 corresponds to the vertical screen axis.
    :arg width:  Canvas width in pixels.
    :arg height: Canvas height in pixels.
    :arg lo:     Tuple containing the mininum ``(x, y, z)`` display
                 coordinates.
    :arg hi:     Tuple containing the maxinum ``(x, y, z)`` display
                 coordinates.

    :arg flipx:  If ``True``, the x axis is inverted.

    :arg flipy:  If ``True``, the y axis is inverted.
    """

    zax = 3 - xax - yax

    xmin, xmax = lo[xax], hi[xax]
    ymin, ymax = lo[yax], hi[yax]
    zmin, zmax = lo[zax], hi[zax]

    projmat = np.eye(4, dtype=np.float32)

    if flipx: projmat[0, 0] = -1
    if flipy: projmat[1, 1] = -1

    gl.glViewport(0, 0, width, height)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadMatrixf(projmat)

    zdist = max(abs(zmin), abs(zmax))

    log.debug('Configuring orthographic viewport: '
              'X: [{} - {}] Y: [{} - {}] Z: [{} - {}]'.format(
                  xmin, xmax, ymin, ymax, -zdist, zdist))

    gl.glOrtho(xmin, xmax, ymin, ymax, -zdist, zdist)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()

    # Rotate world space so the displayed slice
    # is visible and correctly oriented
    # TODO There's got to be a more generic way
    # to perform this rotation. This will break
    # if I add functionality allowing the user
    # to specifty the x/y axes on initialisation.
    if zax == 0:
        gl.glRotatef(270, 1, 0, 0)
        gl.glRotatef(270, 0, 0, 1)
    elif zax == 1:
        gl.glRotatef(270, 1, 0, 0)


def lookAt(eye, centre, up):
    """Replacement for ``gluLookAt`. Creates a transformation matrix which
    transforms the display coordinate system such that a camera at position
    (0, 0, 0), and looking towards (0, 0, -1), will see a scene as if from
    position ``eye``, oriented ``up``, and looking towards ``centre``.

    See:
    https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluLookAt.xml
    """

    eye    = np.array(eye)
    centre = np.array(centre)
    up     = np.array(up)
    proj   = np.eye(4)

    forward  = centre - eye
    forward /= np.sqrt(np.dot(forward, forward))

    right  = np.cross(forward, up)
    right /= np.sqrt(np.dot(right, right))

    up     = np.cross(right, forward)
    up    /= np.sqrt(np.dot(up, up))

    proj[0, :3] =  right
    proj[1, :3] =  up
    proj[2, :3] = -forward

    eye  = transform.scaleOffsetXform(1, -eye)
    proj = transform.concat(proj, eye)

    return proj


def ortho(lo, hi, width, height, zoom):
    """Generates an orthographic projection matrix. The display coordinate
    system origin ``(0, 0, 0)`` is mapped to the centre of the clipping space.

      - The horizontal axis is scaled to::
          [-(hi[0] - lo[0]) / 2, (hi[0] - lo[0]) / 2]

      - The vertical axis is scaled to::
          [-(hi[1] - lo[1]) / 2, (hi[1] - lo[1]) / 2]

    :arg lo:          Low ``(x, y, z)`` bounds.
    :arg hi:          High ``(x, y, z)`` bounds.
    :arg width:       Canvas width in pixels
    :arg height:      Canvas height in pixels
    :arg zoom:        Zoom factor. Required to determine suitable near and far
                      clipping plane locations.

    :returns: A tuple containing:

               - The ``(4, 4)`` projection matrix

               - A list of three ``(min, max)`` tuples, defining the limits
                 for each axis.
    """

    lo = np.array(lo, copy=False)
    hi = np.array(hi, copy=False)

    xmin, ymin = lo[:2]
    xmax, ymax = hi[:2]
    zmin, zmax = min(lo), max(hi)

    xmin, xmax, ymin, ymax = preserveAspectRatio(
        width, height, xmin, xmax, ymin, ymax)

    xlen = xmax - xmin
    ylen = ymax - ymin
    zlen = np.sqrt(np.sum((hi - lo) ** 2)) * zoom

    xhalf = xlen / 2.0
    yhalf = ylen / 2.0

    xmax =  xhalf
    xmin = -xhalf
    ymax =  yhalf
    ymin = -yhalf
    zmin = -zlen
    zmax = +zlen

    projmat       = np.eye(4, dtype=np.float32)
    projmat[0, 0] =  2 / (xmax - xmin)
    projmat[1, 1] =  2 / (ymax - ymin)
    projmat[2, 2] = -2 / (zmax - zmin)
    projmat[0, 3] = -(xmax + xmin) / (xmax - xmin)
    projmat[1, 3] = -(ymax + ymin) / (ymax - ymin)
    projmat[2, 3] = -(zmax + zmin) / (zmax - zmin)

    limits = [(xmin, xmax),
              (ymin, ymax),
              (zmin, zmax)]

    return projmat, limits


def adjust(x, y, w, h):
    """Adjust the given ``x`` and ``y`` values by the aspect ratio
    defined by the given ``w`` and ``h`` values.
    """

    xmin, xmax, ymin, ymax = preserveAspectRatio(w, h, 0, x, 0, y)
    return (xmax - xmin), (ymax - ymin)


def preserveAspectRatio(width, height, xmin, xmax, ymin, ymax, grow=True):
    """Adjusts the given x/y limits so that they can be displayed on a
    display of the given ``width`` and ``height``, while preserving the
    aspect ratio.

    :arg width:  Display width

    :arg height: Display height

    :arg xmin:   Low x limit

    :arg xmax:   High x limit

    :arg ymin:   Low y limit

    :arg ymax:   High y limit

    :arg grow:   If ``True`` (the default), the x/y limits are expanded to
                 preserve the aspect ratio. Otherwise, they are shrunken.
    """

    xlen = xmax - xmin
    ylen = ymax - ymin

    if np.any(np.isclose((width, height, xlen, ylen), 0)):
        return xmin, xmax, ymin, ymax

    # These ratios are used to determine whether
    # we need to expand the display range to
    # preserve the image aspect ratio.
    dispRatio   =        xlen  / ylen
    canvasRatio = float(width) / height

    # the canvas is too wide - we need
    # to grow/shrink the display width,
    # thus effectively shrinking/growing
    # the display along the horizontal
    # axis
    if canvasRatio > dispRatio:
        newxlen  = width * (ylen / height)

        if grow: offset =  0.5 * (newxlen - xlen)
        else:    offset = -0.5 * (newxlen - xlen)

        xmin = xmin - offset
        xmax = xmax + offset

    # the canvas is too high - we need
    # to expand/shrink the display height
    elif canvasRatio < dispRatio:
        newylen  = height * (xlen / width)

        if grow: offset =  0.5 * (newylen - ylen)
        else:    offset = -0.5 * (newylen - ylen)

        ymin = ymin - offset
        ymax = ymax + offset

    return xmin, xmax, ymin, ymax


def text2D(text,
           pos,
           fontSize,
           displaySize,
           angle=None,
           fixedWidth=False,
           calcSize=False):
    """Renders a 2D string using ``glutStrokeCharacter``.

    :arg text:        The text to render. Only ASCII characters 32-127 (and
                      newlines) are supported.

    :arg pos:         2D text position in pixels.

    :arg fontSize:    Font size in pixels

    :arg displaySize: ``(width, height)`` of the canvas in pixels.

    :arg angle:       Angle (in degrees) by which to rotate the text.

    :arg fixedWidth:  If ``True``, a fixed-width font is used. Otherwise a
                      variable-width font is used.

    :arg calcSize:    If ``True``, the text is not rendered. Instead, the
                      size of the text, in pixels, is calculated and returned
                      (before any rotation by the ``angle``).
    """

    if fixedWidth: font = glut.GLUT_STROKE_MONO_ROMAN
    else:          font = glut.GLUT_STROKE_ROMAN

    pos           = list(pos)
    width, height = displaySize

    # The glut characters have a default
    # height (in display coordinates) of
    # 152.38. Scale this to the requested
    # pixel font size.
    scale = fontSize / 152.38

    # Get the current matrix mode,
    # and restore it when we're done
    mm = gl.glGetInteger(gl.GL_MATRIX_MODE)

    # Set up an ortho view where the
    # display coordinates correspond
    # to the canvas pixel coordinates.
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glOrtho(0, width, 0, height, -1, 1)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()

    gl.glEnable(gl.GL_LINE_SMOOTH)

    # Draw each line one at a time
    width  = 0
    height = 0
    lines  = text.split('\n')

    for i, line in enumerate(lines):

        height += scale * 152.38
        pos[1] -= scale * 152.38 * i

        gl.glPushMatrix()
        gl.glTranslatef(pos[0], pos[1], 0)
        gl.glScalef(scale, scale, scale)

        lineWidth = 0
        for char in line:

            # We either calculate the
            # character size, or draw
            # the character, but not
            # both
            if calcSize:
                charWidth  = glut.glutStrokeWidth(font, ord(char))
                lineWidth += charWidth * (fontSize / 152.38)

            else:
                glut.glutStrokeCharacter(font, ord(char))

        if lineWidth > width:
            width = lineWidth

        gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()

    gl.glMatrixMode(mm)

    if calcSize: return width, height
    else:        return 0,     0


def pointGrid(shape,
              resolution,
              xform,
              xax,
              yax,
              origin='centre',
              bbox=None):
    """Calculates a uniform grid of points, in the display coordinate system
    (as specified by the given :class:`.Display` object properties) along the
    x-y plane (as specified by the xax/yax indices), at which the given image
    should be sampled for display purposes.

    This function returns a tuple containing:

     - a numpy array of shape ``(N, 3)``, containing the coordinates of the
       centre of every sampling point in the display coordinate system.

     - the horizontal distance (along xax) between adjacent points

     - the vertical distance (along yax) between adjacent points

     - The number of samples along the horizontal axis (xax)

     - The number of samples along the vertical axis (yax)

    :arg shape:      The shape of the data to be sampled.

    :arg resolution: The desired resolution in display coordinates, along
                     each display axis.

    :arg xform:      A transformation matrix which converts from data
                     coordinates to the display coordinate system.

    :arg xax:        The horizontal display coordinate system axis (0, 1, or
                     2).

    :arg yax:        The vertical display coordinate system axis (0, 1, or 2).

    :arg origin:     ``centre`` or ``corner``. See the
                     :func:`.transform.axisBounds` function.

    :arg bbox:       An optional sequence of three ``(low, high)`` values,
                     defining the bounding box in the display coordinate
                     system which should be considered - the generated grid
                     will be constrained to lie within this bounding box.
    """

    xres = resolution[xax]
    yres = resolution[yax]

    # These values give the min/max x/y
    # values of a bounding box which
    # encapsulates the entire image,
    # in the display coordinate system
    xmin, xmax = transform.axisBounds(shape, xform, xax, origin, boundary=None)
    ymin, ymax = transform.axisBounds(shape, xform, yax, origin, boundary=None)

    # Number of samples along each display
    # axis, given the requested resolution
    xNumSamples = int(np.floor((xmax - xmin) / xres))
    yNumSamples = int(np.floor((ymax - ymin) / yres))

    # adjust the x/y resolution so
    # the samples fit exactly into
    # the data bounding box
    xres = (xmax - xmin) / xNumSamples
    yres = (ymax - ymin) / yNumSamples

    # Calculate the locations of every
    # sample point in display space
    worldX = np.linspace(xmin + 0.5 * xres,
                         xmax - 0.5 * xres,
                         xNumSamples)
    worldY = np.linspace(ymin + 0.5 * yres,
                         ymax - 0.5 * yres,
                         yNumSamples)

    # Apply bounding box constraint
    # if it has been provided
    if bbox is not None:
        xoff   = 0.5 * xres
        yoff   = 0.5 * yres

        xmin   = max((xmin, bbox[xax][0] - xoff))
        xmax   = min((xmax, bbox[xax][1] + xoff))
        ymin   = max((ymin, bbox[yax][0] - yoff))
        ymax   = min((ymax, bbox[yax][1] + yoff))

        worldX = worldX[(worldX >= xmin) & (worldX <= xmax)]
        worldY = worldY[(worldY >= ymin) & (worldY <= ymax)]

    # Generate the coordinates
    worldX, worldY = np.meshgrid(worldX, worldY)

    # reshape them to N*3
    coords = np.zeros((worldX.size, 3), dtype=np.float32)
    coords[:, xax] = worldX.flatten()
    coords[:, yax] = worldY.flatten()

    return coords, xres, yres, xNumSamples, yNumSamples


def pointGrid3D(shape, xform=None, origin='centre', bbox=None):
    """Generates a 3D grid of points into an image of the given ``shape``,
    with the given ``xform`` defining the index to display coordinate
    transform.

    note: Not implemented properly yet.
    """

    coords = np.indices(shape).transpose(1, 2, 3, 0).reshape(-1, 3)

    if xform is not None:
        coords = transform.transform(coords, xform)

    return coords


def samplePointsToTriangleStrip(coords,
                                xpixdim,
                                ypixdim,
                                xlen,
                                ylen,
                                xax,
                                yax):
    """Given a regular 2D grid of points at which an image is to be sampled
    (for example, that generated by the :func:`pointGrid` function above),
    converts those points into an OpenGL vertex triangle strip.

    A grid of ``M*N`` points is represented by ``M*2*(N + 1)`` vertices. For
    example, this image represents a 4*3 grid, with periods representing vertex
    locations::

        .___.___.___.___.
        |   |   |   |   |
        |   |   |   |   |
        .---.---.---.---.
        .___.___.__ .___.
        |   |   |   |   |
        |   |   |   |   |
        .---.---.---.---.
        .___.___.___.___.
        |   |   |   |   |
        |   |   |   |   |
        .___.___.___.___.


    Vertex locations which are vertically adjacent represent the same point in
    space. Such vertex pairs are unable to be combined because, in OpenGL,
    they must be represented by distinct vertices (we can't apply multiple
    colours/texture coordinates to a single vertex location) So we have to
    repeat these vertices in order to achieve accurate colouring of each
    voxel.

    We draw each horizontal row of samples one by one, using two triangles to
    draw each voxel. In order to eliminate the need to specify six vertices
    for every voxel, and hence to reduce the amount of memory used, we are
    using a triangle strip to draw each row of voxels. This image depicts a
    triangle strip used to draw a row of three samples (periods represent
    vertex locations)::


        1  3  5  7
        .  .  .  .
        |\ |\ |\ |
        | \| \| \|
        .  .  .  .
        0  2  4  6

    In order to use a single OpenGL call to draw multiple non-contiguous voxel
    rows, between every column we add a couple of 'dummy' vertices, which will
    then be interpreted by OpenGL as 'degenerate triangles', and will not be
    drawn. So in reality, a 4*3 slice would be drawn as follows (with vertices
    labelled from ``[a-z0-9]``::

         v  x  z  1  33
         |\ |\ |\ |\ |
         | \| \| \| \|
        uu  w  y  0  2
         l  n  p  r  tt
         |\ |\ |\ |\ |
         | \| \| \| \|
        kk  m  o  q  s
         b  d  f  h  jj
         |\ |\ |\ |\ |
         | \| \| \| \|
         a  c  e  g  i

    These repeated/degenerate vertices are dealt with by using a vertex index
    array.  See these links for good overviews of triangle strips and
    degenerate triangles in OpenGL:

     - http://www.learnopengles.com/tag/degenerate-triangles/
     - http://en.wikipedia.org/wiki/Triangle_strip

    A tuple is returned containing:

      - A 2D ``numpy.float32`` array of shape ``(2 * (xlen + 1) * ylen), 3)``,
        containing the coordinates of all triangle strip vertices which
        represent the entire grid of sample points.

      - A 2D ``numpy.float32`` array of shape ``(2 * (xlen + 1) * ylen), 3)``,
        containing the centre of every grid, to be used for texture
        coordinates/colour lookup.

      - A 1D ``numpy.uint32`` array of size ``ylen * (2 * (xlen + 1) + 2) - 2``
        containing indices into the first array, defining the order in which
        the vertices need to be rendered. There are more indices than vertex
        coordinates due to the inclusion of repeated/degenerate vertices.

    :arg coords:  N*3 array of points, the sampling locations.

    :arg xpixdim: Length of one sample along the horizontal axis.

    :arg ypixdim: Length of one sample along the vertical axis.

    :arg xlen:    Number of samples along the horizontal axis.

    :arg ylen:    Number of samples along the vertical axis.

    :arg xax:     Display coordinate system axis which corresponds to the
                  horizontal screen axis.

    :arg yax:     Display coordinate system axis which corresponds to the
                  vertical screen axis.
    """

    coords = coords.reshape(ylen, xlen, 3)

    xlen = int(xlen)
    ylen = int(ylen)

    # Duplicate every row - each voxel
    # is defined by two vertices
    coords = coords.repeat(2, 0)

    texCoords   = np.array(coords, dtype=np.float32)
    worldCoords = np.array(coords, dtype=np.float32)

    # Add an extra column at the end
    # of the world coordinates
    worldCoords = np.append(worldCoords, worldCoords[:, -1:, :], 1)
    worldCoords[:, -1, xax] += xpixdim

    # Add an extra column at the start
    # of the texture coordinates
    texCoords = np.append(texCoords[:, :1, :], texCoords, 1)

    # Move the x/y world coordinates to the
    # sampling point corners (the texture
    # coordinates remain in the voxel centres)
    worldCoords[   :, :, xax] -= 0.5 * xpixdim
    worldCoords[ ::2, :, yax] -= 0.5 * ypixdim
    worldCoords[1::2, :, yax] += 0.5 * ypixdim

    vertsPerRow  = 2 * (xlen + 1)
    dVertsPerRow = 2 * (xlen + 1) + 2
    nindices     = ylen * dVertsPerRow - 2

    indices = np.zeros(nindices, dtype=np.uint32)

    for yi, xi in it.product(range(ylen), range(xlen + 1)):

        ii = yi * dVertsPerRow + 2 * xi
        vi = yi *  vertsPerRow + xi

        indices[ii]     = vi
        indices[ii + 1] = vi + xlen + 1

        # add degenerate vertices at the end
        # every row (but not needed for last
        # row)
        if xi == xlen and yi < ylen - 1:
            indices[ii + 2] = vi + xlen + 1
            indices[ii + 3] = (yi + 1) * vertsPerRow

    worldCoords = worldCoords.reshape((xlen + 1) * (2 * ylen), 3)
    texCoords   = texCoords  .reshape((xlen + 1) * (2 * ylen), 3)

    return worldCoords, texCoords, indices


def voxelGrid(points, xax, yax, xpixdim, ypixdim):
    """Given a ``N*3`` array of ``points`` (assumed to be voxel
    coordinates), creates an array of vertices which can be used
    to render each point as an unfilled rectangle.

    :arg points:  An ``N*3`` array of voxel xyz coordinates

    :arg xax:     XYZ axis index that maps to the horizontal scren axis

    :arg yax:     XYZ axis index that maps to the vertical scren axis

    :arg xpixdim: Length of a voxel along the x axis.

    :arg ypixdim: Length of a voxel along the y axis.
    """

    if len(points.shape) == 1:
        points = points.reshape(1, 3)

    npoints  = points.shape[0]
    vertices = np.repeat(np.array(points, dtype=np.float32), 4, axis=0)

    xpixdim = xpixdim / 2.0
    ypixdim = ypixdim / 2.0

    # bottom left corner
    vertices[ ::4, xax] -= xpixdim
    vertices[ ::4, yax] -= ypixdim

    # bottom right
    vertices[1::4, xax] += xpixdim
    vertices[1::4, yax] -= ypixdim

    # top left
    vertices[2::4, xax] -= xpixdim
    vertices[2::4, yax] += ypixdim

    # top right
    vertices[3::4, xax] += xpixdim
    vertices[3::4, yax] += ypixdim

    # each square is rendered as four lines
    indices = np.array([0, 1, 0, 2, 1, 3, 2, 3], dtype=np.uint32)
    indices = np.tile(indices, npoints)

    indices = (indices.T +
               np.repeat(np.arange(0, npoints * 4, 4, dtype=np.uint32), 8)).T

    return vertices, indices


def voxelBlock(*args, **kwargs):
    """Generates a ``numpy`` array containing all ones, centered at the
    specified voxel.

    :arg dtype: The data type of the returned ``numpy`` array. Defaults to
                ``uint8``.

    All other arguments are passed through to the :func:`voxelBox` function -
    see that function for details on the arguments.

    :returns: A tuple containing:

              - The ``numpy`` array

              - Voxel coordinates specifying the offset of the position of
                this array in the image.
    """

    dtype   = kwargs.pop('dtype', np.uint8)
    corners = voxelBox(*args, **kwargs)

    los  = corners.min(axis=0)
    his  = corners.max(axis=0)

    lens  = his - los
    block = np.ones(lens, dtype=dtype)

    return block, los


def voxelBox(voxel,
             shape,
             dims,
             boxSize,
             axes=(0, 1, 2),
             bias=None,
             bounded=True):
    """Generates a 'box', a cuboid region, in a voxel coordinate system,
    centered at a specific voxel.

    The corners of the box are returnd as a ``numpy`` array of shape
    ``(8, 3)``.

    :arg voxel:   Coordinates of the voxel around which the block is to
                  be centred.

    :arg shape:   Shape of the image in which the block is to be located.

    :arg dims:    Size of the image voxels along each dimension.

    :arg boxSize: Desired width/height/depth of the box in scaled voxels.
                  May be either a single value, or a sequence of three
                  values.

    :arg axes:    Axes along which the block is to be located.

    :arg bias:    ``low``, ``high``, or ``None``. The box can only be
                  centered on the ``voxel`` if the specified ``boxSize``
                  results in an odd number of voxels along each voxel axis.
                  If this is not the case, more voxels must be added to one
                  side of the box centre. You can specify that these voxels
                  are added to the ``high`` side (i.e. larger voxel
                  coordinate) or the ``low`` side  of the voxel. Specifying
                  ``None`` will force the box to have an odd number of voxels
                  along each axis, and thus have the ``voxel`` in the true
                  centre of the box.

    :arg bounded: If ``True`` (the default), and the specified voxel would
                  result in part of the block being located outside of the
                  image shape, the block is truncated to fit inside the
                  image bounds.
    """

    if not isinstance(boxSize, collections.Iterable):
        boxSize = [boxSize] * 3

    for i in range(3):
        if i not in axes:
            boxSize[i] = dims[i]

    voxel       = np.array(voxel)
    dims        = np.array(dims[:3])
    shape       = np.array(shape[:3])
    boxSize     = np.array(boxSize[:3])

    # The block size must be at least
    # one voxel across each dimension
    boxSize     = np.clip(boxSize, dims, boxSize)

    # Voxel location and box low/
    # high bounds in scaled voxels.
    #
    # Note that we are assuming that
    # voxel coordinates correspond to
    # the voxel centre here
    # (voxel + 0.5). This has the effect
    # that the returned box vertices will
    # be integer voxel coordinates (i.e.
    # on voxel borders).
    scaledVoxel = (voxel + 0.5) * dims
    scaledLo    = scaledVoxel - boxSize / 2.0
    scaledHi    = scaledVoxel + boxSize / 2.0

    # Scale the low/high bounds back
    # into voxel coordinates, and
    # round them up or down according
    # to the bias setting.
    if bias == 'low':
        lo = np.floor(scaledLo / dims)
        hi = np.floor(scaledHi / dims)

    elif bias == 'high':
        lo = np.ceil(scaledLo / dims)
        hi = np.ceil(scaledHi / dims)

    else:
        lo = np.floor(scaledLo / dims)
        hi = np.ceil( scaledHi / dims)

    # Crop the box to the
    # image space if necessary
    if bounded:
        lo = np.maximum(lo, 0)
        hi = np.minimum(hi, shape)

    if np.any(hi <= lo):
        return None

    box       = np.zeros((8, 3), dtype=np.uint32)
    box[0, :] = lo[0], lo[1], lo[2]
    box[1, :] = lo[0], lo[1], hi[2]
    box[2, :] = lo[0], hi[1], lo[2]
    box[3, :] = lo[0], hi[1], hi[2]
    box[4, :] = hi[0], lo[1], lo[2]
    box[5, :] = hi[0], lo[1], hi[2]
    box[6, :] = hi[0], hi[1], lo[2]
    box[7, :] = hi[0], hi[1], hi[2]

    return box


def slice2D(dataShape,
            xax,
            yax,
            zpos,
            voxToDisplayMat,
            displayToVoxMat,
            geometry='triangles',
            origin='centre',
            bbox=None):
    """Generates and returns vertices which denote a slice through an
    array of the given ``dataShape``, parallel to the plane defined by the
    given ``xax`` and ``yax`` and at the given z position, in the space
    defined by the given ``voxToDisplayMat``.

    If ``geometry`` is ``triangles`` (the default), six vertices are returned,
    arranged as follows::

         4---5
        1 \  |
        |\ \ |
        | \ \|
        |  \ 3
        0---2

    Otherwise, if geometry is ``square``, four vertices are returned, arranged
    as follows::


        3---2
        |   |
        |   |
        |   |
        0---1

    If ``origin`` is set to ``centre`` (the default), it is assumed that
    a voxel at location ``(x, y, z)`` is located in the space::

        (x - 0.5 : x + 0.5, y - 0.5 : y + 0.5, z - 0.5 : z + 0.5)


    Otherwise, if ``origin`` is set to ``corner``, a voxel at location ``(x,
    y, z)`` is assumed to be located in the space::

        (x : x + 1, y : y + 1, z : z + 1)


    :arg dataShape:       Number of elements along each dimension in the
                          image data.

    :arg xax:             Index of display axis which corresponds to the
                          horizontal screen axis.

    :arg yax:             Index of display axis which corresponds to the
                          vertical screen axis.

    :arg zpos:            Position of the slice along the screen z axis.

    :arg voxToDisplayMat: Affine transformation matrix which transforms from
                          voxel/array indices into the display coordinate
                          system.

    :arg displayToVoxMat: Inverse of the ``voxToDisplayMat``.

    :arg geometry:        ``square`` or ``triangle``.

    :arg origin:          ``centre`` or ``corner``. See the
                          :func:`.transform.axisBounds` function.

    :arg bbox:            An optional sequence of three ``(low, high)``
                          values, defining the bounding box in the display
                          coordinate system which should be considered - the
                          generated grid will be constrained to lie within
                          this bounding box.

    Returns a tuple containing:

      - A ``N*3`` ``numpy.float32`` array containing the vertex locations
        of a slice through the data, where ``N=6`` if ``geometry=triangles``,
        or ``N=4`` if ``geometry=square``,

      - A ``N*3`` ``numpy.float32`` array containing the voxel coordinates
        that correspond to the vertex locations.
    """

    zax        = 3 - xax - yax
    xmin, xmax = transform.axisBounds(
        dataShape, voxToDisplayMat, xax, origin, boundary=None)
    ymin, ymax = transform.axisBounds(
        dataShape, voxToDisplayMat, yax, origin, boundary=None)

    if bbox is not None:

        bbxmin = bbox[xax][0]
        bbxmax = bbox[xax][1]
        bbymin = bbox[yax][0]
        bbymax = bbox[yax][1]

        # The returned vertices and voxCoords
        # have to be aligned, so we need to
        # clamp the bounding box limits to the
        # nearest voxel boundary to preserve
        # this alignment.

        # Voxel lengths along x/y axes
        xvlen  = (xmax - xmin) / dataShape[xax]
        yvlen  = (ymax - ymin) / dataShape[yax]

        # Clamp the bbox limits to the
        # nearest voxel boundaries
        bbxmin = xmin + np.floor((bbxmin - xmin) / xvlen) * xvlen
        bbxmax = xmin + np.ceil( (bbxmax - xmin) / xvlen) * xvlen
        bbymin = ymin + np.floor((bbymin - ymin) / yvlen) * yvlen
        bbymax = ymin + np.ceil( (bbymax - ymin) / yvlen) * yvlen

        xmin = max((xmin, bbxmin))
        xmax = min((xmax, bbxmax))
        ymin = max((ymin, bbymin))
        ymax = min((ymax, bbymax))

    if geometry == 'triangles':

        vertices = np.zeros((6, 3), dtype=np.float32)

        vertices[ 0, [xax, yax]] = [xmin, ymin]
        vertices[ 1, [xax, yax]] = [xmax, ymin]
        vertices[ 2, [xax, yax]] = [xmin, ymax]
        vertices[ 3, [xax, yax]] = [xmax, ymin]
        vertices[ 4, [xax, yax]] = [xmax, ymax]
        vertices[ 5, [xax, yax]] = [xmin, ymax]

    elif geometry == 'square':
        vertices = np.zeros((4, 3), dtype=np.float32)

        vertices[ 0, [xax, yax]] = [xmin, ymin]
        vertices[ 1, [xax, yax]] = [xmax, ymin]
        vertices[ 2, [xax, yax]] = [xmax, ymax]
        vertices[ 3, [xax, yax]] = [xmin, ymax]
    else:
        raise ValueError('Unrecognised geometry type: {}'.format(geometry))

    vertices[:, zax] = zpos

    voxCoords = transform.transform(vertices, displayToVoxMat)

    return vertices, voxCoords


def boundingBox(dataShape,
                voxToDisplayMat,
                displayToVoxMat,
                geometry='triangles',
                origin='centre',
                bbox=None):
    """Generates a bounding box to represent a 3D image of the given shape,
    in the coordinate system defined by the ``voxToDisplayMat`` affine.

    See the :func:`slice2D` function for details on the arguments.

    Returns a tuple containing:

      - A ``N*3`` ``numpy.float32`` array containing the vertex locations
        of a bounding box ``N=36`` if ``geometry=triangles``,
        or ``N=24`` if ``geometry=square``,

      - A ``N*3`` ``numpy.float32`` array containing the voxel coordinates
        that correspond to the vertex locations.
    """

    xlo, ylo, zlo = (0, 0, 0)
    xhi, yhi, zhi = dataShape

    if origin == 'centre':
        xlo, ylo, zlo = xlo - 0.5, ylo - 0.5, zlo - 0.5
        xhi, yhi, zhi = xhi - 0.5, yhi - 0.5, zhi - 0.5

    # If the voxel -> display transformation
    # matrix contains negative scales, we need
    # to invert the voxel coordinate ranges to
    # ensure a correct triangle winding order
    # (so that back faces can be culled).
    scales = transform.decompose(voxToDisplayMat)[0]

    if scales[0] < 0: xlo, xhi = xhi, xlo
    if scales[1] < 0: ylo, yhi = yhi, ylo
    if scales[2] < 0: zlo, zhi = zhi, zlo

    if geometry == 'triangles':
        voxCoords = np.zeros((36, 3), dtype=np.float32)

        voxCoords[ 0, :] = (xlo, yhi, zlo)
        voxCoords[ 1, :] = (xhi, ylo, zlo)
        voxCoords[ 2, :] = (xlo, ylo, zlo)
        voxCoords[ 3, :] = (xlo, yhi, zlo)
        voxCoords[ 4, :] = (xhi, yhi, zlo)
        voxCoords[ 5, :] = (xhi, ylo, zlo)

        voxCoords[ 6, :] = (xlo, ylo, zhi)
        voxCoords[ 7, :] = (xhi, ylo, zhi)
        voxCoords[ 8, :] = (xlo, yhi, zhi)
        voxCoords[ 9, :] = (xlo, yhi, zhi)
        voxCoords[10, :] = (xhi, ylo, zhi)
        voxCoords[11, :] = (xhi, yhi, zhi)

        voxCoords[12, :] = (xlo, ylo, zlo)
        voxCoords[13, :] = (xhi, ylo, zlo)
        voxCoords[14, :] = (xlo, ylo, zhi)
        voxCoords[15, :] = (xlo, ylo, zhi)
        voxCoords[16, :] = (xhi, ylo, zlo)
        voxCoords[17, :] = (xhi, ylo, zhi)

        voxCoords[18, :] = (xlo, yhi, zlo)
        voxCoords[19, :] = (xhi, yhi, zlo)
        voxCoords[20, :] = (xlo, yhi, zhi)
        voxCoords[21, :] = (xlo, yhi, zhi)
        voxCoords[22, :] = (xhi, yhi, zlo)
        voxCoords[23, :] = (xhi, yhi, zhi)

        voxCoords[18, :] = (xlo, yhi, zhi)
        voxCoords[19, :] = (xhi, yhi, zlo)
        voxCoords[20, :] = (xlo, yhi, zlo)
        voxCoords[21, :] = (xlo, yhi, zhi)
        voxCoords[22, :] = (xhi, yhi, zhi)
        voxCoords[23, :] = (xhi, yhi, zlo)

        voxCoords[24, :] = (xlo, ylo, zhi)
        voxCoords[25, :] = (xlo, yhi, zlo)
        voxCoords[26, :] = (xlo, ylo, zlo)
        voxCoords[27, :] = (xlo, ylo, zhi)
        voxCoords[28, :] = (xlo, yhi, zhi)
        voxCoords[29, :] = (xlo, yhi, zlo)

        voxCoords[30, :] = (xhi, ylo, zlo)
        voxCoords[31, :] = (xhi, yhi, zlo)
        voxCoords[32, :] = (xhi, ylo, zhi)
        voxCoords[33, :] = (xhi, ylo, zhi)
        voxCoords[34, :] = (xhi, yhi, zlo)
        voxCoords[35, :] = (xhi, yhi, zhi)

    elif geometry == 'square':
        voxCoords = np.zeros((24, 3), dtype=np.float32)

        voxCoords[ 0, :] = (xlo, ylo, zlo)
        voxCoords[ 1, :] = (xhi, ylo, zlo)
        voxCoords[ 2, :] = (xhi, yhi, zlo)
        voxCoords[ 3, :] = (xlo, yhi, zlo)

        voxCoords[ 4, :] = (xlo, ylo, zhi)
        voxCoords[ 5, :] = (xhi, ylo, zhi)
        voxCoords[ 6, :] = (xhi, yhi, zhi)
        voxCoords[ 7, :] = (xlo, yhi, zhi)

        voxCoords[ 8, :] = (xlo, ylo, zlo)
        voxCoords[ 9, :] = (xhi, ylo, zlo)
        voxCoords[10, :] = (xhi, ylo, zhi)
        voxCoords[11, :] = (xlo, ylo, zhi)

        voxCoords[12, :] = (xlo, yhi, zlo)
        voxCoords[13, :] = (xhi, yhi, zlo)
        voxCoords[14, :] = (xhi, yhi, zhi)
        voxCoords[15, :] = (xlo, yhi, zhi)

        voxCoords[16, :] = (xlo, ylo, zlo)
        voxCoords[17, :] = (xlo, yhi, zlo)
        voxCoords[18, :] = (xlo, yhi, zhi)
        voxCoords[19, :] = (xlo, ylo, zhi)

        voxCoords[20, :] = (xhi, ylo, zlo)
        voxCoords[21, :] = (xhi, yhi, zlo)
        voxCoords[22, :] = (xhi, yhi, zhi)
        voxCoords[23, :] = (xhi, ylo, zhi)

    else:
        raise ValueError('Unrecognised geometry type: {}'.format(geometry))

    vertices = transform.transform(voxCoords, voxToDisplayMat)

    return vertices, voxCoords


def subsample(data, resolution, pixdim=None, volume=None):
    """Samples the given 3D data according to the given resolution.

    Returns a tuple containing:

      - A 3D numpy array containing the sub-sampled data.

      - A tuple containing the ``(x, y, z)`` starting indices of the
        sampled data.

      - A tuple containing the ``(x, y, z)`` steps of the sampled data.

    :arg data:       The data to be sampled.

    :arg resolution: Sampling resolution, proportional to the values in
                     ``pixdim``.

    :arg pixdim:     Length of each dimension in the input data (defaults to
                     ``(1.0, 1.0, 1.0)``).

    :arg volume:     If the image is a 4D volume, the volume index of the 3D
                     image to be sampled.
    """

    if pixdim is None:
        pixdim = (1.0, 1.0, 1.0)

    if volume is None:
        volume = slice(None, None, None)

    xstep = int(np.round(resolution / pixdim[0]))
    ystep = int(np.round(resolution / pixdim[1]))
    zstep = int(np.round(resolution / pixdim[2]))

    if xstep < 1: xstep = 1
    if ystep < 1: ystep = 1
    if zstep < 1: zstep = 1

    xstart = int(np.floor((xstep - 1) / 2))
    ystart = int(np.floor((ystep - 1) / 2))
    zstart = int(np.floor((zstep - 1) / 2))

    if xstart >= data.shape[0]: xstart = data.shape[0] - 1
    if ystart >= data.shape[1]: ystart = data.shape[1] - 1
    if zstart >= data.shape[2]: zstart = data.shape[2] - 1

    if len(data.shape) > 3: sample = data[xstart::xstep,
                                          ystart::ystep,
                                          zstart::zstep,
                                          volume]
    else:                   sample = data[xstart::xstep,
                                          ystart::ystep,
                                          zstart::zstep]

    return sample, (xstart, ystart, zstart), (xstep, ystep, zstep)


def broadcast(vertices, indices, zposes, xforms, zax):
    """Given a set of vertices and indices (assumed to be 2D representations
    of some geometry in a 3D space, with the depth axis specified by ``zax``),
    replicates them across all of the specified Z positions, applying the
    corresponding transformation to each set of vertices.

    :arg vertices: Vertex array (a ``N*3`` numpy array).

    :arg indices:  Index array.

    :arg zposes:   Positions along the depth axis at which the vertices
                   are to be replicated.

    :arg xforms:   Sequence of transformation matrices, one for each
                   Z position.

    :arg zax:      Index of the 'depth' axis

    Returns three values:

      - A numpy array containing all of the generated vertices

      - A numpy array containing the original vertices for each of the
        generated vertices, which may be used as texture coordinates

      - A new numpy array containing all of the generated indices.
    """

    vertices = np.array(vertices)
    indices  = np.array(indices)

    nverts   = vertices.shape[0]
    nidxs    = indices.shape[ 0]

    allTexCoords  = np.zeros((nverts * len(zposes), 3), dtype=np.float32)
    allVertCoords = np.zeros((nverts * len(zposes), 3), dtype=np.float32)
    allIndices    = np.zeros( nidxs  * len(zposes),     dtype=np.uint32)

    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):

        vertices[:, zax] = zpos

        vStart = i * nverts
        vEnd   = vStart + nverts

        iStart = i * nidxs
        iEnd   = iStart + nidxs

        allIndices[   iStart:iEnd]    = indices + i * nverts
        allTexCoords[ vStart:vEnd, :] = vertices
        allVertCoords[vStart:vEnd, :] = transform.transform(vertices, xform)

    return allVertCoords, allTexCoords, allIndices


def planeEquation(xyz1, xyz2, xyz3):
    """Calculates the equation of a plane which contains each
    of the given points.

    Returns a ``numpy`` array containing four values, the coefficients of the
    equation:

    :math:`a\\times x + b\\times y + c \\times z = d`

    for any point ``(x, y, z)`` that lies on the plane.

    See http://paulbourke.net/geometry/pointlineplane/ for details on plane
    equations.
    """
    x1, y1, z1 = xyz1
    x2, y2, z2 = xyz2
    x3, y3, z3 = xyz3

    eq = np.zeros(4, dtype=np.float64)

    eq[0] = (y1 * (z2 - z3)) + (y2 * (z3 - z1)) + (y3 * (z1 - z2))
    eq[1] = (z1 * (x2 - x3)) + (z2 * (x3 - x1)) + (z3 * (x1 - x2))
    eq[2] = (x1 * (y2 - y3)) + (x2 * (y3 - y1)) + (x3 * (y1 - y2))
    eq[3] = -((x1 * ((y2 * z3) - (y3 * z2))) +
              (x2 * ((y3 * z1) - (y1 * z3))) +
              (x3 * ((y1 * z2) - (y2 * z1))))

    return eq


def planeEquation2(origin, normal):
    """Calculates the equation of a plane equation from a normal vector
    and a single point on the plane.

    Returns a ``numpy`` array containing four values, the coefficients of the
    equation:

    See also :func:`planeEquation`.
    """

    normal     = transform.normalise(normal)
    ax, by, cz = np.array(origin) * normal

    eqn     = np.zeros(4, dtype=np.float64)
    eqn[:3] = normal
    eqn[ 3] = -np.sum((ax, by, cz))

    return eqn


def unitSphere(res):
    """Generates a unit sphere, as described in the *Sphere Generation*
    article, on Paul Bourke's excellent website:

        http://paulbourke.net/geometry/circlesphere/

    :arg res: Resolution - the number of angles to sample.

    :returns: A tuple comprising:

              - a ``numpy.float32`` array of size ``(res**2, 3)``
                containing a set of ``(x, y, z)`` vertices which define
                the ellipsoid surface.

              - A ``numpy.uint32`` array of size ``(4 * (res - 1)**2)``
                containing a list of indices into the vertex array,
                defining a vertex ordering that can be used to draw
                the ellipsoid using the OpenGL ``GL_QUAD`` primitive type.


    .. todo:: Generate indices to use with ``GL_TRIANGLES`` instead of
              ``GL_QUADS``.
    """

    # All angles to be sampled
    u = np.linspace(-np.pi / 2, np.pi / 2, res, dtype=np.float32)
    v = np.linspace(-np.pi,     np.pi,     res, dtype=np.float32)

    cosu = np.cos(u)
    cosv = np.cos(v)
    sinu = np.sin(u)
    sinv = np.sin(v)

    cucv = np.outer(cosu, cosv).T
    cusv = np.outer(cosu, sinv).T

    vertices = np.zeros((res ** 2, 3), dtype=np.float32)

    # All x coordinates are of the form cos(u) * cos(v),
    # y coordinates are of the form cos(u) * sin(v),
    # and z coordinates of the form sin(u).
    vertices[:, 0] = cucv.flatten()
    vertices[:, 1] = cusv.flatten()
    vertices[:, 2] = np.tile(sinu, res)

    # Generate a list of indices which join the
    # vertices so they can be used to draw the
    # sphere as GL_QUADs.
    #
    # The vertex locations for each quad follow
    # this pattern:
    #
    #  1. (u,         v)
    #  2. (u + ustep, v)
    #  3. (u + ustep, v + vstep)
    #  4. (u,         v + vstep)
    nquads   = (res - 1) ** 2
    quadIdxs = np.array([0, res, res + 1, 1], dtype=np.uint32)

    indices  = np.tile(quadIdxs, nquads)
    indices += np.arange(nquads,  dtype=np.uint32).repeat(4)
    indices += np.arange(res - 1, dtype=np.uint32).repeat(4 * (res - 1))

    return vertices, indices


def fullUnitSphere(res):
    """Generates a unit sphere in the same way as :func:`unitSphere`, but
    returns all vertices, instead of the unique vertices and an index array.

    :arg res: Resolution - the number of angles to sample.

    :returns: A ``numpy.float32`` array of size ``(4 * (res - 1)**2, 3)``
              containing the ``(x, y, z)`` vertices which can be used to draw
              a unit sphere (using the ``GL_QUADS`` primitive type).
    """

    u = np.linspace(-np.pi / 2, np.pi / 2, res, dtype=np.float32)
    v = np.linspace(-np.pi,     np.pi,     res, dtype=np.float32)

    cosu = np.cos(u)
    cosv = np.cos(v)
    sinu = np.sin(u)
    sinv = np.sin(v)

    vertices = np.zeros(((res - 1) * (res - 1) * 4, 3), dtype=np.float32)

    cucv   = np.outer(cosu[:-1], cosv[:-1]).flatten()
    cusv   = np.outer(cosu[:-1], sinv[:-1]).flatten()
    cu1cv  = np.outer(cosu[1:],  cosv[:-1]).flatten()
    cu1sv  = np.outer(cosu[1:],  sinv[:-1]).flatten()
    cu1cv1 = np.outer(cosu[1:],  cosv[1:]) .flatten()
    cu1sv1 = np.outer(cosu[1:],  sinv[1:]) .flatten()
    cucv1  = np.outer(cosu[:-1], cosv[1:]) .flatten()
    cusv1  = np.outer(cosu[:-1], sinv[1:]) .flatten()

    su     = np.repeat(sinu[:-1], res - 1)
    s1u    = np.repeat(sinu[1:],  res - 1)

    vertices.T[:,  ::4] = [cucv,   cusv,   su]
    vertices.T[:, 1::4] = [cu1cv,  cu1sv,  s1u]
    vertices.T[:, 2::4] = [cu1cv1, cu1sv1, s1u]
    vertices.T[:, 3::4] = [cucv1,  cusv1,  su]

    return vertices


def unitCircle(res, triangles=False):
    """Generates ``res`` vertices which form a 2D circle, centered at (0, 0),
    and with radius 1.

    Returns the vertices as a ``numpy.float32`` array of shape ``(res, 2)``

    If the ``triangles`` argument is ``True``, the vertices are generated
    with the assumption that they will be drawn as a ``GL_TRIANGLE_FAN``.
    """

    step = (2 * np.pi) / res

    u = np.linspace(-np.pi, np.pi - step, res, dtype=np.float32)

    cosu  = np.cos(u)
    sinu  = np.sin(u)
    verts = np.vstack((sinu, cosu)).T

    if triangles:
        origin = np.zeros((1, 3), dtyp=np.float32)
        verts  = np.concatenate((origin, verts))

    return verts


def polygonIndices(nverts):
    """Generate triangle indices for simple 2D polygons. Given vertices
    describing a monotone polygon on a 2D plane, generates an index list
    into the vertices which can be used to draw the vertices as triangles.
    """

    ntris   = nverts - 2
    nidxs   = ntris  * 3
    indices = np.zeros(nidxs, dtype=np.uint32)

    indices[1]    = 1
    indices[2:-1] = np.repeat(np.arange(2, nverts - 1), 3)
    indices[-1]   = nverts - 1
    indices[::3]  = 0

    return indices
