import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusDefaultGroups, ModbusMode, ModbusPollMode
from ..datatypes import ModbusSensorData, ModbusNumberData, ModbusSelectData, ModbusBinarySensorData

from homeassistant.const import UnitOfVolumeFlowRate, UnitOfElectricPotential, UnitOfTime
from homeassistant.const import PERCENTAGE, DEGREE
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.number import NumberDeviceClass

_LOGGER = logging.getLogger(__name__)

class Device(ModbusDevice):
    # Define groups
    GROUP_0 = ModbusGroup(0, ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
    GROUP_DEVICE_INFO = ModbusGroup(1, ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
    GROUP_UI = ModbusGroup(2, ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)

    def __init__(self, connection_params):
        super().__init__(connection_params)

        # Override static device information
        self.manufacturer="Trox"
        self.model="TVE"

        # GROUP 0
        self.Datapoints[self.GROUP_0] = {
            "Setpoint Flowrate": ModbusDatapoint(Address=0, Scaling=0.01, DataType=ModbusNumberData(units=PERCENTAGE, min_value=0, max_value=100, step=1)),
            "Override": ModbusDatapoint(Address=1, DataType=ModbusSelectData(options={0: "None", 1: "Open", 2: "Closed", 3: "Q Min", 4: "Q Max"})),
            "Command": ModbusDatapoint(Address=2, DataType=ModbusSelectData(options={0: "None", 1: "Synchronization", 2: "Test", 4: "Reset"})),
            "Unused": ModbusDatapoint(Address=3),
            "Position": ModbusDatapoint(Address=4, Scaling=0.01, DataType=ModbusSensorData(units=PERCENTAGE)),
            "Position Degrees": ModbusDatapoint(Address=5, DataType=ModbusSensorData(units=DEGREE)),
            "Flowrate Percent": ModbusDatapoint(Address=6, Scaling=0.01, DataType=ModbusSensorData(units=PERCENTAGE)),
            "Flowrate Actual": ModbusDatapoint(Address=7, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.VOLUME_FLOW_RATE, units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, icon="mdi:weather-windy")),
            "Analog Setpoint": ModbusDatapoint(Address=8, Scaling=0.001, DataType=ModbusSensorData(units=UnitOfElectricPotential.VOLT)),
        }

        # DEVICE_INFO - Read-only
        self.Datapoints[self.GROUP_DEVICE_INFO] = {
            "FW": ModbusDatapoint(Address=103),
            "Status": ModbusDatapoint(Address=104)
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "105 Q Min Percent": ModbusDatapoint(Address=105, Scaling=0.01, DataType=ModbusNumberData(units=PERCENTAGE, min_value=0, max_value=100, step=1)),
            "106 Q Max Percent": ModbusDatapoint(Address=106, Scaling=0.01, DataType=ModbusNumberData(units=PERCENTAGE, min_value=0, max_value=100, step=1)),
            "108 Action on Bus Timeout": ModbusDatapoint(Address=108),
            "109 Bus Timeout": ModbusDatapoint(Address=109, DataType=ModbusNumberData(units=UnitOfTime.SECONDS, min_value=0, max_value=100, step=1)),
            "120 Q Min": ModbusDatapoint(Address=120, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.VOLUME_FLOW_RATE, units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, icon="mdi:weather-windy")),
            "121 Q Max": ModbusDatapoint(Address=121, DataType=ModbusNumberData(deviceClass=NumberDeviceClass.VOLUME_FLOW_RATE, units=UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR, icon="mdi:weather-windy")),
            "130 Modbus Address": ModbusDatapoint(Address=130),
            "201 Volume Flow Unit": ModbusDatapoint(Address=201),
            "231 Signal Voltage": ModbusDatapoint(Address=231),
            "568 Modbus Parameters": ModbusDatapoint(Address=568),
            "569 Modbus Response Delay": ModbusDatapoint(Address=569, DataType=ModbusNumberData(units=UnitOfTime.MILLISECONDS, min_value=0, max_value=255, step=1)),
            "572 Switching Threshold": ModbusDatapoint(Address=572),
        }

        # UI Datapoints that don't connect directly with modbus address
        self.Datapoints[self.GROUP_UI] = {
            "Active Alarms": ModbusDatapoint(DataType=ModbusBinarySensorData(deviceClass=BinarySensorDeviceClass.PROBLEM, icon="mdi:bell"))
        }

        _LOGGER.debug("Loaded datapoints for %s %s", self.manufacturer, self.model)

    def onAfterFirstRead(self):
        # We need to adjust scaling of flow values depending on a configuration value
        flowUnits = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
        match self.Datapoints[ModbusDefaultGroups.CONFIG]["201 Volume Flow Unit"].Value:
            case 0:
                flowUnits = "l/s"
            case 1:
                flowUnits = UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR
            case 6:
                flowUnits = UnitOfVolumeFlowRate.CUBIC_FEET_PER_MINUTE
        self.Datapoints[self.GROUP_0]["Flowrate Actual"].DataType.units = flowUnits
        self.Datapoints[ModbusDefaultGroups.CONFIG]["120 Q Min"].DataType.units = flowUnits
        self.Datapoints[ModbusDefaultGroups.CONFIG]["121 Q Max"].DataType.units = flowUnits

    def onAfterRead(self):
        self.sw_version = self.Datapoints[self.GROUP_DEVICE_INFO]["FW"].Value

        # Handle alarms
        alarms = self.Datapoints[self.GROUP_DEVICE_INFO]["Status"].Value

        actAlarm = False
        attrs = {}
        if (alarms & (1 << 4)) != 0:
            attrs.update({"Mechanical Overload":"ALARM"})
            actAlarm = True
        if (alarms & (1 << 7)) != 0:
            attrs.update({"Internal Activity":"WARNING"})
        if (alarms & (1 << 9)) != 0:
            attrs.update({"Bus Timeout":"WARNING"})

        self.Datapoints[self.GROUP_UI]["Active Alarms"].Value = actAlarm
        self.Datapoints[self.GROUP_UI]["Active Alarms"].Attrs = attrs