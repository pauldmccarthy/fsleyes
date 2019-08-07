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
from .texture            import Texture                # noqa
from .texture2d          import Texture2D              # noqa
from .texture2d          import DepthTexture           # noqa
from .texture3d          import Texture3D              # noqa
from .imagetexture       import ImageTexture           # noqa
from .imagetexture       import ImageTexture2D         # noqa
from .imagetexture       import createImageTexture     # noqa
from .colourmaptexture   import ColourMapTexture       # noqa
from .lookuptabletexture import LookupTableTexture     # noqa
from .selectiontexture   import SelectionTexture2D     # noqa
from .selectiontexture   import SelectionTexture3D     # noqa
from .rendertexture      import RenderTexture          # noqa
from .rendertexture      import GLObjectRenderTexture  # noqa
from .rendertexturestack import RenderTextureStack     # noqa
