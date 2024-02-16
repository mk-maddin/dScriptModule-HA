"""Support for dScriptModule sensor devices."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DSCRIPT_TOPICTOENTITYTYPE
from .utils import async_dScript_setup_entry


_LOGGER: Final = logging.getLogger(__name__)
PLATFORM = 'sensor'

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Async: Set up the sensor platform."""
    for sub_platform in DSCRIPT_TOPICTOENTITYTYPE.values():
        if not sub_platform.split("_")[0] == PLATFORM:
            continue
        await async_dScript_setup_entry(hass=hass, entry=entry, async_add_entities=async_add_entities, dSEntityTypes=[sub_platform])
 
