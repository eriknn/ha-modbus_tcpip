import logging

from homeassistant.components.number import NumberEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity

from .devices.datatypes import ModbusGroup, ModbusDefaultGroups, ModbusDatapoint, ModbusNumberData

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
                if isinstance(datapoint.DataType, ModbusNumberData):
                    ha_entities.append(ModbusNumberEntity(coordinator, group, key, datapoint))

    async_add_entities(ha_entities, False)

class ModbusNumberEntity(ModbusBaseEntity, NumberEntity):
    """Representation of a Number."""

    def __init__(self, coordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Initialize ModbusBaseEntity."""
        super().__init__(coordinator, group, key, modbusDataPoint)

        """Number Entity properties"""
        self._attr_device_class = modbusDataPoint.DataType.deviceClass
        self._attr_mode = "box"
        self._attr_native_min_value = modbusDataPoint.DataType.min_value
        self._attr_native_max_value = modbusDataPoint.DataType.max_value
        self._attr_native_step = modbusDataPoint.DataType.step
        self._attr_native_unit_of_measurement = modbusDataPoint.DataType.units

        """Callback for updated value"""
        coordinator.registerOnUpdateCallback(self._key, self.update_callback)

    # Call back for special config number.
    async def update_callback(self, newGroup, newKey):
        newEntity:ModbusDatapoint = self.coordinator._modbusDevice.Datapoints[newGroup][newKey]

        if isinstance(newEntity.DataType, ModbusNumberData):
            self._attr_device_class = newEntity.DataType.deviceClass
            self._attr_native_min_value = newEntity.DataType.min_value
            self._attr_native_max_value = newEntity.DataType.max_value
            self._attr_native_step = newEntity.DataType.step
            self._attr_native_unit_of_measurement = newEntity.DataType.units
            _LOGGER.debug("Settings: %s %s %s %s: ", self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step, self._attr_native_unit_of_measurement)
        else:
            self._attr_device_class = None
            self._attr_native_min_value = 0
            self._attr_native_max_value = 65535
            self._attr_native_step = 1
            self._attr_native_unit_of_measurement = None
            _LOGGER.debug("Settings: Cleared!")

        self._group = newGroup
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
            
