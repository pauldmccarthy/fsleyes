#!/usr/bin/env python
#
# group.py - Overlay groups
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
import copy

import props

import fsl.utils.typedict as td


log = logging.getLogger(__name__)


class OverlayGroup(props.HasProperties):

    
    overlays = props.List()
    """Do not add/remove overlays directly to this list - use the
    :meth:`addOverlay` and :meth:`removeOverlay` methods.
    """

    
    _groupBindings = td.TypeDict({
        'Display'        : ['enabled'],
        'ImageOpts'      : ['volume',
                            'transform'],
        'VolumeOpts'     : ['interpolation'],
        'LabelOpts'      : ['outline',
                            'outlineWidth'],
        'ModelOpts'      : ['outline',
                            'outlineWidth',
                            'refImage',
                            'coordSpace',
                            'transform'],
        'VectorOpts'     : ['suppressX',
                            'suppressY',
                            'suppressZ',
                            'modulate',
                            'modThreshold'],
        'LineVectorOpts' : ['lineWidth',
                            'directed'],
        'RGBVectorOpts'  : ['interpolation'],
    })
    """This dictionary defines the properties which are bound across Display
    instances, and instances of the DisplayOpts sub-classes, for overlays in
    the same group.
    """

    
    def __init__(self, displayCtx, overlayList):

        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__hasBeenSet  = {}
        self.__name        = '{}_{}'.format(type(self).__name__, id(self))

        # Copy all of the properties listed
        # in the _groupBindings dict
        from . import       \
            Display,        \
            ImageOpts,      \
            VolumeOpts,     \
            MaskOpts,       \
            VectorOpts,     \
            RGBVectorOpts,  \
            LineVectorOpts, \
            ModelOpts,      \
            LabelOpts

        for clsName, propNames in OverlayGroup._groupBindings.items():
            cls = locals()[clsName]

            for propName in propNames:
                prop = copy.copy(getattr(cls, propName))
                self.addProperty('{}_{}'.format(clsName, propName), prop)
                
                self.__hasBeenSet[clsName, propName] = False


    def __copy__(self):
        return OverlayGroup(self, self.__displayCtx, self.__overlayList)

            
    def addOverlay(self, overlay):

        self.overlays.append(overlay)

        display = self.__displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        log.debug('Adding overlay {} to group {}'.format(
            overlay.name, self.__name))

        self.__bindDisplayOpts(display)
        self.__bindDisplayOpts(opts)

        display.addListener('overlayType',
                            self.__name,
                            self.__overlayTypeChanged)

            
    def removeOverlay(self, overlay):

        self.overlays.remove(overlay)

        display = self.__displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        log.debug('Removing overlay {} from group {}'.format(
            overlay.name, self.__name)) 

        self.__bindDisplayOpts(display, unbind=True)
        self.__bindDisplayOpts(opts,    unbind=True)

        display.removeListener('overlayType', self.__name)

        if len(self.overlays) == 0:
            for key in self.__hasBeenSet.keys():
                self.__hasBeenSet[key] = False


    def __bindDisplayOpts(self, target, unbind=False):
        
        # This is the first overlay to be added - the
        # group should inherit its property values
        if len(self.overlays) == 1:
            master, slave = target, self
                        
        # Other overlays are already in the group - the
        # new overlay should inherit the group properties
        else:
            master, slave = self, target

        bindProps = OverlayGroup._groupBindings.get(target,
                                                    allhits=True,
                                                    bykey=True)

        for clsName, propNames in bindProps.items():
            for propName in propNames:

                groupName = '{}_{}'.format(clsName, propName)

                # If the group property has not yet
                # taken on a value, initialise it
                # to the property value being bound.
                # 
                # We do this to avoid clobbering
                # property values with un-initialised
                # group property values.
                #
                if not self.__hasBeenSet[clsName, propName]:
                    setattr(self, groupName, getattr(target, propName))

                if slave is self:
                    otherName = propName
                    propName  = groupName
                else:
                    otherName = groupName

                slave.bindProps(propName,
                                master,
                                otherName,
                                bindatt=False,
                                unbind=unbind) 


    def __overlayTypeChanged(self, value, valid, display, name):
        opts = display.getDisplayOpts()
        self.__bindDisplayOpts(opts)
