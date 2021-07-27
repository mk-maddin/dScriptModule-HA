"""Support for dScriptModule sensor devices."""
import logging
import urllib.request
from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import DEVICE_CLASS_MOTION
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
    ATTR_MODEL,
    ATTR_VOLTAGE,
    ATTR_TEMPERATURE,
    ATTR_DEVICE_ID,
    ATTR_SW_VERSION,
)
from . import (
        DOMAIN,
        DATA_BOARDS, 
        DATA_DEVICES, 
        DATA_SERVER,
        getdSDeviceByID,
        CATTR_FW_VERSION,
        CATTR_SW_TYPE,
        CATTR_IP_ADDRESS,
)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the dScriptModule switch platform."""
    domain='sensor'
    devices=[]
    for dSBoard in hass.data[DATA_BOARDS]:
        
        try:
            _LOGGER.debug("%s: Create status %s for board", dSBoard.friendlyname, domain)
            device=dScriptBoardSensor(dSBoard,0)
            exists = False
            for entry in hass.data[DATA_DEVICES]:
                if entry._name == device._name:
                    exists = True
                    _LOGGER.debug("%s: A device with the equal name / entity_id alreay exists: %s", dSBoard.friendlyname, device._name)
                    break
            if not exists:
                hass.data[DATA_DEVICES].append(device)
                devices.append(device)
        except Exception as e:
            _LOGGER.error("%s: Creation of status %s failed: %s", dSBoard.friendlyname, domain, str(e)) 

        if not dSBoard._CustomFirmeware:
            continue    # If the board does not run custom firmeware we cannot identify a motion sensor.
        
        i=0
        _LOGGER.debug("%s: Create %s motion %s for board", dSBoard.friendlyname, dSBoard._ConnectedMotionSensors, domain)
        while i < dSBoard._ConnectedMotionSensors:
            try:
                i += 1
                if getdSDeviceByID(hass, dSBoard.IP, i, 'getmotion'):
                    continue # If the device already exists do not recreate
                device=dScriptMotionSensor(dSBoard,i)
                exists = False
                for entry in hass.data[DATA_DEVICES]:
                    if entry._name == device._name:
                        exists = True
                        _LOGGER.debug("%s: A device with the equal name / entity_id alreay exists: %s", dSBoard.friendlyname, device._name)
                        break
                if not exists:
                    hass.data[DATA_DEVICES].append(device)
                    devices.append(device)
            except Exception as e:
                _LOGGER.error("%s: Creation of motion %s %s failed: %s", dSBoard.friendlyname, domain, i, str(e))

        i=0
        _LOGGER.debug("%s: Setup %s button %s for board", dSBoard.friendlyname, dSBoard._ConnectedButtons, domain)
        while i < dSBoard._ConnectedButtons:
            try:
                i += 1
                if getdSDeviceByID(hass, dSBoard.IP, i, 'getbutton'):
                    continue # If the device already exists do not recreate
                device=dScriptButtonSensor(dSBoard,i)
                exists = False
                for entry in hass.data[DATA_DEVICES]:
                    if entry._name == device._name:
                        exists = True
                        _LOGGER.debug("%s: A device with the equal name / entity_id alreay exists: %s", dSBoard.friendlyname, device._name)
                        break
                if not exists:
                    hass.data[DATA_DEVICES].append(device)
                    devices.append(device)
            except Exception as e:
                _LOGGER.error("%s: Creation of button %s %s failed: %s", dSBoard.friendlyname, domain, i, str(e))   
   
    _LOGGER.info("%s: Prepared setup for %s %s devices", DOMAIN, len(devices), domain)
    add_entities(devices)


class dScriptMotionSensor(Entity):
    """The sensor class for dScriptModule motion sensors."""
    _topic = 'getmotion'

    def __init__(self, board, identifier):
        """Initialize the sensor."""
        self._identifier = identifier
        self._board = board
        self._state = None
        self._device_class = DEVICE_CLASS_MOTION
        self._icon = 'mdi:motion-sensor'
        self._name = self._board.friendlyname + "_Motion" + str(self._identifier)
        _LOGGER.debug("%s: Initialized sensor: %s", self._board.friendlyname, self._name)
        self.update_pull()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def available(self):
        """Return True if entity is available."""
        if self._board._ConnectedMotionSensors < self._identifier:
            return False
        return True

    @property
    def icon(self):
        return self._icon

    @property
    def device_class(self):
        """Return the device_class of the device."""
        return self._device_class

    @property
    def is_on(self):
        """Return true if entity is on."""
        _LOGGER.debug("%s: is_on: %s", self._board.friendlyname, self._name)
        return self._state

    @property
    def state(self):
        return self._state

    def _update_state(self,state):
        """Sets the object status according to the state result"""
        if state == 'on':
            self._state = STATE_ON
        elif state == 'off':
            self._state = STATE_OFF
        else:
            _LOGGER.warning("%s: invalid state update: %s is %s", self._board.friendlyname, self._name, state)

    def update_pull(self):
        """Pull the latest status from device"""
        try:
            _LOGGER.debug("%s: update pull %s", self._board.friendlyname, self._name)
            state=self._board.GetMotion(self._identifier)
            self._update_state(state)
            _LOGGER.debug("%s: update pull complete %s", self._board.friendlyname, self.entity_id)
        except Exception as e:
            _LOGGER.warning("%s: update pull failed %s: %s (%s.%s)", self._board.friendlyname, self.entity_id, str(e), e.__class__.__module__, type(e).__name__)

    def update_push(self):
        """Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s: update push %s", self._board.friendlyname, self._name)
            stateObject=self.hass.states.get(self.entity_id)
            attributesObject=stateObject.attributes.copy()
            state=self._board.GetMotion(self._identifier)
            self._update_state(state)
            self.hass.states.set(self.entity_id,state,attributesObject)
            _LOGGER.debug("%s: update push complete %s", self._board.friendlyname, self.entity_id)
        except Exception as e:
            _LOGGER.warning("%s: update push failed %s: %s (%s.%s)", self._board.friendlyname, self.entity_id, str(e), e.__class__.__module__, type(e).__name__)

    def update(self): #This function is automatically triggered for local_pull integrations
        """Get latest data and states from the device."""
        _LOGGER.debug("%s: update %s", self._board.friendlyname, self._name)
        if self._board._CustomFirmeware and self.hass.data[DATA_SERVER]:
            # If the board has a custom firmware and a server component is defined, update it via local_push, not local_pull
            return
        self.update_pull()


class dScriptButtonSensor(Entity):
    """The sensor class for dScriptModule button clicks."""
    _topic = 'getbutton'

    def __init__(self, board, identifier):
        """Initialize the sensor."""
        self._identifier = identifier
        self._board = board
        self._state = None
        self._device_class = None
        self._icon = 'mdi:light-switch'
        self._name = self._board.friendlyname + "_Button" + str(self._identifier)
        _LOGGER.debug("%s: Initialized sensor: %s", self._board.friendlyname, self._name)
        self.update_pull()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def available(self):
        """Return True if entity is available."""
        if self._board._ConnectedButtons < self._identifier:
            return False
        return True

    @property
    def icon(self):
        return self._icon

    @property
    def device_class(self):
        """Return the device_class of the device."""
        return self._device_class

    @property
    def state(self):
        return self._state

#    def update_manual(self,value):
#        """Manually set the objects status"""
#        try:
#            _LOGGER.debug("%s: update manual: %s", self._board.friendlyname, self._name)
#            if not isinstance(value, int):
#                _LOGGER.error("%s: update manual failed %s: parameter value %s is not int", self._board.friendlyname, self._name, value)
#                return False
#            self._update_state(value)
#        except Exception as e:
#            _LOGGER.warning("%s: update manual failed %s: %s (%s.%s)", self._board.friendlyname, self.entity_id, str(e), e.__class__.__module__, type(e).__name__)

    def _update_state(self,state):
        """Sets the object status according to the state result"""
        self._state = state

    def update_pull(self):
        """Pull the latest status from device"""
        try:
            _LOGGER.debug("%s: update pull %s", self._board.friendlyname, self._name)
            state=self._board.GetButton(self._identifier)
            self._update_state(state)
            _LOGGER.debug("%s: update pull complete %s", self._board.friendlyname, self.entity_id)
        except Exception as e:
            _LOGGER.warning("%s: update pull failed %s: %s (%s.%s)", self._board.friendlyname, self.entity_id, str(e), e.__class__.__module__, type(e).__name__)

    def update_push(self):
        """Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s: update push %s", self._board.friendlyname, self._name)
            stateObject=self.hass.states.get(self.entity_id)
            attributesObject=stateObject.attributes.copy()
            state=self._board.GetButton(self._identifier)
            self._update_state(state)
            self.hass.states.set(self.entity_id,state,attributesObject)
            _LOGGER.debug("%s: update push complete %s", self._board.friendlyname, self.entity_id)
        except Exception as e:
            _LOGGER.warning("%s: update push failed %s: %s (%s.%s)", self._board.friendlyname, self.entity_id, str(e), e.__class__.__module__, type(e).__name__)

    def update(self): #This function is automatically triggered for local_pull integrations
        """Get latest data and states from the device."""
        _LOGGER.debug("%s: update %s", self._board.friendlyname, self._name)
        if self._board._CustomFirmeware and self.hass.data[DATA_SERVER]:
            # If the board has a custom firmware and a server component is defined, update it via local_push, not local_pull
            return
        self.update_pull()


class dScriptBoardSensor(Entity):
    """The sensor class for dScriptModule button clicks."""
    _topic = 'getstatus'

    def __init__(self, board, identifier):
        """Initialize the sensor."""
        self._identifier = identifier
        self._board = board
        self._state = None
        self._device_class = None
        self._icon = 'mdi:developer-board'
        self._name = self._board.friendlyname + "_State"
        self._firmware = str(self._board._SystemFirmwareMajor) + "." + str(self._board._SystemFirmwareMinor)
        self._software = str(self._board._ApplicationFirmwareMajor) + "." + str(self._board._ApplicationFirmwareMinor)
        self._onlineurl= "http://" + self._board.IP + "/index.htm"
        self._configurl= "http://" + self._board.IP + "/_config.htm"
        _LOGGER.debug("%s: Initialized sensor: %s", self._board.friendlyname, self._name)
        self.update_pull()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def available(self):
        """Return True if entity is available."""
        if self._board._ConnectedButtons < self._identifier:
            return False
        return True

    @property
    def icon(self):
        return self._icon

    @property
    def device_class(self):
        """Return the device_class of the device."""
        return self._device_class

    @property
    def state(self):
        return self._state

    def _update_state(self,state):
        """Sets the object status according to the state result"""
        self._state = state

    def update_pull(self):
        """Pull the latest status from device"""
        try:
            _LOGGER.debug("%s: update pull %s", self._board.friendlyname, self._name)
            state = urllib.request.urlopen(self._onlineurl).getcode()
            self._board.GetStatus() 
        except urllib.error.URLError:
            state = 404
        except socket.timeout:
            state = 408
        except urllib.error.HTTPError as e:
            state = e.code
        except Exception as e:
            _LOGGER.warning("%s: update pull failed %s: %s (%s.%s)", self._board.friendlyname, self.entity_id, str(e), e.__class__.__module__, type(e).__name__)
        self._update_state(state)
        _LOGGER.debug("%s: update pull complete %s", self._board.friendlyname, self.entity_id)

    def update_push(self):
        """Get the latest status from device after an update was pushed"""
        try:
            _LOGGER.debug("%s: update push %s", self._board.friendlyname, self._name)
            stateObject=self.hass.states.get(self.entity_id)
            attributesObject=stateObject.attributes.copy()
            state = urllib.request.urlopen(self._onlineurl).getcode()
            self._board.GetStatus()
        except urllib.error.URLError:
            state = 404
        except socket.timeout:
            state = 408
        except urllib.error.HTTPError as e:
            state = e.code
        except Exception as e:
            _LOGGER.warning("%s: update push failed %s: %s (%s.%s)", self._board.friendlyname, self.entity_id, str(e), e.__class__.__module__, type(e).__name__)
        self._update_state(state)
        self.hass.states.set(self.entity_id,state,attributesObject)
        _LOGGER.debug("%s: update push complete %s", self._board.friendlyname, self.entity_id)


    def update(self): #This function is automatically triggered for local_pull integrations
        """Get latest data and states from the device."""
        _LOGGER.debug("%s: update %s", self._board.friendlyname, self._name)
        #default for this sensor is pull by home assistant as usually no push for availability happens
        self.update_pull()

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            ATTR_MODEL: self._board._ModuleID,
            ATTR_VOLTAGE: self._board._Volts,
            ATTR_TEMPERATURE: self._board._Temperature,
            ATTR_DEVICE_ID: self._board._MACAddress,
            ATTR_SW_VERSION: self._software,
            CATTR_FW_VERSION: self._firmware,
            CATTR_IP_ADDRESS: self._board.IP,
            CATTR_SW_TYPE: self._board._CustomFirmeware,
        }

