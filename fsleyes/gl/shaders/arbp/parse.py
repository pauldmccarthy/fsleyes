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


Instead, place holder expressions can be used in the source code. These
expressions may be parsed (using ``jinja2``) by the :func:`parseARBP`
function. Values can then be assigned to the place holders using the
:func:`fillARBP` function.


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
    # attributes, textures, varyings, and
    # constants.
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
    constants     = {}

    # Fill in the template
    vertSrc, fragSrc = parse.fillARBP(vertSrc,
                                      fragSrc,
                                      vertParams,
                                      vertParamLens,
                                      fragParams,
                                      fragParamLens,
                                      constants,
                                      textures,
                                      attrs)

    # Now you can compile the source
    # code and run your program!


Template expressions
--------------------


The following items may be specified as template expressions. As depicted in
the example above, an expression is specified in the following manner (with
the exception of constant values, which are described below)::

    {{ tokenPrefix_itemName }}


Prefixes for each item type are as follows:


 ===================== =================
 Item                  Expression prefix
 ===================== =================
 *Parameters*:         ``param``
 *Vertex attributes*   ``attr``
 *Textures*            ``texture``
 *Varying attributes*  ``varying``
 ===================== =================


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


This can be avoided by using texture expressions::

    TEX voxelValue, texCoord, {{ texture_imageTexture }}, 3D;


Varying attributes
==================


Varying attributes are attributes which are generated in the vertex program,
and passed through to the fragment program. They are equivalent to ``varying``
values in a GLSL program. In an ARB assembly program, they are typically
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


Constants
=========


All expressions in the source which do not fit into any of the above
categories are treated as "constant" values. These can be used to specify any
values which will not change across multiple executions of the program. As a
silly example, let's say you want to apply a fixed offset to some texture
coordinates. You could do this::

    !!ARBfp1.0
    # ...
    TEMP texCoord;
    MOV texCoord, {{ varying_texCoord }};
    ADD texCoord, texCoord, {{ my_fixed_offset }};

Then, when calling :func:`fillARBP` to generate the source code, add
``my_fixed_offset`` as a constant::

    vertSrc = '!!ARBvp1.0 vertex shader source'
    fragSrc = '!!ARBfp1.0 fragment shader source'

    items = parse.parseARBP(vertSrc, fragSrc)

    vertParams    = {}
    vertParamLens = {}
    fragParams    = {}
    fragParamLens = {}
    textures      = {}
    attrs         = {'texCoord'        : 0}
    constants     = {'my_fixed_offset' : '{0.1, 0.2, 0.3, 0}'}

    # Fill in the template
    vertSrc, fragSrc = parse.fillARBP(vertSrc,
                                      fragSrc,
                                      vertParams,
                                      vertParamLens,
                                      fragParams,
                                      fragParamLens,
                                      constants,
                                      textures,
                                      attrs)


Constant values can also be used in ``jinja2`` ``if` and ``for`` statements.
For example, to unroll a ``for`` loop, you could do this::

    !!ARBfp1.0
    # ...
    {% for i in range(num_iters) %}
    # ... do stuff repeatedly
    {% endfor %}

When generating the source, simply add a constant value called ``num_iters``,
specifying the desired number of iterations.


Including other files
=====================


By using this module, you are able to split your application logic across
multiple files and emulate function calls between them. As an example, let's
say that we want to test whether some texture coordinates are valid::


    !!ARBfp1.0

    TEMP textest;

    # do some stuff
    # ...

    # Check that the texture coordinates are in bounds
    MOV texCoord, {{ varying_texCoord }};

    # Test whether any coordinates are < 0.
    # Set textest.x to:
    #   - -1 if any coordinates are < 0
    #   - +1 if they are all >= 0
    CMP textest, texCoord, -1, 1;
    MIN textest.x, textest.x, textest.y;
    MIN textest.x, textest.x, textest.z;

    # Test whether any coordinates are < 0.
    # Set textest.y to:
    #   - -1 if any coordinates are > 1
    #   - +1 if they are all <= 1
    MUL textest.yzw, texCoord,     -1;
    SLT textest.yzw, textest.yzww, -1;
    MAD textest.yzw, textest.yzww   2, -1;
    MUL textest.yzw, textest.yzww, -1;
    MIN textest.y, textest.y, textest.z;
    MIN textest.y, textest.y, textest.w;

    # Set textest.x to:
    #   - -1 if any component of texCoord is < 0 or > 1
    #   - +1 otherwise
    MIN textest.x, textest.x, textest.y;

    # Kill the fragment if the texture
    # coordinates are out of bounds
    KIL textest.x;

    # Othewrwise, carry on
    # processing the fragment.
    # ...


This may be a common operation which we would like to re-use in other fragment
programs. We can do this by using expressions in place of the inputs and
outputs of the routine. First, create a new file called, for example,
``textest.prog``, containing the texture coordinate test routine::

    #
    # textest.prog - test whether texture coordinates are in bounds.
    #
    # Inputs:
    #   - texCoord    - texture coordinates to test
    # Outputs:
    #   - out_textest - The x component will be +1 if the texture coordinates
    #                   are in bounds, -1 otherwise.

    # Test whether any coordinates are < 0.
    # Set textest.x to:
    #   - -1 if any coordinates are < 0
    #   - +1 if they are all >= 0
    CMP {{ out_textest }}, {{ texCoord }} , -1, 1;
    MIN {{ out_textest }}.x, {{ out_textest }}.x, {{ out_textest }}.y;
    MIN {{ out_textest }}.x, {{ out_textest }}.x, {{ out_textest }}.z;

    # Test whether any coordinates are < 0.
    # Set textest.y to:
    #   - -1 if any coordinates are > 1
    #   - +1 if they are all <= 1
    MUL {{ out_textest }}.yzw, {{ texCoord    }},      -1;
    SLT {{ out_textest }}.yzw, {{ out_textest }}.yzww, -1;
    MAD {{ out_textest }}.yzw, {{ out_textest }}.yzww   2, -1;
    MUL {{ out_textest }}.yzw, {{ out_textest }}.yzww, -1;
    MIN {{ out_textest }}.y,   {{ out_textest }}.y,    {{ out_textest }}.z;
    MIN {{ out_textest }}.y,   {{ out_textest }}.y,    {{ out_textest }}.w;

    # Set textest.x to:
    #   - -1 if any component of texCoord is < 0 or > 1
    #   - +1 otherwise
    MIN {{ out_textest ]}.x, {{ out_textest }}.x, {{ out_textest }}.y;


You can then use this routine in any fragment program like so::

    !!ARBfp1.0

    # Make the textest routine
    # available to this program. This
    # (and other includes) must occur
    # at the top of your program.
    {{ arb_include('textest.prog') }}

    TEMP textest;

    # do some stuff
    # ...

    MOV texCoord, {{ varying_texCoord }};

    # Check that the texture coordinates are in bounds
    {{ arb_call('textest.prog',
                texCoord='{{ varying_texCoord }}',
                out_result='textest') }}

    # Kill the fragment if the texture
    # coordinates are out of bounds
    KIL textest.x;

    # Othewrwise, carry on
    # processing the fragment.
    # ...

The only requirement in the expression names that you use are that the
routine's output variables must start with ``'out_'``.


The ``arb_include`` function requires you to pass the name of the routine file
that you wish to use - this must be specified relative to the ``includePath``
argument to the :func:`parseARBP` function.


The ``arb_call`` function requires:

  - The name of the routine file (must be identical to that passed to
    ``arb_include``)

  - Mappings between the variables in your code, and the routine's input and
    output parameters. These must all be passed as named (keyword) arguments.
"""


import os.path     as op
import itertools   as it
import                re
import                random
import                string

import jinja2      as j2
import jinja2.meta as j2meta


TEMPLATE_BUILTIN_CONSTANTS = ['range', 'arb_call', 'arb_include']
"""List of constant variables which may occur in source files, and which are
provided by ``jinja2``, or provided by this module.

As of ``jinja2`` version 2.9.6, the ``jinja2.meta.find_undeclared_variables``
function will return built-in functions such as ``range``, so our
:func:`_findDeclaredVariables`` has to filter them out, and it uses this list
to do so.
"""


def parseARBP(vertSrc, fragSrc):
    """Parses the given ``ARB_vertex_program`` and ``ARB_fragment_program``
    code, and returns information about all declared variables.
    """

    vvars = _findDeclaredVariables(vertSrc)
    fvars = _findDeclaredVariables(fragSrc)

    _checkVariableValidity(vvars, fvars, {}, {}, {}, {}, {})

    vParams, vTextures, vAttrs, vVaryings, vConstants = vvars
    fParams, fTextures, fAttrs, fVaryings, fConstants = fvars

    constants = list(set(list(vConstants) + list(fConstants)))

    return {'vertParam' : vParams,
            'fragParam' : fParams,
            'attr'      : vAttrs,
            'texture'   : fTextures,
            'varying'   : vVaryings,
            'constant'  : constants}


def fillARBP(vertSrc,
             fragSrc,
             vertParams,
             vertParamLens,
             fragParams,
             fragParamLens,
             constants,
             textures,
             attrs,
             includePath):
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

    :arg constants:     Dictionary of ``{name : value}`` mappings,
                        specifying any variables used in the ARB template
                        that are not vertex or fragment program parameters
                        (e.g. vars used in if blocks or for loops).

    :arg textures:      Dictionary of `{name : textureUnit}`` mappings,
                        specifying the texture unit to use for each texture.

    :arg attrs:         Dictionary of `{name : textureUnit}`` mappings,
                        specifying the texture unit to use for each vertex
                        attribute.

    :arg includePath:   Path to a directory which contains any additional
                        files that may be included in the given source files.
    """

    vertVars = _findDeclaredVariables(vertSrc)
    fragVars = _findDeclaredVariables(fragSrc)

    _checkVariableValidity(vertVars,
                           fragVars,
                           vertParams,
                           fragParams,
                           textures,
                           attrs,
                           constants)

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

    vertVars = dict(it.chain(vertParams  .items(),
                             textures    .items(),
                             attrs       .items(),
                             vertVaryings.items(),
                             constants   .items()))
    fragVars = dict(it.chain(fragParams  .items(),
                             textures    .items(),
                             fragVaryings.items(),
                             constants   .items()))

    vertSrc = _render(vertSrc, vertVars, includePath)
    fragSrc = _render(fragSrc, fragVars, includePath)

    return vertSrc, fragSrc


def _render(src, env, includePath):
    """Called by :func:parseARBP`. Renders the given source template using the
    given environment, managing the logic for ``arb_include`` and ``arb_call``
    expressions.
    """

    # 'includes' is a dict containing mappings
    # for each included routine file. For each
    # file, the value is a tuple containing:
    #
    #   - The source code
    #   - A dictionary of {input_key  : unique_name} mappings
    #   - A dictionary of {output_key : unique_name} mappings
    includes     = {}
    usedVarNames = set()

    # Generate a random name to
    # use as a TEMP variable
    def randomName(prefix):

        def _rn():
            suffix = [random.choice(string.ascii_letters) for i in range(5)]
            return '{}_{}'.format(prefix, ''.join(suffix))

        name = _rn()
        while name in usedVarNames:
            name = _rn()

        usedVarNames.add(name)

        return name

    # arb_include routine
    def arb_include(filename):

        # 1. Loads in the included source file
        # 2. Generates unique names for input/output parameters
        # 3. Adds the source code, and the input/output mappings,
        #    to the includes dictionary
        # 4. Generates and returns TEMP declarations for ins/outs

        fileid   = op.splitext(filename)[0]
        filename = op.join(includePath, filename)

        with open(filename, 'rt') as f:
            source = f.read()

        env      = j2.Environment()
        ast      = env.parse(source)
        params   = j2meta.find_undeclared_variables(ast)

        inputs      = {}
        outputs     = {}
        sourceLines = ['# include {}'.format(fileid)]

        for param in params:

            name = randomName('{}_{}'.format(fileid, param))
            if param.startswith('out_'): outputs[param] = name
            else:                        inputs[ param] = name

            sourceLines.append('TEMP {};'.format(name))

        includes[op.basename(filename)] = source, inputs, outputs

        return '\n'.join(sourceLines)

    # arb_call routine
    def arb_call(filename, **args):

        # 1. Looks up the called filename in the includes dictionary
        # 2. Generates code:
        #    a. MOV inputs to function input temps
        #    b. Render file source
        #    c. MOV function outputs to requested output
        # 3. Return generated code

        source, inputs, outputs = includes[filename]

        sourceLines = ['# call {}'.format(filename)]

        callTemplate = j2.Template(source)

        source = callTemplate.render(**inputs, **outputs)

        for inkey, invarname in inputs.items():
            sourceLines.append('MOV {}, {};'.format(invarname, args[inkey]))

        sourceLines.extend(source.split('\n'))

        for outkey, outvarname in outputs.items():
            sourceLines.append('MOV {}, {};'.format(args[outkey], outvarname))

        return '\n'.join(sourceLines)

    template = j2.Template(src)

    env = dict(env)
    env['arb_include'] = arb_include
    env['arb_call']    = arb_call

    # We need to do two passes of the
    # source code, because arb_call
    # arguments may contain un-rendered
    # expressions (e.g. the
    # '{{ varying_texCoord }}' in the
    # documentation example).
    for i in range(2):
        template = j2.Template(src)
        src      = template.render(**env)

    return src


def _findDeclaredVariables(source):
    """Parses the given ARB assembly program source, and returns information
    about all template tokens defined within. Returns a sequence of lists,
    which contain the names of:

      - Parameters
      - Textures
      - Vertex attributes
      - Varying attributes
      - Constants
    """

    env   = j2.Environment()
    ast   = env.parse(source)
    svars = j2meta.find_undeclared_variables(ast)

    pExpr = re.compile('^param([1-9]*)_(.+)$')
    tExpr = re.compile('^texture_(.+)$')
    aExpr = re.compile('^attr_(.+)$')
    vExpr = re.compile('^varying_(.+)$')

    params    = []
    textures  = []
    attrs     = []
    varyings  = []
    constants = []

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
            break
        else:
            constants.append(v)

    constants = [c for c in constants if c not in TEMPLATE_BUILTIN_CONSTANTS]

    return [sorted(v) for v in [params, textures, attrs, varyings, constants]]


def _checkVariableValidity(vertVars,
                           fragVars,
                           vertParamMap,
                           fragParamMap,
                           textureMap,
                           attrMap,
                           constantMap):
    """Checks the information about a vertex/fragment program, and raises
    an error if it looks like something is wrong.
    """
    vParams, vTextures, vAttrs, vVaryings, vConstants = vertVars
    fParams, fTextures, fAttrs, fVaryings, fConstants = fragVars

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
