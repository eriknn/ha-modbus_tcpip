"""Config flow to configure Modbus TCP/IP integration"""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from typing import Any

from .const import DOMAIN, CONF_NAME, CONF_DEVICE_MODEL, CONF_IP, CONF_PORT, CONF_SLAVE_ID, CONF_SCAN_INTERVAL, CONF_SCAN_INTERVAL_FAST
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_FAST

from .devices.helpers import get_available_drivers

CONFIG_ENTRY_NAME = "Modbus TCP/IP"

DEVICE_DATA = {
    CONF_NAME: "",
    CONF_DEVICE_MODEL: None,
    CONF_IP: "192.168.10.13",
    CONF_PORT: 502,
    CONF_SLAVE_ID: 1,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL_FAST: DEFAULT_SCAN_INTERVAL_FAST
}

_LOGGER = logging.getLogger(__name__)


class ModbusFlowHandler(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return ModbusOptionsFlowHandler()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user, adding the integration."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        # Copy ip from existing integration, just for convenience
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        if existing_entries:
            last_entry = existing_entries[-1]
            DEVICE_DATA[CONF_DEVICE_MODEL]= last_entry.data[CONF_DEVICE_MODEL]
            DEVICE_DATA[CONF_IP]= last_entry.data[CONF_IP]
            DEVICE_DATA[CONF_PORT]= last_entry.data[CONF_PORT]

        return self.async_show_form(step_id="user", data_schema=await getDeviceSchema(DEVICE_DATA.copy()), errors=errors)

class ModbusOptionsFlowHandler(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        # Manage the options for the custom component."""

        if user_input is not None:
            # Update config_entry with new data
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )

            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=await getDeviceSchema(self.config_entry.data))

""" ################################################### """
"""                     Dynamic schemas                 """
""" ################################################### """
# Schema taking device details when adding or updating
async def getDeviceSchema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    DEVICE_MODELS = sorted(await get_available_drivers())

    data_schema = vol.Schema(
        {
            vol.Required(
                CONF_NAME, description="Name", default=user_input[CONF_NAME]
            ): cv.string,
            vol.Required(CONF_DEVICE_MODEL, default=user_input[CONF_DEVICE_MODEL]): selector.SelectSelector(
                selector.SelectSelectorConfig(options=DEVICE_MODELS),
            ),     
            vol.Required(
                CONF_IP, description="IP Address", default=user_input[CONF_IP]
            ): cv.string,
            vol.Optional(
                CONF_PORT, description="Port", default=user_input[CONF_PORT]
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
            vol.Optional(
                CONF_SLAVE_ID, description="Slave ID", default=user_input[CONF_SLAVE_ID]
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=256)),
            vol.Optional(
                CONF_SCAN_INTERVAL, default=user_input[CONF_SCAN_INTERVAL]
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=999)),
            vol.Optional(
                CONF_SCAN_INTERVAL_FAST, default=user_input[CONF_SCAN_INTERVAL_FAST]
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=999)),
        }
    )

    return data_schema
