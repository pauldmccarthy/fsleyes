#!/usr/bin/env python


import os
import time

import numpy as np

# When doing multiple test runs in parallel
# on the same machine, we sometimes get
# docker/xvfb-related conflicts.

def pytest_configure():
    if 'DISPLAY' in os.environ:
        for i in range(5):
            try:
                import matplotlib as mpl
                mpl.use('wxagg')
                import matplotlib.pyplot as plt
                break
            except ImportError:
                if i == 4:
                    raise
                time.sleep(np.random.randint(1, 10))
