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
from .texture            import  Texture
from .texture2d          import (Texture2D,
                                 DepthTexture)
from .texture3d          import  Texture3D
from .imagetexture       import (ImageTexture,
                                 ImageTexture2D,
                                 createImageTexture)
from .colourmaptexture   import  ColourMapTexture
from .lookuptabletexture import  LookupTableTexture
from .selectiontexture   import (SelectionTexture2D,
                                 SelectionTexture3D)
from .rendertexture      import (RenderTexture,
                                 GLObjectRenderTexture)
from .rendertexturestack import  RenderTextureStack
from .manager            import (ColourMapTextureManager,
                                 AuxImageTextureManager)
