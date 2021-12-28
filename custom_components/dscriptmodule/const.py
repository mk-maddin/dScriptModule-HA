"""Constants for the dscriptmodule integration."""

from __future__ import annotations
from typing import Final

SUPPORTED_PLATFORMS: Final = ["light", "switch", "cover", "sensor"]
DOMAIN: Final = 'dscriptmodule'
NATIVE_ASYNC: Final = True
SERVER_NATIVE_ASYNC: Final = NATIVE_ASYNC
#SERVER_NATIVE_ASYNC: Final = False
MANUFACTURER: Final = "Devantech"

DSDOMAIN_LIGHT: Final = 'light'
DSDOMAIN_COVER: Final = 'cover'
DSDOMAIN_SWITCH: Final = 'switch'
DSDOMAIN_MOTION: Final = 'motion'
DSDOMAIN_BUTTON: Final = 'button'
DSDOMAIN_BOARD: Final = 'state'

CONF_ADDANOTHER: Final = 'add_another'
CONF_AESKEY: Final = 'aes_key'
CONF_BOARDS: Final = 'boards'
CONF_ENABLED: Final = 'enabled'
CONF_LISTENIP: Final = 'listen_ip'
CONF_SERVER: Final = 'server'

DEFAULT_PORT: Final = 17123
DEFAULT_PROTOCOL: Final = "binary"
DEFAULT_AESKEY: Final = ""
AVAILABLE_PROTOCOLS: Final =  ['modbus','ascii','binary','binaryaes']

DATA_BOARDS: Final = DOMAIN + "_boards"
DATA_CONFIG: Final = DOMAIN + "config"
DATA_ENTITIES: Final = DOMAIN + "_entities"
DATA_SERVER: Final = DOMAIN + "_server"
DATA_YAML: Final = DOMAIN + "_yaml"
DATA_PLATFORMS: Final = DOMAIN + '_platforms'

CATTR_FW_VERSION: Final =  "firmware"
CATTR_IP_ADDRESS: Final =  "ipaddress"
CATTR_PROTOCOL: Final =  "protocol"
CATTR_SW_TYPE: Final =  "custom_app"

STATE_STOPPED: Final = "stopped"
