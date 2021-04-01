#!/usr/bin/env python
#
# atlasmanagementpanel.py - The AtlasManagementPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`AtlasManagementPanel`, which is a sub-panel
that is used by the :class:`.AtlasPanel`.
"""


import logging

import wx

import fsleyes_widgets.elistbox  as elistbox
import fsl.data.atlases          as atlases
import fsleyes.panel             as fslpanel
import fsleyes.actions.loadatlas as loadatlas


log = logging.getLogger(__name__)


class AtlasManagementPanel(fslpanel.FSLeyesPanel):
    """The ``AtlasManagementPanel`` is a sub-panel used by the
    :class:`.AtlasPanel`. It simply displays a list of all known atlases,
    and allows the user to add/remove atlases to/from the list.
    """


    def __init__(self, parent, overlayList, displayCtx, atlasPanel):
        """Create an ``AtlasManagementPanel``.

        :arg parent:      the :mod:`wx` parent object.

        :arg overlayList: The :class:`.OverlayList` instance.

        :arg displayCtx:  The :class:`.DisplayContext` instance.

        :arg atlasPanel:  The :class:`.AtlasPanel` instance that has created
                          this ``AtlasManagementPanel``.
        """
        fslpanel.FSLeyesPanel.__init__(
            self, parent, overlayList, displayCtx, atlasPanel.frame)

        descs = atlases.listAtlases()
        names = [d.name     for d in descs]
        paths = [d.specPath for d in descs]

        self.__atlasList = elistbox.EditableListBox(
            self,
            labels=names,
            clientData=descs,
            tooltips=paths,
            vgap=5,
            style=(elistbox.ELB_NO_MOVE |
                   elistbox.ELB_TOOLTIP_DOWN))

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__atlasList, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.__sizer)
        self.SetMinSize(self.__sizer.GetMinSize())

        self.__atlasList.Bind(elistbox.EVT_ELB_ADD_EVENT,
                              self.__onListAdd)
        self.__atlasList.Bind(elistbox.EVT_ELB_REMOVE_EVENT,
                              self.__onListRemove)

        atlases.registry.register(self.name, self.__atlasAdded,   'add')
        atlases.registry.register(self.name, self.__atlasRemoved, 'remove')


    def destroy(self):
        """Must be called when this ``AtlasManagementPanel`` is no longer
        needed. Removes some property/notification listeners, and calls
        the base class ``destroy`` method.
        """

        fslpanel.FSLeyesPanel.destroy(self)

        atlases.registry.deregister(self.name, 'add')
        atlases.registry.deregister(self.name, 'remove')


    def __atlasAdded(self, registry, topic, desc):
        """Called when an atlas is removed from the :class:`.AtlasRegistry`.
        Removes the corresponding atlas from the list.
        """

        atlasID  = desc.atlasID
        allIDs   = [d.atlasID for d in registry.listAtlases()]
        index    = allIDs.index(atlasID)

        self.__atlasList.Insert(desc.name,
                                index,
                                clientData=desc,
                                tooltip=desc.specPath)


    def __atlasRemoved(self, registry, topic, desc):
        """Called when an atlas is removed from the :class:`.AtlasRegistry`.
        Removes the corresponding atlas from the list.
        """

        index = self.__atlasList.IndexOf(desc)

        self.__atlasList.Remove(index)


    def __onListAdd(self, ev):
        """Called when the user clicks the *Add* button on the list.
        Calls the :func:`.loadatlas.loadAtlas` function.
        """
        loadatlas.loadAtlas(self.frame)


    def __onListRemove(self, ev):
        """Called when the user clicks the *Remove* button on the list.
        Removes the corresponding atlas from the :class:`.AtlasRegistry`.
        """

        with atlases.registry.skip(self.name, 'remove'):
            atlases.removeAtlas(ev.data.atlasID)
