"""Support for dScriptModule switch devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import format_mac
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
    STATE_UNKNOWN,
)

from .utils import async_setupPlatformdScript
from .const import(
    DATA_PLATFORMS,        
    DOMAIN,
    DSDOMAIN_SWITCH,
    MANUFACTURER,
    NATIVE_ASYNC,
) 
_LOGGER: Final = logging.getLogger(__name__)
platform = 'switch'

async def async_setup_platform(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info: Optional[DiscoveryInfoType] = None) -> None:
    """Set up the dScriptModule switch platform."""
    _LOGGER.debug("%s - async_setup_platform: platform %s", DOMAIN, DSDOMAIN_SWITCH)
    await async_setupPlatformdScript(DSDOMAIN_SWITCH, hass, config, async_add_entities, discovery_info)

async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    """Setup sensors from a config entry created in the integrations UI."""
    _LOGGER.debug("%s - async_setup_entry: platform %s", DOMAIN, DSDOMAIN_SWITCH)
    try:
        config = hass.data[DOMAIN][config_entry.entry_id]
        if config_entry.options:
            config.update(config_entry.options)
        await async_setupPlatformdScript(DSDOMAIN_SWITCH, hass, config, async_add_entities)    
        hass.data[DOMAIN][config_entry.entry_id][DATA_PLATFORMS]['in_setup'].remove(platform)
        _LOGGER.debug("%s - async_setup_entry: platform %s complete", DOMAIN, platform)        
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: platform %s failed: %s (%s.%s)", DOMAIN, DSDOMAIN_SWITCH, str(e), e.__class__.__module__, type(e).__name__)  
    
class dScriptSwitch(SwitchEntity):
    """The class for dScriptModule switches."""
    _identifier = None
    _name = None
    _domain = None
    _icon = None
    _device_class = None
    _formatted_mac = None
    uniqueid = None

    def __init__(self, board, identifier, domain) -> None:
        """Initialize the object."""
        _LOGGER.debug("%s - %s%s: __init__", board.friendlyname, domain, str(identifier))
        self._identifier = identifier
        self._board = board
        self._domain = domain
        self._name = self._board.friendlyname + "_" + domain.capitalize() + str(self._identifier)
        self._state = STATE_UNKNOWN
        self._icon = 'mdi:power-socket-de'
        self._formatted_mac = format_mac(str(self._board._MACAddress))
        self.uniqueid = self._formatted_mac + "-" + str(self._identifier)
        _LOGGER.debug("%s - %s: __init__ complete (uid: %s)", self._board.friendlyname, self._name, self.uniqueid)

    @property
    def name(self) -> str | None:
        """Return the name of the device."""
        #_LOGGER.debug("%s - %s: name", self._board.friendlyname, self._name)
        return self._name

    @property
    def icon(self) -> str | None:
        """Return the icon of the device"""
        return self._icon

    @property
    def device_class(self) -> str | None:
        """Return the device_class of the device."""
        return self._device_class

    @property
    def state(self) -> str | None:
        """Return the current device state."""
        return self._state

    @property
    def unique_id(self) -> str | None:
        """Return a unique identifier for this device."""
        _LOGGER.debug("%s - %s: unique_id: %s", self._board.friendlyname, self._name, self.uniqueid)
        return self.uniqueid

    @property
    def available(self) -> bool:
        """Return True if device is available."""
    #    _LOGGER.debug("%s - %s: available", self._board.friendlyname, self._name)
        if self._board._ConnectedSockets < self._identifier:
            return False
        elif not self._board.available:
            return False
        else:
            return True

    @property
    def should_poll(self) -> bool:
        """Return True if polling is needed."""    
    #    _LOGGER.debug("%s - %s: should_poll", self._board.friendlyname, self._name)
        if self._state == STATE_UNKNOWN:
            return True
        elif self._board._CustomFirmeware == True:
            return False
        else:
            return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        _LOGGER.debug("%s - %s: device_info", self._board.friendlyname, self._name)
        info = DeviceInfo(
            identifiers={(DOMAIN, self._formatted_mac)},
            default_manufacturer=MANUFACTURER,
            default_model=self._board._ModuleID,
            default_name=self._board.friendlyname,
            sw_version=str(self._board._ApplicationFirmwareMajor) + "." + str(self._board._ApplicationFirmwareMinor),
            configuration_url="http://" + self._board.IP + "/index.htm",
            suggested_area=self._board.friendlyname.split('_')[-1]            
        )
        _LOGGER.debug("%s - %s: device_info result: %s", self._board.friendlyname, self._name, info)
        return info

    @property
    def is_on(self) -> bool:
        """Return true if entity is on."""
        #_LOGGER.debug("%s - %s: is_on", self._board.friendlyname, self._name)
        if self._state == STATE_ON:
            return True
        elif self._state == STATE_OFF:
            return False
        else:
            #return STATE_UNKNOWN
            return False

    async def async_turn_on(self, **kwargs) -> None:
        """Async: Turn the light on"""
        try:
            _LOGGER.debug("%s - %s: async_turn_on", self._board.friendlyname, self._name)
            if NATIVE_ASYNC:
                await self._board.async_SetSocket(self._identifier, STATE_ON)
            else:
                self.hass.async_add_executor_job(self._board.SetSocket, self._identifier, STATE_ON)
        except Exception as e:
            _LOGGER.error("%s - %s: async_turn_on failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def turn_on(self, **kwargs) -> None:
        """Turn the light on."""
        try:
            _LOGGER.debug("%s - %s: turn_on", self._board.friendlyname, self._name)
            self._board.SetSocket(self._identifier,STATE_ON)
        except Exception as e:
            _LOGGER.error("%s - %s: turn_on failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_turn_off(self, **kwargs) -> None:
        """Async: Turn the light off"""
        try:
            _LOGGER.debug("%s - %s: async_turn_off", self._board.friendlyname, self._name)
            if NATIVE_ASYNC:
                await self._board.async_SetSocket(self._identifier, STATE_OFF)
            else:
                self.hass.async_add_executor_job(self._board.SetSocket, self._identifier, STATE_OFF)
        except Exception as e:
            _LOGGER.error("%s - %s: async_turn_off failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)        

    def turn_off(self, **kwargs) -> None:
        """Turn the light off."""
        try:
            _LOGGER.debug("%s - %s: turn_off", self._board.friendlyname, self._name)
            self._board.SetSocket(self._identifier,STATE_OFF)
        except Exception as e:
            _LOGGER.error("%s - %s: turn_off failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: async_local_poll", self._board.friendlyname, self._name)            
            if NATIVE_ASYNC:
                state = await self._board.async_GetSocket(self._identifier)
            else:
                state = await self.hass.async_add_executor_job(self._board.GetSocket, self._identifier)
            self._state = state
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except OSError as e:
            _LOGGER.debug("%s - %s: async_local_poll failed: known exception: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)
            self._state = STATE_UNKNOWN
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("%s - %s: async_local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def local_poll(self) -> None:
        """Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: local_poll", self._board.friendlyname, self._name)
            state=self._board.GetSocket(self._identifier)
            self._state = state
            _LOGGER.debug("%s - %s: local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s: local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s - %s: async_local_push", self._board.friendlyname, self._name)
            if not state is None:
                if state == STATE_ON: state = STATE_OFF
                elif state == STATE_OFF: state = STATE_ON
                self._state = state
                self.async_write_ha_state()    
                _LOGGER.debug("%s - %s: async_local_push complete: %s", self._board.friendlyname, self._name, state)
            else:
                await self.hass.async_create_task(self.async_local_poll())
        except Exception as e:
            _LOGGER.error("%s - %s: async_local_push failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def local_push(self, state=None) -> None:
        """Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s - %s: local_push", self._board.friendlyname, self._name)
            if not state is None:
                if state == STATE_ON: state = STATE_OFF
                elif state == STATE_OFF: state = STATE_ON
                self._state = state
                _LOGGER.debug("%s - %s: local_push complete: %s", self._board.friendlyname, self._name, state)
            else:
                self.local_poll()
        except Exception as e:
            _LOGGER.error("%s - %s: local_push failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_update(self) -> None:
        """Async: Get latest data and states from the device."""
        try:
            _LOGGER.debug("%s - %s: async_update", self._board.friendlyname, self._name)
            if self.should_poll:
                _LOGGER.debug("%s - %s: async_update is done via poll - initiate", self._board.friendlyname, self._name)
                await self.hass.async_create_task(self.async_local_poll())
            else:
                _LOGGER.debug("%s - %s: async_update is done via push - do nothing / wait for push event", self._board.friendlyname, self._name)
        except Exception as e:
            _LOGGER.error("%s - %s: async_update failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def update(self) -> None:
        """Get latest data and states from the device."""
        try:
            _LOGGER.debug("%s - %s: update", self._board.friendlyname, self._name)
            if self.should_poll:
                _LOGGER.debug("%s - %s: update is done via poll - initiate", self._board.friendlyname, self._name)
                self.local_poll()
            else:
                _LOGGER.debug("%s - %s: update is done via push - do nothing / wait for push event", self._board.friendlyname, self._name)
        except Exception as e:
            _LOGGER.error("%s - %s: update failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)
