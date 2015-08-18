#!/usr/bin/env python
#
# textures.py - Management of OpenGL image textures.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package is a container for a collection of classes which use OpenGL
textures for various purposes. 


The :mod:`.texture` sub-module contains the definition of the :class:`Texture`
class, the base class for all texture types.
"""


# All *Texture classes are made available at the
# textures package level due to these imports
from texture            import Texture
from texture            import Texture2D
from imagetexture       import ImageTexture
from colourmaptexture   import ColourMapTexture
from lookuptabletexture import LookupTableTexture
from selectiontexture   import SelectionTexture
from rendertexture      import RenderTexture
from rendertexture      import GLObjectRenderTexture
from rendertexturestack import RenderTextureStack
