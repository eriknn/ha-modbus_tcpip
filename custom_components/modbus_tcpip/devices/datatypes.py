from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional

###########################################
###### DATA TYPES FOR HOME ASSISTANT ######
###########################################
@dataclass
class ModbusData:
    deviceClass: str = None             # None | Load value from HA device class 
    category: str = None                # None | "config" | "diagnostic"
    icon: str = None                    # None | "mdi:thermometer"....

@dataclass
class ModbusSensorData(ModbusData):
    units: str = None                   # None | from homeassistant.const import UnitOf....

@dataclass
class ModbusSelectData(ModbusData):
    options: dict = field(default_factory=dict)

@dataclass
class ModbusNumberData(ModbusData):
    units: str = None
    min_value: int = 0
    max_value: int = 65535
    step: int = 1

@dataclass
class ModbusBinarySensorData(ModbusData):
    pass

@dataclass
class ModbusSwitchData(ModbusData):
    pass

@dataclass
class ModbusButtonData(ModbusData):
    pass

################################################
###### DATA TYPES FOR MODBUS FUNCTIONALITY ######
################################################
class ModbusMode(Enum):
    NONE = 0        # Used for virtual data points
    INPUT = 3
    HOLDING = 4

class ModbusPollMode(Enum):
    POLL_OFF = 0      # Values will not be read automatically
    POLL_ON = 1         # Values will be read each poll interval
    POLL_ONCE = 2       # Just read them once, for example for static configuration

ModbusGroup = namedtuple("ModbusGroup", ["unique_id", "mode", "poll_mode"])
class ModbusDefaultGroups(Enum):
    CONFIG = ModbusGroup(1000, ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)
    UI = ModbusGroup(1001, ModbusMode.NONE, ModbusPollMode.POLL_OFF)

    @property
    def unique_id(self):
        return self.value[0]
    
    @property
    def mode(self):
        return self.value[1]   
    
    @property
    def poll_mode(self):
        return self.value[2]

@dataclass
class ModbusDatapoint:
    Address: int = 0                                   # 0-indexed address
    Length: int = 1                                     # Number of registers
    Scaling: float = 1                                  # Multiplier for raw value      
    Value: float = 0                                    # Scaled value
    Attrs: Optional[Dict] = None                        # Dict for attributes
    DataType: ModbusData = None                         # Entitiy parameters