"""Config flow for dScriptModule."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import (
    CONF_DEVICES,
    CONF_DISCOVERY,
    CONF_HOST,
    CONF_PORT,
    CONF_PROTOCOL,
)
import homeassistant.helpers.config_validation as cv

from .configuration_schema import (
    BOARD_SCHEMA,
    SERVER_SCHEMA,
)
from .const import (
    CONF_ADDANOTHER,
    AVAILABLE_PROTOCOLS,
    CONF_AESKEY,
    CONF_ENABLED,
    CONF_LISTENIP,
    CONF_SERVER,
    CONF_BOARDS,
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

class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Custom config flow."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH
    data: Optional[Dict[str, Any]]
    loaded_platforms = []
    
    def __init__(self):
        """Initialize."""
        _LOGGER.debug("%s - ConfigFlowHandler: __init__", DOMAIN)

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        _LOGGER.debug("%s - ConfigFlowHandler: async_step_user: %s", DOMAIN, user_input)
        try:
            if not hasattr(self, 'data'):
                self.data = {}
            return await self.async_step_server()        
        except Exception as e:
            _LOGGER.error("%s - ConfigFlowHandler: async_step_user failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")        
        
    async def async_step_server(self, user_input: Optional[Dict[str, Any]] = None):
        """Config flow to define server via  user interface."""
        _LOGGER.debug("%s - ConfigFlowHandler: async_step_server: %s", DOMAIN, user_input)
        try:
            errors: Dict[str, str] = {}
            if user_input is not None:
                _LOGGER.debug("%s - ConfigFlowHandler: async_step_server add user_input to data", DOMAIN, user_input) 
                self.data[CONF_SERVER] = user_input
                return await self.async_step_boards()
            _LOGGER.debug("%s - ConfigFlowHandler: async_step_server: CONF_SERVER %s", DOMAIN, CONF_SERVER)                
            return self.async_show_form(step_id=CONF_SERVER, data_schema=SERVER_SCHEMA, errors=errors) #via the "step_id" the function calls itself after GUI completion
        except Exception as e:
            _LOGGER.error("%s - ConfigFlowHandler: async_step_server failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")        
               
    async def async_step_boards(self, user_input: Optional[Dict[str, Any]] = None):
        """Config flow to define boards via  user interface."""
        _LOGGER.debug("%s - ConfigFlowHandler: async_step_boards: %s", DOMAIN, user_input)
        try:
            errors: Dict[str, str] = {}
            if user_input is not None:
                _LOGGER.debug("%s - ConfigFlowHandler: async_step_boards add user_input to data", DOMAIN, user_input)                
                if not CONF_BOARDS in self.data:
                    self.data[CONF_BOARDS] = []     
                self.data[CONF_BOARDS].append(user_input)
                if user_input.get(CONF_ADDANOTHER, False):
                    return await self.async_step_boards()
                return await self.async_step_final()
            return self.async_show_form(step_id=CONF_BOARDS, data_schema=BOARD_SCHEMA, errors=errors) #via the "step_id" the function calls itself after GUI completion        
        except Exception as e:
            _LOGGER.error("%s - ConfigFlowHandler: async_step_boards failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception") 
               
    async def async_step_import(self, user_input: Optional[Dict[str, Any]] = None):
        """Config flow to define integration via YAML."""
        _LOGGER.debug("%s - ConfigFlowHandler: async_step_import: %s", DOMAIN, user_input)
        try:
            for entry in self._async_current_entries():
                if entry.source == config_entries.SOURCE_IMPORT:
                    _LOGGER.debug("%s - ConfigFlowHandler: async_step_import: already existing entry source type: %s", DOMAIN, entry.source)                
                    return self.async_abort(reason="single_instance_allowed")
                    #return False
            #if user_input is None: user_input={}
            return self.async_create_entry(title="configuration.yaml", data=user_input)
        except Exception as e:
            _LOGGER.error("%s - ConfigFlowHandler: async_step_import failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")

    async def async_step_final(self, user_input: Optional[Dict[str, Any]] = None):
        _LOGGER.debug("%s - ConfigFlowHandler: async_step_final: %s", DOMAIN, user_input)
        return self.async_create_entry(title=DOMAIN + " Integration", data=self.data)
            
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        _LOGGER.debug("%s: ConfigFlowHandler - async_get_options_flow", DOMAIN)
        return OptionsFlowHandler(config_entry)
        
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        _LOGGER.debug("%s - OptionsFlowHandler: __init__: %s", DOMAIN, config_entry)
        self.config_entry = config_entry      
                 
    async def async_step_init(self, user_input: Dict[str, Any] = None) -> Dict[str, Any]:
        """Manage the options for the custom component."""
        _LOGGER.debug("%s - OptionsFlowHandler: async_step_init: %s", DOMAIN, user_input)
        try:
            errors: Dict[str, str] = {}
            if self.config_entry.source == config_entries.SOURCE_IMPORT:
                return await self.async_step_import()
            elif self.config_entry.source == config_entries.SOURCE_USER:
                return await self.async_step_config_server()
            else:
                _LOGGER.warning("%s - OptionsFlowHandler: async_step_init: source not supported: %s", DOMAIN, self.config_entry.source)
                return self.async_abort(reason="not_supported")
        except Exception as e:
            _LOGGER.error("%s - OptionsFlowHandler: async_step_init failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
        
    async def async_step_import(self, user_input=None):
        """Options flow extension to Config flow to define integration via YAML."""
        _LOGGER.debug("%s: OptionsFlowHandler - async_step_import: %s", DOMAIN, user_input)
        try:
            if not user_input:
                return self.async_show_form(step_id=config_entries.SOURCE_IMPORT, data_schema=vol.Schema({}))  #via the "step_id" the function calls itself after GUI completion
            _LOGGER.debug("%s - OptionsFlowHandler: async_step_import complete: %s", DOMAIN, user_input)                
            return self.async_create_entry(title="configuration.yaml - 1", data=user_input)
        except Exception as e:
            _LOGGER.error("%s - OptionsFlowHandler: async_step_import failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
            
    async def async_step_config_server(self, user_input=None):
        _LOGGER.debug("%s - OptionsFlowHandler: async_step_config_server: %s", DOMAIN, user_input)
        try:
            if not user_input:
                return self.async_show_form(step_id="config_server", data_schema=SERVER_SCHEMA)
            _LOGGER.debug("%s - OptionsFlowHandler: async_step_config_server - user_input: %s", DOMAIN, user_input)
            self.data.update(user_input)
            _LOGGER.debug("%s - OptionsFlowHandler: async_step_config_server complete: %s", DOMAIN, user_input)
            return await self.async_step_final()
        except Exception as e:
            _LOGGER.error("%s - OptionsFlowHandler: async_step_config_server failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            return self.async_abort(reason="exception")
        
    async def async_step_final(self):
        _LOGGER.debug("%s - OptionsFlowHandler: async_step_final", DOMAIN)
        _LOGGER.debug("%s - OptionsFlowHandler: async_step_final self is %s", DOMAIN, self)
        await async_ProgrammingDebug(self)
        _LOGGER.debug("%s - OptionsFlowHandler: async_step_final self END --", DOMAIN)
        return self.async_create_entry(title=DOMAIN + " integration", data=self.data)

        
