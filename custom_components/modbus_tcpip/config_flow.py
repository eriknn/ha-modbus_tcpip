"""Config flow to configure Modbus TCP/IP integration"""
import asyncio
import glob
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from typing import Any

from .const import DOMAIN, CONF_DEVICE_MODE, CONF_NAME, CONF_DEVICE_MODEL, CONF_IP, CONF_PORT, CONF_SLAVE_ID, CONF_SCAN_INTERVAL, CONF_SCAN_INTERVAL_FAST
from .const import CONF_MODE_SELECTION, CONF_ADD_TCPIP, CONF_ADD_RTU
from .const import CONF_SERIAL_PORT, CONF_SERIAL_BAUD
from .const import DeviceMode
from .const import DEFAULT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_FAST

from .devices.helpers import get_available_drivers

CONFIG_ENTRY_NAME = "Modbus TCP/IP"

DEVICE_DATA_TCPIP = {
    CONF_DEVICE_MODE: DeviceMode.TCPIP,
    CONF_NAME: "",
    CONF_DEVICE_MODEL: None,
    CONF_IP: "192.168.1.1",
    CONF_PORT: 502,
    CONF_SLAVE_ID: 1,
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL_FAST: DEFAULT_SCAN_INTERVAL_FAST
}

DEVICE_DATA_RTU = {
    CONF_DEVICE_MODE: DeviceMode.RTU, 
    CONF_NAME: "", 
    CONF_DEVICE_MODEL: None,
    CONF_SERIAL_PORT: "",
    CONF_SERIAL_BAUD: 9600,
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
            if user_input.get(CONF_MODE_SELECTION) == CONF_ADD_TCPIP:
                self.selected_mode = DeviceMode.TCPIP
                return await self.async_step_add_tcpip()
            if user_input.get(CONF_MODE_SELECTION) == CONF_ADD_RTU:
                self.selected_mode = DeviceMode.RTU    
                return await self.async_step_add_rtu()           
                #errors["base"] = "mode_not_implemented"

        return self.async_show_form(step_id="user", data_schema=MODE_SCHEMA, errors=errors)
    
    async def async_step_add_tcpip(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user, adding the integration."""
        errors = {}

        if user_input is not None:
            user_input[CONF_DEVICE_MODE] = DeviceMode.TCPIP
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        # Copy ip from existing integration, just for convenience
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        filtered_entries = [entry for entry in existing_entries if entry.data.get(CONF_DEVICE_MODE) == DeviceMode.TCPIP]
        if filtered_entries:
            last_entry = filtered_entries[-1]
            DEVICE_DATA_TCPIP[CONF_DEVICE_MODEL] = last_entry.data[CONF_DEVICE_MODEL]
            DEVICE_DATA_TCPIP[CONF_IP] = last_entry.data[CONF_IP]
            DEVICE_DATA_TCPIP[CONF_PORT] = last_entry.data[CONF_PORT]

        return self.async_show_form(step_id="add_tcpip", data_schema=await getDeviceSchema(DEVICE_DATA_TCPIP.copy()), errors=errors)
    
    async def async_step_add_rtu(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user, adding the integration."""
        errors = {}
        ports = await async_get_ports()

        if user_input is not None:
            user_input[CONF_DEVICE_MODE] = DeviceMode.RTU
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        # Copy ip from existing integration, just for convenience
        existing_entries = self.hass.config_entries.async_entries(DOMAIN)
        filtered_entries = [entry for entry in existing_entries if entry.data.get(CONF_DEVICE_MODE) == DeviceMode.RTU]
        if filtered_entries:
            last_entry = filtered_entries[-1]
            DEVICE_DATA_RTU[CONF_DEVICE_MODEL] = last_entry.data[CONF_DEVICE_MODEL]
            DEVICE_DATA_RTU[CONF_SERIAL_PORT] = last_entry.data[CONF_SERIAL_PORT]
            DEVICE_DATA_RTU[CONF_SERIAL_BAUD] = last_entry.data[CONF_SERIAL_BAUD]

        return self.async_show_form(step_id="add_rtu", data_schema=await getDeviceSchema(DEVICE_DATA_RTU.copy(), ports), errors=errors)

class ModbusOptionsFlowHandler(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        # Manage the options for the custom component."""
        errors = {}
        ports = await async_get_ports()

        if user_input is not None:
            # Update config_entry with new data
            self.hass.config_entries.async_update_entry(
                self.config_entry, title=user_input[CONF_NAME], data=user_input, options=self.config_entry.options
            )

            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="init", data_schema=await getDeviceSchema(self.config_entry.data, ports), errors=errors)



""" ################################################### """
"""                     Static schemas                  """
""" ################################################### """
MODE_VALUES = [CONF_ADD_TCPIP, CONF_ADD_RTU]
MODE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MODE_SELECTION): selector.SelectSelector(
            selector.SelectSelectorConfig(options=MODE_VALUES, translation_key=CONF_MODE_SELECTION),
        )
    }
)

""" ################################################### """
"""                     Dynamic schemas                 """
""" ################################################### """
# Schema returning correct schema based on device mode
async def getDeviceSchema(user_input: dict[str, Any] | None = None, ports = None) -> vol.Schema:
    device_mode = user_input.get(CONF_DEVICE_MODE, DeviceMode.TCPIP)
    if device_mode == DeviceMode.TCPIP:
        return await getTcpIpDeviceSchema(user_input)
    elif device_mode == DeviceMode.RTU:
        return await getRtuDeviceSchema(user_input, ports)
    
    return None

# Schema taking device details when adding or updating tcp/ip device
async def getTcpIpDeviceSchema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    DEVICE_MODELS = sorted(await get_available_drivers())

    data_schema = vol.Schema(
        {
            vol.Required(CONF_NAME, description="Name", default=user_input[CONF_NAME]): cv.string,
            vol.Required(CONF_DEVICE_MODEL, default=user_input[CONF_DEVICE_MODEL]): selector.SelectSelector(selector.SelectSelectorConfig(options=DEVICE_MODELS)),     
            vol.Required(CONF_IP, description="IP Address", default=user_input[CONF_IP]): cv.string,
            vol.Optional(CONF_PORT, description="Port", default=user_input[CONF_PORT]): vol.All(vol.Coerce(int), vol.Range(min=0, max=65535)),
            vol.Optional(CONF_SLAVE_ID, description="Slave ID", default=user_input[CONF_SLAVE_ID]): vol.All(vol.Coerce(int), vol.Range(min=0, max=256)),
            vol.Optional(CONF_SCAN_INTERVAL, default=user_input[CONF_SCAN_INTERVAL]): vol.All(vol.Coerce(int), vol.Range(min=5, max=999)),
            vol.Optional(CONF_SCAN_INTERVAL_FAST, default=user_input[CONF_SCAN_INTERVAL_FAST]): vol.All(vol.Coerce(int), vol.Range(min=1, max=999)),
        }
    )

    return data_schema

# Schema taking device details when adding or updating RTU device
async def getRtuDeviceSchema(user_input: dict[str, Any] | None = None, ports = None) -> vol.Schema:
    DEVICE_MODELS = sorted(await get_available_drivers())
    baud_rates = [9600, 14400, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

    data_schema = vol.Schema(
        {
            vol.Required(CONF_NAME, description="Name", default=user_input[CONF_NAME]): cv.string,
            vol.Required(CONF_DEVICE_MODEL, default=user_input[CONF_DEVICE_MODEL]): selector.SelectSelector(selector.SelectSelectorConfig(options=DEVICE_MODELS)),     
            vol.Required(CONF_SERIAL_PORT, description="Serial Port", default=user_input[CONF_SERIAL_PORT]): vol.In(ports),
            vol.Required(CONF_SERIAL_BAUD, description="Baud Rate", default=user_input[CONF_SERIAL_BAUD]): vol.In(baud_rates),
            vol.Required(CONF_SLAVE_ID, description="Slave ID", default=user_input[CONF_SLAVE_ID]): vol.All(vol.Coerce(int), vol.Range(min=0, max=256)),
            vol.Optional(CONF_SCAN_INTERVAL, default=user_input[CONF_SCAN_INTERVAL]): vol.All(vol.Coerce(int), vol.Range(min=5, max=999)),
            vol.Optional(CONF_SCAN_INTERVAL_FAST, default=user_input[CONF_SCAN_INTERVAL_FAST]): vol.All(vol.Coerce(int), vol.Range(min=1, max=999)),
        }
    )

    return data_schema

""" ################################################### """
"""                         HELPERS                     """
""" ################################################### """
async def async_get_ports():
    # Run the blocking glob call in a separate thread to avoid blocking the event loop
    try:
        return await asyncio.to_thread(glob.glob, '/dev/serial/by-id/*')
    except Exception as e:
        _LOGGER.error("Error fetching serial ports: %s", e)
        return []