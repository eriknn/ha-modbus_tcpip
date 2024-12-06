from homeassistant.const import Platform

# Global Constants
DOMAIN: str = "modbus_tcpip"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.NUMBER, Platform.SELECT, Platform.SENSOR]

# Configuration Device Constants
CONF_NAME: str = "name"
CONF_DEVICE_MODEL: str = "device_model"
CONF_IP: str = "ip_address"
CONF_PORT: str = "port"
CONF_SLAVE_ID: str = "slave_id"
CONF_SCAN_INTERVAL: str = "scan_interval"
CONF_SCAN_INTERVAL_FAST: str = "scan_interval_fast"

# Defaults
DEFAULT_SCAN_INTERVAL: int = 300  # Seconds
DEFAULT_SCAN_INTERVAL_FAST: int = 5  # Seconds