#!/usr/bin/env python
#
# textures.py - Management of OpenGL image textures.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package is a container for a collection of classes which use OpenGL
textures for various purposes.


.. todo:: There is a lot of duplicate code in the various texture sub-classes.
          This will hopefully be rectified at some stage in the future -
          shared code will be moved into the :class:`.Texture` class.
"""


# All *Texture classes are made available at the
# textures package level due to these imports
from .texture            import Texture
from .texture            import Texture2D
from .texture3d          import Texture3D
from .imagetexture       import ImageTexture
from .colourmaptexture   import ColourMapTexture
from .lookuptabletexture import LookupTableTexture
from .selectiontexture   import SelectionTexture
from .rendertexture      import RenderTexture
from .rendertexture      import GLObjectRenderTexture
from .rendertexturestack import RenderTextureStack
