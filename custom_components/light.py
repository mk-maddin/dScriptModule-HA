"""Support for dScriptModule light devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.light import LightEntity
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
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
PLATFORM = 'light'

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Async: Set up the light platform."""
    await async_dScript_setup_entry(hass=hass, entry=entry, async_add_entities=async_add_entities, dSEntityTypes=[PLATFORM])


class dScriptLight(LightEntity, dScriptPlatformEntity):
    """The class for dScriptModule lightes."""

    _platform = PLATFORM

#    def _init_platform_specific(self, **kwargs):
#        """Platform specific init actions"""
#        _LOGGER.debug("%s - %s.%s: _init_platform_specific", self._entry_id, self._board.name, self.uniqueid)  

#    def _state_post_process(self, state):
#        """Platform specific state post processing"""
#        return state

    @property
    def is_on(self) -> bool | None:
        """Return true if entity is on."""
        #_LOGGER.debug("%s - %s.%s: is_on", self._entry_id, self._board.name, self.uniqueid)
        if self._state == STATE_ON: return True
        elif self._state == STATE_OFF: return False
        else: return None

    async def async_turn_on(self, **kwargs) -> None:
        """Async: Turn the light on"""
        try:
            #_LOGGER.debug("%s - %s.%s: async_turn_on", self._entry_id, self._board.name, self.uniqueid)
            await self._board.async_SetLight(self._identifier,STATE_ON)
            #self.hass.async_add_executor_job(self._board.SetLight, self._identifier, STATE_ON)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_turn_on failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)

    async def async_turn_off(self, **kwargs) -> None:
        """Async: Turn the light off"""
        try:
            #_LOGGER.debug("%s - %s.%s: async_turn_off", self._entry_id, self._board.name, self.uniqueid)
            await self._board.async_SetLight(self._identifier,STATE_OFF)
            #self.hass.async_add_executor_job(self._board.SetLight, self._identifier, STATE_OFF)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_turn_off failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)       

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            #_LOGGER.debug("%s - %s.%s: async_local_poll", self._entry_id, self._board.name, self.uniqueid)            
            state = await self._board.async_GetLight(self._identifier)
            #state = await self.hass.async_add_executor_job(self._board.GetLight, self._identifier)
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



