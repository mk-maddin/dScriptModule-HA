"""Support for dScriptModule switch devices."""
import logging
import requests
from homeassistant.components.switch import SwitchEntity
from . import (
        DATA_BOARDS, 
        DATA_DEVICES, 
        DATA_SERVER,
        getdSDeviceByID,
)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the dScriptModule switch platform."""
    domain='switch'
    devices=[]
    for dSBoard in hass.data[DATA_BOARDS]:
        if dSBoard._CustomFirmeware: # If the board runs custom firmeware connect only switch devices as switch
            c=dSBoard._ConnectedSockets
        else: # If the board runs default firmware connect all relays as switch (always 32)
            c=dSBoard._VirtualRelays
        i=0
        _LOGGER.debug("%s: Setup %s %s for board", dSBoard._HostName, c, domain)
        while i < c:
            i += 1
            if getdSDeviceByID(hass, dSBoard.IP, i, 'getsocket'):
                continue # If the device already exists do not recreate
            device=dScriptSwitch(dSBoard,i)
            hass.data[DATA_DEVICES].append(device)
            devices.append(device)
    add_entities(devices)

class dScriptSwitch(SwitchEntity):
    """The switch class for dScriptModule switches."""
    _topic = 'getsocket'

    def __init__(self, board, identifier):
        """Initialize the switch."""
        self._identifier = identifier
        self._board = board
        self._state = None
        if self._board._CustomFirmeware:
           self._name = self._board._HostName + "_Socket" + str(self._identifier)
        else:
            self._name = self._board._HostName + "_Relay" + str(self._identifier)
        self.update_pull()
        _LOGGER.debug("%s: Initialized switch: %s", self._board._HostName, self._name)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def available(self):
        """Return True if entity is available."""
        if self. _board._CustomFirmeware:
            countSwitches=self._board._ConnectedSockets
        else:
            countSwitches=self._board._VirtualRelays
        if countSwitches < self._identifier:
            return False
        return True

    @property
    def icon(self):
        """Return the icon."""
        if self._board._CustomFirmeware:
            return 'mdi:power-socket-de'

    @property
    def is_on(self):
        """Return true if the switch is on."""
        #_LOGGER.debug("%s: is_on: %s", self._board._HostName, self._name)
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        _LOGGER.debug("%s: turn_on: %s", self._board._HostName, self._name)
        self._board.SetSocket(self._identifier,'on')

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        _LOGGER.debug("%s: turn_off: %s", self._board._HostName, self._name)
        self._board.SetSocket(self._identifier,'off')

    def _update_state(self,state):
        """Sets the object status according to the state result"""
        if state == 'on':
            self._state = True
        elif state == 'off':
            self._state = False
        else:
            _LOGGER.warning("%s: invalid state update: %s is %s", self._board._HostName, self._name, state)

    def update_pull(self):
        """Pull the latest status from device"""
        _LOGGER.debug("%s: update pull %s", self._board._HostName, self._name)
        state=self._board.GetSocket(self._identifier)
        self._update_state(state)
        _LOGGER.debug("%s: update pull complete %s", self._board._HostName, self._name)

    def update_push(self):
        """Get the latest status from device after an update was pushed"""
        _LOGGER.debug("%s: update push %s", self._board._HostName, self._name)
        stateObject=self.hass.states.get(self.entity_id)
        attributesObject=stateObject.attributes.copy()
        state=self._board.GetSocket(self._identifier)
        self._update_state(state)
        self.hass.states.set(self.entity_id,state,attributesObject)
        _LOGGER.debug("%s: update push complete %s", self._board._HostName, self.entity_id)

    def update(self): #This function is automatically triggered for local_pull integrations
        """Get latest data and states from the device."""
        #_LOGGER.debug("%s: update %s", self._board._HostName, self._name)
        if self._board._CustomFirmeware and self.hass.data[DATA_SERVER]:
            # If the board has a custom firmware and a server component is defined, update it via local_push, not local_pull
            return
        self.update_pull()

