#!/usr/bin/env python


import string
import random

import fsleyes.utils as utils


def test_validMapKey():
    for i in range(100):
        instr = random.choice(string.ascii_letters) + \
            ''.join([random.choice(string.printable) for i in range(50)])
        key   = utils.makeValidMapKey(instr)
        assert utils.isValidMapKey(key)
