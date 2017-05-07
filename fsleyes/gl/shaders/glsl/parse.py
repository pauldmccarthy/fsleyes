#!/usr/bin/env python
#
# parse.py - Simple parser for extracting information about a GLSL program.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
# Based on work by Nicolas P. Rougier
# <https://github.com/rougier/glsl-parser>, which is released under the New
# BSD license.
#
# Copyright (c) 2014, Nicolas P. Rougier
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
"""This module implements a simple GLSL parser, for extracting information
about a GLSL program.

 .. note:: The code in this module is based on work by Nicolas P. Rougier
           (https://github.com/rougier/glsl-parser), which is released under
           the New BSD license.

The main entry point to this module is the :func:`parseGLSL` function which,
given the source code of a GLSL program, parses it and returns information
about the program.
"""


from __future__ import print_function

import sys
import logging

import pyparsing as pp

import fsl.utils.memoize as memoize


log = logging.getLogger(__name__)


KEYWORDS  = ('attribute const uniform varying break continue do for while '
             'if else '
             'in out inout '
             'float int void bool true false '
             'lowp mediump highp precision invariant  '
             'discard return '
             'mat2 mat3 mat4 '
             'vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 sampler2D '
             'samplerCube '
             'struct')
RESERVED  = ('asm '
             'class union enum typedef template this packed '
             'goto switch default '
             'inline noinline volatile public static extern external '
             'interface flat long short double half fixed unsigned superp '
             'input output '
             'hvec2 hvec3 hvec4 dvec2 dvec3 dvec4 fvec2 fvec3 fvec4 sampler1D '
             'sampler3D '
             'sampler1DShadow sampler2DShadow '
             'sampler2DRect sampler3DRect sampler2DRectShadow '
             'sizeof cast '
             'namespace using ')
PRECISION = 'lowp mediump high'
STORAGE   = 'const uniform attribute varying'


# Tokens
# ----------------------------------
LPAREN     = pp.Literal("(").suppress()
RPAREN     = pp.Literal(")").suppress()
LBRACK     = pp.Literal("[").suppress()
RBRACK     = pp.Literal("]").suppress()
LBRACE     = pp.Literal("{").suppress()
RBRACE     = pp.Literal("}").suppress()
IDENTIFIER = pp.Word(pp.alphas + '_', pp.alphanums + '_')
TYPE       = pp.Word(pp.alphas + '_', pp.alphanums + "_")
END        = pp.Literal(";").suppress()
INT        = pp.Word(pp.nums)
FLOAT      = pp.Regex('[+-]?(((\d+\.\d*)|(\d*\.\d+))'
                      '([eE][-+]?\d+)?)|(\d*[eE][+-]?\d+)')
STORAGE    = pp.Regex('|'.join(STORAGE.split(' ')))
PRECISION  = pp.Regex('|'.join(PRECISION.split(' ')))
STRUCT     = pp.Literal("struct").suppress()


def getDeclarations(code):
    """Get all declarations prefixed with a storage qualifier.

    *Code example*

    ::
        uniform lowp vec4 fg_color = vec4(1),
                          bg_color = vec4(vec3(0),1);
    """

    # Callable expression
    EXPRESSION  = pp.Forward()
    ARG         = pp.Group(EXPRESSION) | IDENTIFIER | FLOAT | INT
    ARGS        = pp.delimitedList(ARG)
    EXPRESSION << IDENTIFIER + pp.Group(LPAREN + pp.Optional(ARGS) + RPAREN)

    # Value
    VALUE = (EXPRESSION |
             pp.Word(pp.alphanums + '_()+-/*')).setParseAction(
                 pp.originalTextFor)

    # Single declaration
    VARIABLE = (IDENTIFIER.setResultsName('name') +
                pp.Optional(LBRACK +
                            (INT | IDENTIFIER).setResultsName('size') +
                            RBRACK) +
                pp.Optional(pp.Literal("=").suppress() +
                            VALUE.setResultsName('value')))

    # Several declarations at once
    DECLARATION = (STORAGE.setResultsName('storage') +
                   pp.Optional(PRECISION).setResultsName('precision') +
                   TYPE.setResultsName('type') +
                   pp.delimitedList(
                       VARIABLE.setResultsName('variable',
                                               listAllMatches=True)) +
                   END)
    DECLARATION.ignore(pp.cStyleComment)

    decs = {'uniform'   : [],
            'varying'   : [],
            'attribute' : []}

    for (tokens, start, end) in DECLARATION.scanString(code):
        for token in tokens.variable:

            if tokens.storage not in decs:
                log.debug('Skipping declaration with unknown storage '
                          'qualifier: {}'.format(tokens.storage))
                continue

            decs[tokens.storage].append((tokens.name, tokens.type))

    return decs


@memoize.memoizeMD5
def parseGLSL(source):
    """Parses the given GLSL source, and returns:
      - The attribute declarations.
    """
    decs = getDeclarations(source)
    return decs


def main():
    """If this module is executed as a script, this function is called.
    It expects a path to a ``glsl`` file as a single parameter. This file
    is parsed, and information about it printed to standard output.
    """

    if len(sys.argv) != 2:
        print('Usage: {}.py file.glsl'.format(__name__))
        sys.exit(0)

    infile = sys.argv[1]

    print('File: {}'.format(infile))

    with open(infile, 'rt') as f:
        code = f.read()

    decs = parseGLSL(code)

    for d, v in decs.items():
        print('\n--{}--\n'.format(d.upper()))
        for t, n in v:
            print('{}: {}'.format(t, n))


if __name__ == '__main__':
    main()
