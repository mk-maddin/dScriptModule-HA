"""Support for dScriptModule sensor devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .sensor_board import dScriptBoardSensor
from .sensor_button import dScriptButtonSensor
from .sensor_motion import dScriptMotionSensor
from .utils import async_setupPlatformdScript
from .const import (
    DATA_PLATFORMS,        
    DOMAIN,
    DSDOMAIN_BOARD,
    DSDOMAIN_BUTTON,
    DSDOMAIN_MOTION,
)

_LOGGER: Final = logging.getLogger(__name__)
platform = 'sensor'

async def async_setup_platform(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info: Optional[DiscoveryInfoType] = None) -> None:
    """Set up the dScriptModule sensor platform."""
    _LOGGER.debug("%s - async_setup_platform: platform %s", DOMAIN, DSDOMAIN_BOARD)
    await async_setupPlatformdScript(DSDOMAIN_BOARD, hass, config, async_add_entities, discovery_info)
    _LOGGER.debug("%s - async_setup_platform: platform %s", DOMAIN, DSDOMAIN_BUTTON)
    await async_setupPlatformdScript(DSDOMAIN_BUTTON, hass, config, async_add_entities, discovery_info)
    _LOGGER.debug("%s - async_setup_platform: platform %s", DOMAIN, DSDOMAIN_MOTION)
    await async_setupPlatformdScript(DSDOMAIN_MOTION, hass, config, async_add_entities, discovery_info)

async def async_setup_entry(hass: HomeAssistant, config_entry: config_entries.ConfigEntry, async_add_entities):
    """Setup sensors from a config entry created in the integrations UI."""
    _LOGGER.debug("%s - async_setup_entry: platform sensor", DOMAIN)
    try:
        config = hass.data[DOMAIN][config_entry.entry_id]
        if config_entry.options:
            config.update(config_entry.options)
        _LOGGER.debug("%s - async_setup_entry: platform sensor %s", DOMAIN, DSDOMAIN_BOARD)
        await async_setupPlatformdScript(DSDOMAIN_BOARD, hass, config, async_add_entities)     
        _LOGGER.debug("%s - async_setup_entry: platform sensor %s", DOMAIN, DSDOMAIN_BUTTON)
        await async_setupPlatformdScript(DSDOMAIN_BUTTON, hass, config, async_add_entities) 
        _LOGGER.debug("%s - async_setup_entry: platform sensor %s", DOMAIN, DSDOMAIN_MOTION)        
        await async_setupPlatformdScript(DSDOMAIN_MOTION, hass, config, async_add_entities) 
        hass.data[DOMAIN][config_entry.entry_id][DATA_PLATFORMS]['in_setup'].remove(platform)        
        _LOGGER.debug("%s - async_setup_entry: platform %s complete", DOMAIN, platform)        
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: platform sensor failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)     
