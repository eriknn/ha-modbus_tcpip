"""Base entity class for Modbus TCP/IP integration."""
import logging

from collections import namedtuple
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = logging.getLogger(__name__)

ModbusEntity = namedtuple('ModbusEntity', ['group', 'key', 'data_type'])

class ModbusBaseEntity(CoordinatorEntity):
    """Modbus base entity class."""

    def __init__(self, coordinator, modbusentity):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

        """Generic Entity properties"""
        self._attr_entity_category = modbusentity.data_type.category
        self._attr_icon = modbusentity.data_type.icon
        self._attr_name = "{} {}".format(self.coordinator.devicename, modbusentity.key)
        self._attr_unique_id = "{}-{}".format(self.coordinator.device_id, self.name)
        self._attr_device_info = {
            "identifiers": self.coordinator.identifiers,
        }
        self._extra_state_attributes = {}
        
        """Store this entities key."""
        self._group = modbusentity.group
        self._key = modbusentity.key

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._extra_state_attributes        
