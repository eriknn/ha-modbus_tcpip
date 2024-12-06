import logging

from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity, ModbusEntity

from .devices.datatypes import ModbusSensorData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        for name, datapoint in datapoints.items():
            if isinstance(datapoint.DataType, ModbusSensorData):
                entity = ModbusEntity(group, name, datapoint.DataType)
                ha_entities.append(ModbusSensorEntity(coordinator, entity))

    async_add_devices(ha_entities, True)


class ModbusSensorEntity(ModbusBaseEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, modbusentity):
        super().__init__(coordinator, modbusentity)

        """Sensor Entity properties"""
        self._attr_device_class = modbusentity.data_type.deviceClass
        self._attr_native_unit_of_measurement = modbusentity.data_type.units

    @property
    def native_value(self):
        """Return the value of the sensor."""
        val = self.coordinator.get_value(self._group, self._key)
        return val
