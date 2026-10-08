"""Diagnostic sensors of a dScriptBoard: temperature, voltage and load (disabled by default)."""

from __future__ import annotations
from typing import Final
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory

from .entities import dScriptPlatformEntity
from .const import SIGNAL_BOARD_STATUS

_LOGGER: Final = logging.getLogger(__name__)
PLATFORM = 'sensor'


class dScriptBoardDiagnosticSensor(SensorEntity, dScriptPlatformEntity):
    """Base class: shows a value of the board object, updated when the board sensor signals new values."""

    _platform = PLATFORM
    _board_attr = None
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def should_poll(self) -> bool:
        """No polling - the board sensor reads the values and signals updates."""
        return False

    @property
    def native_value(self):
        """Return the current value of the board."""
        return getattr(self._board, self._board_attr, None)

    @property
    def available(self) -> bool:
        """Available while the board is reachable and provides the value."""
        return bool(self._board.available) and self.native_value is not None

    async def async_added_to_hass(self) -> None:
        """Subscribe to new board values."""
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_BOARD_STATUS.format(self._board.MACAddress), self._async_board_status_updated))

    @callback
    def _async_board_status_updated(self) -> None:
        """Write the new board values."""
        self.async_write_ha_state()

    async def async_local_poll(self) -> None:
        """Async: values are read by the board sensor - just write the current state"""
        self.async_write_ha_state()

    async def async_local_push(self, state=None) -> None:
        """Async: values are read by the board sensor - just write the current state"""
        self.async_write_ha_state()


class dScriptTemperatureSensor(dScriptBoardDiagnosticSensor):
    """Internal board temperature."""

    _board_attr = '_Temperature'
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS


class dScriptVoltageSensor(dScriptBoardDiagnosticSensor):
    """Supplied voltage of the board."""

    _board_attr = '_Volts'
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT


class dScriptLoadSensor(dScriptBoardDiagnosticSensor):
    """dScript instructions per second - maximum of the last minute (firmware >= 3.9)."""

    _board_attr = '_InstrPerSecMax'
    _icon = 'mdi:speedometer'
    _attr_native_unit_of_measurement = 'instr/s'

    @property
    def extra_state_attributes(self):
        """Value of the last second in addition to the maximum of the last minute."""
        return {'last_second': self._board._InstrPerSec}
