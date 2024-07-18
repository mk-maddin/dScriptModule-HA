"""dscriptmodule helper functions"""

from __future__ import annotations
from getmac import get_mac_address
from typing import Final
from importlib import import_module
import logging
import asyncio


from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
#from homeassistant.helpers.entity_registry import EntityRegistry
from homeassistant.const import (
    CONF_DEVICES,
)


from .const import (
    CONF_ADD_ENTITIES,
    CONF_PYOJBECT,
    DOMAIN,
    DSCRIPT_ENTITYTYPETOCOUNTATTR,
    DSCRIPT_TOPICTOENTITYTYPE,
)

_LOGGER: Final = logging.getLogger(__name__)


#TO-BE-DONE FUNCTION -> save json cache (service call?)

def get_mac_address_from_ip(ip) -> str | None:
    """get mac address form IP - warapper for async execution"""
    try:
        #_LOGGER.debug("%s - get_mac_address_from_ip", DOMAIN)
        mac = get_mac_address(ip=ip)
        _LOGGER.debug("%s - get_mac_address_from_ip: %s -> %s", DOMAIN, ip, mac)
        if mac == '00:00:00:00:00:00':
            return None
        return mac
    except Exception as e:
        _LOGGER.error("%s - get_mac_address_from_ip: failed: %s (%s.%s)", DOMAIN, str(e), e.__class__.__module__, type(e).__name__)


async def async_ProgrammingDebug(obj, show_all=False) -> None:
    """Async: return all attributes of a specific object""" 
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
    """return all attributes of a specific object"""
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


async def async_dScript_GetBoardByIP(hass: HomeAssistant, entry: ConfigEntry, ip: str, data: bool=False):
    """Async: Receive dScript board object from IP address"""
    try:
        entry_data=hass.data[DOMAIN][entry.entry_id]
        _LOGGER.debug("%s - async_dScript_GetBoardByIP: searching by IP for: %s", entry.entry_id, ip)
        
        for board_mac in hass.data[DOMAIN][entry.entry_id][CONF_DEVICES]:
            board_entry=hass.data[DOMAIN][entry.entry_id][CONF_DEVICES].get(board_mac)
            dSBoard=board_entry.get(CONF_PYOJBECT, None)
            if dSBoard is None: continue
            if not dSBoard.IP == ip: continue
            if data:
                return board_entry
            return board_entry.get(CONF_PYOJBECT, None)

        board_mac = await hass.async_add_executor_job(get_mac_address_from_ip, ip)
        if not board_mac is None:
            board_entry = entry_data[CONF_DEVICES].get(board_mac, None)
            if not board_entry is None and data:
                return board_entry
            elif not board_entry is None:
                return board_entry.get(CONF_PYOJBECT, None)
        
        #TO-BE-DONE: LOOP over boards and search for matching IP
        #for board in entry_data[CONF_DEVICES]:

        _LOGGER.debug("%s - async_dScript_GetBoardByIP: cannot find board: %s", entry.entry_id, ip)
        return None
    except Exception as e:
            _LOGGER.error("%s - async_dScript_GetBoardByIP: Failed to search for %s: %s (%s.%s)", entry.entry_id, ip, str(e), e.__class__.__module__, type(e).__name__)


async def async_dScript_GetEntityByUniqueID(hass: HomeAssistant, config_entry_id: str, uniqueid: str, dSBoardMac: Optional[str] = None): 
    """Async: Receive dScript entity object from uniqueid"""    
    try:
        _LOGGER.debug("%s - %s: async_dScript_GetEntityByUniqueID: searching for: %s", config_entry_id, DOMAIN, uniqueid)
        entry_data=hass.data[DOMAIN][config_entry_id]
        entity = None
        if not dSBoardMac is None:
            board_entry = entry_data[CONF_DEVICES].get(dSBoardMac, None)
            if not board_entry is None:
                entity = board_entry.get(uniqueid, None)        
        if entity is None:
            for board_mac in entry_data[CONF_DEVICES]:
                board_entry = entry_data[CONF_DEVICES].get(board_mac)
                entity = board_entry.get(uniqueid, None)
                if not entity is None:
                    return entity
        return entity
    except Exception as e:
        _LOGGER.error("%s - %s: async_dScript_GetEntityByUniqueID: search failed: %s (%s.%s)", config_entry_id, DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return None


async def async_dScript_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Optional[AddEntitiesCallback] = None, dSEntityTypes: list=[], dSBoardList: list=[]) -> None:
    """Async: Register entities for a specific platform or a specific dSBoard""" 
    try:
        _LOGGER.debug("%s - %s: async_dScript_setup_entry: preparing work data", entry.entry_id, DOMAIN)
        platform=None
        entry_data=hass.data[DOMAIN][entry.entry_id]
        entry_data.setdefault(CONF_DEVICES, {})
        if dSEntityTypes == []: dSEntityTypes = DSCRIPT_TOPICTOENTITYTYPE.values()
        if dSBoardList == []:
            for board_entry in entry_data[CONF_DEVICES]:
                dSBoard = board_entry.get(CONF_PYOJBECT, None)
                if not dSBoard is None: dSBoardList.add(dSBoard)
    except Exception as e:
        _LOGGER.error("%s - %s: async_dScript_setup_entry: getting entry data failed: %s (%s.%s)", entry.entry_id, DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return False

    _LOGGER.debug("%s - %s: async_dScript_setup_entry: import entity classes", entry.entry_id, DOMAIN)
    from .switch import dScriptSwitch
    from .light import dScriptLight
    from .cover import dScriptCover
    from .sensor_board import dScriptBoardSensor
    from .sensor_button import dScriptButtonSensor
    from .sensor_motion import dScriptMotionSensor
    
    DSCRIPT_ENTITYTYPETOOBJECT: Final = {
        "light": dScriptLight,
        "switch": dScriptSwitch,
    #    "switch_native": "dScriptSwitch",
        "cover":  dScriptCover,
        "sensor_motion": dScriptMotionSensor,
        "sensor_button": dScriptButtonSensor,
        "sensor_board": dScriptBoardSensor
    }    

    try:
        _LOGGER.debug("%s - %s: async_dScript_setup_entry: preparing platform data", entry.entry_id, DOMAIN)        
        for platform in dSEntityTypes:
            #_LOGGER.debug("%s - %s: async_dScript_setup_entry: processing platform: %s", entry.entry_id, DOMAIN, platform)
            entites=[]
            platform_async_add_entities = None        
            if not async_add_entities is None:
                entry_data.setdefault(CONF_ADD_ENTITIES, {})
                entry_data[CONF_ADD_ENTITIES].setdefault(platform, async_add_entities)
                platform_async_add_entities = async_add_entities
            elif async_add_entities is None and CONF_ADD_ENTITIES in entry_data:
                platform_async_add_entities = entry_data[CONF_ADD_ENTITIES].get(platform, None)

            if platform_async_add_entities is None:
                _LOGGER.warning("%s - %s: async_dScript_setup_entry: No AddEntitiesCallback for platform: %s", entry.entry_id, DOMAIN, platform)
                continue        

            for dSBoard in dSBoardList:
                try:
                    _LOGGER.debug("%s - %s: async_dScript_setup_entry: %s setting up %s platform", entry.entry_id, DOMAIN, dSBoard.name, platform)
                    await asyncio.sleep(0)
                    identifier = 0

                    if platform == 'switch' and not dSBoard._CustomFirmeware: pattr = DSCRIPT_ENTITYTYPETOCOUNTATTR['switch_native']
                    else: pattr=DSCRIPT_ENTITYTYPETOCOUNTATTR[platform]
                    if not hasattr(dSBoard, pattr):
                        _LOGGER.error("%s - %s: async_dScript_setup_entry: %s invalid platform or attribute: %s | %s", entry.entry_id, DOMAIN, dSBoard.name, platform, pattr)
                        continue

                    while identifier < getattr(dSBoard, pattr, 0):
                        identifier += 1
                        _LOGGER.debug("%s - %s: async_dScript_setup_entry: %s setting up entity %s.%s", entry.entry_id, DOMAIN, dSBoard.name, platform, identifier)
                        
                        entity = DSCRIPT_ENTITYTYPETOOBJECT[platform](hass, entry, dSBoard, identifier, platform)
                        if not await async_dScript_GetEntityByUniqueID(hass, entry.entry_id, entity.uniqueid, dSBoard.MACAddress) is None:
                            #_LOGGER.warning("%s - %s: async_dScript_setup_entry: %s entity %s already exists", entry.entry_id, DOMAIN, dSBoard.name, entity.uniqueid)
                            _LOGGER.debug("%s - %s: async_dScript_setup_entry: %s entity %s already exists", entry.entry_id, DOMAIN, dSBoard.name, entity.uniqueid)
                            continue
                        entry_data[CONF_DEVICES][dSBoard.MACAddress][entity.uniqueid] = entity
                        entites.append(entity)            
                except Exception as e:
                    _LOGGER.error("%s - %s: async_dScript_setup_entry: %s setting up %s platform failed: %s (%s.%s)", entry.entry_id, DOMAIN, dSBoard.name, platform, str(e), e.__class__.__module__, type(e).__name__)
                    return False
            if entites:
                platform_async_add_entities(entites)
    except Exception as e:
        _LOGGER.error("%s - %s: async_dScript_setup_entry: preparing platform data %s failed: %s (%s.%s)", entry.entry_id, DOMAIN, platform, str(e), e.__class__.__module__, type(e).__name__)
        return False

