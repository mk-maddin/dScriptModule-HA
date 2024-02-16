"""Integrated dScriptServer for device communication"""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.const import (
    CONF_PARAMS,
    CONF_PORT,
    CONF_PROTOCOL,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.helpers import discovery

from dScriptModule import dScriptServer
from .board import (
    async_setup_dScriptBoard,
    async_dScript_ValidateBoardConfig,
)
from .const import (
    CONF_AESKEY,
    CONF_LISTENIP,
#    DATA_BOARDS,
    DOMAIN,
    DSCRIPT_TOPICTOENTITYTYPE,
)
from .services import async_registerService
from .utils import (
    async_dScript_GetBoardByIP,
    async_dScript_GetEntityByUniqueID,
    async_ProgrammingDebug,
#    ProgrammingDebug,
)
_LOGGER: Final = logging.getLogger(__name__)

platform = 'dScriptBuiltInServer'

class dScriptBuiltInServer(object):
    """The class for dScriptServer running internally"""
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the object."""
        _LOGGER.debug("%s: __init__", platform)
        self._entry = entry
        self._entry_id = self._entry.entry_id        
        self.hass = hass
        
        _LOGGER.debug("%s - %s: __init__: create server object", platform, self._entry_id)        
        conf_params=hass.data[DOMAIN][entry.entry_id][CONF_PARAMS]
        self.dScriptServer = dScriptServer(conf_params.get(CONF_LISTENIP),conf_params.get(CONF_PORT),conf_params.get(CONF_PROTOCOL))

        _LOGGER.debug("%s - %s: __init__: register dScriptServer event handlers", platform, self._entry_id)
        if len(conf_params.get(CONF_AESKEY)) > 0:
            self.dScriptServer.SetAESKey(conf_params.get(CONF_AESKEY))
        self.dScriptServer.addEventHandler('heartbeat',self.dSBoardHeartbeat)
        self.dScriptServer.addEventHandler('getconfig',self.dSBoardGetConfig)
        self.dScriptServer.addEventHandler('getlight',self.dSBoardEntityUpdate)
        self.dScriptServer.addEventHandler('getsocket',self.dSBoardEntityUpdate)
        self.dScriptServer.addEventHandler('getshutter',self.dSBoardEntityUpdate)
        self.dScriptServer.addEventHandler('getmotion',self.dSBoardEntityUpdate)
        self.dScriptServer.addEventHandler('getbutton',self.dSBoardEntityUpdate)
        
        asyncio.run_coroutine_threadsafe(self.async_dSServerRegisterServices(), self.hass.loop)
        _LOGGER.debug("%s - %s: __init__: complete", platform, self._entry_id)

    async def async_dSServerRegisterServices(self) -> None:
        """Register dScript Services and autostart events for dScriptServer"""
        try:        
            _LOGGER.debug("%s - async_dSServerRegisterServices: register dScriptServer to start/stop with home assistant", self._entry_id)
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self.async_dSServerStart)
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_dSServerStop)

            _LOGGER.debug("%s - async_dSServerRegisterServices: regsiter dScriptServer specific services", self._entry_id)
            await async_registerService(self.hass, "serverstop", self.async_dSServerStop)
            await async_registerService(self.hass, "serverstart", self.async_dSServerStart)
        except Exception as e:
            _LOGGER.error("%s - async_dSServerRegisterServices: failed %s", str(e), self._entry_id)        
        
    async def async_dSServerStart(self, event) -> None | bool:
        """Start the dScriptServer instance"""
        try:
            _LOGGER.debug("%s - async_dSServerStart: Start the dScriptServer", self._entry_id)
            if self.dScriptServer.State == True:
                return None
            await self.dScriptServer.async_StartServer()
            #self.dScriptServer.StartServer()
            i = 0
            while self.dScriptServer.State == False:
                if i > 10: raise Exception("Timeout: ", i)
                i += 1
                await asyncio.sleep(1)
            _LOGGER.debug("%s - async_dSServerStart: started", self._entry_id)
        except Exception as e:
            _LOGGER.error("%s - async_dSServerStop: Could not start dScriptServer: %s (%s.%s)", self._entry_id, str(e), e.__class__.__module__, type(e).__name__)
            return False
            
    async def async_dSServerStop(self, event) -> None | bool:
        """Stop the running dScriptServer instance"""
        try:
            _LOGGER.debug("%s - async_dSServerStop: Stop the dScriptServer", self._entry_id)
            if self.dScriptServer.State == False:
                return None
            await self.dScriptServer.async_StopServer()
            #self.dScriptServer.StopServer()
            i = 0
            while self.dScriptServer.State == True:
                if i > 10: raise Exception("Timeout: ", i)
                i += 1
                await asyncio.sleep(1)
            _LOGGER.debug("%s - async_dSServerStart: stopped", self._entry_id)
        except Exception as e:
            _LOGGER.error("%s - async_dSServerStop: Could not stop dScriptServer: %s (%s.%s)", self._entry_id, str(e), e.__class__.__module__, type(e).__name__)
            return False
            
    async def async_dSBoardHeartbeat(self, sender, event) -> None:
        """Handle incoming hearbeat connection of any board"""
        try:       
            _LOGGER.debug("%s - async_dSBoardHeartbeat: handle %s", sender.sender, event)
            dSBoard = await async_dScript_GetBoardByIP(self.hass, self._entry, sender.sender)
            if not dSBoard:
                _LOGGER.debug("%s - async_dSBoardHearbeat: new board", sender.sender)
                self.hass.async_create_task(async_setup_dScriptBoard(self.hass, self._entry, sender.sender))
            else:
                _LOGGER.debug("%s - async_dSBoardHearbeat: known board %s", sender.sender, dSBoard.friendlyname)
                dSBoard.available = True
                if dSBoard._CustomFirmeware:
                    self.hass.async_create_task(self.async_dSBoardGetConfig(sender, event))
        except Exception as e:
            _LOGGER.error("%s - async_dSBoardHearbeat: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    def dSBoardHeartbeat(self, sender, event):
        """Handle incoming hearbeat connection of any board"""
        try:
            _LOGGER.debug("%s - dSBoardHeartbeat: handle %s", sender.sender, event)
            asyncio.run_coroutine_threadsafe(
                    self.async_dSBoardHeartbeat(sender, event), self.hass.loop)
        except Exception as e:
            _LOGGER.error("%s - dSBoardHearbeat: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    async def async_dSBoardGetConfig(self, sender, event) -> None:
        """Handles incomig getconfig connection of any board"""
        try:
            _LOGGER.debug("%s - async_dSBoardGetConfig: handle %s", sender.sender, event)
            dSBoard = await async_dScript_GetBoardByIP(self.hass, self._entry, sender.sender)
            if not dSBoard:
                _LOGGER.warning("%s - async_dSBoardGetConfig: received trigger from identifyable board: %s", sender.sender, event)
                return None
            self.hass.async_create_task(async_dScript_ValidateBoardConfig(self.hass, self._entry, dSBoard))
        except Exception as e:
            _LOGGER.error("%s - async_dSBoardGetConfig: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    def dSBoardGetConfig(self, sender, event) -> None:
        """Handles incomig getconfig connection of any board"""
        try:
            _LOGGER.debug("%s - dSBoardGetConfig: handle %s", sender.sender, event)
            asyncio.run_coroutine_threadsafe(
                    self.async_dSBoardGetConfig(sender, event), self.hass.loop)
        except Exception as e:
            _LOGGER.error("%s - dSBoardGetConfig: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    async def async_dSBoardEntityUpdate(self, sender, event, process=False) -> None:
        """Perform the update action for specified device if device trigger was received"""
        try:
            if process == False:
                #_LOGGER.debug("%s - async_dSBoardEntityUpdate: restart as independent", sender.sender)
                self.hass.async_create_task(self.async_dSBoardEntityUpdate(sender, event, True))
                return None
            else:
                _LOGGER.debug("%s - async_dSBoardEntityUpdate: handle %s", sender.sender, event)                
                dSEntityType = DSCRIPT_TOPICTOENTITYTYPE[sender.topic]
                dSBoard = await async_dScript_GetBoardByIP(self.hass, self._entry, sender.sender)
                if not dSBoard:
                    _LOGGER.warning("%s - async_dSBoardEntityUpdate: received trigger from not identifyable board: %s", sender.sender, event)
                    return None
                uniqueid = DOMAIN.lower()+"_"+str(dSBoard.MACAddress).replace(':','')+'_'+dSEntityType+str(sender.identifier)                
                entity = await async_dScript_GetEntityByUniqueID(self.hass, self._entry, uniqueid, str(dSBoard.MACAddress))
                if not entity is None:
                    _LOGGER.debug("%s - async_dSBoardEntityUpdate: update push %s to state %s", sender.sender, entity .entity_id, sender.value)
                    self.hass.async_create_task(entity.async_local_push(sender.value))
        except Exception as e:
            _LOGGER.error("%s - async_dSBoardEntityUpdate: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    def dSBoardEntityUpdate(self, sender, event):
        """Perform the update action for specified device if device trigger was received"""
        try:
            #_LOGGER.debug("%s - dSBoardEntityUpdate: handle %s", sender.sender, event)
            asyncio.run_coroutine_threadsafe(
                    self.async_dSBoardEntityUpdate(sender, event),self.hass.loop)
        except Exception as e:
            _LOGGER.error("%s - dSBoardEntityUpdate: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

