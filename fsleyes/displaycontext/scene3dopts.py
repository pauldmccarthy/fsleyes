#!/usr/bin/env python
#
# scene3dopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
from . import sceneopts


log = logging.getLogger(__name__)


class Scene3DOpts(sceneopts.SceneOpts):
    def _onPerformanceChange(self, *a):
        pass
