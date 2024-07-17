"""Support for dScriptModule sensor_board devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import urllib.request
import socket

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    ATTR_MODEL,
    ATTR_VOLTAGE,
    ATTR_TEMPERATURE,
    ATTR_DEVICE_ID,
    ATTR_SW_VERSION,
    CONF_UNIQUE_ID,    
    STATE_UNKNOWN,
)

from .entities import dScriptPlatformEntity
from .const import(
    CATTR_FW_VERSION,
    CATTR_IP_ADDRESS,
    CATTR_PROTOCOL,
    CATTR_SW_TYPE,
    DOMAIN,
)

from .utils import(
    async_dScript_setup_entry,
)


_LOGGER: Final = logging.getLogger(__name__)
PLATFORM = 'sensor'

#async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
#    """Async: Set up the sensor_board platform."""
#    await async_dScript_setup_entry(hass=hass, entry=entry, async_add_entities=async_add_entities, dSEntityTypes=[PLATFORM])


class dScriptBoardSensor(dScriptPlatformEntity):
    """The class for dScriptModule sensor_boards."""
    
    _icon = 'mdi:developer-board'
    _platform = PLATFORM
    _firmware = STATE_UNKNOWN
    _software = STATE_UNKNOWN
    _onlineurl = STATE_UNKNOWN
    _configurl = STATE_UNKNOWN   
    _NoGetUpdateCounter = 999

    def _init_platform_specific(self, **kwargs):
        """Platform specific init actions"""
        _LOGGER.debug("%s - %s.%s: _init_platform_specific", self._entry_id, self._board.name, self.uniqueid)
        self._firmware = str(self._board._SystemFirmwareMajor) + "." + str(self._board._SystemFirmwareMinor)
        self._software = str(self._board._ApplicationFirmwareMajor) + "." + str(self._board._ApplicationFirmwareMinor)
        self._onlineurl= "http://" + self._board.IP + "/index.htm"
        self._configurl= "http://" + self._board.IP + "/_config.htm"

#    def _state_post_process(self, state):
#        """Platform specific state post processing"""
#        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_MODEL: self._board._ModuleID,
            ATTR_VOLTAGE: self._board._Volts,
            ATTR_TEMPERATURE: self._board._Temperature,
            ATTR_DEVICE_ID: self._board.MACAddress,
            ATTR_SW_VERSION: self._software,
            CATTR_FW_VERSION: self._firmware,
            CATTR_IP_ADDRESS: self._board.IP,
            CATTR_SW_TYPE: self._board._CustomFirmeware,
            CATTR_PROTOCOL: self._board._Protocol
        }

    @property
    def should_poll(self) -> bool:
        """Return True if polling is needed."""
        #_LOGGER.debug("%s - %s.%s: should_poll", self._entry_id, self._board.name, self.uniqueid)
        return True #always return true as we want http poll always and GetStatus only every 10 poll requests

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s.%s: async_local_poll", self._entry_id, self._board.name, self.uniqueid)         
            state = await self.hass.async_add_executor_job(urllib.request.urlopen,self._onlineurl)
            state = state.getcode()
            if self._NoGetUpdateCounter >= 10:
                self._NoGetUpdateCounter = 0
                await self._board.async_GetStatus()
                #await self.hass.async_add_executor_job(self._board.GetStatus)
            else: self._NoGetUpdateCounter += 1
        except urllib.error.URLError:       state = 404
        except socket.timeout:              state = 408
        except OSError:                     state = 113
        except urllib.error.HTTPError as e: state = e.code
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_poll failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)
            return None
        try:
            if not state == 200:    self._board.available = False
            else:                   self._board.available = True
            self._state = str(state)
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_poll failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)


    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        #push with direct data should never happen for a board sensor
        _LOGGER.warning("%s - %s.%s: unexpected async_local_push request", self._entry_id, self._board.name, self.uniqueid)
