"""dscriptmodule helper functions"""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_BOARDS,
    DATA_DEVICES,
    DSDOMAIN_LIGHT,
    DSDOMAIN_COVER,
    DSDOMAIN_SWITCH,
    DSDOMAIN_MOTION,
    DSDOMAIN_BUTTON,
    DSDOMAIN_BOARD,
    DOMAIN,
)

_LOGGER: Final = logging.getLogger(__name__)


async def async_TopicToDomain(topic) -> str | None:
    """Async: map dscript event topic to ha domain"""
    if topic == 'getlight':
        return DSDOMAIN_LIGHT
    elif topic == 'getsocket':
    	return DSDOMAIN_SWITCH
    elif topic == 'getshutter':
    	return DSDOMAIN_COVER
    elif topic == 'getmotion':
        return DSDOMAIN_MOTION
    elif topic == 'getbutton':
    	return DSDOMAIN_BUTTON
    else:
        return None 

async def async_ProgrammingDebug(obj, show_all=False) -> None:
    """Async: return all attributes of a specific objec""" 
    try:
        _LOGGER.debug("%s - async_ProgrammingDebug: %s", DOMAIN, obj)
        for attr in dir(obj):
            if attr.startswith('_') and not show_all:
                continue
            if hasattr(obj, attr ):
                _LOGGER.critical("%s - async_ProgrammingDebug: %s = %s", DOMAIN, attr, getattr(obj, attr))
            await asyncio.sleep(0)
    except Exception as e:
        _LOGGER.critical("%s - async_ProgrammingDebug: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        pass

def ProgrammingDebug(obj, show_all=False) -> None:
    """return all attributes of a specific objec"""
    try:
        _LOGGER.debug("%s - ProgrammingDebug: %s", DOMAIN, obj)
        for attr in dir(obj):
            if attr.startswith('_') and not show_all:
                continue
            if hasattr(obj, attr ):
                _LOGGER.critical("%s - ProgrammingDebug: %s = %s", DOMAIN, attr, getattr(obj, attr))
    except Exception as e:
        _LOGGER.critical("%s - ProgrammingDebug: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        pass

async def async_getdSDeviceByID(hass: HomeAssistant, dSBoardIP: str, identifier: int, domain: str):
    """Async: Gets a dSDevice from list by poviding its dSBoard, topic and identifier"""
    _LOGGER.debug("%s - async_getdSDeviceByID: %s | %s | %s", DOMAIN, dSBoardIP, str(identifier), domain)
    for dSDevice in hass.data[DOMAIN][DATA_DEVICES]:
        try:
            if dSDevice._board.IP == dSBoardIP and dSDevice._identifier == identifier and dSDevice._domain == domain:
                return dSDevice
            await asyncio.sleep(0)
        except NameError as e:
            _LOGGER.debug("%s - async_getdSDeviceByIP: known exception: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
        except Exception as e:
            _LOGGER.error("%s - async_getdSDeviceByIP: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
    #_LOGGER.warning("%s - async_getdSDeviceByIP: cannot find device: %s | %s | %s", DOMAIN, dSBoardIP, str(identifier), domain)
    _LOGGER.debug("%s - async_getdSDeviceByIP: cannot find device: %s | %s | %s", DOMAIN, dSBoardIP, str(identifier), domain)
    return None

async def async_getdSBoardByIP(hass: HomeAssistant, ip: str):
    """Get a board from the board list by its IP"""
    _LOGGER.debug("%s - async_getdSBoardByIP: %s", DOMAIN, ip)
    for dSBoard in hass.data[DOMAIN][DATA_BOARDS]:
        try:
            if dSBoard.IP == IP:
                return dSBoard
            await asyncio.sleep(0)
        except NameError as e:
            _LOGGER.debug("%s - async_getdSBoardByIP: known exception: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
        except Exception as e:
            _LOGGER.error("%s - async_getdSBoardByIP: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
    #_LOGGER.warning("%s - async_getdSBoardByIP: cannot find board: %s", DOMAIN, ip)
    _LOGGER.debug("%s - async_getdSBoardByIP: cannot find board: %s", DOMAIN, ip)
    return None

async def async_getdSBoardByMAC(hass: HomeAssistant, mac: str):
    """Get a board from the board list by its MAC"""
    _LOGGER.debug("%s - async_getdSBoardByMAC: %s", DOMAIN, mac)
    mac = mac.lower()
    for dSBoard in hass.data[DOMAIN][DATA_BOARDS]:
        try:
            if dSBoard._MACAddress.lower() == mac:
                return dSBoard
            await asyncio.sleep(0)
        except NameError as e:
            _LOGGER.debug("%s - async_getdSBoardByMAC: known exception: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
        except Exception as e:
            _LOGGER.error("%s - async_getdSBoardByMAC: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
    #_LOGGER.warning("%s - async_getdSBoardByMAC: cannot find board: %s", DOMAIN, mac)
    _LOGGER.debug("%s - async_getdSBoardByMAC: cannot find board: %s", DOMAIN, mac)
    return None

async def async_getdSDeviceByEntityID(hass: HomeAssistant, entity_id: str):
    """Handle the service request to reset a specific button to 0"""
    try:
        _LOGGER.debug("%s - async_getdSDeviceByEntityID: %s", DOMAIN, entity_id)
        entity=None
        for device in hass.data[DOMAIN][DATA_DEVICES]:
            if device.entity_id == entity_id:
                entity=device
                break
            await asyncio.sleep(0)            
        if entity is None:
            #_LOGGER.warning("%s - async_getdSDeviceByEntityID: cannot find entity: %s", DOMAIN, entity_id)
            _LOGGER.debug("%s - async_getdSDeviceByEntityID: cannot find entity: %s", DOMAIN, entity_id)
            return None
        _LOGGER.debug("%s - async_getdSDeviceByEntityID: found entity: %s", DOMAIN, entity._name)
        return entity
    except Exception as e:
        _LOGGER.error("%s - async_getdSDeviceByEntityID: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)

async def async_setupPlatformdScript(domain, hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info=None) -> None:
    """Wrapper to set up different dScriptModule platforms."""
    devices=[]
    if discovery_info is None:
        #_LOGGER.critical("%s - async_setupPlatformdScript: using DATA_BOARDS %s", domain, discovery_info)
        boards=hass.data[DOMAIN][DATA_BOARDS]
    else:
        #_LOGGER.critical("%s - async_setupPlatformdScript: using discovery_info %s", domain, discovery_info)
        boards=[ discovery_info ]

    for dSBoard in boards:
        _LOGGER.debug("%s - async_setupPlatformdScript: %s", dSBoard.friendlyname, domain)
        if not dSBoard._CustomFirmeware and not domain =='switch' and not domain =='boardsensor':
            _LOGGER.warning("%s - async_setupPlatformdScript: platform %s requires custom firmware - do nothing", dSBoard.friendlyname, domain)
            continue

        if domain == DSDOMAIN_LIGHT:
            from .light import dScriptLight
            boardDevices=dSBoard._ConnectedLights
        elif domain == DSDOMAIN_COVER:
            from .cover import dScriptCover
            boardDevices=dSBoard._ConnectedShutters
        elif domain == DSDOMAIN_SWITCH:
            from .switch import dScriptSwitch
            if dSBoard._CustomFirmeware: # If the board runs custom firmeware connect only switch devices as switch
                boardDevices=dSBoard._ConnectedSockets
            else: # If the board runs default firmware connect all physical relays as switch
                boardDevices=dSBoard._PhysicalRelays
        elif domain == DSDOMAIN_MOTION:
            from .sensor import dScriptMotionSensor
            boardDevices=dSBoard._ConnectedMotionSensors
        elif domain == DSDOMAIN_BUTTON:
            from .sensor import dScriptButtonSensor
            boardDevices=dSBoard._ConnectedButtons
        elif domain == DSDOMAIN_BOARD:
            from .sensor import dScriptBoardSensor
            boardDevices=1
        else:
            _LOGGER.error("%s - async_setupPlatformdScript: invalid platform %s", dSBoard.friendlyname, domain)
            return None

        _LOGGER.debug("%s - async_setupPlatformdScript: prepare %s %s devices", dSBoard.friendlyname, boardDevices, domain)
        i=0
        while i < boardDevices:
            try:
                i += 1
                device = await async_getdSDeviceByID(hass, dSBoard.IP, i, domain)
                if not device is None:
                    _LOGGER.debug("%s - async_setupPlatformdScript: device alreay exists: %s", dSBoard.friendlyname, device._name)
                    continue # If the device already exists do not recreate

                _LOGGER.debug("%s - async_setupPlatformdScript: create new device: %s%s", dSBoard.friendlyname, domain, str(i))
                if domain == DSDOMAIN_LIGHT:
                    device = dScriptLight(dSBoard, i, domain)
                elif domain == DSDOMAIN_COVER:
                    device = dScriptCover(dSBoard, i, domain)
                elif domain == DSDOMAIN_SWITCH:
                    device = dScriptSwitch(dSBoard, i, domain)
                elif domain == DSDOMAIN_MOTION:
                    device = dScriptMotionSensor(dSBoard, i, domain)
                elif domain == DSDOMAIN_BUTTON:
                    device = dScriptButtonSensor(dSBoard, i, domain)
                elif domain == DSDOMAIN_BOARD:
                    device = dScriptBoardSensor(dSBoard, i, domain)
                else:
                    continue

                entity = await async_getdSDeviceByEntityID(hass, device._name)
                if not entity is None:
                    _LOGGER.warning("%s - async_setupPlatformdScript: a device with the equal name / entity_id alreay exists: %s", dSBoard.friendlyname, device._name)
                    continue
                else:
                    hass.data[DOMAIN][DATA_DEVICES].append(device)
                    devices.append(device)
            except Exception as e:
                _LOGGER.error("%s - async_setupPlatformdScript: failed to create %s%s: %s (%s.%s)", dSBoard.friendlyname, domain, i, str(e), e.__class__.__module__, type(e).__name__)
            await asyncio.sleep(0)
        
    _LOGGER.info("%s - async_setupPlatformdScript: setup %s %s devices", DOMAIN, len(devices), domain)
    if not devices:
        return None
    #async_add_entities(devices, update_before_add=True) #-> causes not NoEntitySpecifiedError
    async_add_entities(devices)

