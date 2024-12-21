import logging

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity

from .devices.datatypes import ModbusGroup, ModbusDefaultGroups, ModbusDatapoint, ModbusSwitchData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup switch from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        if group != ModbusDefaultGroups.CONFIG:
            for key, datapoint in datapoints.items():
                if isinstance(datapoint.DataType, ModbusSwitchData):
                    ha_entities.append(ModbusSwitchEntity(coordinator, group, key, datapoint))
                
    async_add_entities(ha_entities, False)

class ModbusSwitchEntity(ModbusBaseEntity, SwitchEntity):
    """Representation of a Switch."""

    def __init__(self, coordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Initialize ModbusBaseEntity."""
        super().__init__(coordinator, group, key, modbusDataPoint)

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
