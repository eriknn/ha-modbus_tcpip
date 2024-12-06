import logging

from homeassistant.components.select import SelectEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity, ModbusEntity

from .devices.datatypes import ModbusSelectData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        for name, datapoint in datapoints.items():
            if isinstance(datapoint.DataType, ModbusSelectData):
                entity = ModbusEntity(group, name, datapoint.DataType)
                ha_entities.append(ModbusSelectEntity(coordinator, entity))

    async_add_devices(ha_entities, True)

class ModbusSelectEntity(ModbusBaseEntity, SelectEntity):
    """Representation of a Select."""

    def __init__(self, coordinator:ModbusCoordinator, modbusentity):
        """Pass coordinator to ModbusEntity."""
        super().__init__(coordinator, modbusentity)

        """Select Entity properties"""
        if self._key == "Config Selection":
            self._options = self.coordinator.get_config_options()
        else:
            self._options = modbusentity.data_type.options

    @property
    def current_option(self):
        try:
            if self._key == "Config Selection":
                optionIndex = self.coordinator.config_selection
                option = self._options[optionIndex]
            else:
                optionIndex = self.coordinator.get_value(self._group, self._key)
                option = self._options[optionIndex]
        except Exception as e:
            option = "Unknown"
        return option

    @property
    def options(self):
        return list(self._options.values())

    async def async_select_option(self, option):
        """ Find new value """
        value = None

        for key, val in self._options.items():
            if val == option:
                value = key
                break

        if value is None:
            return

        """ Write value to device """
        try:
            if self._key == "Config Selection":
                await self.coordinator.config_select(option, value)
            else:           
                await self.coordinator.write_value(self._group, self._key, value)
        except Exception as err:
            _LOGGER.debug("Error writing command: %s %s", self._group, self._key)
        finally:
            self.async_schedule_update_ha_state(force_refresh=False)
