"""dscriptmodule helper functions"""

from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_BOARDS,
    DATA_BOARDS,
    DATA_ENTITIES,
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
    """Async: map dscript event topic to ha platform"""
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
                _LOGGER.debug("%s - async_ProgrammingDebug: %s = %s", DOMAIN, attr, getattr(obj, attr))
            await asyncio.sleep(0)
    except Exception as e:
        _LOGGER.error("%s - async_ProgrammingDebug: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        pass

def ProgrammingDebug(obj, show_all=False) -> None:
    """return all attributes of a specific objec"""
    try:
        _LOGGER.debug("%s - ProgrammingDebug: %s", DOMAIN, obj)
        for attr in dir(obj):
            if attr.startswith('_') and not show_all:
                continue
            if hasattr(obj, attr ):
                _LOGGER.debug("%s - ProgrammingDebug: %s = %s", DOMAIN, attr, getattr(obj, attr))
    except Exception as e:
        _LOGGER.error("%s - ProgrammingDebug: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        pass

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
    _LOGGER.debug("%s - async_getdSBoardByMAC: cannot find board: %s", DOMAIN, mac)
    return None

async def async_getdSEntityByID(hass: HomeAssistant, dSBoardIP: str, identifier: int, domain: str):
    """Async: Gets a dScript Entity from list by poviding its dSBoard, topic and dSBoard internal identifier"""
    _LOGGER.debug("%s - async_getdSEntityByID: %s | %s | %s", DOMAIN, dSBoardIP, str(identifier), domain)
    for dSDevice in hass.data[DOMAIN][DATA_ENTITIES]:
        try:
            if dSDevice._board.IP == dSBoardIP and dSDevice._identifier == identifier and dSDevice._domain == domain:
                return dSDevice
            await asyncio.sleep(0)
        except NameError as e:
            _LOGGER.debug("%s - async_getdSEntityByID: known exception: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
        except Exception as e:
            _LOGGER.error("%s - async_getdSEntityByID: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
            continue
    _LOGGER.debug("%s - async_getdSEntityByID: cannot find device: %s | %s | %s", DOMAIN, dSBoardIP, str(identifier), domain)
    return None    
    
async def async_getdSEntityByEntityID(hass: HomeAssistant, entity_id: str):
    """Async: Gets a dScript Entity from list by poviding its entity_id"""
    try:
        _LOGGER.debug("%s - async_getdSEntityByEntityID: %s", DOMAIN, entity_id)
        entity=None
        for device in hass.data[DOMAIN][DATA_ENTITIES]:
            if device.entity_id == entity_id:
                entity=device
                break
            await asyncio.sleep(0)            
        if entity is None:
            _LOGGER.debug("%s - async_getdSEntityByEntityID: cannot find entity: %s", DOMAIN, entity_id)
            return None
        _LOGGER.debug("%s - async_getdSEntityByEntityID: found entity: %s", DOMAIN, entity._name)
        return entity
    except Exception as e:
        _LOGGER.error("%s - async_getdSEntityByEntityID: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False

async def async_setupPlatformdScript(platform, hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback, discovery_info=None) -> None:
    """Wrapper to set up different dScriptModule platforms."""
    entites=[]
    try:
        _LOGGER.debug("%s - async_setupPlatformdScript: %s", DOMAIN, platform)
        if discovery_info is None:
            boards=hass.data[DOMAIN][DATA_BOARDS]
            _LOGGER.debug("%s - async_setupPlatformdScript: using DATA_BOARDS %s", DOMAIN, boards)
        else:
            boards=[ discovery_info ]
            _LOGGER.debug("%s - async_setupPlatformdScript: using discovery_info %s", DOMAIN, boards)
    except Exception as e:
        _LOGGER.error("%s - async_setupPlatformdScript: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False

    _LOGGER.debug("%s - async_setupPlatformdScript: %s boards to process", DOMAIN, len(boards))
    for dSBoard in boards:
        try:
            _LOGGER.debug("%s - async_setupPlatformdScript: %s", dSBoard.friendlyname, platform)
            if not dSBoard._CustomFirmeware and not platform =='switch' and not platform =='boardsensor':
                _LOGGER.warning("%s - async_setupPlatformdScript: platform %s requires custom firmware - do nothing", dSBoard.friendlyname, platform)
                continue

            if platform == DSDOMAIN_LIGHT:
                from .light import dScriptLight
                boardEntities=dSBoard._ConnectedLights
            elif platform == DSDOMAIN_COVER:
                from .cover import dScriptCover
                boardEntities=dSBoard._ConnectedShutters
            elif platform == DSDOMAIN_SWITCH:
                from .switch import dScriptSwitch
                if dSBoard._CustomFirmeware: # If the board runs custom firmeware connect only switch devices as switch
                    boardEntities=dSBoard._ConnectedSockets
                else: # If the board runs default firmware connect all physical relays as switch
                    boardEntities=dSBoard._PhysicalRelays
            elif platform == DSDOMAIN_MOTION:
                from .sensor import dScriptMotionSensor
                boardEntities=dSBoard._ConnectedMotionSensors
            elif platform == DSDOMAIN_BUTTON:
                from .sensor import dScriptButtonSensor
                boardEntities=dSBoard._ConnectedButtons
            elif platform == DSDOMAIN_BOARD:
                from .sensor import dScriptBoardSensor
                boardEntities=1
            else:
                _LOGGER.error("%s - async_setupPlatformdScript: invalid platform %s", dSBoard.friendlyname, platform)
                return None

            _LOGGER.debug("%s - async_setupPlatformdScript: prepare %s %s entites", dSBoard.friendlyname, boardEntities, platform)
            i=0
            while i < boardEntities:
                try:
                    i += 1
#                    entity = await async_getdSEntityByID(hass, dSBoard.IP, i, platform)
#                    if not entity is None:
#                        _LOGGER.debug("%s - async_setupPlatformdScript: entity alreay exists: %s", dSBoard.friendlyname, entity._name)
#                        continue # If the entity already exists do not recreate

                    _LOGGER.debug("%s - async_setupPlatformdScript: create new entity: %s%s", dSBoard.friendlyname, platform, str(i))
                    if platform == DSDOMAIN_LIGHT:
                        entity = dScriptLight(dSBoard, i, platform)
                    elif platform == DSDOMAIN_COVER:
                        entity = dScriptCover(dSBoard, i, platform)
                    elif platform == DSDOMAIN_SWITCH:
                        entity = dScriptSwitch(dSBoard, i, platform)
                    elif platform == DSDOMAIN_MOTION:
                        entity = dScriptMotionSensor(dSBoard, i, platform)
                    elif platform == DSDOMAIN_BUTTON:
                        entity = dScriptButtonSensor(dSBoard, i, platform)
                    elif platform == DSDOMAIN_BOARD:
                        entity = dScriptBoardSensor(dSBoard, i, platform)
                    else:
                        continue

                    entity_exist = await async_getdSEntityByEntityID(hass, entity._name)
                    if not entity_exist is None:
                        _LOGGER.warning("%s - async_setupPlatformdScript: a entity with the equal name / entity_id alreay exists: %s", dSBoard.friendlyname, entity._name)
                        continue
                    else:
                        hass.data[DOMAIN][DATA_ENTITIES].append(entity)
                        entites.append(entity)
                except Exception as e:
                    _LOGGER.error("%s - async_setupPlatformdScript: failed to create %s%s: %s (%s.%s)", dSBoard.friendlyname, platform, i, str(e), e.__class__.__module__, type(e).__name__)
                await asyncio.sleep(0)
        except Exception as e:
            _LOGGER.error("%s - async_setupPlatformdScript: setup %s failed: %s (%s.%s)", dSBoard.friendlyname, platform, str(e), e.__class__.__module__, type(e).__name__)
            return False
                
    _LOGGER.info("%s - async_setupPlatformdScript: setup %s %s entitys", DOMAIN, len(entites), platform)
    if not entites:
        return None
    #async_add_entities(entites, update_before_add=True) #-> causes not NoEntitySpecifiedError
    async_add_entities(entites)

