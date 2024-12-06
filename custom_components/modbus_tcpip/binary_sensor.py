import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity, ModbusEntity

from .devices.datatypes import ModbusBinarySensorData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        for name, datapoint in datapoints.items():
            if isinstance(datapoint.DataType, ModbusBinarySensorData):
                entity = ModbusEntity(group, name, datapoint.DataType)
                ha_entities.append(ModbusBinarySensorEntity(coordinator, entity))

    async_add_devices(ha_entities, True)

class ModbusBinarySensorEntity(ModbusBaseEntity, BinarySensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, modbusentity):
        super().__init__(coordinator, modbusentity)

        """Sensor Entity properties"""
        self._attr_device_class = modbusentity.data_type.deviceClass

    @property
    def extra_state_attributes(self):
        #Return entity specific state attributes.
        attrs = {}

        value = self.coordinator.get_value(self._group, self._key)
        if value > 0:
            newAttr = {"Value is:":value}
            attrs.update(newAttr) 
        return attrs

    @property
    def is_on(self):
        """Return the state of the switch."""
        value = self.coordinator.get_value(self._group, self._key)
        return value is not None and value >= 1
