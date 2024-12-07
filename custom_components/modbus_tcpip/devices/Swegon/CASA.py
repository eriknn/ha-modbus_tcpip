import logging

from ..modbusdevice import ModbusDevice
from ..datatypes import ModbusDatapoint, ModbusGroup, ModbusDefaultGroups, ModbusMode, ModbusPollMode
from ..datatypes import ModbusSensorData, ModbusNumberData, ModbusSelectData, ModbusBinarySensorData, ModbusSwitchData, ModbusButtonData

from homeassistant.const import UnitOfVolumeFlowRate, UnitOfElectricPotential, UnitOfTemperature, UnitOfPressure
from homeassistant.const import PERCENTAGE, DEGREE, CONCENTRATION_PARTS_PER_MILLION
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.helpers.entity import EntityCategory

_LOGGER = logging.getLogger(__name__)

class Device(ModbusDevice):
    # Define groups
    GROUP_COMMANDS = ModbusGroup(0, ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
    GROUP_COMMANDS2 = ModbusGroup(1, ModbusMode.HOLDING, ModbusPollMode.POLL_OFF) 
    GROUP_SETPOINTS = ModbusGroup(2, ModbusMode.HOLDING, ModbusPollMode.POLL_ON)
    GROUP_DEVICE_INFO = ModbusGroup(3, ModbusMode.INPUT, ModbusPollMode.POLL_ON)
    GROUP_ALARMS = ModbusGroup(4, ModbusMode.INPUT, ModbusPollMode.POLL_ON)
    GROUP_SENSORS = ModbusGroup(5, ModbusMode.INPUT, ModbusPollMode.POLL_ON)
    GROUP_SENSORS2 = ModbusGroup(6, ModbusMode.INPUT, ModbusPollMode.POLL_ON)
    GROUP_UNIT_STATUSES = ModbusGroup(7, ModbusMode.INPUT, ModbusPollMode.POLL_ON)  
    GROUP_UI = ModbusGroup(8, ModbusMode.HOLDING, ModbusPollMode.POLL_OFF) 

    def __init__(self, host:str, port:int, slave_id:int):
        super().__init__(host, port, slave_id)

        # Override static device information
        self.manufacturer="Swegon"
        self.model="CASA"

        # COMMANDS - Read/Write
        self.Datapoints[self.GROUP_COMMANDS] = {
            "Operating Mode": ModbusDatapoint(Address=5000, DataType=ModbusSelectData(options={0: "Stopped", 1: "Away", 2: "Home", 3: "Boost", 4: "Travel"})),
            "Fireplace Mode": ModbusDatapoint(Address=5001, DataType=ModbusSwitchData()),
            "Unused": ModbusDatapoint(Address=5002),
            "Travelling Mode": ModbusDatapoint(Address=5002, DataType=ModbusSwitchData()),
        }

        # COMMANDS2 - Write
        self.Datapoints[self.GROUP_COMMANDS2] = {
            "Reset Alarms": ModbusDatapoint(Address=5406, DataType=ModbusButtonData()),
        }

        # SETPOINTS - Read/Write
        self.Datapoints[self.GROUP_SETPOINTS] = {
            "Temperature Setpoint": ModbusDatapoint(Address=5100, Scaling=0.1, 
                                                    DataType=ModbusNumberData(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS, min_value=13, max_value=25, step=0.1))
        }

        # DEVICE_INFO - Read-only
        self.Datapoints[self.GROUP_DEVICE_INFO] = {
            "FW Maj": ModbusDatapoint(Address=6000),
            "FW Min": ModbusDatapoint(Address=6001),
            "FW Build": ModbusDatapoint(Address=6002),
            "Par Maj": ModbusDatapoint(Address=6003),
            "Par Min": ModbusDatapoint(Address=6004),
            "Model Name": ModbusDatapoint(Address=6007, Length=15),        # 15 registers
            "Serial Number": ModbusDatapoint(Address=6023, Length=24),     # 24 registers
        }

        # ALARMS - Read-only
        self.Datapoints[self.GROUP_ALARMS] = {
            "T1_Failure": ModbusDatapoint(Address=6100),
            "T2_Failure": ModbusDatapoint(Address=6101),
            "T3_Failure": ModbusDatapoint(Address=6102),
            "T4_Failure": ModbusDatapoint(Address=6103),
            "T5_Failure": ModbusDatapoint(Address=6104),
            "T6_Failure": ModbusDatapoint(Address=6105),
            "T7_Failure": ModbusDatapoint(Address=6106),
            "T8_Failure": ModbusDatapoint(Address=6107),
            "T1_Failure_Unconf": ModbusDatapoint(Address=6108),
            "T2_Failure_Unconf": ModbusDatapoint(Address=6109),
            "T3_Failure_Unconf": ModbusDatapoint(Address=6110),
            "T4_Failure_Unconf": ModbusDatapoint(Address=6111),
            "T5_Failure_Unconf": ModbusDatapoint(Address=6112),
            "T6_Failure_Unconf": ModbusDatapoint(Address=6113),
            "T7_Failure_Unconf": ModbusDatapoint(Address=6114),
            "T8_Failure_Unconf": ModbusDatapoint(Address=6115),
            "Afterheater_Failure": ModbusDatapoint(Address=6116),
            "Afterheater_Failure_Unconf": ModbusDatapoint(Address=6117),
            "Preheater_Failure": ModbusDatapoint(Address=6118),
            "Preheater_Failure_Unconf": ModbusDatapoint(Address=6119),
            "Freezing_Danger": ModbusDatapoint(Address=6120),
            "Freezing_Danger_Unconf": ModbusDatapoint(Address=6121),
            "Internal_Error": ModbusDatapoint(Address=6122),
            "Internal_Error_Unconf": ModbusDatapoint(Address=6123),
            "Supply_Fan_Failure": ModbusDatapoint(Address=6124),
            "Supply_Fan_Failure_Unconf": ModbusDatapoint(Address=6125),
            "Exhaust_Fan_Failure": ModbusDatapoint(Address=6126),
            "Exhaust_Fan_Failure_Unconf": ModbusDatapoint(Address=6127),
            "Service_Info": ModbusDatapoint(Address=6128),
            "Filter_Guard_Info": ModbusDatapoint(Address=6129),
            "Emergency_Stop": ModbusDatapoint(Address=6130),
            "Active Alarms": ModbusDatapoint(Address=6131, DataType=ModbusBinarySensorData(deviceClass=BinarySensorDeviceClass.PROBLEM, icon="mdi:bell")),
            "Info_Unconf": ModbusDatapoint(Address=6132),
        }

        # SENSORS - Read
        self.Datapoints[self.GROUP_SENSORS] = {
            "Fresh Air Temp": ModbusDatapoint(Address=6200, Scaling=0.1, DataType=ModbusSensorData(deviceClass=NumberDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
            "Supply Temp before re-heater": ModbusDatapoint(Address=6201, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
            "Supply Temp": ModbusDatapoint(Address=6202, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
            "Extract Temp": ModbusDatapoint(Address=6203, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
            "Exhaust Temp": ModbusDatapoint(Address=6204, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
            "Room_Temp": ModbusDatapoint(Address=6205, Scaling=0.1),
            "User Panel 1 Temp": ModbusDatapoint(Address=6206, Scaling=0.1, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.TEMPERATURE, units=UnitOfTemperature.CELSIUS)),
            "User Panel 2 Temp": ModbusDatapoint(Address=6207, Scaling=0.1),
            "Water Radiator Temp": ModbusDatapoint(Address=6208, Scaling=0.1),
            "Pre-Heater Temp": ModbusDatapoint(Address=6209, Scaling=0.1),
            "External Fresh Air Temp": ModbusDatapoint(6210, Scaling=0.1),
            "CO2 Unfiltered": ModbusDatapoint(Address=6211, Scaling=1.0),
            "CO2 Filtered": ModbusDatapoint(Address=6212, Scaling=1.0),
            "Relative Humidity": ModbusDatapoint(Address=6213, Scaling=1.0, DataType=ModbusSensorData(deviceClass=SensorDeviceClass.HUMIDITY, units=PERCENTAGE)),
            "Absolute Humidity": ModbusDatapoint(Address=6214, Scaling=0.1, DataType=ModbusSensorData(units="g/m³")),
            "Absolute Humidity SP": ModbusDatapoint(Address=6215, Scaling=0.1),
            "VOC": ModbusDatapoint(Address=6216, Scaling=1.0),
            "Supply Pressure": ModbusDatapoint(Address=6217, Scaling=1.0),
            "Exhaust Pressure": ModbusDatapoint(Address=6218, Scaling=1.0),
            "Supply Flow": ModbusDatapoint(Address=6219, Scaling=3.6),
            "Exhaust Flow": ModbusDatapoint(Address=6220, Scaling=3.6),
        }

        # SENSORS2 - Read
        self.Datapoints[self.GROUP_SENSORS2] = {
            "Heat Exchanger": ModbusDatapoint(Address=6233, DataType=ModbusSensorData(units=PERCENTAGE)),
        }

        # UNIT_STATUSES - Read
        self.Datapoints[self.GROUP_UNIT_STATUSES] = {
            "Unit_state": ModbusDatapoint(Address=6300),
            "Speed_state": ModbusDatapoint(Address=6301),
            "Supply Fan": ModbusDatapoint(Address=6302, DataType=ModbusSensorData(units=PERCENTAGE)),
            "Exhaust Fan": ModbusDatapoint(Address=6303, DataType=ModbusSensorData(units=PERCENTAGE)),
            "Supply_Fan_RPM": ModbusDatapoint(Address=6304),
            "Exhaust_Fan_RPM": ModbusDatapoint(Address=6305),
            "NotUsed1": ModbusDatapoint(Address=6306),
            "NotUsed2": ModbusDatapoint(Address=6307),
            "NotUsed3": ModbusDatapoint(Address=6308),
            "NotUsed4": ModbusDatapoint(Address=6309),
            "NotUsed5": ModbusDatapoint(Address=6310),
            "NotUsed6": ModbusDatapoint(Address=6311),
            "NotUsed7": ModbusDatapoint(Address=6312),
            "NotUsed8": ModbusDatapoint(Address=6313),
            "NotUsed9": ModbusDatapoint(Address=6314),
            "Temp_SP2": ModbusDatapoint(Address=6315),
            "Heating Output": ModbusDatapoint(Address=6316, DataType=ModbusSensorData(units=PERCENTAGE)),            
        }

        # CONFIGURATION - Read/Write
        self.Datapoints[ModbusDefaultGroups.CONFIG] = {
            "Travelling Mode Speed Drop": ModbusDatapoint(Address=5105),
            "Fireplace Run Time": ModbusDatapoint(Address=5103),
            "Fireplace Max Speed Difference": ModbusDatapoint(Address=5104),
            "Night Cooling": ModbusDatapoint(Address=5163),
            "Night Cooling FreshAir Max": ModbusDatapoint(Address=5164),
            "Night Cooling FreshAir Start": ModbusDatapoint(Address=5165),
            "Night Cooling RoomTemp Start": ModbusDatapoint(Address=5166),
            "Night Cooling SupplyTemp Min": ModbusDatapoint(Address=5167),
            "Away Supply Speed": ModbusDatapoint(Address=5301),
            "Away Exhaust Speed": ModbusDatapoint(Address=5302),
            "Home Supply Speed": ModbusDatapoint(Address=5303),
            "Home Exhaust Speed": ModbusDatapoint(Address=5304),
            "Boost Supply Speed": ModbusDatapoint(Address=5305),
            "Boost Exhaust Speed": ModbusDatapoint(Address=5306),
        }

         # CONFIGURATION - Read/Write
        self.Datapoints[self.GROUP_UI] = {
            "Efficiency": ModbusDatapoint(Address=0, DataType=ModbusSensorData(units=PERCENTAGE)),
        }       

        _LOGGER.debug("Loaded datapoints for %s %s", self.manufacturer, self.model)

    async def onBeforeRead(self):
        pass

    async def onAfterRead(self):
        # Update device info
        self.model = self.Datapoints[self.GROUP_DEVICE_INFO]["Model Name"].Value
        self.serial_number = self.Datapoints[self.GROUP_DEVICE_INFO]["Serial Number"].Value

        a = self.Datapoints[self.GROUP_DEVICE_INFO]["FW Maj"].Value
        b = self.Datapoints[self.GROUP_DEVICE_INFO]["FW Min"].Value
        c = self.Datapoints[self.GROUP_DEVICE_INFO]["FW Build"].Value
        self.sw_version = '{}.{}.{}'.format(a,b,c)

        # Calculate efficiency
        fresh = self.Datapoints[self.GROUP_SENSORS]["Fresh Air Temp"].Value
        sup = self.Datapoints[self.GROUP_SENSORS]["Supply Temp before re-heater"].Value
        extract = self.Datapoints[self.GROUP_SENSORS]["Extract Temp"].Value
        efficiency = ((sup - fresh) / (extract - fresh)) * 100
        self.Datapoints[self.GROUP_UI]["Efficiency"].Value = round(efficiency, 1)