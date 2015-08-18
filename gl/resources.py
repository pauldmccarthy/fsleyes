#!/usr/bin/env python
#
# resources.py - Simple manager for shared OpenGL resources.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


class _Resource(object):

    def __init__(self, key, resource):
        self.key      = key
        self.resource = resource
        self.refcount = 0
        

_resources = {}

def exists(key):
    return key in _resources


def get(key, createFunc=None, *args, **kwargs):

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

    r           = _resources[key]
    r.refcount -= 1

    log.debug('Resource {} reference count '
              'decreased to {}'.format(str(key), r.refcount))

    if r.refcount <= 0:

        log.debug('Destroying resource {}'.format(str(key)))

        _resources.pop(key)
        r.resource.destroy()
