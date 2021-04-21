#!/usr/bin/env python
#
# test_plugins.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import textwrap as tw

import os.path as op

import pkg_resources

try:
    from unittest import mock
except ImportError:
    import mock

import fsl.utils.tempdir  as tempdir
import fsl.utils.settings as fslsettings
import fsleyes.plugins    as plugins

from fsleyes.tests import run_with_fsleyes, realYield


plugindirs = ['fsleyes_plugin_example', 'fsleyes_plugin_bad_example']
plugindirs = [op.join(op.dirname(__file__), 'testdata', d) for d in plugindirs]
plugindirs = [op.abspath(d)                                for d in plugindirs]


def setup_module():
    for d in plugindirs:
        pkg_resources.working_set.add_entry(d)
    import fsleyes_plugin_example      # noqa
    import fsleyes_plugin_bad_example  # noqa


def test_listPlugins():
    for plugin in ['fsleyes-plugin-bad-example', 'fsleyes-plugin-example']:
        assert plugin in plugins.listPlugins()


def test_listViews():
    from fsleyes_plugin_example.plugin import PluginView

    views = dict(plugins.listViews())

    assert views['Plugin view'] is PluginView


def test_listControls():
    from fsleyes_plugin_example.plugin import PluginControl
    from fsleyes.views.timeseriespanel import TimeSeriesPanel
    from fsleyes.views.orthopanel      import OrthoPanel

    ctrls      = dict(plugins.listControls())
    ctrlsortho = dict(plugins.listControls(OrthoPanel))
    ctrlsts    = dict(plugins.listControls(TimeSeriesPanel))

    assert ctrls['Plugin control']      is PluginControl
    assert ctrlsortho['Plugin control'] is PluginControl
    assert 'Plugin control' not in ctrlsts


def test_listTools():
    from fsleyes_plugin_example.plugin import PluginTool

    tools = dict(plugins.listTools())

    assert tools['Plugin tool'] is PluginTool


code = tw.dedent("""
from fsleyes.views.viewpanel       import ViewPanel
from fsleyes.controls.controlpanel import ControlPanel
from fsleyes.actions               import Action

class {prefix}View(ViewPanel):
    pass

class {prefix}Control(ControlPanel):
    pass

class {prefix}Tool(Action):
    def __init__(self, overlayList, displayCtx, frame):
        Action.__init__(self, overlayList, displayCtx, self.func)

    def func(self):
        pass
""").strip()


def test_loadPlugin():
    with tempdir.tempdir(changeto=False) as td:
        with open(op.join(td, 'test_loadplugin.py'), 'wt') as f:
            f.write(code.format(prefix='Load'))

        plugins.loadPlugin(op.join(td, 'test_loadplugin.py'))

        mod = sys.modules['fsleyes_plugin_test_loadplugin']

        assert 'fsleyes-plugin-test-loadplugin' in plugins.listPlugins()
        assert plugins.listTools()[   'LoadTool']    is mod.LoadTool
        assert plugins.listControls()['LoadControl'] is mod.LoadControl
        assert plugins.listViews()[   'LoadView']    is mod.LoadView


def test_installPlugin():
    with tempdir.tempdir() as td:

        with open('test_installplugin.py', 'wt') as f:
            f.write(code.format(prefix='Install'))

        s = fslsettings.Settings('test_plugins', cfgdir=td, writeOnExit=False)
        with fslsettings.use(s):

            plugins.installPlugin('test_installplugin.py')

            mod = sys.modules['fsleyes_plugin_test_installplugin']

            assert 'fsleyes-plugin-test-installplugin' in plugins.listPlugins()
            assert plugins.listTools()[   'InstallTool']    is mod.InstallTool
            assert plugins.listControls()['InstallControl'] is mod.InstallControl
            assert plugins.listViews()[   'InstallView']    is mod.InstallView
            assert op.exists(op.join(td, 'plugins', 'test_installplugin.py'))


def test_initialise():

    with tempdir.tempdir(changeto=False) as td1, \
         tempdir.tempdir(changeto=False) as td2:
        with open(op.join(td1, 'plugin1.py'), 'wt') as f:
            f.write(code.format(prefix='Plugin1'))
        with open(op.join(td2, 'plugin2.py'), 'wt') as f:
            f.write(code.format(prefix='Plugin2'))

        with mock.patch.dict(
                'os.environ',
                {'FSLEYES_PLUGIN_PATH' : op.pathsep.join((td1, td2))}):

            plugins.initialise()

            assert 'fsleyes-plugin-plugin1' in plugins.listPlugins()
            assert 'fsleyes-plugin-plugin2' in plugins.listPlugins()

            p1 = sys.modules['fsleyes_plugin_plugin1']
            p2 = sys.modules['fsleyes_plugin_plugin2']

            views = plugins.listViews()
            ctrls = plugins.listControls()
            tools = plugins.listTools()

            assert views['Plugin1View']    is p1.Plugin1View
            assert views['Plugin2View']    is p2.Plugin2View
            assert ctrls['Plugin1Control'] is p1.Plugin1Control
            assert ctrls['Plugin2Control'] is p2.Plugin2Control
            assert tools['Plugin1Tool']    is p1.Plugin1Tool
            assert tools['Plugin2Tool']    is p2.Plugin2Tool




def test_runPlugin():
    plugins.initialise()
    run_with_fsleyes(_test_runPlugin)


def _test_runPlugin(frame, overlayList, displayCtx):
    with tempdir.tempdir(changeto=False) as td:
        with open(op.join(td, 'test_runplugin.py'), 'wt') as f:
            f.write(code.format(prefix='Run'))

        plugins.loadPlugin(op.join(td, 'test_runplugin.py'))

        mod  = sys.modules['fsleyes_plugin_test_runplugin']
        view = frame.addViewPanel(mod.RunView, title='View')
        realYield()
        ctrl = view.togglePanel(mod.RunControl)
        realYield()
        mod.RunTool(overlayList, displayCtx, frame)()
