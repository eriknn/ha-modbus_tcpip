import logging

from homeassistant.components.select import SelectEntity

from .const import DOMAIN
from .coordinator import ModbusCoordinator
from .entity import ModbusBaseEntity

from .devices.datatypes import ModbusGroup, ModbusDefaultGroups, ModbusDatapoint, ModbusSelectData

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor from a config entry created in the integrations UI."""
    # Find coordinator for this device
    coordinator:ModbusCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    # Load entities
    ha_entities = []
    for group, datapoints in coordinator._modbusDevice.Datapoints.items():
        if group != ModbusDefaultGroups.CONFIG:
            for key, datapoint in datapoints.items():
                if isinstance(datapoint.DataType, ModbusSelectData):
                    ha_entities.append(ModbusSelectEntity(coordinator, group, key, datapoint))

    async_add_devices(ha_entities, True)

class ModbusSelectEntity(ModbusBaseEntity, SelectEntity):
    """Representation of a Select."""

    def __init__(self, coordinator, group:ModbusGroup, key:str, modbusDataPoint:ModbusDatapoint):
        """Initialize ModbusBaseEntity."""
        super().__init__(coordinator, group, key, modbusDataPoint)

        """Select Entity properties"""
        if self._key == "Config Selection":
            self._options = self.coordinator.get_config_options()
        else:
            self._options = modbusDataPoint.DataType.options

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
        _LOGGER.debug("Select: %s", self._key)
        try:
            if self._key == "Config Selection":
                _LOGGER.debug("Selecting")
                await self.coordinator.config_select(option, value)
            else:           
                _LOGGER.debug("Writing")
                await self.coordinator.write_value(self._group, self._key, value)
        except Exception as err:
            _LOGGER.debug("Error writing command: %s %s", self._group, self._key)
        finally:
            self.async_schedule_update_ha_state(force_refresh=False)
