"""Support for dScript devices from robot-electronics / devantech ltd."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant import config_entries
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
from .configuration_schema import CONFIG_SCHEMA
from .const import (
    CONF_AESKEY,
    CONF_ENABLED,
    CONF_SERVER,
    DATA_BOARDS,
    DATA_CONFIG,
    DATA_DEVICES,
    DATA_SERVER,
    DATA_YAML,
    DOMAIN,
)
from .utils import (
    async_ProgrammingDebug,
    async_getdSDeviceByEntityID,
)

_LOGGER: Final = logging.getLogger(__name__)

async def async_setup(hass, config) -> bool:
    """Setup the dScriptModule component."""
    _LOGGER.debug("%s: async_setup", DOMAIN)

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    if DOMAIN not in config:
        _LOGGER.warning("%s: no configuration.yaml entry found - setup via UI", DOMAIN)
        return True
    
    _LOGGER.warning("%s: configuration.yaml entry found - setup via YAML", DOMAIN) 
    hass.data[DOMAIN][DATA_CONFIG] = config.get(DOMAIN)
    hass.async_create_task(hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}))
    _LOGGER.debug("%s: async_setup complete", DOMAIN)
    #return await async_setup_entry(hass, config)
    return True

async def async_setup_entry(hass, config_entry) -> bool:
    """Setup the dScriptModule component from YAML"""
    _LOGGER.debug("%s: async_setup_entry", DOMAIN)

    async def async_service_UpdateButton(call) -> None:
        """Handle the service request to update a specific button"""
        try:
            _LOGGER.debug("%s - async_service_UpdateButton", call)
            entity_ids=call.data.get(CONF_ENTITY_ID)
            if entity_ids is None:
                _LOGGER.error("%s - async_service_UpdateButton: please define %s in service call data", call, CONF_ENTITY_ID)
                return None
            for entity_id in entity_ids:
                dSDevice = await async_getdSDeviceByEntityID(hass, entity_id)
                if dSDevice is None:
                    _LOGGER.error("%s - async_service_UpdateButton: unable to find entity: %s", call, entity_id)
                    continue
                _LOGGER.debug("%s - async_service_UpdateButton: update poll: %s", call, dSDevice.entity_id)
                hass.async_create_task(dSDevice.async_local_poll())
        except Exception as e:
            _LOGGER.error("%s - async_service_UpdateButton: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    try:
        _LOGGER.debug("%s - async_setup_entry: initialize data values", DOMAIN)
        if not DATA_BOARDS in hass.data[DOMAIN]:
            hass.data[DOMAIN][DATA_BOARDS] = []
        if not DATA_DEVICES in hass.data[DOMAIN]:
            hass.data[DOMAIN][DATA_DEVICES] = []
        if not DATA_SERVER in hass.data[DOMAIN]:    
            hass.data[DOMAIN][DATA_SERVER] = None
    except Exception as e:
        _LOGGER.error("%s -async_setup_entry: initialize data values failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    #WHEN CONFIGURATION.YAML EXISTS
    # -> config_entry = homeassistant.config_entries.ConfigEntry
    # add_update_listener = <bound method ConfigEntry.add_update_listener of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # as_dict = <bound method ConfigEntry.as_dict of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_cancel_retry_setup = <bound method ConfigEntry.async_cancel_retry_setup of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_migrate = <bound method ConfigEntry.async_migrate of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_on_unload = <bound method ConfigEntry.async_on_unload of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_remove = <bound method ConfigEntry.async_remove of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_setup = <bound method ConfigEntry.async_setup of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_shutdown = <bound method ConfigEntry.async_shutdown of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_start_reauth = <bound method ConfigEntry.async_start_reauth of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # async_unload = <bound method ConfigEntry.async_unload of <homeassistant.config_entries.ConfigEntry object at 0x7f01117e6a90>>
    # data = {}
    # disabled_by = None
    # domain = dscriptmodule
    # entry_id = 0cd944ca12b324aa965ab543effe634e
    # options = {}
    # pref_disable_new_entities = False
    # pref_disable_polling = False
    # reason = None
    # source = import
    # state = ConfigEntryState.NOT_LOADED
    # supports_unload = True
    # title = configuration.yaml
    # unique_id = None
    # update_listeners = []
    # version = 1   

    #WHEN CONFIGURATION.YAML NOT EXISTS and INTEGRATION NEWLY ADDED
    # -> config_entry = homeassistant.config_entries.ConfigEntry
    # add_update_listener = <bound method ConfigEntry.add_update_listener of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # as_dict = <bound method ConfigEntry.as_dict of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_cancel_retry_setup = <bound method ConfigEntry.async_cancel_retry_setup of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_migrate = <bound method ConfigEntry.async_migrate of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_on_unload = <bound method ConfigEntry.async_on_unload of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_remove = <bound method ConfigEntry.async_remove of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_setup = <bound method ConfigEntry.async_setup of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_shutdown = <bound method ConfigEntry.async_shutdown of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_start_reauth = <bound method ConfigEntry.async_start_reauth of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # async_unload = <bound method ConfigEntry.async_unload of <homeassistant.config_entries.ConfigEntry object at 0x7fc7b38e3250>>
    # data = {}
    # disabled_by = None
    # domain = dscriptmodule
    # entry_id = c7508a3200b47ad9062b47ec405c39b1
    # options = {}
    # pref_disable_new_entities = False
    # pref_disable_polling = False
    # reason = None
    # source = user
    # state = ConfigEntryState.NOT_LOADED
    # supports_unload = True
    # title = dscriptmodule
    # unique_id = None
    # update_listeners = []
    # version = 1

    #_LOGGER.debug("%s - async_setup_entry: config is %s", DOMAIN, config)
    #await async_ProgrammingDebug(config)
    #_LOGGER.debug("%s - async_setup_entry: config END --", DOMAIN)
    
    try:
        if config_entry.source == config_entries.SOURCE_IMPORT:
            if DATA_CONFIG in hass.data[DOMAIN]:
                _LOGGER.debug("%s - async_setup_entry: YAML import - pre existing: %s", DOMAIN, hass.data[DOMAIN][DATA_CONFIG])
                #data = hass.data[DOMAIN][DATA_CONFIG]
                config = {DOMAIN: hass.data[DOMAIN][DATA_CONFIG]}
            else:
                _LOGGER.debug("%s - async_setup_entry: YAML import - integration to be removed: %s", DOMAIN, config_entry.entry_id)
                data = {}
                await hass.config_entries.async_remove(config_entry.entry_id)
                return True
        elif config_entry.source == config_entries.SOURCE_USER:
            if config_entry.state == config_entries.ConfigEntryState.NOT_LOADED:
                _LOGGER.info("%s - async_setup_entry: default config_entry creation - run options to continue %s", DOMAIN, config_entry)
                return True
            else:
                _LOGGER.debug("%s - async_setup_entry: config_entry is %s", DOMAIN, config_entry)
                await async_ProgrammingDebug(config_entry)
                _LOGGER.debug("%s - async_setup_entry: config_entry END --", DOMAIN)
                return True
        else:
            _LOGGER.error("%s - async_setup_entry: config_flow - not implemented: %s", DOMAIN, config_entry)
            return False

    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: cannot read configuration: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        hass.data[DOMAIN][DATA_CONFIG]=None
        return False

    # Setup the dScriptServer which handles incoming connections if defined within configuration.yaml
    server_config = config[DOMAIN].get(CONF_SERVER)
    if not server_config is None and server_config.get(CONF_ENABLED):
        _LOGGER.info("%s - async_setup_entry: setup server", DOMAIN)
        try:
            #_LOGGER.debug("%s - async_setup_entry: DEBUG hass=%s | config=%s | server_config=%s", DOMAIN, hass, config, server_config)
            hass.data[DOMAIN][DATA_SERVER] = dScriptBuiltInServer(hass, config, server_config)

        except Exception as e:
            _LOGGER.error("%s - async_setup_entry: setup server failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            hass.data[DOMAIN][DATA_SERVER]=None
            return False
    
    # Setup all dScript devices defined within configuration.yaml
    try:
        await asyncio.sleep(0)
        _LOGGER.info("%s - async_setup_entry: setup devices", DOMAIN)
        configured_devices = config[DOMAIN].get(CONF_DEVICES)
        if configured_devices:
            for device in configured_devices:
                await hass.async_add_executor_job(dSBoardSetup, hass, config_entry, device.get(CONF_HOST), device.get(CONF_PORT), device.get(CONF_PROTOCOL), device.get(CONF_AESKEY))
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: setup devices failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        hass.data[DOMAIN][DATA_DEVICES]=None
        return False

    try:
        await asyncio.sleep(0)
        _LOGGER.info("%s - async_setup_entry: setup services", DOMAIN)
        hass.services.async_register(DOMAIN, "updatebutton", async_service_UpdateButton)
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: setup services failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False

    #Setup all platform devices supported by dScriptModule
    hass.async_create_task(async_dSBoardPlatformSetup(hass, config))

    # Return boolean to indicate that initialization was successful.
    _LOGGER.debug("%s - async_setup_entry: component is ready!", DOMAIN)
    return True

async def async_unload_entry(hass, config_entry) -> bool:
    """Unload a config entry."""
    _LOGGER.error("%s: async_unload_entry: not implemented", DOMAIN)
  
    #WHEN CONFIGURATION.YAML EXISTS AND DELETE is selected
    # -> config = homeassistant.config_entries.ConfigEntry
    # add_update_listener = <bound method ConfigEntry.add_update_listener of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # as_dict = <bound method ConfigEntry.as_dict of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_cancel_retry_setup = <bound method ConfigEntry.async_cancel_retry_setup of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_migrate = <bound method ConfigEntry.async_migrate of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_on_unload = <bound method ConfigEntry.async_on_unload of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_remove = <bound method ConfigEntry.async_remove of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_setup = <bound method ConfigEntry.async_setup of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_shutdown = <bound method ConfigEntry.async_shutdown of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_start_reauth = <bound method ConfigEntry.async_start_reauth of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # async_unload = <bound method ConfigEntry.async_unload of <homeassistant.config_entries.ConfigEntry object at 0x7f6f657e89e0>>
    # data = {}
    # disabled_by = None
    # domain = dscriptmodule
    # entry_id = b940658007964a43d79adcff32582c4b
    # options = {}
    # pref_disable_new_entities = False
    # pref_disable_polling = False
    # reason = None
    # source = import
    # state = ConfigEntryState.LOADED
    # supports_unload = True
    # title = configuration.yaml
    # unique_id = None
    # update_listeners = []
    # version = 1

    _LOGGER.debug("%s - async_unload_entry: config_entry is %s", DOMAIN, config_entry)
    await async_ProgrammingDebug(config_entry)
    _LOGGER.debug("%s - async_unload_entry: config_entry END --", DOMAIN)
    
    #instance = hass.data[DOMAIN][DOMAIN][config_entry.entry_id]
    return True    
    
