"""Integrated dScriptServer for device communication"""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.const import (
    CONF_PORT,
    CONF_PROTOCOL,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.helpers import discovery

from dScriptModule import dScriptServer
from .board import dSBoardSetup, async_dSBoardPlatformSetup
from .const import (
    CONF_AESKEY,
    CONF_LISTENIP,
    DOMAIN,
    NATIVE_ASYNC,
    SERVER_NATIVE_ASYNC,
)
from .utils import (
    async_TopicToDomain,
    async_getdSDeviceByID,
    async_getdSBoardByIP,
)
_LOGGER: Final = logging.getLogger(__name__)

THISCLASS = 'dScriptBuiltInServer'

class dScriptBuiltInServer(object):
    """The class for dScriptServer running internally"""

    def __init__(self, hass, config, server_config) -> None:
        """Initialize the object."""
        _LOGGER.debug("%s: __init__", THISCLASS)
        self.hass = hass
        self.config = config
        self.dScriptServer = dScriptServer(server_config.get(CONF_LISTENIP),server_config.get(CONF_PORT),server_config.get(CONF_PROTOCOL))

        _LOGGER.debug("%s - __init__: register dScriptServer event handlers", THISCLASS)
        if len(server_config.get(CONF_AESKEY)) > 0:
            self.dScriptServer.SetAESKey(server_config.get(CONF_AESKEY))
        self.dScriptServer.addEventHandler('heartbeat',self.dSBoardHeartbeat)
        self.dScriptServer.addEventHandler('getconfig',self.dSBoardGetConfig)
        self.dScriptServer.addEventHandler('getlight',self.dSBoardDeviceUpdate)
        self.dScriptServer.addEventHandler('getsocket',self.dSBoardDeviceUpdate)
        self.dScriptServer.addEventHandler('getshutter',self.dSBoardDeviceUpdate)
        self.dScriptServer.addEventHandler('getmotion',self.dSBoardDeviceUpdate)
        self.dScriptServer.addEventHandler('getbutton',self.dSBoardDeviceUpdate)
        
        asyncio.run_coroutine_threadsafe(self.async_dSServerRegisterServices(), self.hass.loop)            
        _LOGGER.debug("%s: __init__: complete", THISCLASS)

    async def async_dSServerRegisterServices(self) -> None:
        """Register dScript Services and autostart events for dScriptServer"""
        try:        
            _LOGGER.debug("%s - async_dSServerRegisterServices: register dScriptServer to start/stop with home assistant", THISCLASS)
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self.async_dSServerStart)
            self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.async_dSServerStop)

            _LOGGER.debug("%s - async_dSServerRegisterServices: regsiter dScriptServer specific services", THISCLASS)
            self.hass.services.async_register(DOMAIN, "serverstop", self.async_dSServerStop)
            self.hass.services.async_register(DOMAIN, "serverstart", self.async_dSServerStart)
        except Exception as e:
            _LOGGER.error("%s - async_dSServerRegisterServices: failed %s", str(e), THISCLASS)        
        
    async def async_dSServerStart(self, event) -> None:
        """Start the dScriptServer instance"""
        try:
            _LOGGER.debug("%s - async_dSServerStart: Start the dScriptServer", THISCLASS)
            if SERVER_NATIVE_ASYNC:
                await self.dScriptServer.async_StartServer()
            else:
                self.dScriptServer.StartServer()
            i = 0
            while self.dScriptServer.State == False:
                if i > 10: raise Exception("Timeout: ", i)
                i += 1
                await asyncio.sleep(1)
        except Exception as e:
            _LOGGER.error("%s - async_dSServerStart: Could not start dScriptServer: %s", str(e), THISCLASS)

    async def async_dSServerStop(self, event) -> None:
        """Stop the running dScriptServer instance"""
        try:
            _LOGGER.debug("%s - async_dSServerStop: Stop the dScriptServer", THISCLASS)
            if SERVER_NATIVE_ASYNC:
                await self.dScriptServer.async_StopServer()
            else:
                self.dScriptServer.StopServer()

            i = 0
            while self.dScriptServer.State == True:
                if i > 10: raise Exception("Timeout: ", i)
                i += 1
                await asyncio.sleep(1)
        except Exception as e:
            _LOGGER.error("%s - async_dSServerStop: Could not stop dScriptServer: %s", str(e), THISCLASS)

    async def async_dSBoardHeartbeat(self, sender, event) -> None:
        """Handle incoming hearbeat connection of any board"""
        try:
            _LOGGER.debug("%s - async_dSBoardHeartbeat: handle %s", sender.sender, event)
            dSBoard = await async_getdSBoardByIP(self.hass, sender.sender)
            if not dSBoard:
                _LOGGER.debug("%s - async_dSBoardHearbeat: new board", sender.sender)
                dSBoard = await self.hass.async_add_executor_job(dSBoardSetup, self.hass, self.config, sender.sender, self.dScriptServer.Port, self.dScriptServer._Protocol, self.dScriptServer._AESKey, True)
                self.hass.async_create_task(async_dSBoardPlatformSetup(self.hass, self.config, dSBoard))
            else:
                _LOGGER.debug("%s - async_dSBoardHearbeat: known board %s", sender.sender, dSBoard.friendlyname)
                dSBoard.available = True
                if dSBoard._CustomFirmeware:
                    self.async_dSBoardGetConfig(sender, event)
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
            dSBoard = await async_getdSBoardByIP(self.hass, host)
            if not dSBoard:
                _LOGGER.warning("%s - async_dSBoardGetConfig: received trigger from uninitialized board: %s", sender.sender, sender.sender.IP)
                return False
            _LOGGER.debug("%s - dSBoardGetConfig: async check if board config was updated: %s", sender.sender, dSBoard.friendlyname)
            oLights=dSBoard._ConnectedLights
            oShutters=dSBoard._ConnectedShutters
            oSwitches=dSBoard._ConnectedSockets
            oMotionSensors=dSBoard._ConnectedMotionSensors
            oButtons=dSBoard._ConnectedButtons
            if NATIVE_ASYNC:
                await dSBoard.async_GetConfig()
            else:
                dSBoard.GetConfig()
            if not oLights == dSBoard._ConnectedLights:
                self.hass.async_create_task(
                    discovery.async_load_platform(self.hass, 'light', DOMAIN, dSBoard, self.config))
            if not oShutters == dSBoard._ConnectedShutters:
                self.hass.async_create_task(
                    discovery.async_load_platform(self.hass, 'cover', DOMAIN, dSBoard, self.config))
            if not oSwitches == dSBoard._ConnectedSockets:
                self.hass.async_create_task(
                    discovery.async_load_platform(self.hass, 'switch', DOMAIN, dSBoard, self.config))
            if not oMotionSensors == dSBoard._ConnectedMotionSensors or not oButtons == dSBoard._ConnectedButtons:
                self.hass.async_create_task(
                    discovery.async_load_platform(self.hass, 'sensor', DOMAIN, dSBoard, self.config))
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


    async def async_dSBoardDeviceUpdate(self, sender, event) -> None:
        """Perform the update action for specified device if device trigger was received"""
        try:
            _LOGGER.debug("%s - async_dSBoardDeviceUpdate: handle %s", sender.sender, event)
            domain = await async_TopicToDomain(sender.topic)
            dSDevice = await async_getdSDeviceByID(self.hass, sender.sender, sender.identifier, domain)
            _LOGGER.debug("%s - async_dSBoardDeviceUpdate: dSDevice is %s", sender.sender, dSDevice)
            if not dSDevice is None:
                _LOGGER.debug("%s - async_dSBoardDeviceUpdate: update push %s to state %s", sender.sender, dSDevice.entity_id, sender.value)
                self.hass.async_create_task(dSDevice.async_local_push(sender.value))
        except Exception as e:
            _LOGGER.error("%s - async_dSBoardDeviceUpdate: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    def dSBoardDeviceUpdate(self, sender, event):
        """Perform the update action for specified device if device trigger was received"""
        try:
            _LOGGER.debug("%s - dSBoardDeviceUpdate: handle %s", sender.sender, event)
            asyncio.run_coroutine_threadsafe(
                    self.async_dSBoardDeviceUpdate(sender, event),self.hass.loop)
        except Exception as e:
            _LOGGER.error("%s - dSBoardDeviceUpdate: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)
