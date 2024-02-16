"""Support for dScriptModule cover devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.cover import (
    ATTR_POSITION, 
    ATTR_CURRENT_POSITION,
    CoverEntity,
    CoverDeviceClass,
    CoverEntityFeature,  
)
from homeassistant.const import (
    STATE_UNKNOWN,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    SERVICE_OPEN,
    SERVICE_CLOSE,
    CONF_STOP,
)

from .entities import dScriptPlatformEntity
from .const import(
    STATE_STOPPED,
    DOMAIN,
)

from .utils import(
    async_dScript_setup_entry,
)


_LOGGER: Final = logging.getLogger(__name__)
PLATFORM = 'cover'

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Async: Set up the cover platform."""
    await async_dScript_setup_entry(hass=hass, entry=entry, async_add_entities=async_add_entities, dSEntityTypes=[PLATFORM])


class dScriptCover(CoverEntity, dScriptPlatformEntity):
    """The class for dScriptModule covers."""
    
    _platform = PLATFORM
    _attr_current_cover_position = None
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP | CoverEntityFeature.SET_POSITION
    _device_class = CoverDeviceClass.SHUTTER

#    def _init_platform_specific(self, **kwargs):
#        """Platform specific init actions"""
#        _LOGGER.debug("%s - %s.%s: _init_platform_specific", self._entry_id, self._board.name, self.uniqueid)  

    def _state_post_process(self, state):
        """Platform specific state post processing"""
        #_LOGGER.debug("%s - %s: _state_post_process: %s", self._board.friendlyname, self._name, state)
        if isinstance(state, list):
            fallback_state = state[1]
            state = state[0]
        else: fallback_state = state
        if isinstance(state, int): self._attr_current_cover_position = state
        if state == 100: return STATE_OPEN
        elif state == 0: return STATE_CLOSED        
        else: return fallback_state
    
    @property
    def is_opening(self) -> bool:
        """Return true if the cover is currently opening."""
        #_LOGGER.debug("%s - %s: is_opening", self._board.friendlyname, self._name)
        if self._state == STATE_OPENING: return True
        return False

    @property
    def is_open(self) -> bool:
        """Return true if the cover is open."""
        #_LOGGER.debug("%s - %s: is_open", self._board.friendlyname, self._name)        
        if self._attr_current_cover_position == 100: return True
        return False

    @property
    def is_closing(self) -> bool:
        """Return true if the cover is currently closing."""
        #_LOGGER.debug("%s - %s: is_closing", self._board.friendlyname, self._name)
        if self._state == STATE_CLOSING: return True
        return False

    @property
    def is_closed(self) -> bool:
        """Return true if the cover is open."""
        #_LOGGER.debug("%s - %s: is_open", self._board.friendlyname, self._name)        
        if self._attr_current_cover_position == 0: return True
        return False

    async def async_stop_cover(self, **kwargs) -> None:
        """Async: Stop the cover."""
        try:
            #_LOGGER.debug("%s - %s.%s: async_stop_cover", self._entry_id, self._board.name, self.uniqueid)
            await self._board.async_SetShutter(self._identifier, CONF_STOP)
            #self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, CONF_STOP)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_stop_cover failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)

    async def async_open_cover(self, **kwargs) -> None:
        """Async: Open the cover."""
        try:
            #_LOGGER.debug("%s - %s.%s: async_open_cover", self._entry_id, self._board.name, self.uniqueid)
            await self._board.async_SetShutter(self._identifier, SERVICE_OPEN)
            #self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, SERVICE_OPEN)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_open_cover failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)

    async def async_close_cover(self, **kwargs) -> None:
        """Async: Close the cover."""
        try:
            #_LOGGER.debug("%s - %s.%s: sync_close_cover", self._entry_id, self._board.name, self.uniqueid)
            await self._board.async_SetShutter(self._identifier, SERVICE_CLOSE)
            #self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, SERVICE_CLOSE)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: sync_close_cover failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)

    async def async_set_cover_position(self, **kwargs) -> None:
        """Async: Move the cover to a specific position."""        
        try:
            #_LOGGER.debug("%s - %s.%s: async_set_cover_position", self._entry_id, self._board.name, self.uniqueid)
            position = kwargs[ATTR_POSITION]
            _LOGGER.debug("%s - %s.%s: async_set_cover_position to: %s", self._entry_id, self._board.name, self.uniqueid, position)
            await self._board.async_SetShutter(self._identifier, position)
            #self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, position)
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_set_cover_position failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            #_LOGGER.debug("%s - %s.%s: async_local_poll", self._entry_id, self._board.name, self.uniqueid)
            state = await self._board.async_GetShutter(self._identifier)
            #state = await self.hass.async_add_executor_job(self._board.GetShutter, self._identifier)
            #_LOGGER.debug("%s - %s.%s: async_local_poll state received: %s", self._entry_id, self._board.name, self.uniqueid, state)
            state = self._state_post_process(state)
            self._state = state
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except TypeError as e:
            _LOGGER.debug("%s - %s.%s: async_local_poll known exception: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)
            self._state = STATE_UNKNOWN
            self.async_write_ha_state()
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
            else:
                await self.hass.async_create_task(self.async_local_poll())
        except Exception as e:
            _LOGGER.error("%s - %s.%s: async_local_push failed: %s (%s.%s)", self._entry_id, self._board.name, self.uniqueid, str(e), e.__class__.__module__, type(e).__name__)
