import async_timeout
import datetime as dt
import logging

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .devices.helpers import load_device_class
from .devices.datatypes import ModbusDefaultGroups

_LOGGER = logging.getLogger(__name__)

class ModbusCoordinator(DataUpdateCoordinator):    
    def __init__(self, hass, device, device_model:str, ip, port, slave_id, scan_interval, scan_interval_fast):
        """Initialize coordinator parent"""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="ModbusDevice: " + device.name,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=dt.timedelta(seconds=scan_interval),
        )

        self.device_model = device_model
        self.ip = ip
        self.port = port
        self.slave_id = slave_id

        self._fast_poll_enabled = False
        self._fast_poll_count = 0
        self._normal_poll_interval = scan_interval
        self._fast_poll_interval = scan_interval_fast

        self._device = device

        self._modbusDevice = None

        # Initialize states
        self._measurements = None
        self._setpoints = None
        self._timestamp = dt.datetime(2024, 1, 1)

        # Storage for config selection
        self.config_selection = 0

        # Callback to entities
        self._update_callbacks = {}  

    async def initialize(self) -> None:
        # Load modbus device driver
        device_class = await load_device_class(self.device_model)
        if device_class is not None:
            self._modbusDevice = device_class(self.ip, self.port, self.slave_id)
            await self._modbusDevice.readData()

    @property
    def device_id(self):
        return self._device.id

    @property
    def devicename(self):
        return self._device.name

    @property
    def identifiers(self):
        return self._device.identifiers

    def setFastPollMode(self):
        _LOGGER.debug("Enabling fast poll mode")
        self._fast_poll_enabled = True
        self._fast_poll_count = 0
        self.update_interval = dt.timedelta(seconds=self._fast_poll_interval)
        self._schedule_refresh()

    def setNormalPollMode(self):
        _LOGGER.debug("Enabling normal poll mode")
        self._fast_poll_enabled = False
        self.update_interval = dt.timedelta(seconds=self._normal_poll_interval)


    async def _async_update_data(self):
        _LOGGER.debug("Coordinator updating data!!")

        """ Counter for fast polling """
        if self._fast_poll_enabled:
            self._fast_poll_count += 1
            if self._fast_poll_count > 5:
                self.setNormalPollMode()

        """ Fetch data """
        try:
            async with async_timeout.timeout(20):
                await self._modbusDevice.readData()
        except Exception as err:
            _LOGGER.debug("Failed when fetching data: %s", str(err))
        
        await self._async_update_deviceInfo()

    async def _async_update_deviceInfo(self) -> None:
        device_registry = dr.async_get(self.hass)
        device_registry.async_update_device(
            self.device_id,
            manufacturer=self._modbusDevice.manufacturer,
            model=self._modbusDevice.model,
            sw_version=self._modbusDevice.sw_version,
            serial_number=self._modbusDevice.serial_number,
        )
        _LOGGER.debug("Updated device data for: %s", self.devicename) 

    ################################
    ######## Configuration #########
    ################################   
    # Register callback to entity
    def registerOnUpdateCallback(self, entity, callbackfunc):
        self._update_callbacks.update({entity: callbackfunc})

    async def config_select(self, key, value):
        self.config_selection = value
        try:
            await self._modbusDevice.readValue(ModbusDefaultGroups.CONFIG, key)
        finally:
            await self._update_callbacks["Config Value"](ModbusDefaultGroups.CONFIG, key)

    def get_config_options(self):
        options = {}
        for i, config in enumerate(self._modbusDevice.Datapoints[ModbusDefaultGroups.CONFIG]):
            options.update({i:config})
        return options

    ################################
    ######### Read / Write #########
    ################################   
    def get_value(self, group, key):
        if group in self._modbusDevice.Datapoints:
            if key in self._modbusDevice.Datapoints[group]:
                return self._modbusDevice.Datapoints[group][key].Value
        return None

    def get_attrs(self, group, key):
        if group in self._modbusDevice.Datapoints:
            if key in self._modbusDevice.Datapoints[group]:
                return self._modbusDevice.Datapoints[group][key].Attrs
        return None

    async def write_value(self, group, key, value) -> bool:
        _LOGGER.debug("Write_Data: %s - %s - %s", group, key, value)
        await self._modbusDevice.writeValue(group, key, value)
        self.setFastPollMode()
