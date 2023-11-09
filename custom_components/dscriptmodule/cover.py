"""Support for dScriptModule cover devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

#-> not a greate solution as this changes ALL entities of that type to sync at the same time
#from datetime import timedelta
#_SSCAN_INTERVAL = timedelta(seconds=60)

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import format_mac
from homeassistant.components.cover import (
    ATTR_POSITION, 
    ATTR_CURRENT_POSITION,
    CoverEntity,
    DEVICE_CLASS_SHUTTER,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
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

from .utils import async_setupPlatformdScript
from .const import( 
    DATA_PLATFORMS,        
    DOMAIN,
    DSDOMAIN_COVER,
    MANUFACTURER,
    NATIVE_ASYNC,
    STATE_STOPPED,
) 
_LOGGER: Final = logging.getLogger(__name__)
platform = 'cover'

async def async_setup_platform(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info: Optional[DiscoveryInfoType] = None) -> None:
    """Set up the dScriptModule cover platform."""
    _LOGGER.debug("%s - async_setup_platform: platform %s", DOMAIN, DSDOMAIN_COVER)
    await async_setupPlatformdScript(DSDOMAIN_COVER, hass, config, async_add_entities, discovery_info)

async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    """Setup sensors from a config entry created in the integrations UI."""
    _LOGGER.debug("%s - async_setup_entry: platform %s", DOMAIN, DSDOMAIN_COVER)
    try:
        config = hass.data[DOMAIN][config_entry.entry_id]
        if config_entry.options:
            config.update(config_entry.options)
        await async_setupPlatformdScript(DSDOMAIN_COVER, hass, config, async_add_entities)
        hass.data[DOMAIN][config_entry.entry_id][DATA_PLATFORMS]['in_setup'].remove(platform)        
        _LOGGER.debug("%s - async_setup_entry: platform %s complete", DOMAIN, platform)        
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: platform %s failed: %s (%s.%s)", DOMAIN, DSDOMAIN_COVER, str(e), e.__class__.__module__, type(e).__name__)      
    
class dScriptCover(CoverEntity):
    """The light class for dScriptModule lights."""
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
        self._supported_features = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION
        self._current_cover_position = None
        self._state = STATE_UNKNOWN
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
        if self._board._ConnectedShutters < self._identifier:
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
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    @property
    def current_cover_position(self) -> int | str:
        """Return current position of cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._current_cover_position
    
    @property
    def is_opening(self) -> bool:
        """Return true if the cover is currently opening."""
        #_LOGGER.debug("%s - %s: is_opening", self._board.friendlyname, self._name)
        if self._state == STATE_OPENING:
            return True
        return False

    @property
    def is_open(self) -> bool:
        """Return true if the cover is open."""
        #_LOGGER.debug("%s - %s: is_open", self._board.friendlyname, self._name)        
        if self._current_cover_position == 100:
            return True
        return False

    @property
    def is_closing(self) -> bool:
        """Return true if the cover is currently closing."""
        #_LOGGER.debug("%s - %s: is_closing", self._board.friendlyname, self._name)
        if self._state == STATE_CLOSING:
            return True
        return False
    
    async def async_stop_cover(self, **kwargs) -> None:
        """Stop the cover."""
        try:
            _LOGGER.debug("%s - %s: stop_cover", self._board.friendlyname, self._name)
            if NATIVE_ASYNC:
                await self._board.async_SetShutter(self._identifier, CONF_STOP)
            else:
                self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, CONF_STOP)
        except Exception as e:
            _LOGGER.error("%s - %s: stop_cover failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def stop_cover(self, **kwargs) -> None:
        """Stop the cover."""
        try:
            _LOGGER.debug("%s - %s: stop_cover", self._board.friendlyname, self._name)
            self._board.SetShutter(self._identifier, CONF_STOP)
        except Exception as e:
            _LOGGER.error("%s - %s: stop_cover failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_open_cover(self, **kwargs) -> None:
        """Open the cover."""
        try:
            _LOGGER.debug("%s - %s: open_cover", self._board.friendlyname, self._name)
            if NATIVE_ASYNC: 
                await self._board.async_SetShutter(self._identifier, SERVICE_OPEN)
            else:
                self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, SERVICE_OPEN)
        except Exception as e:
            _LOGGER.error("%s - %s: open_cover failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def open_cover(self, **kwargs) -> None:
        """Open the cover."""
        try:
            _LOGGER.debug("%s - %s: open_cover", self._board.friendlyname, self._name)
            self._board.SetShutter(self._identifier, SERVICE_OPEN)
        except Exception as e:
            _LOGGER.error("%s - %s: open_cover failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_close_cover(self, **kwargs) -> None:
        """Close the cover."""
        try:
            _LOGGER.debug("%s - %s: close_cover", self._board.friendlyname, self._name)
            if NATIVE_ASYNC:
                await self._board.async_SetShutter(self._identifier, SERVICE_CLOSE)
            else:
                self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, SERVICE_CLOSE)
        except Exception as e:
            _LOGGER.error("%s - %s: close_cover failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def close_cover(self, **kwargs) -> None:
        """Close the cover."""
        try:
            _LOGGER.debug("%s - %s: close_cover", self._board.friendlyname, self._name)
            self._board.SetShutter(self._identifier, SERVICE_CLOSE)
        except Exception as e:
            _LOGGER.error("%s - %s: close_cover failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_set_cover_position(self, **kwargs) -> None:
        """Move the cover to a specific position."""        
        try:
            _LOGGER.debug("%s - %s: async_set_cover_position", self._board.friendlyname, self._name)
            position = kwargs[ATTR_POSITION]
            _LOGGER.debug("%s - %s: async_set_cover_position to %s", self._board.friendlyname, self._name, position)
            if NATIVE_ASYNC:
                await self._board.async_SetShutter(self._identifier, position)
            else:
                self.hass.async_add_executor_job(self._board.SetShutter, self._identifier, position)
        except Exception as e:
            _LOGGER.error("%s - %s: async_set_cover_position failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    def close_cover(self, **kwargs) -> None:
        """Move the cover to a specific position."""
        try:
            _LOGGER.debug("%s - %s: async_set_cover_position", self._board.friendlyname, self._name)
            position = kwargs[ATTR_POSITION]
            self._board.SetShutter(self._identifier, position)
        except Exception as e:
            _LOGGER.error("%s - %s: async_set_cover_position failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_local_poll(self) -> None:
        """Async: Poll the latest status from device"""
        try:
            _LOGGER.debug("%s - %s: async_local_poll", self._board.friendlyname, self._name)
            if NATIVE_ASYNC:
                state = await self._board.async_GetShutter(self._identifier)
            else:
                state = await self.hass.async_add_executor_job(self._board.GetShutter, self._identifier)
            _LOGGER.debug("%s - %s: async_local_poll: state received: %s", self._board.friendlyname, self._name, state)
            self._current_cover_position = state[0]
            if self._current_cover_position == 100:
                self._state = STATE_OPEN
            elif self._current_cover_position == 0:
                self._state = STATE_CLOSED
            else:
                self._state = state[1]
            self.async_write_ha_state()
            _LOGGER.debug("%s - %s: async_local_poll complete: %s", self._board.friendlyname, self._name, state)
        except TypeError as e:
            _LOGGER.debug("%s - %s: async_local_poll failed: known exception: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)
            self._state = STATE_UNKNOWN
            self.async_write_ha_state()
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
            state=self._board.GetShutter(self._identifier)
            self._current_cover_position = state[0]
            if self._current_cover_position == 100:
                self._state = STATE_OPEN
            elif self._current_cover_position == 0:
                self._state = STATE_CLOSED
            else:
                self._state = state[1]            
            _LOGGER.debug("%s - %s: local_poll complete: %s", self._board.friendlyname, self._name, state)
        except Exception as e:
            _LOGGER.error("%s - %s: local_poll failed: %s (%s.%s)", self._board.friendlyname, self._name, str(e), e.__class__.__module__, type(e).__name__)

    async def async_local_push(self, state=None) -> None:
        """Async: Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s - %s: async_local_push", self._board.friendlyname, self._name)
            if not state is None:
                self._current_cover_position = state
                if self._current_cover_position == 100:
                    self._state = STATE_OPEN
                elif self._current_cover_position == 0:
                    self._state = STATE_CLOSED
                else:
                    self._state = STATE_STOPPED
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
                self._current_cover_position = state
                if self._current_cover_position == 100:
                    self._state = STATE_OPEN
                elif self._current_cover_position == 0:
                    self._state = STATE_CLOSED
                else:
                    self._state = STATE_STOPPED
                _LOGGER.error("%s - %s: local_push complete: %s", self._board.friendlyname, self._name, state)
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
