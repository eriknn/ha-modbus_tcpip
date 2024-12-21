import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity

from .devices.datatypes import ModbusGroup, ModbusDefaultGroups, ModbusDatapoint, ModbusBinarySensorData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup sensor from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        if group != ModbusDefaultGroups.CONFIG:
            for key, datapoint in datapoints.items():
                if isinstance(datapoint.DataType, ModbusBinarySensorData):
                    ha_entities.append(ModbusBinarySensorEntity(coordinator, group, key, datapoint))

    async_add_entities(ha_entities, False)

class ModbusBinarySensorEntity(ModbusBaseEntity, BinarySensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Initialize ModbusBaseEntity."""
        super().__init__(coordinator, group, key, modbusDataPoint)

        """Sensor Entity properties"""
        self._attr_device_class = modbusDataPoint.DataType.deviceClass

    @property
    def is_on(self):
        """Return the state of the switch."""
        value = self.coordinator.get_value(self._group, self._key)
        return value is not None and value >= 1
