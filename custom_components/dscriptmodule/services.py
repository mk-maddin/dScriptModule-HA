"""Support for dScriptModule services."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import functools

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_IP_ADDRESS,
)

from .const import (
    DOMAIN,
    CONF_ENTRY_ID,
    CONF_PYOJBECT,
    CONF_SERVER,
    KNOWN_DATA,
)
from .utils import (
    async_ProgrammingDebug,
    async_dScript_GetEntityByUniqueID,
)

_LOGGER: Final = logging.getLogger(__name__)

class DummySender(object):    
    sender = None
    def __init__(self, sender):
        self.sender = sender

async def async_registerService(hass: HomeAssistant, name:str , service) -> None:
    """Async: Register a service if it does not already exist"""
    try:
        _LOGGER.debug("%s - async_registerService: %s", DOMAIN, name)
        await asyncio.sleep(0)        
        if not hass.services.has_service(DOMAIN, name):
            #_LOGGER.info("%s - async_registerServic: register service: %s", DOMAIN, name)
            #hass.services.async_register(DOMAIN, name, service)
            hass.services.async_register(DOMAIN, name, functools.partial(service, hass))
        else:
            _LOGGER.debug("%s - async_registerServic: service already exists: %s", DOMAIN, name)  
    except Exception as e:
        _LOGGER.error("%s - async_registerService: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)


async def async_service_UpdateButton(hass: HomeAssistant, call) -> None | bool:
    """Async: Handle the service request to update a specific button"""
    try:
        _LOGGER.debug("%s - async_service_UpdateButton", call)
        entity_ids=call.data.get(CONF_ENTITY_ID)
        if entity_ids is None:
            _LOGGER.error("%s - async_service_UpdateButton: please define %s in service call data", call, CONF_ENTITY_ID)
            return False
        entity_reg = entity_registry.async_get(hass)
        if isinstance(entity_ids, str): entity_ids = [ entity_ids ]
        if entity_reg is None:
            _LOGGER.error("%s - async_service_UpdateButton: unable to load entity registry", call)
            return False               
        for entity_id in entity_ids:
            entity_reg_obj = entity_reg.async_get(entity_id)
            if entity_reg_obj is None:
                _LOGGER.error("%s - async_service_UpdateButton: unable to find entity registry object: %s", call, entity_id)
                continue
            entity_obj = await async_dScript_GetEntityByUniqueID(hass, entity_reg_obj.config_entry_id, entity_reg_obj.unique_id)
            if entity_obj is None:
                _LOGGER.error("%s - async_service_UpdateButton: unable to find entity object: %s", call, entity_id)
                continue
            _LOGGER.debug("%s - async_service_UpdateButton: update poll: %s", call, entity_obj.entity_id)            
            hass.async_create_task(entity_obj.async_local_poll())
    except Exception as e:
        _LOGGER.error("%s - async_service_UpdateButton: failed: %s (%s.%s)", call, str(e), e.__class__.__module__, type(e).__name__)
        return False

async def async_service_HeartbeatKnownBoards(hass: HomeAssistant, call) -> None | bool:
    """Async: Handle the service request to heartbeat known boards"""
    try:
        _LOGGER.debug("%s - async_service_HeartbeatKnownBoards", call)
        config_entry_id=call.data.get(CONF_ENTRY_ID)
        if config_entry_id is None:
            _LOGGER.error("%s - async_service_HeartbeatKnownBoards: please define %s in service call data", call, CONF_ENTRY_ID)
            return False
        entry_data=hass.data[DOMAIN][config_entry_id]
        if entry_data is None:
            _LOGGER.error("%s - async_service_HeartbeatKnownBoards: unable to find entry_data", call)
            return False
        
        BuiltInServer = entry_data[CONF_SERVER][CONF_PYOJBECT]
        if BuiltInServer is None:
            _LOGGER.error("%s - async_service_HeartbeatKnownBoards: %s server not existing", call, DOMAIN)
            return False
        elif BuiltInServer.dScriptServer.State is False:
            _LOGGER.error("%s - async_service_HeartbeatKnownBoards: %s server not running", call, DOMAIN)
            return False

        for board_entry in list(entry_data.get(KNOWN_DATA, [])):
            _LOGGER.debug("%s - async_service_HeartbeatKnownBoards: processing board entry: %s ", call, DOMAIN, board_entry)
            board_entry = entry_data[KNOWN_DATA][board_entry]
            ip_address = board_entry.get(CONF_IP_ADDRESS, None)
            if ip_address is None: continue
            
            _LOGGER.debug("%s - async_service_HeartbeatKnownBoards: processing board entry: %s ", call, DOMAIN, ip_address)
            sender = DummySender(ip_address)
            await BuiltInServer.async_dSBoardHeartbeat(sender, 'service_heartbeat')
            #hass.async_create_task(async_setup_dScriptBoard(hass, entry, ip_address))
    except Exception as e:
        _LOGGER.error("%s - async_service_HeartbeatKnownBoards: failed: %s (%s.%s)", call, str(e), e.__class__.__module__, type(e).__name__)
        return False
