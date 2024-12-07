import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusDefaultGroups, ModbusMode, ModbusPollMode
from ..datatypes import ModbusSensorData, ModbusNumberData, ModbusSelectData, ModbusBinarySensorData

from homeassistant.const import UnitOfVolumeFlowRate, UnitOfElectricPotential
from homeassistant.const import PERCENTAGE, DEGREE
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory

_LOGGER = logging.getLogger(__name__)

class Device(ModbusDevice):
    # Define groups
    GROUP_COMMANDS = ModbusGroup(0, ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
    GROUP_SENSORS = ModbusGroup(1, ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
    GROUP_DEVICE_INFO = ModbusGroup(2, ModbusMode.HOLDING, ModbusPollMode.POLL_ON)

    def __init__(self, host:str, port:int, slave_id:int):
        super().__init__(host, port, slave_id)

        # Some custom device stuff
        self.readFirst = False

        # Override static device information
        self.manufacturer="Trox"
        self.model="TVE"

        # COMMANDS - Read/Write
        self.Datapoints[self.GROUP_COMMANDS] = {
            "Setpoint Flowrate": ModbusDatapoint(Address=0, Scaling=0.01, DataType=ModbusNumberData(units=PERCENTAGE, min_value=0, max_value=100, step=1)),
            "Override": ModbusDatapoint(Address=1, DataType=ModbusSelectData(options={0: "None", 1: "Open", 2: "Closed", 3: "Q Min", 4: "Q Max"})),
            "Command": ModbusDatapoint(Address=2, DataType=ModbusSelectData(options={0: "None", 1: "Synchronization", 2: "Test", 4: "Reset"})),
        }

        # SENSORS - Read-only
        self.Datapoints[self.GROUP_SENSORS] = {
            "Position": ModbusDatapoint(Address=4, Scaling=0.01, DataType=ModbusSensorData(units=PERCENTAGE)),
            "Position Degrees": ModbusDatapoint(Address=5, DataType=ModbusSensorData(units=DEGREE)),
            "Flowrate Percent": ModbusDatapoint(Address=6, Scaling=0.01, DataType=ModbusSensorData(units=PERCENTAGE)),
            "Flowrate Actual": ModbusDatapoint(Address=7, Scaling=1, DataType=ModbusSensorData(units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, icon="mdi:weather-windy")),
            "Analog Setpoint": ModbusDatapoint(Address=8, Scaling=0.001, DataType=ModbusSensorData(units=UnitOfElectricPotential.VOLT)),
        }

        # DEVICE_INFO - Read-only
        self.Datapoints[self.GROUP_DEVICE_INFO] = {
            "FW": ModbusDatapoint(Address=103),
            "Status": ModbusDatapoint(Address=104, DataType=ModbusBinarySensorData(deviceClass=BinarySensorDeviceClass.PROBLEM, icon="mdi:bell"))
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "105 Q Min Percent": ModbusDatapoint(Address=105),
            "106 Q Max Percent": ModbusDatapoint(Address=106),
            "108 Action on Bus Timeout": ModbusDatapoint(Address=108),
            "109 Bus Timeout": ModbusDatapoint(Address=109),
            "120 Q Min": ModbusDatapoint(Address=120),
            "121 Q Max": ModbusDatapoint(Address=121),
            "130 Modbus Address": ModbusDatapoint(Address=130),
            "201 Volume Flow Unit": ModbusDatapoint(Address=201),
            "231 Adjustment Mode": ModbusDatapoint(Address=231),
            "568 Modbus Parameters": ModbusDatapoint(Address=568),
            "569 Modbus Response Delay": ModbusDatapoint(Address=569),
            "572 Switching Threshold": ModbusDatapoint(Address=572),
        }

        _LOGGER.debug("Loaded datapoints for %s %s", self.manufacturer, self.model)

    async def onBeforeRead(self):
        if not self.readFirst:
            match await self.readValue(ModbusDefaultGroups.CONFIG, "201 Volume Flow Unit"):
                case 0:
                    self.Datapoints[self.GROUP_SENSORS]["Flowrate Actual"].Scaling = 3.6
                case 1:
                    self.Datapoints[self.GROUP_SENSORS]["Flowrate Actual"].Scaling = 1
                case 6:
                    self.Datapoints[self.GROUP_SENSORS]["Flowrate Actual"].Scaling = 1.69901
            self.readFirst = True

    async def onAfterRead(self):
        self.sw_version = self.Datapoints[self.GROUP_DEVICE_INFO]["FW"].Value