#!/usr/bin/env python
#
# perspectives.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


log = logging.getLogger(__name__)


def getAllPerspectives():
    return ['melview', 'feat']


def loadPerspective(frame, name):
    log.debug('Loading perspective {}'.format(name))


def savePerspective(frame, name):
    log.debug('Saving current perspective with name {}'.format(name))


    
def serialisePerspective(frame):
    log.debug('Serialising current perspective')


class Perspective(object):

    # Views
    # 
    # View layout
    # 
    # For each view:
    #   - Controls
    #   - Control layout
    pass
