"""Support for dScriptModule services."""

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
    DOMAIN,
    DSDOMAIN_BOARD,
    DSDOMAIN_BUTTON,
    DSDOMAIN_MOTION,
)

_LOGGER: Final = logging.getLogger(__name__)

async def async_registerService(hass: HomeAssistant, name:str , service) -> None:
    """Register a service if it does not already exist"""
    try:
        _LOGGER.debug("%s - async_registerService: %s", DOMAIN, name)
        await asyncio.sleep(0)        
        if not hass.services.has_service(DOMAIN, name):
            _LOGGER.info("%s - async_registerServic: register service: %s", DOMAIN, name)
            hass.services.async_register(DOMAIN, name, service)
        else:
            _LOGGER.warning("%s - async_registerServic: service already exists: %s", DOMAIN, name)  
    except Exception as e:
        _LOGGER.error("%s - async_registerService: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)        
    
async def async_service_UpdateButton(call) -> None:
    """Handle the service request to update a specific button"""
    try:
        _LOGGER.debug("%s - async_service_UpdateButton", call)
        entity_ids=call.data.get(CONF_ENTITY_ID)
        if entity_ids is None:
            _LOGGER.error("%s - async_service_UpdateButton: please define %s in service call data", call, CONF_ENTITY_ID)
            return None
        for entity_id in entity_ids:
            dSDevice = await async_getdSEntityByEntityID(hass, entity_id)
            if dSDevice is None:
                _LOGGER.error("%s - async_service_UpdateButton: unable to find entity: %s", call, entity_id)
                continue
            _LOGGER.debug("%s - async_service_UpdateButton: update poll: %s", call, dSDevice.entity_id)
            hass.async_create_task(dSDevice.async_local_poll())
    except Exception as e:
        _LOGGER.error("%s - async_service_UpdateButton: %s failed: %s (%s.%s)", call, str(e), e.__class__.__module__, type(e).__name__)
  