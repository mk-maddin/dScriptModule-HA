"""Support for dScript devices from robot-electronics / devantech ltd."""
import logging

from dScriptModule import dScriptServer, dScriptBoard
import voluptuous as vol

from homeassistant.const import (
    CONF_DEVICES,
    CONF_DISCOVERY,
    CONF_ENTITIES,
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

_LOGGER = logging.getLogger(__name__)

SUPPORTED_DOMAINS = ["light", "switch", "cover", "sensor"]
DOMAIN = 'dScriptModule'

CONF_AESKEY='aes_key'
CONF_SERVER='server'
CONF_ENABLED='enabled'
CONF_LISTENIP='listen_ip'

DEFAULT_PORT=17123
DEFAULT_PROTOCOL="binary"
DEFAULT_AESKEY=""

DATA_DEVICES=DOMAIN + "_Devices"
DATA_BOARDS=DOMAIN + "_Boards"
DATA_SERVER=DOMAIN + "_Server"

CONFIG_SCHEMA = vol.Schema(
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
                                vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(['modbus','ascii','binary','binaryaes']),
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
                        vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(['modbus','ascii','binary','binaryaes']),
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
    """For HA adjusted class of the dScriptBoard"""
    friendlyname=None

def getdSDeviceByID(hass, dSBoardIP, identifier, topic):
    """Gets a dSDevice from list by poviding its dSBoard, topic and identifier"""
    #_LOGGER.debug("getdSDeviceByID: search device")
    for dSDevice in hass.data[DATA_DEVICES]:
        #_LOGGER.debug("getdSDeviceByID: check device: %s", dSDevice.entity_id)
        #_LOGGER.debug("getdSDeviceByID: %s = %s | %s = %s | %s = %s", dSDevice._board.IP, dSBoardIP, dSDevice._identifier, identifier, dSDevice._topic, topic)
        if dSDevice._board.IP == dSBoardIP and dSDevice._identifier == identifier and dSDevice._topic == topic:
            return dSDevice
    return None

def setup(hass, config):
    """Setup the dScriptModule component."""

    def getdSBoardByIP(host):
        """Get a board from the board list by its IP"""
        for dSBoard in hass.data[DATA_BOARDS]:
            if dSBoard.IP == host:
                return dSBoard
        return False
    
    def dSBoardSetup(host, port=DEFAULT_PORT, protocol=DEFAULT_PROTOCOL, aeskey=DEFAULT_AESKEY):
        """Connect to a new dScriptBoard"""
        if getdSBoardByIP(host): 
            _LOGGER.debug("dSBoardConnect: Board is already setup: %s",host)
            return True
        _LOGGER.debug("dSBoardConnect: Setup board: %s", host)

        try:
            #dSBoard = dScriptBoard(TCP_IP=host, TCP_PORT=port, PROTOCOL=protocol)
            dSBoard = dScriptBoardHA(TCP_IP=host, TCP_PORT=port, PROTOCOL=protocol)
            if len(aeskey) > 0:
                dSBoard.SetAESKey(aeskey)
        except:
            _LOGGER.warning("dSBoardConnect: Creation of dScriptBoard %s failed", host)
            _LOGGER.warning("dSBoardConnect: If using an AESKey verify it is exactly 32 characters long")
            return False
        
        try:
            _LOGGER.debug("dSBoardConnect: %s: PRE-init board (%s)", dSBoard._HostName, dSBoard._Protocol)
            dSBoard.InitBoard()
            #dSBoard.GetStatus()
            #dSBoard.GetConfig()
            _LOGGER.info("dSBoardConnect: %s: Initialized board %s (%s)", dSBoard._HostName, dSBoard._ModuleID, dSBoard._Protocol)
            _LOGGER.debug("dSBoardConnect: %s: Firmware: %s.%s | App: %s.%s | Custom: %s", 
                    dSBoard._HostName, dSBoard._SystemFirmwareMajor, dSBoard._SystemFirmwareMinor, dSBoard._ApplicationFirmwareMajor, dSBoard._ApplicationFirmwareMinor, dSBoard._CustomFirmeware)
        except:
            _LOGGER.warning("dSBoardConnect: %s: Initialization of board failed", host)
            return False

        try:
            _LOGGER.debug("dSBoardConnect: %s: Setting friendly name", dSBoard._HostName)
            dSBoard.friendlyname = dSBoard._HostName
            manual_entities = config[DOMAIN].get(CONF_ENTITIES)
            if not manual_entities == None:
                for entity in manual_entities:
                    for att in dir(entity):
                        if entity[CONF_MAC] == dSBoard._MACAddress:
                            dSBoard.friendlyname = entity[CONF_NAME]
                            _LOGGER.debug("dSBoardConnect: %s: Using manual friendly name", dSBoard._HostName)
                            break
            _LOGGER.debug("dSBoardConnect: %s: MAC: %s | FriendlyName %s", dSBoard._HostName, dSBoard._MACAddress, dSBoard.friendlyname)
        except:
            _LOGGER.warning("dSBoardConnect: %s: Could not set friendly name (%s)", dSBoard._HostName, dSBoard.friendlyname)

        hass.data[DATA_BOARDS].append(dSBoard)
        return True

    def dSServerStart(event):
        """Start the dScriptServer instance"""
        _LOGGER.debug("dSServerStart: Start the dScriptServer")
        hass.data[DATA_SERVER].StartServer()

    def dSServerStop(event):
        """Stop the running dScriptServer instance"""
        _LOGGER.debug("dSServerStop: Stop the dScriptServer")
        hass.data[DATA_SERVER].StopServer()

    def dSBoardPlatformSetup():
        """Setup different platforms supported by dScriptModule"""
        for domain in SUPPORTED_DOMAINS:
            _LOGGER.debug("Discover platform: %s - %s",DOMAIN, domain)
            discovery.load_platform(hass, domain, DOMAIN, {}, config)
    
    def dSBoardGetConfig(sender, event):
        """Handles incomig getconfig connection of any board"""
        #_LOGGER.debug("dSBoardGetConfig: handle event")
        dSBoard = getdSBoardByIP(sender.sender)
        if not dSBoard:
            _LOGGER.warning("dSBoardGetConfig: Received trigger from uninitialized board: %s",sender.sender.IP)
            return False
        _LOGGER.debug("dSBoardGetConfig: Check if board config was updated: %s", dSBoard._HostName)
        oLights=dSBoard._ConnectedLights
        oShutters=dSBoard._ConnectedShutters
        oSwitches=dSBoard._ConnectedSockets
        oMotionSensors=dSBoard._ConnectedMotionSensors
        oButtons=dSBoard._ConnectedButtons
        dSBoard.GetConfig()
        if not oLights == dSBoard._ConnectedLights:
            discovery.load_platform(hass, 'light', DOMAIN, {}, config)
        if not oShutters == dSBoard._ConnectedShutters:
            discovery.load_platform(hass, 'cover', DOMAIN, {}, config)
        if not oSwitches == dSBoard._ConnectedSockets:
            discovery.load_platform(hass, 'switch', DOMAIN, {}, config)
        if not oMotionSensors == dSBoard._ConnectedMotionSensors or not oButtons == dSBoard._ConnectedButtons:
            discovery.load_platform(hass, 'sensor', DOMAIN, {}, config)

    def dSBoardHeartbeat(sender, event):
        """Handle incoming hearbeat connection of any board"""
        #_LOGGER.debug("dSBoardHeartbeat: handle event")
        dSBoard = getdSBoardByIP(sender.sender)
        if not dSBoard:
            dSBoardSetup(sender.sender, hass.data[DATA_SERVER].Port, hass.data[DATA_SERVER]._Protocol, hass.data[DATA_SERVER]._AESKey)
            dSBoardPlatformSetup()
        else:
            _LOGGER.debug("dSBoardHearbeat: HeartBeat of known board: %s", dSBoard._HostName)
            if dSBoard._CustomFirmeware:
                dSBoardGetConfig(sender, event)        

    def dSBoardDeviceUpdate(sender, event):
        """Perform the update action for specified device if device trigger was received"""
        #_LOGGER.debug("dSBoardDeviceUpdate: handle event")
        dSDevice=getdSDeviceByID(hass, sender.sender, sender.identifier, sender.topic)
        if dSDevice:
            _LOGGER.debug("dSBoardDeviceUpdate: Push device update: %s -> %s", dSDevice.entity_id, sender.value)
            dSDevice.update_push() # check if in future we can get data directly from "sender.value" and give that to update_push(sender.value)

    def handle_dSServerRestart(call):
        """Handle service call for dSServer restart"""
        _LOGGER.debug("handle_dSServerRestart: init restart")
        dSServerStop(call)
        dSServerStart(call)
	
    # Setup all dScript devices defined within configuration.yaml
    _LOGGER.info("Setup %s devices", DOMAIN)
    hass.data[DATA_BOARDS] = []
    hass.data[DATA_DEVICES] = []
    configured_devices = config[DOMAIN].get(CONF_DEVICES)
    if configured_devices:
        for device in configured_devices:
            dSBoardSetup(device.get(CONF_HOST), device.get(CONF_PORT), device.get(CONF_PROTOCOL), device.get(CONF_AESKEY))

    # Setup the dScriptServer which handles incoming connections if defined within configuration.yaml
    dSSrvConf=config[DOMAIN][CONF_SERVER]
    if not dSSrvConf == None and  dSSrvConf.get(CONF_ENABLED):
        _LOGGER.info("Setup %s server", DOMAIN)
        try:
            hass.data[DATA_SERVER] = dScriptServer(dSSrvConf.get(CONF_LISTENIP),dSSrvConf.get(CONF_PORT),dSSrvConf.get(CONF_PROTOCOL))
            
            _LOGGER.debug("Register dScriptServer event handlers")
            if len(dSSrvConf.get(CONF_AESKEY)) > 0:
                hass.data[DATA_SERVER].SetAESKey(dSSrvConf.get(CONF_AESKEY))
            hass.data[DATA_SERVER].addEventHandler('heartbeat',dSBoardHeartbeat)
            hass.data[DATA_SERVER].addEventHandler('getconfig',dSBoardGetConfig)
            hass.data[DATA_SERVER].addEventHandler('getlight',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getsocket',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getshutter',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getmotion',dSBoardDeviceUpdate)
            hass.data[DATA_SERVER].addEventHandler('getbutton',dSBoardDeviceUpdate)

            # Register service to restart dScriptServer
            _LOGGER.debug("Register services for dScriptServer")
            hass.services.register(DOMAIN, "dSServerRestart", handle_dSServerRestart)
			
            # register server on home assistant start & stop events so it is available when HA starts
            _LOGGER.debug("Register dScriptServer to start/stop with home assistant")
            hass.bus.listen_once(EVENT_HOMEASSISTANT_START, dSServerStart)
            hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, dSServerStop)
        except:
            _LOGGER.warning("Error while setting up dScriptServer!")
            hass.data[DATA_SERVER]=None

    #Setup all platform devices supported by dScriptModule
    dSBoardPlatformSetup()

    # Return boolean to indicate that initialization was successful.
    _LOGGER.debug("The '%s' component is ready!", DOMAIN)
    return True

