import logging

from homeassistant.components.number import NumberEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity, ModbusEntity

from .devices.datatypes import ModbusNumberData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        for name, datapoint in datapoints.items():
            if isinstance(datapoint.DataType, ModbusNumberData):
                entity = ModbusEntity(group, name, datapoint.DataType)
                ha_entities.append(ModbusNumberEntity(coordinator, entity))

    async_add_devices(ha_entities, True)

class ModbusNumberEntity(ModbusBaseEntity, NumberEntity):
    """Representation of a Number."""

    def __init__(self, coordinator, modbusentity):
        """Pass coordinator to ModbusEntity."""
        super().__init__(coordinator, modbusentity)

        """Number Entity properties"""
        self._attr_device_class = modbusentity.data_type.deviceClass
        self._attr_mode = "box"
        self._attr_native_min_value = modbusentity.data_type.min_value
        self._attr_native_max_value = modbusentity.data_type.max_value
        self._attr_native_step = modbusentity.data_type.step
        self._attr_native_unit_of_measurement = modbusentity.data_type.units

        """Callback for updated value"""
        coordinator.registerOnUpdateCallback(self._key, self.update_callback)

    async def update_callback(self, newKey):
        self._key = newKey
        self.async_schedule_update_ha_state(force_refresh=False)

    @property
    def native_value(self) -> float | None:
        """Return number value."""
        val = self.coordinator.get_value(self._group, self._key)
        return val

    async def async_set_native_value(self, value):
        """ Write value to device """
        try:
            await self.coordinator.write_value(self._group, self._key, value)
        except Exception as err:
            _LOGGER.debug("Error writing command: %s %s", self._group, self._key)
        finally:
            self.async_schedule_update_ha_state(force_refresh=False)
            
