from enum import Enum
from homeassistant.const import Platform

# Global Constants
DOMAIN: str = "modbus_tcpip"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH]

# Configuration Device Constants
CONF_NAME: str = "name"
CONF_DEVICE_MODE: str = "device_mode"
CONF_DEVICE_MODEL: str = "device_model"
CONF_SLAVE_ID: str = "slave_id"
CONF_SCAN_INTERVAL: str = "scan_interval"
CONF_SCAN_INTERVAL_FAST: str = "scan_interval_fast"

# Defaults
DEFAULT_SCAN_INTERVAL: int = 300  # Seconds
DEFAULT_SCAN_INTERVAL_FAST: int = 5  # Seconds

# Configuration mode selection
CONF_MODE_SELECTION = "mode_selection"
CONF_ADD_TCPIP = "add_tcpip"
CONF_ADD_RTU = "add_rtu"

# Configuration TCIP Constants
CONF_TCPIP: str = "tcpip"
CONF_IP: str = "ip_address"
CONF_PORT: str = "port"

# Configuration SERIAL Constants
CONF_SERIAL: str = "serial"
CONF_SERIAL_PORT: str = "serial_port"
CONF_SERIAL_BAUD: str = "serial_baud"

class DeviceMode(Enum):
    TCPIP = "tcpip"
    RTU = "rtu"