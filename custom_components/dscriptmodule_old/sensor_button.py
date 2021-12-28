"""Support for dScriptModule sensor devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import format_mac
from homeassistant.const import (
    STATE_UNKNOWN,
)

from .const import (
    DOMAIN,
    MANUFACTURER,    
    NATIVE_ASYNC,
)

_LOGGER: Final = logging.getLogger(__name__)

class dScriptButtonSensor(Entity):
    """The class for dScriptModule button clicks."""
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
        self._icon = 'mdi:light-switch'
        self._name = self._board.friendlyname + "_" + domain.capitalize() + str(self._identifier)
        self._state = STATE_UNKNOWN
        self._formatted_mac = format_mac(str(self._board._MACAddress))
        self.uniqueid = self._formatted_mac + "-" + str(self._identifier) + "-button"        
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
        if self._board._ConnectedButtons < self._identifier:
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

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: async_local_poll", self._board.friendlyname, self._name)            
            if NATIVE_ASYNC:
                state = await self._board.async_GetButton(self._identifier)
            else:
                state = await self.hass.async_add_executor_job(self._board.GetButton, self._identifier)
            self._state = state
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s: async_local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def local_poll(self) -> None:
        """Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: local_poll", self._board.friendlyname, self._name)
            #execute twice to ensure button is reset if we have received information via PUSH (not pull)
            state=self._board.GetButton(self._identifier)
            self._state = state
            _LOGGER.debug("%s - %s: local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s: local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s - %s: async_local_push", self._board.friendlyname, self._name)
            if not state is None:
                self._state = state
                self.async_write_ha_state()    
                _LOGGER.debug("%s - %s: async_local_push complete: %s", self._board.friendlyname, self._name, state)
                # still need to execute a poll as firmware does not reset the value without it :(
                if NATIVE_ASYNC:
                    state = await self._board.async_GetButton(self._identifier)
                else:
                    state = await self.hass.async_add_executor_job(self._board.GetButton, self._identifier)
                _LOGGER.debug("%s - %s: async_local_push post executed poll reset: %s", self._board.friendlyname, self._name, state)
            else:
                await self.hass.async_create_task(self.async_local_poll())        
        except Exception as e:
            _LOGGER.error("%s - %s: async_local_push failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def local_push(self, state=None) -> None:
        """Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s - %s: local_push", self._board.friendlyname, self._name)
            if not state is None:
                self._state = state
                _LOGGER.debug("%s - %s: local_push complete: %s", self._board.friendlyname, self._name, state)
                # still need to execute a poll as firmware does not reset the value without it :(
                state=self._board.GetButton(self._identifier)
                _LOGGER.debug("%s - %s: local_push post executed poll reset: %s", self._board.friendlyname, self._name, state)
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
