"""Support for dScriptModule sensor devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import DEVICE_CLASS_MOTION
from homeassistant.const import (
    ATTR_MODEL,
    ATTR_VOLTAGE,
    ATTR_TEMPERATURE,
    ATTR_DEVICE_ID,
    ATTR_SW_VERSION,
    STATE_UNKNOWN,
)

import urllib.request
import socket
from .const import (
    CATTR_FW_VERSION,
    CATTR_IP_ADDRESS,
    CATTR_PROTOCOL,
    CATTR_SW_TYPE,
    DSDOMAIN_BOARD,
    DSDOMAIN_BUTTON,
    DSDOMAIN_MOTION,
    NATIVE_ASYNC,
)

_LOGGER: Final = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info=None) -> None:
    """Set up the dScriptModule sensor platform."""
    from .utils import async_setupPlatformdScript
    await async_setupPlatformdScript(DSDOMAIN_BOARD, hass, config, async_add_entities, discovery_info)
    await async_setupPlatformdScript(DSDOMAIN_BUTTON, hass, config, async_add_entities, discovery_info)
    await async_setupPlatformdScript(DSDOMAIN_MOTION, hass, config, async_add_entities, discovery_info)

class dScriptBoardSensor(Entity):
    """The class for dScriptModule board webserver availability"""
    _identifier = None
    _name = None
    _domain = None
    _icon = None
    _device_class = None
    _NoGetStatusCounter = 999

    def __init__(self, board, identifier, domain) -> None:
        """Initialize the object."""
        _LOGGER.debug("%s - %s%s: __init__", board.friendlyname, domain, str(identifier))
        self._identifier = identifier
        self._board = board
        self._domain = domain
        self._name = self._board.friendlyname + "_" + domain.capitalize() + str(self._identifier)
        self._state = STATE_UNKNOWN
        self._icon = 'mdi:developer-board'
        self._firmware = str(self._board._SystemFirmwareMajor) + "." + str(self._board._SystemFirmwareMinor)
        self._software = str(self._board._ApplicationFirmwareMajor) + "." + str(self._board._ApplicationFirmwareMinor)
        self._onlineurl= "http://" + self._board.IP + "/index.htm"
        self._configurl= "http://" + self._board.IP + "/_config.htm"
        self._NoGetStatusCounter = 999
        _LOGGER.debug("%s - %s: __init__ complete", self._board.friendlyname, self._name)

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

    #@property
    #def unique_id(self) -> str | None:
    #    """Return a unique identifier for this device."""
    #    _LOGGER.debug("%s - %s: unique_id", self._board.friendlyname, self._name) 
    #    return self._device.uniqueid

    @property
    def available(self) -> bool:
        """Return True if device is available."""
    #    _LOGGER.debug("%s - %s: available", self._board.friendlyname, self._name)
        return True

    @property
    def should_poll(self) -> bool:
        """Return True if polling is needed."""
    #    _LOGGER.debug("%s - %s: should_poll", self._board.friendlyname, self._name)
        return True

    #@property
    #def device_info(self) -> DeviceInfo:
    #    """Return a device description for device registry."""
    #    _LOGGER.debug("%s - %s: device_info", self._board.friendlyname, self._name)
    #    if (self._device.uniqueid is None or
    #            self._device.uniqueid.count(':') != 7):
    #        return None
    #
    #    serial = self._device.uniqueid.split('-', 1)[0]
    #    bridgeid = self.gateway.api.config.bridgeid
    #
    #    return {
    #        'connections': {(CONNECTION_ZIGBEE, serial)},
    #        'identifiers': {(DECONZ_DOMAIN, serial)},
    #        'manufacturer': self._device.manufacturer,
    #        'model': self._device.modelid,
    #        'name': self._device.name,
    #        'sw_version': self._device.swversion,
    #        'via_hub': (DECONZ_DOMAIN, bridgeid),
    #    }

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_MODEL: self._board._ModuleID,
            ATTR_VOLTAGE: self._board._Volts,
            ATTR_TEMPERATURE: self._board._Temperature,
            ATTR_DEVICE_ID: self._board._MACAddress,
            ATTR_SW_VERSION: self._software,
            CATTR_FW_VERSION: self._firmware,
            CATTR_IP_ADDRESS: self._board.IP,
            CATTR_SW_TYPE: self._board._CustomFirmeware,
            CATTR_PROTOCOL: self._board._Protocol,
        }

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: async_local_poll", self._board.friendlyname, self._name)            
            state = await self.hass.async_add_executor_job(urllib.request.urlopen,self._onlineurl)
            state = state.getcode()
            if self._NoGetStatusCounter >= 10:
                self._NoGetStatusCounter = 0
                if NATIVE_ASYNC:
                    await self._board.async_GetStatus()
                else: 
                    await self.hass.async_add_executor_job(self._board.GetStatus)
            else:
                self._NoGetStatusCounter += 1
        except urllib.error.URLError:
            state = 404
        except socket.timeout:
            state = 408
        except OSError:
            state = 113
        except urllib.error.HTTPError as e:
            state = e.code
        except Exception as e:
            _LOGGER.error("%s - %s: async_local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)
        try:
            if not state == 200:
                self._board.available = False
            else:
                self._board.available = True
            self._state = str(state)
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s: local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def local_poll(self) -> None:
        """Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: local_poll", self._board.friendlyname, self._name)
            state = urllib.request.urlopen(self._onlineurl).getcode()
            if self._NoGetStatusCounter >= 10:
                self._NoGetStatusCounter = 0
                self._board.GetStatus()
            else:
                self._NoGetStatusCounter += 1
        except urllib.error.URLError:
            state = 404
        except socket.timeout:
            state = 408
        except OSError:
            state = 113
        except urllib.error.HTTPError as e:
            state = e.code
        except Exception as e:
            _LOGGER.error("%s - %s: local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)
        try:
            if not state == 200:
                self._board.available = False
            else:
                self._board.available = True
            self._state = str(state)
            _LOGGER.debug("%s - %s: local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s: local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        try:
            #push with direct data never happens for a status availability sensor
            await self.hass.async_create_task(self.async_local_poll())
        except Exception as e:
            _LOGGER.error("%s - %s: async_local_push failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def local_push(self, state=None) -> None:
        """Get the latest status from device after an update was pushed"""
        try:
            #push with direct data never happens for a status availability sensor
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

class dScriptButtonSensor(Entity):
    """The class for dScriptModule button clicks."""
    _identifier = None
    _name = None
    _domain = None
    _icon = None
    _device_class = None

    def __init__(self, board, identifier, domain) -> None:
        """Initialize the object."""
        _LOGGER.debug("%s - %s%s: __init__", board.friendlyname, domain, str(identifier))
        self._identifier = identifier
        self._board = board
        self._domain = domain
        self._icon = 'mdi:light-switch'
        self._name = self._board.friendlyname + "_" + domain.capitalize() + str(self._identifier)
        self._state = STATE_UNKNOWN
        _LOGGER.debug("%s - %s: __init__ complete", self._board.friendlyname, self._name)

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

    #@property
    #def unique_id(self) -> str | None:
    #    """Return a unique identifier for this device."""
    #    _LOGGER.debug("%s - %s: unique_id", self._board.friendlyname, self._name) 
    #    return self._device.uniqueid

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

    #@property
    #def device_info(self) -> DeviceInfo:
    #    """Return a device description for device registry."""
    #    _LOGGER.debug("%s - %s: device_info", self._board.friendlyname, self._name)
    #    if (self._device.uniqueid is None or
    #            self._device.uniqueid.count(':') != 7):
    #        return None
    #
    #    serial = self._device.uniqueid.split('-', 1)[0]
    #    bridgeid = self.gateway.api.config.bridgeid
    #
    #    return {
    #        'connections': {(CONNECTION_ZIGBEE, serial)},
    #        'identifiers': {(DECONZ_DOMAIN, serial)},
    #        'manufacturer': self._device.manufacturer,
    #        'model': self._device.modelid,
    #        'name': self._device.name,
    #        'sw_version': self._device.swversion,
    #        'via_hub': (DECONZ_DOMAIN, bridgeid),
    #    }

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

class dScriptMotionSensor(Entity):
    """The class for dScriptModule motion detection."""
    _identifier = None
    _name = None
    _domain = None
    _icon = None
    _device_class = None

    def __init__(self, board, identifier, domain) -> None:
        """Initialize the object."""
        _LOGGER.debug("%s - %s%s: __init__", board.friendlyname, domain, str(identifier))
        self._identifier = identifier
        self._board = board
        self._domain = domain
        self._device_class = DEVICE_CLASS_MOTION
        self._icon = 'mdi:motion-sensor'
        self._name = self._board.friendlyname + "_" + domain.capitalize() + str(self._identifier)
        self._state = STATE_UNKNOWN
        _LOGGER.debug("%s - %s: __init__ complete", self._board.friendlyname, self._name)

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

    #@property
    #def unique_id(self) -> str | None:
    #    """Return a unique identifier for this device."""
    #    _LOGGER.debug("%s - %s: unique_id", self._board.friendlyname, self._name)
    #    return self._device.uniqueid

    @property
    def available(self) -> bool:
        """Return True if device is available."""
    #    _LOGGER.debug("%s - %s: available", self._board.friendlyname, self._name)
        if self._board._ConnectedMotionSensors < self._identifier:
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

    #@property
    #def device_info(self) -> DeviceInfo:
    #    """Return a device description for device registry."""
    #    _LOGGER.debug("%s - %s: device_info", self._board.friendlyname, self._name)
    #    if (self._device.uniqueid is None or
    #            self._device.uniqueid.count(':') != 7):
    #        return None
    #
    #    serial = self._device.uniqueid.split('-', 1)[0]
    #    bridgeid = self.gateway.api.config.bridgeid
    #
    #    return {
    #        'connections': {(CONNECTION_ZIGBEE, serial)},
    #        'identifiers': {(DECONZ_DOMAIN, serial)},
    #        'manufacturer': self._device.manufacturer,
    #        'model': self._device.modelid,
    #        'name': self._device.name,
    #        'sw_version': self._device.swversion,
    #        'via_hub': (DECONZ_DOMAIN, bridgeid),
    #    }

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

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: async_local_poll", self._board.friendlyname, self._name)
            if NATIVE_ASYNC:
                state = await self._board.async_GetMotion(self._identifier)
            else:
                state = await self.hass.async_add_executor_job(self._board.GetMotion, self._identifier)
            self._state = state
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s: async_local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def local_poll(self) -> None:
        """Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: local_poll", self._board.friendlyname, self._name)
            state=self._board.GetMotion(self._identifier)
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
