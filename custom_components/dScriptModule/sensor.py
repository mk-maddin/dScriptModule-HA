"""Support for abfallio sensor devices."""
import logging
from datetime import datetime
from homeassistant.helpers.entity import Entity
from homeassistant.components.binary_sensor import DEVICE_CLASS_MOTION
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
)
from . import (
        DATA_BOARDS, 
        DATA_DEVICES, 
        DATA_SERVER,
        getdSDeviceByID,
)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the dScriptModule switch platform."""
    domain='sensor'
    devices=[]
    for dSBoard in hass.data[DATA_BOARDS]:
        if not dSBoard._CustomFirmeware:
            continue    # If the board does not run custom firmeware we cannot identify a motion sensor.
        i=0
        _LOGGER.debug("%s: Setup %s %s for board", dSBoard._HostName, dSBoard._ConnectedMotionSensors, domain)
        while i < dSBoard._ConnectedMotionSensors:
            i += 1
            if getdSDeviceByID(hass, dSBoard.IP, i, 'getmotion'):
                continue # If the device already exists do not recreate
            device=dScriptMotionSensor(dSBoard,i)
            hass.data[DATA_DEVICES].append(device)
            devices.append(device)
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
        #self._icon = 'mdi:motion-sensor'
        self._name = self._board._HostName + "_Motion" + str(self._identifier)
        _LOGGER.debug("%s: Initialized sensor: %s", self._board._HostName, self._name)
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

#    @property
#    def icon(self):
#        return self._icon

    @property
    def device_class(self):
        """Return the device_class of the device."""
        return self._device_class

    @property
    def is_on(self):
        """Return true if entity is on."""
        _LOGGER.debug("%s: is_on: %s", self._board._HostName, self._name)
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
            _LOGGER.warning("%s: invalid state update: %s is %s", self._board._HostName, self._name, state)

    def update_pull(self):
        """Pull the latest status from device"""
        _LOGGER.debug("%s: update pull %s", self._board._HostName, self._name)
        state=self._board.GetMotion(self._identifier)
        self._update_state(state)
        _LOGGER.debug("%s: update pull complete %s", self._board._HostName, self._name)

    def update_push(self):
        """Get the latest status from device after an update was pushed"""
        _LOGGER.debug("%s: update push %s", self._board._HostName, self._name)
        stateObject=self.hass.states.get(self.entity_id)
        attributesObject=stateObject.attributes.copy()
        state=self._board.GetMotion(self._identifier)
        self._update_state(state)
        self.hass.states.set(self.entity_id,state,attributesObject)
        _LOGGER.debug("%s: update push complete %s", self._board._HostName, self.entity_id)

    def update(self): #This function is automatically triggered for local_pull integrations
        """Get latest data and states from the device."""
        _LOGGER.debug("%s: update %s", self._board._HostName, self._name)
        if self._board._CustomFirmeware and self.hass.data[DATA_SERVER]:
            # If the board has a custom firmware and a server component is defined, update it via local_push, not local_pull
            return
        self.update_pull()
