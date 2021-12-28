"""Configuration Schemas for dScriptModule."""

from typing import Final
import logging
import asyncio
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_DEVICES,
    CONF_DISCOVERY,
    CONF_ENTITIES,
    CONF_ENTITY_ID,
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_PORT,
    CONF_PROTOCOL,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    AVAILABLE_PROTOCOLS,
    CONF_AESKEY,
    CONF_BOARDS,
    CONF_ENABLED,
    CONF_LISTENIP,
    CONF_SERVER,
    DEFAULT_AESKEY,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DOMAIN,
)

#_LOGGER: Final = logging.getLogger(__name__)

CONFIG_SCHEMA: Final = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_DEVICES): vol.All(
                    cv.ensure_list,
                    [
                        vol.Schema(
                            {
                                vol.Required(CONF_HOST): cv.string,
                                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                                vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(AVAILABLE_PROTOCOLS),
                                vol.Optional(CONF_AESKEY, default=DEFAULT_AESKEY): cv.string,
                            }
                        )
                    ],
                ),
                vol.Optional(CONF_BOARDS): vol.All(
                    cv.ensure_list,
                    [
                        vol.Schema(
                            {
                                vol.Required(CONF_HOST): cv.string,
                                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                                vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(AVAILABLE_PROTOCOLS),
                                vol.Optional(CONF_AESKEY, default=DEFAULT_AESKEY): cv.string,
                            }
                        )
                    ],
                ),
                vol.Optional(CONF_ENTITIES): vol.All(
                    cv.ensure_list,
                    [
                        vol.Schema(
                            {
                                vol.Required(CONF_MAC): cv.string,
                                vol.Required(CONF_NAME): cv.string,
                            }
                        )
                    ],
                ),
                vol.Optional(CONF_SERVER): vol.Schema(
                    {
                        vol.Required(CONF_ENABLED): cv.boolean,
                        vol.Optional(CONF_LISTENIP, default="0.0.0.0"): cv.string,
                        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                        vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(AVAILABLE_PROTOCOLS),
                        vol.Optional(CONF_AESKEY, default=DEFAULT_AESKEY): cv.string,
                        vol.Optional(CONF_DISCOVERY, default=True): cv.boolean,
                    }
                )
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

STEP_SCHEMA: Final = vol.Schema(
    {
        vol.Optional(CONF_ENABLED, default=True): cv.boolean,
        vol.Optional(CONF_DISCOVERY, default=True): cv.boolean
    }
)
