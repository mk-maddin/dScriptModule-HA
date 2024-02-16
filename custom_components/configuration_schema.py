"""Configuration Schemas for dScriptModule."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_FRIENDLY_NAME,
    CONF_PORT,
    CONF_PROTOCOL,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    AVAILABLE_PROTOCOLS,
    CONF_AESKEY,
    CONF_LISTENIP,
    CONF_SERVER,
    DEFAULT_AESKEY,
    DEFAULT_LISTENIP,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DOMAIN,
)

_LOGGER: Final = logging.getLogger(__name__)

DSCRIPTMODULE_SCHEMA: Final = vol.Schema({
    vol.Required(CONF_FRIENDLY_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_LISTENIP, default=DEFAULT_LISTENIP): cv.string,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Required(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(AVAILABLE_PROTOCOLS),
    vol.Optional(CONF_AESKEY, default=DEFAULT_AESKEY): cv.string,
})

async def async_get_OPTIONS_DSCRIPTMODULE_SCHEMA(current_data):
    """Async: return an schema object with current values as default""" 
    try:
        _LOGGER.debug("%s - async_get_OPTIONS_DSCRIPTMODULE_SCHEMA", DOMAIN)        
        #_LOGGER.debug("%s - async_get_OPTIONS_DSCRIPTMODULE_SCHEMA: current_data: %s", DOMAIN, current_data)        
        OPTIONS_DSCRIPTMODULE_SCHEMA: Final = vol.Schema({
            vol.Required(CONF_FRIENDLY_NAME, default=current_data.get(CONF_FRIENDLY_NAME,DEFAULT_NAME)): cv.string,
            vol.Required(CONF_LISTENIP, default=current_data.get(CONF_LISTENIP,DEFAULT_LISTENIP)): cv.string,
            vol.Required(CONF_PORT, default=current_data.get(CONF_PORT, DEFAULT_PORT)): cv.port,
            vol.Required(CONF_PROTOCOL, default=current_data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)): vol.In(AVAILABLE_PROTOCOLS),
            vol.Optional(CONF_AESKEY, default=current_data.get(CONF_AESKEY, DEFAULT_AESKEY)): cv.string,
        })
        await asyncio.sleep(0)
        return OPTIONS_DSCRIPTMODULE_SCHEMA
    except Exception as e:
        _LOGGER.error("%s - async_get_OPTIONS_DSCRIPTMODULE_SCHEMA: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return DSCRIPTMODULE_SCHEMA
