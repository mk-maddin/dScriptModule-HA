"""Support for dScriptModule services."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import functools

from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
)

_LOGGER: Final = logging.getLogger(__name__)

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
