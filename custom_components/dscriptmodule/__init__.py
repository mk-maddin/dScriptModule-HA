"""Init for the dscriptmodule integration."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import aiofiles
import json
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_DEVICES,
    CONF_PARAMS,
    CONF_SCAN_INTERVAL,
)

from .const import (
    CONF_ADD_ENTITIES,
    CONF_PYOJBECT,
    CONF_SERVER,
    DSCRIPT_TOPICTOENTITYTYPE,
    DOMAIN,
    FUNC_OPTION_UPDATES,
    KNOWN_DATA,
    KNOWN_DATA_FILE,
)

from .server import dScriptBuiltInServer
from .board import async_dScript_SetupKnownBoards
from .services import (
    async_registerService,
    async_service_UpdateButton,
    async_service_HeartbeatKnownBoards,
)

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up resource from the config entry."""
    _LOGGER.debug("Setting up config entry: %s", entry.entry_id)

    try:
        _LOGGER.debug("%s - async_setup_entry: Creating data store: %s.%s ", entry.entry_id, DOMAIN, entry.entry_id)
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN].setdefault(entry.entry_id, {})
        entry_data=hass.data[DOMAIN][entry.entry_id]
        entry_data[CONF_PARAMS]=entry.data
        entry_data.setdefault(CONF_DEVICES, {})
        entry_data.setdefault(KNOWN_DATA, {})
        entry_data.setdefault(CONF_SERVER, {})        
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: Creating data store failed: %s (%s.%s)", entry.entry_id, str(e), e.__class__.__module__, type(e).__name__)
        return False

    try:
        _LOGGER.debug("%s - async_setup_entry: Register option updates listener: %s ", entry.entry_id, FUNC_OPTION_UPDATES)
        entry_data[FUNC_OPTION_UPDATES] = entry.add_update_listener(options_update_listener) 
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: Register option updates listener failed: %s (%s.%s)", entry.entry_id, str(e), e.__class__.__module__, type(e).__name__)
        return False

    try:
        _LOGGER.debug("%s - async_setup_entry: Searching known data file: %s", entry.entry_id, KNOWN_DATA_FILE)
        if os.path.isfile(KNOWN_DATA_FILE):
            async with aiofiles.open(KNOWN_DATA_FILE, mode='r') as j:
                known_data = json.loads(await j.read())
            _LOGGER.debug("%s - async_setup_entry: Got known file data: %s", entry.entry_id, known_data)
            entry_data[KNOWN_DATA] = known_data.get(DOMAIN, {})
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: Searching known data failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False

    try:
        _LOGGER.debug("%s - async_setup_entry: init dScriptServer", DOMAIN)
        entry_data[CONF_SERVER][CONF_PYOJBECT] = dScriptBuiltInServer(hass, entry)
        BuiltInServer = entry_data[CONF_SERVER][CONF_PYOJBECT]
        if BuiltInServer.dScriptServer.State is False:
            _LOGGER.debug("%s - async_setup_entry: start dScriptServer", DOMAIN)
            await BuiltInServer.async_dSServerStart("integration_setup")
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: init server failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        entry_data[CONF_SERVER][CONF_PYOJBECT]=None
        return False

    try:
        platforms = []
        for p in DSCRIPT_TOPICTOENTITYTYPE.values():
            p=p.split("_")[0]
            platforms.append(p)

        for platform in list(set(platforms)):
            _LOGGER.debug("%s - async_setup_entry: Trigger setup for platform: %s ", entry.entry_id, platform)
            hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, platform))
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: Setup trigger for platform %s failed: %s (%s.%s)", entry.entry_id, platform, str(e), e.__class__.__module__, type(e).__name__)
        return False

    try:
        _LOGGER.debug("%s - async_setup_entry: register services", entry.entry_id)        
        await async_registerService(hass, "updatebutton", async_service_UpdateButton)
        await async_registerService(hass, "heartbeatknownboards", async_service_HeartbeatKnownBoards)
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: register services failed: %s (%s.%s)", entry.entry_id, str(e), e.__class__.__module__, type(e).__name__)
        return False 

    hass.async_create_task(async_dScript_SetupKnownBoards(hass, entry, 3))
    _LOGGER.debug("%s - async_setup_entry: Completed", entry.entry_id)
    return True


async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle options update."""
    _LOGGER.debug("Update options / relaod config entry: %s", entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        _LOGGER.debug("Unloading config entry: %s", entry.entry_id)
        all_ok = True
        for platform in DSCRIPT_TOPICTOENTITYTYPE.values():
            _LOGGER.debug("%s - async_unload_entry: unload platform: %s", entry.entry_id, platform)
            platform_ok = await asyncio.gather(*[hass.config_entries.async_forward_entry_unload(entry, platform)])
            if not platform_ok:
                _LOGGER.error("%s - async_unload_entry: failed to unload: %s (%s)", entry.entry_id, platform, platform_ok)
                all_ok = platform_ok

        entry_data=hass.data[DOMAIN][entry.entry_id]
        if CONF_PYOJBECT in entry_data[CONF_SERVER] and not entry_data[CONF_SERVER].get(CONF_PYOJBECT, None) is None:
            BuiltInServer = entry_data[CONF_SERVER].get(CONF_PYOJBECT)
            if await BuiltInServer.async_dSServerStop("integration_unload") is False:
                _LOGGER.error("%s - async_setup_entry: failed to unload server: %s", DOMAIN, BuiltInServer)
                all_ok = False
            else:
                hass.data[DOMAIN][entry.entry_id].pop(CONF_SERVER)

        if CONF_ADD_ENTITIES in entry_data and not entry_data.get(CONF_ADD_ENTITIES, None) is None:
            hass.data[DOMAIN][entry.entry_id].pop(CONF_ADD_ENTITIES)

        if all_ok:
            _LOGGER.debug("%s - async_unload_entry: Unload option updates listener: %s.%s ", entry.entry_id, FUNC_OPTION_UPDATES)
            hass.data[DOMAIN][entry.entry_id][FUNC_OPTION_UPDATES]()
            _LOGGER.debug("%s - async_unload_entry: Remove data store: %s.%s ", entry.entry_id, DOMAIN, entry.entry_id)
            hass.data[DOMAIN].pop(entry.entry_id)
        return all_ok
    except Exception as e:
        _LOGGER.error("%s - async_unload_entry: Unload device failed: %s (%s.%s)", entry.entry_id, str(e), e.__class__.__module__, type(e).__name__)
        return False

