"""Support for dScriptModule sensor_board devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.const import (
    ATTR_MODEL,
    ATTR_DEVICE_ID,
    ATTR_SW_VERSION,
    CONF_UNIQUE_ID,    
    STATE_UNKNOWN,
)

from .entities import (
    dScriptPlatformEntity,
    create_entity_id,
)
from .const import(
    CATTR_FW_VERSION,
    CATTR_IP_ADDRESS,
    CATTR_PROTOCOL,
    CATTR_SW_TYPE,
    DOMAIN,
    SIGNAL_BOARD_STATUS,
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
    _onlineurl = STATE_UNKNOWN
    _configurl = STATE_UNKNOWN   
    _NoGetUpdateCounter = 999
    _statusurl = STATE_UNKNOWN
    _StatusPageRetryCounter = 0
    _StatusPageRetryPolls = 20 #polls until status.htm is tried again on a board without it (firmware update)

    def _init_platform_specific(self, **kwargs):
        """Platform specific init actions"""
        _LOGGER.debug("%s - %s %s%s: _init_platform_specific", self._entry_id, self._board.name, self._dSEntityType, self._identifier)
        self._onlineurl= "http://" + self._board.IP + "/index.htm"
        self._statusurl= "http://" + self._board.IP + "/status.htm"
        self._configurl= "http://" + self._board.IP + "/_config.htm"

#    def _state_post_process(self, state):
#        """Platform specific state post processing"""
#        return state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_MODEL: self._board._ModuleID,
            ATTR_DEVICE_ID: self._board.MACAddress,
            ATTR_SW_VERSION: str(self._board._ApplicationFirmwareMajor) + "." + str(self._board._ApplicationFirmwareMinor), # read live - changes after a firmware update
            CATTR_FW_VERSION: str(self._board._SystemFirmwareMajor) + "." + str(self._board._SystemFirmwareMinor),
            CATTR_IP_ADDRESS: self._board.IP,
            CATTR_SW_TYPE: self._board._CustomFirmeware,
            CATTR_PROTOCOL: self._board._Protocol
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        #_LOGGER.debug("%s - %s.%s: available", self._entry_id, self._board.name, self.uniqueid)
        if self._onlineurl is STATE_UNKNOWN:
            return False
        return True

    @property
    def should_poll(self) -> bool:
        """Return True if polling is needed."""
        #_LOGGER.debug("%s - %s.%s: should_poll", self._entry_id, self._board.name, self.uniqueid)
        return True #always return true as we want http poll always and GetStatus only every 10 poll requests

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s.%s: async_local_poll", self._entry_id, self._board.name, self.uniqueid)         
            session = async_get_clientsession(self.hass)
            state = None
            if self._board._StatusPageSupported is not False or self._StatusPageRetryCounter >= self._StatusPageRetryPolls:
                # firmware >= 3.9: small page with temperature, voltage and load - no extra GetStatus connection needed
                self._StatusPageRetryCounter = 0
                async with session.get(self._statusurl, timeout=aiohttp.ClientTimeout(total=10)) as response: # always closes the connection to the board
                    state = response.status
                    text = await response.text(errors='replace')
                if state == 200:
                    self._board._StatusPageSupported = self._board.update_from_status_page(text)
                elif state == 404:
                    _LOGGER.debug("%s - %s: async_local_poll: no status.htm (firmware < 3.9) - using index.htm", self._board.friendlyname, self._name)
                    self._board._StatusPageSupported = False
                    state = None
            else:
                self._StatusPageRetryCounter += 1
            if state is None:
                async with session.get(self._onlineurl, timeout=aiohttp.ClientTimeout(total=10)) as response: # always closes the connection to the board
                    state = response.status
                    await response.read()
            if not self._board._StatusPageSupported:
                if self._NoGetUpdateCounter >= 10:
                    self._NoGetUpdateCounter = 0
                    await self._board.async_GetStatus()
                    #await self.hass.async_add_executor_job(self._board.GetStatus)
                else: self._NoGetUpdateCounter += 1
            async_dispatcher_send(self.hass, SIGNAL_BOARD_STATUS.format(self._board.MACAddress))
        except asyncio.TimeoutError:                state = 408
        except aiohttp.ClientResponseError as e:    state = e.status
        except aiohttp.ClientConnectionError:       state = 113
        except aiohttp.ClientError:                 state = 404
        except OSError:                             state = 113
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_poll failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)
            return None
        try:
            if not state == 200 and self._board.available == True: await self._board.async_check_available()
            elif state == 200 and self._board.available == False: await self._board.async_check_available()
            else:
                _LOGGER.debug("%s - %s: async_local_poll board available unchanged: %s", self._board.friendlyname, self._name, self._board.available)
            self._state = str(state)
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_poll failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)


    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        #push with direct data should never happen for a board sensor
        _LOGGER.warning("%s - %s.%s: unexpected async_local_push request", self._entry_id, self._board.name, self.uniqueid)
