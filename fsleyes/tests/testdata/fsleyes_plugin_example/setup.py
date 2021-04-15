#!/usr/bin/env python

from setuptools import setup

setup(
    name='fsleyes-plugin-example',

    packages=['fsleyes_plugin_example'],

    entry_points={

        'fsleyes_views' : [
            'Plugin view = fsleyes_plugin_example.plugin:PluginView',
        ],

        'fsleyes_controls' : [
            'Plugin control = fsleyes_plugin_example.plugin:PluginControl',
        ],

        'fsleyes_tools' : [
            'Plugin tool = fsleyes_plugin_example.plugin:PluginTool',
        ]
    }
)
