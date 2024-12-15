"""Support for Modbus TCP/IP devices."""
import logging

from functools import partial
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from homeassistant.const import CONF_DEVICES
from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_NAME,
    CONF_DEVICE_MODEL,
    CONF_IP,
    CONF_PORT,
    CONF_SLAVE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL_FAST
)
from .coordinator import ModbusCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Set up platform from a ConfigEntry."""
    _LOGGER.debug("Setting up configuration for Modbus TCP/IP!")
    hass.data.setdefault(DOMAIN, {})

    # Load config data
    name = entry.data[CONF_NAME]
    device_model = entry.data.get(CONF_DEVICE_MODEL, None)
    ip = entry.data[CONF_IP]
    port = entry.data[CONF_PORT]
    slave_id = entry.data[CONF_SLAVE_ID]
    scan_interval = entry.data[CONF_SCAN_INTERVAL]
    scan_interval_fast = entry.data[CONF_SCAN_INTERVAL_FAST]

    # Create device
    # Each config entry will have only one device, so we use the entry_id as a
    # unique identifier for the device. This allows us to modify all device parameters without
    # having to modify the identifier.
    device_registry = dr.async_get(hass)
    dev = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=name
    )

    # Set up coordinator
    coordinator = ModbusCoordinator(hass, dev, device_model, ip, port, slave_id,scan_interval, scan_interval_fast)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Might throw ConfigEntryNotReady, that should cause retry later
    await coordinator.async_config_entry_first_refresh()

    # Forward the setup to the platforms.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    # Set up options listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # Register services
    hass.services.async_register(DOMAIN, "request_update",partial(service_request_update, hass))
    
    return True

# Service-call to update values
async def service_request_update(hass, call: ServiceCall):
    """Handle the service call to update entities for a specific device."""
    device_id = call.data.get("device_id")
    if not device_id:
        _LOGGER.error("Device ID is required")
        return

    # Get the device entry from the device registry
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(device_id)
    if not device_entry:
        _LOGGER.error("No device entry found for device ID %s", device_id)
        return
    
    """Find the coordinator corresponding to the given device ID."""
    for entry_id, coordinator in hass.data[DOMAIN].items():
        if getattr(coordinator, "device_id", None) == device_id:
            await coordinator._async_update_data()
            return

    _LOGGER.warning("No coordinator found for device ID %s", device_id)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    _LOGGER.debug("Updating Modbus/TCP entry!")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Modbus/TCP entry!")

    # Unload entries
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove entities and device from HASS"""
    _LOGGER.debug("Removing entities!")
    device_id = device_entry.id

    # Remove entities from entity registry
    ent_reg = er.async_get(hass)
    reg_entities = {}
    for ent in er.async_entries_for_config_entry(ent_reg, config_entry.entry_id):
        if device_id == ent.device_id:
            reg_entities[ent.unique_id] = ent.entity_id
    for entity_id in reg_entities.values():
        _LOGGER.debug("Removing entity!")
        ent_reg.async_remove(entity_id)

    # Remove device from device registry    
    # dev_reg = dr.async_get(hass)
    # dev_reg.async_remove_device(device_id)

    """
    # Remove device from config_entry
    devices = []
    for dev_id, dev_config in config_entry.data.items():
        if dev_config[CONF_NAME] == device_entry.name:
            devices.append(dev_config[CONF_IP])

    new_data = config_entry.data.copy()
    for dev in devices:
        # Remove device from config entry
        new_data[CONF_DEVICES].pop(dev)
    hass.config_entries.async_update_entry(config_entry, data=new_data)
    hass.config_entries._async_schedule_save()
    """

    return True
