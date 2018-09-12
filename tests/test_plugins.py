#!/usr/bin/env python
#
# test_plugins.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import os.path as op

import pkg_resources

import fsleyes.plugins as plugins


plugindirs = ['fsleyes_plugin_example','fsleyes_plugin_bad_example']
plugindirs = [op.join(op.dirname(__file__), 'testdata', d) for d in plugindirs]
plugindirs = [op.abspath(d)                                for d in plugindirs]


def setup_module():
    for d in plugindirs:
        pkg_resources.working_set.add_entry(d)
    import fsleyes_plugin_example      # noqa
    import fsleyes_plugin_bad_example  # noqa


def test_listPlugins():
    # this will break if more plugins
    # are installed in the test environment
    assert sorted(plugins.listPlugins()) == [
        'fsleyes-plugin-bad-example', 'fsleyes-plugin-example']


def test_listViews():
    from fsleyes_plugin_example.plugin import PluginView

    views = dict(plugins.listViews())

    assert views == {'Plugin view' : PluginView}


def test_listControls():
    from fsleyes_plugin_example.plugin import PluginControl
    from fsleyes.views.timeseriespanel import TimeSeriesPanel
    from fsleyes.views.orthopanel      import OrthoPanel

    ctrls      = dict(plugins.listControls())
    ctrlsortho = dict(plugins.listControls(OrthoPanel))
    ctrlsts    = dict(plugins.listControls(TimeSeriesPanel))

    assert ctrls      == {'Plugin control' : PluginControl}
    assert ctrlsortho == {'Plugin control' : PluginControl}
    assert ctrlsts    == {}


def test_listTools():
    from fsleyes_plugin_example.plugin import PluginTool

    tools = dict(plugins.listTools())

    assert tools == {'Plugin tool' : PluginTool}
