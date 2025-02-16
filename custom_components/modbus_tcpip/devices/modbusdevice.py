import logging

from dataclasses import dataclass
from typing import Dict

from homeassistant.helpers.entity import EntityCategory

from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException

from .connection import ConnectionParams, TCPConnectionParams, RTUConnectionParams

from .datatypes import ModbusMode, ModbusPollMode, ModbusDefaultGroups, ModbusGroup, ModbusDatapoint
from .datatypes import ModbusSelectData, ModbusNumberData

_LOGGER = logging.getLogger(__name__)

class InitHelper(type):
    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        instance.post_init()
        return instance

class ModbusDevice(metaclass=InitHelper):
    def __init__(self, connection_params: ConnectionParams):
        if isinstance(connection_params, TCPConnectionParams):
            self._client = ModbusTcpClient(host=connection_params.ip, port=connection_params.port)
        elif isinstance(connection_params, RTUConnectionParams):
            self._client = ModbusSerialClient(port=connection_params.serial_port, baudrate=connection_params.baud_rate)
        else:
            raise ValueError("Unsupported connection parameters")
        
        self._slave_id = connection_params.slave_id
        
        # Default properties
        self.manufacturer = None
        self.model = None
        self.sw_version = None
        self.serial_number = None

        # Initialize empty datapoints
        self.Datapoints: Dict[ModbusGroup, Dict[str, ModbusDatapoint]] = {}

        # Add default data groups
        self.Datapoints[ModbusDefaultGroups.CONFIG] = { }
        self.Datapoints[ModbusDefaultGroups.UI] = { }

        self.firstRead = True
    
    def post_init(self):
        # Add Config UI if we have config values
        if len(self.Datapoints[ModbusDefaultGroups.CONFIG]) > 0:
            self.Datapoints[ModbusDefaultGroups.UI] = {
                "Config Selection": ModbusDatapoint(DataType=ModbusSelectData(category=EntityCategory.CONFIG)),
                "Config Value": ModbusDatapoint(DataType=ModbusNumberData(category=EntityCategory.CONFIG, min_value=0, max_value=65535, step=1))
            }

    """ ******************************************************* """
    """ ************* FUNCTIONS CALLED ON EVENTS ************** """
    """ ******************************************************* """
    def onBeforeRead(self):
        pass
    def onAfterRead(self):
        pass
    def onAfterFirstRead(self):
        pass

    """ ******************************************************* """
    """ *********** EXTERNAL CALL TO READ ALL DATA ************ """
    """ ******************************************************* """
    async def readData(self):
        self.onBeforeRead()

        try:
            for group, datapoints in self.Datapoints.items():
                if group.poll_mode == ModbusPollMode.POLL_ON:
                    await self.readGroup(group)
                elif group.poll_mode == ModbusPollMode.POLL_ONCE and self.firstRead:
                    await self.readGroup(group)   
        except Exception as err:
            raise

        if self.firstRead:      
            self.onAfterFirstRead()
            self.firstRead = False       
        self.onAfterRead()

    """ ******************************************************* """
    """ ******************** READ GROUP *********************** """
    """ ******************************************************* """
    async def readGroup(self, group: ModbusGroup):
        """Read Modbus group registers and update data points."""

        # Calculate the total number of registers to read
        n_reg = sum(point.Length for point in self.Datapoints[group].values())
        if n_reg == 0:
            _LOGGER.warning("No data points to read in group: %s", self.Datapoints[group])
            return

        first_key = next(iter(self.Datapoints[group]))
        first_address = self.Datapoints[group][first_key].Address

        # Read the appropriate type of registers
        try:
            if group.mode == ModbusMode.INPUT:
                response = self._client.read_input_registers(address=first_address, count=n_reg, slave=self._slave_id)
            elif group.mode == ModbusMode.HOLDING:
                response = self._client.read_holding_registers(address=first_address, count=n_reg, slave=self._slave_id)
            else:
                raise ValueError(f"Unsupported Modbus mode: {group.mode}")
        except Exception as err:
            raise

        # Handle Modbus errors
        if response.isError():
            raise ModbusException(f"Error reading group {group}: {response}")

        _LOGGER.debug("Read data - %s: %s", group.unique_id, response.registers)

        # Process the registers and update data points
        register_index = 0
        for dataPointName, data in self.Datapoints[group].items():
            registers = response.registers[register_index:register_index + data.Length]
            register_index += data.Length

            data.Value = self.process_registers(registers, data.Scaling)

    """ ******************************************************* """
    """ **************** READ SINGLE VALUE ******************** """
    """ ******************************************************* """
    async def readValue(self, group: ModbusGroup, key: str) -> float | str:
        _LOGGER.debug("Reading value: Group: %s, Key: %s", group, key)

        if key not in self.Datapoints[group]:
            raise KeyError(f"Key '{key}' not found in group '{group}'")

        datapoint = self.Datapoints[group][key]
        length = datapoint.Length

        try:
            if group.mode == ModbusMode.INPUT:
                response = self._client.read_input_registers(address=datapoint.Address, count=length, slave=self._slave_id)
            elif group.mode == ModbusMode.HOLDING:
                response = self._client.read_holding_registers(address=datapoint.Address, count=length, slave=self._slave_id)
            else:
                raise ValueError(f"Unsupported Modbus mode: {group.mode}")
        except Exception as err:
            raise

        _LOGGER.debug("Read data: %s", response.registers)

        if response.isError():
            raise ModbusException(f"Error reading value for key '{key}': {response}")

        registers = response.registers[:length]
        datapoint.Value = self.process_registers(registers, datapoint.Scaling)

        return datapoint.Value

    """ ******************************************************* """
    """ **************** WRITE SINGLE VALUE ******************* """
    """ ******************************************************* """
    async def writeValue(self, group: ModbusGroup, key: str, value: float):
        _LOGGER.debug("Writing value: Group: %s, Key: %s, Value: %s", group, key, value)

        if key not in self.Datapoints[group]:
            raise KeyError(f"Key '{key}' not found in group '{group}'")

        datapoint = self.Datapoints[group][key]
        length = datapoint.Length
        if length > 2:
            raise ValueError(f"Unsupported register length: {length}. Only 1 or 2 registers are supported.")

        # Scale the value
        scaled_value = round(value / datapoint.Scaling)
        if scaled_value < 0:
            scaled_value = self.twos_complement(scaled_value, bits=16 * length)

        # Prepare the registers
        registers = []
        for _ in range(length):
            registers.insert(0, scaled_value & 0xFFFF)  # Extract the least significant 16 bits
            scaled_value >>= 16  # Shift the value to the next 16 bits

        # Write the registers
        try:
            if length == 1:
                response = self._client.write_register(address=datapoint.Address, value=registers[0], slave=self._slave_id)
            else:
                response = self._client.write_registers(address=datapoint.Address, values=registers, slave=self._slave_id)
        except Exception as err:
            raise

        if response.isError():
            raise ModbusException(f"Failed to write value for key '{key}': {response}")

        # Update the cached value
        datapoint.Value = value
        _LOGGER.debug("Successfully wrote value for key '%s': %s", key, value)

    """ ******************************************************* """
    """ *********** HELPER FOR PROCESSING REGISTERS *********** """
    """ ******************************************************* """
    def twos_complement(self, number: int, bits: int = 16) -> int:
        if number < 0:
            return number  # If the number is negative, no need for two's complement conversion.
        
        max_value = (1 << bits)  # Maximum value for the given bit-width.
        if number >= max_value // 2:
            return number - max_value  # Convert to negative value in two's complement.
        
        return number  # Return the number as is if it's already non-negative.

    def process_registers(self, registers: list[int], scaling: float) -> float | str:
        length = len(registers)

        if length <= 2:
            # Combine registers into a single value (big-endian)
            combined_value = 0
            for reg in registers:
                combined_value = (combined_value << 16) | reg

            newVal = self.twos_complement(combined_value)
            return newVal if scaling == 1.0 else newVal * scaling
        else:
            # Assume this is a text string
            try:
                newVal = ''.join(chr(value) for value in registers)
                return newVal.rstrip('\x00')
            except ValueError as e:
                # Failed to decode text, most likely just registers we are ignoring
                return None