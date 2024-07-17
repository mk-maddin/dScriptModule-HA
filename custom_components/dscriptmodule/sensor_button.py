"""Support for dScriptModule sensor_button devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import (
    STATE_UNKNOWN,
)

from .entities import dScriptPlatformEntity
from .const import(
    DOMAIN,
)

from .utils import(
    async_dScript_setup_entry,
)


_LOGGER: Final = logging.getLogger(__name__)
PLATFORM = 'sensor_button'

#async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
#    """Async: Set up the sensor_board platform."""
#    await async_dScript_setup_entry(hass=hass, entry=entry, async_add_entities=async_add_entities, dSEntityTypes=[PLATFORM])


class dScriptButtonSensor(dScriptPlatformEntity):
    """The class for dScriptModule sensor_buttons."""
    
    _icon = 'mdi:gesture-tap-button'    
    _platform = PLATFORM

#    def _init_platform_specific(self, **kwargs):
#        """Platform specific init actions"""
#        _LOGGER.debug("%s - %s.%s: _init_platform_specific", self._entry_id, self._board.name, self.uniqueid)  

#    def _state_post_process(self, state):
#        """Platform specific state post processing"""
#        return state

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            #_LOGGER.debug("%s - %s.%s: async_local_poll", self._entry_id, self._board.name, self.uniqueid)            
            state = await self._board.async_GetButton(self._identifier)
            #state = await self.hass.async_add_executor_job(self._board.GetButton, self._identifier)
            #_LOGGER.debug("%s - %s.%s: async_local_poll state received: %s", self._entry_id, self._board.name, self.uniqueid, state)
            self._state = state
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s.%s: async_local_poll complete: %s", self._entry_id, self._board.name, self.uniqueid, state) 
        except OSError as e:
            _LOGGER.debug("%s - %s.%s: async_local_poll known exception: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)
            self._state = STATE_UNKNOWN
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_poll failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__) 

    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        try:
            #_LOGGER.debug("%s - %s.%s: async_local_push: %s", self._entry_id, self._board.name, self.uniqueid, state) 
            if not state is None:
                state = self._state_post_process(state)
                self._state = state
                self.async_write_ha_state()
                _LOGGER.debug("%s - %s.%s: async_local_push complete: %s", self._entry_id, self._board.name, self.uniqueid, state)
                # still need to execute a poll as firmware does not reset the internal value without it :(
                state = await self._board.async_GetButton(self._identifier)
                #state = await self.hass.async_add_executor_job(self._board.GetButton, self._identifier)
            else:
                await self.hass.async_create_task(self.async_local_poll())
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_push failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)

