#!/usr/bin/env python


import os
import time
import random
import shlex

import pytest

import numpy as np

import fsleyes.render as render
from fsl.data.image import Image
from fsl.utils.tempdir import tempdir

def pytest_configure():


    # When doing multiple test runs in parallel
    # on the same machine, we sometimes get
    # docker/xvfb-related conflicts.
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

    # Use render to initialise an OpenGL context.  Some tests
    # are skipped depending on the available GL version
    # (e.g. "@pytest.mark.skipif('not haveGL(3.3)')").  This
    # env var can be set to ensure that GL is initialised, so
    # that the haveGL expression is correctly evaluated.
    if 'LOCAL_TEST_FSLEYES' in os.environ:
        with tempdir():
            Image(np.random.random((10, 10, 10))).save('image.nii.gz')
            render.main(shlex.split('-of out.png image'))


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
