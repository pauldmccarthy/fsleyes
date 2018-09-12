#!/usr/bin/env python

from setuptools import setup

setup(
    name='fsleyes-plugin-bad-example',

    packages=['fsleyes_plugin_bad_example'],

    entry_points={

        'fsleyes_views' : [
            'Bad plugin view = fsleyes_plugin_bad_example.plugin:PluginView',
        ],

        'fsleyes_controls' : [
            'Bad plugin control = fsleyes_plugin_bad_example.plugin:PluginControl',
        ],

        'fsleyes_tools' : [
            'Bad plugin tool = fsleyes_plugin_bad_example.plugin:PluginTool',
        ]
    }
)
