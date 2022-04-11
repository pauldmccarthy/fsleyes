#!/usr/bin/env python


import os
import time
import random

import pytest

import numpy as np

from fsleyes.tests import run_with_fsleyes

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

    # Use run_with_fsleyes to initialise an OpenGL context
    if 'LOCAL_TEST_FSLEYES' in os.environ:
        def nothing(*args, **kwargs):
            pass
        run_with_fsleyes(nothing)



def pytest_addoption(parser):
    parser.addoption('--niters',
                     type=int,
                     action='store',
                     default=10,
                     help='Number of test iterations for imagewrapper')

    parser.addoption('--seed',
                     type=int,
                     help='Seed for random number generator')


@pytest.fixture
def seed(request):

    seed = request.config.getoption('--seed')

    if seed is None:
        seed = np.random.randint(2 ** 30)

    np.random.seed(seed)
    random   .seed(seed)
    print('Seed for random number generator: {}'.format(seed))
    return seed


@pytest.fixture
def niters(request):
    """Number of test iterations."""
    return request.config.getoption('--niters')
