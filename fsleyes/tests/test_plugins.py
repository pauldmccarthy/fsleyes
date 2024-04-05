#!/usr/bin/env python
#
# test_plugins.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import textwrap as tw

import os.path as op

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
        sys.path.append(d)
    import fsleyes_plugin_example      # noqa
    import fsleyes_plugin_bad_example  # noqa


def lookup_plugin_module(prefix):
    for modname, mod in sys.modules.items():
        if modname.startswith(f'fsleyes.plugins.{prefix}'):
            return mod


def test_listViews():
    from fsleyes_plugin_example.plugin import PluginView

    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', True):
        views = dict(plugins.listViews())

    assert views['Plugin view'] is PluginView


def test_listControls():

    from fsleyes_plugin_example.plugin import PluginControl
    from fsleyes.views.timeseriespanel import TimeSeriesPanel
    from fsleyes.views.orthopanel      import OrthoPanel

    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', True):
        ctrls      = dict(plugins.listControls())
        ctrlsortho = dict(plugins.listControls(OrthoPanel))
        ctrlsts    = dict(plugins.listControls(TimeSeriesPanel))

    assert ctrls['Plugin control']      is PluginControl
    assert ctrlsortho['Plugin control'] is PluginControl
    assert 'Plugin control' not in ctrlsts


def test_listTools():
    from fsleyes_plugin_example.plugin import PluginTool

    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', True):
        tools = dict(plugins.listTools())

    assert tools['Plugin tool'] is PluginTool


def test_listLayouts():
    from fsleyes_plugin_example.plugin import PluginLayout

    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', True):
        layouts = dict(plugins.listLayouts())

    assert layouts['Plugin layout'] == PluginLayout


def test_layoutModule():
    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', True):
        assert plugins.layoutModule('Plugin layout') == 'fsleyes_plugin_example'


def test_filterThirdParty():

    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', True):
        tools = dict(plugins.listTools())
        assert 'Plugin tool' in tools
    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', False):
        tools = dict(plugins.listTools())
        assert 'Plugin tool' not in tools
    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', {'fsleyes_plugin'}):
        tools = dict(plugins.listTools())
        assert 'Plugin tool' in tools
    with mock.patch('fsleyes.plugins.SHOW_THIRD_PARTY_PLUGINS', {}):
        tools = dict(plugins.listTools())
        assert 'Plugin tool' not in tools


code = tw.dedent("""
from fsleyes.views.viewpanel       import ViewPanel
from fsleyes.controls.controlpanel import ControlPanel
from fsleyes.actions               import Action

FSLEYES_LAYOUT_{prefix}_layout1 = '{prefix} layout 1'

FSLEYES_LAYOUT_{prefix}_layout2 = ('{prefix} layout 2','{prefix} layout 2')

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
        with open(op.join(td, 'test_plugins_loadplugin.py'), 'wt') as f:
            f.write(code.format(prefix='Load'))

        plugins.loadPlugin(op.join(td, 'test_plugins_loadplugin.py'))

        mod = lookup_plugin_module('test_plugins_loadplugin')

        assert plugins.listTools()[   'LoadTool']      is mod.LoadTool
        assert plugins.listControls()['LoadControl']   is mod.LoadControl
        assert plugins.listViews()[   'LoadView']      is mod.LoadView
        assert plugins.listLayouts()[ 'Load_layout1']  == mod.FSLEYES_LAYOUT_Load_layout1
        assert plugins.listLayouts()[ 'Load layout 2'] == mod.FSLEYES_LAYOUT_Load_layout2[1]


def test_installPlugin():
    with tempdir.tempdir() as td:

        with open('test_plugins_installplugin.py', 'wt') as f:
            f.write(code.format(prefix='Install'))

        s = fslsettings.Settings('test_plugins', cfgdir=td, writeOnExit=False)
        with fslsettings.use(s):

            plugins.installPlugin('test_plugins_installplugin.py')

            mod = lookup_plugin_module('test_plugins_installplugin')

            assert plugins.listTools()[   'InstallTool']      is mod.InstallTool
            assert plugins.listControls()['InstallControl']   is mod.InstallControl
            assert plugins.listViews()[   'InstallView']      is mod.InstallView
            assert plugins.listLayouts()[ 'Install_layout1']  == mod.FSLEYES_LAYOUT_Install_layout1
            assert plugins.listLayouts()[ 'Install layout 2'] == mod.FSLEYES_LAYOUT_Install_layout2[1]
            assert op.exists(op.join(td, 'plugins', 'test_plugins_installplugin.py'))


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

            p1 = lookup_plugin_module('plugin1')
            p2 = lookup_plugin_module('plugin2')

            views = plugins.listViews()
            ctrls = plugins.listControls()
            tools = plugins.listTools()

            assert views['Plugin1View']    is p1.Plugin1View
            assert views['Plugin2View']    is p2.Plugin2View
            assert ctrls['Plugin1Control'] is p1.Plugin1Control
            assert ctrls['Plugin2Control'] is p2.Plugin2Control
            assert tools['Plugin1Tool']    is p1.Plugin1Tool
            assert tools['Plugin2Tool']    is p2.Plugin2Tool
            assert plugins.listLayouts()[ 'Plugin1_layout1']  == p1.FSLEYES_LAYOUT_Plugin1_layout1
            assert plugins.listLayouts()[ 'Plugin1 layout 2'] == p1.FSLEYES_LAYOUT_Plugin1_layout2[1]
            assert plugins.listLayouts()[ 'Plugin2_layout1']  == p2.FSLEYES_LAYOUT_Plugin2_layout1
            assert plugins.listLayouts()[ 'Plugin2 layout 2'] == p2.FSLEYES_LAYOUT_Plugin2_layout2[1]




def test_runPlugin():
    plugins.initialise()
    run_with_fsleyes(_test_runPlugin)


def _test_runPlugin(frame, overlayList, displayCtx):
    with tempdir.tempdir(changeto=False) as td:
        with open(op.join(td, 'test_plugins_runplugin.py'), 'wt') as f:
            f.write(code.format(prefix='Run'))

        plugins.loadPlugin(op.join(td, 'test_plugins_runplugin.py'))

        mod  = lookup_plugin_module('test_plugins_runplugin')
        view = frame.addViewPanel(mod.RunView, title='View')
        realYield()
        ctrl = view.togglePanel(mod.RunControl)
        realYield()
        mod.RunTool(overlayList, displayCtx, frame)()


#fsl/fsleyes/fsleyes!400
def test_builtins_get_loaded():

    from fsleyes.plugins.controls.atlaspanel   import  AtlasPanel
    from fsleyes.plugins.controls.clusterpanel import  ClusterPanel
    from fsleyes.plugins.tools.cropimage       import (CropImageAction,
                                                       CropImagePanel)
    plugins.initialise()

    controls = list(plugins.listControls().values())
    tools    = list(plugins.listTools().values())

    assert AtlasPanel         in controls
    assert ClusterPanel       in controls
    assert CropImagePanel not in controls
    assert CropImageAction    in tools
