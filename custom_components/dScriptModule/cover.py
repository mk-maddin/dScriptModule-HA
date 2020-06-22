"""Support for dScriptModule cover devices."""
import logging
import requests
from homeassistant.components.cover import (
        ATTR_POSITION, 
        ATTR_CURRENT_POSITION,
        CoverEntity,
)
from . import (
        DATA_BOARDS, 
        DATA_DEVICES, 
        DATA_SERVER,
        getdSDeviceByID,
)

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the dScriptModule cover platform."""
    domain='cover'
    devices=[]
    for dSBoard in hass.data[DATA_BOARDS]:
        if not dSBoard._CustomFirmeware:
            continue    # If the board does not run custom firmeware we cannot identify a 'cover' - treate all as switch
        i=0
        _LOGGER.debug("%s: Setup %s %s for board", dSBoard._HostName, dSBoard._ConnectedShutters, domain)
        while i < dSBoard._ConnectedShutters:
            i += 1
            if getdSDeviceByID(hass, dSBoard.IP, i, 'getshutter'):
                continue # If the device already exists do not recreate
            device=dScriptCover(dSBoard,i)
            hass.data[DATA_DEVICES].append(device)
            devices.append(device)
    add_entities(devices)

class dScriptCover(CoverEntity):
    """The cover class for dScriptModule covers."""
    _topic = 'getshutter'

    def __init__(self, board, identifier):
        """Initialize the cover."""
        self._identifier = identifier
        self._board = board
        self._name = self._board._HostName + "_Cover" + str(self._identifier)
        self._current_cover_position = None
        self._state = None
        _LOGGER.debug("%s: Initialized cover: %s", self._board._HostName, self._name)
        self.update_pull()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name
    
    @property
    def available(self):
        """Return True if entity is available."""
        if self._board._ConnectedShutters < self._identifier:
            return False
        return True
    
    @property
    def current_cover_position(self):
        """Return current position of cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._current_cover_position
    
    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        if self._state == 'opening':
            return True
        return False
    
    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        if self._state == 'closing':
            return True
        return False
    
    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        if self._current_cover_position == 0:
            return True
        return False
    
    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._board.SetShutter(self._identifier,'stop')
        self.update_push()
    
    def open_cover(self, **kwargs):
        """Open the cover."""
        self._board.SetShutter(self._identifier,'open')
        self.update_push()
    
    def close_cover(self, **kwargs):
        """Close cover."""
        self._board.SetShutter(self._identifier,'close')
        self.update_push()
    
    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs[ATTR_POSITION]
        self._board.SetShutter(self._identifier,position)
        self.update_push()
    
    def _update_state(self,state):
        """Sets the object status according to the state result"""
        self._current_cover_position = state[0]
        self._state = state[1]
    
    def update_pull(self):
        """Pull the latest status from device"""
        _LOGGER.debug("%s: update pull %s", self._board._HostName, self._name)
        state=self._board.GetShutter(self._identifier)
        self._update_state(state)
        _LOGGER.debug("%s: update pull complete %s", self._board._HostName, self._name)
    
    def update_push(self):
        """Get the latest status from device after an update was pushed"""
        _LOGGER.debug("%s: update push %s", self._board._HostName, self._name)
        stateObject=self.hass.states.get(self.entity_id)
        attributesObject=stateObject.attributes.copy()
        state=self._board.GetShutter(self._identifier)
        self._update_state(state)
        attributesObject[ATTR_CURRENT_POSITION] = state[0]
        self.hass.states.set(self.entity_id,state[1],attributesObject)
        _LOGGER.debug("%s: update push complete %s (%s | %s)", self._board._HostName, self.entity_id, state, attributesObject)
    
    def update(self): #This function is automatically triggered for local_pull integrations
        """Get latest data and states from the device."""
        _LOGGER.debug("%s: update %s", self._board._HostName, self._name)
        if self.is_opening or self.is_closing:
            self.update_pull() #If device is currently opening/closing keep status "more" up-to-date
            return
        if self._board._CustomFirmeware and self.hass.data[DATA_SERVER]:
            # If the board has a custom firmware and a server component is defined, update it via local_push, not local_pull
            return
        self.update_pull()
