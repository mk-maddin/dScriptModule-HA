"""Config flow for dScriptModule."""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant import config_entries

from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)

class dScriptConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """dScript config flow."""
    _LOGGER.info("%s: dScriptConfigFlow", domain)