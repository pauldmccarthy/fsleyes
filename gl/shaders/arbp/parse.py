#!/usr/bin/env python
#
# parse.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import jinja2

#
# {{ params.paramName }} -> program.local[X]
#
# Or, if 'paramName' has length > 1
#
# {{ params.paramName }} -> { program.local[x], program.local[x + 1], ... }

# {{ attrs.attName }}     -> vertex.texcoord[N]
#
# {{ textures.texName }} -> texture[N]


# Maybe this too? In vertex program:
# {{ varying.outputName }} -> result.texcoord[N]
#
# In fragment program:
# {{ varying.outputName }} -> fragment.texcoord[N]


def parseARBP(source,
              vert,
              paramMap=None,
              textureMap=None,
              attrMap=None,
              varyingMap=None):

    if paramMap   is None: paramMap   = {}
    if textureMap is None: textureMap = {}
    if attrMap    is None: attrMap    = {}
    if varyingMap is None: varyingMap = {}

    params   = {}
    textures = {}
    attrs    = {}
    varyings = {}

    for name, num in paramMap  .items(): params[  name] = _param(  num)
    for name, num in textureMap.items(): textures[name] = _texture(num)
    for name, num in attrMap   .items(): attrs[   name] = _attr(   num)
    for name, num in varyingMap.items(): varyings[name] = _varying(num, vert)

    template  = jinja2.Template(source)
    parsedSrc = template.render(param=params,
                                texture=textures,
                                attr=attrs,
                                varying=varyings)

    return parsedSrc
                                    

def _param(number):

    try:    number, length = number
    except: number, length = number, 1
    
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
