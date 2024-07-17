"""Constants for the dscriptmodule integration."""

from __future__ import annotations
from typing import Final

DOMAIN: Final = 'dscriptmodule'
MANUFACTURER: Final = "Devantech"
FUNC_OPTION_UPDATES: Final = 'options_update_listener'

CONF_SERVER: Final = 'server'
CONF_AESKEY: Final = 'aes_key'
CONF_LISTENIP: Final = 'listen_ip'
CONF_SERVER: Final = 'server'
CONF_PYOJBECT: Final = 'pyobj'
CONF_ADD_ENTITIES: Final = 'addentitiescallback'

KNOWN_DATA: Final = 'cache'
KNOWN_DATA_FILE: Final = '/config/.'+DOMAIN+'_'+KNOWN_DATA+'.json'

DEFAULT_NAME: Final = 'dScriptModule'
DEFAULT_PORT: Final = 17123
DEFAULT_PROTOCOL: Final = "binary"
DEFAULT_AESKEY: Final = ""
DEFAULT_LISTENIP: Final = "0.0.0.0"
AVAILABLE_PROTOCOLS: Final =  ['modbus','ascii','binary','binaryaes']

CATTR_FW_VERSION: Final =  "firmware"
CATTR_IP_ADDRESS: Final =  "ipaddress"
CATTR_PROTOCOL: Final =  "protocol"
CATTR_SW_TYPE: Final =  "custom_app"

STATE_STOPPED: Final = "stopped"

DSCRIPT_TOPICTOENTITYTYPE: Final = {
    "getlight": "light",
    "getsocket": "switch",
    "getshutter": "cover",
    "getmotion": "sensor_motion",
    "getbutton": "sensor_button",
    "getboard_dummy": "sensor_board"
}

DSCRIPT_ENTITYTYPETOCOUNTATTR: Final = {
    "light": "_ConnectedLights",
    "switch": "_ConnectedSockets",
    "switch_native": "_PhysicalRelays",
    "cover":  "_ConnectedShutters",
    "sensor_motion": "_ConnectedMotionSensors",
    "sensor_button": "_ConnectedButtons",
    "sensor_board": "_ConnectedBoardSensors"
}
