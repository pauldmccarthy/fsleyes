#!/usr/bin/env python

import os.path as op
import multiprocessing as mp
import asyncio
import time
import textwrap as tw

import fsleyes.actions.notebook as notebook

import fsl.utils.idle as idle

from fsleyes.tests import run_with_orthopanel

import logging


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def _submit_code(code, connfile):

    mgr          = notebook.FSLeyesNotebookKernelManager()
    mgr.connfile = connfile

    kernid = asyncio.run(mgr.start_kernel())
    kernel = mgr.get_kernel(kernid)
    client = kernel.client()

    for line in code:
        client.execute(line)
        time.sleep(0.5)


def test_notebook():
    run_with_orthopanel(_test_notebook)
def _test_notebook(panel, overlayList, displayCtx):

    imgfile = op.join(datadir, '3d')
    code    = tw.dedent(f"""
    print(overlayList)
    img = Image('{imgfile}')
    overlayList.append(img)

    display      = frame.viewPanels[0].displayCtx.getDisplay(img)
    opts         = display.opts
    display.name = 'added_from_client'
    opts.cmap    = "hot"
    """).strip().split('\n')

    action = notebook.NotebookAction(overlayList, displayCtx, panel.frame)

    # start the server/kernel
    action(openBrowser=False)

    # submit code via the notebook server
    proc = mp.Process(target=_submit_code, args=(code, action.kernel.connfile))
    proc.start()
    while proc.is_alive():
        idle.block(1)
    proc.join()

    idle.block(2)

    # shut down the server/kernel
    action.shutdown()

    # check that the code was executed
    assert len(overlayList) == 1
    img     = overlayList[0]
    display = panel.displayCtx.getDisplay(img)
    opts    = display.opts
    assert display.name   == 'added_from_client'
    assert opts.cmap.name == 'hot'
