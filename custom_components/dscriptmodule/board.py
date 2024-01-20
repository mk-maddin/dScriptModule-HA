"""Board creation functions"""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.const import (
    CONF_ENTITIES,
    CONF_MAC,
    CONF_NAME,
)
from homeassistant.helpers import discovery

from dScriptModule import dScriptBoard
from .const import (
    DATA_BOARDS,
    DEFAULT_AESKEY,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DOMAIN,
    SUPPORTED_PLATFORMS,
)
from .utils import (
    async_getdSBoardByIP,
    async_getdSBoardByMAC,
)

_LOGGER: Final = logging.getLogger(__name__)

async def async_dSBoardPlatformSetup(hass, config, dSBoard=None) -> None:
    """Setup different platforms supported by dScriptModule"""
    for platform in SUPPORTED_PLATFORMS:
        _LOGGER.debug("async_dSBoardPlatformSetup: discover platform: %s - %s",DOMAIN, platform)
        hass.async_create_task(
            discovery.async_load_platform(hass, platform, DOMAIN, dSBoard, config))

class dScriptBoardHA(dScriptBoard):
    """Custom variant of dScriptBoard object for HA"""
    available = None

def dSBoardSetup(hass, config, host, port=DEFAULT_PORT, protocol=DEFAULT_PROTOCOL, aeskey=DEFAULT_AESKEY, returnObj=False) -> bool | dScriptBoardHA | None:
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

        _LOGGER.debug("%s - dSBoardSetup: MAC cleanup (%s)", host, dSBoard._MACAddress)
        if len(dSBoard._MACAddress) < 17:
            mac=''
            for m in dSBoard._MACAddress.split(':'):
                while len(m) < 2:
                    m = '0' + m
                mac = mac + ':' + m
            mac = mac.lstrip(':')
            _LOGGER.info("%s - dSBoardSetup: MAC %s updated to %s", host, dSBoard._MACAddress, mac)
            dSBoard._MACAddress = mac

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
        
        hass.data[DOMAIN][DATA_BOARDS].append(dSBoard)
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
