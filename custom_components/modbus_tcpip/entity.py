"""Base entity class for Modbus TCP/IP integration."""
import logging

from collections import namedtuple
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .devices.datatypes import ModbusGroup, ModbusDatapoint

_LOGGER = logging.getLogger(__name__)

class ModbusBaseEntity(CoordinatorEntity):
    """Modbus base entity class."""

    def __init__(self, coordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        """Generic Entity properties"""
        self._attr_entity_category = modbusDataPoint.DataType.category
        self._attr_icon = modbusDataPoint.DataType.icon
        self._attr_name = "{} {}".format(self.coordinator.devicename, key)
        self._attr_unique_id = "{}-{}".format(self.coordinator.device_id, self.name)
        self._attr_device_info = {
            "identifiers": self.coordinator.identifiers,
        }
        self._extra_state_attributes = {}
        
        """Store this entities keys."""
        self._group = group
        self._key = key

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        attrs = {}

        new_attrs = self.coordinator.get_attrs(self._group, self._key)
        if new_attrs is not None:
            attrs.update(new_attrs)
        return attrs