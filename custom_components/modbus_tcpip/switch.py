import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity, ModbusEntity

from .devices.datatypes import ModbusSwitchData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup switch from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        for name, datapoint in datapoints.items():
            if isinstance(datapoint.DataType, ModbusSwitchData):
                _LOGGER.debug("Adding switch: %s %s %s", group, name, datapoint.DataType)
                entity = ModbusEntity(group, name, datapoint.DataType)
                ha_entities.append(ModbusSwitchEntity(coordinator, entity))

    async_add_devices(ha_entities, True)

class ModbusSwitchEntity(ModbusBaseEntity, SwitchEntity):
    """Representation of a Switch."""

    def __init__(self, coordinator, modbusentity):
        super().__init__(coordinator, modbusentity)

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self.coordinator.get_value(self._group, self._key)

    async def async_turn_on(self, **kwargs):
        await self.writeValue(1)

    async def async_turn_off(self, **kwargs):
        await self.writeValue(0)

    async def writeValue(self, value):
        """ Write value to device """
        try:
            await self.coordinator.write_value(self._group, self._key, value)
        except Exception as err:
            _LOGGER.debug("Error writing command: %s %s", self._group, self._key)
        finally:
            self.async_schedule_update_ha_state(force_refresh=False)
