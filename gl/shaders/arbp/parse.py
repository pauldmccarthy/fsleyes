#!/usr/bin/env python
#
# parse.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import                re

import jinja2      as j2
import jinja2.meta as j2meta


#
# {{ param_paramName }} -> program.local[X]
#
# Or, if 'paramName' has length > 1
#
# {{ param4_paramName }} -> { program.local[x], program.local[x + 1], ... }

# {{ attr_attName }}     -> vertex.texcoord[N]
#
# {{ texture_texName }} -> texture[N]


# Maybe this too? In vertex program:
# {{ varying_outputName }} -> result.texcoord[N]
#
# In fragment program:
# {{ varying_outputName }} -> fragment.texcoord[N]


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


def fillARBP(vertSrc, fragSrc, vertParams, fragParams, textures, attrs):
    
    if vertParams   is None: vertParams = {}
    if fragParams   is None: fragParams = {}
    if textures     is None: textures   = {}
    if attrs        is None: attrs      = {}

    vertVars = _findDeclaredVariables(vertSrc)
    fragVars = _findDeclaredVariables(fragSrc)
    
    _checkVariableValidity(
        vertVars, fragVars, vertParams, fragParams, textures, attrs)

    for name, (number, length) in vertParams.items():
        
        if length == 1: name = 'param_{}'  .format(name)
        else:           name = 'param{}_{}'.format(name, length)
        
        vertParams[name] = _param(number, length)
        
    for name, (number, length) in fragParams.items():
        
        if length == 1: name = 'param_{}'  .format(name)
        else:           name = 'param{}_{}'.format(name, length)
        
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
    
    vertVars = dict(vertParams  .items() +
                    textures    .items() +
                    attrs       .items() +
                    vertVaryings.items())
    fragVars = dict(fragParams  .items() +
                    textures    .items() +
                    fragVaryings.items()) 
    
    vertSrc = vertTemplate.render(**vertVars)
    fragSrc = fragTemplate.render(**fragVars)

    return vertSrc, fragSrc 


def _findDeclaredVariables(source):

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

    return map(sorted, (params, textures, attrs, varyings))


def _checkVariableValidity(vertVars,
                           fragVars,
                           vertParamMap,
                           fragParamMap,
                           textureMap,
                           attrMap):
    vParams, vTextures, vAttrs, vVaryings = vertVars
    fParams, fTextures, fAttrs, fVaryings = fragVars

    vParams = [vp[0] for vp in vParams]
    fParams = [fp[0] for fp in fParams]

    # TODO Custom error type, and more useful error messages.
    if len(vTextures) != 0:
        raise ValueError('Texture access in vertex program')

    if len(fAttrs) != 0:
        raise ValueError('Attribute access in fragment program')

    if vVaryings != fVaryings:
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

    indices    = range(len(vertVaryings))
    varyingMap = dict(zip(vertVaryings, indices))
    return varyingMap

                                    
def _param(number, length):

    if length == 1: 
        return 'program.local[{}]'.format(number)
    else:
        bits = ['program.local[{}]'.format(n) for n in range(number,
                                                             number + length)]

        return '{{ {} }}'.format(','.join(bits))


def _texture(number):
    return 'texture[{}]'.format(number)


def _attr(number):
    return 'vertex.texcoord[{}]'.format(number)


def _varying(number, vert):
    if vert: return 'result.texcoord[{}]'  .format(number)
    else:    return 'fragment.texcoord[{}]'.format(number)
