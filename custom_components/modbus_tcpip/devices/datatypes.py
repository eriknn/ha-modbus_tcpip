from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
import uuid

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
class ModbusNumberData(ModbusData):
    units: str = None                   # None | from homeassistant.const import UnitOf....
    min_value: int = 0
    max_value: int = 65535
    step: int = 1

@dataclass
class ModbusSelectData(ModbusData):
    options: dict = field(default_factory=dict)

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

class ModbusGroup:
    def __init__(self, mode, poll_mode):
        # Initialize mode and poll_mode
        self.mode = mode
        self.poll_mode = poll_mode
        # Generate a unique ID automatically when the instance is created
        self._unique_id = str(uuid.uuid4())

    @property
    def unique_id(self):
        return self._unique_id  # Return the auto-generated unique ID

    def __eq__(self, other):
        # Ensure equality is based on mode and poll_mode
        if isinstance(other, ModbusGroup):
            return (self.mode == other.mode) and (self.poll_mode == other.poll_mode)
        return False

    def __hash__(self):
        # Hash based on mode, poll_mode, and unique_id to ensure uniqueness in dict
        return hash((self.mode, self.poll_mode, self.unique_id))
    
class ModbusDefaultGroups(Enum):
    CONFIG = ModbusGroup(ModbusMode.HOLDING, ModbusPollMode.POLL_OFF)
    UI = ModbusGroup(ModbusMode.NONE, ModbusPollMode.POLL_OFF)

    @property
    def unique_id(self):
        return self.value.unique_id  # Access the unique_id property directly
    
    @property
    def mode(self):
        return self.value.mode  # Access the mode property directly
    
    @property
    def poll_mode(self):
        return self.value.poll_mode  # Access the poll_mode property directly

@dataclass
class ModbusDatapoint:
    Address: int = 0                                   # 0-indexed address
    Length: int = 1                                     # Number of registers
    Scaling: float = 1                                  # Multiplier for raw value      
    Value: float = 0                                    # Scaled value
    Attrs: Optional[Dict] = None                        # Dict for attributes
    DataType: ModbusData = None                         # Entitiy parameters