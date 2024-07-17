"""Diagnostics support for the dScriptModule integration."""

from __future__ import annotations
from importlib_metadata import version
from typing import (
    Final,
    Any,
)
import logging
import asyncio
#import json
import jsonpickle

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.diagnostics import async_redact_data

from .const import (
    DOMAIN,
)

REDACT_CONFIG = {'dummy1', 'dummy2' }
REDACT_DOMAIN_DATA = {'dummy1', 'dummy2' }

_LOGGER: Final = logging.getLogger(__name__)
platform='diagnostics'

async def async_get_config_entry_diagnostics( hass: HomeAssistant, entry: ConfigEntry ) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _LOGGER.debug("Returning %s platform entry: %s", platform, entry.entry_id) 
    try:
        _LOGGER.debug("%s - async_get_config_entry_diagnostics %s: Add config entry configuration to output", entry.entry_id, platform)
        diag: dict[str, Any] = { "config": async_redact_data(entry.as_dict(), REDACT_CONFIG) }
    except Exception as e:
        _LOGGER.error("%s - async_get_config_entry_diagnostics %s: Adding config entry configuration to output failed: %s (%s.%s)", entry.entry_id, platform, str(e), e.__class__.__module__, type(e).__name__)
        #return False

    try:
        _LOGGER.debug("%s - async_get_config_entry_diagnostics %s: Add domain data", entry.entry_id, platform)
        diag["data_domain"] = async_redact_data(hass.data[DOMAIN], REDACT_DOMAIN_DATA)
    except Exception as e:
        _LOGGER.error("%s - async_get_config_entry_diagnostics %s: Add domain data failed: %s (%s.%s)", entry.entry_id, platform, str(e), e.__class__.__module__, type(e).__name__)
        #return False        

    try:
        _LOGGER.debug("%s - async_get_config_entry_diagnostics %s: Add python module [dScriptModule] version", entry.entry_id, platform)
        diag["py_module_dScriptModule"] = version('dScriptModule')
    except Exception as e:
        _LOGGER.error("%s - async_get_config_entry_diagnostics %s: Add python module [dScriptModule] version failed: %s (%s.%s)", entry.entry_id, platform, str(e), e.__class__.__module__, type(e).__name__)
        #return False

    return diag
