"""Config flow for dScriptModule."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import (
    CONF_DISCOVERY,
    CONF_PORT,
    CONF_PROTOCOL,
)
import homeassistant.helpers.config_validation as cv

from .configuration_schema import STEP_SCHEMA
from .const import (
    AVAILABLE_PROTOCOLS,
    CONF_AESKEY,
    CONF_ENABLED,
    CONF_LISTENIP,
    CONF_SERVER,
    DATA_CONFIG,
    DATA_YAML,
    DEFAULT_AESKEY,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DOMAIN,
)
from .utils import (
    async_ProgrammingDebug,
    ProgrammingDebug,
)

_LOGGER: Final = logging.getLogger(__name__)

class dScriptConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    
    def __init__(self):
        """Initialize."""
        _LOGGER.debug("%s: dScriptConfigFlowHandler - __init__", DOMAIN)

    async def async_step_user(self, user_input={}):
        _LOGGER.debug("%s: dScriptConfigFlowHandler - async_step_user: %s", DOMAIN, user_input)
        try:
            for entry in self._async_current_entries():
                if entry.source == config_entries.SOURCE_USER:
                    return self.async_abort(reason="single_instance_allowed")
            if user_input is None: user_input={}
            return self.async_create_entry(title=DOMAIN, data=user_input)
        except Exception as e:
            _LOGGER.error("%s - dScriptConfigFlowHandler: async_step_user failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
        
    async def async_step_import(self, user_input={}):
        """Import a config entry."""
        _LOGGER.debug("%s: dScriptConfigFlowHandler - async_step_import: %s", DOMAIN, user_input)
        try:
            for entry in self._async_current_entries():
                if entry.source == config_entries.SOURCE_IMPORT:
                    return self.async_abort(reason="single_instance_allowed")
            #if user_input is None: user_input={}
            return self.async_create_entry(title="configuration.yaml", data=user_input)
        except Exception as e:
            _LOGGER.error("%s - dScriptConfigFlowHandler: async_step_import failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
            
    @staticmethod
    @callback
    def async_get_options_flow(config):
        _LOGGER.debug("%s: dScriptConfigFlowHandler - async_get_options_flow", DOMAIN)
        return dScriptOptionsFlowHandler(config)
        
class dScriptOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler."""

    def __init__(self, config):
        """Initialize options flow."""
        _LOGGER.debug("%s: dScriptOptionsFlowHandler - __init__: %s", DOMAIN, config)
        self.config_entry = config
        self._options = {}
        
        _LOGGER.debug("%s - dScriptOptionsFlowHandler: config is %s", DOMAIN, config)
        ProgrammingDebug(config)
        _LOGGER.debug("%s - dScriptOptionsFlowHandler: config END --", DOMAIN)
        
        _LOGGER.debug("%s - dScriptOptionsFlowHandler: self is %s", DOMAIN, self)
        ProgrammingDebug(self)
        _LOGGER.debug("%s - dScriptOptionsFlowHandler: self END --", DOMAIN)        
    
    def v(self, id, sys_default):
            #self.instance is coming from previously defined hass.data[DOMAIN][config_entry.entry_id] -> define later
        #current = self.instance.conf.get(id, None)
        if current is None:
            current=sys_default
        return vol.Optional(id, default=current)        
        
    async def async_step_init(self, user_input=None):
        """Manage the options."""
        _LOGGER.debug("%s: dScriptOptionsFlowHandler - async_step_init: %s", DOMAIN, user_input)
        try:
            if self.config_entry.source == config_entries.SOURCE_IMPORT and not self.config_entry.options:
                return await self.async_step_yaml()
            elif self.config_entry.source == config_entries.SOURCE_USER:
                return await self.async_step_config_server()
                #return await self.async_step_yaml()
            else:
                _LOGGER.warning("%s: dScriptOptionsFlowHandler - async_step_init: source not supported: %s", DOMAIN, self.config_entry.source)
                return self.async_abort(reason="not_supported")
        except Exception as e:
            _LOGGER.error("%s - dScriptOptionsFlowHandler: async_step_init failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
        
    async def async_step_yaml(self, user_input=None):
        _LOGGER.debug("%s: dScriptOptionsFlowHandler - async_step_yaml: %s", DOMAIN, user_input)
        try:
            if not user_input:
                schema = vol.Schema({
                    vol.Optional("convert", default=False): bool
                })
                return self.async_show_form(step_id="yaml", data_schema=schema)

            system_options = {}
            if user_input["convert"]:
                _LOGGER.warning("%s: dScriptOptionsFlowHandler - async_step_yaml: convert workflow not supported (yet)", DOMAIN)
                return self.async_abort(reason="not_supported")
            _LOGGER.debug("%s: dScriptOptionsFlowHandler - async_step_yaml complete: %s", DOMAIN, user_input)                
            return self.async_create_entry(title=DOMAIN + " integration",  data=system_options)
        except Exception as e:
            _LOGGER.error("%s - dScriptOptionsFlowHandler: async_step_yaml failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
            
    async def async_step_config_server(self, user_input=None):
        _LOGGER.debug("%s: dScriptOptionsFlowHandler - async_step_config_server: %s", DOMAIN, user_input)
        try:
            if not user_input:
                schema = vol.Schema({
                    self.v(CONF_ENABLED, True): cv.boolean,
                    self.v(CONF_LISTENIP, "0.0.0.0"): cv.string,
                    self.v(CONF_PORT, DEFAULT_PORT): cv.port,
                    self.v(CONF_PROTOCOL, DEFAULT_PROTOCOL): vol.In(AVAILABLE_PROTOCOLS),
                    self.v(CONF_AESKEY, DEFAULT_AESKEY): cv.string,
                    self.v(CONF_DISCOVERY, True): cv.boolean,
                })
                return self.async_show_form(step_id="config_server", data_schema=schema)

            _LOGGER.debug("%s: dScriptOptionsFlowHandler - async_step_config_server - user_input: %s", DOMAIN, user_input)
            self._options.update(user_input)
            _LOGGER.debug("%s: dScriptOptionsFlowHandler - async_step_config_server complete: %s", DOMAIN, user_input)
            return await self.async_step_final()
        except Exception as e:
            _LOGGER.error("%s - dScriptOptionsFlowHandler: async_step_config_server failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
        
    async def async_step_final(self):
        _LOGGER.debug("%s: dScriptOptionsFlowHandler - async_step_final", DOMAIN, user_input)
        return self.async_create_entry(title=DOMAIN + " integration", data=self._options)

        
