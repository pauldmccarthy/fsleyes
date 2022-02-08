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
about the input variables of a GLSL program. GLSL versions 1.20, 1.50, and
3.30 are supported.

 .. note:: The code in this module is based on work by Nicolas P. Rougier
           (https://github.com/rougier/glsl-parser), which is released under
           the New BSD license.

The main entry point to this module is the :func:`parseGLSL` function which,
given the source code of a GLSL program, parses it and returns information
about the program.

Only information about globally declared input variables is parsed and
returned. Interface blocks (section 4.3.7 of the GLSL 3.30 specification)
are not supported.
"""


import logging

import pyparsing as pp

import fsl.utils.memoize as memoize


log = logging.getLogger(__name__)



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
FLOAT      = pp.Regex(r'[+-]?(((\d+\.\d*)|(\d*\.\d+))'
                      r'([eE][-+]?\d+)?)|(\d*[eE][+-]?\d+)')
STORAGE    = pp.Regex(r'\b(uniform|attribute|in)\b')
PRECISION  = pp.Regex(r'\b(lowp|mediump|highp)\b')


def getDeclarations(code):
    """Get all global input variable declarations prefixed with a storage
    qualifier.

    A dictionary is returned, containing:
       - ``'uniform'``   - List of all declared ``uniform`` variables.
       - ``'attribute'`` - List of all declared  input variables, declared with
                           either ``attribute`` or ``in``.

    Both lists contain``(name, type, size)`` tuples.
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
            'attribute' : []}

    for (tokens, _, _) in DECLARATION.scanString(code):
        for _ in tokens.variable:

            size = tokens.size.strip()

            if size == '':  size = 1
            else:           size = int(size)

            if tokens.storage == 'uniform': ttype = 'uniform'
            else:                           ttype = 'attribute'

            decs[ttype].append((tokens.name, tokens.type, size))

    return decs


@memoize.memoizeMD5
def parseGLSL(source):
    """Parses the given GLSL source, and returns a dictionary containing
    all declared ``uniform`` and ``in`` / ``attribute`` variables.
    """
    decs = getDeclarations(source)
    return decs


def convert120to330(source, shaderType):
    """Convert GLSL 1.20 shader source to GLSL 3.30 compatible source in
    the quickest, hackiest, least robust way possible.

    ``shaderType`` is one of ``'vert'``, ``'frag'``, or ``'geom'``.
    """

    replacements = {
        'all' : [
            ('#version 120', '#version 330'),
            ('texture1D(',   'texture('),
            ('texture2D(',   'texture('),
            ('texture3D(',   'texture('),
            ('gl_FragColor', 'FragColor'),
            (r'attribute',   'in')],
        'vert' : [('varying', 'out')],
        'frag' : [('varying', 'in')],
    }

    replacements = replacements['all'] + replacements.get(shaderType, [])

    additions = {
        'frag' : ['out vec4 FragColor;']
    }

    lines    = source.split('\n')
    newlines = []

    for line in lines:
        newline = line
        for search, replace in replacements:
            if search in newline:
                newline = newline.replace(search, replace)

        newlines.append(newline)
        # Add new lines immediately after the #version line
        if shaderType in additions and '#version' in newline:
            newlines.extend(additions[shaderType])

    return '\n'.join(newlines)
