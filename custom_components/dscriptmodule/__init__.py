"""Support for dScript devices from robot-electronics / devantech ltd."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant import config_entries, core
from homeassistant.const import (
    CONF_DEVICES,
    CONF_ENTITY_ID,
    CONF_HOST,
    CONF_PORT,
    CONF_PROTOCOL,
    EVENT_HOMEASSISTANT_STOP,
    EVENT_HOMEASSISTANT_START,
)

from dScriptModule import dScriptBoard
from .board import dSBoardSetup, async_dSBoardPlatformSetup
from .server import dScriptBuiltInServer
from .services import (
    async_registerService,
    async_service_UpdateButton,
)
from .configuration_schema import CONFIG_SCHEMA
from .const import (
    CONF_AESKEY,
    CONF_ENABLED,
    CONF_SERVER,
    DATA_BOARDS,
    DATA_CONFIG,
    DATA_ENTITIES,
    DATA_SERVER,
    DOMAIN,
    SUPPORTED_PLATFORMS,
)
from .utils import (
    async_ProgrammingDebug,
    async_getdSEntityByEntityID,
)

_LOGGER: Final = logging.getLogger(__name__)

async def async_setup(hass: core.HomeAssistant, config) -> bool:
    """Setup the dScriptModule component."""
    _LOGGER.debug("%s: async_setup", DOMAIN)
    try:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN].setdefault(DATA_BOARDS, [])        
        hass.data[DOMAIN].setdefault(DATA_SERVER, None)
        hass.data[DOMAIN].setdefault(DATA_ENTITIES, [])        
        if DOMAIN not in config:
            _LOGGER.debug("%s: no Configuration.yaml entry found - setup via GUI", DOMAIN)
            return True
        
        _LOGGER.debug("%s: Configuration.yaml entry found - setup from YAML", DOMAIN)
        hass.data[DOMAIN][DATA_CONFIG] = config.get(DOMAIN)
        hass.async_create_task(hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}))
        _LOGGER.debug("%s: async_setup complete", DOMAIN)
        return True
    except Exception as e:
        _LOGGER.error("%s - async_setup: setup devices failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False
    
async def async_setup_entry(hass: core.HomeAssistant, config_entry) -> bool:
    """Setup the dScriptModule component from YAML"""
    _LOGGER.debug("%s: async_setup_entry", DOMAIN)

    try:
        if config_entry.source == config_entries.SOURCE_IMPORT:
            if DATA_CONFIG in hass.data[DOMAIN]:
                _LOGGER.debug("%s - async_setup_entry: setup from configuration.yaml entry: %s", DOMAIN, hass.data[DOMAIN][DATA_CONFIG])
                config_entry.data = hass.data[DOMAIN][DATA_CONFIG]
                hass.data[DOMAIN].pop(DATA_CONFIG, None)
            else:
                _LOGGER.warning("%s - async_setup_entry: no configuration.yaml entry: %s - remove integration: %s", DOMAIN, DOMAIN, config_entry.entry_id)
                await hass.config_entries.async_remove(config_entry.entry_id)
                hass.data[DOMAIN].pop(config_entry.entry_id, None)
                return True
        elif config_entry.source == config_entries.SOURCE_USER:
            if not config_entry.data:
                _LOGGER.error("%s - async_setup_entry: missing data within config_entry: %s", DOMAIN, config_entry)
                return False
        else:
            _LOGGER.error("%s - async_setup_entry: config_entry - setup type not implemented: %s", DOMAIN, config_entry)
            return False
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: cannot read configuration: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        hass.data[DOMAIN][DATA_CONFIG]=None
        return False            
            
    try:
        _LOGGER.debug("%s - async_setup_entry: add config_entry options_update_listener", DOMAIN)
        hass_data = dict(config_entry.data)
        unsub_options_update_listener = config_entry.add_update_listener(options_update_listener)
        hass_data["unsub_options_update_listener"] = unsub_options_update_listener
        hass.data[DOMAIN][config_entry.entry_id] = hass_data
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: config_entry options_update_listener adding failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False

    #_LOGGER.debug("%s - async_setup_entry: hass_data is %s", DOMAIN, hass_data)
    #await async_ProgrammingDebug(hass_data)
    #_LOGGER.debug("%s - async_setup_entry: hass_data END --", DOMAIN)        
        
    # Setup the dScriptServer which handles incoming connections if defined
    server_config = config_entry.data.get(CONF_SERVER, None)
    if not server_config is None and server_config.get(CONF_ENABLED):
        _LOGGER.info("%s - async_setup_entry: setup server", DOMAIN)
        try:
            if DATA_SERVER in hass.data[DOMAIN] and hass.data[DOMAIN][DATA_SERVER] is not None:
                BuiltInServer = hass.data[DOMAIN][DATA_SERVER]
                _LOGGER.warning("%s - async_setup_entry: dScriptServer already exists: %s", DOMAIN, BuiltInServer)
            else:
                _LOGGER.debug("%s - async_setup_entry: create new dScriptServer", DOMAIN)
                BuiltInServer = dScriptBuiltInServer(hass, config_entry, server_config)
                hass.data[DOMAIN][DATA_SERVER] = BuiltInServer
            
            if BuiltInServer.dScriptServer.State is False:
                _LOGGER.debug("%s - async_setup_entry: start dScriptServer", DOMAIN)
                await BuiltInServer.async_dSServerStart("integration_setup")                

        except Exception as e:
            _LOGGER.error("%s - async_setup_entry: setup server failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            hass.data[DOMAIN][DATA_SERVER]=None
            return False        
        
    # Setup all dScript devices defined
    try:
        await asyncio.sleep(0)
        _LOGGER.info("%s - async_setup_entry: setup devices", DOMAIN)
        configured_devices = config_entry.data.get(CONF_DEVICES, None)
        if configured_devices:
            for device in configured_devices:
                _LOGGER.debug("%s - async_setup_entry: setup device: %s", DOMAIN, device.get(CONF_HOST))
                await hass.async_add_executor_job(dSBoardSetup, hass, config_entry, device.get(CONF_HOST), device.get(CONF_PORT), device.get(CONF_PROTOCOL), device.get(CONF_AESKEY))
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: setup devices failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        hass.data[DOMAIN][DATA_DEVICES]=None
        return False        
 
    # Register all dScript services defined
    try:
        await async_registerService(hass, "updatebutton", async_service_UpdateButton)                  
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: register services failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False 
   
    #Setup all platforms supported by dScriptModule
    countBoards=len(hass.data[DOMAIN][DATA_BOARDS])
    if countBoards > 0:
        hass.async_create_task(async_dSBoardPlatformSetup(hass, config_entry))    
    
    _LOGGER.debug("%s - async_setup_entry: component is ready!", DOMAIN)
    return True

async def async_unload_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("%s: async_unload_entry", DOMAIN)
    try:
        all_ok = True
        for platform in SUPPORTED_PLATFORMS:
            _LOGGER.debug("%s - async_setup_entry: unload platform: %s", DOMAIN, platform)
            platform_ok = await asyncio.gather(*[hass.config_entries.async_forward_entry_unload(config_entry, platform)])
            
            if not platform_ok:
                _LOGGER.error("%s - async_setup_entry: failed to unload: %s (%s)", DOMAIN, platform, platform_ok)
                all_ok = platform_ok

        if DATA_SERVER in hass.data[DOMAIN] and hass.data[DOMAIN][DATA_SERVER] is not None:
            BuiltInServer = hass.data[DOMAIN][DATA_SERVER]
            if await BuiltInServer.async_dSServerStop("integration_unload") is False:
                _LOGGER.error("%s - async_setup_entry: failed to unload server: %s", DOMAIN, BuiltInServer)
                all_ok = False
            else:
                hass.data[DOMAIN][DATA_SERVER] = None
        
        hass.data[DOMAIN][config_entry.entry_id]["unsub_options_update_listener"]()
        if all_ok:            
            hass.data[DOMAIN].pop(config_entry.entry_id)        
        return all_ok   
    except Exception as e:
        _LOGGER.error("%s - async_unload_entry: setup devices failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False
        
async def options_update_listener(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry):
    """Handle options update."""
    _LOGGER.debug("%s: options_update_listener", DOMAIN)
    try:    
        await hass.config_entries.async_reload(config_entry.entry_id)
    except Exception as e:
        _LOGGER.error("%s - options_update_listener setup devices failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False    
