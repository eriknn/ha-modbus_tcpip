import logging

from homeassistant.components.button import ButtonEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity

from .devices.datatypes import ModbusGroup, ModbusDefaultGroups, ModbusDatapoint, ModbusButtonData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup button from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        if group != ModbusDefaultGroups.CONFIG:
            for key, datapoint in datapoints.items():
                if isinstance(datapoint.DataType, ModbusButtonData):
                    ha_entities.append(ModbusButtonEntity(coordinator, group, key, datapoint))

    async_add_devices(ha_entities, True)

class ModbusButtonEntity(ModbusBaseEntity, ButtonEntity):
    """Representation of a Button."""

    def __init__(self, coordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Initialize ModbusBaseEntity."""
        super().__init__(coordinator, group, key, modbusDataPoint)

        """Button Entity properties"""
        self._attr_device_class = modbusDataPoint.DataType.deviceClass

    async def async_press(self) -> None:
        """ Write value to device """
        try:
            await self.coordinator.write_value(self._group, self._key, 1)
        except Exception as err:
            _LOGGER.debug("Error writing command: %s %s", self._group, self._key)         
        finally:
            self.async_schedule_update_ha_state(force_refresh=False)
