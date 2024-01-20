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
    DSDOMAIN_BOARD,
    DSDOMAIN_BUTTON,
    DSDOMAIN_MOTION,
)

_LOGGER: Final = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info=None) -> None:
    """Set up the dScriptModule sensor platform."""
    await async_setupPlatformdScript(DSDOMAIN_BOARD, hass, config, async_add_entities, discovery_info)
    await async_setupPlatformdScript(DSDOMAIN_BUTTON, hass, config, async_add_entities, discovery_info)
    await async_setupPlatformdScript(DSDOMAIN_MOTION, hass, config, async_add_entities, discovery_info)


