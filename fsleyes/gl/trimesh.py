#!/usr/bin/env python
#
# trimesh.py - Portions of Michael Dawson-Haggerty's trimesh project.
#
# Author: Michael Dawson-Haggerty
#
# Incorporated into FSLeyes by Paul McCarthy <pauldmccarthy@gmail.com>
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Michael Dawson-Haggerty

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
"""This module provides the :func:`mesh_plane` function, which was gratefully
lifted from Michael Dawson-Haggerty's excellent ``trimesh`` project:


  - https://pypi.python.org/pypi/trimesh/
  - https://github.com/mikedh/trimesh


FSLeyes uses the :func:`mesh_plane` and :func:`points_to_barycentric`
functions when rendering :class:`.GLMesh` instances. No other features of
``trimesh`` are needed (nor any features provided by its dependenceies), so I
didn't see the point in adding the entire ``trimesh`` project as a dependency.
"""


import numpy as np


######################
# From trimesh.version
######################


__version__ = '2.7.15'


########################
# From trimesh.constants
########################


class NumericalToleranceMesh(object):
    '''
    tol.zero: consider floating point numbers less than this zero
    tol.merge: when merging vertices, consider vertices closer than this
               to be the same vertex. Here we use the same value (1e-8)
               as SolidWorks uses, according to their documentation.
    tol.planar: the maximum distance from a plane a point can be and
                still be considered to be on the plane
    tol.facet_rsq: the minimum radius squared that an arc drawn from the
                   center of a face to the center of an adjacent face can
                   be to consider the two faces coplanar. This method is more
                   robust than considering just normal angles as it is tolerant
                   of numerical error on very small faces.
    '''

    def __init__(self, **kwargs):
        self.zero = 1e-12
        self.merge = 1e-8
        self.planar = 1e-5
        self.facet_rsq = 1e8
        self.fit = 1e-2
        self.id_len = 6
        self.__dict__.update(kwargs)


tol = NumericalToleranceMesh()


############################
# From trimesh.intersections
############################


def mesh_plane(vertices,
               faces,
               plane_normal,
               plane_origin,
               return_faces=False):
    '''
    Find a the intersections between a mesh and a plane,
    returning a set of line segments on that plane.

    Arguments
    ---------
    vertices:      (n, 3) float, the vertices in the mesh
    faces:         (m, 3) int, triangles of vertex indices
    plane_normal:  (3,) float, plane normal
    plane_origin:  (3,) float, plane origin
    return_faces:  bool, if True return face index line is from

    Returns
    ----------
    lines:      (m, 2, 3) float, list of 3D line segments
    face_index: (m,) int, index of mesh.faces for each line
    '''

    def triangle_cases(signs):
        '''
        Figure out which faces correspond to which intersection case from
        the signs of the dot product of each vertex.
        Does this by bitbang each row of signs into an 8 bit integer.

        code : signs      : intersects
        0    : [-1 -1 -1] : No
        2    : [-1 -1  0] : No
        4    : [-1 -1  1] : Yes; 2 on one side, 1 on the other
        6    : [-1  0  0] : Yes; one edge fully on plane
        8    : [-1  0  1] : Yes; one vertex on plane, 2 on different sides
        12   : [-1  1  1] : Yes; 2 on one side, 1 on the other
        14   : [0 0 0]    : No (on plane fully)
        16   : [0 0 1]    : Yes; one edge fully on plane
        20   : [0 1 1]    : No
        28   : [1 1 1]    : No

        Arguments
        ----------
        signs: (n,3) int, all values are -1,0, or 1
               Each row contains the dot product of all three vertices
               in a face with respect to the plane

        Returns
        ---------
        basic:      (n,) bool, which faces are in the basic intersection case
        one_vertex: (n,) bool, which faces are in the one vertex case
        one_edge:   (n,) bool, which faces are in the one edge case
        '''

        signs_sorted = np.sort(signs, axis=1)
        coded = np.zeros(len(signs_sorted), dtype=np.int8) + 14
        for i in range(3):
            coded += signs_sorted[:, i] << 3 - i

        # one edge fully on the plane
        # note that we are only accepting *one* of the on- edge cases,
        # where the other vertex has a positive dot product (16) instead
        # of both on- edge cases ([6,16])
        # this is so that for regions that are co-planar with the the section plane
        # we don't end up with an invalid boundary
        key = np.zeros(29, dtype=np.bool)
        key[16] = True
        one_edge = key[coded]

        # one vertex on plane, other two on different sides
        key[:] = False
        key[8] = True
        one_vertex = key[coded]

        # one vertex on one side of the plane, two on the other
        key[:] = False
        key[[4, 12]] = True
        basic = key[coded]

        return basic, one_vertex, one_edge

    def handle_on_vertex(signs, faces, vertices):
        # case where one vertex is on plane, two are on different sides
        vertex_plane = faces[signs == 0]
        edge_thru = faces[signs != 0].reshape((-1, 2))
        point_intersect, valid = plane_lines(plane_origin,
                                             plane_normal,
                                             vertices[edge_thru.T],
                                             line_segments=False)
        lines = np.column_stack((vertices[vertex_plane[valid]],
                                 point_intersect)).reshape((-1, 2, 3))
        return lines

    def handle_on_edge(signs, faces, vertices):
        # case where two vertices are on the plane and one is off
        edges = faces[signs == 0].reshape((-1, 2))
        points = vertices[edges]
        return points

    def handle_basic(signs, faces, vertices):
        # case where one vertex is on one side and two are on the other
        unique_element = unique_value_in_row(signs, unique=[-1, 1])
        edges = np.column_stack((faces[unique_element],
                                 faces[np.roll(unique_element, 1, axis=1)],
                                 faces[unique_element],
                                 faces[np.roll(unique_element, 2, axis=1)])).reshape((-1, 2))
        intersections, valid = plane_lines(plane_origin,
                                           plane_normal,
                                           vertices[edges.T],
                                           line_segments=False)
        # since the data has been pre- culled, any invalid intersections at all
        # means the culling was done incorrectly and thus things are
        # mega-fucked
        assert valid.all()
        return intersections.reshape((-1, 2, 3))

    plane_normal = np.asanyarray(plane_normal)
    plane_origin = np.asanyarray(plane_origin)
    if plane_origin.shape != (3,) or plane_normal.shape != (3,):
        raise ValueError('Plane origin and normal must be (3,)!')

    # dot product of each vertex with the plane normal, indexed by face
    # so for each face the dot product of each vertex is a row
    # shape is the same as mesh.faces (n,3)
    dots = np.dot(plane_normal, (vertices - plane_origin).T)[faces]

    # sign of the dot product is -1, 0, or 1
    # shape is the same as mesh.faces (n,3)
    signs = np.zeros(faces.shape, dtype=np.int8)
    signs[dots < -tol.merge] = -1
    signs[dots > tol.merge] = 1

    # figure out which triangles are in the cross section,
    # and which of the three intersection cases they are in
    cases = triangle_cases(signs)
    # handlers for each case
    handlers = (handle_basic,
                handle_on_vertex,
                handle_on_edge)

    lines = np.vstack([h(signs[c],
                         faces[c],
                         vertices) for c, h in zip(cases, handlers)])

    if return_faces:
        face_index = np.hstack([np.nonzero(c)[0] for c in cases])
        return lines, face_index
    return lines


def plane_lines(plane_origin,
                plane_normal,
                endpoints,
                line_segments=True):
    '''
    Calculate plane-line intersections

    Arguments
    ---------
    plane_origin:  plane origin, (3) list
    plane_normal:  plane direction (3) list
    endpoints:     (2, n, 3) points defining lines to be intersect tested
    line_segments: if True, only returns intersections as valid if
                   vertices from endpoints are on different sides
                   of the plane.

    Returns
    ---------
    intersections: (m, 3) list of cartesian intersection points
    valid        : (n, 3) list of booleans indicating whether a valid
                   intersection occurred
    '''
    endpoints = np.asanyarray(endpoints)
    plane_origin = np.asanyarray(plane_origin).reshape(3)
    line_dir = unitize(endpoints[1] - endpoints[0])
    plane_normal = unitize(np.asanyarray(plane_normal).reshape(3))

    t = np.dot(plane_normal, (plane_origin - endpoints[0]).T)
    b = np.dot(plane_normal, line_dir.T)

    # If the plane normal and line direction are perpendicular, it means
    # the vector is 'on plane', and there isn't a valid intersection.
    # We discard on-plane vectors by checking that the dot product is nonzero
    valid = np.abs(b) > tol.zero
    if line_segments:
        test = np.dot(plane_normal, np.transpose(plane_origin - endpoints[1]))
        different_sides = np.sign(t) != np.sign(test)
        nonzero = np.logical_or(np.abs(t) > tol.zero,
                                np.abs(test) > tol.zero)
        valid = np.logical_and(valid, different_sides)
        valid = np.logical_and(valid, nonzero)

    d = np.divide(t[valid], b[valid])
    intersection = endpoints[0][valid]
    intersection += np.reshape(d, (-1, 1)) * line_dir[valid]

    return intersection, valid


########################
# From trimesh.triangles
########################


def points_to_barycentric(triangles, points, method='cramer'):
    '''
    Find the barycentric coordinates of points relative to triangles.

    The Cramer's rule solution implements:
        http://blackpawn.com/texts/pointinpoly

    The cross product solution implements:
        https://www.cs.ubc.ca/~heidrich/Papers/JGT.05.pdf


    Arguments
    -----------
    triangles: (n,3,3) float, triangles in space
    points:    (n,3) float, point in space associated with a triangle
    method:    str, which method to compute the barycentric coordinates with. Options:
               -'cross': uses a method using cross products, roughly 2x slower but
                         different numerical robustness properties
               -anything else: uses a cramer's rule solution

    Returns
    -----------
    barycentric: (n,3) float, barycentric
    '''

    def method_cross():
        n = np.cross(edge_vectors[:, 0], edge_vectors[:, 1])
        denominator = diagonal_dot(n, n)

        barycentric = np.zeros((len(triangles), 3), dtype=np.float64)
        barycentric[:, 2] = diagonal_dot(
            np.cross(edge_vectors[:, 0], w), n) / denominator
        barycentric[:, 1] = diagonal_dot(
            np.cross(w, edge_vectors[:, 1]), n) / denominator
        barycentric[:, 0] = 1 - barycentric[:, 1] - barycentric[:, 2]
        return barycentric

    def method_cramer():
        dot00 = diagonal_dot(edge_vectors[:, 0], edge_vectors[:, 0])
        dot01 = diagonal_dot(edge_vectors[:, 0], edge_vectors[:, 1])
        dot02 = diagonal_dot(edge_vectors[:, 0], w)
        dot11 = diagonal_dot(edge_vectors[:, 1], edge_vectors[:, 1])
        dot12 = diagonal_dot(edge_vectors[:, 1], w)

        inverse_denominator = 1.0 / (dot00 * dot11 - dot01 * dot01)

        barycentric = np.zeros((len(triangles), 3), dtype=np.float64)
        barycentric[:, 2] = (dot00 * dot12 - dot01 *
                             dot02) * inverse_denominator
        barycentric[:, 1] = (dot11 * dot02 - dot01 *
                             dot12) * inverse_denominator
        barycentric[:, 0] = 1 - barycentric[:, 1] - barycentric[:, 2]
        return barycentric

    # establish that input triangles and points are sane
    triangles = np.asanyarray(triangles, dtype=np.float64)
    points = np.asanyarray(points, dtype=np.float64)
    if not is_shape(triangles, (-1, 3, 3)):
        raise ValueError('triangles shape incorrect')
    if not is_shape(points, (len(triangles), 3)):
        raise ValueError('triangles and points must correspond')

    edge_vectors = triangles[:, 1:] - triangles[:, :1]
    w = points - triangles[:, 0].reshape((-1, 3))

    if method == 'cross':
        return method_cross()
    return method_cramer()


#######################
# From trimesh.grouping
#######################


def unique_value_in_row(data, unique=None):
    '''
    For a 2D array of integers find the position of a value in each
    row which only occurs once. If there are more than one value per
    row which occur once, the last one is returned.
    Arguments
    ----------
    data:   (n,d) int
    unique: (m) int, list of unique values contained in data.
             speedup purposes only, generated from np.unique if not passed
    Returns
    ---------
    result: (n,d) bool, with one or zero True values per row.
    Example
    -------------------------------------
    In [0]: r = np.array([[-1,  1,  1],
                          [-1,  1, -1],
                          [-1,  1,  1],
                          [-1,  1, -1],
                          [-1,  1, -1]], dtype=np.int8)
    In [1]: unique_value_in_row(r)
    Out[1]:
           array([[ True, False, False],
                  [False,  True, False],
                  [ True, False, False],
                  [False,  True, False],
                  [False,  True, False]], dtype=bool)
    In [2]: unique_value_in_row(r).sum(axis=1)
    Out[2]: array([1, 1, 1, 1, 1])
    In [3]: r[unique_value_in_row(r)]
    Out[3]: array([-1,  1, -1,  1,  1], dtype=int8)
    '''
    if unique is None:
        unique = np.unique(data)
    data = np.asanyarray(data)
    result = np.zeros_like(data, dtype=np.bool, subok=False)
    for value in unique:
        test = np.equal(data, value)
        test_ok = test.sum(axis=1) == 1
        result[test_ok] = test[test_ok]
    return result


###################
# From trimesh.util
###################


def unitize(points, check_valid=False):
    '''
    Turn a list of vectors into a list of unit vectors.
    Arguments
    ---------
    points:       (n,m) or (j) input array of vectors.
                  For 1D arrays, points is treated as a single vector
                  For 2D arrays, each row is treated as a vector
    check_valid:  boolean, if True enables valid output and checking
    Returns
    ---------
    unit_vectors: (n,m) or (j) length array of unit vectors
    valid:        (n) boolean array, output only if check_valid.
                  True for all valid (nonzero length) vectors, thus
                  m=sum(valid)
    '''
    points = np.asanyarray(points)
    axis = len(points.shape) - 1
    length = np.sum(points ** 2, axis=axis) ** .5

    if is_sequence(length):
        length[np.isnan(length)] = 0.0

    if check_valid:
        valid = np.greater(length, tol.zero)
        if axis == 1:
            unit_vectors = (points[valid].T / length[valid]).T
        elif len(points.shape) == 1 and valid:
            unit_vectors = points / length
        else:
            unit_vectors = np.array([])
        return unit_vectors, valid
    else:
        unit_vectors = (points.T / length).T
    return unit_vectors


def is_sequence(obj):
    '''
    Returns True if obj is a sequence.
    '''
    seq = (not hasattr(obj, "strip") and
           hasattr(obj, "__getitem__") or
           hasattr(obj, "__iter__"))

    seq = seq and not isinstance(obj, dict)
    seq = seq and not isinstance(obj, set)

    # numpy sometimes returns objects that are single float64 values
    # but sure look like sequences, so we check the shape
    if hasattr(obj, 'shape'):
        seq = seq and obj.shape != ()
    return seq


def diagonal_dot(a, b):
    '''
    Dot product by row of a and b.

    Same as np.diag(np.dot(a, b.T)) but without the monstrous
    intermediate matrix.
    '''
    result = (np.asanyarray(a) *
              np.asanyarray(b)).sum(axis=1)
    return result


def is_shape(obj, shape):
    '''
    Compare the shape of a numpy.ndarray to a target shape,
    with any value less than zero being considered a wildcard

    Note that if a list- like object is passed that is not a numpy
    array, this function will not convert it and will return False.

    Arguments
    ---------
    obj: np.ndarray to check the shape of
    shape: list or tuple of shape.
           Any negative term will be considered a wildcard
           Any tuple term will be evaluated as an OR

    Returns
    ---------
    shape_ok: bool, True if shape of obj matches query shape

    Examples
    ------------------------
    In [1]: a = np.random.random((100,3))

    In [2]: a.shape
    Out[2]: (100, 3)

    In [3]: trimesh.util.is_shape(a, (-1,3))
    Out[3]: True

    In [4]: trimesh.util.is_shape(a, (-1,3,5))
    Out[4]: False

    In [5]: trimesh.util.is_shape(a, (100,-1))
    Out[5]: True

    In [6]: trimesh.util.is_shape(a, (-1,(3,4)))
    Out[6]: True

    In [7]: trimesh.util.is_shape(a, (-1,(4,5)))
    Out[7]: False
    '''

    if (not hasattr(obj, 'shape') or
            len(obj.shape) != len(shape)):
        return False

    for i, target in zip(obj.shape, shape):
        # check if current field has multiple acceptable values
        if is_sequence(target):
            if i in target:
                continue
            else:
                return False
        # check if current field is a wildcard
        if target < 0:
            if i == 0:
                return False
            else:
                continue
        # since we have a single target and a single value,
        # if they are not equal we have an answer
        if target != i:
            return False

    # since none of the checks failed, the two shapes are the same
    return True
