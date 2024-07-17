"""Base entities for the dscriptmodule integration."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import (
    DeviceInfo,
    Entity,
    generate_entity_id,
)
from homeassistant.const import (
    CONF_FRIENDLY_NAME,
    CONF_NAME,
    STATE_UNKNOWN,
)

from .const import (
    DOMAIN,
    DSCRIPT_ENTITYTYPETOCOUNTATTR,
    MANUFACTURER,
)

_LOGGER: Final = logging.getLogger(__name__)

def create_entity_unique_id(dSBoard: dScriptBoardHA, identifier: int, dSEntityType: str): 
    """Create a unique id for entites."""
    return DOMAIN.lower()+"_"+str(dSBoard.MACAddress).replace(':','')+'_'+dSEntityType+str(identifier)

def create_entity_id(dSBoard: dScriptBoardHA, identifier: int, dSEntityType: str): 
    """Create a entity id for entites."""
    entity_id=''
    if hasattr(dSBoard, CONF_FRIENDLY_NAME):
        entity_id=str(getattr(dSBoard, CONF_FRIENDLY_NAME))+'_'+dSEntityType+str(identifier)
    elif hasattr(dSBoard, CONF_NAME):
        entity_id=str(getattr(dSBoard, CONF_NAME))+'_'+dSEntityType+str(identifier)
    else:
        entity_id=create_entity_unique_id(dSBoard, identifier, dSEntityType)
    entity_id=entity_id.replace(':','')
    entity_id=entity_id.replace('-','_')
    entity_id=entity_id.replace(' ','_')
    entity_id=entity_id.lower()
    return entity_id

class dScriptPlatformEntity(Entity):
    """Base class for Govee Life integration."""
    
    _state = STATE_UNKNOWN
    _device_class = None
    _attributes = {}
    _icon = None
    _name = None

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, dSBoard: dScriptBoardHA, identifier: int, dSEntityType: str, **kwargs) -> None:
        """Initialize the object."""
        try:
            self._entry = entry
            self._entry_id = self._entry.entry_id
            self.hass = hass

            _LOGGER.debug("%s - %s: __init__: %s.%s", entry.entry_id, dSBoard.name, dSEntityType, str(identifier))
            self._identifier = identifier
            self._board = dSBoard
            self._dSEntityType = dSEntityType
            self._entity_id = create_entity_id(self._board, self._identifier, self._dSEntityType)

            #_LOGGER.debug("%s - %s.%s: __init__ kwargs = %s", entry.entry_id, self._board.name, self.uniqueid, kwargs)
            self._init_platform_specific(**kwargs)
            self.entity_id = generate_entity_id(self._platform+'.{}', self._entity_id, hass=hass)
            #self.uniqueid = DOMAIN.lower()+"_"+str(self._board.MACAddress).replace(':','')+'_'+self._dSEntityType+str(self._identifier)
            self.uniqueid = create_entity_unique_id(self._board, self._identifier, self._dSEntityType)
            _LOGGER.debug("%s - %s.%s: __init__ complete - entity_id: %s", entry.entry_id, self._board.name, self.uniqueid, self.entity_id)
        except Exception as e:            
            _LOGGER.error("%s - %s.%s: __init__ failed: %s (%s.%s)", entry.entry_id, self._board.name, str(identifier), str(e), e.__class__.__module__, type(e).__name__)
            return None


    def _init_platform_specific(self, **kwargs): 
        """Platform specific init actions"""
        #do nothing here as this is only a drop-in option for other platforms
        #do not put actions in a try / except block - execeptions should be covered by __init__
        pass        


    def _state_post_process(self, state):
        """Platform specific state post processing"""
        #do nothing here as this is only a drop-in option for other platforms
        #do not put actions in a try / except block - execeptions should be covered by calling function
        return state


    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        if self._name is None:
            return self._entity_id
        return self._name


    @property
    def description(self) -> str | None:
        """Return the description of the entity."""
        return self._description


    @property
    def icon(self) -> str | None:
        """Return the icon of the entity"""
        return self._icon


    @property
    def device_class(self) -> str | None:
        """Return the device_class of the entity."""
        return self._device_class


    @property
    def state(self) -> str | None:
        """Return the current state of the entity."""
        return self._state


    @property
    def extra_state_attributes(self):
        """Return the state attributes of the entity."""
        return self._attributes


    @property
    def unique_id(self) -> str | None:
        """Return the unique identifier for this entity."""
        return self.uniqueid


    @property
    def available(self) -> bool:
        """Return True if device is available."""
        #_LOGGER.debug("%s - %s.%s: available", self._entry_id, self._board.name, self.uniqueid)
        if not self._board.available:
            return False
        if self._dSEntityType == 'switch' and not self._board._CustomFirmeware: pattr = DSCRIPT_ENTITYTYPETOCOUNTATTR['switch_native']
        else: pattr=DSCRIPT_ENTITYTYPETOCOUNTATTR[self._dSEntityType]
        if getattr(self._board, pattr, 0) < self._identifier:
            return False
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        #_LOGGER.debug("%s - %s.%s: device_info", self._entry_id, self._board.name, self.uniqueid)
        info = DeviceInfo(
            identifiers={(DOMAIN, self._board.MACAddress)},
            manufacturer=MANUFACTURER,
            model=self._board._ModuleID,
            name=self._board.friendlyname,
            sw_version=str(self._board._ApplicationFirmwareMajor) + "." + str(self._board._ApplicationFirmwareMinor),
            configuration_url="http://" + self._board.IP + "/index.htm",
            suggested_area=str(self._board.name).split('_')[-1]
        )
        #_LOGGER.debug("%s - %s.%s: device_info: %s", self._entry_id, self._board.name, self.uniqueid, info) 
        return info

    @property
    def should_poll(self) -> bool:
        """Return True if polling is needed."""    
        #_LOGGER.debug("%s - %s.%s: should_poll", self._entry_id, self._board.name, self.uniqueid)
        if self._state == STATE_UNKNOWN:
            return True
        elif self._board._CustomFirmeware == True:
            return False
        else:
            return True

    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        try:
            #_LOGGER.debug("%s - %s.%s: async_local_push: %s", self._entry_id, self._board.name, self.uniqueid, state) 
            if not state is None:
                state = self._state_post_process(state)
                self._state = state
                self.async_write_ha_state()
                _LOGGER.debug("%s - %s.%s: async_local_push complete: %s", self._entry_id, self._board.name, self.uniqueid, state) 
            else:
                await self.hass.async_create_task(self.async_local_poll())
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_push failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)

    async def async_update(self) -> None:
        """Async: Get latest data and states from the device."""
        try:
            #_LOGGER.debug("%s - %s.%s: async_update", self._entry_id, self._board.name, self.uniqueid)
            if self.should_poll:
                #_LOGGER.debug("%s - %s.%s: async_update is done via poll - initiate", self._entry_id, self._board.name, self.uniqueid)
                await self.hass.async_create_task(self.async_local_poll())
            else:
                #_LOGGER.debug("%s - %s.%s: async_update is done via push - do nothing / wait for push event", self._entry_id, self._board.name, self.uniqueid)
                pass
        except Exception as e:
             _LOGGER.error("%s - %s.%s: async_update failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)
