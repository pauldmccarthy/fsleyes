#!/usr/bin/env python
"""This package contains interaction profiles (:class:`.Profile` sub-classes)
that are used by built-in FSLeyes plugins.

Profiles are not themselves registered as plugins, but are associated with a
particular FSLeyes view or control. Views can specify their default
interaction profile by passing the profile type to the
:meth:`.ViewPanel.initProfiles` when they are created.

Controls can override the :meth:`.ControlPanel.profileCls` method to specify
that, when they are added to a view, that profile is created and activated
while the control is opened.
"""
