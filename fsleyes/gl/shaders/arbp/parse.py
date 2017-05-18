#!/usr/bin/env python
#
# parse.py - Very simple parser for ARB assembly shader programs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides functions for use with OpenGL ``ARB_vertex_program``
and ``ARB_fragment_program`` assembly source code. It defines a simple
templating system, allowing ARB assembly programs to be written in such a way
that input parameters, vertex attributes, texture locations, and texture
coordinates and do not have to be hard coded in the source.


.. note:: This module is used by the :class:`.ARBPShader` class - if you use
          the :class:`.ARBShader` class, you will not need to use this module
          at all.


Instead, place holder tokens can be used in the source code. These tokens may
be parsed (using ``jinja2``) by the :func:`parseARBP` function. Values can
then be assigned to the place holders using the :func:`fillARBP` function.


An example
----------

As an example, consider the following vertex program, for drawing a slice
from a 3D image texture::


    !!ARBvp1.0

    PARAM imageShape = program.local[0];

    # Transform the vertex position into display coordinates
    DP4 result.position.x, state.matrix.mvp.row[0], vertex.position;
    DP4 result.position.y, state.matrix.mvp.row[1], vertex.position;
    DP4 result.position.z, state.matrix.mvp.row[2], vertex.position;
    DP4 result.position.w, state.matrix.mvp.row[3], vertex.position;

    # Transform the texture coordinates (which are
    # between 0 and 1) into voxel coordinates (which
    # are within the image voxel dimensions).
    MOV voxCoord, vertex.texcoord[0];
    MUL voxCoord, voxCoord, imageShape;

    # Pass the texture coordinates and
    # corresponding voxel coordinates
    # through to the fragment program.
    MOV result.texcoord[0], vertex.texcoord[0];
    MOV result.texcoord[1], voxCoord;

    END


And the corresponding fragment program, which looks up the voxel value
and colours the fragment accordingly::


    !!ARBfp1.0

    TEMP voxValue;

    # A transformation matrix (encoding a linear
    # offset/scale) which transforms a voxel value
    # from the image texture data range to the
    # colour map texture input coordinate range.
    PARAM voxValXform[4] = { program.local[0],
                             program.local[1],
                             program.local[2],
                             program.local[3] };

    # Get the voxel value
    TEX voxValue.x, fragment.texcoord[0], texture[0], 3D;

    # Transform the voxel value
    MAD voxValue, voxValue, voxValXform[0].x, voxValXform[3].x;

    # Get the colour that corresponds to the voxel value
    TEX result.color, voxValue.x, texture[1], 1D;


This program requires:

 - The image shape to be specified as a program parameter at index 0.

 - Image texture coordinates to be passed as coordinates on texture unit 0.

 - Both the vertex and fragment programs to know which texture units the
   texture and voxel coordinates are passed through on.

 - The image texture to be bound to texture unit 0.

 - The colour map texture to be bound to texture unit 1.


By using this module, all of these requirements can be removed by re-writing
the vertex program as follows::


    !!ARBvp1.0

    PARAM imageShape = {{ param_imageShape }};

    TEMP voxCoord;

    # Transform the vertex position into display coordinates
    DP4 result.position.x, state.matrix.mvp.row[0], vertex.position;
    DP4 result.position.y, state.matrix.mvp.row[1], vertex.position;
    DP4 result.position.z, state.matrix.mvp.row[2], vertex.position;
    DP4 result.position.w, state.matrix.mvp.row[3], vertex.position;

    # Transform the texture coordinates (which are
    # between 0 and 1) into voxel coordinates (which
    # are within the image voxel dimensions).
    MOV voxCoord, {{ attr_texCoord }};
    MUL voxCoord, voxCoord, imageShape;

    # Pass the texture coordinates and
    # corresponding voxel coordinates
    # through to the fragment program.
    MOV {{ varying_texCoord }}, {{ attr_texCoord }};
    MOV {{ varying_voxCoord }}, voxCoord;

    END


And the fragment program::


    !!ARBfp1.0

    TEMP voxValue;

    # A transformation matrix (encoding a linear
    # offset/scale) which transforms a voxel value
    # from the image texture data range to the
    # colour map texture input coordinate range.
    PARAM voxValXform[4] = {{ param4_voxValXform }};

    # Get the voxel value
    TEX voxValue.x, {{ varying_texCoord }}, {{ texture_imageTexture }}, 3D;

    # Transform the voxel value
    MAD voxValue, voxValue, voxValXform[0].x, voxValXform[3].x;

    # Get the colour that corresponds to the voxel value
    TEX result.color, voxValue.x, {{ texture_colourMapTexture }}, 1D;


The :func:`parseARBP` function parses the source code and returns information
about all declared items. The :func:`fillARBP` function can then be used to
assign explicit values to each of the items::


    vertSrc = '!!ARBvp1.0 vertex shader source'
    fragSrc = '!!ARBfp1.0 fragment shader source'

    # Get information about all parameters,
    # attributes, textures, and varyings.
    items = parse.parseARBP(vertSrc, fragSrc)

    # ...
    # You have to calculate positions for
    # parameters, attributes and textures.
    # Positions for varying items are
    # automatically calculated for you.
    # ...
    vertParams    = {'imageShape'        : 0}
    vertParamLens = {'imageShape'        : 1}
    fragParams    = {'voxValXform'       : 0}
    fragParamLens = {'voxValXform'       : 4}
    textures      = {'imageTexture'      : 0,
                     'colourMapTexture'  : 1}
    attrs         = {'texCoord'          : 0}

    # Fill in the template
    vertSrc, fragSrc = parse.fillARBP(vertSrc,
                                      fragSrc,
                                      vertParams,
                                      vertParamLens,
                                      fragParams,
                                      fragParamLens,
                                      textures,
                                      attrs)

    # Now you can compile the source
    # code and run your program!


Template tokens
---------------


The following items may be specified as template tokens. As depicted in
the example above, a token is specified in the following manner::

    {{ tokenPrefix_itemName }}


Prefixes for each item type are as follows:


 ===================== ============
 Item                  Token prefix
 ===================== ============
 *Parameters*:         ``param``
 *Vertex attributes*   ``attr``
 *Textures*            ``texture``
 *Varying attributes*  ``varying``
 ===================== ============


Parameters
==========

*Parameters* are constant values which are passed to every instantiation of a
shader program - they are equivalent to ``uniform`` values in a GLSL program.
In a normal ARB assembly program, parameters are accessed as follows::

    PARAM imageShape = program.local[0];


When using this module, you may instead access parameters in this way::

    PARAM imageShape = {{ param_imageShape }};


Parameters with a length greater than 1 (e.g. matrix parameters) are
traditionally accessed in this way::

    PARAM xform[4] = { program.local[0],
                       program.local[1],
                       program.local[2],
                       program.local[3] };


When using this module, you may access matrix parameters in this way::

    PARAM xform[4] = {{ param4_xform }};


Vertex attributes
=================


*Vertex attributes* are values which are associated with every rendered
vertex. They are equivalent to ``attribute`` values in a GLSL program.
In a normal ARB assembly program, one would typically pass vertex
attributes as texture coordinates bound to a specified texture unit::

    PARAM texCoord = vertex.texcoord[0];


When using this module, you may access vertex attributes as follows::

    PARAM texCoord = {{ attr_texCoord }};


Textures
========

In a typical ARB assembly program, the texture unit to which each texture is
bound must be hard coded::

    TEX voxelValue, texCoord, texture[0], 3D;


This can be avoided by using texture tokens::

    TEX voxelValue, texCoord, {{ texture_imageTexture }}, 3D;


Varying attributes
==================


Varying attributes are attributes which are generated in the vertex program,
and passed through to the fragment program. They are equivalent to ``varying``
values in a GLSXL program. In an ARB assembly program, they are typically
passed and accessed as texture coordinates::

    !!ARBvp1.0
    # In the vertex program, we pass varying
    # attribute through as texture coordinates:
    MOV result.texcoord[0], texCoord;
    MOV result.texcoord[1], voxCoord;
    # ...


    !!ARBfp1.0
    # ...
    # In the fragment program, we access varying
    # attrbutes as texture coordinates
    TEMP texCoord;
    TEMP voxCoord;
    MOV texCoord, fragment.texcoord[0];
    MOV voxCoord, fragment.texcoord[1];
    # ...


This can be avoided by using the :func:`fillARBP` function, which will
automatically assign texture coordinate positions to each varying attribute.
The assembly code can thus be re-written as follows::

    !!ARBvp1.0
    # ...
    MOV {{ varying_texCoord }}, texCoord;
    MOV {{ varying_voxCoord }}, voxCoord;
    # ...


    !!ARBfp1.0
    # ...
    TEMP texCoord;
    TEMP voxCoord;
    MOV texCoord, {{ varying_texCoord }};
    MOV voxCoord, {{ varying_voxCoord }};
    # ...
"""


import itertools   as it
import                re

import jinja2      as j2
import jinja2.meta as j2meta


def parseARBP(vertSrc, fragSrc):
    """Parses the given ``ARB_vertex_program`` and ``ARB_fragment_program``
    code, and returns information about all declared variables.
    """

    vParams, vTextures, vAttrs, vVaryings = _findDeclaredVariables(vertSrc)
    fParams, fTextures, fAttrs, fVaryings = _findDeclaredVariables(fragSrc)

    _checkVariableValidity((vParams, vTextures, vAttrs, vVaryings),
                           (fParams, fTextures, fAttrs, fVaryings),
                           {}, {}, {}, {})

    return {'vertParam' : vParams,
            'fragParam' : fParams,
            'attr'      : vAttrs,
            'texture'   : fTextures,
            'varying'   : vVaryings}


def fillARBP(vertSrc,
             fragSrc,
             vertParams,
             vertParamLens,
             fragParams,
             fragParamLens,
             textures,
             attrs):
    """Fills in the given ARB assembly code, replacing all template tokens
    with the values specified by the various arguments.

    :arg vertSrc:       Vertex program source.

    :arg fragSrc:       Fragment program source.

    :arg vertParams:    Dictionary of ``{name : position}`` mappings,
                        specifying the position indices of all vertex
                        program parameters.

    :arg vertParamLens: Dictionary ``{name : length}`` mappings,
                        specifying the lengths of all vertex program
                        parameters.

    :arg fragParams:    Dictionary of ``{name : position}`` mappings,
                        specifying the position indices of all fragment
                        program parameters.

    :arg fragParamLens: Dictionary ``{name : length}`` mappings,
                        specifying the lengths of all fragment program
                        parameters.

    :arg textures:      Dictionary of `{name : textureUnit}`` mappings,
                        specifying the texture unit to use for each texture.

    :arg attrs:         Dictionary of `{name : textureUnit}`` mappings,
                        specifying the texture unit to use for each vertex
                        attribute.
    """

    vertVars = _findDeclaredVariables(vertSrc)
    fragVars = _findDeclaredVariables(fragSrc)

    _checkVariableValidity(
        vertVars, fragVars, vertParams, fragParams, textures, attrs)

    for name, number in list(vertParams.items()):

        length = vertParamLens[name]

        if length == 1: name = 'param_{}'  .format(name)
        else:           name = 'param{}_{}'.format(length, name)

        vertParams[name] = _param(number, length)

    for name, number in list(fragParams.items()):

        length = fragParamLens[name]

        if length == 1: name = 'param_{}'  .format(name)
        else:           name = 'param{}_{}'.format(length, name)

        fragParams[name] = _param(number, length)

    textures = {'texture_{}'.format(n) : _texture(v)
                for n, v in textures.items()}

    attrs = {'attr_{}'.format(n) : _attr(v) for n, v in attrs.items()}
    varyings     = _makeVaryingMap(vertVars[3], fragVars[3])
    vertVaryings = {}
    fragVaryings = {}

    for name, num in varyings.items():
        vertVaryings['varying_{}'.format(name)] = _varying(num, True)
        fragVaryings['varying_{}'.format(name)] = _varying(num, False)

    vertTemplate  = j2.Template(vertSrc)
    fragTemplate  = j2.Template(fragSrc)

    vertVars = dict(it.chain(vertParams  .items(),
                             textures    .items(),
                             attrs       .items(),
                             vertVaryings.items()))
    fragVars = dict(it.chain(fragParams  .items(),
                             textures    .items(),
                             fragVaryings.items()))

    vertSrc = vertTemplate.render(**vertVars)
    fragSrc = fragTemplate.render(**fragVars)

    return vertSrc, fragSrc


def _findDeclaredVariables(source):
    """Parses the given ARB assembly program source, and returns information
    about all template tokens defined within.
    """

    env   = j2.Environment()
    ast   = env.parse(source)
    svars = j2meta.find_undeclared_variables(ast)

    pExpr = re.compile('^param([1-9]*)_(.+)$')
    tExpr = re.compile('^texture_(.+)$')
    aExpr = re.compile('^attr_(.+)$')
    vExpr = re.compile('^varying_(.+)$')

    params   = []
    textures = []
    attrs    = []
    varyings = []

    for v in svars:
        for expr, namelist in zip([pExpr,  tExpr,    aExpr, vExpr],
                                  [params, textures, attrs, varyings]):

            match = expr.match(v)

            if match is None:
                continue

            if expr is pExpr:
                length = match.group(1)
                name   = match.group(2)

                if length == '': length = 1
                else:            length = int(length)
                namelist.append((name, length))
            else:
                name = match.group(1)
                namelist.append(name)

    return [sorted(v) for v in [params, textures, attrs, varyings]]


def _checkVariableValidity(vertVars,
                           fragVars,
                           vertParamMap,
                           fragParamMap,
                           textureMap,
                           attrMap):
    """Checks the information about a vertex/fragment program, and raises
    an error if it looks like something is wrong.
    """
    vParams, vTextures, vAttrs, vVaryings = vertVars
    fParams, fTextures, fAttrs, fVaryings = fragVars

    vParams = [vp[0] for vp in vParams]
    fParams = [fp[0] for fp in fParams]

    # TODO Custom error type, and more useful error messages.
    if len(vTextures) != 0:
        raise ValueError('Texture access in vertex program')

    if len(fAttrs) != 0:
        raise ValueError('Attribute access in fragment program')

    if any([n not in vVaryings for n in fVaryings]):
        raise ValueError('Fragment/vertex varyings do not match')

    if any([n not in vParams for n in vertParamMap]):
        raise ValueError('Unknown variable in vertex parameter map.')

    if any([n not in fParams for n in fragParamMap]):
        raise ValueError('Unknown variable in fragment parameter map.')

    if any([n not in fTextures for n in textureMap]):
        raise ValueError('Unknown variable in texture parameter map.')

    if any([n not in vAttrs for n in attrMap]):
        raise ValueError('Unknown variable in attribute parameter map.')


def _makeVaryingMap(vertVaryings, fragVaryings):
    """Generates texture unit indices for all varying attributes. """

    indices    = range(len(vertVaryings))
    varyingMap = dict(zip(vertVaryings, indices))
    return varyingMap


def _param(number, length):
    """Generates ARB assembly for the named vertex/fragment program parameter.
    """

    if length == 1:
        return 'program.local[{}]'.format(number)
    else:
        bits = ['program.local[{}]'.format(n) for n in range(number,
                                                             number + length)]

        return '{{ {} }}'.format(', '.join(bits))


def _texture(number):
    """Generates ARB assembly for a texture."""
    return 'texture[{}]'.format(number)


def _attr(number):
    """Generates ARB assembly for a vertex attribute. """
    return 'vertex.texcoord[{}]'.format(number)


def _varying(number, vert):
    """Generates ARB assembly for a varying attribute. """
    if vert: return 'result.texcoord[{}]'  .format(number)
    else:    return 'fragment.texcoord[{}]'.format(number)
