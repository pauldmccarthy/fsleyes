#!/usr/bin/env python
#
# resources.py - Simple manager for shared OpenGL resources.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module implements a simple API for managing shared OpenGL resources.
Some OpenGL resources (e.g. textures) take up a lot of memory so it makes
sense to share these resources where possible, instead of creating and
maintaining multiple copies. The API defined in this module consists of the
following functions:


.. autosummary::
   :nosignatures:

   exists
   get
   set
   delete


On creation, resources must be given a unique name, referred to as a
``key``. Subsequent accesses to the resource are performed by specifying this
key. As an example, let's say that we have a :class:`.Image` called
``myImage``::


    import fsleyes.gl.resources as glresources
    import fsleyes.gl.textures  as gltextures
    import fsl.data.image       as fslimage

    image = fslimage.Image('data.nii.gz')

We wish to create an :class:`.ImageTexture` which can be shared by multiple
users. All users of this texture can use the :func:`get` function to access
the texture. The first call to :func:`get` will result in the texture being
created, whereas subsequent calls will return a reference to the existing
texture, and will increase its reference count::

    texture = glresources.get(
        'myTexture',
         gltextures.ImageTexture,
         'myTexture',
         image,
         interp=gl.GL_LINEAR)


.. note:: Here, we have used ``'myTexture'`` as the resource key. In practice,
          you will need to use something that is guaranteed to be unique
          throughout your application.


When a user of the texture no longer needs the texture, it must call the
:func:`delete` method. Calls to :func:`delete` will decrement the reference
count; when this count reaches zero, the texture will be destroyed::


    glresources.delete('myTexture')


.. note:: This module was written for managing OpenGL :class:`.Texture`
          objects, but can actually be used with any type - the only
          requirement is that the type defines a method called ``destroy``,
          which performs any required clean-up operations.
"""

import logging


log = logging.getLogger(__name__)


def exists(key):
    """Returns ``True`` if a resource with the specified key exists, ``False``
    otherwise.
    """
    return key in _resources


def get(key, createFunc=None, *args, **kwargs):
    """Return a reference to the resource wiuh the specified key.

    If no resource with the given key exists, and ``createFunc`` is not
    ``None``, the resource is created, registered, and returned. If
    the resource does not exist, and ``createFunc`` is ``None``, a
    :exc:`KeyError` is raised.

    :arg key:        Unique resource identifier.
    :arg createFunc: If the resource does not exist, and this argument
                     is provided, it will be called to create the resource.

    All other positional and keyword arguments will be passed through to
    the ``createFunc``.
    """

    r = _resources.get(key, None)

    if r is None and createFunc is None:
        raise KeyError('Resource {} does not exist'.format(str(key)))

    if r is not None:
        r.refcount += 1

        log.debug('Resource {} reference count '
                  'increased to {}'.format(str(key), r.refcount))

        return r.resource

    if createFunc is not None:
        return set(key, createFunc(*args, **kwargs))


def set(key, resource, overwrite=False):
    """Create a new resource, or update an existing one.

    :arg key:       Unique resource identifier.

    :arg resource:  The resource itself.

    :arg overwrite: If ``False`` (the default), and a resource with
                    the specified ``key`` already exists, a :exc:`KeyError`
                    is raised. Otherwise, it is assumed that a resource with
                    the specified ``key`` exists - the existing resource is
                    replaced with the specified ``resource``.
    """

    if (not overwrite) and (key in _resources):
        raise KeyError('Resource {} already exists'.format(str(key)))

    if not overwrite:
        log.debug('Adding resource {}'.format(str(key)))

        r               = _Resource(key, resource)
        r.refcount     += 1
        _resources[key] = r

        log.debug('Resource {} reference count '
                  'increased to {}'.format(str(key), r.refcount))

    else:
        log.debug('Updating resource {}'.format(str(key)))

        _resources[key].resource = resource

    return resource


def delete(key):
    """Decrements the reference count of the resource with the specified key.
    When the resource reference count reaches ``0``, the ``destroy`` method
    is called on the resource.

    :arg key: Unique resource identifier.
    """

    r           = _resources[key]
    r.refcount -= 1

    log.debug('Resource {} reference count '
              'decreased to {}'.format(str(key), r.refcount))

    if r.refcount <= 0:

        log.debug('Destroying resource {}'.format(str(key)))

        _resources.pop(key)
        r.resource.destroy()


class _Resource(object):
    """Internal type which is used to encapsulate a resource, and the
    number of active references to that resources. The following attributes
    are available on a ``_Resource``:

    ============ ============================================================
    ``key``      The unique resource key.
    ``resource`` The resource itself.
    ``refcount`` Number of references to the resource (initialised to ``0``).
    ============ ============================================================
    """

    def __init__(self, key, resource):
        """Create a ``_Resource``.

        :arg key:      The unique resource key.
        :arg resource: The resource itself.
        """
        self.key      = key
        self.resource = resource
        self.refcount = 0


_resources = {}
"""A dictionary containing ``{key : _Resource}`` mappings for all resources
that exist.
"""
