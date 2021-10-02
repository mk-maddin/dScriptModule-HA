"""Support for dScript devices from robot-electronics / devantech ltd."""

from __future__ import annotations
from typing import Final
import logging
import asyncio
import voluptuous as vol

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
    EVENT_HOMEASSISTANT_STOP,
    EVENT_HOMEASSISTANT_START,
    STATE_ON,
    STATE_OFF,
)
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

from dScriptModule import dScriptServer, dScriptBoard
from .const import (
    AVAILABLE_PROTOCOLS,
    CONF_AESKEY,
    CONF_ENABLED,
    CONF_LISTENIP,
    CONF_SERVER,
    DATA_BOARDS,
    DATA_DEVICES,
    DATA_SERVER,
    DEFAULT_AESKEY,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DOMAIN,
    NATIVE_ASYNC,
    SERVER_NATIVE_ASYNC,
    SUPPORTED_PLATFORMS,
)
from .utils import (
    async_TopicToDomain,
    async_ProgrammingDebug,
    async_getdSDeviceByID,
    async_getdSBoardByIP,
    async_getdSBoardByMAC,
    async_getdSDeviceByEntityID,
)

_LOGGER: Final = logging.getLogger(__name__)

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


class dScriptBoardHA(dScriptBoard):
    """Custom variant of dScriptBoard object for HA"""
    available = None

async def async_setup(hass, config) -> bool:
    """Setup the dScriptModule component."""
    _LOGGER.debug("%s: async_setup", DOMAIN)

    return await async_setup_entry(hass, config)

async def async_setup_entry(hass, config) -> bool:
    """Setup the dScriptModule component from YAML"""
    _LOGGER.debug("%s: async_setup_entry", DOMAIN)

    def dSBoardSetup(host, port=DEFAULT_PORT, protocol=DEFAULT_PROTOCOL, aeskey=DEFAULT_AESKEY, returnObj=False) -> bool | dScriptBoardHA | None:
        """Connect to a new dScriptBoard"""
        try:
            _LOGGER.debug("%s - dSBoardSetup", host)
            dSBoard = asyncio.run_coroutine_threadsafe(async_getdSBoardByIP(hass, host), hass.loop).result()
            if not dSBoard is None: 
                _LOGGER.debug("%s - dSBoardSetup: already exists (%s)", host, dSBoard.IP)
                if returnObj:
                    return dSBoard
                else:
                    return True

            #dSBoard = dScriptBoard(TCP_IP=host, TCP_PORT=port, PROTOCOL=protocol)
            dSBoard = dScriptBoardHA(TCP_IP=host, TCP_PORT=port, PROTOCOL=protocol)
            if len(aeskey) > 0:
                dSBoard.SetAESKey(aeskey)

            _LOGGER.debug("%s - dSBoardSetup: pre-init via protocol %s", dSBoard._HostName, dSBoard._Protocol)
            dSBoard.InitBoard()
            dSBoard.available = True
            _LOGGER.info("%s - dSBoardSetup: initialized %s (%s)", dSBoard._HostName, dSBoard._ModuleID, dSBoard.IP)
            _LOGGER.debug("%s - dSBoardSetup: Firmware: %s.%s | App: %s.%s | Custom: %s | MAC: %s | IP: %s | Protocol: %s",
                dSBoard._HostName, dSBoard._SystemFirmwareMajor, dSBoard._SystemFirmwareMinor, 
                dSBoard._ApplicationFirmwareMajor, dSBoard._ApplicationFirmwareMinor, dSBoard._CustomFirmeware, dSBoard._MACAddress, dSBoard.IP, dSBoard._Protocol)

            dSBoard2 = asyncio.run_coroutine_threadsafe(async_getdSBoardByMAC(hass, dSBoard._MACAddress), hass.loop).result()
            if not dSBoard2 is None: 
                _LOGGER.debug("%s - dSBoardSetup: already exists (%s)", host, dSBoard2._MACAddress)
                if returnObj:
                    return dSBoard2
                else:
                    return True

            manual_entities = config[DOMAIN].get(CONF_ENTITIES)
            if not manual_entities is None:
                _LOGGER.debug("%s - dSBoardSetup: setting friendly name", dSBoard._HostName)
                for entity in manual_entities:
                    for att in dir(entity):
                        if entity[CONF_MAC].lower() == dSBoard._MACAddress.lower():
                            dSBoard.friendlyname = entity[CONF_NAME]
                            break
            _LOGGER.debug("%s - dSBoardSetup: MAC: %s | FriendlyName %s", dSBoard._HostName, dSBoard._MACAddress, dSBoard.friendlyname)
            
            hass.data[DATA_BOARDS].append(dSBoard)
            if returnObj:
                return dSBoard
            else:
                return True
        except Exception as e:
            _LOGGER.error("%s - dSBoardSetup: failed: %s (%s.%s)", host, str(e), e.__class__.__module__, type(e).__name__)
            if returnObj:
                return None
            else:
                return False

    async def async_dSServerStart(event) -> None:
        """Start the dScriptServer instance"""
        try:
            _LOGGER.debug("async_dSServerStart: Start the dScriptServer")
            if SERVER_NATIVE_ASYNC:
                #hass.data[DATA_SERVER].StartServer_async_thread()
                await hass.data[DATA_SERVER].async_StartServer()
            else:
                hass.data[DATA_SERVER].StartServer()
            i = 0
            while hass.data[DATA_SERVER].State == False:
                if i > 10: raise Exception("Timeout: ", i)
                i += 1
                await asyncio.sleep(1)
        except Exception as e:
            _LOGGER.error("async_dSServerStart: Could not start dScriptServer: %s", str(e))

    async def async_dSServerStop(event) -> None:
        """Stop the running dScriptServer instance"""
        try:
            _LOGGER.debug("async_dSServerStop: Stop the dScriptServer")
            if SERVER_NATIVE_ASYNC:
                #hass.data[DATA_SERVER].StopServer_async_thread()
                await hass.data[DATA_SERVER].async_StopServer()
            else:
                hass.data[DATA_SERVER].StopServer()
            
            i = 0
            while hass.data[DATA_SERVER].State == True:
                if i > 10: raise Exception("Timeout: ", i)
                i += 1
                await asyncio.sleep(1)
        except Exception as e:
            _LOGGER.error("async_dSServerStop: Could not stop dScriptServer: %s", str(e))

    async def async_dSBoardPlatformSetup(dSBoard=None) -> None:
        """Setup different platforms supported by dScriptModule"""
        for platform in SUPPORTED_PLATFORMS:
            _LOGGER.debug("async_dSBoardPlatformSetup: discover platform: %s - %s",DOMAIN, platform)
            hass.async_create_task(
                    discovery.async_load_platform(hass, platform, DOMAIN, dSBoard, config))

    async def async_dSBoardGetConfig(sender, event) -> None:
        """Handles incomig getconfig connection of any board"""
        try:
            _LOGGER.debug("%s - async_dSBoardGetConfig: handle %s", sender.sender, event)
            dSBoard = await async_getdSBoardByIP(hass, host)
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
                hass.async_create_task(
                    discovery.async_load_platform(hass, 'light', DOMAIN, dSBoard, config))
            if not oShutters == dSBoard._ConnectedShutters:
                hass.async_create_task(
                    discovery.async_load_platform(hass, 'cover', DOMAIN, dSBoard, config))
            if not oSwitches == dSBoard._ConnectedSockets:
                hass.async_create_task(
                    discovery.async_load_platform(hass, 'switch', DOMAIN, dSBoard, config))
            if not oMotionSensors == dSBoard._ConnectedMotionSensors or not oButtons == dSBoard._ConnectedButtons:
                hass.async_create_task(
                    discovery.async_load_platform(hass, 'sensor', DOMAIN, dSBoard, config))
        except Exception as e:
            _LOGGER.error("%s - async_dSBoardGetConfig: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    def dSBoardGetConfig(sender, event) -> None:
        """Handles incomig getconfig connection of any board"""
        try:
            _LOGGER.debug("%s - dSBoardGetConfig: handle %s", sender.sender, event)
            asyncio.run_coroutine_threadsafe(
                    async_dSBoardGetConfig(sender, event), hass.loop) 
        except Exception as e:
            _LOGGER.error("%s - dSBoardGetConfig: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    async def async_dSBoardHeartbeat(sender, event) -> None:
        """Handle incoming hearbeat connection of any board"""
        try:
            _LOGGER.debug("%s - async_dSBoardHeartbeat: handle %s", sender.sender, event)
            dSBoard = await async_getdSBoardByIP(hass, sender.sender)
            if not dSBoard:
                _LOGGER.debug("%s - async_dSBoardHearbeat: new board", sender.sender)
                dSBoard = await hass.async_add_executor_job(dSBoardSetup, sender.sender, hass.data[DATA_SERVER].Port, hass.data[DATA_SERVER]._Protocol, hass.data[DATA_SERVER]._AESKey, True)
                hass.async_create_task(async_dSBoardPlatformSetup(dSBoard))
            else:
                _LOGGER.debug("%s - async_dSBoardHearbeat: known board %s", sender.sender, dSBoard.friendlyname)
                dSBoard.available = True
                if dSBoard._CustomFirmeware:
                    async_dSBoardGetConfig(sender, event)
        except Exception as e:
            _LOGGER.error("%s - async_dSBoardHearbeat: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    def dSBoardHeartbeat(sender, event):
        """Handle incoming hearbeat connection of any board"""
        try:
            _LOGGER.debug("%s - dSBoardHeartbeat: handle %s", sender.sender, event)
            asyncio.run_coroutine_threadsafe(
                    async_dSBoardHeartbeat(sender, event), hass.loop)
        except Exception as e:
            _LOGGER.error("%s - dSBoardHearbeat: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    async def async_dSBoardDeviceUpdate(sender, event) -> None:
        """Perform the update action for specified device if device trigger was received"""
        try:
            _LOGGER.debug("%s - async_dSBoardDeviceUpdate: handle %s", sender.sender, event)
            domain = await async_TopicToDomain(sender.topic)
            dSDevice = await async_getdSDeviceByID(hass, sender.sender, sender.identifier, domain)
            _LOGGER.debug("%s - async_dSBoardDeviceUpdate: dSDevice is %s", sender.sender, dSDevice)
            if not dSDevice is None:
                _LOGGER.debug("%s - async_dSBoardDeviceUpdate: update push %s to state %s", sender.sender, dSDevice.entity_id, sender.value)
                hass.async_create_task(dSDevice.async_local_push(sender.value))
        except Exception as e:
            _LOGGER.error("%s - async_dSBoardDeviceUpdate: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    def dSBoardDeviceUpdate(sender, event):
        """Perform the update action for specified device if device trigger was received"""
        try:
            _LOGGER.debug("%s - dSBoardDeviceUpdate: handle %s", sender.sender, event)
            asyncio.run_coroutine_threadsafe(
                    async_dSBoardDeviceUpdate(sender, event),hass.loop)
        except Exception as e:
            _LOGGER.error("%s - dSBoardDeviceUpdate: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    async def async_service_UpdateButton(call) -> None:
        """Handle the service request to update a specific button"""
        try:
            _LOGGER.debug("%s - async_service_UpdateButton", call)
            entity_ids=call.data.get(CONF_ENTITY_ID)
            if entity_ids is None:
                _LOGGER.error("%s - async_service_UpdateButton: please define %s in service call data", call, CONF_ENTITY_ID)
                return None
            for entity_id in entity_ids:
                dSDevice = await async_getdSDeviceByEntityID(hass, entity_id)
                if dSDevice is None:
                    _LOGGER.error("%s - async_service_UpdateButton: unable to find entity: %s", call, entity_id)
                    continue
                _LOGGER.debug("%s - async_service_UpdateButton: update poll: %s", call, dSDevice.entity_id)
                hass.async_create_task(dSDevice.async_local_poll())
        except Exception as e:
            _LOGGER.error("%s - async_service_UpdateButton: failed: %s (%s.%s)", sender.sender, str(e), e.__class__.__module__, type(e).__name__)

    _LOGGER.debug("%s - async_setup_entry: initialize integration values", DOMAIN)
    hass.data[DATA_BOARDS] = []
    hass.data[DATA_DEVICES] = []
    hass.data[DATA_SERVER] = None 

    # Setup the dScriptServer which handles incoming connections if defined within configuration.yaml
    dSSrvConf=config[DOMAIN].get(CONF_SERVER)
    if not dSSrvConf is None and dSSrvConf.get(CONF_ENABLED):
        _LOGGER.info("%s - async_setup_entry: setup server", DOMAIN)
        try:
            hass.data[DATA_SERVER] = dScriptServer(dSSrvConf.get(CONF_LISTENIP),dSSrvConf.get(CONF_PORT),dSSrvConf.get(CONF_PROTOCOL))

            _LOGGER.debug("%s - async_setup_entry: register dScriptServer event handlers", DOMAIN)
            if len(dSSrvConf.get(CONF_AESKEY)) > 0:
                hass.data[DATA_SERVER].SetAESKey(dSSrvConf.get(CONF_AESKEY))
            hass.data[DATA_SERVER].addEventHandler('heartbeat',dSBoardHeartbeat)
            hass.data[DATA_SERVER].addEventHandler('getconfig',dSBoardGetConfig)
            hass.data[DATA_SERVER].addEventHandler('getlight',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getsocket',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getshutter',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getmotion',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getbutton',dSBoardDeviceUpdate)

            #_LOGGER.debug("Setup start the dScriptServer")
            #await async_dSServerStart(None)

            # register server on home assistant start & stop events so it is available when HA starts
            _LOGGER.debug("%s - async_setup_entry: register dScriptServer to start/stop with home assistant", DOMAIN)
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, async_dSServerStart)
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_dSServerStop)

            _LOGGER.debug("%s - async_setup_entry: regsiter dScriptServer specific services", DOMAIN)
            hass.services.async_register(DOMAIN, "serverstop", async_dSServerStop)
            hass.services.async_register(DOMAIN, "serverstart", async_dSServerStart)

        except Exception as e:
            _LOGGER.error("%s - async_setup_entry: setup server failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            hass.data[DATA_SERVER]=None
            return False
    
    # Setup all dScript devices defined within configuration.yaml
    try:
        await asyncio.sleep(0)
        _LOGGER.info("%s - async_setup_entry: setup devices", DOMAIN)
        configured_devices = config[DOMAIN].get(CONF_DEVICES)
        if configured_devices:
            for device in configured_devices:
                await hass.async_add_executor_job(dSBoardSetup, device.get(CONF_HOST), device.get(CONF_PORT), device.get(CONF_PROTOCOL), device.get(CONF_AESKEY))
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: setup devices failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        hass.data[DATA_DEVICES]=None
        return False

    try:
        await asyncio.sleep(0)
        _LOGGER.info("%s - async_setup_entry: setup services", DOMAIN)
        hass.services.async_register(DOMAIN, "updatebutton", async_service_UpdateButton)
    except Exception as e:
        _LOGGER.error("%s - async_setup_entry: setup services failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False

    #Setup all platform devices supported by dScriptModule
    hass.async_create_task(async_dSBoardPlatformSetup())

    # Return boolean to indicate that initialization was successful.
    _LOGGER.debug("%s - async_setup_entry: component is ready!", DOMAIN)
    return True
