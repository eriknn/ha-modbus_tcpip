import logging

from homeassistant.components.button import ButtonEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity, ModbusEntity

from .devices.datatypes import ModbusButtonData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup button from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        for name, datapoint in datapoints.items():
            if isinstance(datapoint.DataType, ModbusButtonData):
                entity = ModbusEntity(group, name, datapoint.DataType)
                ha_entities.append(ModbusButtonEntity(coordinator, entity))

    async_add_devices(ha_entities, True)

class ModbusButtonEntity(ModbusBaseEntity, ButtonEntity):
    """Representation of a Button."""

    def __init__(self, coordinator, modbusentity):
        super().__init__(coordinator, modbusentity)

        """Button Entity properties"""
        self._attr_device_class = modbusentity.data_type.deviceClass

    async def async_press(self) -> None:
        """ Write value to device """
        try:
            await self.coordinator.write_value(self._group, self._key, 1)
        except Exception as err:
            _LOGGER.debug("Error writing command: %s %s", self._group, self._key)         
        finally:
            self.async_schedule_update_ha_state(force_refresh=False)
