"""Integrated dScriptBoard for device communication"""


from __future__ import annotations
from typing import Final
import logging
import asyncio

from homeassistant.const import (
    CONF_DEVICES,
    CONF_FRIENDLY_NAME,
    CONF_IP_ADDRESS,
)
from homeassistant.helpers import discovery

from dScriptModule import dScriptBoard
from .const import (
    CONF_PYOJBECT,
    CONF_SERVER,
    DEFAULT_AESKEY,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DOMAIN,
    DSCRIPT_ENTITYTYPETOCOUNTATTR,
    DSCRIPT_TOPICTOENTITYTYPE,
    KNOWN_DATA,
)
from .entities import (
    create_entity_unique_id
)
from .utils import (
    async_dScript_setup_entry,
    ProgrammingDebug,
    async_ProgrammingDebug,
)

_LOGGER: Final = logging.getLogger(__name__)


async def async_setup_dScriptBoard(hass: HomeAssistant, entry: ConfigEntry, tcp_ip, tcp_port=DEFAULT_PORT, protocol=DEFAULT_PROTOCOL, aeskey=DEFAULT_AESKEY):
    """Set up a new dScriptBoard."""
    try:
        _LOGGER.debug("%s - %s: async_setup_dScriptBoard: setup board", entry.entry_id, tcp_ip)
        dSBoard = dScriptBoardHA(entry.entry_id, tcp_ip, tcp_port, protocol, aeskey)
        entry_data=hass.data[DOMAIN][entry.entry_id]
        if not entry_data[KNOWN_DATA].get(dSBoard.MACAddress, None) is None and not entry_data[KNOWN_DATA][dSBoard.MACAddress].get(CONF_PYOJBECT, None) is None:
            _LOGGER.warning("%s - %s: async_setup_dScriptBoard: board already exists: %s", entry.entry_id, tcp_ip, dSBoard.name)
            return None

        _LOGGER.debug("%s - %s: async_setup_dScriptBoard: merge known data for: %s", entry.entry_id, tcp_ip, dSBoard.MACAddress)
        dSBoardKnown = entry_data[KNOWN_DATA].get(dSBoard.MACAddress, None)
        if not dSBoardKnown is None:
            dSBoard.friendlyname = dSBoardKnown.get(CONF_FRIENDLY_NAME, dSBoard.friendlyname)
            _LOGGER.debug("%s - %s: async_setup_dScriptBoard: found known data for board: %s - %s", entry.entry_id, tcp_ip, dSBoard.MACAddress, dSBoard.friendlyname)

        _LOGGER.debug("%s - %s: async_setup_dScriptBoard: add to entry_data", entry.entry_id, tcp_ip)
        #entry_data=hass.data[DOMAIN][entry.entry_id]
        entry_data.setdefault(CONF_DEVICES, {})
        entry_data[CONF_DEVICES].setdefault(dSBoard.MACAddress, {})
        entry_data[CONF_DEVICES][dSBoard.MACAddress][CONF_PYOJBECT] = dSBoard

        _LOGGER.debug("%s - %s: async_setup_dScriptBoard: save to known data", entry.entry_id, tcp_ip)        
        entry_data[KNOWN_DATA].setdefault(dSBoard.MACAddress, {})
        entry_data[KNOWN_DATA][dSBoard.MACAddress][CONF_FRIENDLY_NAME] = dSBoard.name
        entry_data[KNOWN_DATA][dSBoard.MACAddress][CONF_IP_ADDRESS] = dSBoard.IP

        _LOGGER.debug("%s - %s: async_setup_dScriptBoard: setup platforms", entry.entry_id, tcp_ip)
        await async_dScript_ValidateBoardConfig(hass, entry, dSBoard, True)
    except Exception as e:
        _LOGGER.error("%s - %s: async_setup_dScriptBoard: failed: %s (%s.%s)", entry.entry_id, tcp_ip, str(e), e.__class__.__module__, type(e).__name__)


async def async_dScript_ValidateBoardConfig(hass: HomeAssistant, entry: ConfigEntry, dSBoard: dScriptBoardHA, init=False):
    """Update configuration and create entities of dScriptBoard."""
    try:
        if init == True:
            _LOGGER.debug("%s - %s: async_dScript_ValidateBoardConfig: initialize board entities", entry.entry_id, dSBoard.name)
            await async_dScript_setup_entry(hass=hass, entry=entry, dSBoardList=[dSBoard])
        else:
            _LOGGER.debug("%s - %s: async_dScript_ValidateBoardConfig: storing board entities count", entry.entry_id, dSBoard.name)
            counts_pre = {}
            for platform in DSCRIPT_TOPICTOENTITYTYPE.values():
                if platform == 'switch' and not dSBoard._CustomFirmeware: pattr = DSCRIPT_ENTITYTYPETOCOUNTATTR['switch_native']
                else: pattr=DSCRIPT_ENTITYTYPETOCOUNTATTR[platform]
                if not hasattr(dSBoard, pattr):
                    _LOGGER.error("%s - %s: async_dScript_ValidateBoardConfig: %s invalid platform or attribute: %s | %s", entry.entry_id, DOMAIN, dSBoard.name, platform, pattr)
                    continue
                counts_pre[platform] = getattr(dSBoard, pattr, 0)
            
            _LOGGER.debug("%s - %s: async_dScript_ValidateBoardConfig: updating board entities count", entry.entry_id, dSBoard.name)
            await dSBoard.async_GetConfig()
            platforms_add_entities=[]
            platforms_remove_entities=[]        
            for platform in counts_pre.keys():
                if platform == 'switch' and not dSBoard._CustomFirmeware: pattr = DSCRIPT_ENTITYTYPETOCOUNTATTR['switch_native']
                else: pattr=DSCRIPT_ENTITYTYPETOCOUNTATTR[platform]
                count_post = getattr(dSBoard, pattr, 0)
                if counts_pre[platform] == count_post: continue
                elif counts_pre[platform] < count_post: platforms_add_entities.append(platform)
                elif counts_pre[platform] > count_post:
                    for identifier in list(range(int(count_post)+1,int(counts_pre[platform])+1)):
                        uniqueid = create_entity_unique_id(dSBoard, identifier, platform)
                        entity_object = async_dScript_GetEntityByUniqueID(hass, entry.entry_id, uniqueid, dSBoard.MACAddress)
                        if entity_object is None:
                            _LOGGER.warning("%s - %s: async_dScript_ValidateBoardConfig: unable to find remove entity: %s", entry.entry_id, dSBoard.name, uniqueid)
                            continue
                        platforms_remove_entities.append(entity_object)

            if platforms_remove_entities:
#            To-Be-Done 
                _LOGGER.debug("%s - %s: async_dScript_ValidateBoardConfig: remove non existing entities (TBD)", entry.entry_id, dSBoard.name)
#                await async_dScript_remove_entry(hass=hass, entry=entry, dSEntityTypes=platforms_add_entities, dSBoardList=[dSBoard])
#                #hass.add_job(entity_object.async_remove())
            if platforms_add_entities:
                _LOGGER.debug("%s - %s: async_dScript_ValidateBoardConfig: register newly added entities", entry.entry_id, dSBoard.name)
                await async_dScript_setup_entry(hass=hass, entry=entry, dSEntityTypes=platforms_add_entities, dSBoardList=[dSBoard])
                #self.hass.async_create_task(discovery.async_load_platform(self.hass, 'light', DOMAIN, dSBoard, self._entry))
    except Exception as e:
        _LOGGER.error("%s - %s: async_dScript_ValidateBoardConfig: failed: %s (%s.%s)", entry.entry_id, dSBoard.name, str(e), e.__class__.__module__, type(e).__name__)


async def async_dScript_SetupKnownBoards(hass: HomeAssistant, entry: ConfigEntry, delay: int = 0):
    """Async: Trigger heartbeat for all known boards"""    
    try:
        await asyncio.sleep(delay)
        _LOGGER.debug("%s - %s: async_dScript_SetupKnownBoards: heartbeat known boards", entry.entry_id, DOMAIN)
        entry_data=hass.data[DOMAIN][entry.entry_id]
        BuiltInServer = entry_data[CONF_SERVER][CONF_PYOJBECT]
        
        for board_entry in list(entry_data.get(KNOWN_DATA, [])):
            _LOGGER.debug("%s - %s: async_dScript_SetupKnownBoards: processing board entry: %s ", entry.entry_id, DOMAIN, board_entry)
            board_entry = entry_data[KNOWN_DATA][board_entry]
            ip_address = board_entry.get(CONF_IP_ADDRESS, None)
            if ip_address is None: continue
            
            _LOGGER.debug("%s - %s: async_dScript_SetupKnownBoards: heartbeat known board IP: %s ", entry.entry_id, DOMAIN, ip_address)
            hass.async_create_task(async_setup_dScriptBoard(hass, entry, ip_address))
    except Exception as e:
        _LOGGER.error("%s - %s: async_dScript_SetupKnownBoards: heartbeat known boards failed: %s (%s.%s)", entry.entry_id, DOMAIN, str(e), e.__class__.__module__, type(e).__name__)
        return None

class dScriptBoardHA(dScriptBoard):
    """Custom variant of dScriptBoard object for HA"""
    available = None
    friendlyname = None
    MACAddress = '00:00:00:00:00:00'
    _ConnectedBoardSensors = 1 #set this fixed to 1 as we have a single board status sensor implemented in HA
    
    def __init__(self, entry_id: str, tcp_ip, tcp_port=DEFAULT_PORT, protocol=DEFAULT_PROTOCOL, aeskey=DEFAULT_AESKEY):
        """Initialize the object."""
        try:
            _LOGGER.debug("%s - %s: dScriptBoardHA __init__: prepare", entry_id, tcp_ip)
            super().__init__(TCP_IP=tcp_ip, TCP_PORT=tcp_port, PROTOCOL=protocol)
            if len(aeskey) > 0:
                self.SetAESKey(aeskey)
        except Exception as e:
            _LOGGER.error("%s - %s: dScriptBoardHA __init__: prepare failed: %s (%s.%s)", entry_id, tcp_ip, str(e), e.__class__.__module__, type(e).__name__)
            return None

        try:
            _LOGGER.debug("%s - %s: dScriptBoardHA __init__: connect", entry_id, tcp_ip)
            self.InitBoard()            
        except Exception as e:
            _LOGGER.error("%s - %s: dScriptBoardHA __init__: connect failed: %s (%s.%s)", entry_id, tcp_ip, str(e), e.__class__.__module__, type(e).__name__)
            return None

        try:
            _LOGGER.debug("%s - %s: dScriptBoardHA __init__: post-process", entry_id, tcp_ip)
            self.available = True
            self.MACAddress = str(self._MACAddress)
            self._cleanup_macaddress()
        except Exception as e:
            _LOGGER.error("%s - %s: dScriptBoardHA __init__: post-process failed: %s (%s.%s)", entry_id, tcp_ip, str(e), e.__class__.__module__, type(e).__name__)
            return None

        _LOGGER.debug("%s - %s: dScriptBoardHA __init__ complete: FW: %s.%s | App: %s.%s | Custom: %s | MAC: %s | IP: %s | Prot: %s", 
            self._HostName, self._SystemFirmwareMajor, self._SystemFirmwareMinor, 
            self._ApplicationFirmwareMajor, self._ApplicationFirmwareMinor, self._CustomFirmeware, self.MACAddress, self.IP, self._Protocol)


    def _cleanup_macaddress(self):
        """Cleanup own MacAddress format"""
        try:
            if len(self.MACAddress) < 17:
                mac=''
                for m in self.MACAddress.split(':'):
                    while len(m) < 2:
                        m = '0' + m
                    mac = mac + ':' + m
                mac = mac.lstrip(':')
                _LOGGER.debug("%s - %s: dScriptBoardHA _cleanup_macaddress: %s -> %s", self._HostName, self.IP, self.MACAddress, mac)
                self.MACAddress = mac
        except Exception as e:
            _LOGGER.error("%s - %s: dScriptBoardHA _cleanup_macaddress failed: %s (%s.%s)", self._HostName, self.IP, str(e), e.__class__.__module__, type(e).__name__)
            

    @property
    def name(self) -> str | None:
        """Return the name of the device."""
        #_LOGGER.debug("%s - %s: name", self._board.friendlyname, self._name)
        if self.friendlyname is None:
            return self._HostName
        else:
            return self.friendlyname
