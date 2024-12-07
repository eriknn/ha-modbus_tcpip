import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusMode, ModbusPollMode
from ..datatypes import ModbusSensorData

from homeassistant.const import UnitOfTemperature
from homeassistant.const import PERCENTAGE
from homeassistant.components.sensor import SensorDeviceClass

_LOGGER = logging.getLogger(__name__)

class Device(ModbusDevice):
    # Define groups
    GROUP_SENSORS = ModbusGroup(0, ModbusMode.INPUT, ModbusPollMode.POLL_ON)

    def __init__(self, host:str, port:int, slave_id:int):
        super().__init__(host, port, slave_id)

        # Override static device information
        self.manufacturer="Shandong Renke"
        self.model="RS-WS-N01-8"

        # SENSORS - Read-only
        self.Datapoints[self.GROUP_SENSORS] = {
            "Temperature": ModbusDatapoint(Address=0, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
            "Humidity": ModbusDatapoint(Address=1, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.HUMIDITY, units=PERCENTAGE)),
        }

        _LOGGER.debug("Loaded datapoints for %s %s", self.manufacturer, self.model)